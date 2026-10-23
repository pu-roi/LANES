"""Private immutable batch receipts and strict, network-free evidence replay."""
from __future__ import annotations

import asyncio
import base64
from datetime import datetime, timezone
import hashlib
import json
import re
from urllib.parse import quote

import httpx

from app.services.news_claim_auditor import NewsClaimAuditor, _unique_json_object
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError, ResolutionResponse, quote_options
from app.services.news_pilot_budget import GCSLedgerStore
from app.services.news_provider_diagnostics import provider_diagnostic

MAX_RESPONSE = 65_536
FIELDS = ('place', 'status', 'time', 'depth', 'access', 'section')


def failure(code: str, diagnostic: dict | None = None) -> ResolutionError:
    error = ResolutionError(code)
    error.provider_diagnostic = diagnostic or {}
    return error


class GCSReceiptStore:
    """Only create/read objects under one private diagnostic/receipt session."""
    def __init__(self, prefix: str, *, token: object = None) -> None:
        if not re.fullmatch(r'private/news-pilot/[a-zA-Z0-9-]+/diagnostics/[a-zA-Z0-9-]+/', prefix):
            raise failure('native_resolution_receipt_location_invalid')
        self.prefix = prefix
        self.auth = GCSLedgerStore('lanes-storage', prefix+'identity', token=token)

    def _name(self, name: str) -> str:
        if not re.fullmatch(r'[a-f0-9]{64}/[a-z-]+\.json', name):
            raise failure('native_resolution_receipt_name_invalid')
        return self.prefix+name

    def put(self, name: str, value: dict) -> None:
        raw = json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
        if len(raw) > 1_048_576:
            raise failure('native_resolution_receipt_too_large')
        try:
            response = httpx.post('https://storage.googleapis.com/upload/storage/v1/b/lanes-storage/o',
                params={'uploadType': 'media', 'name': self._name(name), 'ifGenerationMatch': '0'},
                headers={**self.auth._headers(), 'Content-Type': 'application/json'},
                content=raw, timeout=10, follow_redirects=False)
            if response.status_code not in (200, 201):
                raise failure('native_resolution_receipt_storage_failed')
        except httpx.HTTPError as exc:
            raise failure('native_resolution_receipt_storage_failed') from exc

    def get(self, name: str) -> dict:
        try:
            url='https://storage.googleapis.com/storage/v1/b/lanes-storage/o/'+quote(self._name(name), safe='')
            with httpx.Client(headers=self.auth._headers(), timeout=10, follow_redirects=False) as client:
                metadata=client.get(url)
                if metadata.status_code != 200:
                    raise failure('native_resolution_receipt_storage_failed')
                response=client.get(url, params={'alt':'media', 'generation':metadata.json()['generation']})
                if response.status_code != 200 or len(response.content)>1_048_576:
                    raise failure('native_resolution_receipt_storage_failed')
                return json.loads(response.content, object_pairs_hook=_unique_json_object)
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise failure('native_resolution_receipt_storage_failed') from exc


class BatchJournal:
    def __init__(self, store: object, *, secrets: tuple[str, ...] = ()) -> None:
        self.store, self.secrets = store, secrets

    def begin(self, payload: dict, context: dict, model: str, reservation: str | None) -> str:
        key=sha({'request_sha256':sha(payload), 'context':context})
        value={'schema_version':'news-gemini-batch-intent-v1', 'request_identity':key,
            'request_sha256':sha(payload), 'payload':payload, 'context':context, 'model':model,
            'budget_reservation_id':reservation, 'created_at':datetime.now(timezone.utc).isoformat()}
        serialized=json.dumps(value,ensure_ascii=False)
        if any(s and s in serialized for s in self.secrets):
            raise failure('native_resolution_receipt_secret_in_request')
        self.store.put(key+'/intent.json',value)
        return key

    def response(self, key: str, status: int, body: bytes, *, oversized: bool=False) -> dict:
        raw=body[:MAX_RESPONSE]
        for secret in self.secrets:
            if secret:
                raw=raw.replace(secret.encode(),b'[redacted]')
        redacted=raw!=body[:MAX_RESPONSE]
        value={'schema_version':'news-gemini-batch-response-v1','request_identity':key,
            'http_status':status,'body_base64':base64.b64encode(raw).decode('ascii'),
            'body_sha256':hashlib.sha256(raw).hexdigest(),
            'provider_body_prefix_sha256':hashlib.sha256(body[:MAX_RESPONSE]).hexdigest(),
            'replayable':not redacted and not oversized, 'redacted':redacted,'oversized':oversized}
        self.store.put(key+'/response.json',value)
        return value

    def outcome(self, key: str, stage: str, *, code: str | None=None, diagnostic: dict | None=None) -> None:
        self.store.put(key+'/validation.json',{'schema_version':'news-gemini-batch-validation-v1',
            'request_identity':key,'stage':stage,'error_code':code,'diagnostic':diagnostic or {},
            'article_acceptance':'not_evaluated','database_publication':'not_attempted'})

    def article(self, context: dict, payload: dict | None, code: str | None) -> None:
        key=sha({'article_validation':context})
        value={'schema_version':'news-gemini-article-validation-v1','context':context,
            'payload':payload,'canonical_validation':'failed' if code else 'passed',
            'error_code':code,'database_commit':'not_confirmed'}
        if any(s and s in json.dumps(value,ensure_ascii=False) for s in self.secrets):
            raise failure('native_resolution_receipt_secret_in_response')
        self.store.put(key+'/article-validation.json',value)

    def semantic(self, payload: dict, context: dict, *, error_code: str | None = None,
                 row_outcomes: list | None = None) -> None:
        key = sha({'request_sha256':sha(payload), 'context':context})
        value = {'schema_version':'news-gemini-batch-semantic-v1',
            'request_identity':key, 'stage':'failed' if error_code else 'passed',
            'error_code':error_code, 'article_acceptance':'not_evaluated', 'database_publication':'not_attempted'}
        if row_outcomes is not None:
            value.update(schema_version='news-gemini-batch-semantic-v2',
                         stage='row_outcomes_recorded', row_outcomes=row_outcomes)
        self.store.put(key+'/semantic-validation.json', value)


def validate_batch(payload: dict, raw: bytes, config: object) -> tuple[object, dict]:
    """Same strict JSON/targets, followed by fail-fast evidence index checks."""
    if len(raw)>MAX_RESPONSE:
        raise failure('native_resolution_response_too_large')
    try:
        envelope=json.loads(raw,object_pairs_hook=_unique_json_object)
        content,request_id=NewsClaimAuditor(config)._content(envelope)
        value=json.loads(content,object_pairs_hook=_unique_json_object)
        parsed=ResolutionResponse.model_validate_json(json.dumps(value),strict=True)
        document=json.loads(payload['contents'][0]['parts'][0]['text'],object_pairs_hook=_unique_json_object)
        expected=[m['id'] for m in document['targets']]
        options=quote_options(document['evidence_text'])
        if document['quote_options'] != [{'option_index':i,'quote':q['quote']} for i,q in enumerate(options)]:
            raise failure('native_resolution_quote_options_changed')
        received=[r.target_id for r in parsed.results]
        if len(received)!=len(expected) or len(set(received))!=len(received) or set(received)!=set(expected):
            raise failure('native_resolution_target_mismatch', {'category':'response_target_mismatch',
                'expected_count':len(expected),'returned_count':len(received),
                'missing_count':len(set(expected)-set(received)),
                'unexpected_count':len(set(received)-set(expected)),
                'duplicate_count':len(received)-len(set(received))})
        errors=[]
        for row in parsed.results:
            for field in FIELDS:
                indexes=getattr(row,field+'_evidence')
                duplicates=sorted(i for i in set(indexes) if indexes.count(i)>1)
                invalid=[i for i in indexes if not 0<=i<len(options)]
                if duplicates or invalid:
                    display=lambda values:[i if abs(i)<=1_000_000 else 'outside_display_range' for i in values[:12]]
                    errors.append({'target_id':row.target_id,'field':field+'_evidence',
                        'duplicate_indices':display(duplicates),'out_of_range_indices':display(invalid),
                        'valid_range':[0,len(options)-1]})
        if errors:
            raise failure('native_resolution_evidence_invalid',{'category':'invalid_evidence_references',
                'error_count':len(errors),'errors':errors[:32]})
        observation=usage_observation(envelope)
        if isinstance(request_id,str) and re.fullmatch(r'[A-Za-z0-9_./:-]{1,200}',request_id):
            observation['request_id']=request_id
        return parsed,observation
    except ResolutionError:
        raise
    except (ValueError,KeyError,TypeError,AttributeError) as exc:
        raise failure('native_resolution_response_invalid') from exc


def usage_observation(envelope: object) -> dict:
    """Bounded reporting only; the independent budget ledger settles charges.

    Do not require article JSON to be valid before preserving provider usage.
    """
    if not isinstance(envelope,dict):
        return {}
    result={}
    for name,key in (('request_id','responseId'),('actual_model','modelVersion')):
        value=envelope.get(key)
        if isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9_./:-]{1,200}',value):result[name]=value
    usage=envelope.get('usageMetadata',{})
    if isinstance(usage,dict):
        for name,key in (('input_tokens','promptTokenCount'),('output_tokens','candidatesTokenCount'),('thinking_tokens','thoughtsTokenCount')):
            value=usage.get(key)
            if type(value) is int and 0<=value<=10_000_000:result[name]=value
    return result


async def request_batch(config: object, payload: dict, context: dict, *, http: httpx.AsyncClient,
                        timeout: float=30, budget: object=None, journal: BatchJournal | None=None) -> tuple:
    reservation=None;key=None;diagnostic={};posted=False;outcome_written=False;observed={}
    try:
        if budget is not None:reservation=budget.reserve(config.model,payload,context)
        if journal is not None:key=journal.begin(payload,context,config.model,reservation)
        body=bytearray();oversized=False
        async with asyncio.timeout(timeout):
            posted=True
            async with http.stream('POST','https://generativelanguage.googleapis.com/v1beta/models/'+config.model+':generateContent',
                    headers={'x-goog-api-key':config.gemini_api_key},json=payload,follow_redirects=False) as response:
                status=response.status_code
                async for chunk in response.aiter_bytes():
                    body.extend(chunk[:max(0,MAX_RESPONSE+1-len(body))])
                    if len(body)>MAX_RESPONSE:
                        oversized=True;break
        if journal is not None:
            saved=journal.response(key,status,bytes(body),oversized=oversized)
            if saved['redacted']:raise failure('native_resolution_receipt_secret_in_response')
        if oversized:raise failure('native_resolution_response_too_large')
        # Billing metadata must survive malformed/unsupported article facts.
        if budget is not None and hasattr(budget,'observe_response'):
            if journal is None:raise failure('pilot_accounting_receipt_required')
            diagnostic=budget.observe_response(reservation,journal.store.get(key+'/intent.json'),saved)
        if status!=200:
            diagnostic=await provider_diagnostic(httpx.Response(status,content=bytes(body)),secrets=(config.gemini_api_key,))
            error=failure('native_resolution_rate_limited' if status==429 else 'native_resolution_http_error',diagnostic)
            error.retryable=status in (408,429) or status>=500
            raise error
        try:
            observed=usage_observation(json.loads(bytes(body),object_pairs_hook=_unique_json_object))
        except (ValueError,TypeError):
            pass  # Retained invalid envelope remains a hard failure below.
        parsed,observation=validate_batch(payload,bytes(body),config)
        diagnostic=observation
        if journal is not None:
            journal.outcome(key,'evidence_references_passed',diagnostic=observation);outcome_written=True
        if reservation is not None:
            budget.finish(reservation,succeeded=True,diagnostic=observation);reservation=None
        return parsed,observation
    except BaseException as exc:
        diagnostic=getattr(exc,'provider_diagnostic',diagnostic)
        if journal is not None and key is not None and not outcome_written:
            code=getattr(exc,'code','native_resolution_request_interrupted' if isinstance(exc,asyncio.CancelledError) else 'native_resolution_request_failed')
            journal.outcome(key,'failed',code=code,diagnostic=diagnostic)
        if isinstance(exc,(ResolutionError,httpx.HTTPError,TimeoutError)):
            exc.request_count=int(posted)
            exc.response_usage=observed
        raise
    finally:
        if reservation is not None:budget.finish(reservation,succeeded=False,diagnostic=diagnostic)


def replay_bundle(bundle: dict, expected_sha256: str, *, config: object) -> dict:
    if sha(bundle)!=expected_sha256:
        raise failure('native_resolution_receipt_tampered')
    try:
        intent,response=bundle['intent'],bundle['response']
        key=sha({'request_sha256':sha(intent['payload']),'context':intent['context']})
        if (intent.get('schema_version')!='news-gemini-batch-intent-v1'
                or response.get('schema_version')!='news-gemini-batch-response-v1'
                or key!=intent['request_identity'] or key!=response['request_identity']
                or intent['request_sha256']!=sha(intent['payload']) or intent['model']!=config.model
                or intent.get('budget_reservation_id') not in (None,key) or not response['replayable']):
            raise failure('native_resolution_receipt_binding_invalid')
        raw=base64.b64decode(response['body_base64'],validate=True)
        if hashlib.sha256(raw).hexdigest()!=response['body_sha256']:
            raise failure('native_resolution_receipt_tampered')
        if response['http_status']!=200:
            return {'status':'provider_rejected','http_status':response['http_status'],'provider_requests':0}
        parsed,usage=validate_batch(intent['payload'],raw,config)
        return {'status':'evidence_references_passed','targets':len(parsed.results),
            'usage':usage,'article_acceptance':'not_evaluated','provider_requests':0}
    except ResolutionError:
        raise
    except (ValueError,KeyError,TypeError) as exc:
        raise failure('native_resolution_receipt_binding_invalid') from exc
