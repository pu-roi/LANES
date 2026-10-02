"""Explain retrieval, processing and questionable evidence to staff."""

from sqlalchemy.orm import Session

from app.crud.news_collection import list_collection
from app.schemas.news_browsing import NewsPublisherOption
from app.schemas.news_collection import CollectionFilter, NewsCollectionItem, NewsCollectionPage
from app.services.news_browsing_service import publisher_labels

COLLECTION_LABELS = {
    "ready": ("Locations available", "Reported locations appear in the main list. Exact map placement may still need verification."),
    "needs_checking": ("Needs checking", "Some extracted mentions do not clearly describe a flood at a usable place, or the extraction has incomplete evidence."),
    "no_locations": ("No flood locations", "Processing completed without extracting any flood locations."),
    "waiting": ("Waiting for processing", "No extraction is recorded for this saved article."),
    "processing": ("Processing", "The newest extraction is queued, running or waiting for another attempt."),
    "processing_failed": ("Processing failed", "The newest extraction failed. Older results are available only in processing history."),
    "retrieval_failed": ("Article retrieval failed", "The latest attempt to retrieve the article text failed."),
    "missing_text": ("Article text missing", "Only article metadata is saved; the full article text is unavailable."),
}


def browse_news_collection(db: Session, *, page: int, page_size: int, search: str,
                           publisher: str | None, status: CollectionFilter) -> NewsCollectionPage:
    rows, total, actual_page, counts, publishers = list_collection(db, page=page, page_size=page_size,
        search=search, publisher=publisher, status=status)
    labels = publisher_labels()
    items = []
    for article, body, processing, run_id, state, locations, questionable in rows:
        label, reason = COLLECTION_LABELS[state]
        items.append(NewsCollectionItem(id=article.id, title=article.title, excerpt=article.excerpt,
            canonical_url=article.canonical_url, publisher_source_id=article.publisher_source_id,
            publisher=labels.get(article.publisher_source_id, article.publisher_source_id), published_at=article.published_at,
            last_seen_at=article.last_seen_at, body_status=body, article_error=article.article_error,
            review_state=article.review_state, processing_status=processing, latest_run_id=run_id,
            collection_status=state, collection_label=label, collection_reason=reason,
            location_count=locations, questionable_count=questionable))
    return NewsCollectionPage(items=items, total=total, page=actual_page, page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size), counts={key: counts.get(key, 0) for key in COLLECTION_LABELS},
        publishers=[NewsPublisherOption(id=value, label=labels.get(value, value)) for value in publishers])
