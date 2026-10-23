"""Local-only native queue worker. Never evaluates, places or publishes."""
from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
import platform
import os
import signal
import threading
import time

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.crud.news_processing import MAX_ATTEMPTS, capture_pending_inputs, claim_due_run, finish_owned_run, utc_now
from app.services.configuration_service import read_configuration, selected_news_sources
from app.services.news_ner_runtime.supervisor import Session as ModelSession, RuntimeFailure
from .adapter import build_native_result
from .assets import TrustedAssets
from .contracts import NerEvidenceError, RunEvidence

JOB_SECONDS=450
ARTICLE_SECONDS=125
WORK_SECONDS=115
TRANSACTION_SECONDS=5


class OperationDeadline(RuntimeError):
    pass


def require_local_target(environment: str, database_url: str) -> None:
    try:
        url=make_url(database_url)
        if environment!='test' or url.get_backend_name()!='postgresql' or not (url.database or '').startswith('lanes_p3_verify_'):
            raise ValueError('not_disposable')
    except (ValueError,TypeError) as exc:
        raise NerEvidenceError('ner_configuration_invalid') from exc


@contextmanager
def deadline(seconds: float) -> Iterator[None]:
    if seconds<=0:raise OperationDeadline('ner_runtime_timeout')
    if platform.system()!='Linux' or threading.current_thread() is not threading.main_thread():
        raise NerEvidenceError('ner_configuration_invalid')
    if signal.getitimer(signal.ITIMER_REAL)[0]:raise NerEvidenceError('ner_configuration_invalid')
    previous=signal.getsignal(signal.SIGALRM)
    def expired(*_args: object) -> None:raise OperationDeadline('ner_runtime_timeout')
    signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,seconds)
    try:yield
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)


@dataclass
class NativeProcessingSummary:
    processing_method: str='ner_rules_v1'
    pipeline_version: str | None=None
    captured: int=0
    completed: int=0
    failed: int=0
    retry_wait: int=0
    lease_lost: int=0
    stop_reason: str='limit_reached'
    error_code: str | None=None
    runs: list[dict]=field(default_factory=list)
    resource_snapshots: list[dict]=field(default_factory=list)


@contextmanager
def transaction(factory: Callable[[],Session], seconds: float=TRANSACTION_SECONDS) -> Iterator[Session]:
    with deadline(min(seconds,TRANSACTION_SECONDS)):
        with factory() as db,db.begin():
            # PostgreSQL cancels blocking SQL independently of Python's timer.
            milliseconds=max(1,int(min(seconds,TRANSACTION_SECONDS)*1000))
            db.execute(text("SELECT set_config('statement_timeout', :timeout, true), set_config('lock_timeout', :timeout, true)"),
                       {'timeout':str(milliseconds)})
            yield db


async def process_native_saved_news(factory: Callable[[],Session], *, load_assets: Callable[[],TrustedAssets],
        environment: str, database_url: str, limit: int=50, article_id: int | None=None, sources: tuple | None=None,
        runtime_factory: Callable[[TrustedAssets],ModelSession] | None=None,
        clock: Callable[[],datetime]=utc_now, monotonic: Callable[[],float]=time.monotonic,
        invocation_deadline: float | None=None, prepare_readers: bool=False,
        run_ids: tuple[int,...] | None=None, historical_authorization: object | None=None) -> NativeProcessingSummary:
    started=monotonic();end=started+JOB_SECONDS
    if invocation_deadline is not None:
        from math import isfinite
        if not isfinite(invocation_deadline):raise NerEvidenceError('ner_configuration_invalid')
        end=min(end,invocation_deadline)
    if historical_authorization is None:
        require_local_target(environment,database_url)
    else:
        from app.services.news_historical_policy import HistoricalAuthorization
        from app.services.news_three_article_pilot import PilotAuthority
        if (type(historical_authorization) not in (HistoricalAuthorization, PilotAuthority) or run_ids is None
                or article_id is not None or prepare_readers):
            raise NerEvidenceError('ner_configuration_invalid')
    if not 1<=limit<=200 or (article_id is not None and article_id<=0):raise NerEvidenceError('ner_configuration_invalid')
    if run_ids is not None and (not isinstance(run_ids,tuple) or len(run_ids)>limit
            or any(type(i) is not int or i<=0 for i in run_ids) or len(set(run_ids))!=len(run_ids) or article_id is not None):
        raise NerEvidenceError('ner_configuration_invalid')
    summary=NativeProcessingSummary();runtime=None;cancelled=False
    def resource_check() -> None:
        if os.environ.get('LANES_HISTORY_RESOURCE_PROFILE') == 'cloud-run-v1':
            if historical_authorization is None or historical_authorization.policy.get('resource_profile') != 'cloud-run-v1':
                raise NerEvidenceError('ner_configuration_invalid')
            from app.services.news_history_resources import checkpoint
            try:
                summary.resource_snapshots.append(checkpoint())
            except (OSError, ValueError) as exc:
                raise NerEvidenceError('ner_configuration_invalid') from exc
    if end-started<ARTICLE_SECONDS:
        summary.stop_reason='budget_exhausted'
        return summary
    try:
        resource_check()
        with deadline(min(60,end-monotonic())):
            trusted=load_assets();trusted.validate()
        summary.pipeline_version=trusted.pipeline_version
        if historical_authorization is not None and trusted.manifest != historical_authorization.trusted.manifest:
            raise NerEvidenceError('ner_configuration_invalid')
        # Verify the actual connection, not just a supplied URL, before writes.
        with transaction(factory) as db:
            if historical_authorization is not None:
                historical_authorization.validate_session(db, run_ids, sources)
            if db.scalar(text('SELECT current_database()'))!=make_url(database_url).database:
                raise NerEvidenceError('ner_configuration_invalid')
            from app.services.news_three_article_pilot import PilotAuthority
            if not read_configuration(db).news_processing_enabled and type(historical_authorization) is not PilotAuthority:
                summary.stop_reason='paused';return summary
            selected=tuple(s.id for s in selected_news_sources(db,sources))
            if run_ids is not None:
                pass  # An explicit capture set never enters the mutable-article handoff.
            elif article_id is None:
                summary.captured=capture_pending_inputs(db,limit,selected,mode='ner_rules_v1',pipeline_version=trusted.pipeline_version)
            else:
                from .capture import capture_native_pending_inputs
                summary.captured=capture_native_pending_inputs(db,limit,selected,trusted.pipeline_version,article_id)
        for _ in range(limit):
            if end-monotonic()<ARTICLE_SECONDS:
                summary.stop_reason='budget_exhausted';break
            operation=monotonic();work_end=operation+WORK_SECONDS
            with transaction(factory) as db:
                if historical_authorization is not None:
                    historical_authorization.validate_session(db, run_ids, sources)
                if not read_configuration(db).news_processing_enabled and type(historical_authorization) is not PilotAuthority:
                    summary.stop_reason='paused';break
                current=tuple(s.id for s in selected_news_sources(db,sources))
                if current!=selected:
                    summary.stop_reason='sources_changed';break
                selection = {'run_ids':run_ids, 'pending_only':True} if run_ids is not None else {}
                claim=claim_due_run(db,clock(),article_id=article_id,source_ids=current,
                    mode='ner_rules_v1',pipeline_version=trusted.pipeline_version, **selection)
            if claim is None:
                summary.stop_reason='no_work';break
            if claim.exhausted:
                summary.failed+=1;summary.runs.append({'run_id':claim.run_id,'status':'failed','error_code':'lease_expired_exhausted'})
                continue
            result=None;code=None;retryable=False;stop=False
            try:
                with deadline(work_end-monotonic()):
                    from types import SimpleNamespace
                    context=RunEvidence.from_records(SimpleNamespace(id=claim.run_id,article_version_id=claim.article_version_id,
                        mode=claim.mode,pipeline_version=claim.pipeline_version),SimpleNamespace(id=claim.article_version_id,
                        article_id=claim.article_id,input_snapshot=claim.input_snapshot,input_fingerprint=claim.input_fingerprint))
                    request=context.source().runtime_request(claim.input_fingerprint)
                    trusted.validate()
                if runtime is None:
                    resource_check()
                    runtime=(runtime_factory(trusted) if runtime_factory else ModelSession(trusted.manifest['model']['bundle_sha256'],trusted._code))
                    await asyncio.wait_for(runtime.start(),timeout=min(60,max(.001,work_end-monotonic())))
                # The runtime owns its timer while validating neural output.
                inference=await asyncio.wait_for(runtime.request(request,timeout=min(60,max(.001,work_end-monotonic()))),
                                                 timeout=max(.001,work_end-monotonic()))
                with deadline(work_end-monotonic()):
                    resource_check()
                    prepared=build_native_result(context,inference,trusted,extracted_at=clock())
                    if historical_authorization is not None:
                        from .read_projection import build_read_projection
                        prepared.read_projection=build_read_projection(context.source(),prepared,trusted.catalog)
                    if prepare_readers:
                        from .enrichment import enrich_native_result
                        prepared=enrich_native_result(context,prepared,trusted)
                    result=prepared.model_dump(mode='json',by_alias=True)
                    resource_check()
            except NerEvidenceError as exc:
                code=exc.code;stop=code!='ner_input_binding_invalid'
            except (OperationDeadline,asyncio.TimeoutError):
                code='ner_runtime_timeout';retryable=stop=True
            except asyncio.CancelledError:
                code='ner_runtime_cancelled';retryable=stop=cancelled=True
            except RuntimeFailure as exc:
                code='ner_runtime_timeout' if str(exc) in ('deadline','session_budget') else 'ner_runtime_failed'
                retryable=stop=True
            except ValueError:
                code='ner_result_contract_invalid';stop=True
            except Exception:
                code='ner_runtime_failed';retryable=stop=True
            if stop and runtime is not None:
                try:await runtime.close()
                except (Exception,asyncio.CancelledError):summary.error_code='ner_runtime_cleanup_failed'
            # Cancellation/error is persisted once, never retried in this session.
            with transaction(factory,min(TRANSACTION_SECONDS,operation+ARTICLE_SECONDS-monotonic())) as db:
                if historical_authorization is not None:
                    historical_authorization.validate_session(db, run_ids, sources)
                owned=finish_owned_run(db,claim,clock(),result=result,error_code=code,retryable=retryable)
            status='lease_lost' if not owned else 'retry_wait' if code and retryable and claim.attempt_count<MAX_ATTEMPTS else 'failed' if code else 'completed'
            setattr(summary,status,getattr(summary,status)+1)
            summary.runs.append({'run_id':claim.run_id,'status':status,'error_code':code,
                                 'operation_seconds':round(monotonic()-operation,6)})
            if stop:
                summary.stop_reason='cancelled' if cancelled else 'processing_failed';break
    except (SQLAlchemyError,OperationDeadline):
        summary.error_code='news_processing_storage_unavailable';summary.stop_reason='storage_failed'
    except NerEvidenceError as exc:
        summary.error_code=exc.code;summary.stop_reason='configuration_or_contract_failed'
    finally:
        if runtime is not None:
            try:await runtime.close()
            except (Exception,asyncio.CancelledError):
                summary.error_code='ner_runtime_cleanup_failed';summary.stop_reason='cleanup_failed'
        try:
            resource_check()
        except NerEvidenceError:
            summary.error_code='historical_resource_envelope_unqualified';summary.stop_reason='resource_failed'
    if cancelled:raise asyncio.CancelledError()
    return summary
