"""Read stored artifact claims; do not recompute or infer publication decisions."""

import json

from sqlalchemy.orm import Session

from app.crud.news_results import list_result_rows, read_result_row
from app.schemas.news_browsing import NewsPublisherOption
from app.models.news import NewsArticle
from app.schemas.news_extraction import ExtractedClaim, FloodCondition
from app.schemas.news_results import NewsResultDetail, NewsResultItem, NewsResultPage, PlacementFilter, ResultOrder
from app.services.news_browsing_service import publisher_labels
from app.services.news_presentation_service import summarize_news_claim
from app.services.news_saved_run_service import SavedRunReadError


def result_item(row: dict, labels: dict[str, str]) -> NewsResultItem:
    claim = json.loads(row["claim"]) if isinstance(row["claim"], str) else row["claim"]
    return NewsResultItem(**{**row, "claim": claim}, key=f"{row['run_id']}:{row['claim_index']}",
                          summary=summarize_news_claim(ExtractedClaim.model_validate(claim)),
                          publisher=labels.get(row["publisher_source_id"], row["publisher_source_id"]))


def browse_news_results(db: Session, *, page: int, page_size: int, search: str, publisher: str | None,
                        condition: FloodCondition | None, placement: PlacementFilter | None,
                        order: ResultOrder, processing_context=None) -> NewsResultPage:
    if processing_context is not None:
        from app.services.news_ner_durable.readers import validate_read_context
        validate_read_context(db,processing_context)
        from app.crud.news_ner_results import list_native_result_rows
        from app.services.news_ner_durable.readers import native_item
        from app.services.news_native_read_context import reader_pipeline_selection
        rows,total,actual_page,publishers=list_native_result_rows(db,pipeline_version=reader_pipeline_selection(processing_context),
            page=page,page_size=page_size,search=search,publisher=publisher,condition=condition,placement=placement,order=order)
        labels=publisher_labels()
        from app.services.news_reviewed_corner_projection import corrected_rows
        from app.services.news_verification_presentation import with_verification
        rows=corrected_rows(db,rows)
        items=[]
        for row in rows:
            item=native_item(row,labels) if row.get('group_id') is not None else result_item(row,labels)
            raw=json.loads(row['claim']) if isinstance(row['claim'],str) else row['claim']
            summary=with_verification(item.summary,raw,estimated_placement=row.get('_reviewed_placement_saved',False))
            items.append(item.model_copy(update={'summary':summary}))
        return NewsResultPage(items=items,total=total,page=actual_page,
            page_size=page_size,pages=max(1,(total+page_size-1)//page_size),
            publishers=[NewsPublisherOption(id=p,label=labels.get(p,p)) for p in publishers])
    rows, total, actual_page, publishers = list_result_rows(db, page=page, page_size=page_size, search=search,
        publisher=publisher, condition=condition, placement=placement, order=order)
    labels = publisher_labels()
    return NewsResultPage(items=[result_item(row, labels) for row in rows], total=total, page=actual_page,
        page_size=page_size, pages=max(1, (total + page_size - 1) // page_size),
        publishers=[NewsPublisherOption(id=value, label=labels.get(value, value)) for value in publishers])


def read_news_result(db: Session, run_id: int, claim_index: int) -> NewsResultDetail | None:
    row = read_result_row(db, run_id, claim_index)
    if row is None:
        return None
    run, version = row
    # Native groups/source checking are a later Phase C gate. An old scalar
    # reader must not turn an unqualified projection into a usable result.
    if run.mode == 'ner_rules_v1':
        from app.services.news_ner_durable.readers import inspect_native, group_row, native_item, read_native_lifecycle
        result=inspect_native(run,version)
        entry=next((g for g in result.read_projection.groups if g.claim_index==claim_index),None)
        if entry is None:
            return None
        item=native_item(group_row(run,version,db.get(NewsArticle,version.article_id),result,entry.group_id),publisher_labels())
        return NewsResultDetail(item=item,claim=result.claims[claim_index],captured_input=version.input_snapshot,
            input_fingerprint=version.input_fingerprint,pipeline_version=run.pipeline_version,
            extraction_errors=result.errors,is_metadata_only=False,lifecycle=read_native_lifecycle(db,run.id,claim_index))
    if run.mode != "rules_only" or any(key in run.result for key in ("schema_version", "processing_method", "native")):
        raise SavedRunReadError("news_native_result_consumer_not_ready")
    claim = run.result["claims"][claim_index]
    source = version.input_snapshot
    item = result_item(dict(run_id=run.id, claim_index=claim_index, article_version_id=version.id,
        article_id=version.article_id, title=source["title"], publisher_source_id=source["publisher"],
        published_at=source.get("published_at"), extracted_at=run.result.get("extracted_at"), captured_at=version.created_at,
        saved_at=db.get(NewsArticle, version.article_id).first_seen_at, claim=claim), publisher_labels())
    return NewsResultDetail(item=item, claim=claim, captured_input=source, input_fingerprint=version.input_fingerprint,
        pipeline_version=run.pipeline_version, extraction_errors=run.result.get("errors", []),
        is_metadata_only=run.result.get("is_metadata_only", False))
