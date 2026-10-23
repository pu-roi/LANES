"""Owned native source-consistency evaluation; no legacy recognizer or provider IO."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import json

from sqlalchemy import select, exists, func, case

from app.crud.news_browsing import latest_article_runs
from app.crud.news_evaluation import (bind_completed_run, claim_due_batch, start_owned_attempt,
                                     finish_owned_evaluation, validate_run, canonical_sha256)
from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimSource, NewsClaimEvaluation
from app.services.configuration_service import read_configuration, selected_news_sources
from app.services.news_evaluation_service import (EvaluationPolicy, EvaluationSummary, publication_is_current,
    source_is_approved, _completed_result)
from .assets import TrustedAssets
from .contracts import NerEvidenceError, SOURCE_VERSION
from .source_check import source_policy_fingerprint, check_native_sources
from .collection import require_native_storage


def native_evaluation_policy(trusted: TrustedAssets, configuration) -> EvaluationPolicy:
    identity={'provider':'source_rules','model':'ner-source-consistency-v1','prompt_version':SOURCE_VERSION,
              'response_version':'source-evidence-v2','processing_method':'ner_rules_v1'}
    if trusted.manifest['projection'].get('llm_resolution') is not None:
        identity = {**trusted.manifest['projection']['llm_resolution'],'processing_method':'ner_rules_v1'}
    base=canonical_sha256({'expiry_minutes':configuration.evidence_expiry_minutes,
        'retention_hours':configuration.news_unconfirmed_retention_hours,'identity':identity})
    from types import SimpleNamespace
    fingerprint=source_policy_fingerprint(trusted,publication_policy=SimpleNamespace(fingerprint=base))
    return EvaluationPolicy(fingerprint,trusted.pipeline_version,identity,configuration.evidence_expiry_minutes,
                            configuration.news_unconfirmed_retention_hours,native_assets=trusted)


def seed_native_evaluations(factory, policy: EvaluationPolicy, *, now: datetime, sources: tuple, limit: int=50) -> EvaluationSummary:
    summary=EvaluationSummary()
    trusted=policy.native_assets
    if trusted is None:raise NerEvidenceError('ner_configuration_invalid')
    with factory() as db:
        require_native_storage(db)
        latest=latest_article_runs('ner_rules_v1',policy.pipeline_version)
        bound=exists(select(NewsClaimEvaluation.id).join(NewsClaimSource).where(
            NewsClaimSource.extraction_run_id==NewsExtractionRun.id,
            NewsClaimEvaluation.policy_fingerprint==policy.fingerprint))
        claims=NewsExtractionRun.result['claims']
        nonempty=case((func.jsonb_typeof(claims)=='array',func.jsonb_array_length(claims)),else_=0)>0
        ids=list(db.scalars(select(NewsExtractionRun.id).join(latest,latest.c.run_id==NewsExtractionRun.id).where(
            NewsExtractionRun.status=='completed',nonempty,~bound).order_by(NewsExtractionRun.id).limit(limit)))
    for run_id in ids:
        with factory() as db,db.begin():
            require_native_storage(db)
            if not read_configuration(db).news_processing_enabled:break
            selected=selected_news_sources(db,sources)
            run=db.get(NewsExtractionRun,run_id);version=db.get(NewsArticleVersion,run.article_version_id)
            try:
                article,result=validate_run(run,version,trusted=trusted)
            except NerEvidenceError as exc:
                if exc.code in ('ner_assets_unavailable','ner_configuration_invalid'):
                    summary.error_code=exc.code;break
                summary.skipped.append({'run_id':run_id,'reason_code':exc.code});continue
            except (ValueError,TypeError,KeyError):
                summary.skipped.append({'run_id':run_id,'reason_code':'invalid_immutable_extraction'});continue
            if not result.claims:continue
            if not source_is_approved(article,selected) or not publication_is_current(article,now,policy):
                summary.skipped.append({'run_id':run_id,'reason_code':'native_source_not_current_or_selected'});continue
            a,b=bind_completed_run(db,run_id,policy.fingerprint,now,trusted=trusted)
            summary.sources_created+=a;summary.evaluations_created+=b
    return summary


def evaluate_native_claims(factory, policy: EvaluationPolicy, *, clock, sources: tuple, limit: int=50) -> EvaluationSummary:
    summary=EvaluationSummary();visited=[]
    if policy.native_assets is None:raise NerEvidenceError('ner_configuration_invalid')
    while len(visited)<limit:
        now=clock()
        with factory() as db,db.begin():
            require_native_storage(db)
            if not read_configuration(db).news_processing_enabled:break
            selected=selected_news_sources(db,sources)
            if not selected:break
            owned=claim_due_batch(db,now,policy_fingerprint=policy.fingerprint,limit=8,
                max_rows=min(200,limit-len(visited)),exclude_evaluation_ids=tuple(visited),
                source_ids=tuple(s.id for s in selected))
        if not owned:break
        visited.extend(o.evaluation_id for o in owned)
        active=[];errors={};audits={};article=None;result=None
        with factory() as db,db.begin():
            for item in owned:
                if item.exhausted:
                    summary.failed+=1;continue
                started=start_owned_attempt(db,item,clock())
                if started is None:summary.lease_lost+=1
                else:active.append(started)
        if not active:continue
        try:
            with factory() as db:
                run=db.get(NewsExtractionRun,active[0].run_id);version=db.get(NewsArticleVersion,run.article_version_id)
                article,result=validate_run(run,version,trusted=policy.native_assets)
                if (run.pipeline_version!=policy.pipeline_version or not source_is_approved(article,selected)
                        or not publication_is_current(article,clock(),policy)):
                    raise NerEvidenceError('ner_configuration_invalid')
                audits=check_native_sources(run,version,run.result,[o.claim_ordinal for o in active],
                    policy.native_assets,now=clock(),publication_policy=policy)
        except NerEvidenceError as exc:
            errors={o.evaluation_id:exc.code for o in active}
        except (ValueError,TypeError,KeyError,IndexError):
            errors={o.evaluation_id:'native_source_evidence_invalid' for o in active}
        for item in active:
            error=errors.get(item.evaluation_id)
            audit=audits.get(item.claim_ordinal)
            if audit and (audit.input_sha256!=item.input_fingerprint or audit.claim_sha256!=item.claim_sha256):
                error='audit_evidence_mismatch'
            payload=None if error else _completed_result(item,policy,audit.reason_code,audit,
                result.claims[item.claim_ordinal],article,clock())
            if payload is not None and len(json.dumps(payload,ensure_ascii=False,allow_nan=False).encode('utf-8'))>65536:
                payload=None;error='evaluation_result_oversized'
            with factory() as db,db.begin():
                saved=finish_owned_evaluation(db,item,clock(),result=payload,error_code=error,retryable=False)
            state='lease_lost' if not saved else 'failed' if error else 'completed'
            setattr(summary,state,getattr(summary,state)+1)
            summary.evaluations.append({'evaluation_id':item.evaluation_id,'case_id':item.case_id,'status':state,'error_code':error})
    return summary
