"""Explicit historical capture registration; no extraction or publication.

Registration reuses local_update's existing scheduled-processing exclusion. It
never changes the latest body or review state of a pre-existing article.
"""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlsplit

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.news import NewsArticle, NewsArticleVersion
from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_discovery_service import extraction_input_snapshot
from app.services.news_history_seed_inventory import canonical_source_url
from app.services.news_ner_durable.contracts import sha
from app.services.news_historical_processing import database_identity, disposable_target, require
from app.crud.news_historical_processing import readonly_historical_session


def capture_selection(captures: dict, sources: tuple) -> list[dict]:
    """Deduplicate canonical articles while retaining all original capture hashes."""
    by_url: dict[str, list[tuple[str, dict]]] = {}
    for digest, captured in captures.items():
        import hashlib
        require(hashlib.sha256(captured['text'].encode('utf-8')).hexdigest() == digest,
            'historical_training_capture_hash_mismatch')
        by_url.setdefault(canonical_source_url(captured['url']), []).append((digest,captured))
    result = []
    for url, choices in sorted(by_url.items()):
        matches = [s for s in sources if s.enabled and s.verified_at and s.accepts_article_host(urlsplit(url).hostname)]
        if len(matches) != 1:
            result.append({'url':url,'outcome':'unresolved','reason':'historical_publisher_not_selected_or_ambiguous',
                'source_hashes': sorted(d for d,_ in choices)})
            continue
        # Deterministic newest captured full source; never concatenate versions.
        digest, captured = max(choices,key=lambda pair:(pair[1].get('captured_at') or '', pair[0]))
        raw = captured.get('published_at')
        published = None
        if raw and 'T' in raw:
            value = datetime.fromisoformat(raw.replace('Z','+00:00'))
            published = value if value.tzinfo else None
        snapshot, fingerprint = extraction_input_snapshot(NewsArticleExtractorInput(
            article_id=0,canonical_url=url,publisher=matches[0].id,title=captured['title'] or url,
            article_text=captured['text'],excerpt='',published_at=published))
        snapshot['historical_source_capture'] = {key: captured.get(key) for key in
            ('source_id','text_sha256','capture_version','published_at','publication_basis','captured_at','extraction_method')}
        fingerprint = sha(snapshot)
        result.append({'url':url,'outcome':'capture_selected','snapshot':snapshot,'input_fingerprint':fingerprint,
            'selected_source_hash':digest,'source_hashes':sorted(d for d,_ in choices)})
    return result


def register_captures(engine: object, captures: dict, *, captures_sha256: str, target_sha256: str,
        confirmed_database: str, environment: str, apply: bool = False, sources: tuple | None = None,
        authorization: object | None = None) -> dict:
    from app.services.configuration_service import selected_news_sources
    require(sha(captures) == captures_sha256, 'historical_training_capture_changed')
    require(database_identity(engine) == target_sha256 and engine.url.database == confirmed_database,
        'historical_capture_target_mismatch')
    with readonly_historical_session(engine,confirmed_database) as db:
        selected = capture_selection(captures,selected_news_sources(db,sources))
    receipt = {'schema_version':'historical-capture-registration-v1','status':'ready','captures_sha256':captures_sha256,
        'target_sha256':target_sha256,'database_writes_performed':False,'selection':selected}
    if authorization is not None:
        from app.services.news_history_authority import ArchiveAuthority
        require(type(authorization) is ArchiveAuthority, 'historical_shared_authority_invalid')
        authorization.validate(engine, 'register_captures', captures_sha256)
    if not apply:
        return receipt
    if authorization is None:
        require(disposable_target(engine,environment), 'historical_capture_shared_release_not_qualified')
    with Session(engine) as db, db.begin():
        if authorization is not None:
            authorization.validate(engine, 'register_captures', captures_sha256)
        require(db.scalar(text('SELECT current_database()')) == confirmed_database,'historical_capture_target_mismatch')
        require(capture_selection(captures,selected_news_sources(db,sources)) == selected,'historical_source_selection_changed')
        now = datetime.now(timezone.utc)
        ids = []
        for row in selected:
            if row['outcome'] != 'capture_selected':
                continue
            snapshot = row['snapshot']
            article_id = db.scalar(insert(NewsArticle).values(canonical_url=row['url'],publisher_source_id=snapshot['publisher'],
                title=snapshot['title'],excerpt='',article_text=snapshot['article_text'],published_at=snapshot['published_at'],
                content_fingerprint=row['input_fingerprint'],review_state='local_update',first_seen_at=now,last_seen_at=now
            ).on_conflict_do_nothing(index_elements=['canonical_url']).returning(NewsArticle.id))
            if article_id is None:
                article_id = db.scalar(select(NewsArticle.id).where(NewsArticle.canonical_url == row['url']))
            version_id = db.scalar(insert(NewsArticleVersion).values(article_id=article_id,
                input_fingerprint=row['input_fingerprint'],input_snapshot=snapshot,created_at=now
            ).on_conflict_do_nothing(index_elements=['article_id','input_fingerprint']).returning(NewsArticleVersion.id))
            if version_id is None:
                version_id = db.scalar(select(NewsArticleVersion.id).where(NewsArticleVersion.article_id == article_id,
                    NewsArticleVersion.input_fingerprint == row['input_fingerprint']))
            ids.append(version_id)
        receipt.update(status='completed',database_writes_performed=True,version_ids=ids)
    return receipt
