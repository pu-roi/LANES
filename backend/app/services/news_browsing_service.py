"""Assemble existing evidence and immutable inputs without extracting or mutating."""

from sqlalchemy.orm import Session

from app.crud.news_browsing import get_article_detail_rows, list_articles
from app.schemas.news_browsing import (
    ArticleOrder, BodyStatus, NewsArticleDetail, NewsArticleListItem, NewsArticlePage,
    NewsArticleVersionSummary, NewsPublisherOption, ProcessingStatus,
)
from app.schemas.news_candidate import NewsArticleSummary, NewsExtractionRunSummary
from app.services.news_sources import load_news_sources
from app.services.news_presentation_service import summarize_news_claim


def publisher_labels() -> dict[str, str]:
    return {source.id: source.publisher for source in load_news_sources()}


def browse_news_articles(
    db: Session, *, page: int, page_size: int, search: str, publisher: str | None,
    body: BodyStatus | None, processing: ProcessingStatus | None, order: ArticleOrder,
) -> NewsArticlePage:
    rows, total, actual_page, publishers = list_articles(
        db, page=page, page_size=page_size, search=search, publisher=publisher,
        body=body, processing=processing, order=order,
    )
    labels = publisher_labels()
    return NewsArticlePage(
        items=[NewsArticleListItem(
            id=row.id, title=row.title, excerpt=row.excerpt, canonical_url=row.canonical_url,
            publisher_source_id=row.publisher_source_id, publisher=labels.get(row.publisher_source_id, row.publisher_source_id),
            published_at=row.published_at, last_seen_at=row.last_seen_at, body_status=body_status,
            article_error=row.article_error, review_state=row.review_state, processing_status=processing_status, latest_run_id=run_id,
        ) for row, body_status, processing_status, run_id in rows],
        total=total, page=actual_page, page_size=page_size, pages=max(1, (total + page_size - 1) // page_size),
        publishers=[NewsPublisherOption(id=value, label=labels.get(value, value)) for value in publishers],
    )


def read_news_article_detail(db: Session, article_id: int) -> NewsArticleDetail | None:
    rows = get_article_detail_rows(db, article_id)
    if rows is None:
        return None
    article, runs, versions, total = rows
    run_summaries = [NewsExtractionRunSummary.model_validate(run) for run in runs]
    body_status = "error" if article.article_error is not None else "available" if (article.article_text or "").strip() else "missing"
    return NewsArticleDetail(
        article=NewsArticleSummary.model_validate(article),
        publisher=publisher_labels().get(article.publisher_source_id, article.publisher_source_id),
        body_status=body_status,
        runs=run_summaries,
        versions=[NewsArticleVersionSummary.model_validate(version) for version in versions],
        history_total=total, history_limit=20,
        flood_summaries={run.id: [summarize_news_claim(claim) for claim in run.result.claims]
                        for run in run_summaries if run.status == "completed" and run.result is not None},
    )
