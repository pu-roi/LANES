"""Manual cloud worker: default read-only checks, paid resolve explicitly gated."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('preflight','contract-check','provider-check','resolve',
        'pilot-ner','pilot-resolve','pilot-preview','pilot-apply',
        'gma-preflight','gma-resolve','gma-preview','gma-archive',
        'gma-count','gma-gate','gma-budget-resolve','gma-budget-preview','gma-budget-archive',
        'gma-scoped-count','gma-scoped-gate',
        'gma-scoped-prepare','gma-scoped-resolve','gma-scoped-preview','gma-scoped-archive',
        'gma-shared-preview','gma-shared-archive',
        'source-ner','source-count','source-resolve','source-preview','source-archive',
        'heading-count','heading-resolve','inline-count','inline-resolve','inline-finalize',
        'gma-active-preview','gma-active-apply',
        'tribune-ner','tribune-count','tribune-resolve','tribune-finalize','tribune-preview','tribune-apply'),nargs='?',default='preflight')
    parser.add_argument('--allow-one-provider-request',action='store_true')
    parser.add_argument('--run-id',type=int,action='append',default=[])
    parser.add_argument('--authority',type=Path)
    parser.add_argument('--authority-sha256')
    parser.add_argument('--authority-object')
    parser.add_argument('--article-id', type=int)
    args=parser.parse_args();result={'status':'failed','error_code':'verified_worker_failed'};error_type=()
    try:
        from app.services.news_verified_cloud import (release_file,preflight,assets_for_release,
            resolver_for_release,require_provider_execution)
        from app.services.news_ner_durable.resolution import ResolutionError
        error_type=ResolutionError
        from app.services.news_history_resources import checkpoint
        from app.core.config import settings
        resources=[checkpoint()]
        release=release_file(Path(os.environ['LANES_NEWS_VERIFIED_RELEASE']),
                             os.environ['LANES_NEWS_VERIFIED_RELEASE_SHA256'])
        if args.mode.startswith('tribune-'):
            from scripts.run_news_tribune_pilot import run_tribune
            result=run_tribune(args,release)
        elif args.mode in ('gma-active-preview','gma-active-apply'):
            from scripts.run_news_gma_active import run_active
            result=run_active(args,release)
        elif args.mode=='inline-finalize':
            from scripts.run_news_gma_inline_finalize import run_finalize
            result=run_finalize(args,release)
        elif args.mode.startswith('inline-'):
            from scripts.run_news_gma_inline_continuation import run_inline
            result=run_inline(args,release)
        elif args.mode.startswith('heading-'):
            from scripts.run_news_gma_heading_repair import run_heading_repair
            result=run_heading_repair(args,release)
        elif args.mode.startswith('source-'):
            from scripts.run_news_source_repair import run_source_repair
            result=run_source_repair(args,release)
        elif args.mode in ('gma-shared-preview','gma-shared-archive'):
            from scripts.run_news_gma_shared_history import run_shared_history
            result=run_shared_history(args,release)
        elif args.mode in ('gma-scoped-prepare','gma-scoped-resolve','gma-scoped-preview','gma-scoped-archive'):
            from scripts.run_news_gma_scoped_continuation import run_continuation
            result=run_continuation(args,release)
        elif args.mode in ('gma-scoped-count','gma-scoped-gate'):
            from scripts.run_news_scoped_gma_diagnostic import run_diagnostic
            result=run_diagnostic(args,release)
        elif args.mode in ('gma-count','gma-gate','gma-budget-resolve','gma-budget-preview','gma-budget-archive'):
            from scripts.run_news_gma_budget_review import run_budget_review
            result = run_budget_review(args, release)
        elif args.mode.startswith('gma-'):
            from scripts.run_news_gma_review import run_gma_review
            result = run_gma_review(args, release)
        elif args.mode.startswith('pilot-'):
            from scripts.run_news_three_article_pilot import run_pilot
            result = run_pilot(args, release)
        elif args.mode=='resolve':
            require_provider_execution(release,authority=args.authority,authority_sha256=args.authority_sha256)
            if not 1<=len(args.run_id)<=2:
                raise ResolutionError('native_resolution_batch_invalid')
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from app.services.news_ner_durable.resolution_worker import resolve_native_runs
            from app.services.news_sources import load_news_sources
            engine=create_engine(settings.DATABASE_URL,hide_parameters=True,connect_args={'connect_timeout':5})
            try:
                from app.services.news_historical_processing import database_identity
                if database_identity(engine)!=release['database_identity_sha256'] or engine.url.database!=release['confirmed_database']:
                    raise ResolutionError('verified_storage_mismatch')
                result=asyncio.run(resolve_native_runs(sessionmaker(bind=engine),tuple(args.run_id),
                    trusted=assets_for_release(release),resolver=resolver_for_release(release),
                    sources=load_news_sources(),authority=json.loads(args.authority.read_text()),
                    authority_sha256=args.authority_sha256))
                result['status']='requires_attention' if result['failed'] or result['retry_wait'] or result['busy'] else 'completed'
            finally:engine.dispose()
        else:
            if args.mode=='provider-check' and not args.allow_one_provider_request:
                raise ResolutionError('verified_provider_check_authorization_required')
            result=preflight(release,database_url=settings.DATABASE_URL)
            if args.mode=='contract-check':
                from scripts.news_verified_contract import check_contract
                from unittest.mock import patch
                with patch('socket.socket.connect',side_effect=RuntimeError('contract_external_socket_forbidden')):
                    result['contract']=asyncio.run(check_contract(assets_for_release(release),resolver_for_release(release)))
            elif args.mode=='provider-check':
                from scripts.news_verified_provider_check import check_provider
                from app.services.news_pilot_budget import PilotBudget, GCSLedgerStore
                budget = PilotBudget(GCSLedgerStore('lanes-storage',
                    os.environ['LANES_NEWS_PILOT_BUDGET_OBJECT']), os.environ['LANES_NEWS_PILOT_BUDGET_IDENTITY'])
                resolver = resolver_for_release(release)
                resolver.budget = budget
                result['provider_check']=asyncio.run(check_provider(assets_for_release(release),resolver))
                result['external_provider_requests']=result['provider_check']['external_provider_requests']
                result['status']='completed' if result['provider_check']['status']=='passed' else 'requires_attention'
        resources.append(checkpoint());result['resource_snapshots']=resources
    except (KeyboardInterrupt,asyncio.CancelledError):
        result={'status':'interrupted','error_code':'verified_worker_cancelled'}
    except Exception as exc:
        # No provider bodies, credentials, URLs or source articles in Cloud Logs.
        # Frame identifiers locate unexpected failures without exception text,
        # source lines or local variables (which may contain private data).
        import traceback
        result={'status':'failed','error_code':exc.code if isinstance(exc,error_type) else 'verified_worker_failed',
                'error_type':type(exc).__name__,
                'error_frames':[{'file':Path(frame.filename).name,'function':frame.name,'line':frame.lineno}
                    for frame in traceback.extract_tb(exc.__traceback__)[-5:]]}
    print(json.dumps({'schema':'news-verified-cloud-receipt-v1','mode':args.mode,**result},sort_keys=True),flush=True)
    return 130 if result['status']=='interrupted' else 0 if result['status'] in ('preflight_passed','completed') else 1


if __name__=='__main__':raise SystemExit(main())
