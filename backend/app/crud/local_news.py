"""Bounded recent article reads, independent of extraction/publication state."""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, load_only

from app.models.news import NewsArticle

MAX_LOCAL_NEWS_CANDIDATES = 200


def recent_local_news_candidates(db: Session, *, source_ids: tuple[str, ...],
                                 since: datetime, now: datetime) -> list[NewsArticle]:
    if not source_ids:
        return []
    query = select(NewsArticle).where(
        NewsArticle.publisher_source_id.in_(source_ids),
        NewsArticle.published_at >= since, NewsArticle.published_at <= now,
        NewsArticle.article_error.is_(None),
        func.length(func.trim(NewsArticle.article_text)).between(1, 100_000),
        func.length(func.trim(NewsArticle.title)) > 0,
        NewsArticle.review_state.not_in(("rejected", "suppressed")),
    ).options(load_only(NewsArticle.id, NewsArticle.publisher_source_id, NewsArticle.title,
        NewsArticle.excerpt, NewsArticle.canonical_url, NewsArticle.published_at, NewsArticle.article_text)
    ).order_by(NewsArticle.published_at.desc(), NewsArticle.id.desc()).limit(MAX_LOCAL_NEWS_CANDIDATES)
    return list(db.scalars(query))
