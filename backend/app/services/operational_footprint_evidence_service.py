"""Server-owned current-incident approval; no live downloads or database writes.

An operator-approved catalog is separate from client labels and modeled assets.
Staff approval is constructed only from an authenticated, capable stored actor.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from shapely import set_srid
from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry
from sqlalchemy.orm import Session

from app.services.news_permissions import may_write_news_claims
from app.crud.news_evaluation import canonical_sha256, require_utc
from app.crud.news_publication import NewsPublicationError
from app.models.user import User
from app.schemas.news_extraction import ExtractedClaim
from app.schemas.news_publication import OperationalFootprintBinding, OperationalFootprintProvenance
from app.services.news_road_placement_service import get_news_road_placement_provider
from app.services.operational_footprint_service import (
    OperationalFootprintValidation, validate_operational_shape, validate_operational_footprint,
)


class IncidentFootprintRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    record_id: str = Field(min_length=1, max_length=200)
    source_id: str = Field(min_length=1, max_length=200)
    source_url: str = Field(pattern=r"^https://", max_length=1000)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evidence_kind: Literal["authoritative_current_incident"]
    article_id: int = Field(gt=0)
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    claim_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    incident_identity: str = Field(pattern=r"^[0-9a-f]{64}$")
    observed_at: datetime
    city: str = Field(min_length=1, max_length=200)
    barangay: str | None = Field(default=None, max_length=200)
    srid: Literal[4326]
    geometry: dict
    component_sha256: list[str] = Field(min_length=1, max_length=25)


class IncidentFootprintCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")
    format_version: Literal[1]
    records: list[IncidentFootprintRecord] = Field(max_length=500)


class IncidentFootprintProvider:
    def __init__(self, directory: Path | None) -> None:
        self.records: dict[str, IncidentFootprintRecord] = {}
        self.digest: str | None = None
        self.error: str | None = None
        if directory is None:
            self.error = "operational_footprint_catalog_not_configured"
            return
        try:
            manifest_path, catalog_path = directory / "manifest.json", directory / "footprints.json"
            if manifest_path.stat().st_size > 8192 or catalog_path.stat().st_size > 4_000_000:
                raise ValueError("catalog size")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if set(manifest) != {"catalog_sha256", "approved_source_ids"}:
                raise ValueError("manifest fields")
            approved = manifest["approved_source_ids"]
            if not isinstance(approved, list) or not approved or any(not isinstance(item, str) or not item for item in approved):
                raise ValueError("approved sources")
            raw = catalog_path.read_bytes()
            self.digest = hashlib.sha256(raw).hexdigest()
            if self.digest != manifest["catalog_sha256"]:
                raise ValueError("catalog checksum")
            catalog = IncidentFootprintCatalog.model_validate_json(raw)
            for record in catalog.records:
                if record.record_id in self.records or record.source_id not in approved:
                    raise ValueError("unapproved or duplicate source record")
                require_utc(record.observed_at)
                result = validate_operational_shape(record.geometry, geometry_srid=record.srid)
                if not result.is_eligible or record.component_sha256 != [canonical_sha256(part) for part in result.polygon_parts]:
                    raise ValueError("invalid catalog geometry/components")
                # Canonical GeoJSON serialization only: no coordinate repair,
                # clipping, reprojection or reordered/discarded components.
                self.records[record.record_id] = record.model_copy(update={"geometry": result.geojson})
        except (OSError, ValueError, TypeError, KeyError, ValidationError):
            self.records.clear()
            self.error = "invalid_operational_footprint_catalog"


def get_incident_footprint_provider() -> IncidentFootprintProvider:
    directory = os.environ.get("LANES_NEWS_OPERATIONAL_FOOTPRINT_DIR")
    return IncidentFootprintProvider(Path(directory) if directory else None)


def context_for(claim: ExtractedClaim, *, article_id: int, input_sha256: str,
                claim_sha256: str, incident_identity: str) -> dict[str, Any]:
    return dict(article_id=article_id, input_sha256=input_sha256, claim_sha256=claim_sha256,
                incident_identity=incident_identity, observed_at=claim.event_time_resolved,
                city=claim.canonical_city, barangay=claim.canonical_barangay)


def approve_news_footprint(db: Session, footprint: Any, *, geometry_srid: int | None,
        claim: ExtractedClaim, context: dict[str, Any], now: datetime,
        actor_user_id: int | None = None, review_id: str | None = None,
        record_id: str | None = None, source: str | None = None, checksum: str | None = None,
        caller_parent: BaseGeometry | None = None) -> tuple[OperationalFootprintValidation, OperationalFootprintProvenance]:
    """Resolve approval from the server catalog or stored staff identity only."""
    now = require_utc(now)
    observed = require_utc(context["observed_at"])
    if not observed <= now < observed + timedelta(hours=2):
        raise NewsPublicationError("observation_evidence_expired")
    provider = get_news_road_placement_provider()
    parent = provider.locality_boundary(claim)
    if parent is None:
        raise NewsPublicationError("missing_parent_locality_boundary")
    # Catalog geometries are RFC 7946 longitude/latitude. No reprojection or
    # clipping is performed to make a submitted footprint fit.
    parent = set_srid(parent, 4326)
    if caller_parent is not None and canonical_sha256(mapping(caller_parent)) != canonical_sha256(mapping(parent)):
        raise NewsPublicationError("parent_locality_identity_mismatch")
    result = validate_operational_shape(footprint, geometry_srid=geometry_srid, parent_boundary=parent)
    if not result.is_eligible:
        raise NewsPublicationError(result.reason_code)
    components = [canonical_sha256(part) for part in result.polygon_parts]
    catalog_digest = None
    if actor_user_id is not None:
        actor = db.get(User, actor_user_id)
        if (actor is None or not actor.is_active or actor.deleted_at is not None
                or not may_write_news_claims(actor) or not review_id):
            raise NewsPublicationError("unauthorized_footprint_review", 403)
        kind, approved_id = "staff_review", review_id
        approved_source = f"staff:{actor_user_id}"
        approved_checksum = canonical_sha256({"review_id": review_id, "context": {**context, "observed_at": observed.isoformat()},
                                             "geometry": result.geojson, "actor_user_id": actor_user_id})
    else:
        assets = get_incident_footprint_provider()
        if assets.error:
            raise NewsPublicationError(assets.error)
        record = assets.records.get(record_id or "")
        if record is None:
            raise NewsPublicationError("unapproved_operational_footprint_record")
        if any(getattr(record, key) != value for key, value in context.items()):
            raise NewsPublicationError("operational_incident_identity_mismatch")
        if (source is not None and source != record.source_id) or (checksum is not None and checksum != record.source_sha256):
            raise NewsPublicationError("operational_source_identity_mismatch")
        if (record.srid != geometry_srid or canonical_sha256(record.geometry) != canonical_sha256(result.geojson)
                or record.component_sha256 != components):
            raise NewsPublicationError("operational_geometry_evidence_mismatch")
        kind, approved_id, approved_source = record.evidence_kind, record.record_id, record.source_id
        approved_checksum, catalog_digest = record.source_sha256, assets.digest
    binding = OperationalFootprintBinding(evidence_kind=kind, record_id=approved_id,
        actor_user_id=actor_user_id, **context, srid=4326, boundary_revision=provider.revision,
        component_sha256=components, catalog_sha256=catalog_digest)
    provenance = OperationalFootprintProvenance(source=approved_source, source_checksum=approved_checksum,
        geometry_sha256=canonical_sha256(result.geojson), parent_boundary_sha256=canonical_sha256(mapping(parent)), binding=binding)
    verified = validate_operational_footprint(footprint, geometry_srid=geometry_srid,
                                            parent_boundary=parent, trusted_provenance=provenance)
    if not verified.is_eligible:
        raise NewsPublicationError(verified.reason_code)
    return verified, provenance
