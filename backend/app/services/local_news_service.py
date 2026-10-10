"""Source-labeled local news articles; no audit, publication or map writes."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.crud.local_news import recent_local_news_candidates
from app.schemas.local_news import LocalNewsArticle, LocalNewsUpdates
from app.services.news_discovery_service import MAX_NEWS_AGE, body_has_metro_manila_flood_claim
from app.services.news_feed_service import NewsEntry, canonical_article_url
from app.services.news_sources import NewsSource, load_news_sources


def local_news_clock() -> datetime:
    return datetime.now(timezone.utc)


def browse_local_news(db: Session, *, limit: int = 5, now: datetime | None = None,
                      sources: tuple[NewsSource, ...] | None = None) -> LocalNewsUpdates:
    if not 1 <= limit <= 10:
        raise ValueError("Local news limit must be between 1 and 10")
    now = now or local_news_clock()
    approved = {source.id: source for source in (sources if sources is not None else load_news_sources())
                if source.enabled and source.verified_at is not None}
    rows = recent_local_news_candidates(db, source_ids=tuple(approved), since=now - MAX_NEWS_AGE, now=now)
    items: list[LocalNewsArticle] = []
    for article in rows:
        source = approved[article.publisher_source_id]
        source_url = canonical_article_url(article.canonical_url, source)
        if source_url is None:
            continue
        # Previously saved articles can be unrelated or have revised bodies.
        # Reuse discovery's local-evidence screen, without durable extraction or AI.
        entry = NewsEntry(source.id, source.publisher, "", "", article.title,
                          article.excerpt, source_url, article.published_at)
        if not body_has_metro_manila_flood_claim(entry, article.article_text):
            continue
        published = article.published_at
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        items.append(LocalNewsArticle(id=article.id, title=article.title, publisher=source.publisher,
                                     source_url=source_url, published_at=published))
        if len(items) == limit:
            break
    return LocalNewsUpdates(items=items, as_of=now)
