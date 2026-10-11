"""Aggregate current evidence without loading bodies or extraction payloads."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud.news_browsing import article_body_status, latest_article_runs
from app.models.news import NewsArticle, NewsExtractionRun


def read_monitoring_rows(db: Session, limit: int = 10) -> tuple[dict, dict, list]:
    body = article_body_status()
    body_counts = dict(db.execute(select(body, func.count()).group_by(body)).all())
    latest = latest_article_runs()
    status = func.coalesce(NewsExtractionRun.status, "not_recorded")
    processing_counts = dict(db.execute(
        select(status, func.count()).select_from(NewsArticle)
        .outerjoin(latest, latest.c.article_id == NewsArticle.id)
        .outerjoin(NewsExtractionRun, NewsExtractionRun.id == latest.c.run_id)
        .group_by(status)
    ).all())
    issues = list(db.execute(
        select(NewsArticle.id, NewsArticle.title, NewsArticle.publisher_source_id,
               body, NewsArticle.article_error, NewsArticle.last_seen_at)
        .where(body != "available")
        .order_by(NewsArticle.last_seen_at.desc(), NewsArticle.id.desc()).limit(limit)
    ).all())
    return body_counts, processing_counts, issues
