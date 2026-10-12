"""Real-clock model circuit protection in existing bounded setting JSON."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field
from app.models.setting import SystemSetting
from app.schemas.news_audit import IndependentAuditResult, AuditTransportDiagnostics
from app.services.news_audit_quota_service import deadline, quota_identity, real_now

AVAILABILITY_KEY = "news_audit_availability_v1"
MAX_MODEL_STATES = 8


class ModelAvailability(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consecutive_failures: int = Field(default=0, ge=0, le=2)
    recovery_failures: int = Field(default=0, ge=0, le=3)
    blocked_until: str | None = None
    last_checked_at: str | None = None
    last_error: str | None = Field(default=None, max_length=100)
    last_phase: str | None = Field(default=None, max_length=20)
    last_transport: AuditTransportDiagnostics | None = None


def model_identity(auditor) -> str:
    return hashlib.sha256((quota_identity(auditor) + "\0" + (auditor.config.model or "")).encode()).hexdigest()


def read_availability(db, auditor) -> ModelAvailability:
    row = db.get(SystemSetting, AVAILABILITY_KEY, populate_existing=True)
    values = row.value if row else {}
    return ModelAvailability.model_validate(values.get(model_identity(auditor), {}))


def save_availability(factory, auditor, state: ModelAvailability) -> None:
    with factory() as db, db.begin():
        row = db.get(SystemSetting, AVAILABILITY_KEY)
        if row is None:
            row = SystemSetting(key=AVAILABILITY_KEY)
            db.add(row)
        values = dict(row.value or {})
        values[model_identity(auditor)] = state.model_dump(mode="json")
        while len(values) > MAX_MODEL_STATES:
            oldest = min((key for key in values if key != model_identity(auditor)),
                key=lambda key: values[key].get("last_checked_at") or "")
            values.pop(oldest)
        row.value = values


def availability_failure(result: IndependentAuditResult) -> bool:
    return (result.reason_code in {"auditor_timeout", "auditor_transport_error", "auditor_exception", "audit_batch_result_missing"}
        or result.provider_http_status == 408 or (result.provider_http_status or 0) >= 500
        or (result.reason_code == "auditor_response_invalid" and result.transport is not None
            and result.transport.finish_reason not in (None, "stop")))


def record_availability(factory, auditor, result: IndependentAuditResult, *, now: datetime | None = None) -> ModelAvailability:
    now = now or real_now()
    with factory() as db:
        state = read_availability(db, auditor)
    until = deadline(state.blocked_until)
    recovering = until is not None and until <= now
    if availability_failure(result):
        state.consecutive_failures = min(2, state.consecutive_failures + 1)
        if recovering:
            state.recovery_failures = min(3, state.recovery_failures + 1)
        if state.consecutive_failures >= 2 or recovering:
            delay = (15, 30, 60, 60)[state.recovery_failures]
            state.blocked_until = (now + timedelta(minutes=delay)).isoformat()
        state.last_error = result.reason_code
    elif result.provider_http_status == 200 and result.reason_code != "auditor_response_invalid":
        # A complete response with a rejected fact proves availability, not truth.
        state.consecutive_failures = state.recovery_failures = 0
        state.blocked_until = None
        state.last_error = None
    state.last_checked_at = now.isoformat()
    state.last_phase = result.transport.phase if result.transport else None
    state.last_transport = result.transport
    save_availability(factory, auditor, state)
    return state
