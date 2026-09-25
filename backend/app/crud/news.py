"""Database operations for the read-only news discovery evidence queue."""

import hashlib
import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.news import NewsArticle, NewsArticleFeedEntry, NewsFeedCheckpoint
from app.services.news_discovery_service import NewsCandidate
from app.services.news_feed_service import FeedProbe, NewsEntry


def content_fingerprint(entry: NewsEntry) -> str:
    normalized = " ".join(re.findall(r"\w+", f"{entry.title} {entry.excerpt}".casefold()))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_checkpoint(db: Session, feed_url: str) -> NewsFeedCheckpoint | None:
    return db.scalar(select(NewsFeedCheckpoint).where(NewsFeedCheckpoint.feed_url == feed_url))


def get_article(db: Session, canonical_url: str) -> NewsArticle | None:
    return db.scalar(select(NewsArticle).where(NewsArticle.canonical_url == canonical_url))


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


def save_candidate(db: Session, entry: NewsEntry, candidate: NewsCandidate | None) -> NewsArticle:
    """Save article plus feed provenance; repeated URLs/GUIDs update their seen time."""
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
            review_state="pending",
        )
        db.add(article)
        db.flush()
    else:
        article.last_seen_at = now
        article.title = entry.title
        article.excerpt = entry.excerpt
        article.published_at = entry.published_at or article.published_at
        article.content_fingerprint = fingerprint
        if candidate is not None:
            article.fetched_at = candidate.fetched_at
            if candidate.article_text is not None:
                article.article_text = candidate.article_text
                article.article_error = None
            elif article.article_text is None:
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
    return article


def list_pending_articles(db: Session, limit: int) -> list[NewsArticle]:
    return list(db.scalars(select(NewsArticle).where(NewsArticle.review_state == "pending")
                           .options(selectinload(NewsArticle.feed_entries))
                           .order_by(NewsArticle.last_seen_at.desc()).limit(limit)))


def list_feed_checkpoints(db: Session) -> list[NewsFeedCheckpoint]:
    return list(db.scalars(select(NewsFeedCheckpoint).order_by(NewsFeedCheckpoint.source_id)))
