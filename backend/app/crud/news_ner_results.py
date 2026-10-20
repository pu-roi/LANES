"""PostgreSQL native group pagination over compact saved read projections."""
from __future__ import annotations

from sqlalchemy import Integer, Text, DateTime, and_, case, cast, column, func, or_, select, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from .news_browsing import latest_article_runs


def native_result_rows(pipeline_version: str):
    run, version = NewsExtractionRun, NewsArticleVersion
    items = func.jsonb_array_elements(run.result['read_projection']['groups']).table_valued(
        column('item', JSONB)).render_derived(name='native_cards')
    item = items.c.item
    index = cast(item['claim_index'].astext, Integer)
    display = item['display']
    span = display['evidence_span']
    quote = func.substr(version.input_snapshot['article_text'].astext,
                        cast(span[0].astext, Integer) + 1,
                        cast(span[1].astext, Integer) - cast(span[0].astext, Integer))
    native_display = display.op('||')(func.jsonb_build_object('evidence_sentence', quote))
    claim = case((index.is_not(None), run.result['claims'].op('->')(index)), else_=native_display)
    source = lambda key: version.input_snapshot[key].astext
    latest = latest_article_runs('ner_rules_v1', pipeline_version)
    query = select(run.id.label('run_id'), version.id.label('article_version_id'), version.article_id,
        index.label('claim_index'), item['group_id'].astext.label('group_id'), claim.label('claim'),
        source('title').label('title'), source('publisher').label('publisher_source_id'),
        source('published_at').label('published_at'), run.result['extracted_at'].astext.label('extracted_at'),
        version.created_at.label('captured_at'), NewsArticle.first_seen_at.label('saved_at')).select_from(run).join(
            version, version.id == run.article_version_id).join(NewsArticle, NewsArticle.id == version.article_id).join(
            latest, and_(latest.c.article_id == version.article_id, latest.c.run_id == run.id)).join(items, true()).where(
                run.status == 'completed', run.mode == 'ner_rules_v1',
                run.result['schema_version'].astext == 'lanes-news-ner-result-v1',
                run.result['processing_method'].astext == 'ner_rules_v1',
                run.result['read_projection']['version'].astext == 'ner-result-read-v1')
    return query, claim


def list_native_result_rows(db: Session, *, pipeline_version: str, page: int, page_size: int,
                           search: str, publisher: str | None, condition: str | None,
                           placement: str | None, order: str) -> tuple[list[dict], int, int, list[str]]:
    query, claim = native_result_rows(pipeline_version)
    all_rows = query.subquery()
    publishers = list(db.scalars(select(all_rows.c.publisher_source_id).distinct().order_by(all_rows.c.publisher_source_id)))
    filtered = query.subquery()
    value = filtered.c.claim
    query = select(filtered)
    if search.strip():
        query = query.where(or_(*(field.icontains(search.strip(), autoescape=True) for field in (
            filtered.c.title, value['raw_place_name'].astext, value['canonical_city'].astext,
            value['canonical_road'].astext, value['evidence_sentence'].astext))))
    if publisher:
        query = query.where(filtered.c.publisher_source_id == publisher)
    if condition:
        query = query.where(value['condition'].astext == condition)
    if placement:
        query = query.where(func.coalesce(value['road_placement']['status'].astext, 'not_recorded') == placement)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    actual = min(page, max(1, (total + page_size - 1) // page_size))
    rows = query.subquery()
    clock = rows.c.published_at if order == 'publication_newest' else rows.c.extracted_at
    result = db.execute(select(rows).order_by(cast(clock, DateTime(timezone=True)).desc().nulls_last(),
        rows.c.run_id.desc(), rows.c.group_id).offset((actual - 1) * page_size).limit(page_size)).mappings()
    return [dict(row) for row in result], total, actual, publishers
