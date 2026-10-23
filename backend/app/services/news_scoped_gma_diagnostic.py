"""One counted, retained GMA diagnostic; never stores application results."""
from __future__ import annotations

import hashlib
import json

import httpx

from app.services.news_claim_auditor import _unique_json_object
from app.services.news_gemini_receipts import request_batch
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_ner_durable.scoped_resolution import CONTRACT, evaluate_rows
from app.services.news_pilot_accounting import accounting_policy, commitment, reservation

SESSION = 'scoped-gma-gate-20261023-v1'
ROOT = 'private/news-pilot/20261022-5512bbaa/'
PREFIX = ROOT + 'diagnostics/' + SESSION + '/'
REQUEST = 'af01fd06dab994a4180a018eb6201598b1c23ec72f0c5008dba72eb59461ff26'
PARENT = '93de1cc2436171660376ee466b0fd9f37b413d80582a8f8a9d37d83957c4fe54'
VERSION = 'news-scoped-gma-diagnostic-v1'
TARGETS = ['n12','n13','n14','n15']


def stop_session(store: object) -> None:
    """Stop this explicitly resumed session even on pre-dispatch validation errors."""
    state,generation=store.read()
    resumes=state.get('manual_resumptions',[])
    if resumes and resumes[-1].get('id')==SESSION and state['status']!='stopped':
        state.update(status='stopped',stop_reason='scoped_gma_diagnostic_exit_requires_review')
        store.compare_and_swap(generation,state)


def validate_authority(authority: dict, pin: str, release: dict, packet: dict, *, operation: str,
                       receipts_prefix: str, budget_identity: str) -> None:
    expected = {'schema_version','session_id','release_sha256','application_sha256','assets_sha256',
        'database_identity_sha256','resolver','article_id','version_id','parent_run_id','parent_result_sha256',
        'input_sha256','source_body_sha256','source_layout_sha256','request_sha256','batch_index','targets',
        'operation','generation_requests','count_requests','database_writes','budget_object','budget_identity',
        'baseline_sha256','attempts_sha256','settlements_sha256','receipts_prefix','accounting_policy_sha256',
        'count_catalog','expected_reservation_nanodollars'}
    if (set(authority)!=expected or sha(authority)!=pin or authority['schema_version']!=VERSION
            or operation not in ('count','gate') or authority['operation']!=operation
            or authority['session_id']!=SESSION or authority['release_sha256']!=sha(release)
            or authority['application_sha256']!=sha(release['application_files'])
            or authority['assets_sha256']!=release['base_assets_sha256']
            or authority['database_identity_sha256']!=release['database_identity_sha256']
            or authority['resolver']!=release['resolver'] or release['resolver'].get('evidence_contract')!=CONTRACT
            or [authority[k] for k in ('article_id','version_id','parent_run_id','batch_index')]!=[47,574,375,3]
            or authority['parent_result_sha256']!=PARENT or authority['targets']!=TARGETS
            or authority['generation_requests']!=(1 if operation=='gate' else 0)
            or authority['count_requests']!=(1 if operation=='count' else 0)
            or authority['database_writes'] is not False
            or authority['budget_object']!=ROOT+'budget.json' or authority['budget_identity']!=budget_identity
            or authority['receipts_prefix']!=PREFIX or receipts_prefix!=PREFIX
            or authority['accounting_policy_sha256']!=sha(accounting_policy())
            or authority['request_sha256']!=REQUEST or sha(packet['payload'])!=REQUEST):
        raise ResolutionError('scoped_diagnostic_authority_invalid')
    document=json.loads(packet['payload']['contents'][0]['parts'][0]['text'])
    if (packet['context']['parent_run_id']!=375 or packet['context']['parent_result_sha256']!=PARENT
            or packet['context']['input_sha256']!=authority['input_sha256']
            or hashlib.sha256(document['evidence_text'].encode()).hexdigest()!=authority['source_body_sha256']
            or sha(document['source_layout'])!=authority['source_layout_sha256']
            or [m['id'] for m in document['targets']]!=TARGETS):
        raise ResolutionError('scoped_diagnostic_request_changed')
    for key in ('baseline_sha256','attempts_sha256','settlements_sha256'):
        if not isinstance(authority[key],str) or len(authority[key])!=64:
            raise ResolutionError('scoped_diagnostic_baseline_invalid')
    if operation=='count' and (authority['count_catalog'] is not None or authority['expected_reservation_nanodollars'] is not None):
        raise ResolutionError('scoped_diagnostic_count_authority_invalid')


def validate_baseline(state: dict, authority: dict, *, ready: bool=False) -> None:
    if (state['status']!=('ready' if ready else 'stopped') or len(state['attempts'])!=23
            or any(a['status']=='in_flight' for a in state['attempts'])
            or commitment(state)!=667_374_400
            or sum(a['reserved_nanodollars'] for a in state['attempts'])!=845_678_800
            or sha(state['attempts'])!=authority['attempts_sha256']
            or sha(state['settlements'])!=authority['settlements_sha256']):
        raise ResolutionError('scoped_diagnostic_baseline_changed')
    if not ready and sha(state)!=authority['baseline_sha256']:
        raise ResolutionError('scoped_diagnostic_baseline_changed')
    if ready:
        resumes=state.get('manual_resumptions',[])
        if not resumes or resumes[-1].get('id')!=SESSION or resumes[-1].get('previous_sha256')!=authority['baseline_sha256']:
            raise ResolutionError('scoped_diagnostic_resume_required')


async def count_once(config: object, packet: dict, journal: object, *, http: httpx.AsyncClient,
                     session_id: str = SESSION, schema_version: str = VERSION) -> dict:
    """Retain count response before parsing; immutable intent blocks resending."""
    payload=packet['payload'];key=sha({'count_tokens':sha(payload),'session_id':session_id})
    journal.store.put(key+'/count-intent.json',{'schema_version':schema_version,'request_sha256':sha(payload),
        'session_id':session_id,'model':config.model,'accounting_policy_sha256':sha(accounting_policy())})
    error=None;posted=False
    try:
        posted=True  # A transport interruption may leave dispatch uncertain.
        async with http.stream('POST','https://generativelanguage.googleapis.com/v1beta/models/'+config.model+':countTokens',
                headers={'x-goog-api-key':config.gemini_api_key},follow_redirects=False,timeout=10,
                json={'generateContentRequest':{'model':'models/'+config.model,**payload}}) as response:
            raw=bytearray();oversized=False
            async for chunk in response.aiter_bytes():
                raw.extend(chunk[:max(0,16385-len(raw))])
                if len(raw)>16384:oversized=True;break
            saved=journal.response(key,response.status_code,bytes(raw),oversized=oversized)
        if saved['redacted'] or oversized or response.status_code!=200:
            raise ResolutionError('scoped_diagnostic_count_response_invalid')
        value=json.loads(raw,object_pairs_hook=_unique_json_object)
        item={'schema_version':'news-pilot-count-v2','request_sha256':sha(payload),'model':config.model,
            'accounting_policy_sha256':sha(accounting_policy()),'total_tokens':value.get('totalTokens'),
            'reserved_nanodollars':reservation(payload,value.get('totalTokens')),'response_sha256':saved['body_sha256']}
        catalog={'schema_version':'news-pilot-count-catalog-v2','accounting_policy_sha256':sha(accounting_policy()),'requests':[item]}
        journal.store.put(sha(catalog)+'/count-catalog.json',catalog)
        return catalog
    except BaseException as exc:
        error=getattr(exc,'code','scoped_diagnostic_count_failed')
        raise
    finally:
        journal.store.put(key+'/count-validation.json',{'schema_version':schema_version,
            'status':'failed' if error else 'completed','error_code':error,'count_requests':int(posted),'generation_requests':0})


def qualify_count(catalog: dict, authority: dict, packet: dict, state: dict) -> int:
    reference=authority['count_catalog']
    if (not isinstance(reference,dict) or set(reference)!={'object','sha256'}
            or not reference['object'].startswith(PREFIX)
            or sha(catalog)!=reference['sha256'] or catalog.get('schema_version')!='news-pilot-count-catalog-v2'
            or catalog.get('accounting_policy_sha256')!=sha(accounting_policy())
            or len(catalog.get('requests',[]))!=1):
        raise ResolutionError('scoped_diagnostic_count_changed')
    item=catalog['requests'][0];cost=reservation(packet['payload'],item['total_tokens'])
    if (item['request_sha256']!=REQUEST or item['model']!=accounting_policy()['model']
            or item['accounting_policy_sha256']!=sha(accounting_policy())
            or item['reserved_nanodollars']!=cost or authority['expected_reservation_nanodollars']!=cost):
        raise ResolutionError('scoped_diagnostic_count_changed')
    if commitment(state)+cost>1_000_000_000:
        raise ResolutionError('pilot_budget_exhausted')
    return cost


def semantic_quality(source: object, baseline: object, rows: object, catalog: object) -> dict:
    claims,groups,_,outcomes,layout_sha=evaluate_rows(source,baseline,rows,catalog)
    by_id={r.target_id:r for r in rows};accepted={g['target_entity_ids'][0]:claims[g['claim_index']] for g in groups}
    issues=[]
    for target_id in ('n12','n15'):
        if by_id[target_id].verdict!='unsupported':issues.append({'target_id':target_id,'code':'context_heading_not_unsupported'})
    for target_id in ('n13','n14'):
        claim=accepted.get(target_id);row=by_id[target_id]
        if claim is None:
            issues.append({'target_id':target_id,'code':'road_not_accepted'});continue
        if claim.canonical_city!=catalog.city('Quezon City')[0].name or row.status!='active':
            issues.append({'target_id':target_id,'code':'road_place_or_status_mismatch'})
        if claim.event_time_resolved is None or claim.event_time_resolved.isoformat()!='2026-09-09T08:55:00+08:00':
            issues.append({'target_id':target_id,'code':'observation_time_mismatch'})
        if row.depth_scope!='shared' or row.depth_text!='Waist-deep (37 inches)' or claim.depth_canonical is not None:
            issues.append({'target_id':target_id,'code':'shared_depth_not_preserved'})
    return {'status':'one_batch_accepted' if not issues else 'one_batch_incomplete',
            'row_outcomes':outcomes,'quality_issues':issues,'source_layout_sha256':layout_sha,
            'article_acceptance':'not_evaluated','database_writes':0}


async def gate_once(resolver: object, packet: dict, source: object, baseline: object, budget: object,
                    *, http: httpx.AsyncClient) -> dict:
    key=sha({'request_sha256':REQUEST,'context':packet['context']})
    result={'status':'requires_attention','provider_requests':0,'count_requests':0,'database_writes':0,
            'article_acceptance':'not_evaluated','receipt_prefix':PREFIX+key+'/'}
    try:
        rows,usage=await request_batch(resolver.config,packet['payload'],packet['context'],http=http,
            timeout=resolver.timeout_seconds,budget=budget,journal=resolver.receipts)
        result.update(provider_requests=1,transport='succeeded',response_retained=True,references='passed',usage=usage)
        quality=semantic_quality(source,baseline,rows.results,resolver.catalog)
        resolver.receipts.semantic(packet['payload'],packet['context'],row_outcomes=quality['row_outcomes'])
        resolver.receipts.store.put(key+'/batch-quality.json',quality)
        result.update(status='completed' if quality['status']=='one_batch_accepted' else 'requires_attention',
            semantic_quality=quality['status'],row_outcomes=quality['row_outcomes'],quality_issues=quality['quality_issues'])
    except (ResolutionError,httpx.HTTPError,TimeoutError) as exc:
        result.update(error_code=getattr(exc,'code','scoped_diagnostic_transport_failed'),
                      provider_requests=max(result['provider_requests'],getattr(exc,'request_count',0)),
                      diagnostic=getattr(exc,'provider_diagnostic',{}))
    finally:
        budget.stop('scoped_gma_one_batch_finished_requires_review')
    return result
