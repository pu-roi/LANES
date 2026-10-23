"""Exact GMA-only review stage: old-parent adoption, frozen batches, archive only."""
from __future__ import annotations

import base64
from copy import deepcopy
from datetime import datetime, timezone
import json

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimEvaluation
from app.services.news_gemini_receipts import validate_batch, replay_bundle
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError

PARENT_RESULT = '93de1cc2436171660376ee466b0fd9f37b413d80582a8f8a9d37d83957c4fe54'
PARENT_PIPELINE = 'ner-v1:41ecf61ec4bd78e73098e68b3cc7911439ad7d5bf6e3205f500c63affffe1aaa'
INPUT_PIN = '3940f740acabf6cb4f88900bb845b97973a0412b09a4bf9b7beea682b180ba4f'
CACHE_PIN = 'e8b539af345e16930d541dbea1791ddd7ff6a71f4ca63821bc2eeb54ba06cf4b'
REQUESTS = (
    ('02f4b9b633a06363912fa0f47262377de92e7cb083dcc00011ce76a6cf1ddd8a', 42_097_400),
    ('566111dde6fafd17a800ca3b0104265c4b8a049cb66a45768da40a3bd0fc23fe', 42_523_400),
    ('b7a992c2106b7ddcf37b8fd5586bf45f73fc4df076afc9415d4674ba916c9fdc', 42_555_800),
    ('b4e32de84fe59373f3597fc08fd3a19d72689d06e1f3bb785163568db38d51b7', 42_574_400),
    ('a39b15d8bc6a4dc31caee13f0e909920ecf4a2597878e61bc571a5d3fbecfd2e', 42_563_600),
    ('e363949551475c52252ce4c4babfb6cd1e63290bb766942d81b40353dfd4ff9f', 42_551_600),
    ('218c3d06ef126489e31fc5fbece3a96d75b4361410120d26191cdcbbd5017696', 42_440_600),
)


def batch_manifest() -> dict:
    return {'schema_version':'gma-review-batches-v1', 'parent_run_id':375,
        'parent_result_sha256':PARENT_RESULT, 'input_sha256':INPUT_PIN, 'cached_bundle_sha256':CACHE_PIN,
        'sizes':[4,8,8,8,8,8,7],
        'requests':[{'request_sha256':pin,'reservation_nanodollars':cost} for pin,cost in REQUESTS]}


class GmaBatchPlan:
    def __init__(self, manifest: dict, *, cache_loader: object = None) -> None:
        if manifest != batch_manifest():
            raise ResolutionError('gma_batch_manifest_changed')
        self.manifest = deepcopy(manifest)
        self.cache_loader = cache_loader

    @property
    def identity(self) -> str:
        if self.manifest != batch_manifest():
            raise ResolutionError('gma_batch_manifest_changed')
        return sha(self.manifest)

    def batches(self, candidates: list[dict]) -> list[list[dict]]:
        if len(candidates)!=51 or [c['id'] for c in candidates]!=['n'+str(i) for i in range(51)]:
            raise ResolutionError('gma_target_inventory_changed')
        output=[];start=0
        for size in self.manifest['sizes']:
            output.append(candidates[start:start+size]);start+=size
        return output

    def adopt(self, index: int, payload: dict, context: dict, config: object, journal: object) -> tuple | None:
        expected=self.manifest['requests'][index]
        size=len(json.dumps(payload,ensure_ascii=False,allow_nan=False).encode())
        if (sha(payload)!=expected['request_sha256']
                or (2*size+16384)*300+8192*2500!=expected['reservation_nanodollars']
                or any(context.get(k)!=self.manifest[k] for k in ('parent_run_id','parent_result_sha256','input_sha256'))):
            raise ResolutionError('gma_frozen_request_changed')
        if index:
            return None
        if self.cache_loader is None or journal is None:
            raise ResolutionError('gma_cached_evidence_required')
        bundle=self.cache_loader()
        replay=replay_bundle(bundle,CACHE_PIN,config=config)
        intent=bundle['intent']
        if (replay['status']!='evidence_references_passed' or intent['payload']!=payload
                or any(intent['context'].get(k)!=v for k,v in context.items())):
            raise ResolutionError('gma_cached_evidence_changed')
        key=sha({'request_sha256':sha(payload),'context':context})
        journal.store.put(key+'/adoption.json',{'schema_version':'gma-batch-adoption-v1',
            'source_bundle_sha256':CACHE_PIN,'source_request_identity':intent['request_identity'],
            'source_reservation_id':intent['budget_reservation_id'],'parent_run_id':375,
            'new_provider_requests':0,'new_reservations':0,'article_acceptance':'not_evaluated'})
        return validate_batch(payload,base64.b64decode(bundle['response']['body_base64']),config)


def validate_authority(authority: object, engine: object) -> None:
    from app.services.news_three_article_pilot import PilotAuthority
    p=authority.policy
    if (p.get('schema_version')!='news-gma-review-v1' or sha(p)!=authority.policy_sha256
            or p.get('allowed_operations') not in (['resolve'],['archive'])
            or p.get('allowed_article_ids')!=[47] or p.get('allowed_parent_run_ids')!=[375]
            or p.get('parent_pipeline_version')!=PARENT_PIPELINE
            or p.get('parent_result_sha256')!=PARENT_RESULT or p.get('parent_version_id')!=574
            or p.get('cache_bundle_sha256')!=CACHE_PIN or p.get('batch_manifest')!=batch_manifest()
            or p.get('resolver',{}).get('batch_plan_sha256')!=sha(batch_manifest())
            or p.get('resolver',{}).get('batch_size')!=8 or p.get('budget_limit_nanodollars')!=1_000_000_000):
        raise ResolutionError('gma_review_authority_invalid')
    # Reuse all ordinary exact database/application/assets/input guards; only
    # this reviewed old parent and archive operation differ from V1.
    compatible={**p,'schema_version':'news-three-article-pilot-v1',
        'allowed_operations':['resolve'] if p['allowed_operations']==['resolve'] else ['outputs']}
    PilotAuthority(compatible,sha(compatible),authority.trusted).validate(engine)


def validate_session(authority: object, db: Session, run_ids: tuple | None, sources: tuple | None, operation: str) -> None:
    from app.services.news_three_article_pilot import PilotAuthority
    authority.validate(db.get_bind());p=authority.policy
    if p['allowed_operations']!=[operation] or operation not in ('resolve','archive'):
        raise ResolutionError('gma_operation_not_authorized')
    compatible={**p,'schema_version':'news-three-article-pilot-v1','allowed_operations':['resolve']}
    PilotAuthority(compatible,sha(compatible),authority.trusted).validate_session(db,None,sources,operation='resolve')
    raw=db.get(NewsExtractionRun,375);version=db.get(NewsArticleVersion,574);failed=db.get(NewsExtractionRun,376)
    if (raw is None or version is None or failed is None or raw.status!='completed'
            or raw.pipeline_version!=PARENT_PIPELINE or raw.article_version_id!=574
            or sha(raw.result)!=PARENT_RESULT or version.input_fingerprint!=INPUT_PIN or version.article_id!=47
            or failed.status!='failed' or failed.result is not None):
        raise ResolutionError('gma_original_parent_changed')
    old=raw.result['provenance']['manifest']
    current=authority.trusted.manifest
    if any(old[k]!=current[k] for k in ('model','tokenizer','runtime','geography','location_rules','context_rules')):
        raise ResolutionError('gma_parent_assets_changed')
    if run_ids is not None:
        if len(run_ids)!=1:
            raise ResolutionError('gma_one_run_required')
        selected=db.get(NewsExtractionRun,run_ids[0])
        expected=PARENT_PIPELINE if operation=='resolve' else p['resolved_pipeline_version']
        if selected is None or selected.article_version_id!=574 or selected.pipeline_version!=expected:
            raise ResolutionError('gma_run_selection_changed')
        if operation=='resolve' and run_ids!=(375,):
            raise ResolutionError('gma_run_selection_changed')


def archive_outputs(engine: object, authority: object, run_id: int, *, sources: tuple,
                    apply: bool=False, placement_service: object=None) -> dict:
    from app.services.news_pilot_outputs import _qualify
    from app.services.news_historical_outputs import _materialize,_source
    from app.services.news_historical_interpretation import historical_placement_claim
    from app.services.news_history_protection import protected_fingerprints,verify_protected
    from app.crud.news_historical_processing import readonly_historical_session
    if not apply:
        with readonly_historical_session(engine,engine.url.database) as db:
            outputs,*_=_qualify(db,authority,run_id,sources,placement_service,operation='archive')
            return {'status':'preview','outputs':outputs,'outputs_sha256':sha(outputs),'database_writes':0}
    with Session(engine) as db,db.begin():
        db.execute(text("SET LOCAL lock_timeout='30000'"))
        db.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':int(sha('three-article-pilot')[:15],16)})
        before=protected_fingerprints(db)
        outputs,package,derived,run,version,result=_qualify(db,authority,run_id,sources,placement_service,operation='archive')
        if sha(outputs)!=authority.policy.get('outputs_sha256') or any(o['disposition'] not in (None,'historical_archive') for o in outputs):
            raise ResolutionError('gma_archive_preview_changed')
        now=datetime.now(timezone.utc);persisted=[]
        for output in outputs:
            if output['claim_index'] is None:
                persisted.append(output);continue
            claim,_=historical_placement_claim(result,output['group_id'])
            source=_source(db,run,output['claim_index'],result.claims[output['claim_index']],now)
            fingerprint=sha({'schema':'gma-review-archive-v1','session':authority.policy['session_id'],
                'run_id':run.id,'group_id':output['group_id'],'result':sha(run.result)})
            previous=db.scalar(select(NewsClaimEvaluation).where(NewsClaimEvaluation.claim_source_id==source.id,
                NewsClaimEvaluation.policy_fingerprint==fingerprint))
            if previous is not None:
                if previous.status!='completed':raise ResolutionError('gma_archive_state_conflict')
                persisted.append({**previous.result,'repeat':True});continue
            if output['outcome']=='geometry_qualified':
                output=_materialize(db,package,derived,deepcopy(output),run,version,claim,now)
            db.add(NewsClaimEvaluation(claim_source_id=source.id,policy_fingerprint=fingerprint,status='completed',
                attempt_count=0,result=output,created_at=now,updated_at=now,completed_at=now))
            persisted.append(output)
        db.flush();verify_protected(before,protected_fingerprints(db))
        return {'status':'completed','outputs':persisted,'active_instances_created':0,'database_writes':True}
