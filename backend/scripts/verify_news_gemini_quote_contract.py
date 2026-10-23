"""Version-two, one-request quote-ID diagnostic; read-only SQL and no NER."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path

import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.schemas.news_ner_result import parse_saved_result
from app.services.news_claim_auditor import AuditorConfig
from app.services.news_gemini_receipts import BatchJournal, GCSReceiptStore, request_batch
from app.services.news_history_resources import checkpoint
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.gemini_resolution import EVIDENCE_CONTRACT, INSTRUCTIONS, response_schema
from app.services.news_ner_durable.resolution import ResolutionError, quote_options, targets
from app.services.news_pilot_budget import GCSLedgerStore, MODEL, PilotBudget
from app.services.news_verified_cloud import preflight, release_file

REQUEST_PIN = '02f4b9b633a06363912fa0f47262377de92e7cb083dcc00011ce76a6cf1ddd8a'
RESERVATION = 42_097_400
PARENT_RELEASE = 'eef8c6c2c4b83c7b09fcbde15dc414cce1b4ccd48ade5a866da9b450e8102c11'
PARENT_PIPELINE = 'ner-v1:41ecf61ec4bd78e73098e68b3cc7911439ad7d5bf6e3205f500c63affffe1aaa'


def validate_packet(release: dict, authority: dict, packet: dict, authority_pin: str) -> dict:
    """V2 admits only the reviewed replacement; never repurposes v1 approval."""
    if (sha(authority) != authority_pin
            or authority.get('schema_version') != 'news-evidence-diagnostic-authority-v2'
            or authority.get('release_sha256') != sha(release)
            or authority.get('application_sha256') != sha(release['application_files'])
            or authority.get('database_identity_sha256') != release['database_identity_sha256']
            or authority.get('allowed_operation') != 'verify-quote-contract-one-batch'
            or authority.get('provider_requests') != 1 or authority.get('database_writes') is not False
            or authority.get('batch_index') != 0
            or authority.get('expected_reservation_nanodollars') != RESERVATION
            or authority.get('request_sha256') != REQUEST_PIN
            or authority.get('parent_pipeline_version') != PARENT_PIPELINE
            or authority.get('original_release_sha256') != PARENT_RELEASE
            or authority.get('receipts_prefix') != os.environ.get('LANES_NEWS_RECEIPTS_PREFIX')
            or authority.get('session_id') != 'quote-contract-20261022-v1'):
        raise ResolutionError('quote_diagnostic_authority_invalid')
    if (sha(packet) != authority['input_sha256']
            or packet.get('schema_version') != 'news-quote-contract-diagnostic-input-v2'
            or packet['article_id'] != 47 or packet['version_id'] != 574
            or packet['context']['parent_run_id'] != 375 or packet['batch_index'] != 0
            or packet['model'] != MODEL or sha(packet['payload']) != REQUEST_PIN
            or packet['expected_reservation_nanodollars'] != RESERVATION
            or packet['original_release_sha256'] != PARENT_RELEASE
            or packet['resolver_identity'] != release['resolver']
            or release['resolver'].get('evidence_contract') != EVIDENCE_CONTRACT):
        raise ResolutionError('quote_diagnostic_input_changed')
    payload = packet['payload']
    document = json.loads(payload['contents'][0]['parts'][0]['text'])
    options = quote_options(document['evidence_text'])
    size = len(json.dumps(payload, ensure_ascii=False, allow_nan=False).encode())
    if (len(document['targets']) != 4
            or [t['id'] for t in document['targets']] != ['n0', 'n1', 'n2', 'n3']
            or packet['context']['targets_sha256'] != sha(document['targets'])
            or document['quote_options'] != [{'option_index': i, 'quote': q['quote']} for i, q in enumerate(options)]
            or payload['systemInstruction'] != {'parts': [{'text': INSTRUCTIONS}]}
            or payload['generationConfig'] != {'temperature': 0, 'maxOutputTokens': 8192,
                'responseMimeType': 'application/json',
                'responseJsonSchema': response_schema(document['targets'], 'compact', len(options))}
            or (2*size+16384)*300+8192*2500 != RESERVATION):
        raise ResolutionError('quote_diagnostic_contract_changed')
    return document


def verified_input(args: object) -> tuple:
    release = release_file(Path(os.environ['LANES_NEWS_VERIFIED_RELEASE']), os.environ['LANES_NEWS_VERIFIED_RELEASE_SHA256'])
    readiness = preflight(release, database_url=settings.DATABASE_URL)
    authority, _ = GCSLedgerStore('lanes-storage', args.authority_object).read()
    # Verify authority integrity before using its input location.
    if sha(authority) != args.authority_sha256:
        raise ResolutionError('quote_diagnostic_authority_invalid')
    packet, _ = GCSLedgerStore('lanes-storage', authority['input_object']).read()
    document = validate_packet(release, authority, packet, args.authority_sha256)
    engine = create_engine(settings.DATABASE_URL, hide_parameters=True, connect_args={'connect_timeout': 5})
    try:
        with engine.connect().execution_options(isolation_level='REPEATABLE READ') as connection:
            connection.execute(text('SET TRANSACTION READ ONLY'))
            connection.execute(text("SET LOCAL statement_timeout='5000'"))
            with Session(bind=connection) as db:
                run = db.get(NewsExtractionRun, 375)
                version = db.get(NewsArticleVersion, 574)
                failed = db.get(NewsExtractionRun, 376)
                if (run is None or version is None or failed is None or run.status != 'completed'
                        or failed.status != 'failed' or failed.result is not None
                        or run.article_version_id != 574 or version.article_id != 47
                        or run.pipeline_version != PARENT_PIPELINE
                        or sha(run.result) != packet['context']['parent_result_sha256']
                        or version.input_fingerprint != packet['context']['input_sha256']
                        or version.input_snapshot['article_text'] != document['evidence_text']
                        or hashlib.sha256(document['evidence_text'].encode()).hexdigest() != packet['source_body_sha256']
                        or targets(parse_saved_result(run.mode, run.result))[:4] != document['targets']):
                    raise ResolutionError('quote_diagnostic_parent_changed')
    finally:
        engine.dispose()
    return release, authority, packet, readiness


async def execute(args: object) -> dict:
    _, authority, packet, readiness = verified_input(args)
    if not args.allow_one_request:
        return {'status': 'preflight_passed', 'provider_requests': 0, 'database_writes': 0,
            'neural_inferences': 0, 'request_sha256': REQUEST_PIN, 'counts': readiness['counts']}
    if (authority['budget_object'] != os.environ.get('LANES_NEWS_PILOT_BUDGET_OBJECT')
            or authority['budget_identity'] != os.environ.get('LANES_NEWS_PILOT_BUDGET_IDENTITY')):
        raise ResolutionError('quote_diagnostic_budget_changed')
    budget = PilotBudget(GCSLedgerStore('lanes-storage', authority['budget_object']), authority['budget_identity'])
    config = AuditorConfig.from_environment()
    if config.provider != 'gemini' or config.model != MODEL or config.error_code():
        raise ResolutionError('quote_diagnostic_provider_changed')
    journal = BatchJournal(GCSReceiptStore(authority['receipts_prefix']), secrets=(config.gemini_api_key,))
    context = {**packet['context'], 'diagnostic_session_id': authority['session_id']}
    key = sha({'request_sha256': REQUEST_PIN, 'context': context})
    result = {'status': 'failed', 'provider_requests': 0, 'database_writes': 0, 'neural_inferences': 0,
        'request_identity': key, 'request_sha256': REQUEST_PIN, 'article_acceptance': 'not_evaluated', 'seeding': 'not_attempted'}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30, connect=5), follow_redirects=False,
                transport=httpx.AsyncHTTPTransport(retries=0)) as client:
            parsed, usage = await request_batch(config, packet['payload'], context, http=client, budget=budget, journal=journal)
        result.update(status='one_batch_evidence_references_passed', provider_requests=1, targets=len(parsed.results), usage=usage)
    except ResolutionError as exc:
        result.update(error_code=exc.code, diagnostic=getattr(exc, 'provider_diagnostic', {}), provider_requests=exc.request_count)
    except (httpx.HTTPError, TimeoutError) as exc:
        result.update(error_code='quote_diagnostic_transport_failed', error_type=type(exc).__name__,
            provider_requests=getattr(exc, 'request_count', 0), transport_status='outcome_unknown')
    finally:
        budget.stop('single_quote_contract_diagnostic_completed_requires_review')
    result['receipt_prefix'] = authority['receipts_prefix']+key+'/'
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authority-object', required=True)
    parser.add_argument('--authority-sha256', required=True)
    parser.add_argument('--allow-one-request', action='store_true')
    args = parser.parse_args()
    try:
        resources = [checkpoint()]
        result = asyncio.run(execute(args))
        result['resource_snapshots'] = [*resources, checkpoint()]
    except Exception as exc:
        result = {'status': 'failed', 'error_code': getattr(exc, 'code', 'quote_diagnostic_failed'), 'error_type': type(exc).__name__}
    print(json.dumps({'schema': 'news-quote-contract-diagnostic-v2', **result}, sort_keys=True), flush=True)
    return 0 if result['status'] in ('preflight_passed', 'one_batch_evidence_references_passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
