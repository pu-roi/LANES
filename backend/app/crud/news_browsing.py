"""Bounded, deterministic staff reads over existing news evidence tables."""

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, defer, selectinload
from sqlalchemy.sql.selectable import Subquery

from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.schemas.news_browsing import ArticleOrder, BodyStatus, ProcessingStatus


def article_body_status() -> object:
    return case(
        (NewsArticle.article_error.is_not(None), "error"),
        (func.length(func.trim(NewsArticle.article_text)) > 0, "available"),
        else_="missing",
    )


def latest_article_runs() -> Subquery:
    """Select the newest recorded run, including failures and pending attempts."""
    return select(NewsArticleVersion.article_id, func.max(NewsExtractionRun.id).label("run_id")).join(
        NewsExtractionRun, NewsExtractionRun.article_version_id == NewsArticleVersion.id,
    ).group_by(NewsArticleVersion.article_id).subquery()


def list_articles(
    db: Session, *, page: int, page_size: int, search: str, publisher: str | None,
    body: BodyStatus | None, processing: ProcessingStatus | None, order: ArticleOrder,
) -> tuple[list[tuple[NewsArticle, str, str, int | None]], int, int, list[str]]:
    latest = latest_article_runs()
    body_status = article_body_status()
    processing_status = func.coalesce(NewsExtractionRun.status, "not_recorded")
    query = select(NewsArticle, body_status, processing_status, NewsExtractionRun.id).outerjoin(
        latest, latest.c.article_id == NewsArticle.id,
    ).outerjoin(NewsExtractionRun, NewsExtractionRun.id == latest.c.run_id)
    if search.strip():
        # Literal contains search: user input cannot introduce SQL wildcards.
        query = query.where(or_(NewsArticle.title.icontains(search.strip(), autoescape=True),
                               NewsArticle.excerpt.icontains(search.strip(), autoescape=True)))
    if publisher:
        query = query.where(NewsArticle.publisher_source_id == publisher)
    if body:
        query = query.where(body_status == body)
    if processing:
        query = query.where(processing_status == processing)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    pages = max(1, (total + page_size - 1) // page_size)
    actual_page = min(page, pages)
    ordering = NewsArticle.published_at.desc().nulls_last() if order == "publication_newest" else NewsArticle.last_seen_at.desc()
    rows = db.execute(query.options(defer(NewsArticle.article_text)).order_by(
        ordering, NewsArticle.id.desc(),
    ).offset((actual_page - 1) * page_size).limit(page_size)).all()
    publishers = list(db.scalars(select(NewsArticle.publisher_source_id).distinct().order_by(NewsArticle.publisher_source_id)))
    return [tuple(row) for row in rows], total, actual_page, publishers


def get_article_detail_rows(
    db: Session, article_id: int, limit: int = 20,
) -> tuple[NewsArticle, list[NewsExtractionRun], list[NewsArticleVersion], int] | None:
    article = db.scalar(select(NewsArticle).where(NewsArticle.id == article_id).options(selectinload(NewsArticle.feed_entries)))
    if article is None:
        return None
    query = select(NewsExtractionRun).join(NewsArticleVersion).where(NewsArticleVersion.article_id == article_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    runs = list(db.scalars(query.order_by(NewsExtractionRun.id.desc()).limit(limit)))
    version_ids = {run.article_version_id for run in runs}
    versions = list(db.scalars(select(NewsArticleVersion).where(
        NewsArticleVersion.article_id == article_id, NewsArticleVersion.id.in_(version_ids),
    ).order_by(NewsArticleVersion.id.desc()))) if version_ids else []
    return article, runs, versions, total
