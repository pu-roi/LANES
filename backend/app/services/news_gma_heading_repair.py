"""Exact-source correction authority; no inference, archive or activation rights."""
from __future__ import annotations

from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_source_repair import BODY

VERSION = 'gma-heading-repair-v1'
SESSION = 'gma-heading-20261023-v3'
PARENT_RESULT = 'a7d87c19ebe306c2cbf0dab6100e9c27a9590ddddaee3c01fe36767715df30a5'
PARENT_MANIFEST = 'c94df15a2c730f3e789d369275a8356001d60a03718e67e4cf36949419a47360'
PARENT_INPUT = '72f561ea2f7fbf0fa06147025440d6f68632590716d2f544533a413a6a0ab49f'
PARENT_RELEASE = 'be8acbef57bf43c9ae1139f32cd32eb4c03e9bb176bff134a65cff5e582f35fc'


class HeadingBatchPlan:
    required_targets = ('n6','n8','n10')

    def __init__(self, manifest: dict) -> None:
        self.manifest = manifest
        if manifest != {'schema_version':VERSION,'targets':['n'+str(i) for i in range(11)],
                'required_targets':list(self.required_targets),'batch_sizes':[4,4,3]}:
            raise ResolutionError('heading_batch_manifest_invalid')

    @property
    def identity(self) -> str:
        return sha(self.manifest)

    def batches(self, candidates: list[dict]) -> list[list[dict]]:
        if [m['id'] for m in candidates] != self.manifest['targets']:
            raise ResolutionError('heading_target_inventory_changed')
        return [candidates[:4],candidates[4:8],candidates[8:]]

    def adopt(self, *args: object) -> None:
        return None


def delegate(authority: object) -> object:
    from app.services.news_three_article_pilot import PilotAuthority
    p = {**authority.policy,'schema_version':'news-three-article-pilot-v1','allowed_operations':['resolve']}
    return PilotAuthority(p,sha(p),authority.trusted)


def validate_authority(authority: object, engine: object) -> None:
    p = authority.policy
    if (sha(p)!=authority.policy_sha256 or p.get('schema_version')!=VERSION or p.get('session_id')!=SESSION
            or p.get('allowed_operations') not in (['count'],['resolve']) or p.get('allowed_article_ids')!=[47]
            or p.get('native_version_id')!=569 or p.get('source_version_id')!=140
            or p.get('parent_run_id')!=382 or p.get('source_body_sha256')!=BODY
            or p.get('parent_result_sha256')!=PARENT_RESULT
            or p.get('parent_manifest_sha256')!=PARENT_MANIFEST
            or p.get('parent_pipeline_version')!='ner-v1:'+PARENT_MANIFEST
            or p.get('parent_input_sha256')!=PARENT_INPUT
            or p.get('resolver',{}).get('evidence_contract')!='scoped-quote-options-v3'
            or p.get('resolver',{}).get('batch_plan_sha256')!=HeadingBatchPlan(p['batch_manifest']).identity
            or p.get('active_output_allowed') is not False):
        raise ResolutionError('heading_authority_invalid')
    delegate(authority).validate(engine)


def validate_session(authority: object, db: object, run_ids: tuple | None, sources: tuple | None,
                     operation: str) -> None:
    from app.models.news import NewsExtractionRun,NewsArticleVersion
    authority.validate(db.get_bind());p=authority.policy
    if p['allowed_operations']!=[operation] or run_ids!=(382,):
        raise ResolutionError('heading_operation_or_parent_invalid')
    delegate(authority).validate_session(db,None,sources,operation='resolve')
    parent=db.get(NewsExtractionRun,382);version=db.get(NewsArticleVersion,569)
    if (parent is None or version is None or parent.status!='completed' or parent.mode!='ner_rules_v1'
            or parent.article_version_id!=569 or version.article_id!=47
            or parent.pipeline_version!=p['parent_pipeline_version'] or sha(parent.result)!=p['parent_result_sha256']
            or version.input_fingerprint!=p['parent_input_sha256']
            or sha(parent.result['provenance']['manifest'])!=p['parent_manifest_sha256']):
        raise ResolutionError('heading_frozen_parent_changed')
    old=parent.result['provenance']['manifest'];current=authority.trusted.manifest
    if any(old[k]!=current[k] for k in ('model','tokenizer','runtime','geography','location_rules','context_rules')):
        raise ResolutionError('heading_parent_runtime_or_assets_changed')
    proof=p.get('verified_parent',{})
    if proof!={'status':'verified','result_sha256':PARENT_RESULT,'manifest_sha256':PARENT_MANIFEST,
            'frozen_release_sha256':PARENT_RELEASE,'source_version_id':569,'parent_run_id':382,
            'pipeline_version':'ner-v1:'+PARENT_MANIFEST,'input_sha256':PARENT_INPUT}:
        raise ResolutionError('heading_parent_verification_required')


def require_three_observations(result: object) -> None:
    groups=result.projection['groups']
    if len(result.claims)!=3 or {tuple(g['target_entity_ids']) for g in groups}!={('n6',),('n8',),('n10',)}:
        raise ResolutionError('heading_three_observations_required')
    cities={'n6':'City of Malabon','n8':'City of Malabon','n10':'City of Marikina'}
    for group in groups:
        target=group['target_entity_ids'][0];claim=result.claims[group['claim_index']]
        if (claim.canonical_city!=cities[target] or claim.depth_canonical!='gutter'
                or claim.depth_raw.casefold()!='gutter deep' or claim.depth_inches is not None or claim.depth_meters is not None
                or claim.event_time_resolved is None or claim.event_time_resolved.isoformat()!='2026-09-09T14:47:00+08:00'
                or claim.road_passability!='passable_all' or claim.condition!='active'):
            raise ResolutionError('heading_expected_source_facts_not_accepted')
        if target=='n8' and claim.canonical_barangay!='Tañong':
            raise ResolutionError('heading_tanong_context_missing')
    landmark=next(m for m in result.native.graph.mentions if m.id=='n10')
    if landmark.label!='LANDMARK':
        raise ResolutionError('heading_original_neural_label_changed')
