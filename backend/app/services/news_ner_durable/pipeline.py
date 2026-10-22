"""Controlled local RSS-to-native pipeline; the scheduled production default is unchanged."""
from __future__ import annotations

from contextlib import nullcontext
from dataclasses import asdict
from datetime import datetime
import time

import httpx
from sqlalchemy import event,text
from sqlalchemy.exc import SQLAlchemyError

from app.crud.news_processing import utc_now
from app.services.configuration_service import read_configuration,selected_news_sources
from app.services.news_discovery_service import discover_news
from .collection import NativeCollectionContext
from .contracts import NerEvidenceError
from .processing import (process_native_saved_news,deadline,OperationDeadline,require_local_target)
from .evaluation import native_evaluation_policy,seed_native_evaluations,evaluate_native_claims
from .reconciliation import pending_reconciliation_runs,reconcile_native_article

INVOCATION_SECONDS=580
DISCOVERY_SECONDS=120
DOWNSTREAM_SECONDS=100
FINAL_SECONDS=10


def bounded_session_factory(factory, end: float, monotonic):
    def create():
        db=factory()
        def after_begin(_session,_transaction,connection):
            remaining=end-monotonic()
            if remaining<=0:raise OperationDeadline()
            milliseconds=max(1,int(min(5,remaining)*1000))
            connection.execute(text("SELECT set_config('statement_timeout', :value, true), set_config('lock_timeout', :value, true)"),
                               {'value':str(milliseconds)})
        event.listen(db,'after_begin',after_begin)
        return db
    return create


async def run_native_news_pipeline(factory, *, load_assets, environment: str, database_url: str,
        sources: tuple, client: httpx.Client | None=None, limit: int=50, clock=utc_now,
        monotonic=time.monotonic, runtime_factory=None, on_stage=None) -> dict:
    started=monotonic();end=started+INVOCATION_SECONDS
    require_local_target(environment,database_url)
    if not 1<=limit<=200:raise NerEvidenceError('ner_configuration_invalid')
    factory=bounded_session_factory(factory,end-FINAL_SECONDS,monotonic)
    result={'processing_method':'ner_rules_v1','pipeline_version':None,'stage_outcomes':{},'error_code':None,
            'stop_reason':'completed','reconciled':0}
    def report(stage,summary=None):
        if on_stage:on_stage(stage,summary)
    try:
        with deadline(min(60,end-monotonic()-FINAL_SECONDS)):
            trusted=load_assets();trusted.validate()
            if 'placement' not in trusted.manifest['geography']:
                raise NerEvidenceError('ner_configuration_invalid')
            context=NativeCollectionContext(trusted,environment,database_url)
            with factory() as db:
                context.validate(db)
                try:
                    configuration=read_configuration(db);selected=selected_news_sources(db,sources)
                except (ValueError,TypeError,KeyError) as exc:
                    raise NerEvidenceError('ner_configuration_invalid') from exc
            result['pipeline_version']=trusted.pipeline_version
            policy=native_evaluation_policy(trusted,configuration)
        report('collection')
        if configuration.news_collection_enabled and selected:
            with deadline(min(DISCOVERY_SECONDS-(monotonic()-started),end-monotonic()-DOWNSTREAM_SECONDS-FINAL_SECONDS)):
                managed=httpx.Client(timeout=httpx.Timeout(12,connect=5)) if client is None else nullcontext(client)
                with managed as http, factory() as db:
                    run=discover_news(selected,http,db,processing_context=context)
                result['collection']={'entries_read':sum(p.entry_count for p in run.probes),
                    'captured_candidates':len(run.candidates),'failed':sum(bool(p.error) for p in run.probes)}
                result['stage_outcomes']['collection']='failed' if result['collection']['failed'] else 'completed'
        else:
            result['collection']={'entries_read':0,'captured_candidates':0,'failed':0}
            result['stage_outcomes']['collection']='paused' if not configuration.news_collection_enabled else 'no_enabled_sources'
        report('collection',result['collection'])
        report('extraction')
        if configuration.news_processing_enabled:
            summary=await process_native_saved_news(factory,load_assets=lambda:trusted,environment=environment,
                database_url=database_url,sources=sources,limit=limit,clock=clock,monotonic=monotonic,
                runtime_factory=runtime_factory,prepare_readers=True,
                invocation_deadline=end-DOWNSTREAM_SECONDS-FINAL_SECONDS)
            result['extraction']=asdict(summary)
            result['stage_outcomes']['extraction']='failed' if summary.error_code or summary.failed or summary.retry_wait else summary.stop_reason
            if summary.error_code:result['error_code']=summary.error_code
        else:
            result['extraction']={'completed':0,'error_code':None,'stop_reason':'paused'}
            result['stage_outcomes']['extraction']='paused'
        report('extraction',result['extraction'])
        with deadline(min(DOWNSTREAM_SECONDS,end-monotonic()-FINAL_SECONDS)):
            if configuration.news_processing_enabled:
                report('seed')
                result['seed']=asdict(seed_native_evaluations(factory,policy,now=clock(),sources=sources,limit=limit))
                report('seed',result['seed']);report('evaluation')
                result['evaluation']=asdict(evaluate_native_claims(factory,policy,clock=clock,sources=sources,limit=limit))
                report('evaluation',result['evaluation'])
            report('publication')
            from app.services.news_publication_service import process_news_publications
            with factory() as db:publication_enabled=read_configuration(db).news_publication_enabled
            result['publication']=asdict(process_news_publications(factory,policy=policy,clock=clock,sources=sources,
                limit=limit,maintenance_only=not publication_enabled))
            report('publication',result['publication'])
            if publication_enabled:
                report('footprints')
                from app.services.news_footprint_worker_service import process_news_footprints
                result['footprints']=asdict(process_news_footprints(factory,policy=policy,clock=clock,sources=sources,limit=limit))
                report('footprints',result['footprints'])
            with factory() as db:ids=pending_reconciliation_runs(db,trusted.pipeline_version,limit)
            report('reconciliation')
            for run_id in ids:
                with factory() as db,db.begin():
                    result['reconciled']+=reconcile_native_article(db,run_id,now=clock(),policy=policy)
            report('reconciliation',{'completed':result['reconciled']})
        from app.services.news_pipeline_service import pipeline_has_failures
        if result['extraction'].get('stop_reason')=='budget_exhausted':
            result['stop_reason']='budget_exhausted'
        if pipeline_has_failures(result) or result['collection']['failed']:
            result['stop_reason']='requires_attention'
    except OperationDeadline:
        result['error_code']='ner_pipeline_budget_exhausted';result['stop_reason']='budget_exhausted'
    except NerEvidenceError as exc:
        result['error_code']=exc.code;result['stop_reason']='configuration_or_contract_failed'
    except SQLAlchemyError:
        result['error_code']='news_processing_storage_unavailable';result['stop_reason']='storage_failed'
    except Exception:
        result['error_code']='ner_runtime_failed';result['stop_reason']='requires_attention'
    result['elapsed_seconds']=round(monotonic()-started,6)
    return result
