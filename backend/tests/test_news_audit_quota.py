"""Quota state is bounded, credential-free and recoverable without flood writes."""
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy.orm import sessionmaker

from app.schemas.news_audit import AuditQuotaState, IndependentAuditResult
from app.services.news_audit_quota_service import check_quota, dispatched, read_quota, record_error, deadline, save_quota, quota_identity
from app.services.news_claim_auditor import AuditorConfig, NewsClaimAuditor
from tests.test_news_automation import status_db


@pytest.mark.asyncio
async def test_exhausted_quota_caches_cooldown_then_recovers(status_db):
    factory = sessionmaker(bind=status_db.get_bind())
    service = NewsClaimAuditor(AuditorConfig(provider="openrouter", model="openrouter/free", openrouter_api_key="synthetic-only"))
    now = datetime.now(timezone.utc)
    calls = []
    def handler(request):
        calls.append(request)
        remaining = 0 if len(calls) == 1 else 50
        return httpx.Response(200, json={"data": {"free_model_daily_requests": {
            "used": 50-remaining, "limit": 50, "remaining": remaining}, "secret": "NEVER_PERSIST"}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        state = await check_quota(factory, service, client=client, now=now)
        assert state.remaining == 0 and deadline(state.blocked_until) == now+timedelta(minutes=30)
        again = await check_quota(factory, service, client=client, now=now+timedelta(minutes=15))
        assert len(calls) == 1 and again.remaining == 0
        recovered = await check_quota(factory, service, client=client, now=now+timedelta(minutes=30))
        assert len(calls) == 2 and recovered.remaining == 50 and recovered.blocked_until is None
        dispatched(factory, recovered, 8)
        cached = await check_quota(factory, service, client=client, now=now+timedelta(minutes=30, seconds=10))
        assert cached.remaining == 49 and cached.request_count == 1 and cached.claims_dispatched == 8
    with factory() as db:
        saved = read_quota(db)
        assert "synthetic-only" not in saved.model_dump_json() and "NEVER_PERSIST" not in saved.model_dump_json()


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [{}, {"remaining": "0", "limit": 50, "used": 50}, {"remaining": -1, "limit": 50, "used": 50}])
async def test_absent_or_invalid_counter_is_unknown_not_exhausted(status_db, payload):
    factory = sessionmaker(bind=status_db.get_bind())
    service = NewsClaimAuditor(AuditorConfig(provider="openrouter", model="openrouter/free", openrouter_api_key="synthetic-only"))
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"data": {"free_model_daily_requests": payload}}))) as client:
        state = await check_quota(factory, service, client=client)
    assert state.remaining is None and state.error_code == "auditor_quota_unknown" and state.blocked_until is None


def test_rate_limit_error_persists_only_safe_status_and_deadline(status_db):
    factory = sessionmaker(bind=status_db.get_bind())
    state = read_quota(status_db)
    result = IndependentAuditResult(outcome="unavailable", reason_code="auditor_rate_limited", retryable=True,
        provider_http_status=429, retry_after_seconds=90, prompt_version="fixture", response_version="fixture",
        input_sha256="a"*64, claim_sha256="b"*64)
    record_error(factory, state, result)
    assert state.http_status == 429 and state.error_code == "auditor_rate_limited" and deadline(state.blocked_until)


@pytest.mark.asyncio
async def test_changed_credential_identity_does_not_inherit_stale_cooldown(status_db):
    factory = sessionmaker(bind=status_db.get_bind())
    now = datetime.now(timezone.utc)
    first = NewsClaimAuditor(AuditorConfig(provider="openrouter", model="openrouter/free", openrouter_api_key="first-synthetic"))
    second = NewsClaimAuditor(AuditorConfig(provider="openrouter", model="openrouter/free", openrouter_api_key="second-synthetic"))
    calls = []
    def handler(r):
        calls.append(r)
        return httpx.Response(200, json={"data": {"free_model_daily_requests": {"used": 50, "limit": 50, "remaining": 0}}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await check_quota(factory, first, client=client, now=now)
        await check_quota(factory, second, client=client, now=now)
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_expired_short_provider_cooldown_rechecks_before_cache_expires(status_db):
    factory = sessionmaker(bind=status_db.get_bind())
    service = NewsClaimAuditor(AuditorConfig(provider="openrouter", model="openrouter/free", openrouter_api_key="synthetic-only"))
    now = datetime.now(timezone.utc)
    calls = []
    def handler(request):
        calls.append(request)
        remaining = 0 if len(calls) == 1 else 50
        return httpx.Response(200, headers={"retry-after": "5"}, json={"data": {
            "free_model_daily_requests": {"used": 50-remaining, "limit": 50, "remaining": remaining}}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        first = await check_quota(factory, service, client=client, now=now)
        assert deadline(first.blocked_until) == now+timedelta(seconds=5)
        recovered = await check_quota(factory, service, client=client, now=now+timedelta(seconds=6))
        assert len(calls) == 2 and recovered.remaining == 50 and recovered.blocked_until is None


def test_status_does_not_claim_available_capacity_when_cooldown_expired(status_db, monkeypatch):
    from app.services.news_automation_service import read_news_automation
    factory = sessionmaker(bind=status_db.get_bind())
    now = datetime.now(timezone.utc)
    service = NewsClaimAuditor()
    save_quota(factory, AuditQuotaState(identity=quota_identity(service), remaining=0, checked_at=now.isoformat(),
        blocked_until=(now-timedelta(seconds=1)).isoformat(), error_code="auditor_daily_quota_exhausted"))
    monkeypatch.setattr("app.services.news_audit_quota_service.real_now", lambda: now)
    status = read_news_automation(status_db)
    assert status.audit.state == "awaiting_check" and status.audit.remaining == 0
