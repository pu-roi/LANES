"""One exact authority-bound real batch; no NER, result persistence or seeding."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path

import httpx
from sqlalchemy import create_engine,select,text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.news import NewsExtractionRun,NewsArticleVersion
from app.services.news_claim_auditor import AuditorConfig
from app.services.news_gemini_receipts import BatchJournal,GCSReceiptStore,request_batch
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError,quote_options
from app.services.news_pilot_budget import GCSLedgerStore,PilotBudget,MODEL
from app.services.news_verified_cloud import release_file,preflight
from app.services.news_history_resources import checkpoint


def verified_input(args: object) -> tuple:
    release=release_file(Path(os.environ['LANES_NEWS_VERIFIED_RELEASE']),os.environ['LANES_NEWS_VERIFIED_RELEASE_SHA256'])
    result=preflight(release,database_url=settings.DATABASE_URL)
    authority,_=GCSLedgerStore('lanes-storage',args.authority_object).read()
    if (sha(authority)!=args.authority_sha256 or authority.get('schema_version')!='news-evidence-diagnostic-authority-v1'
            or authority.get('release_sha256')!=sha(release)
            or authority.get('application_sha256')!=sha(release['application_files'])
            or authority.get('database_identity_sha256')!=release['database_identity_sha256']
            or authority.get('allowed_operation')!='diagnose-one-batch'
            or authority.get('provider_requests')!=1 or authority.get('database_writes') is not False
            or authority.get('batch_index')!=0 or authority.get('expected_reservation_nanodollars')!=40430000
            or authority.get('receipts_prefix')!=os.environ.get('LANES_NEWS_RECEIPTS_PREFIX')):
        raise ResolutionError('evidence_diagnostic_authority_invalid')
    packet,_=GCSLedgerStore('lanes-storage',authority['input_object']).read()
    if (sha(packet)!=authority['input_sha256'] or packet['article_id']!=47 or packet['version_id']!=574
            or packet['context']['parent_run_id']!=375 or packet['batch_index']!=0 or packet['model']!=MODEL
            or sha(packet['payload'])!=authority['request_sha256']
            or sha(packet['payload'])!='35be3bd3917a156796057312b21958da5aa17beab62bd7cf4a0151bb0b98d732'
            or packet['expected_reservation_nanodollars']!=40430000
            or packet['original_release_sha256']!=authority['original_release_sha256']
            or packet['resolver_identity']!=release['resolver']):
        raise ResolutionError('evidence_diagnostic_input_changed')
    document=json.loads(packet['payload']['contents'][0]['parts'][0]['text'])
    if (len(document['targets'])!=4 or packet['context']['targets_sha256']!=sha(document['targets'])
            or document['quote_options']!=[{'option_index':i,'quote':q['quote']} for i,q in enumerate(quote_options(document['evidence_text']))]):
        raise ResolutionError('evidence_diagnostic_targets_changed')
    engine=create_engine(settings.DATABASE_URL,hide_parameters=True,connect_args={'connect_timeout':5})
    try:
        with engine.connect().execution_options(isolation_level='REPEATABLE READ') as connection:
            connection.execute(text('SET TRANSACTION READ ONLY'))
            with Session(bind=connection) as db:
                run=db.get(NewsExtractionRun,375);version=db.get(NewsArticleVersion,574)
                if (run is None or version is None or run.status!='completed' or run.article_version_id!=574
                        or version.article_id!=47 or run.pipeline_version!=authority['parent_pipeline_version']
                        or sha(run.result)!=packet['context']['parent_result_sha256']
                        or version.input_fingerprint!=packet['context']['input_sha256']
                        or version.input_snapshot['article_text']!=document['evidence_text']
                        or hashlib.sha256(document['evidence_text'].encode()).hexdigest()!=packet['source_body_sha256']):
                    raise ResolutionError('evidence_diagnostic_parent_changed')
    finally:engine.dispose()
    return release,authority,packet,result


async def execute(args: object) -> dict:
    release,authority,packet,preflight_result=verified_input(args)
    if not args.allow_one_request:
        return {'status':'preflight_passed','provider_requests':0,'database_writes':0,'neural_inferences':0,
            'request_sha256':authority['request_sha256'],'counts':preflight_result['counts']}
    if (authority['budget_object']!=os.environ.get('LANES_NEWS_PILOT_BUDGET_OBJECT')
            or authority['budget_identity']!=os.environ.get('LANES_NEWS_PILOT_BUDGET_IDENTITY')):
        raise ResolutionError('evidence_diagnostic_budget_changed')
    budget=PilotBudget(GCSLedgerStore('lanes-storage',authority['budget_object']),authority['budget_identity'])
    config=AuditorConfig.from_environment()
    if config.provider!='gemini' or config.model!=MODEL or config.error_code():
        raise ResolutionError('evidence_diagnostic_provider_changed')
    journal=BatchJournal(GCSReceiptStore(authority['receipts_prefix']),secrets=(config.gemini_api_key,))
    context={**packet['context'],'diagnostic_session_id':authority['session_id']}
    key=sha({'request_sha256':sha(packet['payload']),'context':context})
    result={'status':'failed','provider_requests':0,'database_writes':0,'neural_inferences':0,
        'request_identity':key,'request_sha256':sha(packet['payload']),
        'article_acceptance':'not_evaluated','seeding':'not_attempted'}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30,connect=5),follow_redirects=False,
                transport=httpx.AsyncHTTPTransport(retries=0)) as client:
            parsed,usage=await request_batch(config,packet['payload'],context,http=client,budget=budget,journal=journal)
        result.update(status='one_batch_evidence_references_passed',provider_requests=1,targets=len(parsed.results),usage=usage)
    except ResolutionError as exc:
        result.update(error_code=exc.code,diagnostic=getattr(exc,'provider_diagnostic',{}),provider_requests=exc.request_count)
    except (httpx.HTTPError,TimeoutError) as exc:
        result.update(error_code='evidence_diagnostic_transport_failed',error_type=type(exc).__name__,
            provider_requests=getattr(exc,'request_count',0),transport_status='outcome_unknown')
    finally:
        budget.stop('single_evidence_diagnostic_completed_requires_review')
    # Export artifact references/hashes, never provider text or credentials, to logs.
    result['receipt_prefix']=authority['receipts_prefix']+key+'/'
    return result


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authority-object',required=True)
    parser.add_argument('--authority-sha256',required=True)
    parser.add_argument('--allow-one-request',action='store_true')
    args=parser.parse_args()
    try:
        resources=[checkpoint()];result=asyncio.run(execute(args));resources.append(checkpoint())
        result['resource_snapshots']=resources
    except Exception as exc:
        result={'status':'failed','error_code':getattr(exc,'code','evidence_diagnostic_failed'),'error_type':type(exc).__name__}
    print(json.dumps({'schema':'news-evidence-diagnostic-v1',**result},sort_keys=True),flush=True)
    return 0 if result['status'] in ('preflight_passed','one_batch_evidence_references_passed') else 1

if __name__=='__main__':raise SystemExit(main())
