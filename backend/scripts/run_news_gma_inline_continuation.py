"""Manually count or correct one authenticated older NER parent; never infer."""
from __future__ import annotations

import asyncio
from datetime import datetime
from uuid import uuid4
import os
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.news import NewsExtractionRun,NewsArticleVersion
from app.services.news_ner_durable.contracts import RunEvidence,sha
from app.services.news_ner_durable.assets import with_resolution_assets
from app.services.news_ner_durable.adapter import build_native_result
from app.services.news_ner.location_pipeline import from_neural_mentions
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_three_article_pilot import PilotAuthority
from app.services.news_gma_inline_continuation import VERSION
from app.services.news_gemini_receipts import GCSReceiptStore
from app.services.news_pilot_budget import GCSLedgerStore


def run_inline(args: object, release: dict) -> dict:
    from app.services.news_verified_cloud import preflight,assets_for_release,resolver_for_release
    from app.services.news_sources import load_news_sources
    from app.services.news_ner_durable.resolution_worker import resolve_native_runs
    from app.services.news_pilot_accounting import count_request,accounting_policy
    from app.services.news_gma_inline_budget import InlineBudget
    if not args.authority_object or not args.authority_sha256 or args.run_id!=[382]:
        raise ResolutionError('heading_authority_required')
    p,_=GCSLedgerStore('lanes-storage',args.authority_object).read()
    operation='count' if args.mode=='inline-count' else 'resolve'
    if (sha(p)!=args.authority_sha256 or p.get('schema_version')!=VERSION
            or p.get('release_sha256')!=sha(release) or p.get('resolver')!=release['resolver']
            or p.get('receipts_prefix')!=os.environ.get('LANES_NEWS_RECEIPTS_PREFIX')
            or p.get('allowed_operations')!=[operation]):
        raise ResolutionError('heading_release_changed')
    preflight(release,database_url=settings.DATABASE_URL)
    trusted=assets_for_release(release);resolver=resolver_for_release(release)
    authority=PilotAuthority(p,sha(p),trusted);sources=load_news_sources()
    journal=GCSReceiptStore(p['receipts_prefix']);ledger=GCSLedgerStore('lanes-storage',p['budget_object'])
    before,_=ledger.read()
    if operation=='count' and before['status']!='stopped':raise ResolutionError('heading_ledger_not_stopped')
    key=sha({'mode':args.mode,'authority':sha(p),'invocation':str(uuid4())})
    journal.put(key+'/stage-intent.json',{'schema_version':VERSION,'authority_sha256':sha(p),'ledger_sha256':sha(before)})
    engine=create_engine(settings.DATABASE_URL,hide_parameters=True,connect_args={'connect_timeout':5})
    factory=sessionmaker(bind=engine,expire_on_commit=False)
    try:
        with factory() as db:
            authority.validate_session(db,(382,),sources,operation=operation)
            parent=db.get(NewsExtractionRun,382);version=db.get(NewsArticleVersion,569)
            context=RunEvidence.from_records(parent,version);source=context.source();original=parent.result
            proposal=from_neural_mentions({**source.runtime_request(context.input_fingerprint),
                'mentions':original['native']['neural_mentions']})['proposal']
            if any(proposal[k]!=original['native'][k] for k in ('effective_mentions','proposals','abstentions')):
                raise ResolutionError('heading_parent_recomputation_changed')
            derived=with_resolution_assets(trusted,resolver.identity)
            baseline=build_native_result(context.model_copy(update={'pipeline_version':derived.pipeline_version}),
                {'proposal':proposal,'graph':original['native']['graph'],'measurements':original['measurements'],
                 'provenance':original['provenance']['runtime']},derived,extracted_at=datetime.fromisoformat(original['extracted_at']))
            packets=resolver.request_packets(source,baseline,parent_run_id=382,parent_result_sha256=sha(original))
        if [sha(v['payload']) for v in packets]!=p['request_sha256s']:
            raise ResolutionError('heading_request_changed')
        from types import SimpleNamespace
        from app.services.news_ner_durable.scoped_resolution_v4 import evaluate_rows
        resolver.catalog=derived.catalog
        class AdoptionPreview:
            def put(self,key: str,value: dict) -> None:pass
        outcomes=[]
        for index in (0,1):
            parsed,_=resolver.batch_plan.adopt(index,packets[index]['payload'],packets[index]['context'],
                resolver.config,SimpleNamespace(store=AdoptionPreview()))
            outcomes.extend(evaluate_rows(source,baseline,parsed.results,derived.catalog)[3])
        by_id={o['target_id']:o['outcome'] for o in outcomes}
        if (by_id.get('n6')!='accepted' or by_id.get('n7')!='context_only'
                or any(o['outcome']=='accepted' and o['target_id']!='n6' for o in outcomes)):
            raise ResolutionError('inline_adoption_preflight_failed')
        journal.put(key+'/adoption-preflight.json',{'schema_version':VERSION,'row_outcomes':outcomes,'provider_requests':0})
        if operation=='count':
            async def count() -> list:
                async with httpx.AsyncClient() as client:
                    return [await count_request(resolver.config,v['payload'],http=client,journal=journal) for v in packets[2:]]
            result={'status':'completed','schema_version':'news-pilot-count-catalog-v2',
                'accounting_policy_sha256':sha(accounting_policy()),'requests':asyncio.run(count())}
            if ledger.read()[0]!=before:raise ResolutionError('heading_count_ledger_changed')
        else:
            counts,_=GCSLedgerStore('lanes-storage',p['counts_object']).read()
            if sha(counts)!=p['counts_sha256']:raise ResolutionError('heading_counts_changed')
            resolver.budget=InlineBudget(ledger,p['budget_identity'],policy=p['budget_policy'],counts=counts,journal=journal)
            try:
                result=asyncio.run(resolve_native_runs(factory,(382,),trusted=trusted,resolver=resolver,sources=sources,
                    limit=1,pilot_authorization=authority))
            finally:
                resolver.budget.stop('heading_stage_complete_inspect_before_resuming')
            result['status']='completed' if result['completed'] or result['reused'] else 'failed'
        journal.put(key+'/stage-output.json',result)
        return {'status':result['status'],'private_output_object':p['receipts_prefix']+key+'/stage-output.json',
            'result_sha256':sha(result),'provider_requests':result.get('request_count',0),'active_instances_created':0}
    except Exception as exc:
        journal.put(key+'/stage-failure.json',{'schema_version':VERSION,'error_type':type(exc).__name__,
            'error_code':exc.code if isinstance(exc,ResolutionError) else 'heading_execution_failed'})
        raise
    finally:
        if operation=='resolve':
            state,generation=ledger.read()
            if state.get('inline_policy')==p.get('budget_policy') and state['status']!='stopped':
                state['status']='stopped'
                state['stop_reason']='heading_stage_complete_inspect_before_resuming'
                ledger.compare_and_swap(generation,state)
        engine.dispose()
