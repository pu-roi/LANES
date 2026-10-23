"""Consolidate exactly three authenticated responses; provider dispatch forbidden."""
from __future__ import annotations
import asyncio
import os
from uuid import uuid4
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.news_gma_inline_continuation import FINAL_VERSION
from app.services.news_gma_inline_budget import inline_commitment
from app.services.news_gemini_receipts import GCSReceiptStore
from app.services.news_pilot_budget import GCSLedgerStore
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_three_article_pilot import PilotAuthority


class NoDispatchBudget:
    def reserve(self,*args: object,**kwargs: object) -> None:
        raise ResolutionError('inline_finalization_provider_dispatch_forbidden')


def run_finalize(args: object,release: dict) -> dict:
    from app.services.news_verified_cloud import preflight,assets_for_release,resolver_for_release
    from app.services.news_ner_durable.resolution_worker import resolve_native_runs
    from app.services.news_sources import load_news_sources
    if not args.authority_object or not args.authority_sha256 or args.run_id!=[382]:
        raise ResolutionError('inline_finalization_authority_required')
    p,_=GCSLedgerStore('lanes-storage',args.authority_object).read()
    if (sha(p)!=args.authority_sha256 or p.get('schema_version')!=FINAL_VERSION
            or p.get('release_sha256')!=sha(release) or p.get('resolver')!=release['resolver']
            or p.get('receipts_prefix')!=os.environ.get('LANES_NEWS_RECEIPTS_PREFIX')
            or p.get('generation_requests_allowed')!=0 or p.get('allowed_operations')!=['resolve']):
        raise ResolutionError('inline_finalization_release_changed')
    ledger=GCSLedgerStore('lanes-storage',p['budget_object']);before,generation=ledger.read()
    if (before['status']!='stopped' or len(before['attempts'])!=42 or sha(before)!=p['stopped_ledger_sha256']
            or inline_commitment(before,before['inline_policy'])!=p['effective_nanodollars']):
        raise ResolutionError('inline_finalization_ledger_changed')
    preflight(release,database_url=settings.DATABASE_URL)
    trusted=assets_for_release(release);resolver=resolver_for_release(release)
    if resolver.batch_plan.manifest.get('generation_requests_allowed')!=0:
        raise ResolutionError('inline_finalization_cached_schedule_required')
    resolver.budget=NoDispatchBudget();journal=GCSReceiptStore(p['receipts_prefix'])
    key=sha({'authority':sha(p),'invocation':str(uuid4())})
    journal.put(key+'/stage-intent.json',{'schema_version':FINAL_VERSION,'ledger_sha256':sha(before),'provider_requests_allowed':0})
    engine=create_engine(settings.DATABASE_URL,hide_parameters=True,connect_args={'connect_timeout':5})
    factory=sessionmaker(bind=engine,expire_on_commit=False);authority=PilotAuthority(p,sha(p),trusted)
    async def execute() -> dict:
        def forbidden(request: httpx.Request) -> httpx.Response:
            raise ResolutionError('inline_finalization_network_dispatch_forbidden')
        async with httpx.AsyncClient(transport=httpx.MockTransport(forbidden)) as client:
            return await resolve_native_runs(factory,(382,),trusted=trusted,resolver=resolver,sources=load_news_sources(),
                limit=1,pilot_authorization=authority,client=client)
    try:
        result=asyncio.run(execute())
        if ledger.read()!=(before,generation):raise ResolutionError('inline_finalization_spending_changed')
        if result['request_count']!=0:raise ResolutionError('inline_finalization_dispatch_detected')
        result.update(status='completed' if result['completed'] or result['reused'] else 'failed',provider_requests=0)
        journal.put(key+'/stage-output.json',result)
        return {'status':result['status'],'private_output_object':p['receipts_prefix']+key+'/stage-output.json',
            'result_sha256':sha(result),'provider_requests':0,'active_instances_created':0}
    finally:
        engine.dispose()
