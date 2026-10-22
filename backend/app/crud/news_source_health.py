"""Aggregate saved retrieval state; no publisher probes or article body loads."""
from sqlalchemy import func, select, tuple_
from sqlalchemy.orm import Session
from app.crud.news_browsing import article_body_status
from app.models.news import NewsArticle, NewsFeedCheckpoint


def source_health_rows(db: Session, source_ids: tuple[str, ...], feeds: tuple[tuple[str,str], ...]) -> tuple[list[NewsFeedCheckpoint], list]:
    body = article_body_status()
    checkpoints = list(db.scalars(select(NewsFeedCheckpoint).where(
        tuple_(NewsFeedCheckpoint.source_id,NewsFeedCheckpoint.feed_url).in_(feeds))))
    counts = list(db.execute(select(NewsArticle.publisher_source_id, body, func.count()).where(
        NewsArticle.publisher_source_id.in_(source_ids)).group_by(
        NewsArticle.publisher_source_id, body)))
    return checkpoints, counts
