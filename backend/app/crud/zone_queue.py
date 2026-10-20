"""Batch metadata and detail reads for the staff zone queue."""
from collections import defaultdict
from typing import Any

from sqlalchemy import Text, cast, func, select
from sqlalchemy.orm import Session, selectinload

from app.crud.report import avoidance_zones_query
from app.models.report import FloodAvoidanceZone, FloodReport
from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimZoneLink, NewsClaimSource
from app.models.news import NewsExtractionRun
from app.models.user import User


def queue_metadata(db: Session, *, active_only: bool) -> list[dict[str, Any]]:
    zone = FloodAvoidanceZone
    geometry = func.ST_AsGeoJSON(func.ST_Transform(zone.geometry, 32651)) if db.get_bind().dialect.name == "postgresql" else cast(zone.geometry, Text)
    eligible = avoidance_zones_query(db, active_only=active_only)
    rows = eligible.with_entities(zone.id, zone.name, zone.created_at, zone.curated_by_admin_id,
        zone.severity_override, zone.depth_override, zone.admin_notes, geometry.label("geometry")).all()
    ids = [row.id for row in rows]
    if not ids:
        return []
    reports: dict[int, list[Any]] = defaultdict(list)
    for row in db.execute(select(FloodReport.zone_id, FloodReport.id, FloodReport.source,
        FloodReport.human_readable_location, FloodReport.city, FloodReport.barangay,
        FloodReport.raw_text, FloodReport.severity, FloodReport.depth)
        .where(FloodReport.zone_id.in_(ids), FloodReport.deleted_at.is_(None))
        .order_by(FloodReport.id)).mappings():
        reports[row["zone_id"]].append(row)
    news: dict[int, list[dict[str, Any]]] = defaultdict(list)
    statement = select(NewsClaimZoneLink.zone_id, NewsClaimDecision.snapshot, NewsExtractionRun.result, NewsClaimSource.claim_ordinal)
    statement = (statement.select_from(NewsClaimZoneLink)
        .join(NewsClaimDecision, NewsClaimDecision.id == NewsClaimZoneLink.decision_id)
        .join(NewsClaimCase, NewsClaimCase.id == NewsClaimDecision.case_id)
        .outerjoin(NewsClaimSource, NewsClaimSource.id == NewsClaimDecision.snapshot["claim_source_id"].as_integer())
        .outerjoin(NewsExtractionRun, NewsExtractionRun.id == NewsClaimSource.extraction_run_id)
        .where(NewsClaimZoneLink.zone_id.in_(ids)).order_by(NewsClaimDecision.revision.desc()))
    if active_only:
        statement = statement.where(NewsClaimDecision.revision == NewsClaimCase.revision)
    for zone_id, snapshot, result, ordinal in db.execute(statement):
        claims = (result or {}).get("claims", [])
        claim = claims[ordinal] if ordinal is not None and 0 <= ordinal < len(claims) else {}
        news[zone_id].append({"snapshot": snapshot or {}, "claim": claim})
    return [dict(row._mapping, reports=reports[row.id], news=news[row.id]) for row in rows]


def queue_zone_details(db: Session, ids: list[int]) -> list[FloodAvoidanceZone]:
    if not ids:
        return []
    reports = selectinload(FloodAvoidanceZone.reports)
    return list(db.scalars(select(FloodAvoidanceZone).where(FloodAvoidanceZone.id.in_(ids)).options(
        reports.selectinload(FloodReport.user).selectinload(User.profile),
        reports.selectinload(FloodReport.user).selectinload(User.role),
        reports.selectinload(FloodReport.survey))))


def active_zone_ids(db: Session, ids: list[int]) -> set[int]:
    return {row.id for row in avoidance_zones_query(db, active_only=True)
            .with_entities(FloodAvoidanceZone.id).filter(FloodAvoidanceZone.id.in_(ids)).all()} if ids else set()
