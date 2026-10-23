"""Frozen-input historical processing and qualification; never a publication switch."""
from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
import subprocess
from uuid import uuid4


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('preflight', 'process'))
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--confirm-database', required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--bundle-sha256', required=True)
    parser.add_argument('--worker-code-sha256', required=True)
    parser.add_argument('--assets-sha256', required=True)
    parser.add_argument('--receipt-directory', type=Path, required=True)
    parser.add_argument('--target-policy', type=Path)
    parser.add_argument('--target-policy-sha256')
    args = parser.parse_args()
    engine = None
    error_type = ()
    write_receipt = None
    private = None
    attempt = uuid4().hex
    result = {'mode': args.mode, 'status': 'failed', 'error_code': 'historical_processing_failed',
              'database_writes_performed': False}
    try:
        from app.services.news_historical_preparation import PreparationError
        error_type = PreparationError
        from app.services.news_historical_processing import (load_historical_package, preflight_historical,
            process_historical, save_attempt, require)
        root = Path(__file__).resolve().parents[2]
        private = args.receipt_directory.resolve()
        require(private.is_relative_to(root/'data') and private != root/'data'
            and not private.is_relative_to(args.manifest.resolve().parent), 'historical_private_receipts_required')
        ignored = subprocess.run(['git', 'check-ignore', '--quiet', '--', str(private)],
                                 cwd=root, capture_output=True, check=False)
        require(ignored.returncode == 0, 'historical_ignored_receipts_required')
        write_receipt = save_attempt
        require(all(re.fullmatch(r'[a-f0-9]{64}', value) for value in (args.manifest_sha256,
            args.bundle_sha256, args.worker_code_sha256, args.assets_sha256)), 'historical_hash_argument_invalid')
        result['parent_manifest_sha256'] = args.manifest_sha256
        result['requested_assets_sha256'] = args.assets_sha256
        package = load_historical_package(args.manifest, args.manifest_sha256)
        from app.services.news_ner_durable.assets import load_trusted_assets, with_placement_assets
        trusted = with_placement_assets(load_trusted_assets(args.bundle.resolve(), args.bundle_sha256,
            expected_worker_code_sha256=args.worker_code_sha256))
        from app.core.config import settings
        from sqlalchemy import create_engine
        engine = create_engine(settings.DATABASE_URL, connect_args={'connect_timeout': 5}, pool_timeout=5,
                               pool_pre_ping=False)
        options = dict(assets_sha256=args.assets_sha256, confirmed_database=args.confirm_database,
                       environment=settings.ENVIRONMENT)
        require(bool(args.target_policy) == bool(args.target_policy_sha256), 'historical_target_policy_arguments_invalid')
        if args.target_policy:
            require(bool(re.fullmatch(r'[a-f0-9]{64}', args.target_policy_sha256)), 'historical_hash_argument_invalid')
            from app.services.news_historical_policy import load_target_policy
            options['authorization'] = load_target_policy(args.target_policy, args.target_policy_sha256,
                                                         package, trusted, engine)
        if args.mode == 'preflight':
            result = preflight_historical(engine, package, trusted, **options)
        else:
            result['database_writes_performed'] = None  # Unknown until execution returns its durable result.
            result = asyncio.run(process_historical(engine, package, trusted, **options))
    except (KeyboardInterrupt, asyncio.CancelledError):
        result.update(status='interrupted', error_code='ner_runtime_cancelled')
    except Exception as exc:
        result.update(status='failed', error_code=str(exc) if isinstance(exc, error_type) else 'historical_processing_failed')
    finally:
        if engine is not None:
            engine.dispose()
    if write_receipt is not None:
        try:
            write_receipt(private, result, attempt)
        except Exception:
            result.update(status='failed', receipt_error_code='historical_receipt_write_failed')
    # Large asset/source documents are private; stdout is bounded status only.
    public = {key: value for key, value in result.items()
              if key not in {'execution_manifest', 'historical_interpretations'}}
    public['attempt_id'] = attempt
    print(json.dumps(public, ensure_ascii=False, allow_nan=False))
    return 130 if result['status'] == 'interrupted' else 0 if result['status'] in ('ready', 'completed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
