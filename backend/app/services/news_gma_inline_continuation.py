"""Pinned adoption of two paid v3 batches plus exactly one v4 request."""
from __future__ import annotations

import base64
from copy import deepcopy
import json

from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_gemini_receipts import replay_bundle,validate_batch
from app.services.news_gma_heading_repair import (PARENT_INPUT,PARENT_MANIFEST,PARENT_RELEASE,PARENT_RESULT,
    delegate)
from app.services.news_source_repair import BODY

VERSION='gma-inline-continuation-v1'
SESSION='gma-inline-20261023-v4'
FINAL_VERSION='gma-inline-finalize-v1'
FINAL_SESSION='gma-inline-finalize-20261023-v1'
FINAL_CACHE_PIN='8e8e0a77ef978c933ba8c02ef5ba01e8e3ad1f61e74d6815627ca8b89b563b79'
CACHE_PINS=(
    '7c60fd5bebbdb8b053d3f18321793bdbf737db951738d4ff5c57070dc5f0b373',
    '96f47762f1f9e5bceaf27b3d46cbac75c1ae7ac58dd04b33153ae9756bce06ae')


def batch_manifest() -> dict:
    return {'schema_version':VERSION,'targets':['n'+str(i) for i in range(11)],
        'required_targets':['n6','n8','n10'],'batch_sizes':[4,4,3],'adopted_bundle_sha256s':list(CACHE_PINS)}


def final_manifest(last_bundle_sha256: str) -> dict:
    if last_bundle_sha256!=FINAL_CACHE_PIN:raise ResolutionError('inline_final_bundle_pin_invalid')
    return {**batch_manifest(),'schema_version':FINAL_VERSION,
        'adopted_bundle_sha256s':[*CACHE_PINS,last_bundle_sha256],'generation_requests_allowed':0}


class InlineBatchPlan:
    required_targets=('n6','n8','n10')

    def __init__(self, manifest: dict, *, cache_loader: object=None) -> None:
        final=manifest.get('schema_version')==FINAL_VERSION
        expected=final_manifest(manifest['adopted_bundle_sha256s'][2]) if final else batch_manifest()
        if manifest!=expected:raise ResolutionError('inline_batch_manifest_changed')
        self.manifest=deepcopy(manifest);self.cache_loader=cache_loader

    @property
    def identity(self) -> str:
        expected=(final_manifest(self.manifest['adopted_bundle_sha256s'][2])
            if self.manifest.get('schema_version')==FINAL_VERSION else batch_manifest())
        if self.manifest!=expected:raise ResolutionError('inline_batch_manifest_changed')
        return sha(self.manifest)

    def batches(self,candidates: list[dict]) -> list[list[dict]]:
        self.identity
        if [m['id'] for m in candidates]!=self.manifest['targets']:raise ResolutionError('inline_target_inventory_changed')
        return [candidates[:4],candidates[4:8],candidates[8:]]

    def adopt(self,index: int,payload: dict,context: dict,config: object,journal: object) -> tuple | None:
        self.identity
        final=self.manifest.get('schema_version')==FINAL_VERSION
        if index==2 and not final:return None
        if index not in (0,1,2) or self.cache_loader is None or journal is None:
            raise ResolutionError('inline_adoption_evidence_required')
        bundle=self.cache_loader(index)
        pin=self.manifest['adopted_bundle_sha256s'][index]
        if replay_bundle(bundle,pin,config=config)['status']!='evidence_references_passed':
            raise ResolutionError('inline_cached_response_rejected')
        intent=bundle['intent'];old=intent['payload']
        previous=json.loads(old['contents'][0]['parts'][0]['text']);current=json.loads(payload['contents'][0]['parts'][0]['text'])
        from app.services.news_ner_durable import scoped_resolution_v3 as v3,scoped_resolution_v4 as v4
        from app.services.news_ner_durable.gemini_resolution import INSTRUCTIONS
        old_policy=v3 if index<2 else v4
        if (intent['context']!=context or intent['model']!=config.model
                or old['systemInstruction']!={'parts':[{'text':INSTRUCTIONS+old_policy.INSTRUCTIONS}]}
                or payload['systemInstruction']!={'parts':[{'text':INSTRUCTIONS+v4.INSTRUCTIONS}]}
                or old['generationConfig']!=payload['generationConfig']
                or previous['evidence_contract']!=old_policy.CONTRACT or current['evidence_contract']!=v4.CONTRACT):
            raise ResolutionError('inline_cached_contract_changed')
        for key in ('article','evidence_text','native_facts','native_groups','quote_options','targets'):
            if previous[key]!=current[key]:raise ResolutionError('inline_cached_source_or_targets_changed')
        stripped=deepcopy(current['source_layout']);stripped['schema_version']=old_policy.CONTRACT
        if index<2:
            for target in stripped['targets']:target.pop('inline_locality_owner',None)
        if stripped!=previous['source_layout']:raise ResolutionError('inline_cached_layout_changed')
        key=sha({'request_sha256':sha(payload),'context':context})
        journal.store.put(key+'/adoption.json',{'schema_version':self.manifest['schema_version'],'original_bundle_sha256':pin,
            'original_request_sha256':intent['request_sha256'],'original_contract':old_policy.CONTRACT,
            'new_contract':v4.CONTRACT,'new_request_sha256':sha(payload),'context':context,
            'original_rows_unchanged':True,'new_provider_requests':0,'new_reservations':0})
        return validate_batch(old,base64.b64decode(bundle['response']['body_base64']),config)


def validate_authority(authority: object,engine: object) -> None:
    p=authority.policy
    final=p.get('schema_version')==FINAL_VERSION
    expected=final_manifest(p['batch_manifest']['adopted_bundle_sha256s'][2]) if final else batch_manifest()
    if (sha(p)!=authority.policy_sha256 or p.get('schema_version') not in (VERSION,FINAL_VERSION)
            or p.get('session_id')!=(FINAL_SESSION if final else SESSION)
            or p.get('allowed_operations') not in (['count'],['resolve']) or p.get('allowed_article_ids')!=[47]
            or p.get('native_version_id')!=569 or p.get('source_version_id')!=140 or p.get('parent_run_id')!=382
            or p.get('source_body_sha256')!=BODY or p.get('parent_result_sha256')!=PARENT_RESULT
            or p.get('parent_manifest_sha256')!=PARENT_MANIFEST or p.get('parent_input_sha256')!=PARENT_INPUT
            or p.get('parent_pipeline_version')!='ner-v1:'+PARENT_MANIFEST
            or p.get('resolver',{}).get('evidence_contract')!='scoped-quote-options-v4'
            or p.get('batch_manifest')!=expected or p.get('resolver',{}).get('batch_plan_sha256')!=sha(expected)
            or (final and (p.get('generation_requests_allowed')!=0 or p['allowed_operations']!=['resolve']))
            or p.get('active_output_allowed') is not False):
        raise ResolutionError('inline_authority_invalid')
    delegate(authority).validate(engine)


def validate_session(authority: object,db: object,run_ids: tuple | None,sources: tuple | None,operation: str) -> None:
    from app.models.news import NewsExtractionRun,NewsArticleVersion
    authority.validate(db.get_bind());p=authority.policy
    if run_ids!=(382,) or p['allowed_operations']!=[operation]:raise ResolutionError('inline_operation_changed')
    delegate(authority).validate_session(db,None,sources,operation='resolve')
    parent=db.get(NewsExtractionRun,382);version=db.get(NewsArticleVersion,569)
    if (parent is None or version is None or parent.status!='completed' or parent.mode!='ner_rules_v1'
            or parent.article_version_id!=569 or version.article_id!=47 or version.input_fingerprint!=PARENT_INPUT
            or parent.pipeline_version!='ner-v1:'+PARENT_MANIFEST or sha(parent.result)!=PARENT_RESULT):
        raise ResolutionError('inline_parent_changed')
    old=parent.result['provenance']['manifest']
    if sha(old)!=PARENT_MANIFEST or any(old[k]!=authority.trusted.manifest[k] for k in
            ('model','tokenizer','runtime','geography','location_rules','context_rules')):
        raise ResolutionError('inline_parent_assets_changed')
    expected={'status':'verified','result_sha256':PARENT_RESULT,'manifest_sha256':PARENT_MANIFEST,
        'frozen_release_sha256':PARENT_RELEASE,'source_version_id':569,'parent_run_id':382,
        'pipeline_version':'ner-v1:'+PARENT_MANIFEST,'input_sha256':PARENT_INPUT}
    if p.get('verified_parent')!=expected:raise ResolutionError('inline_parent_proof_changed')


def require_three_observations(result: object) -> None:
    projected=[g for g in result.projection['groups'] if g['claim_index'] is not None]
    if len(result.claims)!=3 or {tuple(g['target_entity_ids']) for g in projected}!={('n6',),('n8',),('n10',)}:
        raise ResolutionError('inline_three_observations_required')
    for group in projected:
        target=group['target_entity_ids'][0];claim=result.claims[group['claim_index']]
        if (claim.canonical_city!=('City of Marikina' if target=='n10' else 'City of Malabon')
                or claim.depth_canonical!='gutter' or claim.depth_raw.casefold()!='gutter deep'
                or claim.depth_inches is not None or claim.depth_meters is not None
                or claim.event_time_resolved is None or claim.event_time_resolved.isoformat()!='2026-09-09T14:47:00+08:00'
                or claim.road_passability!='passable_all' or claim.condition!='active'):
            raise ResolutionError('inline_expected_source_facts_missing')
        if target=='n8' and (claim.road_segment_raw!='Tañong F. Sevilla Blvd. (Bayan)'
                or claim.canonical_barangay not in (None,'Tañong')):
            raise ResolutionError('inline_reported_tanong_section_missing')
    if next(m for m in result.native.graph.mentions if m.id=='n10').label!='LANDMARK':
        raise ResolutionError('inline_original_label_changed')
    road=next(c for c in result.claims if c.canonical_road=='Rizal Ave Extn')
    if road.canonical_barangay!='San Agustin':raise ResolutionError('inline_san_agustin_missing')
    contexts=[g for g in result.projection['groups'] if g['claim_index'] is None]
    if (len(contexts)!=1 or contexts[0]['target_entity_ids']!=['n7'] or contexts[0]['disposition']!='context_only'
            or contexts[0]['normalizations'].get('inline_locality_owner',{}).get('target_id')!='n6'):
        raise ResolutionError('inline_context_classification_missing')
