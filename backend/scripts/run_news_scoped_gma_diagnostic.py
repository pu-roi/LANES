"""Restricted worker modes for one scoped GMA count and diagnostic."""
from __future__ import annotations

import asyncio
import os

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.services.news_scoped_gma_diagnostic import (PREFIX, ROOT, REQUEST, validate_authority,
    validate_baseline, count_once, qualify_count, gate_once, stop_session)
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_pilot_budget import GCSLedgerStore
from app.services.news_pilot_accounting import AccountedPilotBudget


def run_diagnostic(args: object, release: dict) -> dict:
    try:
        return _run_diagnostic(args,release)
    finally:
        if args.mode=='gma-scoped-gate':
            stop_session(GCSLedgerStore('lanes-storage',ROOT+'budget.json'))


def _run_diagnostic(args: object, release: dict) -> dict:
    from app.core.config import settings
    from app.services.news_verified_cloud import preflight,assets_for_release,resolver_for_release
    from app.services.news_gma_budget_review import prepare_parent
    from app.services.news_sources import load_news_sources
    from app.services.configuration_service import selected_news_sources
    operation={'gma-scoped-count':'count','gma-scoped-gate':'gate'}[args.mode]
    authority,_=GCSLedgerStore('lanes-storage',args.authority_object).read()
    ledger=GCSLedgerStore('lanes-storage',ROOT+'budget.json');state,_=ledger.read()
    trusted=assets_for_release(release);resolver=resolver_for_release(release)
    if resolver.receipts is None:raise ResolutionError('scoped_diagnostic_receipts_required')
    preflight(release,database_url=settings.DATABASE_URL)
    engine=create_engine(settings.DATABASE_URL,hide_parameters=True,connect_args={'connect_timeout':5})
    try:
        with engine.connect().execution_options(isolation_level='REPEATABLE READ') as connection:
            connection.exec_driver_sql('SET TRANSACTION READ ONLY')
            with Session(bind=connection) as db:
                source,baseline=prepare_parent(db,trusted,resolver,selected_news_sources(db,load_news_sources()))
    finally:engine.dispose()
    resolver.catalog=trusted.catalog
    packet=resolver.request_packets(source,baseline,parent_run_id=375,parent_result_sha256=authority['parent_result_sha256'])[3]
    validate_authority(authority,args.authority_sha256,release,packet,operation=operation,
        receipts_prefix=os.environ.get('LANES_NEWS_RECEIPTS_PREFIX'),budget_identity=state['identity'])
    validate_baseline(state,authority,ready=operation=='gate')
    async def run() -> dict:
        async with httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(retries=0),follow_redirects=False) as http:
            if operation=='count':
                catalog=await count_once(resolver.config,packet,resolver.receipts,http=http)
                return {'status':'completed','count_requests':1,'provider_requests':0,'database_writes':0,
                        'catalog_object':PREFIX+sha(catalog)+'/count-catalog.json','catalog_sha256':sha(catalog),
                        'reserved_nanodollars':catalog['requests'][0]['reserved_nanodollars']}
            reference=authority['count_catalog'];catalog,_=GCSLedgerStore('lanes-storage',reference['object']).read()
            qualify_count(catalog,authority,packet,state)
            budget=AccountedPilotBudget(ledger,state['identity'],counts=catalog,counts_sha256=reference['sha256'],
                                       journal=resolver.receipts.store)
            return await gate_once(resolver,packet,source,baseline,budget,http=http)
    return asyncio.run(run())
