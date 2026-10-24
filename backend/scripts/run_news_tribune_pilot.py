"""One-source Tribune stages; default worker behavior remains read-only."""
from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime
import os
from uuid import uuid4

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.news import NewsExtractionRun, NewsArticleVersion
from app.services.news_ner_durable.contracts import RunEvidence, sha
from app.services.news_pilot_budget import GCSLedgerStore
from app.services.news_gemini_receipts import GCSReceiptStore
from app.services.news_three_article_pilot import PilotAuthority
from app.services.news_tribune_pilot import VERSION, require, outputs


def run_tribune(args: object, release: dict) -> dict:
    from app.services.news_verified_cloud import assets_for_release, resolver_for_release, preflight
    from app.services.news_sources import load_news_sources
    require(bool(args.authority_object) and bool(args.authority_sha256), 'tribune_authority_required')
    policy, _ = GCSLedgerStore('lanes-storage', args.authority_object).read()
    operation = {'tribune-ner':'ner','tribune-count':'count','tribune-resolve':'resolve','tribune-finalize':'resolve',
        'tribune-preview':'outputs','tribune-apply':'outputs'}[args.mode]
    require(sha(policy) == args.authority_sha256 and policy.get('schema_version') == VERSION
        and policy.get('release_sha256') == sha(release) and policy.get('resolver') == release['resolver']
        and policy.get('receipts_prefix') == os.environ.get('LANES_NEWS_RECEIPTS_PREFIX')
        and policy.get('allowed_operations') == [operation], 'tribune_release_changed')
    preflight(release, database_url=settings.DATABASE_URL)
    trusted = assets_for_release(release)
    authority = PilotAuthority(policy, sha(policy), trusted)
    resolver = resolver_for_release(release)
    engine = create_engine(settings.DATABASE_URL, hide_parameters=True, connect_args={'connect_timeout':5})
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    journal = GCSReceiptStore(policy['receipts_prefix'])
    key = sha(dict(mode=args.mode, authority=sha(policy), invocation=str(uuid4())))
    ledger = GCSLedgerStore('lanes-storage', policy['budget_object'])
    before, _ = ledger.read()
    if args.mode == 'tribune-finalize':
        require(before['status'] == 'stopped' and policy.get('generation_requests_allowed') == 0
            and 'tribune_replay_manifest' in release, 'tribune_zero_provider_finalize_required')
    elif 'tribune_replay_manifest' in release:
        require(operation == 'outputs', 'tribune_replay_operation_invalid')
    require(operation == 'resolve' or before['status'] == 'stopped', 'tribune_ledger_must_be_stopped')
    journal.put(key+'/stage-intent.json', dict(schema_version=VERSION, mode=args.mode,
        authority_sha256=sha(policy), release_sha256=sha(release), ledger_sha256=sha(before)))
    try:
        sources = load_news_sources()
        authority.validate(engine)
        if operation == 'ner':
            from app.crud.news_historical_processing import enqueue_historical_captures
            from app.services.news_ner_durable.processing import process_native_saved_news
            with factory() as db, db.begin():
                authority.validate_session(db, sources=sources)
                ids = enqueue_historical_captures(db, tuple(policy['inputs']), trusted.pipeline_version)
            value = asyncio.run(process_native_saved_news(factory, load_assets=lambda:trusted,
                environment=settings.ENVIRONMENT, database_url=settings.DATABASE_URL,
                limit=1, run_ids=ids, sources=sources, historical_authorization=authority))
            result = dict(status='completed' if value.completed or value.stop_reason == 'no_work' else 'failed',
                run_ids=ids, ner=asdict(value))
        else:
            require(len(args.run_id) == 1, 'tribune_run_required')
            run_id = args.run_id[0]
            with factory() as db:
                authority.validate_session(db, (run_id,), sources, operation=operation)
                run = db.get(NewsExtractionRun, run_id)
                version = db.get(NewsArticleVersion, run.article_version_id)
                context = RunEvidence.from_records(run, version)
                packets = None
                if operation != 'outputs':
                    from app.services.news_ner_durable.adapter import verify_saved_result
                    if 'parent_pipeline_version' in policy:
                        from app.services.news_tribune_replay import SHARED_TIME_VERSION
                        from app.services.news_ner_durable.adapter import parse_saved_result
                        require(args.mode == 'tribune-finalize'
                            and release['tribune_replay_manifest']['schema_version'] == SHARED_TIME_VERSION
                            and run.pipeline_version == policy['parent_pipeline_version'],
                            'tribune_replay_parent_invalid')
                        # The exact parent result/source is bound by the grant.
                        # The resolution worker independently reconstructs the
                        # neural proposal and graph under current normalizers.
                        original = parse_saved_result(run.mode, run.result)
                    else:
                        original = verify_saved_result(context, run.result, trusted)
                    packets = resolver.request_packets(context.source(), original,
                        parent_run_id=run_id, parent_result_sha256=sha(run.result))
                    require([sha(p['payload']) for p in packets] == policy['request_sha256s'], 'tribune_requests_changed')
            if operation == 'count':
                from app.services.news_pilot_accounting import count_request, accounting_policy
                async def count() -> list:
                    async with httpx.AsyncClient() as client:
                        return [await count_request(resolver.config, p['payload'], http=client, journal=journal) for p in packets]
                result = dict(schema_version='news-pilot-count-catalog-v2',
                    accounting_policy_sha256=sha(accounting_policy()), requests=asyncio.run(count()), status='completed')
            elif operation == 'resolve':
                from app.services.news_tribune_budget import TribuneBudget
                from app.services.news_ner_durable.resolution_worker import resolve_native_runs
                if args.mode == 'tribune-finalize':
                    from app.services.news_tribune_replay import ZeroProviderBudget
                    resolver.budget = ZeroProviderBudget()
                else:
                    counts, _ = GCSLedgerStore('lanes-storage', policy['counts_object']).read()
                    require(sha(counts) == policy['counts_sha256'], 'tribune_counts_changed')
                    resolver.budget = TribuneBudget(ledger, policy['budget_identity'],
                        policy=policy['budget_policy'], counts=counts, journal=journal)
                try:
                    result = asyncio.run(resolve_native_runs(factory, (run_id,), trusted=trusted,
                        resolver=resolver, sources=sources, limit=1, pilot_authorization=authority))
                finally:
                    if args.mode != 'tribune-finalize':
                        resolver.budget.stop('tribune_stage_complete_inspect_before_resuming')
                result['status'] = 'completed' if result['completed'] or result['reused'] else 'failed'
            else:
                result = outputs(engine, authority, run_id, sources, apply=args.mode == 'tribune-apply')
        require((operation == 'resolve' and args.mode != 'tribune-finalize') or ledger.read()[0] == before, 'tribune_ledger_changed')
        journal.put(key+'/stage-output.json', result)
        return dict(status=result['status'], private_output_object=policy['receipts_prefix']+key+'/stage-output.json',
            result_sha256=sha(result), run_ids=result.get('run_ids'), provider_requests=result.get('request_count', 0))
    except Exception as exc:
        from app.services.news_ner_durable.resolution import ResolutionError
        journal.put(key+'/stage-failure.json', dict(schema_version=VERSION, error_type=type(exc).__name__,
            error_code=exc.code if isinstance(exc, ResolutionError) else 'tribune_stage_failed'))
        raise
    finally:
        engine.dispose()
