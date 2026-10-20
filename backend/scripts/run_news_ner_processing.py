"""Internal C3a disposable-local worker; never a production activation switch."""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
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
    parser.add_argument('--article-id',type=int)
    args=parser.parse_args()
    try:
        return _run(args)
    except (KeyboardInterrupt,asyncio.CancelledError):
        print(json.dumps({'error_code':'ner_runtime_cancelled'}));return 130
    except Exception:
        print(json.dumps({'error_code':'ner_runtime_failed'}));return 1


def _run(args: argparse.Namespace) -> int:
    # Keep dependency loading inside main's boundary. Exception classes used by
    # the processing handlers below are not safe to reference until imports finish.
    from pydantic import ValidationError
    try:
        from app.services.news_ner_durable.processing import process_native_saved_news,require_local_target
        from app.services.news_ner_durable.assets import load_trusted_assets
        from app.services.news_ner_durable.contracts import NerEvidenceError
        from sqlalchemy import create_engine
        from sqlalchemy.exc import ArgumentError
        from sqlalchemy.orm import sessionmaker
    except ValidationError:
        print(json.dumps({'error_code':'ner_configuration_invalid'}));return 1
    engine=None
    try:
        url=os.environ.get('DATABASE_URL','');environment=os.environ.get('ENVIRONMENT','')
        require_local_target(environment,url)
        if platform.system()!='Linux':raise NerEvidenceError('ner_configuration_invalid')
        engine=create_engine(url,connect_args={'connect_timeout':5},pool_pre_ping=False)
        result=asyncio.run(process_native_saved_news(sessionmaker(bind=engine),environment=environment,database_url=url,
            load_assets=lambda:load_trusted_assets(args.bundle,args.bundle_sha256,expected_worker_code_sha256=args.worker_code_sha256),
            limit=args.limit,article_id=args.article_id))
        print(json.dumps(asdict(result)))
        return int(bool(result.error_code or result.failed or result.retry_wait or result.lease_lost))
    except NerEvidenceError as exc:
        print(json.dumps({'error_code':exc.code}));return 1
    except ArgumentError:
        print(json.dumps({'error_code':'ner_configuration_invalid'}));return 1
    except (KeyboardInterrupt,asyncio.CancelledError):
        print(json.dumps({'error_code':'ner_runtime_cancelled'}));return 130
    except Exception:
        print(json.dumps({'error_code':'ner_runtime_failed'}));return 1
    finally:
        if engine is not None:engine.dispose()


if __name__=='__main__':raise SystemExit(main())
