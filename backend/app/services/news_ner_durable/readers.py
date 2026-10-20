"""Saved native inspection/presentation; never inference or source revalidation."""
from __future__ import annotations

from app.schemas.news_ner_result import NewsNerResult, parse_saved_result
from app.schemas.news_results import NewsNativeResultItem, NewsNativeGroupDetail, NewsResultLifecycle
from app.schemas.news_presentation import NewsFloodSummary
from app.services.news_presentation_service import summarize_news_claim
from app.services.news_saved_run_service import SavedRunReadError
from .collection import NativeCollectionContext
from .contracts import RunEvidence


def get_news_read_context() -> NativeCollectionContext | None:
    """Release default stays legacy. Controlled tests explicitly override this dependency."""
    return None


def validate_read_context(db, context: NativeCollectionContext) -> None:
    try:
        context.validate(db)
    except ValueError as exc:
        raise SavedRunReadError('news_native_reader_unavailable') from exc


def native_item(row: dict, labels: dict[str, str]) -> NewsNativeResultItem:
    try:
        return _native_item(row,labels)
    except (ValueError,TypeError,KeyError,IndexError) as exc:
        raise SavedRunReadError('news_saved_result_unsupported_or_invalid') from exc


def _native_item(row: dict, labels: dict[str, str]) -> NewsNativeResultItem:
    claim = row['claim']
    if row['claim_index'] is not None:
        from app.schemas.news_ner_result import NerProjectedClaim
        summary = summarize_news_claim(NerProjectedClaim.model_validate(claim))
    else:
        summary = NewsFloodSummary(location=claim['raw_place_name'], area=claim['canonical_city'],
            location_qualifier='Measurements retain their reported scope; see the source evidence.',
            water_level=claim.get('depth_raw') or 'Not stated in article',
            passability={'passable_all':'Passable to all vehicles','passable_with_caution':'Passable with caution; vehicle types not specified',
                'passable_unspecified':'Passable; vehicle types not specified','light_vehicle_closed':'Not passable to light vehicles',
                'impassable_all':'Not passable to any vehicles'}.get(claim.get('road_passability'),'Not stated in article'),
            condition={'active':'Flooding reported','rising':'Water rising','receding':'Water receding','subsided':'Floodwater subsided'}.get(claim['condition'],'Condition not stated'),
            flood_time=claim.get('event_time_resolved'),
            flood_time_label={'observation':'Flood observed in article','report':'Flood reported in article'}.get(claim['event_time_kind'],'Flood time in article'),
            map_status='Map location not checked',reading_status='reported_location',reading_reason=None)
    return NewsNativeResultItem(**row, key=f"{row['run_id']}:group:{row['group_id']}",
        publisher=labels.get(row['publisher_source_id'],row['publisher_source_id']),summary=summary)


def inspect_native(run: object, version: object) -> NewsNerResult:
    if isinstance(run.result,dict) and run.result.get('read_projection') is None:
        raise SavedRunReadError('news_native_result_consumer_not_ready')
    try:
        context = RunEvidence.from_records(run, version)
        source = context.source()
        result = parse_saved_result(run.mode, run.result)
        if (not isinstance(result, NewsNerResult) or result.read_projection is None
                or result.source.article_version_id != version.id or result.article_id != version.article_id
                or result.source.input_fingerprint != version.input_fingerprint
                or result.source.canonical_url != source.canonical_url
                or result.canonical_url != source.canonical_url
                or result.processed_text_length != len(source.article_text)
                or result.source.published_at != context.input_snapshot['published_at']
                or result.source.publication_timezone_known != source.publication_evidence.timezone_known
                or result.source.text_sha256 != source.runtime_request(context.input_fingerprint)['text_sha256']):
            raise ValueError('unsupported_native_reader')
        return result
    except (ValueError,TypeError,KeyError,AttributeError) as exc:
        raise SavedRunReadError('news_saved_result_unsupported_or_invalid') from exc


def group_row(run: object, version: object, article: object, result: NewsNerResult, group_id: str) -> dict | None:
    entry=next((g for g in result.read_projection.groups if g.group_id==group_id),None)
    if entry is None:
        return None
    if entry.claim_index is not None:
        if not 0 <= entry.claim_index < len(result.claims):
            raise SavedRunReadError('news_saved_result_unsupported_or_invalid')
        claim=result.claims[entry.claim_index].model_dump(mode='json')
    else:
        if entry.display is None:
            raise SavedRunReadError('news_saved_result_unsupported_or_invalid')
        claim=entry.display.model_dump(mode='json')
        start,end=entry.display.evidence_span
        text=version.input_snapshot['article_text']
        if not 0<=start<end<=len(text):
            raise SavedRunReadError('news_saved_result_unsupported_or_invalid')
        claim['evidence_sentence']=text[start:end]
    source=version.input_snapshot
    return dict(run_id=run.id,article_version_id=version.id,article_id=version.article_id,
        claim_index=entry.claim_index,group_id=group_id,claim=claim,title=source['title'],
        publisher_source_id=source['publisher'],published_at=source.get('published_at'),
        extracted_at=result.extracted_at,captured_at=version.created_at,saved_at=article.first_seen_at)


def read_native_group(db, run_id: int, group_id: str, labels: dict[str,str]) -> NewsNativeGroupDetail | None:
    from app.models.news import NewsArticle,NewsArticleVersion,NewsExtractionRun
    run=db.get(NewsExtractionRun,run_id)
    if run is None or run.status!='completed' or run.mode!='ner_rules_v1':
        return None
    version=db.get(NewsArticleVersion,run.article_version_id)
    result=inspect_native(run,version)
    row=group_row(run,version,db.get(NewsArticle,version.article_id),result,group_id)
    group=next((g for g in result.projection['groups'] if g['group_id']==group_id),None)
    if row is None or group is None:
        return None
    return NewsNativeGroupDetail(item=native_item(row,labels),group=group,result=result,
        captured_input=version.input_snapshot,input_fingerprint=version.input_fingerprint,pipeline_version=run.pipeline_version,
        lifecycle=read_native_lifecycle(db,run.id,row['claim_index']))


def read_native_lifecycle(db, run_id: int, claim_index: int | None) -> NewsResultLifecycle:
    from sqlalchemy import select
    from app.models.news_publication import NewsClaimSource,NewsClaimEvaluation,NewsClaimDecision
    if claim_index is None:
        return NewsResultLifecycle(state='not_projected')
    source=db.scalar(select(NewsClaimSource).where(NewsClaimSource.extraction_run_id==run_id,
                                                 NewsClaimSource.claim_ordinal==claim_index))
    if source is None:return NewsResultLifecycle(state='not_evaluated')
    evaluation=db.scalar(select(NewsClaimEvaluation).where(NewsClaimEvaluation.claim_source_id==source.id).order_by(NewsClaimEvaluation.id.desc()).limit(1))
    decision=db.scalar(select(NewsClaimDecision).where(NewsClaimDecision.case_id==source.case_id).order_by(NewsClaimDecision.revision.desc()).limit(1))
    if decision is not None:
        return NewsResultLifecycle(state=decision.public_state,case_id=source.case_id,evaluation_id=decision.evaluation_id,
            decision_id=decision.id,review_state=decision.review_state,reason_code=decision.reason_code)
    if evaluation is None:return NewsResultLifecycle(state='not_evaluated',case_id=source.case_id)
    state='evaluation_failed' if evaluation.status=='failed' else 'evaluated' if evaluation.status=='completed' else 'evaluation_pending'
    return NewsResultLifecycle(state=state,case_id=source.case_id,evaluation_id=evaluation.id,
        reason_code=evaluation.error_code or (evaluation.result or {}).get('reason_code'))
