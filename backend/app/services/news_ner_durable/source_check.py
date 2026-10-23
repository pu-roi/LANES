"""Native source consistency: neither old-recognizer agreement nor field proof."""
from __future__ import annotations

from datetime import datetime
import json
from collections.abc import Sequence

from app.schemas.news_audit import (AuditEvidenceSpan,AuditedAccess,AuditedDepth,AuditedPlace,AuditedStatus,
                                    AuditedTime,IndependentAuditResult,ProviderClaimAudit)
from app.services.news_claim_auditor import canonical_claim_sha256
from app.services.news_evaluation_service import preliminary_reason
from .adapter import verify_saved_result
from .assets import TrustedAssets
from .contracts import NerEvidenceError, RunEvidence, SOURCE_VERSION, sha


def source_policy_fingerprint(trusted: TrustedAssets, *, publication_policy: object | None=None) -> str:
    trusted.validate()
    return sha({'version':SOURCE_VERSION,'manifest':sha(trusted.manifest),'pipeline':trusted.pipeline_version,
                'publication_policy':getattr(publication_policy,'fingerprint',None)})


def check_native_source(run: object, version: object, saved: object, claim_ordinal: int, trusted: TrustedAssets,
                         *, now: datetime, publication_policy: object | None=None) -> IndependentAuditResult:
    return check_native_sources(run,version,saved,(claim_ordinal,),trusted,now=now,
                                publication_policy=publication_policy)[claim_ordinal]


def check_native_sources(run: object, version: object, saved: object, claim_ordinals: Sequence[int], trusted: TrustedAssets,
                          *, now: datetime, publication_policy: object | None=None) -> dict[int,IndependentAuditResult]:
    context=RunEvidence.from_records(run,version)
    if (not isinstance(now,datetime) or now.utcoffset() is None
            or (publication_policy is not None and getattr(publication_policy,'pipeline_version',None)!=context.pipeline_version)):
        raise NerEvidenceError('ner_configuration_invalid')
    if run.status!='completed' or run.completed_at is None:
        raise NerEvidenceError('ner_result_contract_invalid')
    result=verify_saved_result(context,saved,trusted)
    if hasattr(run,'result') and run.result is not None and sha(run.result)!=sha(result.model_dump(mode='json',by_alias=True)):
        raise NerEvidenceError('ner_result_contract_invalid')
    if (any(type(i) is not int or not 0<=i<len(result.claims) for i in claim_ordinals)
            or len(set(claim_ordinals))!=len(claim_ordinals)):
        raise NerEvidenceError('ner_result_contract_invalid')
    if 'llm_resolution' in result.provenance:
        from .resolution import resolution_audit
        return {i:resolution_audit(context,result,i) for i in claim_ordinals}
    return {i:_check_verified(context,result,i,now,publication_policy) for i in claim_ordinals}


def _check_verified(context: RunEvidence, result: object, claim_ordinal: int, now: datetime,
                     publication_policy: object | None) -> IndependentAuditResult:
    if type(claim_ordinal) is not int or not 0<=claim_ordinal<len(result.claims):
        raise NerEvidenceError('ner_result_contract_invalid')
    claim=result.claims[claim_ordinal]
    group=next(g for g in result.projection['groups'] if g['claim_index']==claim_ordinal)
    norm=group['normalizations'];text=context.source().article_text

    def spans(values: list[dict]) -> tuple[AuditEvidenceSpan,...]:
        unique={(e['start'],e['end'],e['text']) for e in values}
        try:
            if len(unique)>12:raise ValueError('too_many_spans')
            for a,b,t in unique:
                if not 0<=a<b<=len(text) or text[a:b]!=t:raise ValueError('source_slice_mismatch')
            return tuple(AuditEvidenceSpan(start=a,end=b,quote=t) for a,b,t in sorted(unique))
        except (ValueError,TypeError) as exc:raise NerEvidenceError('ner_result_contract_invalid') from exc

    observed=claim.event_time_kind=='observation' and claim.event_time_resolved is not None
    depth=claim.depth_raw is not None
    depth_facts={f.id:f for f in result.native.graph.facts}
    selected=norm['depth']['selected_fact_id']
    if depth and not norm['depth']['evidence']:
        ds=[e.model_dump(mode='json') for f in result.native.graph.facts if f.id in norm['projected_fact_ids'] and f.kind=='depth' for e in f.evidence]
    else:ds=norm['depth']['evidence']
    audit=ProviderClaimAudit(claim_sha256=canonical_claim_sha256(claim),
        place=AuditedPlace(confirmed=True,evidence=spans(norm['locality']['evidence']),raw_place_name=claim.raw_place_name,
                           canonical_city=claim.canonical_city,canonical_barangay=claim.canonical_barangay),
        status=AuditedStatus(confirmed=True,evidence=spans(norm['status_evidence']),classification=claim.condition,
                            contradictory=False,historical=False),
        time=AuditedTime(confirmed=observed,evidence=spans(norm['time']['evidence']),
                        observed_at=claim.event_time_resolved.isoformat() if observed else None,kind=claim.event_time_kind),
        depth=AuditedDepth(confirmed=depth,evidence=spans(ds),canonical=claim.depth_canonical,raw=claim.depth_raw,
                          qualifiers=tuple(depth_facts[selected].qualifiers) if selected else ()),
        access=AuditedAccess(confirmed=claim.road_passability!='unknown',evidence=spans(norm['access']['evidence']),classification=claim.road_passability))
    reason=preliminary_reason(claim,now,publication_policy)
    response=IndependentAuditResult(outcome='review' if reason else 'verified',reason_code=reason or 'source_ner_consistent',
        provider='source_rules',model='ner-source-consistency-v1',prompt_version=SOURCE_VERSION,response_version='source-evidence-v2',
        input_sha256=context.input_fingerprint,claim_sha256=canonical_claim_sha256(claim),evidence=audit)
    if len(json.dumps(response.model_dump(mode='json'),ensure_ascii=False).encode('utf-8'))>65536:
        response=response.model_copy(update={'outcome':'review','reason_code':'source_ner_evidence_exceeds_audit_limit','evidence':None})
    return response
