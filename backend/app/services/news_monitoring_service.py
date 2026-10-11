"""Report only persisted state; never infer discovery success or publication."""

from sqlalchemy.orm import Session

from app.crud.news_monitoring import read_monitoring_rows
from app.schemas.news_monitoring import NewsMonitoringSummary, NewsRetrievalIssue
from app.services.news_browsing_service import publisher_labels


def read_news_monitoring(db: Session) -> NewsMonitoringSummary:
    bodies, processing, issues = read_monitoring_rows(db)
    labels = publisher_labels()
    return NewsMonitoringSummary(
        articles_total=sum(bodies.values()),
        body_counts={key: bodies.get(key, 0) for key in ("available", "missing", "error")},
        latest_processing_counts={key: processing.get(key, 0) for key in
            ("not_recorded", "pending", "processing", "completed", "retry_wait", "failed")},
        recent_retrieval_issues=[NewsRetrievalIssue(
            article_id=id, title=title, publisher=labels.get(publisher, publisher),
            body_status=body, article_error=error, last_seen_at=seen,
        ) for id, title, publisher, body, error, seen in issues],
    )
