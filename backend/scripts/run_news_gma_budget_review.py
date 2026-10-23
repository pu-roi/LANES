"""Explicit tokenizer, single gate, complete correction, or archive-only stage."""
from __future__ import annotations

import asyncio
import os

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError, resolve_rows
from app.services.news_pilot_budget import GCSLedgerStore
from app.services.news_pilot_accounting import AccountedPilotBudget, accounting_policy, count_request
from app.services.news_gma_budget_review import prepare_parent, qualify_schedule, REQUESTS


def run_budget_review(args: object, release: dict) -> dict:
    from app.services.news_verified_cloud import assets_for_release,resolver_for_release
    from app.services.news_three_article_pilot import PilotAuthority
    from app.services.news_sources import load_news_sources
    from app.services.news_gemini_receipts import request_batch, replay_bundle
    from app.services.news_gma_review import archive_outputs
    document,_=GCSLedgerStore('lanes-storage',args.authority_object).read()
    if (sha(document)!=args.authority_sha256 or document.get('schema_version')!='news-gma-budget-review-v2'
            or document.get('release_sha256')!=sha(release) or document.get('resolver')!=release['resolver']
            or document.get('resolved_pipeline_version')!=release['resolved_pipeline_version']):
        raise ResolutionError('gma_release_authority_changed')
    trusted=assets_for_release(release);resolver=resolver_for_release(release)
    if resolver.receipts is None:raise ResolutionError('gma_receipts_required')
    journal=resolver.receipts.store;authority=PilotAuthority(document,args.authority_sha256,trusted)
    engine=create_engine(settings.DATABASE_URL,hide_parameters=True,connect_args={'connect_timeout':5})
    factory=sessionmaker(bind=engine,expire_on_commit=False);sources=load_news_sources()
    operation={'gma-count':'count','gma-gate':'gate','gma-budget-resolve':'resolve',
        'gma-budget-preview':'archive','gma-budget-archive':'archive'}[args.mode]
    try:
        authority.validate(engine)
        with factory() as db:
            db.connection().exec_driver_sql('SET TRANSACTION READ ONLY')
            authority.validate_session(db,(375,) if operation!='archive' else tuple(args.run_id),sources,operation=operation)
            source,baseline=prepare_parent(db,trusted,resolver,sources)
        resolver.catalog=trusted.catalog
        packets=resolver.request_packets(source,baseline,parent_run_id=375,
            parent_result_sha256=document['parent_result_sha256'])
        if [sha(p['payload']) for p in packets]!=list(REQUESTS):raise ResolutionError('gma_frozen_request_changed')
        if operation=='count':
            async def count_all():
                values=[]
                async with httpx.AsyncClient() as client:
                    for packet in packets:
                        values.append(await count_request(resolver.config,packet['payload'],http=client,journal=journal))
                return {'schema_version':'news-pilot-count-catalog-v2',
                    'accounting_policy_sha256':sha(accounting_policy()),'requests':values}
            catalog=asyncio.run(count_all());key=sha(catalog)+'/count-catalog.json';journal.put(key,catalog)
            return {'status':'completed','count_requests':13,'generation_requests':0,'database_writes':0,
                'catalog_object':journal.prefix+key,'catalog_sha256':sha(catalog)}
        if operation=='archive':
            if len(args.run_id)!=1:raise ResolutionError('gma_archive_selection_invalid')
            result=archive_outputs(engine,authority,args.run_id[0],sources=sources,apply=args.mode=='gma-budget-archive')
            projections={sha(o['read_projection']):o['read_projection'] for o in result['outputs'] if 'read_projection' in o}
            private={**result,'canonical_result_sha256':sha(result),'read_projections':projections,
                'outputs':[{**{k:v for k,v in o.items() if k!='read_projection'},
                    **({'read_projection_sha256':sha(o['read_projection'])} if 'read_projection' in o else {})} for o in result['outputs']]}
            key=sha(private)+'/archive-output.json';journal.put(key,private)
            from collections import Counter
            return {'status':'completed','outputs_sha256':result.get('outputs_sha256'),
                'private_output_object':journal.prefix+key,'group_count':len(result['outputs']),
                'outcomes':dict(Counter(o['outcome'] for o in result['outputs'])),'active_instances_created':0}
        reference=document['count_catalog'];catalog,_=GCSLedgerStore('lanes-storage',reference['object']).read()
        budget=AccountedPilotBudget(GCSLedgerStore('lanes-storage',document['budget_object']),document['budget_identity'],
            counts=catalog,counts_sha256=reference['sha256'],journal=journal)
        state,_=budget._read();projected=qualify_schedule(packets,catalog,state)
        if state['status']!='ready':raise ResolutionError('pilot_budget_stopped_or_in_flight')
        resolver.budget=budget
        try:
            if operation=='gate':
                if len(state['attempts'])!=20:raise ResolutionError('gma_gate_attempt_baseline_changed')
                async def gate():
                    packet=packets[1]
                    async with httpx.AsyncClient() as client:
                        parsed,usage=await request_batch(resolver.config,packet['payload'],packet['context'],
                            http=client,timeout=resolver.timeout_seconds,budget=budget,journal=resolver.receipts)
                    try:resolve_rows(source,baseline,parsed.results,trusted.catalog)
                    except ResolutionError as exc:
                        resolver.receipts.semantic(packet['payload'],packet['context'],error_code=exc.code);raise
                    resolver.receipts.semantic(packet['payload'],packet['context'])
                    key=sha({'request_sha256':sha(packet['payload']),'context':packet['context']})
                    bundle={'intent':journal.get(key+'/intent.json'),'response':journal.get(key+'/response.json')}
                    pin=sha(bundle);journal.put(pin+'/accepted-gate.json',bundle)
                    return {'status':'completed','one_batch_acceptance':True,'generation_requests':1,'database_writes':0,
                        'gate_bundle_object':journal.prefix+pin+'/accepted-gate.json','gate_bundle_sha256':pin,
                        'projected_commitment_nanodollars':projected,'usage':usage}
                return asyncio.run(gate())
            reference=document['accepted_gate'];bundle,_=GCSLedgerStore('lanes-storage',reference['object']).read()
            if replay_bundle(bundle,reference['sha256'],config=resolver.config)['status']!='evidence_references_passed':
                raise ResolutionError('gma_cached_gate_changed')
            # Revalidate all source semantics before permitting the next paid batch.
            from app.services.news_gemini_receipts import validate_batch
            import base64
            parsed,_=validate_batch(packets[1]['payload'],base64.b64decode(bundle['response']['body_base64']),resolver.config)
            resolve_rows(source,baseline,parsed.results,trusted.catalog)
            resolver.batch_plan.accepted_gate={'bundle':bundle,'sha256':reference['sha256']}
            from app.services.news_ner_durable.resolution_worker import resolve_native_runs
            result=asyncio.run(resolve_native_runs(factory,(375,),trusted=trusted,resolver=resolver,sources=sources,
                limit=1,pilot_authorization=authority))
            return {'status':'completed' if result['completed'] or result['reused'] else 'requires_attention',**result}
        finally:budget.stop('gma_budget_review_stage_finished')
    finally:engine.dispose()
