"""Atomic publication on one empty disposable local database, never live state."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.crud.news_evaluation import bind_completed_run, claim_due_evaluation, finish_owned_evaluation
from app.crud.news_publication import NewsPublicationError, latest_decision
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimEvaluation, NewsClaimSource
from app.models.report import FloodAvoidanceZone, FloodEvent, FloodReport
from app.models.user import User
from app.models.role import Role
from app.schemas.news_audit import IndependentAuditResult, ProviderClaimAudit
from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput, NewsExtractionResult
from app.schemas.news_publication import NewsStaffDecisionRequest
from app.services.news_claim_auditor import AuditorConfig, NewsClaimAuditor, canonical_claim_sha256
from app.services.news_discovery_service import extraction_input_snapshot
from app.services.news_evaluation_service import EvaluationPolicy
from app.services.news_publication_service import (
    apply_staff_decision, clear_case_from_evaluation, expire_case, preview_staff_decision,
    process_news_publications, public_projection, publish_completed_evaluation,
)
from app.services.news_sources import NewsSource
from tests.test_news_claim_auditor import evidence
from tests.operational_footprint_fixtures import BOUNDARY, SyntheticLocalityProvider, register_footprint


@pytest.fixture(autouse=True)
def trusted_synthetic_footprint_assets(tmp_path, monkeypatch):
    from app.services import operational_footprint_evidence_service as service
    monkeypatch.setattr(service, "get_news_road_placement_provider", lambda: SyntheticLocalityProvider())
    monkeypatch.setenv("LANES_NEWS_OPERATIONAL_FOOTPRINT_DIR", str(tmp_path))

NOW = datetime(2026, 10, 5, 3, tzinfo=timezone.utc)
IDENTITY = NewsClaimAuditor(AuditorConfig(provider="openrouter", model="fixture/model", openrouter_api_key="synthetic")).policy_identity()
POLICY = EvaluationPolicy("a" * 64, "publication-fixture-v1", IDENTITY)
SOURCES = (NewsSource("fixture", "Fixture News", ("example.org",), ("https://example.org/feed",), NOW.date(), True),)


@pytest.fixture(scope="session")
def publication_factory():
    url = os.getenv("LANES_NEWS_PUBLICATION_LIFECYCLE_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Fresh disposable publication lifecycle database required")
    parsed = make_url(url)
    assert parsed.host in ("localhost", "127.0.0.1", "::1")
    assert (parsed.database or "").startswith("lanes_publication_lifecycle_test_")
    from app.core.config import settings
    patch = pytest.MonkeyPatch()
    patch.setattr(settings, "DATABASE_URL", url)
    engine = create_engine(url)
    assert not inspect(engine).get_table_names(), "Refusing a nonempty lifecycle database"
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    try:
        command.upgrade(config, "head")
        yield sessionmaker(bind=engine)
    finally:
        engine.dispose()
        patch.undo()


def seed_evaluation(factory, *, policy=POLICY, article_id=None, condition="active", observed=None,
                    depth="knee", status="completed", body_suffix="", evaluation_result_changes=None,
                    audit_access=False, bind=True, extraction_result_changes=None, **changes):
    observed = observed or NOW - timedelta(minutes=5)
    raw_depth = f"{depth} deep" if depth else None
    wording = f"was flooded {raw_depth or 'with unknown depth'}" if condition == "active" else "floodwaters subsided"
    access_wording = {"impassable_all": " No vehicles can pass.",
                      "light_vehicle_closed": " Light vehicles cannot pass.",
                      "passable_all": " All vehicles can pass.",
                      "passable_with_caution": " Passable with caution.",
                      "passable_unspecified": " Reported passable."}.get(changes.get("road_passability"), "")
    wording += access_wording
    body = f"At {observed.isoformat()}, Sample Road between First Street and Second Street in Pasig City {wording}." + body_suffix
    start = body.index("Sample Road")
    value = ExtractedClaim(**{
        "raw_place_name": "Sample Road", "canonical_road": "Sample Road", "canonical_city": "City of Pasig",
        "road_segment_raw": "Sample Road between First Street and Second Street", "place_type": "street",
        "place_char_start": start, "place_char_end": start + 11, "evidence_sentence": body,
        "evidence_sentence_offset": (0, len(body)), "condition": condition,
        "depth_raw": raw_depth if condition == "active" else None,
        "depth_canonical": depth if condition == "active" else None,
        "event_time_kind": "observation", "event_time_raw": observed.isoformat(),
        "event_time_resolved": observed, **changes,
    })
    with factory() as db, db.begin():
        row = db.get(NewsArticle, article_id) if article_id else None
        if row is None:
            row = NewsArticle(canonical_url=f"https://example.org/flood/{uuid4()}", publisher_source_id="fixture",
                title="Observed flooding", article_text=body, published_at=NOW, excerpt="", content_fingerprint="0" * 64)
            db.add(row)
            db.flush()
        article = NewsArticleExtractorInput(article_id=row.id, canonical_url=row.canonical_url, publisher="fixture",
            title="Observed flooding", article_text=body, published_at=NOW)
        snapshot, fingerprint = extraction_input_snapshot(article)
        version = NewsArticleVersion(article_id=row.id, input_snapshot=snapshot, input_fingerprint=fingerprint)
        db.add(version)
        db.flush()
        result = NewsExtractionResult(article_id=row.id, canonical_url=row.canonical_url, is_metadata_only=False,
            processed_text_length=len(body), claims=[value])
        if extraction_result_changes:
            result = result.model_copy(update=extraction_result_changes)
        run = NewsExtractionRun(article_version_id=version.id, pipeline_version=policy.pipeline_version,
            status="completed", completed_at=NOW, result=result.model_dump(mode="json"))
        db.add(run)
        db.flush()
        if not bind:
            return run.id, None, row.id
        bind_completed_run(db, run.id, policy.fingerprint, NOW)
        source = db.scalar(select(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run.id))
        owned = claim_due_evaluation(db, NOW, policy_fingerprint=policy.fingerprint, run_id=run.id)
        response = evidence(value, article)
        if value.depth_raw is None:
            response["depth"] = {"confirmed": False, "evidence": [], "canonical": None, "raw": None, "qualifiers": []}
        if audit_access:
            response["access"] = {"confirmed": True, "evidence": [{"start": 0, "end": len(body), "quote": body}],
                                  "classification": value.road_passability}
        audit = IndependentAuditResult(outcome="verified", reason_code="claim_evidence_verified", provider="openrouter",
            model="fixture/model", prompt_version=IDENTITY["prompt_version"], response_version=IDENTITY["response_version"],
            input_sha256=fingerprint, claim_sha256=source.claim_sha256,
            evidence=ProviderClaimAudit.model_validate_json(__import__("json").dumps(response)))
        evaluated = {"schema_version": "independent-claim-evaluation-v1", "policy_fingerprint": policy.fingerprint,
            "policy_identity": policy.auditor_identity, "input_sha256": fingerprint, "claim_sha256": source.claim_sha256,
            "reason_code": "claim_evidence_verified", "audit": audit.model_dump(mode="json")}
        if evaluation_result_changes:
            evaluated.update(evaluation_result_changes)
        if status == "failed":
            finish_owned_evaluation(db, owned, NOW, error_code="auditor_credential_missing")
        else:
            finish_owned_evaluation(db, owned, NOW, result=evaluated)
        return owned.evaluation_id, source.case_id, row.id


def publish(factory, evaluation_id, **kwargs):
    with factory() as db, db.begin():
        result = publish_completed_evaluation(db, evaluation_id, policy=kwargs.pop("policy", POLICY),
            now=kwargs.pop("now", NOW), sources=SOURCES, **kwargs)
        return result.id, result.case_id


def test_automatic_alert_is_atomic_idempotent_and_creates_no_operational_rows(publication_factory):
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory)
    first = publish(factory, evaluation_id)
    assert publish(factory, evaluation_id) == first
    with factory() as db:
        row = db.get(NewsClaimDecision, first[0])
        assert row.public_state == "active_alert" and row.expires_at == row.observed_at + timedelta(hours=2)
        assert public_projection(row, NOW).status == "Active"
        assert db.scalar(select(func.count()).select_from(FloodAvoidanceZone)) == 0
        assert db.scalar(select(func.count()).select_from(FloodEvent)) == 0
        assert db.scalar(select(func.count()).select_from(FloodReport)) == 0
        assert db.get(NewsClaimCase, case_id).revision == 1


def test_expiry_projects_immediately_then_records_unconfirmed_once(publication_factory):
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory)
    decision_id, _ = publish(factory, evaluation_id)
    later = NOW + timedelta(hours=2)
    with factory() as db:
        assert public_projection(db.get(NewsClaimDecision, decision_id), later).status == "Unconfirmed"
    with factory() as db, db.begin():
        assert expire_case(db, case_id, now=later).public_state == "expired"
    with factory() as db, db.begin():
        assert expire_case(db, case_id, now=later) is None
        assert db.get(NewsClaimCase, case_id).revision == 2


def test_unique_newer_audited_clearance_matches_same_source_section(publication_factory):
    factory = publication_factory
    wet, case_id, article_id = seed_evaluation(factory)
    publish(factory, wet)
    clearance, _, _ = seed_evaluation(factory, article_id=article_id, condition="subsided", observed=NOW)
    decision_id, matched_case = publish(factory, clearance)
    assert matched_case == case_id
    with factory() as db:
        row = db.get(NewsClaimDecision, decision_id)
        assert row.operation == "clear" and row.observed_at == NOW
        projection = public_projection(row, NOW)
        assert projection.status == "Cleared" and projection.cleared_at == NOW
        assert projection.observed_at == NOW - timedelta(minutes=5)
        assert projection.depth_label is None and projection.passability_label == "Vehicle passability unknown"
    assert publish(factory, clearance)[0] == decision_id


def test_clearance_from_different_article_cannot_clear_by_road_name(publication_factory):
    factory = publication_factory
    wet, case_id, _ = seed_evaluation(factory)
    publish(factory, wet)
    clearance, _, _ = seed_evaluation(factory, condition="subsided", observed=NOW)
    with pytest.raises(NewsPublicationError, match="identity_unproven"):
        with factory() as db, db.begin():
            clear_case_from_evaluation(db, case_id, clearance, expected_revision=1,
                request_id=uuid4(), policy=POLICY, now=NOW, sources=SOURCES)


def test_staff_clearance_request_binds_complete_payload_for_retries(publication_factory):
    factory = publication_factory
    wet, case_id, article_id = seed_evaluation(factory)
    publish(factory, wet)
    clearance, _, _ = seed_evaluation(factory, article_id=article_id, condition="subsided", observed=NOW)
    actor = staff_user(factory)
    request = NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=1, operation="clear",
        reason="Matched audited clearance", evaluation_id=clearance)
    with factory() as db, db.begin():
        decision_id = apply_staff_decision(db, case_id, request, actor_user_id=actor,
            policy=POLICY, now=NOW, sources=SOURCES).id
    with factory() as db, db.begin():
        assert apply_staff_decision(db, case_id, request, actor_user_id=actor,
            policy=POLICY, now=NOW, sources=SOURCES).id == decision_id
    changed = request.model_copy(update={"public_correction": "Different retry payload"})
    with pytest.raises(NewsPublicationError, match="request_identity_conflict"):
        with factory() as db, db.begin():
            apply_staff_decision(db, case_id, changed, actor_user_id=actor,
                policy=POLICY, now=NOW, sources=SOURCES)


def test_freshness_rechecked_after_audit_and_unknown_depth_not_fabricated(publication_factory):
    factory = publication_factory
    stale, _, _ = seed_evaluation(factory, observed=NOW - timedelta(hours=3))
    stale_id, _ = publish(factory, stale)
    unknown, _, _ = seed_evaluation(factory, depth=None)
    unknown_id, _ = publish(factory, unknown)
    with factory() as db:
        assert db.get(NewsClaimDecision, stale_id).public_state == "unpublished"
        row = db.get(NewsClaimDecision, unknown_id)
        assert row.public_state == "active_alert" and public_projection(row, NOW).depth_label is None


def test_failed_evaluation_consumed_once_instead_of_starving_worker(publication_factory):
    factory = publication_factory
    failed, _, _ = seed_evaluation(factory, status="failed")
    with factory() as db, db.begin():
        result = publish_completed_evaluation(db, failed, policy=POLICY, now=NOW, sources=SOURCES)
        assert result.evaluation_id == failed and result.review_state == "needs_review"
    summary = process_news_publications(factory, policy=POLICY, clock=lambda: NOW, sources=SOURCES)
    assert not summary.skipped


def staff_user(factory):
    with factory() as db, db.begin():
        role = db.scalar(select(Role).limit(1))
        if role is None:
            role = Role(name="Publication Fixture", permissions={"reports": "full"})
            db.add(role)
            db.flush()
        user = User(username=f"staff-{uuid4().hex[:12]}", email=f"{uuid4().hex}@example.org",
                    hashed_password="fixture-not-login", role_id=role.id)
        db.add(user)
        db.flush()
        return user.id


def test_staff_reject_revision_request_retry_and_reopen_do_not_resurrect(publication_factory):
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory)
    publish(factory, evaluation_id)
    actor = staff_user(factory)
    request = NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=1, operation="reject", reason="Unsupported source correction")
    with factory() as db, db.begin():
        effect = preview_staff_decision(db, case_id, request, policy=POLICY, now=NOW, sources=SOURCES)
        assert effect.public_state == "withdrawn"
        row = apply_staff_decision(db, case_id, request, actor_user_id=actor, policy=POLICY, now=NOW, sources=SOURCES)
        saved_id = row.id
    with factory() as db, db.begin():
        assert apply_staff_decision(db, case_id, request, actor_user_id=actor, policy=POLICY, now=NOW, sources=SOURCES).id == saved_id
    with pytest.raises(NewsPublicationError, match="request_identity_conflict"):
        with factory() as db, db.begin():
            apply_staff_decision(db, case_id, request.model_copy(update={"reason": "different request"}),
                actor_user_id=actor, policy=POLICY, now=NOW, sources=SOURCES)
    with pytest.raises(NewsPublicationError, match="stale_case_revision"):
        with factory() as db, db.begin():
            apply_staff_decision(db, case_id, request.model_copy(update={"request_id": uuid4()}),
                actor_user_id=actor, policy=POLICY, now=NOW, sources=SOURCES)
    reopen = NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=2, operation="reopen", reason="Recheck fresh evidence")
    with factory() as db, db.begin():
        row = apply_staff_decision(db, case_id, reopen, actor_user_id=actor, policy=POLICY, now=NOW, sources=SOURCES)
        assert row.public_state == "unpublished" and row.review_state == "needs_review"
        assert public_projection(row, NOW, include_retained=True) is None


def test_different_policy_can_recover_automatic_audit_exception(publication_factory):
    factory = publication_factory
    failed, case_id, _ = seed_evaluation(factory, status="failed")
    publish(factory, failed)
    policy = EvaluationPolicy("b" * 64, POLICY.pipeline_version, {**IDENTITY, "config_revision": "2"})
    with factory() as db, db.begin():
        old = db.get(NewsClaimEvaluation, failed)
        source = db.get(NewsClaimSource, old.claim_source_id)
        bind_completed_run(db, source.extraction_run_id, policy.fingerprint, NOW)
        leased = claim_due_evaluation(db, NOW, policy_fingerprint=policy.fingerprint, run_id=source.extraction_run_id)
        run = db.get(NewsExtractionRun, source.extraction_run_id)
        version = db.get(NewsArticleVersion, run.article_version_id)
        article = NewsArticleExtractorInput.model_validate({**version.input_snapshot, "article_id": version.article_id})
        claim = NewsExtractionResult.model_validate(run.result).claims[0]
        audit = IndependentAuditResult(outcome="verified", reason_code="claim_evidence_verified", provider="openrouter",
            model="fixture/model", prompt_version=IDENTITY["prompt_version"], response_version=IDENTITY["response_version"],
            input_sha256=version.input_fingerprint, claim_sha256=source.claim_sha256,
            evidence=ProviderClaimAudit.model_validate_json(__import__("json").dumps(evidence(claim, article))))
        finish_owned_evaluation(db, leased, NOW, result={"policy_fingerprint": policy.fingerprint,
            "policy_identity": policy.auditor_identity, "input_sha256": version.input_fingerprint,
            "claim_sha256": source.claim_sha256, "audit": audit.model_dump(mode="json")})
        recovered_id = leased.evaluation_id
    decision_id, _ = publish(factory, recovered_id, policy=policy)
    with factory() as db:
        assert db.get(NewsClaimDecision, decision_id).public_state == "active_alert"
        assert db.get(NewsClaimCase, case_id).revision == 2


def test_transaction_rollback_leaves_no_partial_decision_or_revision(publication_factory):
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory)
    with pytest.raises(RuntimeError, match="simulated interruption"):
        with factory() as db, db.begin():
            publish_completed_evaluation(db, evaluation_id, policy=POLICY, now=NOW, sources=SOURCES)
            raise RuntimeError("simulated interruption")
    with factory() as db:
        assert db.get(NewsClaimCase, case_id).revision == 0
        assert db.scalar(select(NewsClaimDecision.id).where(NewsClaimDecision.case_id == case_id)) is None
    assert publish(factory, evaluation_id)[1] == case_id


def test_parallel_publication_consumes_one_revision(publication_factory):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory)
    barrier = Barrier(2)
    def worker():
        barrier.wait(timeout=10)
        return publish(factory, evaluation_id)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.submit(worker), pool.submit(worker)
        assert first.result(timeout=30) == second.result(timeout=30)
    with factory() as db:
        assert db.get(NewsClaimCase, case_id).revision == 1


def test_fabricated_extracted_span_cannot_match_clearance(publication_factory):
    factory = publication_factory
    changes = {"road_segment_raw": "Sample Road between Invented Street and Unknown Street"}
    wet, case_id, article_id = seed_evaluation(factory, **changes)
    publish(factory, wet)
    clearance, _, _ = seed_evaluation(factory, article_id=article_id, condition="subsided", observed=NOW, **changes)
    with pytest.raises(NewsPublicationError, match="identity_unproven"):
        with factory() as db, db.begin():
            clear_case_from_evaluation(db, case_id, clearance, expected_revision=1,
                request_id=uuid4(), policy=POLICY, now=NOW, sources=SOURCES)


def test_older_observation_cannot_reappear_after_newer_clearance(publication_factory):
    factory = publication_factory
    wet, case_id, article_id = seed_evaluation(factory)
    publish(factory, wet)
    clearance, _, _ = seed_evaluation(factory, article_id=article_id, condition="subsided", observed=NOW)
    publish(factory, clearance)
    older, _, _ = seed_evaluation(factory, article_id=article_id, observed=NOW - timedelta(minutes=10))
    decision_id, _ = publish(factory, older)
    with factory() as db:
        row = db.get(NewsClaimDecision, decision_id)
        assert row.public_state == "unpublished" and row.reason_code == "source_observation_superseded"


def test_qualified_newer_observation_refreshes_same_case_once(publication_factory):
    factory = publication_factory
    wet, case_id, article_id = seed_evaluation(factory)
    initial_id, _ = publish(factory, wet)
    fresh, separate_evidence_case, _ = seed_evaluation(factory, article_id=article_id, observed=NOW, body_suffix=" Updated observation.")
    refreshed_id, matched_case_id = publish(factory, fresh)
    assert matched_case_id == case_id and separate_evidence_case != case_id
    assert publish(factory, fresh)[0] == refreshed_id
    with factory() as db:
        first = db.get(NewsClaimDecision, initial_id)
        second = db.get(NewsClaimDecision, refreshed_id)
        assert second.reason_code == "newer_matched_flood_observation"
        assert second.revision == 2 and second.expires_at == NOW + timedelta(hours=2)
        assert first.expires_at == NOW + timedelta(hours=1, minutes=55)
        assert db.get(NewsClaimCase, separate_evidence_case).revision == 0


@pytest.mark.parametrize("intermediate", ["reopen", "reject", "defer"])
def test_clearance_history_blocks_old_wet_correction_after_administrative_choices(publication_factory, intermediate):
    factory = publication_factory
    wet, case_id, article_id = seed_evaluation(factory)
    publish(factory, wet)
    clearance, _, _ = seed_evaluation(factory, article_id=article_id, condition="subsided", observed=NOW)
    publish(factory, clearance)
    actor = staff_user(factory)
    change = NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=2, operation=intermediate,
        reason="Administrative review only", deferred_until=NOW + timedelta(hours=1) if intermediate == "defer" else None)
    with factory() as db, db.begin():
        apply_staff_decision(db, case_id, change, actor_user_id=actor, policy=POLICY, now=NOW, sources=SOURCES)
    correction = NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=3, operation="correct",
        reason="Try original wet evidence", evaluation_id=wet)
    for method in (preview_staff_decision, apply_staff_decision):
        with pytest.raises(NewsPublicationError, match="source_observation_superseded"):
            with factory() as db, db.begin():
                kwargs = {"actor_user_id": actor} if method is apply_staff_decision else {}
                method(db, case_id, correction, policy=POLICY, now=NOW, sources=SOURCES, **kwargs)
    with factory() as db:
        assert db.get(NewsClaimCase, case_id).revision == 3
    automatic_old, _, _ = seed_evaluation(factory, article_id=article_id, observed=NOW - timedelta(minutes=10),
        body_suffix=" Older captured source version.")
    automatic_id, _ = publish(factory, automatic_old)
    with factory() as db:
        row = db.get(NewsClaimDecision, automatic_id)
        assert row.public_state == "unpublished" and row.reason_code == "source_observation_superseded"


def test_consumed_refresh_evidence_cannot_publish_duplicate_via_staff_correction(publication_factory):
    factory = publication_factory
    wet, case_id, article_id = seed_evaluation(factory)
    publish(factory, wet)
    fresh, evidence_case, _ = seed_evaluation(factory, article_id=article_id, observed=NOW, body_suffix=" Revised source.")
    publish(factory, fresh)
    actor = staff_user(factory)
    correction = NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=0, operation="correct",
        reason="Try already consumed evaluation", evaluation_id=fresh)
    for method in (preview_staff_decision, apply_staff_decision):
        with pytest.raises(NewsPublicationError, match="evaluation_already_consumed_by_other_case"):
            with factory() as db, db.begin():
                kwargs = {"actor_user_id": actor} if method is apply_staff_decision else {}
                method(db, evidence_case, correction, policy=POLICY, now=NOW, sources=SOURCES, **kwargs)


@pytest.mark.parametrize("administrative", [False, True])
def test_newer_wet_history_blocks_downgrade_to_old_same_case_evaluation(publication_factory, administrative):
    factory = publication_factory
    wet, case_id, article_id = seed_evaluation(factory)
    publish(factory, wet)
    fresh, _, _ = seed_evaluation(factory, article_id=article_id, observed=NOW, body_suffix=" Newer wet status.")
    publish(factory, fresh)
    actor = staff_user(factory)
    revision = 2
    if administrative:
        with factory() as db, db.begin():
            apply_staff_decision(db, case_id, NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=2,
                operation="reject", reason="Administrative withdrawal"), actor_user_id=actor,
                policy=POLICY, now=NOW, sources=SOURCES)
        revision = 3
    correction = NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=revision,
        operation="correct", reason="Try older status and depth", evaluation_id=wet)
    for method in (preview_staff_decision, apply_staff_decision):
        with pytest.raises(NewsPublicationError, match="source_observation_superseded"):
            with factory() as db, db.begin():
                kwargs = {"actor_user_id": actor} if method is apply_staff_decision else {}
                method(db, case_id, correction, policy=POLICY, now=NOW, sources=SOURCES, **kwargs)


def test_shared_support_withdrawal_preserves_independent_news_and_citizen_coverage(publication_factory):
    from geoalchemy2 import WKTElement
    from app.crud.news_publication import append_decision, lock_case, reserve_decision_id
    from app.models.news_publication import NewsClaimZoneLink
    from app.models.report import ReportSeverity, ReportSource, ReportStatus
    from app.schemas.news_publication import NewsDecisionSnapshot
    factory = publication_factory
    evaluations = [seed_evaluation(factory) for _ in range(2)]
    published = [publish(factory, item[0]) for item in evaluations]
    with factory() as db, db.begin():
        event = FloodEvent(peak_severity=ReportSeverity.MEDIUM, verified_at=NOW)
        db.add(event)
        db.flush()
        zone = FloodAvoidanceZone(event_id=event.id, geometry=WKTElement(
            "POLYGON((121 14.5,121.001 14.5,121.001 14.501,121 14.501,121 14.5))", srid=4326),
            is_active=True, expires_at=NOW + timedelta(hours=3))
        db.add(zone)
        db.flush()
        for ordinal, (decision_id, case_id) in enumerate(published):
            old = db.get(NewsClaimDecision, decision_id)
            case = lock_case(db, case_id)
            identity = reserve_decision_id(db)
            snapshot = NewsDecisionSnapshot.model_validate(old.snapshot)
            snapshot.public = snapshot.public.model_copy(update={"decision_id": identity, "revision": 2})
            new = append_decision(db, case, decision_id=identity, request_id=uuid4(), actor_kind="automatic",
                actor_user_id=None, operation="evaluate", public_state="active_zone", review_state="resolved",
                reason_code="native_support_fixture", snapshot=snapshot, observed_at=old.observed_at,
                expires_at=old.expires_at, now=NOW)
            db.add(NewsClaimZoneLink(decision_id=new.id, zone_id=zone.id, relation="created" if ordinal == 0 else "supported"))
        zone_id, event_id = zone.id, event.id
    actor = staff_user(factory)
    with factory() as db, db.begin():
        apply_staff_decision(db, published[0][1], NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=2,
            operation="reject", reason="Withdraw this source"), actor_user_id=actor, policy=POLICY, now=NOW, sources=SOURCES)
        assert db.get(FloodAvoidanceZone, zone_id).is_active
    # Add independent citizen support; withdrawing final news must preserve it.
    with factory() as db, db.begin():
        report = FloodReport(zone_id=zone_id, event_id=event_id, raw_text="Independent citizen observation",
            source=ReportSource.USER_REPORT, severity=ReportSeverity.MEDIUM, status=ReportStatus.APPROVED)
        db.add(report)
    with factory() as db, db.begin():
        apply_staff_decision(db, published[1][1], NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=2,
            operation="reject", reason="Withdraw the other source"), actor_user_id=actor, policy=POLICY, now=NOW, sources=SOURCES)
        assert db.get(FloodAvoidanceZone, zone_id).is_active
        assert db.get(FloodAvoidanceZone, zone_id).expires_at == NOW + timedelta(hours=3)


def test_activate_operational_footprint_splits_multipolygon_and_creates_zones(publication_factory):
    from app.services.news_publication_service import activate_operational_footprint
    from app.models.news_publication import NewsClaimZoneLink

    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory)
    publish(factory, evaluation_id)

    # MultiPolygon with 2 disjoint polygon components in Pasig
    multi_poly_geojson = {
        "type": "MultiPolygon",
        "coordinates": [
            [[[121.070, 14.580], [121.071, 14.580], [121.071, 14.581], [121.070, 14.581], [121.070, 14.580]]],
            [[[121.075, 14.585], [121.076, 14.585], [121.076, 14.586], [121.075, 14.586], [121.075, 14.585]]]
        ]
    }

    actor = staff_user(factory)
    with factory() as db, db.begin():
        decision = activate_operational_footprint(
            db,
            case_id,
            footprint=multi_poly_geojson,
            geometry_srid=4326,
            expected_revision=1,
            provenance_source="field_survey:drrmo_pasig",
            policy=POLICY,
            now=NOW,
            actor_user_id=actor,
            sources=SOURCES,
        )
        assert decision.public_state == "active_zone"
        assert decision.review_state == "resolved"
        assert decision.reason_code == "verified_operational_footprint"
        assert decision.snapshot["geometry_reason"] == "staff_reviewed_footprint"
        assert decision.snapshot["operational_provenance"]["binding"]["evidence_kind"] == "staff_review"

        # Check links created
        links = list(db.scalars(select(NewsClaimZoneLink).where(NewsClaimZoneLink.decision_id == decision.id)))
        assert len(links) == 2
        for link in links:
            assert link.relation == "created"
            zone = db.get(FloodAvoidanceZone, link.zone_id)
            assert zone is not None
            assert zone.is_active is True
            assert zone.report_source == "news"
            assert len(zone.contributors) == 1
            assert zone.contributors[0]["reporter_role"] == "News Publisher"

        # Verify both zones share the same FloodEvent parent
        z1 = db.get(FloodAvoidanceZone, links[0].zone_id)
        z2 = db.get(FloodAvoidanceZone, links[1].zone_id)
        assert z1.event_id is not None
        assert z1.event_id == z2.event_id

        # Public projection reflects operational polygon and affects routing
        proj = public_projection(decision, NOW)
        assert proj.status == "Active"
        assert proj.geometry_precision == "operational_polygon"
        assert proj.affects_routing is True
        assert proj.display_geojson is not None


def test_observation_refresh_extends_active_zone_expiry(publication_factory):
    from app.services.news_publication_service import activate_operational_footprint
    from app.models.news_publication import NewsClaimZoneLink

    factory = publication_factory
    wet, case_id, article_id = seed_evaluation(factory, observed=NOW - timedelta(minutes=30))
    publish(factory, wet)

    poly_geojson = {
        "type": "Polygon",
        "coordinates": [[[121.070, 14.580], [121.071, 14.580], [121.071, 14.581], [121.070, 14.581], [121.070, 14.580]]]
    }
    actor = staff_user(factory)
    with factory() as db, db.begin():
        act_dec = activate_operational_footprint(
            db,
            case_id,
            footprint=poly_geojson,
            geometry_srid=4326,
            expected_revision=1,
            provenance_source="field_survey:drrmo_pasig",
            policy=POLICY,
            now=NOW,
            actor_user_id=actor,
            sources=SOURCES,
        )
        zone_id = act_dec.snapshot["linked_zone_ids"][0]
        initial_provenance = act_dec.snapshot["operational_provenance"]
        initial_decision_id = act_dec.id
        initial_expiry = db.get(FloodAvoidanceZone, zone_id).expires_at

    # Newer observation from revised article
    fresh, fresh_case, _ = seed_evaluation(factory, article_id=article_id, observed=NOW, body_suffix=" Water still rising.")
    register_footprint(factory, fresh_case, poly_geojson)
    fresh_dec_id, refreshed_case_id = publish(factory, fresh)
    assert refreshed_case_id == case_id

    with factory() as db:
        fresh_dec = db.get(NewsClaimDecision, fresh_dec_id)
        assert fresh_dec.public_state == "active_zone"
        assert fresh_dec.reason_code == "newer_matched_flood_observation"
        proof = fresh_dec.snapshot["operational_provenance"]
        assert proof["geometry_sha256"] == initial_provenance["geometry_sha256"]
        assert proof["binding"]["observed_at"] != initial_provenance["binding"]["observed_at"]
        assert proof["binding"]["evidence_kind"] == "authoritative_current_incident"
        assert db.get(NewsClaimDecision, initial_decision_id).snapshot["operational_provenance"] == initial_provenance
        zone = db.get(FloodAvoidanceZone, zone_id)
        assert zone.expires_at > initial_expiry
        assert zone.expires_at == fresh_dec.expires_at

        # Verify a 'supported' link was added for this decision
        sup_link = db.scalar(select(NewsClaimZoneLink).where(
            NewsClaimZoneLink.decision_id == fresh_dec.id,
            NewsClaimZoneLink.zone_id == zone_id,
        ))
        assert sup_link is not None
        assert sup_link.relation == "supported"


OPERATIONAL_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[121.070, 14.580], [121.071, 14.580], [121.071, 14.581],
                     [121.070, 14.581], [121.070, 14.580]]],
}


def activation(factory, case_id, **changes):
    from app.services.news_publication_service import activate_operational_footprint
    options = dict(expected_revision=1, provenance_source="synthetic:operational-test", geometry_srid=4326,
                   policy=POLICY, now=NOW, sources=SOURCES)
    options.update(changes)
    footprint = options.pop("footprint", OPERATIONAL_POLYGON)
    options.setdefault("evidence_record_id", register_footprint(factory, case_id, footprint,
        source=options["provenance_source"], checksum=options.get("provenance_checksum")))
    with factory() as db, db.begin():
        return activate_operational_footprint(db, case_id, footprint, **options).id


def operational_counts(factory):
    from app.models.news_publication import NewsClaimZoneLink
    with factory() as db:
        return tuple(db.scalar(select(func.count()).select_from(model))
                     for model in (FloodEvent, FloodAvoidanceZone, NewsClaimZoneLink))


@pytest.mark.parametrize("scenario,reason", [
    ("expired", "observation_evidence_expired"),
    ("changed_policy", "publication_policy_changed"),
    ("unapproved_source", "unapproved_article_source"),
    ("stale_revision", "stale_case_revision"),
    ("unknown_depth", "operational_depth_not_verified"),
    ("passable_all", "reported_passable_to_all_vehicles"),
])
def test_activation_rechecks_current_evidence_before_any_operational_write(publication_factory, scenario, reason):
    from dataclasses import replace
    factory = publication_factory
    claim = {"depth": None} if scenario == "unknown_depth" else {}
    if scenario == "passable_all":
        claim["road_passability"] = "passable_all"
    evaluation_id, case_id, _ = seed_evaluation(factory, **claim)
    publish(factory, evaluation_id)
    options = {}
    if scenario == "expired":
        options["now"] = NOW + timedelta(hours=2)
    elif scenario == "changed_policy":
        options["policy"] = replace(POLICY, fingerprint="b" * 64)
    elif scenario == "unapproved_source":
        options["sources"] = ()
    elif scenario == "stale_revision":
        options["expected_revision"] = 0
    before = operational_counts(factory)
    with pytest.raises(NewsPublicationError, match=reason):
        activation(factory, case_id, **options)
    assert operational_counts(factory) == before
    with factory() as db:
        assert db.get(NewsClaimCase, case_id).revision == 1


@pytest.mark.parametrize("changed", ["geometry", "source", "checksum", "actor", "policy", "revision", "parent"])
def test_activation_retries_bind_complete_payload(publication_factory, changed):
    from copy import deepcopy
    from dataclasses import replace
    from shapely.geometry import Polygon
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory)
    publish(factory, evaluation_id)
    request_id = uuid4()
    first_id = activation(factory, case_id, request_id=request_id)
    assert activation(factory, case_id, request_id=request_id, now=NOW + timedelta(hours=3)) == first_id
    before = operational_counts(factory)
    options = {"request_id": request_id}
    if changed == "geometry":
        polygon = deepcopy(OPERATIONAL_POLYGON)
        polygon["coordinates"][0][1][0] += 0.001
        options["footprint"] = polygon
    elif changed == "source":
        options["provenance_source"] = "synthetic:different-source"
    elif changed == "checksum":
        options["provenance_checksum"] = "f" * 64
    elif changed == "actor":
        options["actor_user_id"] = staff_user(factory)
    elif changed == "policy":
        options["policy"] = replace(POLICY, fingerprint="b" * 64)
    elif changed == "revision":
        options["expected_revision"] = 2
    else:
        from shapely import set_srid
        options["parent_boundary"] = set_srid(Polygon([(121.06,14.57),(121.08,14.57),(121.08,14.59),(121.06,14.59)]),4326)
    with pytest.raises(NewsPublicationError, match="request_identity_conflict"):
        activation(factory, case_id, **options)
    assert operational_counts(factory) == before
    with factory() as db:
        assert db.get(NewsClaimCase, case_id).revision == 2
        assert db.get(NewsClaimDecision, first_id).expires_at == NOW + timedelta(hours=1, minutes=55)


def test_activation_default_request_is_stable_and_records_private_geometry_identity(publication_factory):
    from app.crud.news_evaluation import canonical_sha256
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory)
    publish(factory, evaluation_id)
    first_id = activation(factory, case_id, provenance_checksum="c" * 64)
    assert activation(factory, case_id, provenance_checksum="c" * 64, now=NOW + timedelta(minutes=5)) == first_id
    with factory() as db:
        row = db.get(NewsClaimDecision, first_id)
        proof = row.snapshot["operational_provenance"]
        assert proof["source"] == "synthetic:operational-test" and proof["source_checksum"] == "c" * 64
        assert proof["geometry_sha256"] == canonical_sha256(OPERATIONAL_POLYGON)
        from shapely.geometry import mapping
        assert proof["parent_boundary_sha256"] == canonical_sha256(mapping(BOUNDARY))
        assert proof["binding"]["article_id"] == row.snapshot["article_id"]
        assert proof["binding"]["claim_sha256"] == row.snapshot["claim_sha256"]
        assert "operational_provenance" not in public_projection(row, NOW).model_dump()


def test_parallel_activation_retries_create_one_decision_and_one_zone(publication_factory):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory)
    publish(factory, evaluation_id)
    before = operational_counts(factory)
    request_id, barrier = uuid4(), Barrier(2)
    def worker():
        barrier.wait(timeout=10)
        return activation(factory, case_id, request_id=request_id)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.submit(worker), pool.submit(worker)
        assert first.result(timeout=30) == second.result(timeout=30)
    assert operational_counts(factory) == tuple(value + 1 for value in before)


def test_activation_outer_rollback_leaves_no_partial_event_zone_links_or_revision(publication_factory):
    from app.services.news_publication_service import activate_operational_footprint
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory)
    publish(factory, evaluation_id)
    before = operational_counts(factory)
    request_id = uuid4()
    record_id = register_footprint(factory, case_id, OPERATIONAL_POLYGON)
    with pytest.raises(RuntimeError, match="interrupted activation"):
        with factory() as db, db.begin():
            activate_operational_footprint(db, case_id, OPERATIONAL_POLYGON, expected_revision=1,
                provenance_source="synthetic:operational-test", policy=POLICY, now=NOW,
                geometry_srid=4326, evidence_record_id=record_id,
                sources=SOURCES, request_id=request_id)
            raise RuntimeError("interrupted activation")
    assert operational_counts(factory) == before
    with factory() as db:
        assert db.get(NewsClaimCase, case_id).revision == 1
        assert db.scalar(select(NewsClaimDecision.id).where(NewsClaimDecision.request_id == request_id)) is None
    activation(factory, case_id, request_id=request_id)


@pytest.mark.parametrize("invalid_result,reason", [
    ({"audit": None, "reason_code": "independent_audit_unavailable"}, "independent_audit_unavailable"),
    ({"audit": {"outcome": "verified"}}, "invalid_independent_audit"),
    ({"claim_sha256": "f" * 64}, "evaluation_identity_mismatch"),
])
def test_preexisting_active_label_cannot_bypass_current_stored_audit_validation(publication_factory, invalid_result, reason):
    # Construct a bad upstream decision with the low-level append helper. Even
    # an existing Active label must not substitute for valid current evidence.
    from app.services.news_publication_service import _load, _snapshot, _write
    from app.crud.news_publication import lock_case, reserve_decision_id
    factory = publication_factory
    valid_evaluation, _, _ = seed_evaluation(factory)
    valid_decision, _ = publish(factory, valid_evaluation)
    evaluation_id, case_id, _ = seed_evaluation(factory, evaluation_result_changes=invalid_result)
    with factory() as db, db.begin():
        evaluation, source, _, version, article, claim, _, failure = _load(db,evaluation_id,POLICY,NOW,SOURCES)
        assert failure
        case = lock_case(db, case_id)
        decision_id = reserve_decision_id(db)
        public = public_projection(db.get(NewsClaimDecision,valid_decision),NOW).model_copy(update={
            "case_id": case_id, "decision_id": decision_id, "revision": 1, "source_url": article.canonical_url,
        })
        snapshot = _snapshot(source,version,claim,POLICY,"a"*64,evaluation_id=evaluation.id,public=public)
        _write(db,case,decision_id,uuid4(),snapshot,NOW,state="active_alert",review="resolved",
               observed=claim.event_time_resolved,expiry=public.expires_at)
    before = operational_counts(factory)
    with pytest.raises(NewsPublicationError, match=reason):
        activation(factory,case_id)
    assert operational_counts(factory) == before
    with factory() as db:
        assert db.get(NewsClaimCase,case_id).revision == 1


@pytest.mark.parametrize("later_condition", ["active", "subsided"])
def test_activation_historical_observation_barriers_survive_an_old_active_label(publication_factory, later_condition):
    from app.services.news_publication_service import _load, _snapshot, _write
    from app.crud.news_publication import lock_case, reserve_decision_id
    factory = publication_factory
    wet, _, article_id = seed_evaluation(factory)
    original_id, _ = publish(factory, wet)
    newer, _, _ = seed_evaluation(factory, article_id=article_id, condition=later_condition,
                                  observed=NOW, body_suffix=" Newer source observation.")
    publish(factory, newer)
    old, old_case, _ = seed_evaluation(factory, article_id=article_id,
                                      observed=NOW-timedelta(minutes=10), body_suffix=" Old captured revision.")
    with factory() as db, db.begin():
        evaluation, source, _, version, article, claim, _, failure = _load(db,old,POLICY,NOW,SOURCES)
        assert failure is None
        case = lock_case(db,old_case)
        decision_id = reserve_decision_id(db)
        public = public_projection(db.get(NewsClaimDecision,original_id),NOW).model_copy(update={
            "case_id": old_case, "decision_id": decision_id, "revision": 1,
            "observed_at": claim.event_time_resolved, "expires_at": claim.event_time_resolved+timedelta(hours=2),
        })
        snapshot = _snapshot(source,version,claim,POLICY,"a"*64,evaluation_id=evaluation.id,public=public)
        _write(db,case,decision_id,uuid4(),snapshot,NOW,state="active_alert",review="resolved",
               observed=claim.event_time_resolved,expiry=public.expires_at)
    before = operational_counts(factory)
    with pytest.raises(NewsPublicationError, match="source_observation_superseded"):
        activation(factory,old_case)
    assert operational_counts(factory) == before


@pytest.mark.parametrize("operation", ["expire", "clear"])
def test_activation_provenance_survives_linked_zone_lifecycle(publication_factory, operation):
    factory = publication_factory
    wet, case_id, article_id = seed_evaluation(factory)
    publish(factory,wet)
    activated_id = activation(factory,case_id)
    with factory() as db:
        activated = db.get(NewsClaimDecision,activated_id)
        provenance = activated.snapshot["operational_provenance"]
        zone_id = activated.snapshot["linked_zone_ids"][0]
    if operation == "clear":
        evaluation_id, _, _ = seed_evaluation(factory,article_id=article_id,condition="subsided",observed=NOW)
    with factory() as db, db.begin():
        if operation == "expire":
            result = expire_case(db,case_id,now=NOW+timedelta(hours=2))
        else:
            result = clear_case_from_evaluation(db,case_id,evaluation_id,expected_revision=2,
                request_id=uuid4(),policy=POLICY,now=NOW,sources=SOURCES)
        assert result.snapshot["operational_provenance"] == provenance
        assert not db.get(FloodAvoidanceZone,zone_id).is_active


def staff_activation(factory, case_id, evaluation_id, **changes):
    actor = changes.pop("actor_user_id", None) or staff_user(factory)
    options = dict(request_id=uuid4(), expected_revision=1, operation="correct",
                   reason="Reviewed synthetic operational footprint", evaluation_id=evaluation_id,
                   operational_footprint=OPERATIONAL_POLYGON)
    options["operational_footprint_srid"] = 4326
    options.update(changes)
    with factory() as db, db.begin():
        return apply_staff_decision(db, case_id, NewsStaffDecisionRequest(**options),
            actor_user_id=actor, policy=POLICY, now=NOW, sources=SOURCES).id


@pytest.mark.parametrize("path", ["automatic", "staff"])
@pytest.mark.parametrize("depth,access,expected_access", [
    ("gutter", "unknown", None),
    ("knee", "unknown", None),
    ("waist", "unknown", None),
    ("neck", "unknown", None),
    ("gutter", "light_vehicle_closed", "Light vehicles prohibited"),
    ("gutter", "impassable_all", "No vehicles"),
    ("gutter", "passable_with_caution", "Passable with caution; vehicle types unspecified"),
    ("gutter", "passable_unspecified", "Passability reported; vehicle types unspecified"),
])
def test_every_news_polygon_persists_verified_metadata(publication_factory, path, depth, access, expected_access):
    from copy import deepcopy
    from app.schemas.report import FloodAvoidanceZoneResponse
    from app.services.flood_depth import get_flood_depth_measurement
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory, depth=depth, road_passability=access,
                                                audit_access=access != "unknown")
    publish(factory, evaluation_id)
    second = deepcopy(OPERATIONAL_POLYGON["coordinates"])
    for point in second[0]:
        point[0] += 0.005
    multi = {"type": "MultiPolygon", "coordinates": [OPERATIONAL_POLYGON["coordinates"], second]}
    decision_id = (activation(factory, case_id, footprint=multi) if path == "automatic"
                   else staff_activation(factory, case_id, evaluation_id, operational_footprint=multi))
    measurement = get_flood_depth_measurement(depth)
    with factory() as db:
        decision = db.get(NewsClaimDecision, decision_id)
        zone_ids = decision.snapshot["linked_zone_ids"]
        assert len(zone_ids) == 2
        events = set()
        for zone_id in zone_ids:
            zone = db.get(FloodAvoidanceZone, zone_id)
            events.add(zone.event_id)
            response = FloodAvoidanceZoneResponse.model_validate(zone)
            assert response.severity == measurement.severity.value
            assert response.depth == depth
            assert response.depth_meters == measurement.meters
            assert response.depth_inches == measurement.inches
            assert response.depth_formatted == f"{measurement.display_label} • {measurement.formatted}"
            assert response.passable_vehicles == expected_access
            assert response.report_source == "news"
            assert response.contributors[0].depth == depth
            assert response.contributors[0].severity == measurement.severity.value
            assert zone.curated_by_admin_id is None
        assert len(events) == 1
        event = db.get(FloodEvent, events.pop())
        assert event.peak_severity == measurement.severity and event.peak_depth == depth


@pytest.mark.asyncio
@pytest.mark.parametrize("depth,access,expected", [
    ("gutter", "unknown", {"walk": "passable", "motorcycle": "passable", "light": "passable", "heavy": "passable"}),
    ("gutter", "light_vehicle_closed", {"walk": "passable", "motorcycle": "blocked", "light": "blocked", "heavy": "passable"}),
    ("gutter", "impassable_all", {"walk": "passable", "motorcycle": "blocked", "light": "blocked", "heavy": "blocked"}),
    ("waist", "passable_with_caution", {"walk": "cautious", "motorcycle": "blocked", "light": "blocked", "heavy": "blocked"}),
    ("neck", "unknown", {"walk": "blocked", "motorcycle": "blocked", "light": "blocked", "heavy": "blocked"}),
])
async def test_public_zone_api_and_native_routing_read_news_metadata(publication_factory, monkeypatch, depth, access, expected):
    import httpx
    from types import SimpleNamespace
    from sqlalchemy import literal
    from app.core.database import get_db
    from app.main import app
    from app.crud import report as report_crud
    from app.services import flood_routing_policy as routing
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory, depth=depth, road_passability=access,
                                                audit_access=access != "unknown")
    publish(factory, evaluation_id)
    decision_id = activation(factory, case_id)
    with factory() as db:
        zone_id = db.get(NewsClaimDecision, decision_id).snapshot["linked_zone_ids"][0]
    # Use the fixture observation clock in the real SQL expiry predicates.
    monkeypatch.setattr(report_crud, "func", SimpleNamespace(now=lambda: literal(NOW)))
    monkeypatch.setattr(routing, "func", SimpleNamespace(now=lambda: literal(NOW), ST_AsGeoJSON=func.ST_AsGeoJSON))
    def database():
        with factory() as db:
            yield db
    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = database
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            result = await client.get("/api/v1/reports/active-zones")
        assert result.status_code == 200
        public = next(item for item in result.json() if item["id"] == zone_id)
        assert public["depth"] == depth and public["report_source"] == "news"
        with factory() as db:
            routed = next(zone for zone in routing.get_active_flood_zones(db) if zone.id == zone_id)
            assert routed.severity == public["severity"]
            assert routed.passable_vehicles == public["passable_vehicles"]
            assert {profile: routing.zone_decision(profile, routed) for profile in expected} == expected
        with factory() as db, db.begin():
            expire_case(db, case_id, now=NOW+timedelta(hours=2))
        with factory() as db:
            assert zone_id not in {zone.id for zone in routing.get_active_flood_zones(db)}
            assert zone_id not in {zone.id for zone in report_crud.get_active_avoidance_zones(db)}
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


@pytest.mark.parametrize("depth,access,reason", [
    (None, "unknown", "operational_depth_not_verified"),
    ("gutter", "passable_all", "reported_passable_to_all_vehicles"),
    ("gutter", "light_vehicle_closed", "operational_access_not_verified"),
])
def test_staff_geometry_cannot_invent_operational_measurements_or_access(publication_factory, depth, access, reason):
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory, depth=depth, road_passability=access)
    publish(factory, evaluation_id)
    before = operational_counts(factory)
    with pytest.raises(NewsPublicationError, match=reason):
        staff_activation(factory, case_id, evaluation_id)
    assert operational_counts(factory) == before
    with factory() as db:
        assert db.get(NewsClaimCase, case_id).revision == 1


@pytest.mark.parametrize("access", ["light_vehicle_closed", "impassable_all"])
def test_automatic_zone_requires_independently_verified_known_access(publication_factory, access):
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory, road_passability=access)
    publish(factory, evaluation_id)
    before = operational_counts(factory)
    with pytest.raises(NewsPublicationError, match="operational_access_not_verified"):
        activation(factory, case_id)
    assert operational_counts(factory) == before


@pytest.mark.parametrize("end", ["reject", "defer", "reopen", "text_only", "clear", "expire"])
def test_same_case_retained_zone_stays_active_until_its_final_support_ends(publication_factory, end):
    from app.models.news_publication import NewsClaimZoneLink
    from app.models.report import FloodEventStatus
    factory = publication_factory
    evaluation_id, case_id, article_id = seed_evaluation(factory, depth="waist")
    publish(factory, evaluation_id)
    original = staff_activation(factory, case_id, evaluation_id)
    actor = staff_user(factory)
    with factory() as db:
        original_decision = db.get(NewsClaimDecision, original)
        zone_id = original_decision.snapshot["linked_zone_ids"][0]
        expiry = db.get(FloodAvoidanceZone, zone_id).expires_at
    retained_request = NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=2, operation="correct",
        reason="Retain the same reviewed footprint", evaluation_id=evaluation_id, operational_zone_id=zone_id)
    with factory() as db, db.begin():
        retained = apply_staff_decision(db, case_id, retained_request, actor_user_id=actor, policy=POLICY,
                                       now=NOW, sources=SOURCES)
        retained_id = retained.id
        zone = db.get(FloodAvoidanceZone, zone_id)
        event_id = zone.event_id
        assert zone.is_active and zone.expires_at == expiry and zone.depth == "waist"
        assert db.get(FloodEvent, event_id).status == FloodEventStatus.ACTIVE
        assert db.scalar(select(NewsClaimZoneLink.relation).where(NewsClaimZoneLink.decision_id == retained.id)) == "supported"
    counts = operational_counts(factory)
    with factory() as db, db.begin():
        assert apply_staff_decision(db, case_id, retained_request, actor_user_id=actor, policy=POLICY,
            now=NOW+timedelta(minutes=10), sources=SOURCES).id == retained_id
        assert db.get(FloodAvoidanceZone, zone_id).expires_at == expiry
    assert operational_counts(factory) == counts
    if end == "clear":
        cleared, _, _ = seed_evaluation(factory, article_id=article_id, condition="subsided", observed=NOW)
    with factory() as db, db.begin():
        ended_at = NOW+timedelta(hours=2) if end == "expire" else NOW
        if end == "expire":
            expire_case(db, case_id, now=ended_at)
        elif end == "clear":
            clear_case_from_evaluation(db, case_id, cleared, expected_revision=3, request_id=uuid4(),
                                      policy=POLICY, now=NOW, sources=SOURCES)
        else:
            options = {"evaluation_id": evaluation_id} if end == "text_only" else {}
            if end == "defer": options["deferred_until"] = NOW+timedelta(hours=1)
            request = NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=3,
                operation="correct" if end == "text_only" else end, reason="End retained source support", **options)
            if end == "reopen":
                with pytest.raises(NewsPublicationError, match="claim_cannot_reopen"):
                    apply_staff_decision(db, case_id, request, actor_user_id=actor, policy=POLICY, now=NOW, sources=SOURCES)
                assert db.get(FloodAvoidanceZone, zone_id).is_active
                apply_staff_decision(db, case_id, NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=3,
                    operation="reject", reason="Withdraw before reopening"), actor_user_id=actor,
                    policy=POLICY, now=NOW, sources=SOURCES)
                request = request.model_copy(update={"request_id": uuid4(), "expected_revision": 4})
            apply_staff_decision(db, case_id, request, actor_user_id=actor, policy=POLICY, now=NOW, sources=SOURCES)
        zone = db.get(FloodAvoidanceZone, zone_id)
        assert not zone.is_active and zone.expires_at <= ended_at
        assert db.get(FloodEvent, event_id).status == FloodEventStatus.ENDED
        assert db.get(NewsClaimDecision, original).public_state == "active_zone"
        assert db.get(NewsClaimDecision, retained_id).public_state == "active_zone"


def test_replacement_footprint_ends_old_support_but_keeps_new_zone_active(publication_factory):
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory)
    publish(factory, evaluation_id)
    original = staff_activation(factory, case_id, evaluation_id)
    with factory() as db:
        old_id = db.get(NewsClaimDecision, original).snapshot["linked_zone_ids"][0]
    replacement = staff_activation(factory, case_id, evaluation_id, expected_revision=2)
    with factory() as db:
        new_id = db.get(NewsClaimDecision, replacement).snapshot["linked_zone_ids"][0]
        assert new_id != old_id
        assert not db.get(FloodAvoidanceZone, old_id).is_active
        assert db.get(FloodAvoidanceZone, new_id).is_active


def test_parallel_same_case_retention_serializes_revision_and_preserves_zone(publication_factory):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory)
    publish(factory, evaluation_id)
    original = staff_activation(factory, case_id, evaluation_id)
    actor = staff_user(factory)
    with factory() as db:
        zone_id = db.get(NewsClaimDecision, original).snapshot["linked_zone_ids"][0]
    barrier = Barrier(2)
    def worker():
        barrier.wait(timeout=10)
        try:
            with factory() as db, db.begin():
                result = apply_staff_decision(db, case_id, NewsStaffDecisionRequest(request_id=uuid4(),
                    expected_revision=2, operation="correct", reason="Concurrent retention",
                    evaluation_id=evaluation_id, operational_zone_id=zone_id), actor_user_id=actor,
                    policy=POLICY, now=NOW, sources=SOURCES)
                return result.public_state
        except NewsPublicationError as exc:
            return exc.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker) for _ in range(2)]
        assert sorted(future.result(timeout=30) for future in futures) == ["active_zone", "stale_case_revision"]
    with factory() as db:
        assert db.get(FloodAvoidanceZone, zone_id).is_active
        assert db.get(NewsClaimCase, case_id).revision == 3


@pytest.mark.parametrize("replacement", [False, True])
def test_retained_or_replaced_zone_changes_rollback_with_outer_transaction(publication_factory, replacement):
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory)
    publish(factory, evaluation_id)
    original = staff_activation(factory, case_id, evaluation_id)
    actor = staff_user(factory)
    with factory() as db:
        zone_id = db.get(NewsClaimDecision, original).snapshot["linked_zone_ids"][0]
    before = operational_counts(factory)
    geometry = {"operational_footprint": OPERATIONAL_POLYGON, "operational_footprint_srid": 4326} if replacement else {"operational_zone_id": zone_id}
    with pytest.raises(RuntimeError, match="Interrupt support change"):
        with factory() as db, db.begin():
            apply_staff_decision(db, case_id, NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=2,
                operation="correct", reason="Rollback fixture", evaluation_id=evaluation_id, **geometry),
                actor_user_id=actor, policy=POLICY, now=NOW, sources=SOURCES)
            raise RuntimeError("Interrupt support change")
    assert operational_counts(factory) == before
    with factory() as db:
        assert db.get(NewsClaimCase, case_id).revision == 2
        assert db.get(FloodAvoidanceZone, zone_id).is_active


def test_expired_zone_cannot_be_retained_as_current_coverage(publication_factory):
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory)
    publish(factory, evaluation_id)
    original = staff_activation(factory, case_id, evaluation_id)
    with factory() as db, db.begin():
        zone_id = db.get(NewsClaimDecision, original).snapshot["linked_zone_ids"][0]
        db.get(FloodAvoidanceZone, zone_id).expires_at = NOW
    before = operational_counts(factory)
    with pytest.raises(NewsPublicationError, match="invalid_operational_zone"):
        staff_activation(factory, case_id, evaluation_id, expected_revision=2,
                         operational_footprint=None, operational_zone_id=zone_id)
    assert operational_counts(factory) == before


@pytest.mark.parametrize("change,reason", [
    ("no_catalog","operational_footprint_catalog_not_configured"),
    ("no_record","unapproved_operational_footprint_record"),
    ("source","operational_source_identity_mismatch"),
    ("checksum","operational_source_identity_mismatch"),
    ("geometry","operational_geometry_evidence_mismatch"),
    ("article_id","operational_incident_identity_mismatch"),
    ("input_sha256","operational_incident_identity_mismatch"),
    ("claim_sha256","operational_incident_identity_mismatch"),
    ("incident_identity","operational_incident_identity_mismatch"),
    ("observed_at","operational_incident_identity_mismatch"),
    ("city","operational_incident_identity_mismatch"),
    ("barangay","operational_incident_identity_mismatch"),
    ("missing_boundary","missing_parent_locality_boundary"),
    ("missing_srid","unsupported_or_missing_geometry_srid"),
])
def test_automatic_footprint_requires_exact_server_approved_evidence(publication_factory, monkeypatch, change, reason):
    import json
    from copy import deepcopy
    from tests.operational_footprint_fixtures import write_catalog
    from app.services import operational_footprint_evidence_service as evidence_service
    from app.services.news_publication_service import activate_operational_footprint
    factory = publication_factory
    evaluation_id, case_id, _ = seed_evaluation(factory)
    publish(factory,evaluation_id)
    record_id = register_footprint(factory,case_id,OPERATIONAL_POLYGON)
    directory = Path(os.environ["LANES_NEWS_OPERATIONAL_FOOTPRINT_DIR"])
    options = dict(geometry_srid=4326,evidence_record_id=record_id,provenance_source="synthetic:operational-test")
    polygon = deepcopy(OPERATIONAL_POLYGON)
    if change == "no_catalog": monkeypatch.delenv("LANES_NEWS_OPERATIONAL_FOOTPRINT_DIR")
    elif change == "no_record": options["evidence_record_id"] = "client-forged-current-authority"
    elif change == "source": options["provenance_source"] = "official-current-flood"
    elif change == "checksum": options["provenance_checksum"] = "f"*64
    elif change == "geometry": polygon["coordinates"][0][1][0] += .001
    elif change == "missing_srid": options["geometry_srid"] = None
    elif change == "missing_boundary":
        class NoBoundary(SyntheticLocalityProvider):
            def locality_boundary(self,claim): return None
        monkeypatch.setattr(evidence_service,"get_news_road_placement_provider", lambda: NoBoundary())
    else:
        records = json.loads((directory/"footprints.json").read_text())["records"]
        records[0][change] = ({"article_id":999999,"input_sha256":"f"*64,"claim_sha256":"f"*64,
            "incident_identity":"f"*64,"observed_at":NOW.isoformat(),"city":"City of Manila","barangay":"Unknown"}[change])
        write_catalog(directory,records)
    before = operational_counts(factory)
    with pytest.raises(NewsPublicationError,match=reason):
        with factory() as db, db.begin():
            activate_operational_footprint(db,case_id,polygon,expected_revision=1,policy=POLICY,now=NOW,
                                           sources=SOURCES,**options)
    assert operational_counts(factory) == before
    with factory() as db: assert db.get(NewsClaimCase,case_id).revision == 1


@pytest.mark.parametrize("actor_kind",["inactive","commuter","deleted"])
def test_staff_footprint_preview_and_write_recheck_stored_actor(publication_factory,actor_kind):
    factory = publication_factory
    evaluation_id,case_id,_ = seed_evaluation(factory)
    publish(factory,evaluation_id)
    actor = staff_user(factory)
    with factory() as db,db.begin():
        user = db.get(User,actor)
        if actor_kind == "inactive": user.is_active = False
        elif actor_kind == "deleted": user.deleted_at = NOW
        else:
            role = db.scalar(select(Role).where(Role.name == "Commuter"))
            if role is None:
                role = Role(name="Commuter",permissions={"reports":"full"})
                db.add(role); db.flush()
            user.role_id = role.id
    request = NewsStaffDecisionRequest(request_id=uuid4(),expected_revision=1,operation="correct",
        reason="Attempt fixture review",evaluation_id=evaluation_id,operational_footprint=OPERATIONAL_POLYGON,
        operational_footprint_srid=4326)
    before = operational_counts(factory)
    for method in (preview_staff_decision,apply_staff_decision):
        with pytest.raises(NewsPublicationError,match="unauthorized_footprint_review") as caught:
            with factory() as db,db.begin():
                method(db,case_id,request,actor_user_id=actor,policy=POLICY,now=NOW,sources=SOURCES)
        assert caught.value.status_code == 403
    assert operational_counts(factory) == before


@pytest.mark.parametrize("valid",[False,True])
def test_staff_preview_and_submit_share_containment_checks(publication_factory,valid):
    from copy import deepcopy
    factory = publication_factory
    evaluation_id,case_id,_ = seed_evaluation(factory)
    publish(factory,evaluation_id)
    actor = staff_user(factory)
    polygon = deepcopy(OPERATIONAL_POLYGON)
    if not valid:
        for point in polygon["coordinates"][0]: point[0] += .0295
    request = NewsStaffDecisionRequest(request_id=uuid4(),expected_revision=1,operation="correct",
        reason="Explicit current staff review",evaluation_id=evaluation_id,operational_footprint=polygon,
        operational_footprint_srid=4326)
    before = operational_counts(factory)
    with factory() as db:
        if valid:
            preview = preview_staff_decision(db,case_id,request,actor_user_id=actor,policy=POLICY,now=NOW,sources=SOURCES)
            assert preview.affects_routing and preview.public_state == "active_zone"
        else:
            with pytest.raises(NewsPublicationError,match="outside_parent_locality"):
                preview_staff_decision(db,case_id,request,actor_user_id=actor,policy=POLICY,now=NOW,sources=SOURCES)
    assert operational_counts(factory) == before
    with factory() as db,db.begin():
        if valid:
            decision = apply_staff_decision(db,case_id,request,actor_user_id=actor,policy=POLICY,now=NOW,sources=SOURCES)
            binding = decision.snapshot["operational_provenance"]["binding"]
            assert binding["actor_user_id"] == actor and binding["record_id"] == str(request.request_id)
            assert binding["evidence_kind"] == "staff_review" and binding["catalog_sha256"] is None
        else:
            with pytest.raises(NewsPublicationError,match="outside_parent_locality"):
                apply_staff_decision(db,case_id,request,actor_user_id=actor,policy=POLICY,now=NOW,sources=SOURCES)


def test_empty_staff_footprint_does_not_silently_become_text_correction(publication_factory):
    factory = publication_factory
    evaluation_id,case_id,_ = seed_evaluation(factory)
    publish(factory,evaluation_id)
    actor = staff_user(factory)
    request = NewsStaffDecisionRequest(request_id=uuid4(),expected_revision=1,operation="correct",
        reason="Invalid empty geometry",evaluation_id=evaluation_id,operational_footprint={},operational_footprint_srid=4326)
    before = operational_counts(factory)
    for method in (preview_staff_decision,apply_staff_decision):
        with pytest.raises(NewsPublicationError,match="invalid_geometry_syntax"):
            with factory() as db,db.begin():
                method(db,case_id,request,actor_user_id=actor,policy=POLICY,now=NOW,sources=SOURCES)
    assert operational_counts(factory) == before


@pytest.mark.parametrize("change",["no_current_extent","different_extent","changed_depth","edited_zone"])
def test_newer_article_cannot_renew_unsupported_old_footprint(publication_factory,change):
    from copy import deepcopy
    from geoalchemy2 import WKTElement
    from shapely.geometry import shape
    factory = publication_factory
    evaluation_id,case_id,article_id = seed_evaluation(factory,observed=NOW-timedelta(minutes=30))
    publish(factory,evaluation_id)
    original = staff_activation(factory,case_id,evaluation_id)
    with factory() as db:
        old = db.get(NewsClaimDecision,original)
        zone_id = old.snapshot["linked_zone_ids"][0]
        original_snapshot = deepcopy(old.snapshot)
    fresh,fresh_case,_ = seed_evaluation(factory,article_id=article_id,observed=NOW,
                                        depth="waist" if change == "changed_depth" else "knee")
    if change != "no_current_extent":
        polygon = deepcopy(OPERATIONAL_POLYGON)
        if change == "different_extent":
            for point in polygon["coordinates"][0]: point[0] += .005
        register_footprint(factory,fresh_case,polygon)
    if change == "edited_zone":
        with factory() as db,db.begin():
            polygon = deepcopy(OPERATIONAL_POLYGON)
            for point in polygon["coordinates"][0]: point[0] += .005
            db.get(FloodAvoidanceZone,zone_id).geometry = WKTElement(shape(polygon).wkt,srid=4326)
    refreshed,matched = publish(factory,fresh)
    assert matched == case_id
    with factory() as db:
        decision = db.get(NewsClaimDecision,refreshed)
        assert decision.public_state == "active_alert"
        assert decision.reason_code == "newer_observation_footprint_unverified"
        assert decision.snapshot["private_reason"] == "operational_footprint_refresh_unverified"
        assert not decision.snapshot["public"]["affects_routing"]
        assert decision.snapshot["public"]["display_geojson"] is None
        assert not db.get(FloodAvoidanceZone,zone_id).is_active
        assert db.get(NewsClaimDecision,original).snapshot == original_snapshot


@pytest.mark.parametrize("change",["different_article","edited_geometry","legacy_proof"])
def test_existing_zone_id_does_not_substitute_for_bound_incident_evidence(publication_factory,change):
    from copy import deepcopy
    from geoalchemy2 import WKTElement
    from shapely.geometry import shape
    factory = publication_factory
    evaluation_id,case_id,_ = seed_evaluation(factory)
    publish(factory,evaluation_id)
    original = staff_activation(factory,case_id,evaluation_id)
    with factory() as db,db.begin():
        old = db.get(NewsClaimDecision,original)
        zone_id = old.snapshot["linked_zone_ids"][0]
        if change == "legacy_proof":
            from app.crud.news_publication import lock_case, reserve_decision_id
            from app.models.news_publication import NewsClaimZoneLink
            from app.schemas.news_publication import NewsDecisionSnapshot
            from app.services.news_publication_service import _write
            existing = db.get(FloodAvoidanceZone,zone_id)
            legacy = FloodAvoidanceZone(geometry=existing.geometry,event_id=existing.event_id,
                is_active=True,expires_at=existing.expires_at,severity_override=existing.severity_override,
                depth_override=existing.depth_override,passable_vehicles_override=existing.passable_vehicles_override)
            db.add(legacy); db.flush()
            zone_id = legacy.id
            identity = reserve_decision_id(db)
            saved = NewsDecisionSnapshot.model_validate(old.snapshot)
            saved.operational_provenance.binding = None
            saved.linked_zone_ids = [zone_id]
            saved.public = saved.public.model_copy(update={"decision_id":identity,"revision":3})
            fixture = _write(db,lock_case(db,case_id),identity,uuid4(),saved,NOW,
                state="active_zone",review="resolved",reason="legacy_unbound_fixture",
                observed=old.observed_at,expiry=old.expires_at)
            db.add(NewsClaimZoneLink(decision_id=fixture.id,zone_id=zone_id,relation="created"))
        elif change == "edited_geometry":
            polygon = deepcopy(OPERATIONAL_POLYGON)
            for point in polygon["coordinates"][0]: point[0] += .005
            db.get(FloodAvoidanceZone,zone_id).geometry = WKTElement(shape(polygon).wkt,srid=4326)
    revision = 3 if change == "legacy_proof" else 2
    if change == "different_article":
        evaluation_id,case_id,_ = seed_evaluation(factory)
        publish(factory,evaluation_id)
        revision = 1
    before = operational_counts(factory)
    with pytest.raises(NewsPublicationError,match="operational_zone_incident_unverified"):
        staff_activation(factory,case_id,evaluation_id,expected_revision=revision,
                         operational_footprint=None,operational_zone_id=zone_id)
    assert operational_counts(factory) == before


def footprint_batch(factory,**kwargs):
    from app.services.news_footprint_worker_service import process_news_footprints
    return process_news_footprints(factory,policy=POLICY,clock=lambda:NOW,sources=SOURCES,**kwargs)


@pytest.fixture
def estimated_assets(tmp_path, monkeypatch):
    from shapely.geometry import box, mapping
    from test_news_placement_preview import service
    from test_news_road_placement import ways, write_catalog
    from app.services import news_estimated_road_service as estimated
    from app.services import operational_footprint_evidence_service as approval
    engine = service(tmp_path, city="City of Pasig")
    roads = ways()
    for road, name in zip(roads, ["Sample Road", "First Street", "Second Street"]):
        road["name"] = name
    engine.roads = write_catalog(tmp_path / "roads", roads,
        cities=[dict(name="City of Pasig", relation_id=106569, boundary=mapping(box(120.99,14.60,121.03,14.67)))])
    monkeypatch.setattr(estimated, "get_news_placement_preview_service", lambda: engine)
    monkeypatch.setattr(approval, "get_news_road_placement_provider", lambda: engine.roads)
    monkeypatch.delenv("LANES_NEWS_OPERATIONAL_FOOTPRINT_DIR")
    return engine


@pytest.mark.asyncio
async def test_worker_estimate_creates_public_zone_core_and_routing_then_expires(publication_factory, estimated_assets, monkeypatch):
    from geoalchemy2.shape import to_shape
    from app.services import news_zone_projection_service as projection
    factory = publication_factory
    evaluation, case_id, _ = seed_evaluation(factory)
    publish(factory, evaluation)
    before = operational_counts(factory)
    result = footprint_batch(factory, after_case_id=case_id-1, limit=1)
    assert result.estimated_activated == 1 and not result.skipped and not result.unresolved
    assert operational_counts(factory) == tuple(value + 1 for value in before)
    assert footprint_batch(factory, after_case_id=case_id-1, limit=1).activated == 0
    monkeypatch.setattr(projection, "utc_now", lambda: NOW)
    with factory() as db:
        decision = db.get(NewsClaimDecision, result.outcomes[0]["decision_id"])
        assert decision.snapshot["public"]["geometry_basis"] == "estimated_road_corridor"
        binding = decision.snapshot["operational_provenance"]["binding"]
        assert binding["evidence_kind"] == "estimated_news_road"
        zone = db.get(FloodAvoidanceZone, decision.snapshot["linked_zone_ids"][0])
        assert to_shape(zone.geometry).covers(to_shape(zone.source_geometry))
        response = projection.zone_responses_with_news(db, [zone])[0]
        assert response.report_geometry.type == "LineString" and response.news[0].affects_routing
        assert response.news[0].source_url.startswith("https://example.org/")
    import httpx
    from types import SimpleNamespace
    from sqlalchemy import literal
    from app.core.database import get_db
    from app.main import app
    from app.crud import report as report_crud
    from app.services import flood_routing_policy as routing
    monkeypatch.setattr(report_crud, "func", SimpleNamespace(now=lambda: literal(NOW)))
    monkeypatch.setattr(routing, "func", SimpleNamespace(now=lambda: literal(NOW), ST_AsGeoJSON=func.ST_AsGeoJSON))
    def database():
        with factory() as db:
            yield db
    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = database
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            http_response = await client.get("/api/v1/reports/active-zones")
        assert http_response.status_code == 200
        public = next(item for item in http_response.json() if item["id"] == zone.id)
        assert public["report_geometry"]["type"] == "LineString"
        assert public["news"][0]["geometry_basis"] == "estimated_road_corridor"
        assert "operational_provenance" not in public["news"][0]
        with factory() as db:
            routed = next(item for item in routing.get_active_flood_zones(db) if item.id == zone.id)
            assert routing.zone_decision("light", routed) == "blocked"
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
    with factory() as db, db.begin():
        expired = expire_case(db, case_id, now=NOW+timedelta(hours=2))
        assert expired.public_state == "expired"
    with factory() as db:
        assert not db.get(FloodAvoidanceZone, zone.id).is_active
        assert zone.id not in {item.id for item in routing.get_active_flood_zones(db)}


@pytest.mark.parametrize("changes", [{"road_segment_raw": None}, {"depth": None}])
def test_unresolved_estimate_enters_review_and_retries_without_history_spam(publication_factory, estimated_assets, changes):
    factory = publication_factory
    evaluation, case_id, _ = seed_evaluation(factory, **changes)
    publish(factory, evaluation)
    before = operational_counts(factory)
    result = footprint_batch(factory, after_case_id=case_id-1, limit=1)
    assert result.estimated_activated == 0 and result.unresolved and not result.skipped
    with factory() as db:
        decision = latest_decision(db, case_id)
        assert decision.review_state == "needs_review" and decision.revision == 2
    assert footprint_batch(factory, after_case_id=case_id-1, limit=1).estimated_considered == 0
    with factory() as db:
        assert latest_decision(db, case_id).revision == 2
    assert operational_counts(factory) == before


def test_estimate_refresh_rechecks_assets_and_keeps_existing_zone(publication_factory, estimated_assets):
    factory = publication_factory
    evaluation, case_id, article_id = seed_evaluation(factory)
    publish(factory, evaluation)
    footprint_batch(factory, after_case_id=case_id-1, limit=1)
    before = operational_counts(factory)
    newer, _, _ = seed_evaluation(factory, article_id=article_id, observed=NOW-timedelta(minutes=1))
    _, refreshed_case = publish(factory, newer)
    assert refreshed_case == case_id
    with factory() as db:
        decision = latest_decision(db, case_id)
        assert decision.public_state == "active_zone"
        assert decision.snapshot["public"]["geometry_basis"] == "estimated_road_corridor"
        assert decision.snapshot["operational_provenance"]["binding"]["observed_at"].startswith("2026-10-05T02:59")
    assert operational_counts(factory) == (before[0], before[1], before[2]+1)


def test_parallel_estimate_workers_do_not_duplicate_zone(publication_factory, estimated_assets):
    from concurrent.futures import ThreadPoolExecutor
    factory = publication_factory
    evaluation, case_id, _ = seed_evaluation(factory, observed=NOW)
    publish(factory, evaluation)
    before = operational_counts(factory)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: footprint_batch(factory, after_case_id=case_id-1, limit=1), range(2)))
    assert all(not result.skipped for result in results)
    assert operational_counts(factory) == tuple(value+1 for value in before)


def test_changed_noah_extent_cannot_silently_refresh_old_estimate(publication_factory, estimated_assets, tmp_path):
    from shapely.geometry import box
    from test_news_placement_preview import noah_catalog
    factory = publication_factory
    evaluation, case_id, article_id = seed_evaluation(factory)
    publish(factory, evaluation)
    footprint_batch(factory, after_case_id=case_id-1, limit=1)
    with factory() as db:
        zone_id = latest_decision(db, case_id).snapshot["linked_zone_ids"][0]
    estimated_assets.noah = noah_catalog(tmp_path / "changed_noah", box(120.999,14.6304,121.001,14.632))
    newer, _, _ = seed_evaluation(factory, article_id=article_id, observed=NOW-timedelta(minutes=1))
    publish(factory, newer)
    with factory() as db:
        decision = latest_decision(db, case_id)
        assert decision.public_state == "active_alert"
        assert decision.snapshot["private_reason"] == "estimated_road_extent_changed"
        assert not db.get(FloodAvoidanceZone, zone_id).is_active


def test_estimate_flag_cannot_approve_tampered_geometry(publication_factory, estimated_assets):
    import json
    from app.services.news_estimated_road_service import build_estimated_road_zone
    from app.services.news_publication_service import activate_operational_footprint
    factory = publication_factory
    evaluation, case_id, _ = seed_evaluation(factory, observed=NOW)
    publish(factory, evaluation)
    with factory() as db:
        source = db.get(NewsClaimSource, latest_decision(db, case_id).snapshot["claim_source_id"])
        claim = ExtractedClaim.model_validate(db.get(NewsExtractionRun, source.extraction_run_id).result["claims"][0])
    estimate = build_estimated_road_zone(claim)
    changed = json.loads(json.dumps(estimate.geometry))
    for point in changed["coordinates"][0]:
        point[0] += .0001
    before = operational_counts(factory)
    with pytest.raises(NewsPublicationError, match="estimated_road_evidence_mismatch"):
        with factory() as db, db.begin():
            activate_operational_footprint(db, case_id, changed, expected_revision=1,
                provenance_source=estimate.source_id, provenance_checksum=estimate.checksum,
                geometry_srid=4326, estimated_road=True, policy=POLICY, now=NOW, sources=SOURCES)
    assert operational_counts(factory) == before


def test_worker_activates_exact_approved_case_and_retry_creates_no_duplicate_zone(publication_factory):
    factory=publication_factory
    evaluation,case_id,_=seed_evaluation(factory)
    publish(factory,evaluation)
    register_footprint(factory,case_id,OPERATIONAL_POLYGON)
    before=operational_counts(factory)
    summary=footprint_batch(factory)
    assert summary.activated == 1 and not summary.skipped
    assert summary.outcomes[0]["case_id"] == case_id
    assert operational_counts(factory)==tuple(value+1 for value in before)
    assert footprint_batch(factory).activated == 0
    assert operational_counts(factory)==tuple(value+1 for value in before)
    with factory() as db:
        current=db.get(NewsClaimCase,case_id)
        assert current.revision==2
        decision=db.get(NewsClaimDecision,summary.outcomes[0]["decision_id"])
        assert decision.snapshot["operational_provenance"]["binding"]["evidence_kind"] == "authoritative_current_incident"
        assert decision.actor_user_id is None


@pytest.mark.parametrize("kind",["unconfigured","invalid","missing_record"])
def test_worker_retains_alert_without_approved_assets(publication_factory,monkeypatch,kind):
    factory=publication_factory
    evaluation,case_id,_=seed_evaluation(factory)
    alert,_=publish(factory,evaluation)
    if kind=="unconfigured": monkeypatch.delenv("LANES_NEWS_OPERATIONAL_FOOTPRINT_DIR")
    elif kind=="invalid":
        Path(os.environ["LANES_NEWS_OPERATIONAL_FOOTPRINT_DIR"],"manifest.json").write_text("bad")
    else:
        from tests.operational_footprint_fixtures import write_catalog
        write_catalog(Path(os.environ["LANES_NEWS_OPERATIONAL_FOOTPRINT_DIR"]),[])
    before=operational_counts(factory)
    summary=footprint_batch(factory)
    assert summary.activated==0 and operational_counts(factory)==before
    assert bool(summary.skipped)==(kind=="invalid")
    with factory() as db:
        assert db.get(NewsClaimCase,case_id).revision==(1 if kind=="invalid" else 2)
        assert db.get(NewsClaimDecision,alert).public_state=="active_alert"


@pytest.mark.parametrize("choice",["correct","reject","defer"])
def test_worker_cannot_override_staff_choices(publication_factory,choice):
    factory=publication_factory
    evaluation,case_id,_=seed_evaluation(factory)
    publish(factory,evaluation)
    register_footprint(factory,case_id,OPERATIONAL_POLYGON)
    request=NewsStaffDecisionRequest(request_id=uuid4(),expected_revision=1,operation=choice,
        reason="Explicit staff choice",evaluation_id=evaluation if choice=="correct" else None,
        deferred_until=NOW+timedelta(hours=1) if choice=="defer" else None)
    actor=staff_user(factory)
    with factory() as db,db.begin():
        apply_staff_decision(db,case_id,request,actor_user_id=actor,policy=POLICY,now=NOW,sources=SOURCES)
    before=operational_counts(factory)
    assert footprint_batch(factory).activated==0
    assert operational_counts(factory)==before


def test_worker_filters_missing_footprints_before_applying_batch_limit(publication_factory):
    factory=publication_factory
    for _ in range(3):
        evaluation,_,_=seed_evaluation(factory)
        publish(factory,evaluation)
    evaluation,case_id,_=seed_evaluation(factory)
    publish(factory,evaluation)
    register_footprint(factory,case_id,OPERATIONAL_POLYGON)
    summary=footprint_batch(factory,limit=1)
    assert summary.activated==1 and summary.next_after_case_id==case_id
    assert footprint_batch(factory,limit=1,after_case_id=case_id).next_after_case_id==0


def test_worker_reports_ambiguous_records_without_guessing(publication_factory):
    from copy import deepcopy
    factory=publication_factory
    evaluation,case_id,_=seed_evaluation(factory)
    publish(factory,evaluation)
    register_footprint(factory,case_id,OPERATIONAL_POLYGON)
    other=deepcopy(OPERATIONAL_POLYGON)
    for point in other["coordinates"][0]: point[0]+=.005
    register_footprint(factory,case_id,other)
    before=operational_counts(factory)
    summary=footprint_batch(factory)
    assert summary.activated==0 and summary.skipped==[{"case_id":case_id,"reason_code":"ambiguous_operational_footprint_records"}]
    assert operational_counts(factory)==before


@pytest.mark.parametrize("failure",["validation","storage"])
def test_worker_rolls_back_failed_claim_and_continues_next_claim(publication_factory,monkeypatch,failure):
    from sqlalchemy.exc import SQLAlchemyError
    from app.services import news_footprint_worker_service as worker
    factory=publication_factory
    cases=[]
    for _ in range(2):
        evaluation,case_id,_=seed_evaluation(factory)
        publish(factory,evaluation)
        register_footprint(factory,case_id,OPERATIONAL_POLYGON)
        cases.append(case_id)
    original=worker.activate_operational_footprint
    def interrupted(db,case_id,*args,**kwargs):
        result=original(db,case_id,*args,**kwargs)
        if case_id==cases[0]:
            if failure=="storage": raise SQLAlchemyError("synthetic private details must not leak")
            raise NewsPublicationError("synthetic_approval_changed")
        return result
    monkeypatch.setattr(worker,"activate_operational_footprint",interrupted)
    before=operational_counts(factory)
    summary=footprint_batch(factory,limit=1)
    assert summary.activated==1 and summary.outcomes[0]["case_id"]==cases[1]
    assert summary.skipped==[{"case_id":cases[0],"reason_code":"footprint_storage_unavailable" if failure=="storage" else "synthetic_approval_changed"}]
    assert operational_counts(factory)==tuple(value+1 for value in before)
    with factory() as db: assert db.get(NewsClaimCase,cases[0]).revision==1


def test_parallel_footprint_workers_create_one_operational_result(publication_factory):
    from concurrent.futures import ThreadPoolExecutor
    factory=publication_factory
    evaluation,case_id,_=seed_evaluation(factory)
    publish(factory,evaluation)
    register_footprint(factory,case_id,OPERATIONAL_POLYGON)
    before=operational_counts(factory)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:footprint_batch(factory),range(2)))
    assert all(not result.skipped for result in results)
    assert operational_counts(factory)==tuple(value+1 for value in before)


def test_restart_safe_seed_skips_completed_handoffs_and_empty_claim_runs(publication_factory):
    from app.services.news_evaluation_service import seed_claim_evaluations
    factory=publication_factory
    old,_,_=seed_evaluation(factory)
    seed_evaluation(factory,bind=False,extraction_result_changes={"claims":[]})
    seed_evaluation(factory,bind=False)
    first=seed_claim_evaluations(factory,POLICY,now=NOW,limit=1,unbound_only=True,sources=SOURCES)
    assert first.evaluations_created==1
    second_run,_,_=seed_evaluation(factory,bind=False)
    second=seed_claim_evaluations(factory,POLICY,now=NOW,limit=1,unbound_only=True,sources=SOURCES)
    assert second.evaluations_created==1 and second.next_after_run_id==second_run


@pytest.mark.asyncio
async def test_saved_pipeline_commits_zone_retries_and_expires_on_native_postgis(publication_factory,monkeypatch):
    """Real storage/stage handoffs; extraction/auditor/extent remain synthetic."""
    from types import SimpleNamespace
    import json
    from app.crud import news_processing as queue
    from app.services import news_processing_service as processing
    from app.services import news_evaluation_service as evaluation
    from app.services import news_pipeline_service as pipeline
    factory=publication_factory
    _,reference_case,reference_article=seed_evaluation(factory)
    with factory() as db,db.begin():
        original=db.get(NewsArticle,reference_article)
        source=db.scalar(select(NewsClaimSource).where(NewsClaimSource.case_id==reference_case))
        extraction=NewsExtractionResult.model_validate(db.get(NewsExtractionRun,source.extraction_run_id).result)
        saved=NewsArticle(canonical_url=f"https://example.org/pipeline/{uuid4()}",publisher_source_id="fixture",
            title=original.title,article_text=original.article_text,published_at=NOW,excerpt="",content_fingerprint="0"*64)
        db.add(saved)
        db.flush()
        article_id=saved.id

    def capture_target(db,limit):
        # Restrict fixture admission; all queue leases/commits are real.
        return int(queue.enqueue_article(db,db.get(NewsArticle,article_id)) is not None)
    async def fixture_extract(article):
        assert article.article_id==article_id
        return SimpleNamespace(error=None,extraction=extraction.model_copy(update={
            "article_id":article.article_id,"canonical_url":article.canonical_url}))
    class FixtureAuditor:
        def policy_identity(self): return IDENTITY
        async def audit(self,claim,article,**kwargs):
            if article.article_id==article_id:
                with factory() as db:
                    source=db.scalar(select(NewsClaimSource).join(NewsExtractionRun,
                        NewsExtractionRun.id==NewsClaimSource.extraction_run_id).join(NewsArticleVersion,
                        NewsArticleVersion.id==NewsExtractionRun.article_version_id)
                        .where(NewsArticleVersion.article_id==article_id))
                    case_id=source.case_id
                # Simulates separately provisioned operator evidence, no guess.
                register_footprint(factory,case_id,OPERATIONAL_POLYGON)
            return IndependentAuditResult(outcome="verified",reason_code="claim_evidence_verified",provider="openrouter",
                model="fixture/model",prompt_version=IDENTITY["prompt_version"],response_version=IDENTITY["response_version"],
                input_sha256=extraction_input_snapshot(article)[1],claim_sha256=canonical_claim_sha256(claim),
                evidence=ProviderClaimAudit.model_validate_json(json.dumps(evidence(claim,article))))
    for module in (queue,processing,evaluation):
        monkeypatch.setattr(module,"current_pipeline_version",lambda:POLICY.pipeline_version)
    monkeypatch.setattr(processing,"capture_pending_inputs",capture_target)
    monkeypatch.setattr(processing,"extract_captured_news_article",fixture_extract)
    monkeypatch.setattr(pipeline,"evaluation_policy",lambda _:POLICY)
    before=operational_counts(factory)
    result=await pipeline.run_news_pipeline(factory,limit=200,auditor=FixtureAuditor(),sources=SOURCES,
        unbound_only=True,clock=lambda:NOW)
    assert result["extraction"]["completed"]==1
    assert result["footprints"]["activated"]==1, result
    assert operational_counts(factory)==tuple(value+1 for value in before)
    with factory() as db:
        source=db.scalar(select(NewsClaimSource).join(NewsExtractionRun,
            NewsExtractionRun.id==NewsClaimSource.extraction_run_id).join(NewsArticleVersion,
            NewsArticleVersion.id==NewsExtractionRun.article_version_id)
            .where(NewsArticleVersion.article_id==article_id))
        current=db.scalar(select(NewsClaimDecision).where(NewsClaimDecision.case_id==source.case_id)
            .order_by(NewsClaimDecision.revision.desc()))
        assert current.public_state=="active_zone"
        zone_id=current.snapshot["linked_zone_ids"][0]
        case_id=source.case_id
    retry=await pipeline.run_news_pipeline(factory,limit=200,auditor=FixtureAuditor(),sources=SOURCES,
        unbound_only=True,clock=lambda:NOW)
    assert retry["extraction"]["completed"]==retry["footprints"]["activated"]==0
    assert operational_counts(factory)==tuple(value+1 for value in before)
    expired=await pipeline.run_news_pipeline(factory,limit=200,auditor=FixtureAuditor(),sources=SOURCES,
        unbound_only=True,clock=lambda:NOW+timedelta(hours=2))
    assert expired["publication"]["expired"]>=1
    with factory() as db:
        zone=db.get(FloodAvoidanceZone,zone_id)
        assert not zone.is_active and db.get(FloodEvent,zone.event_id).status=="ended"
        current=db.scalar(select(NewsClaimDecision).where(NewsClaimDecision.case_id==case_id)
            .order_by(NewsClaimDecision.revision.desc()))
        assert current.public_state=="expired" and public_projection(current,NOW+timedelta(hours=2)).status=="Unconfirmed"
