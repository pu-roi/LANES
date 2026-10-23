"""Compare saved source bodies without changing immutable evidence or fetching URLs."""
from __future__ import annotations

from typing import TypeVar

from sqlalchemy.orm import Session

from app.models.news import NewsArticle, NewsArticleVersion
from app.schemas.news_browsing import NewsCapturedInput
from app.schemas.news_results import NewsNativeGroupDetail, NewsResultDetail, NewsSourceReview
from app.services.news_saved_run_service import SavedRunReadError

Detail = TypeVar('Detail', NewsResultDetail, NewsNativeGroupDetail)


def compare_source_capture(article: NewsArticle, version: NewsArticleVersion) -> NewsSourceReview:
    if article.id != version.article_id:
        raise SavedRunReadError('news_source_article_mismatch')
    current = None
    if (article.article_text or '').strip():
        current = NewsCapturedInput(canonical_url=article.canonical_url,
            publisher=article.publisher_source_id, title=article.title, excerpt=article.excerpt,
            article_text=article.article_text, published_at=article.published_at)
    state = ('current_unavailable' if current is None else 'matching_capture'
        if current.article_text == version.input_snapshot.get('article_text') else 'different_capture')
    return NewsSourceReview(state=state, current_input=current,
        current_fetched_at=article.fetched_at, selected_captured_at=version.created_at)


def with_source_review(db: Session, detail: Detail | None) -> Detail | None:
    if detail is None:
        return None
    article = db.get(NewsArticle, detail.item.article_id)
    version = db.get(NewsArticleVersion, detail.item.article_version_id)
    if article is None or version is None:
        raise SavedRunReadError('news_source_capture_missing')
    updates = {'source_review': compare_source_capture(article, version)}
    if isinstance(detail, NewsNativeGroupDetail):
        updates['supporting_passages'] = supporting_passages(detail.group, version.input_snapshot['article_text'])
        target = detail.group.get('normalizations', {}).get('resolution_target_id')
        resolution = detail.result.provenance.get('llm_resolution', {})
        rows = [row for row in resolution.get('results', []) if target and row.get('target_id') == target]
        if len(rows) == 1 and rows[0].get('depth_scope') in ('shared', 'individual'):
            updates['depth_scope'] = rows[0]['depth_scope']
    return detail.model_copy(update=updates)


def supporting_passages(group: dict, text: str) -> list[str]:
    """Use saved field-specific quotes, not the intervening article/page chrome."""
    audit = group.get('normalizations', {}).get('audit', {})
    passages = set()
    for field in ('place', 'time', 'depth', 'status', 'access'):
        for item in audit.get(field, {}).get('evidence', []):
            start, end, quote = item.get('start'), item.get('end'), item.get('quote')
            if (type(start) is not int or type(end) is not int or not isinstance(quote, str)
                    or not 0 <= start < end <= len(text) or text[start:end] != quote):
                raise SavedRunReadError('news_supporting_passage_mismatch')
            passages.add((start, end, quote))
    return [quote for _start, _end, quote in sorted(passages)]


def require_current_pilot_capture(db: Session, version: NewsArticleVersion) -> None:
    """A historical grant must not silently resurrect a replaced collection body."""
    from app.services.news_ner_durable.resolution import ResolutionError
    article = db.get(NewsArticle, version.article_id)
    if article is None or compare_source_capture(article, version).state != 'matching_capture':
        raise ResolutionError('pilot_source_capture_requires_review')
