"""Manual NER-to-Gemini handoff. Preflight is read-only and never calls Gemini."""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import replace
import json
from pathlib import Path
from uuid import uuid4


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('preflight','resolve'))
    parser.add_argument('--run-id',type=int,action='append',required=True)
    parser.add_argument('--model',required=True)
    parser.add_argument('--evidence-contract',choices=('quote-option-enum-v1','scoped-quote-options-v2'),
                        default='quote-option-enum-v1')
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--bundle-sha256',required=True)
    parser.add_argument('--worker-code-sha256',required=True)
    parser.add_argument('--confirm-database',required=True)
    parser.add_argument('--receipt-directory',type=Path,required=True)
    parser.add_argument('--authority',type=Path)
    parser.add_argument('--authority-sha256')
    args=parser.parse_args()
    engine=None
    output=None
    resolution_error_type=()
    interrupted=False
    result={'status':'failed','error_code':'native_resolution_failed'}
    try:
        from app.services.news_ner_durable.gemini_resolution import GeminiResolver
        from app.services.news_ner_durable.resolution import ResolutionError
        resolution_error_type=ResolutionError
        from app.services.news_claim_auditor import AuditorConfig
        from app.services.news_ner_durable.assets import load_trusted_assets,with_resolution_assets
        from app.services.news_ner_durable.resolution_worker import resolution_preflight,resolve_native_runs
        from app.services.news_historical_processing import read_document
        from app.services.news_sources import load_news_sources
        from app.core.config import settings
        from sqlalchemy import create_engine,text
        from sqlalchemy.orm import sessionmaker
        from app.services.news_ner_durable.contracts import sha
        # Receipts contain only safe IDs/hashes/errors, never provider headers or keys.
        root=(Path(__file__).resolve().parents[2]/'data').resolve()
        requested_output=args.receipt_directory.resolve()
        if not requested_output.is_relative_to(root) or requested_output==root:
            raise ResolutionError('native_resolution_private_receipts_required')
        output=requested_output
        resolver=GeminiResolver(replace(AuditorConfig.from_environment(),provider='gemini',model=args.model),
                                evidence_contract=args.evidence_contract)
        trusted=load_trusted_assets(args.bundle.resolve(),args.bundle_sha256,expected_worker_code_sha256=args.worker_code_sha256)
        engine=create_engine(settings.DATABASE_URL,connect_args={'connect_timeout':5},pool_timeout=5)
        with engine.connect() as db:
            if db.scalar(text('SELECT current_database()'))!=args.confirm_database or engine.url.database!=args.confirm_database:
                raise ResolutionError('native_resolution_target_invalid')
        factory=sessionmaker(bind=engine)
        ids=tuple(args.run_id)
        sources=load_news_sources()
        if args.mode=='preflight':
            authority=resolution_preflight(factory,ids,trusted,resolver.identity,sources)
            output.mkdir(parents=True,exist_ok=True)
            authority_path=output/('authority-'+uuid4().hex+'.json')
            authority_path.write_text(json.dumps(authority,indent=2,sort_keys=True)+'\n',encoding='utf-8')
            from app.models.news import NewsExtractionRun
            with factory() as db:
                parents=sorted({db.get(NewsExtractionRun,i).pipeline_version for i in ids})
            read_context={'schema_version':'saved-native-read-context-v2',
                'pipeline_version':with_resolution_assets(trusted,resolver.identity).pipeline_version,
                'database_identity_sha256':authority['database_identity_sha256'],'fallback_pipeline_versions':parents}
            read_path=output/('read-context-'+uuid4().hex+'.json')
            read_path.write_text(json.dumps(read_context,indent=2,sort_keys=True)+'\n',encoding='utf-8')
            result={'status':'preflight_passed','credentials_configured':True,'api_requests':0,
                'authority_file':str(authority_path),'authority_sha256':sha(authority),
                'read_context_file':str(read_path),'read_context_sha256':sha(read_context),
                'pipeline_version':with_resolution_assets(trusted,resolver.identity).pipeline_version}
        else:
            if len(ids)>2:
                raise ResolutionError('native_resolution_batch_invalid')
            authority=read_document(args.authority) if args.authority else None
            result=asyncio.run(resolve_native_runs(factory,ids,trusted=trusted,resolver=resolver,sources=sources,
                authority=authority,authority_sha256=args.authority_sha256))
            result['status']='requires_attention' if result['failed'] or result['retry_wait'] or result['busy'] else 'completed'
    except (KeyboardInterrupt,asyncio.CancelledError):
        interrupted=True
        result={'status':'failed','error_code':'native_resolution_cancelled'}
    except Exception as exc:
        result={'status':'failed','error_code':exc.code if isinstance(exc,resolution_error_type) else 'native_resolution_failed'}
    finally:
        if engine is not None:engine.dispose()
        if output is not None:
            try:
                output.mkdir(parents=True,exist_ok=True)
                (output/('receipt-'+uuid4().hex+'.json')).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
            except OSError:
                result={'status':'failed','error_code':'native_resolution_receipt_write_failed'}
    print(json.dumps(result,sort_keys=True))
    return 130 if interrupted else 0 if result.get('status') in ('completed','preflight_passed') else 1


if __name__=='__main__':
    raise SystemExit(main())
