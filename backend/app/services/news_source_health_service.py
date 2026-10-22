"""Explain registry, worker selection and persisted retrieval independently."""
from dataclasses import asdict
from sqlalchemy.orm import Session
from app.crud.news_source_health import source_health_rows
from app.schemas.news_candidate import NewsSourceSummary, NewsFeedHealth
from app.services.configuration_service import read_configuration, selected_news_sources
from app.services.news_sources import load_news_sources, NewsSource


def read_source_health(db: Session, sources: tuple[NewsSource, ...] | None = None) -> list[NewsSourceSummary]:
    sources = load_news_sources() if sources is None else sources
    config = read_configuration(db)
    selected = {source.id for source in selected_news_sources(db, sources)}
    checkpoints, rows = source_health_rows(db, tuple(source.id for source in sources),
        tuple((source.id,url) for source in sources for url in source.feed_urls))
    saved = {(row.source_id, row.feed_url): row for row in checkpoints}
    counts = {(source, body): count for source, body, count in rows}
    result = []
    for source in sources:
        feeds = []
        for url in source.feed_urls:
            checkpoint = saved.get((source.id, url))
            checked = checkpoint is not None and checkpoint.last_checked_at is not None
            error = bool(checked and checkpoint.last_error)
            successful = bool(checked and checkpoint.last_success_at
                              and checkpoint.last_success_at >= checkpoint.last_checked_at)
            feeds.append(NewsFeedHealth(feed_url=url, status='error' if error else 'ok' if successful else 'not_recorded',
                last_checked_at=checkpoint.last_checked_at if checkpoint else None,
                last_success_at=checkpoint.last_success_at if checkpoint else None,
                error_code='feed_retrieval_failed' if error else None))
        result.append(NewsSourceSummary(**asdict(source),
            registry_eligible=bool(source.enabled and source.verified_at and source.feed_urls),
            selected_for_collection=source.id in selected,
            collection_active=config.news_collection_enabled and source.id in selected,
            feed_health=feeds, body_counts={key: counts.get((source.id, key), 0) for key in ('available','missing','error')}))
    return result
