"""Read retained news lineage, independent of today's publication projection.

Only exact decision sources / import run references are followed. Current article
versions and current case revisions cannot replace evidence behind an old event.
"""
from __future__ import annotations

from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime, Integer, String, cast, func, literal, or_, select, union_all
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimDecision as Decision, NewsClaimSource as Source, NewsClaimZoneLink as Link
from app.models.report import FloodAvoidanceZone as Zone, FloodEvent as Event, FloodReport as Report, FloodEventTimelineEntry as Timeline
from app.models.report import FloodEventLocation
from app.models.report import FloodReportModerationOutcome as Outcome
from app.schemas.historical_news import HistoricalNewsMetadata

PHT = ZoneInfo('Asia/Manila')


def evidence_refs() -> Any:
    """Bounded SQL references; do not materialize full extraction results."""
    legacy = select(Zone.event_id.label('event_id'), Link.zone_id.label('zone_id'),
        Source.extraction_run_id.label('run_id'), Source.claim_ordinal.label('claim_index'),
        cast(literal(None), String).label('group_id'), Decision.observed_at.label('observed_at'),
        Decision.snapshot.label('snapshot'), cast(literal(None), JSONB).label('metadata'))
    legacy = legacy.select_from(Link).join(Zone, Zone.id == Link.zone_id).join(
        Decision, Decision.id == Link.decision_id).join(Source,
        Source.id == cast(Decision.snapshot['claim_source_id'].as_string(), Integer))
    from sqlalchemy.orm import aliased
    older = aliased(Timeline)
    latest_import = select(func.max(older.id)).where(older.event_id==Timeline.event_id,
        older.entry_type=='historical_import',
        older.snapshot_json['run_id'].as_string()==Timeline.snapshot_json['run_id'].as_string(),
        older.snapshot_json['group_id'].as_string()==Timeline.snapshot_json['group_id'].as_string(),
        older.snapshot_json['schema_version'].as_string()=='historical-import-v1').correlate(Timeline).scalar_subquery()
    imported = select(Timeline.event_id, cast(literal(None), Integer).label('zone_id'),
        cast(Timeline.snapshot_json['run_id'].as_string(), Integer).label('run_id'),
        cast(literal(None), Integer).label('claim_index'),
        Timeline.snapshot_json['group_id'].as_string().label('group_id'),
        cast(Timeline.snapshot_json['observed_at'].as_string(), DateTime(timezone=True)).label('observed_at'),
        cast(literal(None), JSONB).label('snapshot'), Timeline.snapshot_json.label('metadata')).where(
            Timeline.entry_type == 'historical_import',
            Timeline.id == latest_import,
            Timeline.snapshot_json['schema_version'].as_string() == 'historical-import-v1')
    return union_all(legacy, imported).subquery('history_news_refs')


def news_summary() -> Any:
    refs = evidence_refs()
    return select(refs.c.event_id,
        func.count(func.distinct(NewsArticleVersion.article_id)).label('news_article_count'),
        func.count(func.distinct(func.concat(refs.c.run_id, ':', func.coalesce(refs.c.group_id,
            cast(refs.c.claim_index, String))))).label('news_evidence_count'),
        func.min(refs.c.observed_at).label('news_observed_at')).select_from(refs).join(
            NewsExtractionRun, NewsExtractionRun.id == refs.c.run_id).join(
            NewsArticleVersion, NewsArticleVersion.id == NewsExtractionRun.article_version_id
        ).group_by(refs.c.event_id).subquery('history_news_summary')


def has_reports(event_column: Any = None) -> Any:
    """Durable report lineage survives soft deletion/status changes.

    Display counters separately count approved, non-deleted submissions.
    """
    column = Event.id if event_column is None else event_column
    return select(Report.id).where(Report.event_id == column).correlate_except(Report).exists()


def legacy_news_instant() -> Any:
    # Only creation ownership establishes news-origin timing. Supporting news
    # attached to a citizen incident never replaces that incident's timing.
    return select(func.min(Decision.observed_at)).select_from(Link).join(Zone,
        Zone.id == Link.zone_id).join(Decision, Decision.id == Link.decision_id).where(
            Zone.event_id == Event.id, Link.relation == 'created').correlate_except(Link, Zone, Decision).scalar_subquery()


def legacy_news_event() -> Any:
    return news_created_event() & ~citizen_origin_event()


def citizen_origin_event() -> Any:
    approved = select(Outcome.id).where(Outcome.event_id == Event.id,
        Outcome.outcome == 'approved', Outcome.acted_at == Event.verified_at).correlate_except(Outcome).exists()
    original_report = select(Report.id).where(Report.event_id == Event.id,
        Report.created_at == Event.first_reported_at).correlate_except(Report).exists()
    return approved | original_report


def news_timing_event() -> Any:
    from app.services.historical_news_metadata import metadata_field
    created_import = select(Timeline.id).where(Timeline.event_id == Event.id,
        Timeline.entry_type == 'historical_import', Timeline.snapshot_json['schema_version'].as_string() == 'historical-import-v1',
        or_(Timeline.snapshot_json['original_event_id'].as_string().is_(None),
            cast(Timeline.snapshot_json['original_event_id'].as_string(), Integer) != Event.id)
    ).correlate_except(Timeline).exists()
    return ((news_created_event() | created_import) & ~citizen_origin_event()) | (
        metadata_field('dataset_id').is_not(None) & ~has_reports())


def news_created_event() -> Any:
    return select(Link.id).join(Zone, Zone.id == Link.zone_id).where(
        Zone.event_id == Event.id, Link.relation == 'created').correlate_except(Link, Zone).exists()


def event_projections(db: Session, ids: list[int], *, locations: dict | None = None) -> dict[int, dict]:
    if not ids:
        return {}
    from app.services.historical_news_metadata import metadata_snapshot
    summary = news_summary()
    statement = select(Event.id, has_reports().label('reports'), news_created_event().label('news_created'), summary.c.news_article_count,
        summary.c.news_evidence_count, legacy_news_instant().label('observed'),
        metadata_snapshot().label('metadata')).select_from(Event).outerjoin(summary, summary.c.event_id == Event.id).where(Event.id.in_(ids))
    if locations is not None:
        statement = statement.add_columns(FloodEventLocation).outerjoin(FloodEventLocation,
            FloodEventLocation.event_id == Event.id).order_by(FloodEventLocation.location_type, FloodEventLocation.display_name)
    statement = statement.add_columns(news_timing_event().label('news_timing'))
    rows = db.execute(statement)
    values = {}
    for row in rows:
        if locations is not None and row.FloodEventLocation is not None:
            locations.setdefault(row.id, []).append(row.FloodEventLocation)
        if row.id in values:
            continue
        metadata = HistoricalNewsMetadata.model_validate(row.metadata) if row.metadata else None
        news = bool(row.news_article_count)
        origin = ('mixed' if news and row.reports else 'news' if news and (row.news_created or metadata)
            else 'user' if row.reports else 'unknown')
        # original_history means appended evidence, not a newly imported lifecycle.
        news_timing = bool(row.news_timing)
        imported = metadata is not None and news_timing
        observed = metadata.observed_at if imported else row.observed if news_timing else None
        day = metadata.occurrence_date if imported else observed.astimezone(PHT).date() if observed else None
        values[row.id] = dict(origin=origin, news_article_count=row.news_article_count or 0,
            news_evidence_count=row.news_evidence_count or 0, occurrence_date=day.isoformat() if day else None,
            observed_at=observed.isoformat() if observed else None,
            observation_precision=metadata.precision if imported else 'instant' if observed else 'unknown',
            news_timing=news_timing, historical=metadata,
            closure_basis=metadata.closure_basis if imported else 'administrative' if news_timing else 'operational')
    return values


def project_values(value: dict, projection: dict | None) -> dict:
    if not projection:
        return value
    result = {**value, **{k: v for k, v in projection.items() if k not in {'historical', 'news_timing'}}}
    metadata = projection['historical']
    result['historical'] = metadata.model_dump(mode='json') if metadata else None
    if projection['news_timing']:
        result.update(duration_seconds=None, duration_minutes=None, duration_basis=projection['closure_basis'])
    return result


def news_sources(db: Session, event_id: int, page: int) -> Any:
    from app.schemas.spatial_browse import InspectionPage, HistoryNewsSource
    refs = evidence_refs()
    # Collapse repeated zone components and repeated lineage for the same source.
    selected = select(refs).where(refs.c.event_id == event_id).distinct(
        refs.c.run_id, refs.c.claim_index, refs.c.group_id).order_by(
        refs.c.run_id, refs.c.claim_index, refs.c.group_id, refs.c.zone_id).subquery()
    total = db.scalar(select(func.count()).select_from(selected))
    pages = max(1, (total + 19)//20); actual = min(page, pages)
    groups = func.jsonb_array_elements(NewsExtractionRun.result['projection']['groups']).table_valued('value').alias('history_groups')
    native_index = select(cast(cast(groups.c.value, JSONB)['claim_index'].astext, Integer)).where(
        cast(groups.c.value, JSONB)['group_id'].astext == selected.c.group_id).correlate(NewsExtractionRun, selected).limit(1).scalar_subquery()
    ordinal = func.coalesce(selected.c.claim_index, native_index)
    rows = db.execute(select(selected, NewsExtractionRun.mode, NewsExtractionRun.status,
        NewsExtractionRun.completed_at, NewsExtractionRun.pipeline_version,
        ordinal.label('resolved_index'), NewsExtractionRun.result['claims'][ordinal].label('claim'),
        NewsArticleVersion.id.label('version_id'), NewsArticleVersion.article_id,
        *[NewsArticleVersion.input_snapshot[key].as_string().label(key) for key in
            ('title', 'publisher', 'canonical_url', 'published_at')],
        (func.length(NewsArticleVersion.input_snapshot['article_text'].as_string()) > 0).label('has_text')
        ).join(NewsExtractionRun, NewsExtractionRun.id == selected.c.run_id).join(
            NewsArticleVersion, NewsArticleVersion.id == NewsExtractionRun.article_version_id).order_by(
            selected.c.run_id, selected.c.group_id, selected.c.claim_index).offset((actual-1)*20).limit(20)).mappings().all()
    items = []
    from app.services.news_sources import load_news_sources
    publishers = {source.id: source.publisher for source in load_news_sources()}
    for row in rows:
        claim = row['claim'] or {}; metadata = row['metadata'] or {}
        public = (row['snapshot'] or {}).get('public') or {}
        items.append(dict(article_id=row['article_id'], article_version_id=row['version_id'],
            run_id=row['run_id'], claim_index=row['resolved_index'], group_id=row['group_id'],
            title=row['title'], publisher=public.get('source_publisher') or publishers.get(row['publisher'], row['publisher']), source_url=row['canonical_url'],
            published_at=row['published_at'], published_date=metadata.get('source_published_date'), captured_text_available=bool(row['has_text']),
            excerpt=metadata.get('source_excerpt') or claim.get('evidence_sentence') or public.get('evidence_excerpt'),
            observed_at=row['observed_at'], occurrence_date=metadata.get('occurrence_date'),
            precision=metadata.get('precision') or ('instant' if row['observed_at'] else 'unknown'),
            road=metadata.get('canonical_road') or claim.get('canonical_road') or claim.get('raw_place_name'),
            city=claim.get('canonical_city') or metadata.get('canonical_city'),
            barangay=claim.get('canonical_barangay') or metadata.get('canonical_barangay'),
            depth_raw=claim.get('depth_raw'), depth_normalized=claim.get('depth_canonical'),
            passability=claim.get('road_passability'), condition=claim.get('condition'),
            extraction_mode=row['mode'], extraction_status=row['status'], completed_at=row['completed_at'],
            pipeline_version=row['pipeline_version'], geometry_basis=metadata.get('geometry_basis') or public.get('geometry_basis'),
            geometry_provenance=(row['snapshot'] or {}).get('operational_provenance'),
            closure_basis=metadata.get('closure_basis') or 'administrative'))
    return InspectionPage(items=[HistoryNewsSource.model_validate(item).model_dump(mode='json') for item in items],
        total=total, pages=pages, page=actual, page_size=20)
