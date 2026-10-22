"""Batch metadata and detail reads for the staff zone queue."""
from collections import defaultdict
from typing import Any

from sqlalchemy import Text, cast, func, select, literal
from sqlalchemy.orm import Session, selectinload

from app.crud.report import avoidance_zones_query
from app.models.report import FloodAvoidanceZone, FloodReport
from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimZoneLink, NewsClaimSource
from app.models.news import NewsExtractionRun
from app.models.user import User


def queue_metadata(db: Session, *, active_only: bool) -> list[dict[str, Any]]:
    zone = FloodAvoidanceZone
    def projected_geometry(value: Any) -> Any:
        if not active_only:
            return literal(None)
        return func.ST_AsBinary(func.ST_Transform(value, 32651)) if db.get_bind().dialect.name == "postgresql" else cast(value, Text)

    geometry = projected_geometry(zone.geometry)
    map_geometry = (func.ST_AsBinary(func.ST_Envelope(zone.geometry)) if db.get_bind().dialect.name == "postgresql" else cast(zone.geometry, Text)) if active_only else literal(None)
    eligible = avoidance_zones_query(db, active_only=active_only)
    rows = eligible.with_entities(zone.id, zone.name, zone.created_at, zone.curated_by_admin_id,
        zone.severity_override, zone.depth_override, zone.admin_notes,
        projected_geometry(zone.source_geometry).label("source_geometry"),
        map_geometry.label("map_geometry"), geometry.label("geometry")).all()
    ids = [row.id for row in rows]
    if not ids:
        return []
    reports: dict[int, list[Any]] = defaultdict(list)
    for row in db.execute(select(FloodReport.zone_id, FloodReport.id, FloodReport.source,
        FloodReport.human_readable_location, FloodReport.city, FloodReport.barangay,
        FloodReport.raw_text, FloodReport.severity, FloodReport.depth,
        projected_geometry(FloodReport.geometry).label("geometry"))
        .where(FloodReport.zone_id.in_(ids), FloodReport.deleted_at.is_(None))
        .order_by(FloodReport.id)).mappings():
        reports[row["zone_id"]].append(row)
    news: dict[int, list[dict[str, Any]]] = defaultdict(list)
    public_keys = ("evidence_excerpt", "source_title", "location_label")
    claim_keys = ("canonical_road", "canonical_city", "canonical_barangay")
    claim = NewsExtractionRun.result["claims"][NewsClaimSource.claim_ordinal]
    statement = select(NewsClaimZoneLink.zone_id,
        *(NewsClaimDecision.snapshot["public"][key].as_string().label(key) for key in public_keys),
        *(claim[key].as_string().label(key) for key in claim_keys))
    statement = (statement.select_from(NewsClaimZoneLink)
        .join(NewsClaimDecision, NewsClaimDecision.id == NewsClaimZoneLink.decision_id)
        .join(NewsClaimCase, NewsClaimCase.id == NewsClaimDecision.case_id)
        .outerjoin(NewsClaimSource, NewsClaimSource.id == NewsClaimDecision.snapshot["claim_source_id"].as_integer())
        .outerjoin(NewsExtractionRun, NewsExtractionRun.id == NewsClaimSource.extraction_run_id)
        .where(NewsClaimZoneLink.zone_id.in_(ids)).order_by(NewsClaimDecision.revision.desc()))
    if active_only:
        statement = statement.where(NewsClaimDecision.revision == NewsClaimCase.revision)
    for item in db.execute(statement).mappings():
        news[item["zone_id"]].append({"snapshot": {"public": {key: item[key] for key in public_keys}},
            "claim": {key: item[key] for key in claim_keys}})
    return [dict(row._mapping, reports=reports[row.id], news=news[row.id]) for row in rows]


def queue_zone_details(db: Session, ids: list[int], *, brief: bool = False) -> list[FloodAvoidanceZone]:
    if not ids:
        return []
    relationship = FloodAvoidanceZone.reports
    if brief:
        ranked = select(FloodReport.id, func.row_number().over(partition_by=FloodReport.zone_id,
            order_by=FloodReport.id).label("rank")).where(FloodReport.zone_id.in_(ids)).subquery()
        relationship = relationship.and_(FloodReport.id.in_(select(ranked.c.id).where(ranked.c.rank <= 20)))
    reports = selectinload(relationship)
    return list(db.scalars(select(FloodAvoidanceZone).where(FloodAvoidanceZone.id.in_(ids)).options(
        reports.selectinload(FloodReport.user).selectinload(User.profile),
        reports.selectinload(FloodReport.user).selectinload(User.role),
        reports.selectinload(FloodReport.survey)).execution_options(populate_existing=True)))


def active_zone_ids(db: Session, ids: list[int]) -> set[int]:
    return {row.id for row in avoidance_zones_query(db, active_only=True)
            .with_entities(FloodAvoidanceZone.id).filter(FloodAvoidanceZone.id.in_(ids)).all()} if ids else set()
