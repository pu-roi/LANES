"""Version-level correction review even when no compatibility claims exist."""
from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select

from app.crud.news_evaluation import canonical_sha256
from app.crud.news_publication import (append_decision, reserve_decision_id, publication_lock,
    lock_case, latest_decision, existing_request)
from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimSource, NewsClaimZoneLink
from app.schemas.news_publication import NewsDecisionSnapshot, NativeReconciliationReference
from .collection import require_native_storage


def reconcile_native_article(db, run_id: int, *, now, policy) -> int:
    require_native_storage(db)
    run=db.get(NewsExtractionRun,run_id)
    if (run is None or run.mode!='ner_rules_v1' or run.pipeline_version!=policy.pipeline_version
            or run.status not in ('completed','failed','retry_wait')):
        return 0
    version=db.get(NewsArticleVersion,run.article_version_id)
    result=None
    if run.status=='completed':
        from .adapter import verify_saved_result
        from .contracts import RunEvidence
        result=verify_saved_result(RunEvidence.from_records(run,version),run.result,policy.native_assets)
    candidates=list(db.scalars(select(NewsClaimDecision.case_id).join(NewsClaimCase,
        NewsClaimCase.id==NewsClaimDecision.case_id).where(NewsClaimDecision.revision==NewsClaimCase.revision,
        NewsClaimDecision.snapshot['article_id'].as_integer()==version.article_id,
        NewsClaimDecision.public_state.in_(('active_alert','active_zone','expired'))).order_by(NewsClaimDecision.case_id)))
    created=0
    for case_id in candidates:
        request_id=uuid5(NAMESPACE_URL,f'lanes-native-reconciliation:{case_id}:{run_id}:{policy.fingerprint}')
        digest=canonical_sha256({'case_id':case_id,'run_id':run_id,'policy':policy.fingerprint})
        publication_lock(db,digest)
        if existing_request(db,request_id,digest) is not None:continue
        case=lock_case(db,case_id);previous=latest_decision(db,case_id)
        if previous is None or previous.actor_kind=='staff':continue
        saved=NewsDecisionSnapshot.model_validate(previous.snapshot)
        source=db.get(NewsClaimSource,saved.claim_source_id)
        old_run=db.get(NewsExtractionRun,source.extraction_run_id)
        old_version=db.get(NewsArticleVersion,old_run.article_version_id)
        if old_version.id>=version.id or old_version.input_fingerprint==version.input_fingerprint:continue
        disposition='processing_failed' if result is None else (
            result.projection['disposition'] if not result.claims else 'changed_observation')
        # Version references retain the full graph without a fake claim/source
        # row or an unbounded copy of all groups in a publication snapshot.
        reference=NativeReconciliationReference(run_id=run_id,article_version_id=version.id,
            input_sha256=version.input_fingerprint,disposition=disposition)
        decision_id=reserve_decision_id(db)
        public=saved.public.model_copy(update={'decision_id':decision_id,'revision':case.revision+1}) if saved.public else None
        snapshot=saved.model_copy(update={'request_sha256':digest,'previous_decision_id':previous.id,
            'native_reconciliation':reference,'public':public})
        decision=append_decision(db,case,request_id=request_id,decision_id=decision_id,actor_kind='maintenance',
            actor_user_id=None,operation='defer',public_state=previous.public_state,review_state='needs_review',
            reason_code='newer_article_evidence_requires_review',snapshot=snapshot,
            observed_at=previous.observed_at,expires_at=previous.expires_at,now=now)
        for zone_id in saved.linked_zone_ids:
            db.add(NewsClaimZoneLink(decision_id=decision.id,zone_id=zone_id,relation='supported'))
        created+=1
    return created


def pending_reconciliation_runs(db, pipeline_version: str, limit: int) -> list[int]:
    from sqlalchemy.orm import aliased
    from .collection import require_native_storage
    from app.crud.news_browsing import latest_article_runs
    require_native_storage(db)
    latest=latest_article_runs('ner_rules_v1',pipeline_version)
    older_run=aliased(NewsExtractionRun);older_version=aliased(NewsArticleVersion)
    query=select(NewsExtractionRun.id).join(NewsArticleVersion).join(latest,latest.c.run_id==NewsExtractionRun.id).join(
        NewsClaimDecision,NewsClaimDecision.snapshot['article_id'].as_integer()==NewsArticleVersion.article_id).join(
        NewsClaimCase,NewsClaimCase.id==NewsClaimDecision.case_id).join(
        NewsClaimSource,NewsClaimSource.id==NewsClaimDecision.snapshot['claim_source_id'].as_integer()).join(
        older_run,older_run.id==NewsClaimSource.extraction_run_id).join(older_version,older_version.id==older_run.article_version_id).where(
        NewsExtractionRun.status.in_(('completed','failed','retry_wait')),
        NewsClaimDecision.revision==NewsClaimCase.revision,NewsClaimDecision.actor_kind!='staff',
        NewsClaimDecision.public_state.in_(('active_alert','active_zone','expired')),
        older_version.id<NewsArticleVersion.id,older_version.input_fingerprint!=NewsArticleVersion.input_fingerprint,
        NewsClaimDecision.snapshot['native_reconciliation']['run_id'].as_integer().is_distinct_from(NewsExtractionRun.id))
    return list(db.scalars(query.distinct().order_by(NewsExtractionRun.id).limit(limit)))
