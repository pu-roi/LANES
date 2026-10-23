"""Owned, repeatable Gemini handoff using existing article/run tables only.

The raw NER run is immutable. A separate native run with a distinct pinned
projection identity holds the corrected JSON. No inference/discovery/publication.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import time

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from app.crud.news_processing import claim_due_run, finish_owned_run
from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.schemas.news_ner_result import parse_saved_result
from app.services.configuration_service import read_configuration, selected_news_sources
from app.services.news_evaluation_service import source_is_approved
from .adapter import build_native_result, verify_saved_result
from .assets import with_resolution_assets
from .contracts import RunEvidence, sha
from .resolution import ResolutionError, apply_resolution, targets
from .read_projection import build_read_projection


def _parent(db: object, run_id: int, sources: tuple, *, lock: bool = False) -> tuple:
    query = select(NewsExtractionRun).where(NewsExtractionRun.id == run_id)
    if lock:
        query = query.with_for_update()
    run = db.scalar(query)
    if run is None or run.mode != 'ner_rules_v1' or run.status != 'completed':
        raise ResolutionError('native_resolution_parent_invalid')
    version = db.get(NewsArticleVersion, run.article_version_id)
    context = RunEvidence.from_records(run, version)
    source = context.source()
    from app.schemas.news_extraction import NewsArticleExtractorInput
    article = NewsArticleExtractorInput.model_validate({**context.input_snapshot,'article_id':context.article_id})
    if not source_is_approved(article, sources):
        raise ResolutionError('native_resolution_source_suppressed')
    original = parse_saved_result(run.mode, run.result)
    if 'llm_resolution' in original.provenance:
        raise ResolutionError('native_resolution_parent_already_derived')
    if (original.source.input_fingerprint != context.input_fingerprint
            or original.source.text_sha256 != source.runtime_request(context.input_fingerprint)['text_sha256']):
        raise ResolutionError('native_resolution_parent_binding_invalid')
    return run, version, context, source, original


def verify_authority(factory: object, run_ids: tuple[int, ...], trusted: object, identity: dict,
                     sources: tuple, authority: dict | None, authority_sha256: str | None) -> None:
    """Shared writes need an exact reviewed target/selection/code/model grant."""
    from app.services.news_historical_processing import database_identity
    trusted.validate()
    if trusted.manifest['projection'].get('llm_resolution') is not None:
        raise ResolutionError('native_resolution_parent_assets_required')
    if not run_ids or len(run_ids)>200 or len(set(run_ids))!=len(run_ids) or any(type(i)!=int or i<=0 for i in run_ids):
        raise ResolutionError('native_resolution_selection_invalid')
    with factory() as db:
        if db.scalar(text('SELECT version_num FROM alembic_version'))!='f1a9c7e2b604' or not db.scalar(text('SELECT postgis_version()')):
            raise ResolutionError('native_resolution_schema_invalid')
        actual = db.scalar(text('SELECT current_database()'))
        if actual != db.get_bind().url.database or db.get_bind().dialect.name != 'postgresql':
            raise ResolutionError('native_resolution_target_invalid')
        selected = selected_news_sources(db, sources)
        rows = [_parent(db,i,selected) for i in run_ids]
        if len({r[1].id for r in rows}) != len(rows):
            raise ResolutionError('native_resolution_duplicate_version')
        for _run,_version,_context,source,original in rows:
            targets(original)
            from .resolution import quote_options
            quote_options(source.article_text)
        expected = {'schema_version':'native-resolution-authority-v1',
            'database_identity_sha256':database_identity(db.get_bind()),
            'assets_sha256':sha(trusted.manifest),'resolver':identity,'allowed_operations':['resolve'],
            'inputs':[{'run_id':r[0].id,'result_sha256':sha(r[0].result),
                       'input_sha256':r[2].input_fingerprint} for r in rows]}
        if authority is None:
            if authority_sha256 is not None or not actual.startswith('lanes_p3_verify_'):
                raise ResolutionError('native_resolution_authority_required')
        elif (sha(authority)!=authority_sha256 or authority!=expected):
            raise ResolutionError('native_resolution_authority_mismatch')


def resolution_preflight(factory: object, run_ids: tuple[int, ...], trusted: object, identity: dict,
                         sources: tuple) -> dict:
    """Read-only review artifact; never checks a credential with a paid request."""
    from app.services.news_historical_processing import database_identity
    trusted.validate()
    if trusted.manifest['projection'].get('llm_resolution') is not None:
        raise ResolutionError('native_resolution_parent_assets_required')
    if not run_ids or len(run_ids)>2 or len(set(run_ids))!=len(run_ids) or any(type(i)!=int or i<=0 for i in run_ids):
        raise ResolutionError('native_resolution_selection_invalid')
    with factory() as db:
        if db.scalar(text('SELECT version_num FROM alembic_version'))!='f1a9c7e2b604' or not db.scalar(text('SELECT postgis_version()')):
            raise ResolutionError('native_resolution_schema_invalid')
        if (db.get_bind().dialect.name!='postgresql'
                or db.scalar(text('SELECT current_database()'))!=db.get_bind().url.database):
            raise ResolutionError('native_resolution_target_invalid')
        selected=selected_news_sources(db,sources)
        rows=[_parent(db,i,selected) for i in run_ids]
        if len({r[1].id for r in rows})!=len(rows):
            raise ResolutionError('native_resolution_duplicate_version')
        return {'schema_version':'native-resolution-authority-v1',
            'database_identity_sha256':database_identity(db.get_bind()),'assets_sha256':sha(trusted.manifest),
            'resolver':identity,'allowed_operations':['resolve'],
            'inputs':[{'run_id':r[0].id,'result_sha256':sha(r[0].result),'input_sha256':r[2].input_fingerprint} for r in rows],
            # The authority excludes output/run IDs; those are discovered safely
            # by the unique existing version/method/pipeline constraint.
        }


async def resolve_native_runs(factory: object, run_ids: tuple[int, ...], *, trusted: object,
        resolver: object, sources: tuple, clock: object = None, client: object = None,
        limit: int = 2, authority: dict | None = None, authority_sha256: str | None = None,
        budget_seconds: float = 450, pilot_authorization: object | None = None) -> dict:
    """At most two owned runs per invocation. API calls have no open SQL txn."""
    clock = clock or (lambda:datetime.now(timezone.utc))
    if not 1<=limit<=2 or not 1<=budget_seconds<=450:
        raise ResolutionError('native_resolution_batch_invalid')
    def verify_grant() -> None:
        if pilot_authorization is None:
            verify_authority(factory,run_ids,trusted,resolver.identity,sources,authority,authority_sha256)
        else:
            from app.services.news_three_article_pilot import PilotAuthority
            if (type(pilot_authorization) is not PilotAuthority or authority is not None
                    or authority_sha256 is not None or resolver.budget is None
                    or pilot_authorization.policy.get('resolver') != resolver.identity
                    or pilot_authorization.policy.get('assets_sha256') != sha(trusted.manifest)):
                raise ResolutionError('pilot_resolution_grant_invalid')
            with factory() as db:
                pilot_authorization.validate_session(db, run_ids, sources, operation='resolve')
    verify_grant()
    derived = with_resolution_assets(trusted,resolver.identity)
    resolver.catalog = trusted.catalog
    end = time.monotonic() + budget_seconds
    summary={'pipeline_version':derived.pipeline_version,'completed':0,'reused':0,'failed':0,
        'retry_wait':0,'busy':0,'request_count':0,'input_tokens':0,'output_tokens':0,'thinking_tokens':0,'runs':[]}
    for parent_id in run_ids[:limit]:
        if end - time.monotonic() < 5:
            summary['stop_reason']='budget_exhausted'
            break
        verify_grant()
        with factory() as db,db.begin():
            if pilot_authorization is not None:
                pilot_authorization.validate_session(db, run_ids, sources, operation='resolve')
            if not read_configuration(db).news_processing_enabled and pilot_authorization is None:
                raise ResolutionError('native_resolution_processing_paused')
            parent,version,parent_context,source,original=_parent(db,parent_id,selected_news_sources(db,sources),lock=True)
            parent_hash=sha(parent.result)
            run_id=db.scalar(insert(NewsExtractionRun).values(article_version_id=version.id,
                pipeline_version=derived.pipeline_version,mode='ner_rules_v1',status='pending',attempt_count=0,
                created_at=clock(),updated_at=clock()).on_conflict_do_nothing(
                    index_elements=['article_version_id','pipeline_version','mode']).returning(NewsExtractionRun.id))
            run=db.get(NewsExtractionRun,run_id) if run_id else db.scalar(select(NewsExtractionRun).where(
                NewsExtractionRun.article_version_id==version.id,NewsExtractionRun.pipeline_version==derived.pipeline_version,
                NewsExtractionRun.mode=='ner_rules_v1'))
            context=RunEvidence.from_records(run,version)
            if run.status=='completed':
                saved=verify_saved_result(context,run.result,derived)
                if saved.provenance['llm_resolution']['parent_run_id']!=parent_id or saved.provenance['llm_resolution']['parent_result_sha256']!=parent_hash:
                    raise ResolutionError('native_resolution_parent_changed')
                summary['reused']+=1;summary['runs'].append({'run_id':run.id,'parent_run_id':parent_id,'status':'reused'})
                continue
            owned=claim_due_run(db,clock(),mode='ner_rules_v1',pipeline_version=derived.pipeline_version,run_ids=(run.id,))
            if owned is None or owned.exhausted:
                summary['busy' if owned is None and run.status!='failed' else 'failed']+=1
                summary['runs'].append({'run_id':run.id,'parent_run_id':parent_id,'status':run.status})
                continue
            # Source/model IPC is independently revalidated before trusting any
            # saved raw mention. No model is loaded and old claims are ignored.
            from app.services.news_ner.location_pipeline import from_neural_mentions
            proposal=from_neural_mentions({**source.runtime_request(context.input_fingerprint),
                'mentions':[m.model_dump(mode='json') for m in original.native.neural_mentions]})['proposal']
            if (proposal['effective_mentions'] != [m.model_dump(mode='json') for m in original.native.effective_mentions]
                    or proposal['proposals']!=original.native.proposals or proposal['abstentions']!=original.native.abstentions):
                raise ResolutionError('native_resolution_parent_binding_invalid')
            raw={'proposal':proposal,
                'graph':original.native.graph.model_dump(mode='json',by_alias=True),
                'measurements':original.measurements,'provenance':original.provenance['runtime']}
        error=None;retry=False;output=None;cancelled=False;payload=None;counted=False
        # Resolvers are reused for multiple articles. Never carry usage from a
        # previous article into a failed/timeout summary.
        resolver.last_usage = []; resolver.last_request_count = 0
        try:
            baseline=build_native_result(context,raw,derived,extracted_at=original.extracted_at)
            async with asyncio.timeout(max(.001,end-time.monotonic())):
                payload=await resolver.resolve(source,baseline,parent_run_id=parent_id,parent_result_sha256=parent_hash,client=client)
            summary['request_count']+=getattr(resolver,'last_request_count',len(payload.get('transport',[])))
            counted=True
            prepared=apply_resolution(source,baseline,payload,derived.catalog,resolver.identity)
            if pilot_authorization is not None and pilot_authorization.policy.get('schema_version') in ('gma-inline-continuation-v1','gma-inline-finalize-v1'):
                from app.services.news_gma_inline_continuation import require_three_observations
                require_three_observations(prepared)
            if pilot_authorization is not None and pilot_authorization.policy.get('schema_version')=='gma-heading-repair-v1':
                from app.services.news_gma_heading_repair import require_three_observations
                require_three_observations(prepared)
            if 'placement' in derived.manifest['geography']:
                from .enrichment import enrich_native_result
                prepared=enrich_native_result(context,prepared,derived)
            else:
                prepared.read_projection=build_read_projection(source,prepared,derived.catalog)
            output=verify_saved_result(context,prepared,derived).model_dump(mode='json',by_alias=True)
        except ResolutionError as exc:
            error=exc.code;retry=exc.retryable
            if not counted:
                summary['request_count']+=exc.request_count
        except TimeoutError:
            error='native_resolution_timeout';retry=True
        except (ValueError,TypeError,KeyError,IndexError):
            error='native_resolution_response_invalid'
        except asyncio.CancelledError:
            error='native_resolution_cancelled';retry=True;cancelled=True
        except Exception:
            error='native_resolution_failed'
        # Provider usage and article acceptance are independent. Retain usage
        # even if source validation or final recomputation rejects the result.
        for field in ('input_tokens','output_tokens','thinking_tokens'):
            summary[field]+=sum(r.get(field,0) for r in getattr(resolver,'last_usage',[]))
        if getattr(resolver, 'receipts', None) is not None:
            try:
                resolver.receipts.article({'parent_run_id':parent_id, 'run_id':owned.run_id,
                    'input_sha256':context.input_fingerprint, 'parent_result_sha256':parent_hash}, payload, error)
            except ResolutionError as exc:
                error=exc.code;retry=False;output=None
        with factory() as db,db.begin():
            # Recheck both source selection and parent identity at commit time.
            try:
                if pilot_authorization is not None:
                    pilot_authorization.validate_session(db, run_ids, sources, operation='resolve')
                current,*_=_parent(db,parent_id,selected_news_sources(db,sources),lock=True)
                if sha(current.result)!=parent_hash or (not read_configuration(db).news_processing_enabled and pilot_authorization is None):
                    error='native_resolution_source_changed';retry=False;output=None
            except ResolutionError as exc:
                error=exc.code;retry=False;output=None
            saved=finish_owned_run(db,owned,clock(),result=output,error_code=error,retryable=retry)
        if error and pilot_authorization is not None:
            resolver.budget.stop(error)
        status='lease_lost' if not saved else 'retry_wait' if error and retry and owned.attempt_count<5 else 'failed' if error else 'completed'
        summary[status if status in summary else 'failed']+=1
        summary['runs'].append({'run_id':owned.run_id,'parent_run_id':parent_id,'status':status,'error_code':error})
        if cancelled:
            raise asyncio.CancelledError()
        if error:
            break  # Paid/failed attempts are never silently repeated here.
    return summary
