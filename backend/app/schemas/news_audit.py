"""Strict, immutable evidence from the independent news auditor.

Provider output is not a publication decision or operational geometry.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
    evidence: ProviderClaimAudit | None = None
