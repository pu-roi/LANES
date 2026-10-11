"""Bounded quota checks and cooldowns; no flood evidence or publication writes."""
from __future__ import annotations

from contextlib import contextmanager
import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import json

import httpx
from sqlalchemy import text

from app.models.setting import SystemSetting
from app.schemas.news_audit import AuditQuotaState, IndependentAuditResult
from app.services.news_claim_auditor import NewsClaimAuditor, safe_retry_seconds

QUOTA_KEY = "news_audit_quota_v1"
AUDIT_LOCK = 614296504


def real_now() -> datetime:
    # Provider limits use real time, including during historical article replays.
    return datetime.now(timezone.utc)


def deadline(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None


def quota_identity(auditor: NewsClaimAuditor) -> str:
    payload = json.dumps(auditor.policy_identity(), sort_keys=True) + auditor.config.openrouter_api_key
    return hashlib.sha256(payload.encode()).hexdigest()


def read_quota(db, *, identity: str | None = None) -> AuditQuotaState:
    row = db.get(SystemSetting, QUOTA_KEY, populate_existing=True)
    state = AuditQuotaState.model_validate(row.value) if row else AuditQuotaState()
    if identity is not None and state.identity != identity:
        return AuditQuotaState(identity=identity)
    return state


def save_quota(factory, state: AuditQuotaState) -> None:
    with factory() as db, db.begin():
        row = db.get(SystemSetting, QUOTA_KEY)
        if row is None:
            row = SystemSetting(key=QUOTA_KEY)
            db.add(row)
        row.value = state.model_dump(mode="json")


@contextmanager
def audit_dispatch_lock(factory):
    with factory() as db:
        engine = db.get_bind()
    # Session advisory ownership on an autocommit connection; no transaction or
    # evaluation row lock is held during external requests.
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        acquired = bool(connection.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": AUDIT_LOCK}))
        try:
            yield acquired
        finally:
            if acquired:
                connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": AUDIT_LOCK})


def free_router(auditor: NewsClaimAuditor) -> bool:
    return auditor.config.provider == "openrouter" and (
        auditor.config.model == "openrouter/free" or (auditor.config.model or "").endswith(":free"))


async def check_quota(factory, auditor: NewsClaimAuditor, *, client: httpx.AsyncClient | None = None,
                      now: datetime | None = None) -> AuditQuotaState:
    now = now or real_now()
    with factory() as db:
        state = read_quota(db, identity=quota_identity(auditor))
    until = deadline(state.blocked_until)
    checked = deadline(state.checked_at)
    if until and until > now:
        return state
    if checked and state.quota_check_succeeded and not until and timedelta(0) <= now - checked < timedelta(seconds=60):
        return state
    own = client is None
    client = client or httpx.AsyncClient(timeout=10, follow_redirects=False)
    state.used = state.limit = state.remaining = None
    state.blocked_until = None
    state.checked_at = now.isoformat()
    state.quota_check_succeeded = False
    state.error_code = None
    try:
        async with asyncio.timeout(10), client.stream("GET", "https://openrouter.ai/api/v1/key", timeout=10,
            headers={"Authorization": "Bearer " + auditor.config.openrouter_api_key}, follow_redirects=False) as response:
            state.http_status = response.status_code
            if response.status_code == 200:
                content = bytearray()
                async for piece in response.aiter_bytes(chunk_size=4096):
                    content.extend(piece)
                    if len(content) > 16384:
                        raise ValueError("quota_response_oversized")
                quota = json.loads(content).get("data", {}).get("free_model_daily_requests")
                state.quota_check_succeeded = True
                if isinstance(quota, dict) and all(type(quota.get(k)) is int and 0 <= quota[k] <= 10**9
                                                  for k in ("used", "limit", "remaining")):
                    state.used, state.limit, state.remaining = (quota[k] for k in ("used", "limit", "remaining"))
                else:
                    state.error_code = "auditor_quota_unknown"
                if state.remaining == 0 and free_router(auditor):
                    delay = safe_retry_seconds(response.headers, now=now) or 1800
                    state.blocked_until = (now + timedelta(seconds=delay)).isoformat()
                    state.error_code = "auditor_daily_quota_exhausted"
            else:
                state.error_code = "auditor_quota_unavailable"
                if response.status_code == 429:
                    state.blocked_until = (now + timedelta(seconds=safe_retry_seconds(response.headers, now=now) or 900)).isoformat()
    except (httpx.HTTPError, TimeoutError, ValueError, TypeError, AttributeError):
        state.error_code = "auditor_quota_unknown"
        state.http_status = None
    finally:
        if own:
            await client.aclose()
    save_quota(factory, state)
    return state


def dispatched(factory, state: AuditQuotaState, count: int) -> None:
    state.request_count += 1
    state.claims_dispatched += count
    if state.remaining is not None:
        state.remaining = max(0, state.remaining - 1)
    if state.used is not None:
        state.used += 1
    save_quota(factory, state)


def record_error(factory, state: AuditQuotaState, result: IndependentAuditResult) -> None:
    state.http_status = result.provider_http_status
    state.error_code = result.reason_code if result.outcome in ("invalid", "unavailable") else None
    if result.provider_http_status == 429:
        state.blocked_until = (real_now() + timedelta(seconds=result.retry_after_seconds or 900)).isoformat()
    save_quota(factory, state)
