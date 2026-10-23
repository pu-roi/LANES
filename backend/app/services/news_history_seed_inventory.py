"""Inventory training source membership and saved captures without inference.

Training metadata identifies source articles only. Labels and annotated passages
are never interpreted as flood observations or used to fill source content.
"""
from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit
import hashlib

from sqlalchemy import select, func
from sqlalchemy.engine import Engine

from app.models.news import NewsArticleVersion
from app.crud.news_historical_processing import readonly_historical_session


def canonical_source_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {'https', 'http'} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('historical_source_url_invalid')
    return urlunsplit(('https', parsed.netloc.lower(), parsed.path.rstrip('/'), parsed.query, ''))


def training_sources(provenance: list[dict], source_register: list[dict]) -> list[dict]:
    selected = {row['source_sha256'] for row in provenance
        if row.get('split', row.get('partition')) == 'train'}
    by_hash: dict[str, list[dict]] = {}
    for row in source_register:
        by_hash.setdefault(row['source_sha256'], []).append(row)
    result = []
    for digest in sorted(selected):
        sources = by_hash.get(digest, [])
        if not sources:
            result.append({'source_sha256': digest, 'outcome': 'training_source_capture_unresolved'})
        else:
            for source in sources:
                result.append({'source_sha256': digest, 'source_id': source['source_id'],
                    'canonical_url': canonical_source_url(source['url']), 'publisher': source['publisher'],
                    'publication_date': source.get('publication_date'), 'capture_version': source.get('capture_version'),
                    'outcome': 'training_source_identified'})
    return result


def complete_training_captures(rows: list[dict], training: list[dict]) -> dict[str, dict]:
    """Read only embedded complete source captures for known training members."""
    selected = {row['source_sha256'] for row in training}
    captures = {}
    for row in rows:
        source = row.get('source') or {}
        digest = source.get('text_sha256')
        if digest not in selected:
            continue
        body = source.get('text')
        if not isinstance(body,str) or not body.strip() or hashlib.sha256(body.encode('utf-8')).hexdigest() != digest:
            raise ValueError('historical_training_capture_hash_mismatch')
        # Source object only: no annotation labels, relations, passage text or facts.
        captures[digest] = {key: source.get(key) for key in
            ('source_id','url','title','publisher','published_at','publication_basis','captured_at','text','text_sha256','capture_version','extraction_method')}
    return captures


def seed_inventory(engine: Engine, confirmed_database: str, training: list[dict]) -> dict:
    version = NewsArticleVersion
    # Latest full-body capture per article; a changed input stays a distinct version.
    with readonly_historical_session(engine, confirmed_database) as db:
        rows = db.execute(select(version.id, version.article_id, version.input_fingerprint,
            *[version.input_snapshot[key].as_string().label(key) for key in ('canonical_url','publisher','title')],
            func.length(version.input_snapshot['article_text'].as_string()).label('characters'))
            .distinct(version.article_id).where(func.length(version.input_snapshot['article_text'].as_string()) > 0)
            .order_by(version.article_id, version.id.desc())).mappings().all()
        saved = [dict(row) for row in rows]
    urls = {canonical_source_url(row['canonical_url']): row for row in saved}
    joined = []
    for source in training:
        saved_source = urls.get(source.get('canonical_url'))
        joined.append({**source, 'saved_article_id': saved_source['article_id'] if saved_source else None,
            'saved_version_id': saved_source['id'] if saved_source else None,
            'outcome': 'saved_capture_selected' if saved_source else source['outcome'] if 'canonical_url' not in source else
                'full_training_capture_registration_required'})
    return {'schema_version': 'news-history-seed-inventory-v1', 'read_only': True,
        'saved_articles': saved, 'training_sources': joined,
        'selection': {'dataset_id': 'news-history-seed-v1', 'version_ids': sorted(row['id'] for row in saved)},
        'scope': 'NCR observations only; extraction/source/geometry qualification pending',
        'missing_capture_policy': 'Do not substitute annotated passages for complete article bodies'}
