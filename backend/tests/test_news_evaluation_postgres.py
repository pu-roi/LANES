"""Native lease/idempotency tests; only a fresh disposable loopback DB is allowed."""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from threading import Barrier
from uuid import uuid4

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, func, inspect, select, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker

from app.crud.news_evaluation import bind_completed_run, claim_due_evaluation, finish_owned_evaluation
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimEvaluation, NewsClaimSource
from app.models.report import FloodAvoidanceZone, FloodReport
from app.schemas.news_audit import IndependentAuditResult
from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput, NewsExtractionResult
from app.services.news_claim_auditor import AuditorConfig, NewsClaimAuditor, canonical_claim_sha256
from app.services.news_discovery_service import extraction_input_snapshot
from app.services.news_evaluation_service import EvaluationPolicy, evaluate_news_claims, evaluation_policy, seed_claim_evaluations
from app.services.news_sources import NewsSource
from tests.test_news_evaluation import claim
from tests.test_news_claim_auditor import evidence, reply

NOW = datetime(2026, 10, 5, 3, tzinfo=timezone.utc)
POLICY = EvaluationPolicy("a" * 64, "evaluation-fixture", {"provider": "fixture", "model": "fixture"})
SOURCES = (NewsSource("fixture", "Fixture", ("example.org",), ("https://example.org/feed",), NOW.date(), True),)


@pytest.fixture(scope="module")
def factory():
    url = os.environ.get("LANES_NEWS_EVALUATION_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Fresh disposable local PostgreSQL evaluation DB required")
    parsed = make_url(url)
    assert parsed.host in ("localhost", "127.0.0.1", "::1")
    assert (parsed.database or "").startswith("lanes_evaluation_test_")
    from app.core.config import settings
    patch = pytest.MonkeyPatch()
    patch.setattr(settings, "DATABASE_URL", url)
    engine = create_engine(url)
    assert not inspect(engine).get_table_names(), "Refusing a nonempty evaluation database"
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    try:
        command.upgrade(config, "head")
        yield sessionmaker(bind=engine)
    finally:
        engine.dispose()
        patch.undo()


def seed(factory, *, published_at=NOW, source_id="fixture", **changes):
    body = "C5 in Pasig City is flooded, knee-deep as of 10:55 AM on October 5, 2026."
    value = claim(**{"evidence_sentence": body, "evidence_sentence_offset": (0, len(body)), **changes})
    with factory() as db, db.begin():
        url = f"https://example.org/flood/{uuid4()}"
        row = NewsArticle(canonical_url=url, publisher_source_id=source_id, title="Flood",
                          excerpt="", article_text=body, published_at=published_at, content_fingerprint="0" * 64)
        db.add(row)
        db.flush()
        article = NewsArticleExtractorInput(article_id=row.id, publisher=source_id, title="Flood", excerpt="",
            article_text=body, published_at=published_at, canonical_url=url)
        snapshot, digest = extraction_input_snapshot(article)
        version = NewsArticleVersion(article_id=row.id, input_snapshot=snapshot, input_fingerprint=digest)
        db.add(version)
        db.flush()
        result = NewsExtractionResult(article_id=row.id, canonical_url=url, is_metadata_only=False,
                                      processed_text_length=len(body), claims=[value])
        run = NewsExtractionRun(article_version_id=version.id, pipeline_version=POLICY.pipeline_version,
                                status="completed", completed_at=NOW, result=result.model_dump(mode="json"))
        db.add(run)
        db.flush()
        return run.id, result.model_dump(mode="json")


def bind(factory, run_id, fingerprint=POLICY.fingerprint):
    with factory() as db, db.begin():
        return bind_completed_run(db, run_id, fingerprint, NOW)


def seed_many(factory, count=26, ineligible=0):
    from tests.test_news_batch_audit import sample
    candidates, article = sample(count)
    candidates = tuple(c.model_copy(update={"claim": c.claim.model_copy(update={"is_forecast": True})})
        if i < ineligible else c for i, c in enumerate(candidates))
    article.publisher = "fixture"
    article.published_at = datetime(2026, 10, 5, 7, 1, tzinfo=timezone.utc)
    article.canonical_url = f"https://example.org/flood/{uuid4()}"
    with factory() as db, db.begin():
        row = NewsArticle(canonical_url=article.canonical_url, publisher_source_id="fixture", title=article.title,
            excerpt="", article_text=article.article_text, published_at=article.published_at, content_fingerprint="0"*64)
        db.add(row)
        db.flush()
        article.article_id = row.id
        snapshot, digest = extraction_input_snapshot(article)
        version = NewsArticleVersion(article_id=row.id, input_snapshot=snapshot, input_fingerprint=digest)
        db.add(version)
        db.flush()
        result = NewsExtractionResult(article_id=row.id, canonical_url=article.canonical_url,
            is_metadata_only=False, processed_text_length=len(article.article_text), claims=[c.claim for c in candidates])
        run = NewsExtractionRun(article_version_id=version.id, pipeline_version=POLICY.pipeline_version,
            status="completed", completed_at=NOW, result=result.model_dump(mode="json"))
        db.add(run)
        db.flush()
        return run.id, article, {canonical_claim_sha256(c.claim): c.claim for c in candidates}


@pytest.mark.parametrize("remaining", [50, 0, None])
@pytest.mark.parametrize("ineligible", [0, 7])
def test_batch_requests_and_zero_quota_preserve_individual_rows(factory, monkeypatch, remaining, ineligible):
    import json
    from tests.test_news_batch_audit import rows
    from app.schemas.news_audit_batch import AuditCandidate
    run_id, article, claims = seed_many(factory, count=26+ineligible, ineligible=ineligible)
    service = NewsClaimAuditor(AuditorConfig(provider="openrouter", model="openrouter/free", openrouter_api_key=str(uuid4())))
    policy = EvaluationPolicy(str(uuid4()).replace("-", "")*2, POLICY.pipeline_version, service.policy_identity())
    now = datetime(2026, 10, 5, 7, 5, tzinfo=timezone.utc)
    bind(factory, run_id, policy.fingerprint)
    monkeypatch.setattr("app.services.news_evaluation_service.current_pipeline_version", lambda: POLICY.pipeline_version)
    post_sizes, gets = [], []
    def transport(request):
        if request.method == "GET":
            gets.append(request)
            return httpx.Response(200, json={"data": {"free_model_daily_requests": {
                "used": 50-remaining, "limit": 50, "remaining": remaining}}} if remaining is not None else {"data": {}})
        assert remaining is not None, "Unconfirmed allowance must not dispatch a POST"
        document = json.loads(json.loads(request.content)["messages"][1]["content"])
        candidates = tuple(AuditCandidate(candidate_id=c["candidate_id"],
            claim=next(value for value in claims.values() if value.raw_place_name == c["claim"]["raw_place_name"]))
            for c in document["candidates"])
        post_sizes.append(len(candidates))
        return reply({"results": rows(candidates, article)[::-1]})
    async def execute():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            return await evaluate_news_claims(factory, run_id=run_id, auditor=service, policy=policy,
                sources=SOURCES, clock=lambda: now, client=client)
    summary = asyncio.run(execute())
    assert len(gets) == 1
    with factory() as db:
        evaluations = db.scalars(select(NewsClaimEvaluation).join(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run_id)).all()
        assert len(evaluations) == 26+ineligible
        rejected = [e for e in evaluations if e.result and e.result.get("reason_code") == "forecast_claim"]
        assert len(rejected) == ineligible and all(e.attempt_count == 0 for e in rejected)
        dispatched_rows = [e for e in evaluations if e not in rejected]
        if remaining:
            assert post_sizes == [8, 8, 8, 2]
            assert summary.request_count == 4 and summary.claims_dispatched == 26 and summary.completed == 26+ineligible
            assert all(e.status == "completed" and e.attempt_count == 1 and e.result["audit"]["outcome"] == "verified" for e in dispatched_rows)
        else:
            assert not post_sizes and summary.quota_deferred == 26
            assert all(e.status == "retry_wait" and e.attempt_count == 0 for e in dispatched_rows)
            assert summary.request_count == summary.claims_dispatched == 0
            if remaining is None:
                assert all(e.error_code == "auditor_quota_unknown" for e in dispatched_rows)
    repeated = asyncio.run(execute())
    assert not repeated.evaluations and len(post_sizes) == (4 if remaining else 0)


def test_429_stops_cycle_and_saves_safe_diagnostics_for_dispatched_claims(factory, monkeypatch):
    import json
    run_id, _, _ = seed_many(factory)
    service = NewsClaimAuditor(AuditorConfig(provider="openrouter", model="openrouter/free", openrouter_api_key=str(uuid4())))
    policy = EvaluationPolicy(uuid4().hex*2, POLICY.pipeline_version, service.policy_identity())
    now = datetime(2026, 10, 5, 7, 5, tzinfo=timezone.utc)
    bind(factory, run_id, policy.fingerprint)
    monkeypatch.setattr("app.services.news_evaluation_service.current_pipeline_version", lambda: POLICY.pipeline_version)
    requests = []
    def transport(request):
        if request.method == "GET":
            return httpx.Response(200, json={"data": {"free_model_daily_requests": {"used": 0, "limit": 50, "remaining": 50}}})
        requests.append(request)
        return httpx.Response(429, headers={"retry-after": "600", "x-request-id": "fixture-429"},
            json={"error": {"message": "unrestricted provider text and secret must never be saved"}})
    async def execute():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            return await evaluate_news_claims(factory, run_id=run_id, auditor=service, policy=policy,
                sources=SOURCES, clock=lambda: now, client=client)
    summary = asyncio.run(execute())
    assert len(requests) == summary.request_count == 1 and summary.claims_dispatched == 8
    assert summary.retry_wait == 26 and summary.quota_deferred == 18
    with factory() as db:
        rows = db.scalars(select(NewsClaimEvaluation).join(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run_id)
            .order_by(NewsClaimEvaluation.id)).all()
        assert sorted(e.attempt_count for e in rows) == [0]*18+[1]*8
        assert all(e.status == "retry_wait" and e.next_attempt_at == now+timedelta(seconds=600) for e in rows[:8])
        assert rows[0].result["diagnostic"]["provider_http_status"] == 429
        assert rows[0].result["diagnostic"]["provider_request_id"] == "fixture-429"
        assert "unrestricted" not in json.dumps([e.result for e in rows])
    assert not asyncio.run(execute()).evaluations


def test_dispatch_lock_stops_concurrent_worker_without_consuming_attempt(factory, monkeypatch):
    from app.services.news_audit_quota_service import audit_dispatch_lock
    run_id, _ = seed(factory)
    bind(factory, run_id)
    with audit_dispatch_lock(factory) as held:
        assert held
        result = asyncio.run(evaluate_news_claims(factory, run_id=run_id, auditor=FakeAuditor(factory, run_id),
            policy=POLICY, sources=SOURCES, clock=lambda: NOW))
    assert result.error_code == "auditor_already_running" and not result.evaluations
    with factory() as db:
        row = db.scalar(select(NewsClaimEvaluation).join(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run_id))
        assert row.status == "pending" and row.attempt_count == 0


@pytest.mark.parametrize("elapsed_budget", [False, True])
def test_owned_cycle_reuses_client_and_defers_undispatched_claims_without_attempts(factory, monkeypatch, elapsed_budget):
    import json
    from types import SimpleNamespace
    from tests.test_news_batch_audit import rows
    from app.schemas.news_audit_batch import AuditCandidate
    run_id, article, claims = seed_many(factory, count=64)
    service = NewsClaimAuditor(AuditorConfig(provider="openrouter", model="openrouter/free", openrouter_api_key=uuid4().hex))
    policy = EvaluationPolicy(uuid4().hex*2, POLICY.pipeline_version, service.policy_identity())
    bind(factory, run_id, policy.fingerprint)
    monkeypatch.setattr("app.services.news_evaluation_service.current_pipeline_version", lambda: POLICY.pipeline_version)
    if elapsed_budget:
        ticks = iter([0]+[400]*20)
        monkeypatch.setattr("app.services.news_evaluation_service.time", SimpleNamespace(monotonic=lambda: next(ticks)))
    requests, clients, progress = [], [], []
    def transport(request):
        requests.append(request.method)
        if request.method == "GET":
            return httpx.Response(200, json={"data": {"free_model_daily_requests": {"used": 0, "limit": 50, "remaining": 50}}})
        document = json.loads(json.loads(request.content)["messages"][1]["content"])
        candidates = tuple(AuditCandidate(candidate_id=c["candidate_id"],
            claim=next(value for value in claims.values() if value.raw_place_name == c["claim"]["raw_place_name"]))
            for c in document["candidates"])
        return reply({"results": rows(candidates, article)})
    original_client = httpx.AsyncClient
    def make_client(**kwargs):
        client = original_client(transport=httpx.MockTransport(transport), **kwargs)
        clients.append(client)
        return client
    monkeypatch.setattr("app.services.news_evaluation_service.httpx.AsyncClient", make_client)
    summary = asyncio.run(evaluate_news_claims(factory, limit=100, run_id=run_id, auditor=service, policy=policy,
        sources=SOURCES, clock=lambda: datetime(2026, 10, 5, 7, 5, tzinfo=timezone.utc), on_progress=progress.append))
    dispatched_count = 0 if elapsed_budget else 48
    assert len(clients) == 1 and clients[0].is_closed
    assert requests.count("GET") == 1 and requests.count("POST") == dispatched_count//8
    assert summary.completed == dispatched_count and summary.budget_deferred == 64-dispatched_count
    assert len(progress) == dispatched_count//8
    with factory() as db:
        values = db.scalars(select(NewsClaimEvaluation).join(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run_id)).all()
        assert sum(row.attempt_count for row in values) == dispatched_count
        assert all(row.status == "retry_wait" and row.attempt_count == 0
            for row in values if row.error_code == "auditor_cycle_deferred")


@pytest.mark.parametrize("http_status", [200, 500])
def test_oversized_groups_split_before_dispatch_and_failures_never_fan_out(factory, monkeypatch, http_status):
    import json
    from app.schemas.news_audit_batch import AuditCandidate
    from tests.test_news_batch_audit import rows
    run_id, article, claims = seed_many(factory, count=8)
    class SmallRequestAuditor(NewsClaimAuditor):
        def batch_document(self, candidates, article):
            document = super().batch_document(candidates, article)
            if len(candidates) > 3:
                raise ValueError("audit_input_oversized")
            return document
    service = SmallRequestAuditor(AuditorConfig(provider="openrouter", model="openrouter/free", openrouter_api_key=uuid4().hex))
    policy = EvaluationPolicy(uuid4().hex*2, POLICY.pipeline_version, service.policy_identity())
    bind(factory, run_id, policy.fingerprint)
    monkeypatch.setattr("app.services.news_evaluation_service.current_pipeline_version", lambda: POLICY.pipeline_version)
    sizes = []
    def transport(request):
        if request.method == "GET":
            return httpx.Response(200, json={"data": {"free_model_daily_requests": {"used": 0, "limit": 50, "remaining": 50}}})
        document = json.loads(json.loads(request.content)["messages"][1]["content"])
        candidates = tuple(AuditCandidate(candidate_id=c["candidate_id"],
            claim=next(value for value in claims.values() if value.raw_place_name == c["claim"]["raw_place_name"]))
            for c in document["candidates"])
        sizes.append(len(candidates))
        return reply({"results": rows(candidates, article)}) if http_status == 200 else httpx.Response(500)
    async def execute():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            return await evaluate_news_claims(factory, run_id=run_id, auditor=service, policy=policy, sources=SOURCES,
                clock=lambda: datetime(2026, 10, 5, 7, 5, tzinfo=timezone.utc), client=client)
    summary = asyncio.run(execute())
    expected = [2, 2, 2, 2] if http_status == 200 else [2, 2]
    assert sizes == expected and summary.request_count == len(expected) and summary.claims_dispatched == sum(expected)
    assert summary.completed == (8 if http_status == 200 else 0)
    assert summary.retry_wait == (0 if http_status == 200 else 8)
    with factory() as db:
        attempts = db.scalars(select(NewsClaimEvaluation.attempt_count).join(NewsClaimSource)
            .where(NewsClaimSource.extraction_run_id == run_id)).all()
        assert sorted(attempts) == ([1]*8 if http_status == 200 else [0]*4+[1]*4)
    assert summary.availability_deferred == (0 if http_status == 200 else 4)


@pytest.mark.parametrize("error_code", ["auditor_daily_quota_exhausted", "auditor_quota_unknown", "auditor_quota_unavailable"])
def test_quota_cooldown_alone_does_not_wake_controller_but_evidence_maintenance_does(factory, monkeypatch, error_code):
    from app.crud.news_weather import pending_pipeline_work
    from app.schemas.configuration import OperationalSettings
    from app.schemas.news_audit import AuditQuotaState
    from app.services.news_audit_quota_service import quota_identity, save_quota, real_now
    source_id = "fixture-"+uuid4().hex
    run_id, _ = seed(factory, source_id=source_id)
    fingerprint = uuid4().hex*2
    bind(factory, run_id, fingerprint)
    service = NewsClaimAuditor(AuditorConfig(provider="openrouter", model="openrouter/free", openrouter_api_key=uuid4().hex))
    monkeypatch.setattr("app.services.news_claim_auditor.NewsClaimAuditor", lambda: service)
    monkeypatch.setattr("app.crud.news_processing.current_pipeline_version", lambda: POLICY.pipeline_version)
    save_quota(factory, AuditQuotaState(identity=quota_identity(service), remaining=0,
        blocked_until=(real_now()+timedelta(minutes=30)).isoformat()))
    with factory() as db, db.begin():
        owned = claim_due_evaluation(db, NOW, policy_fingerprint=fingerprint, run_id=run_id, count_attempt=False)
        assert finish_owned_evaluation(db, owned, NOW, error_code=error_code,
            retryable=True, retry_at=NOW)
    config = OperationalSettings(news_publication_enabled=False)
    with factory() as db:
        assert not pending_pipeline_work(db, NOW, config, (source_id,), policy_fingerprint=fingerprint, admission_age=timedelta(hours=12))
        row = db.get(NewsClaimEvaluation, owned.evaluation_id)
        row.error_code = "auditor_quota_evidence_due"
        db.commit()
        assert pending_pipeline_work(db, NOW, config, (source_id,), policy_fingerprint=fingerprint, admission_age=timedelta(hours=12))


def test_repeat_and_changed_policy_preserve_source_and_terminal_history(factory):
    run_id, result = seed(factory)
    assert bind(factory, run_id) == (1, 1)
    assert bind(factory, run_id) == (0, 0)
    with factory() as db, db.begin():
        leased = claim_due_evaluation(db, NOW, policy_fingerprint=POLICY.fingerprint, run_id=run_id)
        assert finish_owned_evaluation(db, leased, NOW, result={"audit": "review"})
    assert bind(factory, run_id, "b" * 64) == (0, 1)
    with factory() as db:
        rows = db.scalars(select(NewsClaimEvaluation).join(NewsClaimSource).where(
            NewsClaimSource.extraction_run_id == run_id).order_by(NewsClaimEvaluation.id)).all()
        assert [row.status for row in rows] == ["completed", "pending"]
        assert db.get(NewsExtractionRun, run_id).result == result
    with pytest.raises(DBAPIError, match="immutable"):
        with factory() as db, db.begin():
            db.execute(update(NewsClaimEvaluation).where(NewsClaimEvaluation.id == leased.evaluation_id)
                       .values(result={"replaced": True}))


def test_concurrent_binding_has_one_case_source_and_evaluation(factory):
    run_id, _ = seed(factory)
    barrier = Barrier(2)

    def worker():
        barrier.wait(timeout=10)
        return bind(factory, run_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        one, two = pool.submit(worker), pool.submit(worker)
        assert sorted([one.result(timeout=30), two.result(timeout=30)]) == [(0, 0), (1, 1)]
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(NewsClaimSource).where(
            NewsClaimSource.extraction_run_id == run_id)) == 1


def test_skip_locked_and_reclaim_prevent_old_worker_completion(factory):
    run_id, _ = seed(factory)
    bind(factory, run_id)
    with factory() as first, first.begin():
        old = claim_due_evaluation(first, NOW, policy_fingerprint=POLICY.fingerprint, run_id=run_id)
        with factory() as second, second.begin():
            assert claim_due_evaluation(second, NOW, policy_fingerprint=POLICY.fingerprint, run_id=run_id) is None
    later = NOW + timedelta(minutes=3)
    with factory() as db, db.begin():
        new = claim_due_evaluation(db, later, policy_fingerprint=POLICY.fingerprint, run_id=run_id)
        assert new.attempt_count == 2 and new.lease_token != old.lease_token
        assert not finish_owned_evaluation(db, old, later, result={"old": True})
        assert finish_owned_evaluation(db, new, later, result={"new": True})


def test_retry_wait_and_exhaustion_are_bounded_and_do_not_refresh_observation(factory):
    run_id, original = seed(factory)
    bind(factory, run_id)
    now = NOW
    for attempt in range(1, 6):
        with factory() as db, db.begin():
            leased = claim_due_evaluation(db, now, policy_fingerprint=POLICY.fingerprint, run_id=run_id)
            assert leased.attempt_count == attempt
            assert finish_owned_evaluation(db, leased, now, error_code="auditor_timeout", retryable=True)
        with factory() as db:
            row = db.get(NewsClaimEvaluation, leased.evaluation_id)
            assert row.status == ("retry_wait" if attempt < 5 else "failed")
            if attempt < 5:
                now = row.next_attempt_at
            assert db.get(NewsExtractionRun, run_id).result == original


class FakeAuditor:
    def __init__(self, factory, run_id, outcome="verified"):
        self.factory, self.run_id, self.outcome = factory, run_id, outcome
        self.calls = 0

    def policy_identity(self):
        return POLICY.auditor_identity

    def batch_document(self, candidates, article):
        return "fixture"

    async def audit_batch(self, candidates, article, **kwargs):
        return {c.candidate_id: await self.audit(c.claim, article, **kwargs) for c in candidates}

    async def audit(self, value, article, **kwargs):
        self.calls += 1
        # A second real session can acquire the row: network runs outside locks.
        with self.factory() as db, db.begin():
            db.execute(text("SET LOCAL lock_timeout = '1s'"))
            evaluation = db.scalar(select(NewsClaimEvaluation).join(NewsClaimSource).where(
                NewsClaimSource.extraction_run_id == self.run_id).with_for_update(of=NewsClaimEvaluation))
            assert evaluation.status == "processing"
        return IndependentAuditResult(outcome=self.outcome, reason_code="independently_verified",
            prompt_version="fixture", response_version="fixture",
            input_sha256=extraction_input_snapshot(article)[1], claim_sha256=canonical_claim_sha256(value))


def test_durable_worker_commits_lease_before_audit_and_never_publishes(factory, monkeypatch):
    run_id, original = seed(factory)
    seeded = seed_claim_evaluations(factory, POLICY, now=NOW, run_id=run_id, sources=SOURCES)
    assert seeded.sources_created == seeded.evaluations_created == 1
    monkeypatch.setattr("app.services.news_evaluation_service.current_pipeline_version", lambda: POLICY.pipeline_version)
    auditor = FakeAuditor(factory, run_id)
    summary = asyncio.run(evaluate_news_claims(factory, run_id=run_id, auditor=auditor, policy=POLICY,
                                             sources=SOURCES, clock=lambda: NOW))
    assert summary.completed == 1 and auditor.calls == 1
    repeated = asyncio.run(evaluate_news_claims(factory, run_id=run_id, auditor=auditor, policy=POLICY,
                                              sources=SOURCES, clock=lambda: NOW))
    assert not repeated.evaluations and auditor.calls == 1
    with factory() as db:
        source = db.scalar(select(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run_id))
        case = db.get(NewsClaimCase, source.case_id)
        row = db.scalar(select(NewsClaimEvaluation).where(NewsClaimEvaluation.claim_source_id == source.id))
        assert row.result["audit"]["outcome"] == "verified"
        assert row.result["publication_permitted"] is False
        assert case.revision == 0 and db.get(NewsExtractionRun, run_id).result == original
        for model in (NewsClaimDecision, FloodAvoidanceZone, FloodReport):
            assert db.scalar(select(func.count()).select_from(model)) == 0


def test_expired_observation_completes_review_without_external_call(factory, monkeypatch):
    run_id, _ = seed(factory, event_time_resolved=NOW - timedelta(hours=2))
    bind(factory, run_id)
    monkeypatch.setattr("app.services.news_evaluation_service.current_pipeline_version", lambda: POLICY.pipeline_version)
    auditor = FakeAuditor(factory, run_id)
    summary = asyncio.run(evaluate_news_claims(factory, run_id=run_id, auditor=auditor, policy=POLICY,
                                             sources=SOURCES, clock=lambda: NOW))
    assert summary.completed == 1 and auditor.calls == 0
    with factory() as db:
        row = db.scalar(select(NewsClaimEvaluation).join(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run_id))
        assert row.result["reason_code"] == "observation_evidence_expired"
        assert row.result["audit"] is None


@pytest.mark.parametrize("changes,error", [
    ({"evidence_sentence_offset": (0, 2)}, "invalid_evidence_offsets"),
    ({"raw_place_name": "Other Road"}, "invalid_place_offsets"),
])
def test_invalid_bound_claim_has_no_orphan_case(factory, changes, error):
    run_id, _ = seed(factory, **changes)
    with factory() as db:
        before = db.scalar(select(func.count()).select_from(NewsClaimCase))
    with pytest.raises(ValueError, match=error):
        bind(factory, run_id)
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(NewsClaimCase)) == before


def test_lease_exhaustion_after_crashed_attempts_is_terminal(factory):
    run_id, _ = seed(factory)
    bind(factory, run_id)
    now = NOW
    for attempt in range(1, 6):
        with factory() as db, db.begin():
            leased = claim_due_evaluation(db, now, policy_fingerprint=POLICY.fingerprint, run_id=run_id)
            assert not leased.exhausted and leased.attempt_count == attempt
        now += timedelta(minutes=3)
    with factory() as db, db.begin():
        exhausted = claim_due_evaluation(db, now, policy_fingerprint=POLICY.fingerprint, run_id=run_id)
        assert exhausted.exhausted and exhausted.lease_token is None
    with factory() as db, db.begin():
        assert claim_due_evaluation(db, now, policy_fingerprint=POLICY.fingerprint, run_id=run_id) is None
        row = db.get(NewsClaimEvaluation, exhausted.evaluation_id)
        assert row.error_code == "lease_expired_exhausted" and row.result is None


def test_worker_timeout_is_retryable_without_changing_completed_extraction(factory, monkeypatch):
    run_id, original = seed(factory)
    bind(factory, run_id)
    monkeypatch.setattr("app.services.news_evaluation_service.current_pipeline_version", lambda: POLICY.pipeline_version)

    class UnavailableAuditor(FakeAuditor):
        async def audit(self, value, article, **kwargs):
            return IndependentAuditResult(outcome="unavailable", reason_code="auditor_timeout", retryable=True,
                prompt_version="fixture", response_version="fixture", input_sha256=extraction_input_snapshot(article)[1],
                claim_sha256=canonical_claim_sha256(value))

    summary = asyncio.run(evaluate_news_claims(factory, run_id=run_id,
        auditor=UnavailableAuditor(factory, run_id), policy=POLICY, sources=SOURCES, clock=lambda: NOW))
    assert summary.retry_wait == 1
    with factory() as db:
        assert db.get(NewsExtractionRun, run_id).status == "completed"
        assert db.get(NewsExtractionRun, run_id).result == original


def test_policy_change_and_wrong_audit_identity_cannot_complete_confirmation(factory, monkeypatch):
    run_id, _ = seed(factory)
    bind(factory, run_id)
    monkeypatch.setattr("app.services.news_evaluation_service.current_pipeline_version", lambda: POLICY.pipeline_version)

    class WrongIdentity(FakeAuditor):
        async def audit(self, value, article, **kwargs):
            return IndependentAuditResult(outcome="verified", reason_code="independently_verified",
                prompt_version="fixture", response_version="fixture", input_sha256="f" * 64,
                claim_sha256=canonical_claim_sha256(value))

    summary = asyncio.run(evaluate_news_claims(factory, run_id=run_id, auditor=WrongIdentity(factory, run_id),
        policy=POLICY, sources=SOURCES, clock=lambda: NOW))
    assert summary.failed == 1 and summary.evaluations[0]["error_code"] == "audit_evidence_mismatch"
    new_run, _ = seed(factory)
    bind(factory, new_run)
    monkeypatch.setattr("app.services.news_evaluation_service.current_pipeline_version", lambda: "changed-assets")
    auditor = FakeAuditor(factory, new_run)
    changed = asyncio.run(evaluate_news_claims(factory, run_id=new_run, auditor=auditor, policy=POLICY,
                                              sources=SOURCES, clock=lambda: NOW))
    assert changed.failed == 1 and auditor.calls == 0
    assert changed.evaluations[0]["error_code"] == "evaluation_policy_changed"


def test_lease_expiring_during_network_call_is_reported_without_overwrite(factory, monkeypatch):
    run_id, _ = seed(factory)
    bind(factory, run_id)
    monkeypatch.setattr("app.services.news_evaluation_service.current_pipeline_version", lambda: POLICY.pipeline_version)
    now = [NOW]

    class SlowAuditor(FakeAuditor):
        async def audit(self, value, article, **kwargs):
            result = await super().audit(value, article, **kwargs)
            now[0] += timedelta(minutes=3)
            return result

    summary = asyncio.run(evaluate_news_claims(factory, run_id=run_id, auditor=SlowAuditor(factory, run_id),
        policy=POLICY, sources=SOURCES, clock=lambda: now[0]))
    assert summary.lease_lost == 1 and summary.completed == 0
    with factory() as db:
        row = db.scalar(select(NewsClaimEvaluation).join(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run_id))
        assert row.status == "processing" and row.result is None


def test_storage_completion_failure_propagates_and_no_success_is_reported(factory, monkeypatch):
    run_id, original = seed(factory)
    bind(factory, run_id)
    monkeypatch.setattr("app.services.news_evaluation_service.current_pipeline_version", lambda: POLICY.pipeline_version)

    def failed_completion(*args, **kwargs):
        raise RuntimeError("simulated durable storage outage")

    monkeypatch.setattr("app.services.news_evaluation_service.finish_owned_evaluation", failed_completion)
    with pytest.raises(RuntimeError, match="durable storage outage"):
        asyncio.run(evaluate_news_claims(factory, run_id=run_id, auditor=FakeAuditor(factory, run_id),
                                        policy=POLICY, sources=SOURCES, clock=lambda: NOW))
    with factory() as db:
        assert db.get(NewsExtractionRun, run_id).result == original
        row = db.scalar(select(NewsClaimEvaluation).join(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run_id))
        assert row.status == "processing" and row.result is None


def test_real_provider_adapter_to_durable_evaluation_with_mock_http(factory, monkeypatch):
    run_id, original = seed(factory, depth_raw="knee-deep", depth_canonical="knee", event_time_raw="10:55 AM")
    auditor = NewsClaimAuditor(AuditorConfig(provider="openrouter", model="fixture/model",
                                           openrouter_api_key="synthetic-not-live"))
    policy = EvaluationPolicy("c" * 64, POLICY.pipeline_version, auditor.policy_identity())
    bind(factory, run_id, policy.fingerprint)
    with factory() as db:
        row = db.get(NewsExtractionRun, run_id)
        version = db.get(NewsArticleVersion, row.article_version_id)
        article = NewsArticleExtractorInput.model_validate({**version.input_snapshot, "article_id": version.article_id})
        value = ExtractedClaim.model_validate(original["claims"][0])
    payload = evidence(value, article)
    calls = []

    def mock_http(request):
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"data": {}})
        document = __import__("json").loads(__import__("json").loads(request.content)["messages"][1]["content"])
        return reply({"results": [{"candidate_id": document["candidates"][0]["candidate_id"], **payload}]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(mock_http)) as client:
            return await evaluate_news_claims(factory, run_id=run_id, auditor=auditor, policy=policy,
                                              sources=SOURCES, clock=lambda: NOW, client=client)

    monkeypatch.setattr("app.services.news_evaluation_service.current_pipeline_version", lambda: POLICY.pipeline_version)
    summary = asyncio.run(run())
    assert summary.completed == 1 and len([r for r in calls if r.method == "POST"]) == 1
    with factory() as db:
        row = db.scalar(select(NewsClaimEvaluation).join(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run_id))
        assert row.result["audit"]["outcome"] == "verified"
        assert row.result["audit"]["evidence"]["time"]["observed_at"] == value.event_time_resolved.isoformat()
        assert row.result["publication_permitted"] is False


def test_completion_preserves_audit_and_records_publication_age_out(factory, monkeypatch):
    run_id, _ = seed(factory, published_at=NOW - timedelta(hours=12) + timedelta(seconds=1))
    bind(factory, run_id)
    now = [NOW]
    monkeypatch.setattr("app.services.news_evaluation_service.current_pipeline_version", lambda: POLICY.pipeline_version)

    class PublicationAgesOut(FakeAuditor):
        async def audit(self, value, article, **kwargs):
            response = await super().audit(value, article, **kwargs)
            now[0] += timedelta(seconds=2)
            return response

    summary = asyncio.run(evaluate_news_claims(factory, run_id=run_id,
        auditor=PublicationAgesOut(factory, run_id), policy=POLICY, sources=SOURCES, clock=lambda: now[0]))
    assert summary.completed == 1
    with factory() as db:
        row = db.scalar(select(NewsClaimEvaluation).join(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run_id))
        assert row.result["freshness_reason_at_completion"] == "publication_outside_admission_window"
        assert row.result["audit"]["outcome"] == "verified"


def test_new_config_revision_recovers_failed_audit_without_erasing_history(factory, monkeypatch):
    run_id, _ = seed(factory)
    monkeypatch.setattr("app.services.news_evaluation_service.current_pipeline_version", lambda: POLICY.pipeline_version)
    first = NewsClaimAuditor(AuditorConfig(provider="openrouter", model="fixture/model",
        openrouter_api_key="synthetic-old-key", config_revision="1"))
    repaired = NewsClaimAuditor(AuditorConfig(provider="openrouter", model="fixture/model",
        openrouter_api_key="synthetic-repaired-key", config_revision="2"))
    one, two = evaluation_policy(first), evaluation_policy(repaired)
    assert one.fingerprint != two.fingerprint
    assert bind(factory, run_id, one.fingerprint) == (1, 1)
    with factory() as db, db.begin():
        leased = claim_due_evaluation(db, NOW, policy_fingerprint=one.fingerprint, run_id=run_id)
        assert finish_owned_evaluation(db, leased, NOW, error_code="auditor_http_error")
    assert bind(factory, run_id, two.fingerprint) == (0, 1)
    with factory() as db:
        rows = db.scalars(select(NewsClaimEvaluation).join(NewsClaimSource).where(
            NewsClaimSource.extraction_run_id == run_id).order_by(NewsClaimEvaluation.id)).all()
        assert [row.status for row in rows] == ["failed", "pending"]
        assert rows[0].error_code == "auditor_http_error"


@pytest.mark.parametrize("publication_offset,reason", [(-13, "publication_outside_admission_window"),
                                                         (1, "publication_outside_admission_window")])
def test_seed_rejects_old_or_future_publication_without_creating_cases(factory, publication_offset, reason):
    run_id, _ = seed(factory, published_at=NOW + timedelta(hours=publication_offset))
    seeded = seed_claim_evaluations(factory, POLICY, now=NOW, run_id=run_id, sources=SOURCES)
    assert seeded.sources_created == seeded.evaluations_created == 0
    assert seeded.skipped == [{"run_id": run_id, "reason_code": reason}]
    with factory() as db:
        assert not db.scalar(select(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run_id))


def test_unapproved_or_old_pipeline_cannot_seed_work(factory):
    run_id, _ = seed(factory)
    denied = seed_claim_evaluations(factory, POLICY, now=NOW, run_id=run_id, sources=())
    assert denied.skipped[0]["reason_code"] == "unapproved_article_source"
    changed = EvaluationPolicy("f" * 64, "different-assets", POLICY.auditor_identity)
    stale = seed_claim_evaluations(factory, changed, now=NOW, run_id=run_id, sources=SOURCES)
    assert stale.skipped[0]["reason_code"] == "stale_extraction_policy"


def test_seed_cursor_is_resumable_and_repeat_cannot_create_duplicate_sources(factory):
    first, _ = seed(factory)
    second, _ = seed(factory)
    initial = seed_claim_evaluations(factory, POLICY, now=NOW, limit=1, after_run_id=first - 1, sources=SOURCES)
    assert initial.next_after_run_id == first and initial.sources_created == 1
    resumed = seed_claim_evaluations(factory, POLICY, now=NOW, limit=1,
                                    after_run_id=initial.next_after_run_id, sources=SOURCES)
    assert resumed.next_after_run_id == second and resumed.sources_created == 1
    repeat = seed_claim_evaluations(factory, POLICY, now=NOW, run_id=first, sources=SOURCES)
    assert repeat.sources_created == repeat.evaluations_created == 0
