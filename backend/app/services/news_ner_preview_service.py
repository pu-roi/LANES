"""Transient saved-body extraction. No database, queue, fetch or placement writes."""
from datetime import datetime
import hashlib
from pathlib import Path
from typing import Awaitable, Callable

from app.core.config import Settings, settings
from app.schemas.news_ner_preview import NerPreview
from app.services.news_ner.contract import IMAGE, MAX_CHARS, object_sha, validate_raw_input
from app.services.news_ner.context_association_v42 import validate_output
from app.services.news_ner.location_pipeline import from_neural_mentions, LOCATION_RULES, LOCATION_METHOD
from app.services.news_ner.projection import LIMITATIONS, project
from app.services.news_ner.runtime import PreviewError, run_local


def ensure_enabled(config: Settings) -> None:
    if not config.NEWS_NER_PREVIEW_ENABLED:
        raise PreviewError(503, 'preview_disabled')
    if config.ENVIRONMENT.lower() not in {'development', 'local', 'test'}:
        raise PreviewError(503, 'preview_environment_unavailable')


async def preview_article(article: object, config: Settings = settings,
                          runner: Callable[..., Awaitable[dict]] = run_local) -> NerPreview:
    ensure_enabled(config)
    text = article.article_text
    if article.article_error or not isinstance(text, str) or not text.strip():
        raise PreviewError(409, 'article_body_unavailable')
    if len(text) > MAX_CHARS:
        raise PreviewError(413, 'article_too_large')
    # Copy all fields before the first await. This hash identifies the input
    # read for this request even if a later capture changes the saved row.
    published: datetime | None = article.published_at
    published_raw = published.isoformat() if published is not None else None
    timezone_known = published is not None and published.utcoffset() is not None
    snapshot = {'article_id': article.id, 'canonical_url': article.canonical_url,
        'publisher_source_id': article.publisher_source_id, 'article_text': text,
        'published_at': published_raw}
    input_sha = object_sha(snapshot)
    text_sha = hashlib.sha256(text.encode('utf-8')).hexdigest()
    raw = {'record_id': 'preview-' + input_sha, 'text': text, 'text_sha256': text_sha,
        'publication': {'value': published_raw, 'basis': 'saved_article_metadata'} if timezone_known else None}
    try:
        result = await runner(raw, Path(config.NEWS_NER_PREVIEW_BUNDLE).resolve(),
            config.NEWS_NER_PREVIEW_BUNDLE_SHA256, config.NEWS_NER_PREVIEW_DOCKER)
        if set(result) != {'proposal', 'graph', 'provenance', 'measurements'}:
            raise ValueError('unexpected worker response')
        proposal = result['proposal']
        validate_raw_input({**raw, 'mentions': proposal['neural_mentions']})
        expected = from_neural_mentions({**raw, 'mentions': proposal['neural_mentions']})
        if proposal != expected['proposal'] or result['graph'] != expected['graph']:
            raise ValueError('proposal binding mismatch')
        effective = {**raw, 'mentions': proposal['effective_mentions']}
        validate_output(effective, result['graph'])
        provenance = result['provenance']
        if (provenance['bundle_sha256'] != config.NEWS_NER_PREVIEW_BUNDLE_SHA256
                or provenance['image'] != IMAGE or provenance['model'] != 'v19-control-seed-0'
                or provenance['location_rules'] != LOCATION_RULES
                or provenance['location_method'] != LOCATION_METHOD
                or provenance['context_rules'] != 'lanes-context-association-v42'):
            raise ValueError('pipeline binding mismatch')
        limitations = list(LIMITATIONS)
        if published is not None and not timezone_known:
            limitations.append('publication_timezone_unknown')
        return NerPreview(source={'article_id': snapshot['article_id'], 'canonical_url': snapshot['canonical_url'], 'text_sha256': text_sha,
            'input_sha256': input_sha, 'published_at': published_raw, 'publication_timezone_known': timezone_known},
            provenance=provenance, measurements=result['measurements'], neural_mentions=proposal['neural_mentions'], effective_mentions=proposal['effective_mentions'],
            proposals=proposal['proposals'], abstentions=proposal['abstentions'],
            graph=result['graph'], groups=project(effective, result['graph']),
            unassigned=result['graph']['unassigned'], limitations=limitations)
    except PreviewError:
        raise
    except OSError as exc:
        raise PreviewError(503, 'preview_runtime_unavailable') from exc
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise PreviewError(502, 'preview_worker_failed') from exc
