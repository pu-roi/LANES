"""Database operations for the read-only news discovery evidence queue."""

import hashlib
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.news import NewsArticle, NewsArticleFeedEntry, NewsFeedCheckpoint
from app.services.news_discovery_service import NewsCandidate
from app.services.news_feed_service import FeedProbe, NewsEntry
from app.services.news_sources import NewsSource


def content_fingerprint(entry: NewsEntry) -> str:
    normalized = " ".join(re.findall(r"\w+", f"{entry.title} {entry.excerpt}".casefold()))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_checkpoint(db: Session, feed_url: str) -> NewsFeedCheckpoint | None:
    return db.scalar(select(NewsFeedCheckpoint).where(NewsFeedCheckpoint.feed_url == feed_url))


def get_article(db: Session, canonical_url: str) -> NewsArticle | None:
    return db.scalar(select(NewsArticle).where(NewsArticle.canonical_url == canonical_url))


def list_due_refresh_urls(db: Session, sources: tuple[NewsSource, ...], *, now: datetime,
                         refresh_interval: timedelta, max_age: timedelta, limit: int) -> set[str]:
    """Give the oldest captures a turn across all enabled, reviewed feeds."""
    approved = [and_(NewsArticleFeedEntry.source_id == source.id,
                     NewsArticleFeedEntry.feed_url.in_(source.feed_urls))
                for source in sources if source.enabled and source.verified_at]
    if not approved:
        return set()
    rows = db.execute(select(NewsArticle.canonical_url, NewsArticle.fetched_at, NewsArticle.id)
        .join(NewsArticleFeedEntry, NewsArticleFeedEntry.article_id == NewsArticle.id).where(
            or_(*approved), NewsArticle.publisher_source_id == NewsArticleFeedEntry.source_id,
            NewsArticle.article_text.is_not(None),
            or_(NewsArticle.fetched_at.is_(None), NewsArticle.fetched_at <= now - refresh_interval),
            or_(NewsArticle.published_at.between(now - max_age, now),
                (NewsArticle.published_at.is_(None) & NewsArticle.first_seen_at.between(now - max_age, now))),
        ).distinct().order_by(NewsArticle.fetched_at.asc(), NewsArticle.id).limit(limit)).all()
    return {row.canonical_url for row in rows}


def list_due_feed_articles(db: Session, source: NewsSource, feed_url: str, *, now: datetime,
                          refresh_interval: timedelta, max_age: timedelta, limit: int,
                          refresh_urls: set[str]) -> list[NewsEntry]:
    """Bounded saved feed provenance for body refresh when RSS returns 304."""
    rows = db.execute(select(NewsArticle, NewsArticleFeedEntry).join(
        NewsArticleFeedEntry, NewsArticleFeedEntry.article_id == NewsArticle.id,
    ).where(
        NewsArticleFeedEntry.source_id == source.id,
        NewsArticleFeedEntry.feed_url == feed_url,
        NewsArticle.publisher_source_id == source.id,
        NewsArticle.canonical_url.in_(refresh_urls),
        NewsArticle.article_text.is_not(None),
        or_(NewsArticle.fetched_at.is_(None), NewsArticle.fetched_at <= now - refresh_interval),
        or_(NewsArticle.published_at.between(now - max_age, now),
            (NewsArticle.published_at.is_(None) & NewsArticle.first_seen_at.between(now - max_age, now))),
    ).order_by(NewsArticle.fetched_at.asc(), NewsArticle.id, NewsArticleFeedEntry.id).limit(limit)).all()
    return [NewsEntry(source.id, source.publisher, feed_url, feed.feed_guid,
                      article.title, article.excerpt or "", article.canonical_url,
                      article.published_at.replace(tzinfo=timezone.utc) if article.published_at
                      and article.published_at.tzinfo is None else article.published_at)
            for article, feed in rows]


def save_checkpoint(db: Session, probe: FeedProbe) -> NewsFeedCheckpoint:
    checkpoint = get_checkpoint(db, probe.feed_url)
    if checkpoint is None:
        checkpoint = NewsFeedCheckpoint(source_id=probe.source_id, feed_url=probe.feed_url)
        db.add(checkpoint)
    checkpoint.source_id = probe.source_id
    checkpoint.last_checked_at = datetime.now(timezone.utc)
    if probe.status in {"parsed", "empty", "unchanged"}:
        checkpoint.last_success_at = checkpoint.last_checked_at
        checkpoint.last_error = None
        checkpoint.etag = probe.etag
        checkpoint.last_modified = probe.last_modified
    else:
        checkpoint.last_error = (probe.error or probe.status)[:2000]
    return checkpoint


def save_candidate(db: Session, entry: NewsEntry, candidate: NewsCandidate | None,
                   *, local_update_only: bool = False) -> NewsArticle:
    """Save article plus feed provenance; repeated URLs/GUIDs update their seen time."""
    from app.crud.news_processing import enqueue_article

    if candidate is not None and (candidate.source_id != entry.source_id or candidate.article_url != entry.article_url):
        raise ValueError("Captured article identity does not match its feed entry")

    now = datetime.now(timezone.utc)
    fingerprint = content_fingerprint(entry)
    article = get_article(db, entry.article_url)
    if article is None:
        article = NewsArticle(
            canonical_url=entry.article_url,
            publisher_source_id=entry.source_id,
            title=entry.title,
            excerpt=entry.excerpt,
            published_at=entry.published_at,
            fetched_at=candidate.fetched_at if candidate else None,
            first_seen_at=now,
            last_seen_at=now,
            article_text=candidate.article_text if candidate else None,
            article_error=candidate.article_error if candidate else None,
            content_fingerprint=fingerprint,
            review_state="local_update" if local_update_only else "pending",
        )
        db.add(article)
        db.flush()
    else:
        enqueue_article(db, article)  # Preserve the successful input before replacing it.
        if article.review_state == "local_update" and not local_update_only:
            article.review_state = "pending"  # Newly observed flooding follows normal processing.
        article.last_seen_at = now
        # A failed refresh must not relabel the last successful body as a newer
        # observation. Preserve its metadata/time; expose the refresh failure.
        failed_refresh = candidate is not None and candidate.article_text is None and article.article_text is not None
        if not failed_refresh and (candidate is not None or article.article_text is None):
            article.title = entry.title
            article.excerpt = entry.excerpt
            article.published_at = entry.published_at or article.published_at
            article.content_fingerprint = fingerprint
        if candidate is not None:
            article.fetched_at = candidate.fetched_at
            if candidate.article_text is not None:
                # Preserve the old immutable input above, then bind the new
                # body to its actual capture identity. Admission still checks
                # the registered ID and host; an unregistered refresh must not
                # inherit approval from an older body.
                article.publisher_source_id = entry.source_id
                article.article_text = candidate.article_text
                article.article_error = None
            else:
                article.article_error = candidate.article_error
    feed_entry = db.scalar(select(NewsArticleFeedEntry).where(
        NewsArticleFeedEntry.source_id == entry.source_id,
        NewsArticleFeedEntry.feed_url == entry.feed_url,
        NewsArticleFeedEntry.feed_guid == entry.feed_id,
    ))
    if feed_entry is None:
        db.add(NewsArticleFeedEntry(
            article_id=article.id,
            source_id=entry.source_id,
            feed_url=entry.feed_url,
            feed_guid=entry.feed_id,
            first_seen_at=now,
            last_seen_at=now,
            raw_metadata={"title": entry.title, "excerpt": entry.excerpt,
                          "published_at": entry.published_at.isoformat() if entry.published_at else None},
        ))
    else:
        feed_entry.last_seen_at = now
        feed_entry.article_id = article.id
    db.flush()
    enqueue_article(db, article)
    return article


def list_pending_articles(db: Session, limit: int) -> list[NewsArticle]:
    return list(db.scalars(select(NewsArticle).where(NewsArticle.review_state == "pending")
                           .options(selectinload(NewsArticle.feed_entries))
                           .order_by(NewsArticle.last_seen_at.desc()).limit(limit)))


def list_feed_checkpoints(db: Session) -> list[NewsFeedCheckpoint]:
    return list(db.scalars(select(NewsFeedCheckpoint).order_by(NewsFeedCheckpoint.source_id)))
