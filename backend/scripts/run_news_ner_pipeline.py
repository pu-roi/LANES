"""Internal disposable-local C3b pipeline. Never a production activation switch."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import platform


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--bundle-sha256',required=True)
    parser.add_argument('--worker-code-sha256',required=True)
    parser.add_argument('--limit',type=int,default=50)
    parser.add_argument('--verify-with-gemini',action='store_true',help='Use the existing Gemini key for an owned derived-run handoff')
    parser.add_argument('--gemini-model',help='Explicit Gemini model; required with --verify-with-gemini')
    args=parser.parse_args()
    try:
        result=_run(args)
    except (KeyboardInterrupt,asyncio.CancelledError):
        print(json.dumps({'error_code':'ner_runtime_cancelled'}));return 130
    except Exception:
        print(json.dumps({'error_code':'ner_runtime_failed'}));return 1
    print(json.dumps(result))
    return int(bool(result.get('error_code') or result.get('stop_reason')=='requires_attention'))


def _run(args: argparse.Namespace) -> dict:
    from pydantic import ValidationError
    try:
        from app.services.news_ner_durable.assets import load_trusted_assets,with_placement_assets
        from app.services.news_ner_durable.pipeline import run_native_news_pipeline
        from app.services.news_ner_durable.processing import require_local_target
        from app.services.news_ner_durable.contracts import NerEvidenceError
        from app.services.news_sources import load_news_sources
        from sqlalchemy import create_engine
        from sqlalchemy.exc import ArgumentError
        from sqlalchemy.orm import sessionmaker
    except ValidationError:
        return {'error_code':'ner_configuration_invalid'}
    engine=None
    try:
        url=os.environ.get('DATABASE_URL','');environment=os.environ.get('ENVIRONMENT','')
        require_local_target(environment,url)
        if platform.system()!='Linux':raise NerEvidenceError('ner_configuration_invalid')
        engine=create_engine(url,connect_args={'connect_timeout':5},pool_timeout=5,pool_pre_ping=False)
        resolver=None
        if args.verify_with_gemini:
            from dataclasses import replace
            from app.services.news_claim_auditor import AuditorConfig
            from app.services.news_ner_durable.gemini_resolution import GeminiResolver
            if not args.gemini_model:raise NerEvidenceError('ner_configuration_invalid')
            resolver=GeminiResolver(replace(AuditorConfig.from_environment(),provider='gemini',model=args.gemini_model))
        return asyncio.run(run_native_news_pipeline(sessionmaker(bind=engine),environment=environment,database_url=url,
            load_assets=lambda:with_placement_assets(load_trusted_assets(args.bundle,args.bundle_sha256,
                expected_worker_code_sha256=args.worker_code_sha256)),sources=load_news_sources(),limit=args.limit,resolver=resolver))
    except NerEvidenceError as exc:
        return {'error_code':exc.code}
    except ArgumentError:
        return {'error_code':'ner_configuration_invalid'}
    finally:
        if engine is not None:engine.dispose()


if __name__=='__main__':raise SystemExit(main())
