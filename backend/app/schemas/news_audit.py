"""Strict, immutable evidence from the independent news auditor.

Provider output is not a publication decision or operational geometry.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuditEvidenceSpan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    start: int = Field(ge=0)
    end: int = Field(gt=0)
    quote: str = Field(min_length=1, max_length=4000)


class AuditedFact(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    confirmed: bool
    evidence: tuple[AuditEvidenceSpan, ...] = Field(max_length=12)


class AuditedPlace(AuditedFact):
    raw_place_name: str
    canonical_city: str | None
    canonical_barangay: str | None


class AuditedStatus(AuditedFact):
    classification: Literal["active", "rising", "receding", "subsided", "forecast", "negated", "unclear"]
    contradictory: bool
    historical: bool


class AuditedTime(AuditedFact):
    # Parse explicitly after strict JSON validation; publication/fetch times do
    # not establish an observation, including when the model echoes them.
    observed_at: str | None
    kind: Literal["observation", "report", "unspecified"]


class AuditedDepth(AuditedFact):
    canonical: Literal["gutter", "half-knee", "half-tire", "knee", "tires", "waist", "chest", "neck"] | None
    raw: str | None
    qualifiers: tuple[str, ...] = Field(max_length=12)


class AuditedAccess(AuditedFact):
    classification: Literal["passable_all", "passable_with_caution", "passable_unspecified", "light_vehicle_closed", "impassable_all", "unknown"]


class ProviderClaimAudit(BaseModel):
    """All dimensions are required; omitted or coercible fields are rejected."""
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    claim_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    place: AuditedPlace
    status: AuditedStatus
    time: AuditedTime
    depth: AuditedDepth
    access: AuditedAccess


class AuditEvidenceReference(BaseModel):
    """Provider selects a backend-owned exact source slice, never invents offsets."""
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    option_index: int = Field(ge=0, lt=256)


class SelectedPlace(AuditedPlace):
    evidence: tuple[AuditEvidenceReference, ...] = Field(max_length=12)


class SelectedStatus(AuditedStatus):
    evidence: tuple[AuditEvidenceReference, ...] = Field(max_length=12)


class SelectedTime(AuditedTime):
    evidence: tuple[AuditEvidenceReference, ...] = Field(max_length=12)


class SelectedDepth(AuditedDepth):
    evidence: tuple[AuditEvidenceReference, ...] = Field(max_length=12)


class SelectedAccess(AuditedAccess):
    evidence: tuple[AuditEvidenceReference, ...] = Field(max_length=12)


class ProviderClaimAuditSelection(ProviderClaimAudit):
    """Wire contract only; stored audit evidence retains full exact source spans."""
    place: SelectedPlace
    status: SelectedStatus
    time: SelectedTime
    depth: SelectedDepth
    access: SelectedAccess


class AuditTransportDiagnostics(BaseModel):
    """Bounded observations only; never provider bodies, URLs or credentials."""
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    phase: Literal["prepare", "headers", "body", "parse", "validate", "complete"]
    timeout_kind: Literal["connect", "read", "write", "pool", "overall"] | None = None
    elapsed_ms: int = Field(ge=0, le=3_600_000)
    timings_ms: dict[str, int] = Field(default_factory=dict, max_length=8)
    response_bytes: int = Field(default=0, ge=0, le=100_000)
    request_bytes: int = Field(default=0, ge=0, le=1_000_000)
    candidate_count: int = Field(ge=1, le=8)
    actual_model: str | None = Field(default=None, max_length=160, pattern=r"^[A-Za-z0-9_./:-]+$")
    gateway_request_id: str | None = Field(default=None, max_length=200, pattern=r"^[A-Za-z0-9_./:-]+$")
    generation_id: str | None = Field(default=None, max_length=200, pattern=r"^[A-Za-z0-9_./:-]+$")
    finish_reason: str | None = Field(default=None, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    prompt_tokens: int | None = Field(default=None, ge=0, le=10_000_000)
    completion_tokens: int | None = Field(default=None, ge=0, le=10_000_000)
    error_category: Literal["schema_rejected", "reasoning_rejected", "parameter_rejected", "model_unavailable", "unspecified"] | None = None

    @field_validator("timings_ms")
    @classmethod
    def bounded_timings(cls, value: dict[str, int]) -> dict[str, int]:
        if (set(value) - {"prepared", "headers", "first_body", "body_complete", "parsed", "validated"}
                or any(type(v) is not int or not 0 <= v <= 3_600_000 for v in value.values())):
            raise ValueError("Invalid safe audit timings")
        return value


class IndependentAuditResult(BaseModel):
    """Safe internal result saved independently from immutable extraction."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: Literal["verified", "review", "unavailable", "invalid"]
    reason_code: str = Field(pattern=r"^[a-z][a-z0-9_]{0,99}$")
    retryable: bool = False
    provider: str | None = None
    model: str | None = None
    prompt_version: str
    response_version: str
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    claim_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_request_id: str | None = Field(default=None, max_length=200)
    provider_http_status: int | None = Field(default=None, ge=100, le=599)
    retry_after_seconds: int | None = Field(default=None, ge=1, le=86400)
    evidence: ProviderClaimAudit | None = None
    transport: AuditTransportDiagnostics | None = None


class BatchClaimSelection(ProviderClaimAuditSelection):
    candidate_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")


class ProviderBatchSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    results: tuple[BatchClaimSelection, ...] = Field(max_length=8)


class CompactClaimSelection(BaseModel):
    """Provider chooses facts; the backend owns immutable hash association."""
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    candidate_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    place: SelectedPlace
    status: SelectedStatus
    time: SelectedTime
    depth: SelectedDepth
    access: SelectedAccess


class CompactBatchSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    results: tuple[CompactClaimSelection, ...] = Field(max_length=8)


class AuditQuotaState(BaseModel):
    """Credential-free state in the existing system-settings JSON table."""
    model_config = ConfigDict(extra="forbid")
    identity: str = ""
    checked_at: str | None = None
    quota_check_succeeded: bool = False
    blocked_until: str | None = None
    used: int | None = Field(default=None, ge=0)
    limit: int | None = Field(default=None, ge=0)
    remaining: int | None = Field(default=None, ge=0)
    error_code: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_]{0,99}$")
    http_status: int | None = Field(default=None, ge=100, le=599)
    request_count: int = Field(default=0, ge=0)
    claims_dispatched: int = Field(default=0, ge=0)
