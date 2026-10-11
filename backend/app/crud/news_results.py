"""Paginate JSON claim rows in SQL, never load the entire extraction backlog."""

from collections.abc import Callable
from typing import Any

from sqlalchemy import DateTime, Integer, Text, and_, cast, column, func, or_, select, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement, Select

from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.schemas.news_extraction import FloodCondition
from app.schemas.news_results import PlacementFilter, ResultOrder
from app.crud.news_browsing import latest_article_runs
from app.services.news_evidence_policy import FLOOD_OBSERVATION_PATTERN, HYPOTHETICAL_FLOOD_PATTERN, METRO_CITY_PATTERN, NON_OBSERVATION_PATTERN, OBSERVED_EVENT_PATTERN


def result_rows(db: Session, *, latest_only: bool = False) -> tuple[Select, Callable[[str], ColumnElement], ColumnElement, Callable[[str], ColumnElement]]:
    run, version = NewsExtractionRun, NewsArticleVersion
    if db.get_bind().dialect.name == "postgresql":
        rows = func.jsonb_array_elements(run.result["claims"]).table_valued(
            column("claim", JSONB), with_ordinality="ordinal",
        ).render_derived(name="claims")
        claim, index = rows.c.claim, cast(rows.c.ordinal - 1, Integer)
        value = lambda name: cast(claim.op("->>")(name), Text)
        placement = cast(claim.op("->")("road_placement").op("->>")("status"), Text)
        source = lambda name: version.input_snapshot[name].astext
        extracted = run.result["extracted_at"].astext
    else:
        rows = func.json_each(run.result, "$.claims").table_valued("key", "value").alias("claims")
        claim, index = rows.c.value, cast(rows.c.key, Integer)
        value = lambda name: func.json_extract(claim, f"$.{name}")
        placement = func.json_extract(claim, "$.road_placement.status")
        source = lambda name: func.json_extract(version.input_snapshot, f"$.{name}")
        extracted = func.json_extract(run.result, "$.extracted_at")
    query = select(run.id.label("run_id"), version.id.label("article_version_id"), version.article_id,
                   index.label("claim_index"), claim.label("claim"), source("title").label("title"),
                   source("publisher").label("publisher_source_id"), source("published_at").label("published_at"),
                   extracted.label("extracted_at"), version.created_at.label("captured_at"), NewsArticle.first_seen_at.label("saved_at")).select_from(run).join(version).join(NewsArticle, NewsArticle.id == version.article_id).join(rows, true()).where(
                       run.status == "completed", run.result.is_not(None))
    if latest_only:
        latest = latest_article_runs()
        query = query.join(latest, and_(latest.c.article_id == version.article_id, latest.c.run_id == run.id))
    return query, value, placement, source


def context_only_claim(value: Callable[[str], ColumnElement]) -> ColumnElement:
    """City/locality qualifiers stay in history without becoming attention items."""
    return cast(func.coalesce(value("uncertainty_reasons"), "[]"), Text).contains('"location_context_only"')


def readable_claim(value: Callable[[str], ColumnElement]) -> ColumnElement:
    """Conservative browsing gate; this does not approve or activate a flood zone."""
    place = func.trim(func.coalesce(value("raw_place_name"), ""))
    evidence = func.trim(func.coalesce(value("evidence_sentence"), ""))
    normalized_evidence = func.lower(evidence)
    city = func.lower(func.trim(func.coalesce(value("canonical_city"), "")))
    psgc = func.coalesce(value("psgc_code"), "")
    truth = lambda field, default: cast(func.coalesce(value(field), default), Text).in_(["true", "1"])
    return and_(
        func.length(place).between(1, 120), func.length(evidence) > 0,
        normalized_evidence.regexp_match(FLOOD_OBSERVATION_PATTERN),
        ~normalized_evidence.regexp_match(HYPOTHETICAL_FLOOD_PATTERN),
        or_(psgc.startswith("13"), and_(psgc == "", city.regexp_match(METRO_CITY_PATTERN))),
        or_(~normalized_evidence.regexp_match(NON_OBSERVATION_PATTERN),
            normalized_evidence.regexp_match(OBSERVED_EVENT_PATTERN)),
        ~place.contains("\n"), or_(place != evidence, func.length(place) <= 60),
        truth("flood_mentioned", "true"),
        ~truth("is_forecast", "false"), ~truth("is_negated", "false"), ~truth("is_historical", "false"),
        ~cast(func.coalesce(value("uncertainty_reasons"), "[]"), Text).contains('"photo_caption_only"'),
        ~context_only_claim(value),
        or_(value("condition").in_(["active", "rising", "receding", "subsided"]),
            func.length(func.trim(func.coalesce(value("depth_raw"), ""))) > 0,
            func.length(func.trim(func.coalesce(value("depth_formatted"), ""))) > 0,
            value("road_passability").in_(["impassable_all", "light_vehicle_closed"])),
    )


def readable_run(db: Session) -> ColumnElement:
    result = NewsExtractionRun.result
    if db.get_bind().dialect.name == "postgresql":
        metadata = result["is_metadata_only"].astext
        errors = func.jsonb_array_length(result["errors"])
    else:
        metadata = func.json_extract(result, "$.is_metadata_only")
        errors = func.json_array_length(result, "$.errors")
    return and_(~cast(func.coalesce(metadata, "false"), Text).in_(["true", "1"]), func.coalesce(errors, 0) == 0)


def list_result_rows(db: Session, *, page: int, page_size: int, search: str, publisher: str | None,
                     condition: FloodCondition | None, placement: PlacementFilter | None,
                     order: ResultOrder) -> tuple[list[dict[str, Any]], int, int, list[str]]:
    query, value, placement_value, source = result_rows(db, latest_only=True)
    query = query.where(readable_claim(value), readable_run(db))
    if search.strip():
        query = query.where(or_(*(item.icontains(search.strip(), autoescape=True) for item in [
            source("title"), value("raw_place_name"), value("canonical_city"), value("canonical_road"), value("evidence_sentence"),
        ])))
    if publisher:
        query = query.where(source("publisher") == publisher)
    if condition:
        query = query.where(value("condition") == condition)
    if placement:
        query = query.where(func.coalesce(placement_value, "not_recorded") == placement)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    pages = max(1, (total + page_size - 1) // page_size)
    actual_page = min(page, pages)
    filtered = query.subquery()
    timestamp = filtered.c.published_at if order == "publication_newest" else filtered.c.extracted_at
    normalized = cast(timestamp, DateTime(timezone=True)) if db.get_bind().dialect.name == "postgresql" else func.julianday(timestamp)
    ordered = normalized.desc().nulls_last()
    rows = list(db.execute(select(filtered).order_by(ordered, filtered.c.run_id.desc(), filtered.c.claim_index).
                           offset((actual_page - 1) * page_size).limit(page_size)).mappings())
    all_rows, all_value, _, _ = result_rows(db, latest_only=True)
    all_rows = all_rows.where(readable_claim(all_value), readable_run(db))
    all_results = all_rows.subquery()
    publishers = list(db.scalars(select(all_results.c.publisher_source_id).distinct().order_by(all_results.c.publisher_source_id)))
    return [dict(row) for row in rows], total, actual_page, publishers


def read_result_row(db: Session, run_id: int, claim_index: int) -> tuple[NewsExtractionRun, NewsArticleVersion] | None:
    if run_id < 1 or claim_index < 0:
        return None
    row = db.execute(select(NewsExtractionRun, NewsArticleVersion).join(NewsArticleVersion).where(
        NewsExtractionRun.id == run_id, NewsExtractionRun.status == "completed",
    )).first()
    if row is None or row[0].result is None or claim_index >= len(row[0].result.get("claims", [])):
        return None
    return row[0], row[1]
