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
from app.crud.news_publication import NewsPublicationError
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
                    depth="knee", status="completed", body_suffix="", **changes):
    observed = observed or NOW - timedelta(minutes=5)
    raw_depth = "knee deep" if depth else None
    wording = "was flooded knee deep" if condition == "active" else "floodwaters subsided"
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
        run = NewsExtractionRun(article_version_id=version.id, pipeline_version=policy.pipeline_version,
            status="completed", completed_at=NOW, result=result.model_dump(mode="json"))
        db.add(run)
        db.flush()
        bind_completed_run(db, run.id, policy.fingerprint, NOW)
        source = db.scalar(select(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run.id))
        owned = claim_due_evaluation(db, NOW, policy_fingerprint=policy.fingerprint, run_id=run.id)
        response = evidence(value, article)
        if value.depth_raw is None:
            response["depth"] = {"confirmed": False, "evidence": [], "canonical": None, "raw": None, "qualifiers": []}
        audit = IndependentAuditResult(outcome="verified", reason_code="claim_evidence_verified", provider="openrouter",
            model="fixture/model", prompt_version=IDENTITY["prompt_version"], response_version=IDENTITY["response_version"],
            input_sha256=fingerprint, claim_sha256=source.claim_sha256,
            evidence=ProviderClaimAudit.model_validate_json(__import__("json").dumps(response)))
        evaluated = {"schema_version": "independent-claim-evaluation-v1", "policy_fingerprint": policy.fingerprint,
            "policy_identity": policy.auditor_identity, "input_sha256": fingerprint, "claim_sha256": source.claim_sha256,
            "reason_code": "claim_evidence_verified", "audit": audit.model_dump(mode="json")}
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
            provenance_source="field_survey:drrmo_pasig",
            policy=POLICY,
            now=NOW,
            actor_user_id=actor,
            sources=SOURCES,
        )
        assert decision.public_state == "active_zone"
        assert decision.review_state == "resolved"
        assert decision.reason_code == "verified_operational_footprint"

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
            provenance_source="field_survey:drrmo_pasig",
            policy=POLICY,
            now=NOW,
            actor_user_id=actor,
            sources=SOURCES,
        )
        zone_id = act_dec.snapshot["linked_zone_ids"][0]
        initial_expiry = db.get(FloodAvoidanceZone, zone_id).expires_at

    # Newer observation from revised article
    fresh, _, _ = seed_evaluation(factory, article_id=article_id, observed=NOW, body_suffix=" Water still rising.")
    fresh_dec_id, refreshed_case_id = publish(factory, fresh)
    assert refreshed_case_id == case_id

    with factory() as db:
        fresh_dec = db.get(NewsClaimDecision, fresh_dec_id)
        assert fresh_dec.public_state == "active_zone"
        assert fresh_dec.reason_code == "newer_matched_flood_observation"
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

