"""Versioned, exact GMA continuation with scoped evidence and archive-only writes."""
from __future__ import annotations

import base64
from copy import deepcopy

from app.services.news_gemini_receipts import replay_bundle, validate_batch
from app.services.news_gma_scoped_budget import SESSION, extension_policy, effective_commitment
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_ner_durable.scoped_resolution import CONTRACT
from app.services.news_pilot_accounting import accounting_policy, reservation

VERSION = 'news-gma-scoped-continuation-v1'
CACHE_PIN = 'ccab75b20fefc9f53d206d82f05cbe7fa2ca9fcfe4c8310ce406dd018bf1eead'
REQUESTS = (
    'ac8a4910e6b39549f7f10d40ed672f3c8fa391106df75b2fb6e3d239415a134b',
    'e6df16feca68c66118f30f2e3156fb00edef09fd917a45c19545693a06f2b074',
    '757eaadd88a948e3445565de0baa0175e2be0a76bc5380b42c8416adfb700c4b',
    'af01fd06dab994a4180a018eb6201598b1c23ec72f0c5008dba72eb59461ff26',
    '15a8b1e343dc640b85f3e9ea963015d98517171f2327239c19cba0654931b27f',
    'eca91e3472694f577adbfd39ff37247a8386a21d3c9c545d97d11331201222fd',
    '6f1ca5e5f6bdc88eeccb5c61e3d519c09626df0c156a98bc56736aa8eed44a78',
    'f82aac5af7e0ccb43d0a2df372b3daece1022211c001dbac7a9c2b823facfd77',
    '6d45644437f4f00104e20d502460bd529e9b81662f07166923468da9f3e96d14',
    '9cd179a876bc1d21cd9fcef37d802b857c37ecfe2121b3f02d4e50167f6796f9',
    'f9c0a7e470fcb691d0195ee34469dd9314c29966dae0ba88c33237722b45d386',
    '53bb23fcb5de3327fc0a8282b9b64e3df43edcb1822e770d8faa3229dc9cb387',
    '687562c58312a7c46c437a01efb2cfa751ee1547476e1e0195257b5df72fa94b',
)


def batch_manifest() -> dict:
    from app.services.news_gma_review import PARENT_RESULT, INPUT_PIN
    return {'schema_version':'gma-scoped-batches-v1','parent_run_id':375,
        'parent_result_sha256':PARENT_RESULT,'input_sha256':INPUT_PIN,'sizes':[4]*12+[3],
        'request_sha256s':list(REQUESTS),'cached_batch_index':3,'cached_bundle_sha256':CACHE_PIN,
        'accounting_extension':extension_policy([p for i,p in enumerate(REQUESTS) if i != 3])}


class ScopedGmaBatchPlan:
    def __init__(self, manifest: dict, *, cache_loader: object = None) -> None:
        if manifest != batch_manifest():
            raise ResolutionError('gma_scoped_manifest_changed')
        self.manifest = deepcopy(manifest)
        self.cache_loader = cache_loader

    @property
    def identity(self) -> str:
        if self.manifest != batch_manifest():
            raise ResolutionError('gma_scoped_manifest_changed')
        return sha(self.manifest)

    def batches(self, candidates: list[dict]) -> list[list[dict]]:
        self.identity
        if [c['id'] for c in candidates] != ['n'+str(i) for i in range(51)]:
            raise ResolutionError('gma_target_inventory_changed')
        return [candidates[i:i+4] for i in range(0,51,4)]

    def adopt(self, index: int, payload: dict, context: dict, config: object, journal: object) -> tuple | None:
        self.identity
        if (sha(payload) != REQUESTS[index] or any(context.get(k) != self.manifest[k]
                for k in ('parent_run_id','parent_result_sha256','input_sha256'))):
            raise ResolutionError('gma_frozen_request_changed')
        if index != 3:
            return None
        if self.cache_loader is None or journal is None:
            raise ResolutionError('gma_cached_evidence_required')
        bundle = self.cache_loader()
        if (replay_bundle(bundle,CACHE_PIN,config=config)['status'] != 'evidence_references_passed'
                or bundle['intent']['payload'] != payload or bundle['intent']['context'] != context):
            raise ResolutionError('gma_cached_evidence_changed')
        key = sha({'request_sha256':sha(payload),'context':context})
        journal.store.put(key+'/adoption.json',{'schema_version':'gma-scoped-adoption-v1',
            'source_bundle_sha256':CACHE_PIN,'source_request_identity':bundle['intent']['request_identity'],
            'new_provider_requests':0,'new_reservations':0,'article_acceptance':'not_evaluated'})
        return validate_batch(payload,base64.b64decode(bundle['response']['body_base64']),config)


def validate_authority(authority: object, engine: object) -> None:
    from app.services.news_three_article_pilot import PilotAuthority
    p = authority.policy
    if (sha(p) != authority.policy_sha256 or p.get('schema_version') != VERSION
            or p.get('session_id') != SESSION or p.get('allowed_operations') not in (['count'],['resolve'],['archive'])
            or p.get('allowed_article_ids') != [47] or p.get('allowed_parent_run_ids') != [375]
            or p.get('parent_version_id') != 574 or p.get('batch_manifest') != batch_manifest()
            or p.get('cache_bundle_sha256') != CACHE_PIN or p.get('budget_limit_nanodollars') != 1_000_000_000
            or p.get('resolver',{}).get('batch_plan_sha256') != sha(batch_manifest())
            or p['resolver'].get('evidence_contract') != CONTRACT or p['resolver'].get('batch_size') != 4):
        raise ResolutionError('gma_scoped_authority_invalid')
    from app.services.news_gma_review import PARENT_PIPELINE, PARENT_RESULT, INPUT_PIN
    if (p.get('parent_pipeline_version') != PARENT_PIPELINE or p.get('parent_result_sha256') != PARENT_RESULT
            or p.get('input_sha256') != INPUT_PIN):
        raise ResolutionError('gma_scoped_parent_changed')
    compatible = {**p,'schema_version':'news-three-article-pilot-v1','allowed_operations':['resolve']}
    PilotAuthority(compatible,sha(compatible),authority.trusted).validate(engine)


def validate_session(authority: object, db: object, run_ids: tuple | None, sources: tuple | None,
                     operation: str) -> None:
    from app.services.news_three_article_pilot import PilotAuthority
    from app.services import news_gma_review
    from app.models.news import NewsExtractionRun
    authority.validate(db.get_bind())
    p = authority.policy
    if p['allowed_operations'] != [operation] or operation not in ('count','resolve','archive'):
        raise ResolutionError('gma_operation_not_authorized')
    # Reuse old-parent/source/configuration guards locally; old grants are unchanged.
    compatible = {**p,'schema_version':'news-gma-review-v1',
        'batch_manifest':news_gma_review.batch_manifest(),'cache_bundle_sha256':news_gma_review.CACHE_PIN,
        'resolver':{**p['resolver'],'batch_size':8,'batch_plan_sha256':sha(news_gma_review.batch_manifest())},
        'allowed_operations':['archive' if operation == 'archive' else 'resolve']}
    old = PilotAuthority(compatible,sha(compatible),authority.trusted)
    news_gma_review.validate_session(old,db,run_ids,sources,compatible['allowed_operations'][0])
    for run_id in (378,379):
        failed = db.get(NewsExtractionRun,run_id)
        if failed is None or failed.status != 'failed' or failed.result is not None:
            raise ResolutionError('gma_failed_correction_changed')


def qualify_schedule(packets: list[dict], catalog: dict, state: dict) -> int:
    if ([sha(p['payload']) for p in packets] != list(REQUESTS)
            or catalog.get('schema_version') != 'news-pilot-count-catalog-v2'
            or catalog.get('accounting_policy_sha256') != sha(accounting_policy())
            or [r['request_sha256'] for r in catalog.get('requests',[])] != [p for i,p in enumerate(REQUESTS) if i != 3]):
        raise ResolutionError('gma_scoped_count_schedule_changed')
    total = 0
    used = {a.get('request_sha256') for a in state['attempts'][24:]}
    for packet,item in zip([p for i,p in enumerate(packets) if i != 3],catalog['requests'],strict=True):
        cost = reservation(packet['payload'],item['total_tokens'])
        if (item['reserved_nanodollars'] != cost or item['accounting_policy_sha256'] != sha(accounting_policy())
                or item['model'] != accounting_policy()['model']):
            raise ResolutionError('gma_scoped_count_schedule_changed')
        if item['request_sha256'] not in used:
            total += cost
    total += effective_commitment(state,batch_manifest()['accounting_extension'])
    if total > 1_000_000_000:
        raise ResolutionError('pilot_budget_schedule_exhausted')
    return total
