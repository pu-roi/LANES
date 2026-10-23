"""Manually scoped clean-source repair; one article, stopped ledger, no activation."""
from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
import os
from uuid import uuid4

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.news import NewsExtractionRun, NewsArticleVersion
from app.services.news_ner_durable.contracts import RunEvidence, sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_three_article_pilot import PilotAuthority
from app.services.news_pilot_budget import GCSLedgerStore
from app.services.news_gemini_receipts import GCSReceiptStore
from app.services.news_source_repair import VERSION, SESSION, repair_outputs


def run_source_repair(args: object, release: dict) -> dict:
    from app.services.news_verified_cloud import preflight, assets_for_release, resolver_for_release
    from app.services.news_sources import load_news_sources
    if not args.authority_object or not args.authority_sha256:
        raise ResolutionError('source_repair_authority_required')
    p, _ = GCSLedgerStore('lanes-storage', args.authority_object).read()
    operation = {'source-ner':'ner', 'source-count':'count', 'source-resolve':'resolve',
        'source-preview':'archive', 'source-archive':'archive'}[args.mode]
    if (sha(p) != args.authority_sha256 or p.get('schema_version') != VERSION
            or p.get('release_sha256') != sha(release) or p.get('resolver') != release['resolver']
            or p.get('receipts_prefix') != os.environ.get('LANES_NEWS_RECEIPTS_PREFIX')
            or p.get('allowed_operations') != [operation]):
        raise ResolutionError('source_repair_release_changed')
    preflight(release, database_url=settings.DATABASE_URL)
    trusted = assets_for_release(release)
    authority = PilotAuthority(p, sha(p), trusted)
    resolver = resolver_for_release(release)
    engine = create_engine(settings.DATABASE_URL, hide_parameters=True, connect_args={'connect_timeout':5})
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    journal = GCSReceiptStore(p['receipts_prefix'])
    key = sha({'mode':args.mode,'authority':sha(p),'invocation':str(uuid4())})
    ledger = GCSLedgerStore('lanes-storage', p['budget_object'])
    before, _ = ledger.read()
    if operation != 'resolve' and before['status'] != 'stopped':
        raise ResolutionError('source_repair_ledger_must_be_stopped')
    journal.put(key+'/stage-intent.json', {'schema_version':VERSION,'mode':args.mode,
        'authority_sha256':sha(p),'release_sha256':sha(release),'ledger_sha256':sha(before)})
    result = None
    try:
        sources = load_news_sources()
        authority.validate(engine)
        if operation == 'ner':
            from app.crud.news_historical_processing import enqueue_historical_captures
            from app.services.news_ner_durable.processing import process_native_saved_news
            with factory() as db, db.begin():
                authority.validate_session(db, sources=sources)
                ids = enqueue_historical_captures(db, tuple(i for i in p['inputs'] if i['article_id']==47), trusted.pipeline_version)
            value = asyncio.run(process_native_saved_news(factory, load_assets=lambda:trusted,
                environment=settings.ENVIRONMENT, database_url=settings.DATABASE_URL, limit=1,
                run_ids=ids, sources=sources, historical_authorization=authority))
            result = {'status':'completed' if value.completed or value.stop_reason=='no_work' else 'failed',
                'run_ids':ids,'ner':asdict(value)}
        else:
            if len(args.run_id) != 1:
                raise ResolutionError('source_repair_run_required')
            run_id = args.run_id[0]
            with factory() as db:
                authority.validate_session(db, (run_id,), sources, operation=operation)
                run = db.get(NewsExtractionRun, run_id);version = db.get(NewsArticleVersion, run.article_version_id)
                context = RunEvidence.from_records(run, version)
                from app.services.news_ner_durable.adapter import verify_saved_result
                original = verify_saved_result(context, run.result, trusted) if operation != 'archive' else None
                packets = resolver.request_packets(context.source(), original, parent_run_id=run_id,
                    parent_result_sha256=sha(run.result)) if original is not None else None
            if operation == 'count':
                from app.services.news_pilot_accounting import count_request, accounting_policy
                if [sha(v['payload']) for v in packets] != p['request_sha256s']:
                    raise ResolutionError('source_repair_request_changed')
                async def count():
                    async with httpx.AsyncClient() as client:
                        return [await count_request(resolver.config, v['payload'], http=client, journal=journal) for v in packets]
                counts = asyncio.run(count())
                result = {'schema_version':'news-pilot-count-catalog-v2','accounting_policy_sha256':sha(accounting_policy()),
                    'requests':counts,'status':'completed'}
            elif operation == 'resolve':
                from app.services.news_source_repair_budget import SourceRepairBudget
                from app.services.news_ner_durable.resolution_worker import resolve_native_runs
                counts, _ = GCSLedgerStore('lanes-storage', p['counts_object']).read()
                if sha(counts) != p['counts_sha256'] or [sha(v['payload']) for v in packets] != p['request_sha256s']:
                    raise ResolutionError('source_repair_counts_changed')
                resolver.budget = SourceRepairBudget(ledger, p['budget_identity'], policy=p['budget_policy'], counts=counts, journal=journal)
                try:
                    result = asyncio.run(resolve_native_runs(factory, (run_id,), trusted=trusted, resolver=resolver,
                        sources=sources, limit=1, pilot_authorization=authority))
                finally:
                    resolver.budget.stop('source_repair_stage_complete_inspect_before_resuming')
                result['status'] = 'completed' if result['completed'] or result['reused'] else 'failed'
            else:
                result = repair_outputs(engine, authority, run_id, sources, apply=args.mode=='source-archive')
        if operation != 'resolve' and ledger.read()[0] != before:
            raise ResolutionError('source_repair_ledger_changed')
        journal.put(key+'/stage-output.json', result)
        return {'status':result['status'],'private_output_object':p['receipts_prefix']+key+'/stage-output.json',
            'result_sha256':sha(result),'run_ids':result.get('run_ids'),
            'provider_requests':result.get('request_count',0),'active_instances_created':0}
    except Exception as error:
        journal.put(key+'/stage-failure.json', {'schema_version':VERSION,'error_type':type(error).__name__,
            'error_code':error.code if isinstance(error,ResolutionError) else 'source_repair_failed',
            'inspect_before_resuming':True})
        raise
    finally:
        engine.dispose()
