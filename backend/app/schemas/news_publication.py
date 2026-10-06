"""Validated immutable decisions and deliberately separate public projections."""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NewsPublicationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PublicNewsSource(NewsPublicationModel):
    publisher: str = Field(max_length=160)
    title: str = Field(max_length=500)
    url: str = Field(max_length=2048)


class PublicNewsDepth(NewsPublicationModel):
    raw: str | None = Field(default=None, max_length=500)
    canonical: Literal["gutter", "half-knee", "half-tire", "knee", "tires", "waist", "chest", "neck"] | None = None
    formatted: str | None = Field(default=None, max_length=500)
    qualifiers: list[str] = Field(default_factory=list, max_length=12)


class PublicNewsAlert(NewsPublicationModel):
    case_id: int = Field(gt=0)
    decision_id: int = Field(gt=0)
    revision: int = Field(gt=0)
    status: Literal["Active", "Unconfirmed", "Cleared"]
    location_label: str = Field(max_length=250)
    location_qualifier: str | None = Field(default=None, max_length=500)
    depth_label: str | None = Field(default=None, max_length=500)
    condition_label: str = Field(max_length=200)
    passability_label: str = Field(max_length=200)
    observed_at: datetime | None = None
    expires_at: datetime | None = None
    cleared_at: datetime | None = None
    updated_at: datetime
    source_title: str = Field(max_length=500)
    source_publisher: str = Field(max_length=160)
    source_url: str = Field(max_length=2048)
    source_published_at: datetime | None = None
    correction_note: str | None = Field(default=None, max_length=500)
    evidence_excerpt: str = Field(max_length=700)
    geometry_precision: Literal["text_only", "display_suggestion", "operational_polygon"] = "text_only"
    display_geojson: dict | None = None
    current_status_unknown: bool = False
    affects_routing: bool = False
    geometry_basis: Literal["verified_current_footprint", "estimated_road_corridor"] | None = None


    @field_validator("source_url")
    @classmethod
    def safe_source_url(cls, value: str) -> str:
        from app.services.news_sources import _public_host
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or not _public_host(parsed.hostname) or parsed.username
                or parsed.password or parsed.port not in (None, 443) or any(ord(char) < 32 for char in value)):
            raise ValueError("Unsafe public source URL")
        return value

class PublicNewsAlertPage(NewsPublicationModel):
    items: list[PublicNewsAlert]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    pages: int = Field(ge=0)
    as_of: datetime


class EstimatedRoadEvidence(NewsPublicationModel):
    policy_version: Literal["news-estimated-road-v1"] = "news-estimated-road-v1"
    candidate_id: str = Field(min_length=1, max_length=300)
    placement_revision: str = Field(min_length=1, max_length=500)
    osm_catalog_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    noah_catalog_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    buffer_radius_metres: Literal[25.0] = 25.0
    component_centerlines: list[dict] = Field(min_length=1, max_length=25)


class OperationalFootprintBinding(NewsPublicationModel):
    evidence_kind: Literal["authoritative_current_incident", "staff_review", "estimated_news_road"]
    record_id: str = Field(min_length=1, max_length=200)
    actor_user_id: int | None = Field(default=None, gt=0)
    article_id: int = Field(gt=0)
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    claim_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    incident_identity: str = Field(pattern=r"^[0-9a-f]{64}$")
    observed_at: datetime
    city: str = Field(min_length=1, max_length=200)
    barangay: str | None = Field(default=None, max_length=200)
    srid: Literal[4326]
    boundary_revision: str = Field(min_length=1, max_length=300)
    component_sha256: list[str] = Field(min_length=1, max_length=25)
    catalog_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    estimated_road: EstimatedRoadEvidence | None = None


class OperationalFootprintProvenance(NewsPublicationModel):
    """Private server-approved binding; legacy unbound attribution stays readable."""
    source: str = Field(min_length=1, max_length=500)
    source_checksum: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    geometry_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    parent_boundary_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    binding: OperationalFootprintBinding | None = None


class NewsDecisionSnapshot(NewsPublicationModel):
    schema_version: Literal["news-publication-v1"] = "news-publication-v1"
    request_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    policy_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    claim_source_id: int = Field(gt=0)
    evaluation_id: int | None = Field(default=None, gt=0)
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    claim_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    incident_identity: str = Field(pattern=r"^[0-9a-f]{64}$")
    article_id: int = Field(gt=0)
    public: PublicNewsAlert | None = None
    private_reason: str | None = Field(default=None, max_length=2000)
    target_case_id: int | None = Field(default=None, gt=0)
    previous_decision_id: int | None = Field(default=None, gt=0)
    deferred_until: datetime | None = None
    unconfirmed_retention_hours: int = Field(default=24, ge=1, le=72)
    geometry_reason: Literal[
        "operational_geometry_not_verified",
        "verified_incident_footprint",
        "staff_reviewed_footprint",
        "estimated_road_corridor",
    ] = "operational_geometry_not_verified"
    linked_zone_ids: list[int] = Field(default_factory=list)
    operational_provenance: OperationalFootprintProvenance | None = None
    estimated_road_review_revision: str | None = Field(default=None, max_length=500)


class NewsStaffDecisionRequest(NewsPublicationModel):
    request_id: UUID
    expected_revision: int = Field(ge=0)
    operation: Literal["correct", "defer", "reject", "reopen", "clear"]
    reason: str = Field(min_length=3, max_length=2000)
    evaluation_id: int | None = Field(default=None, gt=0)
    public_correction: str | None = Field(default=None, max_length=500)
    deferred_until: datetime | None = None
    operational_zone_id: int | None = Field(default=None, gt=0)
    operational_footprint: dict | None = None
    operational_footprint_srid: Literal[4326] | None = None

    @field_validator("deferred_until")
    @classmethod
    def timezone_required(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("Timezone required")
        return value


class NewsDecisionSummary(NewsPublicationModel):
    id: int
    revision: int
    operation: str
    public_state: str
    review_state: str
    reason_code: str
    decided_at: datetime
    observed_at: datetime | None
    expires_at: datetime | None


class NewsClaimDetail(NewsPublicationModel):
    case_id: int
    revision: int
    allowed_actions: list[str]
    current: NewsDecisionSummary | None
    public: PublicNewsAlert | None
    decisions: list[NewsDecisionSummary]
    evaluation_options: list[NewsEvaluationOption] = Field(default_factory=list)


class NewsEvaluationOption(NewsPublicationModel):
    evaluation_id: int
    source_id: int
    run_id: int
    claim_ordinal: int
    condition: str
    observed_at: datetime | None
    outcome: str
    reason_code: str


class NewsDecisionEffect(NewsPublicationModel):
    public_state: str
    review_state: str
    status: Literal["Active", "Unconfirmed", "Cleared"] | None = None
    reason_code: str
    affects_routing: bool = False
    linked_zone_ids: list[int] = Field(default_factory=list)




NewsClaimDetail.model_rebuild()
