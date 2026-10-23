"""Restricted GMA count, corrected projection, preview and archive worker stages."""
from __future__ import annotations

import asyncio
import os

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.news_gma_scoped_budget import SESSION, ScopedGmaBudget
from app.services.news_gma_scoped_continuation import batch_manifest, qualify_schedule, VERSION, REQUESTS
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_pilot_budget import GCSLedgerStore


def run_continuation(args: object, release: dict) -> dict:
    from app.services.news_verified_cloud import preflight, assets_for_release, resolver_for_release
    from app.services.news_gma_budget_review import prepare_parent
    from app.services.news_three_article_pilot import PilotAuthority
    from app.services.news_sources import load_news_sources
    from app.services.configuration_service import selected_news_sources
    from app.services.news_pilot_accounting import accounting_policy
    from app.services.news_gma_review import archive_outputs
    operation = {'gma-scoped-prepare':'count','gma-scoped-resolve':'resolve',
        'gma-scoped-preview':'archive','gma-scoped-archive':'archive'}[args.mode]
    document,_ = GCSLedgerStore('lanes-storage',args.authority_object).read()
    if (sha(document) != args.authority_sha256 or document.get('schema_version') != VERSION
            or document.get('release_sha256') != sha(release) or document.get('resolver') != release['resolver']
            or document.get('receipts_prefix') != os.environ.get('LANES_NEWS_RECEIPTS_PREFIX')):
        raise ResolutionError('gma_scoped_release_authority_changed')
    ledger = GCSLedgerStore('lanes-storage',document['budget_object'])
    trusted = assets_for_release(release)
    resolver = resolver_for_release(release)
    journal = resolver.receipts.store
    authority = PilotAuthority(document,sha(document),trusted)
    engine = create_engine(settings.DATABASE_URL,hide_parameters=True,connect_args={'connect_timeout':5})
    budget = None
    try:
        preflight(release,database_url=settings.DATABASE_URL)
        factory = sessionmaker(bind=engine)
        with factory() as db:
            db.connection().exec_driver_sql('SET TRANSACTION READ ONLY')
            authority.validate_session(db,(375,) if operation != 'archive' else tuple(args.run_id),
                load_news_sources(),operation=operation)
            source,baseline = prepare_parent(db,trusted,resolver,selected_news_sources(db,load_news_sources()))
        resolver.catalog = trusted.catalog
        packets = resolver.request_packets(source,baseline,parent_run_id=375,
            parent_result_sha256=document['parent_result_sha256'])
        if [sha(p['payload']) for p in packets] != list(REQUESTS):
            raise ResolutionError('gma_frozen_request_changed')
        if operation == 'count':
            state,_ = ledger.read()
            if (sha(state) != document['ledger_baseline_sha256'] or state['status'] != 'stopped'
                    or len(state['attempts']) != 24 or any(a['status']=='in_flight' for a in state['attempts'])):
                raise ResolutionError('gma_scoped_count_baseline_changed')
            # Existing retained-count primitive has immutable per-payload intent,
            # bounded response-before-parse and no retries. The new authority and
            # dedicated receipt prefix separate it from the consumed diagnostic.
            from app.services.news_scoped_gma_diagnostic import count_once
            async def count_all() -> dict:
                items = []
                async with httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(retries=0)) as http:
                    for index,packet in enumerate(packets):
                        if index == 3:
                            continue
                        catalog = await count_once(resolver.config,packet,resolver.receipts,http=http,
                            session_id=SESSION,schema_version=VERSION)
                        items.extend(catalog['requests'])
                return {'schema_version':'news-pilot-count-catalog-v2',
                    'accounting_policy_sha256':sha(accounting_policy()),'requests':items}
            catalog = asyncio.run(count_all())
            key = sha(catalog)+'/count-catalog.json'
            journal.put(key,catalog)
            return {'status':'completed','count_requests':12,'generation_requests':0,'database_writes':0,
                'catalog_object':resolver.receipts.store.prefix+key,'catalog_sha256':sha(catalog)}
        if operation == 'archive':
            if len(args.run_id) != 1:
                raise ResolutionError('gma_archive_selection_invalid')
            result = archive_outputs(engine,authority,args.run_id[0],sources=load_news_sources(),
                apply=args.mode=='gma-scoped-archive')
            projections = {sha(o['read_projection']):o['read_projection'] for o in result['outputs']
                if 'read_projection' in o}
            private = {**result,'canonical_result_sha256':sha(result),'read_projections':projections,
                'outputs':[{**{k:v for k,v in o.items() if k != 'read_projection'},
                    **({'read_projection_sha256':sha(o['read_projection'])} if 'read_projection' in o else {})}
                    for o in result['outputs']]}
            key = sha(private)+'/archive-output.json'
            journal.put(key,private)
            from collections import Counter
            return {'status':'completed','outputs_sha256':result.get('outputs_sha256'),
                'private_output_object':document['receipts_prefix']+key,'group_count':len(result['outputs']),
                'outcomes':dict(Counter(o['outcome'] for o in result['outputs'])),'active_instances_created':0}
        reference = document['count_catalog']
        catalog,_ = GCSLedgerStore('lanes-storage',reference['object']).read()
        budget = ScopedGmaBudget(ledger,document['budget_identity'],policy=batch_manifest()['accounting_extension'],
            counts=catalog,counts_sha256=reference['sha256'],journal=journal)
        state,_ = budget._read()
        qualify_schedule(packets,catalog,state)
        resolver.budget = budget
        # Completed-run reuse is checked before any resolver dispatch; the stopped
        # ledger is intentionally sufficient for this idempotence check.
        from app.services.news_ner_durable.resolution_worker import resolve_native_runs
        result = asyncio.run(resolve_native_runs(factory,(375,),trusted=trusted,resolver=resolver,
            sources=load_news_sources(),limit=1,pilot_authorization=authority))
        return {'status':'completed' if result['completed'] or result['reused'] else 'requires_attention',**result}
    finally:
        if operation == 'resolve':
            state,generation = ledger.read()
            if state.get('manual_resumptions',[{}])[-1].get('id') == SESSION and state['status'] != 'stopped':
                state.update(status='stopped',stop_reason='gma_scoped_stage_finished_requires_review')
                ledger.compare_and_swap(generation,state)
        engine.dispose()
