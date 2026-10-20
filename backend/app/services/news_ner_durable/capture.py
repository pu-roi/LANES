"""Native handoff of existing saved articles; no RSS admission or source fetch."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.schemas.news_extraction import NewsArticleExtractorInput
from .contracts import NativeInput, NerEvidenceError, capture_native_input


def capture_native_pending_inputs(db: Session, limit: int, source_ids: tuple[str,...] | None,
                                  pipeline: str, article_id: int | None=None) -> int:
    from app.crud.news_processing import enqueue_article
    query=select(NewsArticle).where(NewsArticle.review_state=='pending',NewsArticle.article_error.is_(None),
        func.length(func.trim(NewsArticle.article_text))>0,func.length(NewsArticle.article_text)<=100000,
        NewsArticle.publisher_source_id.in_(source_ids) if source_ids is not None else True,
        NewsArticle.id==article_id if article_id is not None else True).order_by(NewsArticle.id)
    count=0
    # Streaming avoids loading every article body. The caller enforces the
    # capture transaction's CPU/SQL deadline; no unbounded transaction is allowed.
    for article in db.scalars(query.execution_options(yield_per=20)):
        source=NewsArticleExtractorInput(article_id=article.id,canonical_url=article.canonical_url,
            publisher=article.publisher_source_id,title=article.title,excerpt=article.excerpt or '',
            article_text=article.article_text,published_at=article.published_at)
        from .collection import saved_publication
        publication = saved_publication(db, article)
        snapshot,_=capture_native_input(source, publication_evidence=publication)
        current=NativeInput.model_validate(snapshot)
        versions=db.scalars(select(NewsArticleVersion).join(NewsExtractionRun).where(
            NewsArticleVersion.article_id==article.id,NewsExtractionRun.mode=='ner_rules_v1',
            NewsExtractionRun.pipeline_version==pipeline).order_by(NewsArticleVersion.id.desc()))
        captured=False
        for version in versions:
            # Inspection-only historical native fixtures cannot certify capture.
            if version.input_snapshot.get('capture_schema')!='lanes-news-ner-input-v1':continue
            try:saved=NativeInput.model_validate(version.input_snapshot)
            except ValueError as exc:raise NerEvidenceError('ner_input_binding_invalid') from exc
            comparable = saved.model_copy(update={'publication_evidence':current.publication_evidence}) if publication.basis == 'legacy_unknown' else saved
            if comparable==current:
                captured=True;break
        if not captured:
            enqueue_article(db,article,mode='ner_rules_v1',pipeline_version=pipeline,publication_evidence=publication)
            count+=1
            if count>=limit:break
    return count
