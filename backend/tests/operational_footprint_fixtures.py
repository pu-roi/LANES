"""Synthetic server assets for isolated tests; never a production flood extent."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from threading import Lock

from shapely import set_srid
from shapely.geometry import Polygon, mapping
from sqlalchemy import select

from app.crud.news_evaluation import canonical_sha256, validate_run
from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimSource
from app.services.operational_footprint_service import validate_operational_shape

BOUNDARY = set_srid(Polygon([(121.05,14.55),(121.10,14.55),(121.10,14.60),(121.05,14.60)]), 4326)
CATALOG_LOCK = Lock()


class SyntheticLocalityProvider:
    revision = "synthetic-boundary-v1"

    def locality_boundary(self, claim):
        return BOUNDARY if claim.canonical_city == "City of Pasig" and not claim.canonical_barangay else None


def write_catalog(directory: Path, records: list[dict], approved: list[str] | None = None) -> None:
    raw = json.dumps({"format_version": 1, "records": records}, sort_keys=True).encode()
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "footprints.json").write_bytes(raw)
    (directory / "manifest.json").write_text(json.dumps({
        "catalog_sha256": hashlib.sha256(raw).hexdigest(),
        "approved_source_ids": approved or sorted({r["source_id"] for r in records}) or ["synthetic:operational-test"],
    }), encoding="utf-8")


def register_footprint(factory, case_id: int, geometry: dict, *,
                       source: str = "synthetic:operational-test", checksum: str | None = None) -> str:
    from app.services.news_publication_service import _footprint_context
    with factory() as db:
        claim_source = db.scalar(select(NewsClaimSource).where(NewsClaimSource.case_id == case_id)
                                 .order_by(NewsClaimSource.id.desc()))
        run = db.get(NewsExtractionRun, claim_source.extraction_run_id)
        version = db.get(NewsArticleVersion, run.article_version_id)
        article, result = validate_run(run, version)
        context = _footprint_context(claim_source, version, article, result.claims[claim_source.claim_ordinal])
    validated = validate_operational_shape(geometry, geometry_srid=4326)
    # Invalid candidate requests must reach the service without manufactured proof.
    if not validated.is_eligible:
        return "synthetic-invalid-shape"
    context["observed_at"] = context["observed_at"].isoformat()
    record = dict(**context, source_id=source, source_url="https://example.org/current-incident-fixture",
                  source_sha256=checksum or "e" * 64, evidence_kind="authoritative_current_incident",
                  srid=4326, geometry=validated.geojson,
                  component_sha256=[canonical_sha256(part) for part in validated.polygon_parts])
    record_id = "fixture:" + canonical_sha256(record)
    record["record_id"] = record_id
    directory = Path(os.environ["LANES_NEWS_OPERATIONAL_FOOTPRINT_DIR"])
    with CATALOG_LOCK:
        existing = json.loads((directory / "footprints.json").read_text())["records"] if (directory / "footprints.json").exists() else []
        if not any(item["record_id"] == record_id for item in existing):
            existing.append(record)
            write_catalog(directory, existing)
    return record_id
