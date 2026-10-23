"""Versioned four-target continuation; accounting and authority are explicit."""
from __future__ import annotations

import base64
from copy import deepcopy

from app.models.news import NewsExtractionRun
from app.services.news_gma_review import PARENT_RESULT, PARENT_PIPELINE, INPUT_PIN, CACHE_PIN
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_pilot_accounting import accounting_policy, commitment, reservation

REQUESTS = (
    '02f4b9b633a06363912fa0f47262377de92e7cb083dcc00011ce76a6cf1ddd8a',
    '330065512f56ade7a1d492c84dda8cf98c45c83a467fd5738e171cba14f7af2f',
    '4315539a78182efb3090711c5c584892b7ca55d8353c665722026e5a0af38b32',
    'ddf318f1ae457b1c22324850cc192650e94355629210c9fcbded238fdd6a354e',
    '576bd7d9d4a3970422cb101ff04ed32c5374a9eb53574e9ef40373df4f72cdaf',
    'a34da60f794487b914f6ce07c271e8ce46de1a4000ab68e6253eeb7c462945fd',
    '28b0400c6ea3baecdacf10ad76da7b5ce0a3fdab085c9869bbcfc32c7a0aefe3',
    '8b68fcd98226448cd7b3d457f08d5908eecc54957c11d60306661d299ea25962',
    'cf69552e353b143af333a370a5fd728096e746bcf0148fe14e17b66a45120330',
    '14aa9ba8109bd818b12704a636a0f3acd8060c297283a6bd6c07c070758eef35',
    'a9afb4105654d65bc5702cc7546ffd0de7160219c4f9e32c3910bcd1e9e1f37d',
    'db120b54c8c4ad76236c6d1f9bd8729ffca167aa338af2616aad9a3642720ec6',
    'a3392d239eac1a0d7ab6971d2fc1abd108527a131d9d0e919452dd15e331ceeb',
)


def batch_manifest() -> dict:
    return {'schema_version':'gma-budget-review-batches-v2','parent_run_id':375,
        'parent_result_sha256':PARENT_RESULT,'input_sha256':INPUT_PIN,
        'cached_bundle_sha256':CACHE_PIN,'sizes':[4]*12+[3],
        'request_sha256s':list(REQUESTS),'accounting_policy_sha256':sha(accounting_policy())}


class GmaBudgetBatchPlan:
    def __init__(self, manifest: dict, *, cache_loader: object = None) -> None:
        if manifest!=batch_manifest():raise ResolutionError('gma_batch_manifest_changed')
        self.manifest=deepcopy(manifest);self.cache_loader=cache_loader
        self.accepted_gate=None

    @property
    def identity(self) -> str:
        if self.manifest!=batch_manifest():raise ResolutionError('gma_batch_manifest_changed')
        return sha(self.manifest)

    def batches(self,candidates: list[dict]) -> list[list[dict]]:
        if [c['id'] for c in candidates]!=['n'+str(i) for i in range(51)]:
            raise ResolutionError('gma_target_inventory_changed')
        return [candidates[i:i+4] for i in range(0,51,4)]

    def adopt(self,index: int,payload: dict,context: dict,config: object,journal: object) -> tuple | None:
        from app.services.news_gemini_receipts import replay_bundle,validate_batch
        if (sha(payload)!=REQUESTS[index] or any(context.get(k)!=self.manifest[k]
                for k in ('parent_run_id','parent_result_sha256','input_sha256'))):
            raise ResolutionError('gma_frozen_request_changed')
        if index>1 or index==1 and self.accepted_gate is None:return None
        bundle=self.cache_loader() if index==0 else self.accepted_gate['bundle']
        pin=CACHE_PIN if index==0 else self.accepted_gate['sha256']
        replay=replay_bundle(bundle,pin,config=config)
        intent=bundle['intent']
        if (replay['status']!='evidence_references_passed' or intent['payload']!=payload
                or any(intent['context'].get(k)!=v for k,v in context.items()) or journal is None):
            raise ResolutionError('gma_cached_evidence_changed')
        key=sha({'request_sha256':sha(payload),'context':context})
        journal.store.put(key+'/adoption.json',{'schema_version':'gma-batch-adoption-v2',
            'source_bundle_sha256':pin,'source_request_identity':intent['request_identity'],
            'new_provider_requests':0,'new_reservations':0,'article_acceptance':'not_evaluated'})
        return validate_batch(payload,base64.b64decode(bundle['response']['body_base64']),config)


def validate_authority(authority: object,engine: object) -> None:
    from app.services.news_three_article_pilot import PilotAuthority
    p=authority.policy
    if (sha(p)!=authority.policy_sha256 or p.get('schema_version')!='news-gma-budget-review-v2'
            or p.get('allowed_operations') not in (['count'],['gate'],['resolve'],['archive'])
            or p.get('allowed_article_ids')!=[47] or p.get('allowed_parent_run_ids')!=[375]
            or p.get('parent_pipeline_version')!=PARENT_PIPELINE or p.get('parent_version_id')!=574
            or p.get('parent_result_sha256')!=PARENT_RESULT or p.get('cache_bundle_sha256')!=CACHE_PIN
            or p.get('batch_manifest')!=batch_manifest() or p.get('resolver',{}).get('batch_size')!=4
            or p.get('resolver',{}).get('batch_plan_sha256')!=sha(batch_manifest())
            or p.get('accounting_policy_sha256')!=sha(accounting_policy())
            or p.get('budget_limit_nanodollars')!=1_000_000_000):
        raise ResolutionError('gma_budget_authority_invalid')
    compatible={**p,'schema_version':'news-three-article-pilot-v1','allowed_operations':['resolve']}
    PilotAuthority(compatible,sha(compatible),authority.trusted).validate(engine)


def validate_session(authority: object,db: object,run_ids: tuple | None,sources: tuple | None,operation: str) -> None:
    from app.services.news_three_article_pilot import PilotAuthority
    from app.services import news_gma_review
    authority.validate(db.get_bind());p=authority.policy
    if p['allowed_operations']!=[operation] or operation not in ('count','gate','resolve','archive'):
        raise ResolutionError('gma_operation_not_authorized')
    # Reuse source, paused settings and old-parent checks without repurposing
    # an earlier signed authority. This local adapter never escapes validation.
    compatible={**p,'schema_version':'news-gma-review-v1',
        'batch_manifest':news_gma_review.batch_manifest(),
        'resolver':{**p['resolver'],'batch_size':8,'batch_plan_sha256':sha(news_gma_review.batch_manifest())},
        'allowed_operations':['archive' if operation=='archive' else 'resolve']}
    old=PilotAuthority(compatible,sha(compatible),authority.trusted)
    news_gma_review.validate_session(old,db,run_ids,sources,compatible['allowed_operations'][0])
    failed=db.get(NewsExtractionRun,378)
    if failed is None or failed.status!='failed' or failed.result is not None:
        raise ResolutionError('gma_failed_correction_changed')


def qualify_schedule(packets: list[dict],catalog: dict,state: dict) -> int:
    if (catalog.get('schema_version')!='news-pilot-count-catalog-v2'
            or catalog.get('accounting_policy_sha256')!=sha(accounting_policy())
            or [sha(p['payload']) for p in packets]!=list(REQUESTS)
            or len(catalog.get('requests',[]))!=13):raise ResolutionError('gma_count_schedule_changed')
    costs=[]
    for packet,item,pin in zip(packets,catalog['requests'],REQUESTS,strict=True):
        cost=reservation(packet['payload'],item['total_tokens'])
        if (item['request_sha256']!=pin or item['reserved_nanodollars']!=cost
                or item['accounting_policy_sha256']!=sha(accounting_policy())
                or item['model']!=accounting_policy()['model']):raise ResolutionError('gma_count_schedule_changed')
        costs.append(cost)
    # Count first payload as a calibration; its input allowance must cover the
    # independently retained provider prompt usage, including schema overhead.
    if costs[0]-8192*2500<6349*300:raise ResolutionError('gma_count_calibration_failed')
    outstanding=[cost for pin,cost in zip(REQUESTS[1:],costs[1:],strict=True)
        if not any(a.get('request_sha256')==pin for a in state['attempts'])]
    total=commitment(state)+sum(outstanding)
    if total>1_000_000_000:raise ResolutionError('pilot_budget_schedule_exhausted')
    return total


def prepare_parent(db: object,trusted: object,resolver: object,sources: tuple) -> tuple:
    """Rebuild deterministic native proposals from immutable 375; no NER call."""
    from app.services.news_ner_durable.resolution_worker import _parent
    from app.services.news_ner_durable.contracts import RunEvidence
    from app.services.news_ner_durable.assets import with_resolution_assets
    from app.services.news_ner_durable.adapter import build_native_result
    from app.services.news_ner.location_pipeline import from_neural_mentions
    run,version,context,source,original=_parent(db,375,sources)
    if sha(run.result)!=PARENT_RESULT:raise ResolutionError('gma_original_parent_changed')
    derived=with_resolution_assets(trusted,resolver.identity)
    child=RunEvidence.model_validate({**context.model_dump(),'pipeline_version':derived.pipeline_version})
    proposal=from_neural_mentions({**source.runtime_request(context.input_fingerprint),
        'mentions':[m.model_dump(mode='json') for m in original.native.neural_mentions]})['proposal']
    if (proposal['effective_mentions']!=[m.model_dump(mode='json') for m in original.native.effective_mentions]
            or proposal['proposals']!=original.native.proposals or proposal['abstentions']!=original.native.abstentions):
        raise ResolutionError('native_resolution_parent_binding_invalid')
    raw={'proposal':proposal,'graph':original.native.graph.model_dump(mode='json',by_alias=True),
        'measurements':original.measurements,'provenance':original.provenance['runtime']}
    return source,build_native_result(child,raw,derived,extracted_at=original.extracted_at)
