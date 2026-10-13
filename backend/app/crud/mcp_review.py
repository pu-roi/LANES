"""Unfiltered saved extraction reads. No writes or worker ownership."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.news import NewsArticleVersion, NewsExtractionRun


def saved_runs(db: Session, page: int, page_size: int) -> tuple[list[tuple], int]:
    predicate = NewsExtractionRun.status == "completed"
    total = db.scalar(select(func.count()).select_from(NewsExtractionRun).where(predicate)) or 0
    rows = db.execute(select(NewsExtractionRun.id, NewsExtractionRun.pipeline_version,
        NewsExtractionRun.completed_at, NewsArticleVersion.id, NewsArticleVersion.article_id,
        NewsArticleVersion.input_fingerprint, NewsArticleVersion.input_snapshot["title"].astext,
        NewsArticleVersion.input_snapshot["publisher"].astext,
        NewsArticleVersion.input_snapshot["published_at"].astext,
        func.jsonb_array_length(NewsExtractionRun.result["claims"]))
        .join(NewsArticleVersion).where(predicate)
        .order_by(NewsExtractionRun.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return rows, total


def saved_run(db: Session, run_id: int) -> tuple[NewsExtractionRun, NewsArticleVersion] | None:
    return db.execute(select(NewsExtractionRun, NewsArticleVersion).join(NewsArticleVersion)
        .where(NewsExtractionRun.id == run_id, NewsExtractionRun.status == "completed")).first()
