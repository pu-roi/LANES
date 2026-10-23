"""Qualify/apply saved historical outputs on an owned disposable local target."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from uuid import uuid4


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('preflight', 'apply'))
    for name in ('manifest', 'output-policy', 'bundle', 'receipt-directory'):
        parser.add_argument('--'+name, type=Path, required=True)
    for name in ('manifest-sha256', 'output-policy-sha256', 'bundle-sha256', 'worker-code-sha256', 'confirm-database'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--shared-policy', type=Path)
    parser.add_argument('--shared-policy-sha256')
    args = parser.parse_args()
    engine = None
    try:
        from app.core.config import settings
        from sqlalchemy import create_engine
        from app.services.news_historical_processing import load_historical_package, read_document, require
        from app.services.news_historical_preparation import PreparationError
        from app.services.news_ner_durable.assets import load_trusted_assets, with_placement_assets
        from app.services.news_historical_outputs import historical_outputs
        package = load_historical_package(args.manifest, args.manifest_sha256)
        trusted = with_placement_assets(load_trusted_assets(args.bundle, args.bundle_sha256,
            expected_worker_code_sha256=args.worker_code_sha256))
        root = Path(__file__).resolve().parents[2]
        private = args.receipt_directory.resolve()
        require(private.is_relative_to(root/'data') and private != root/'data'
            and not private.is_relative_to(args.manifest.resolve().parent), 'historical_private_receipts_required')
        require(subprocess.run(['git', 'check-ignore', '--quiet', '--', str(private)], cwd=root,
            capture_output=True).returncode == 0, 'historical_ignored_receipts_required')
        engine = create_engine(settings.DATABASE_URL, connect_args={'connect_timeout': 5}, pool_timeout=5)
        require(bool(args.shared_policy) == bool(args.shared_policy_sha256), 'historical_shared_arguments_invalid')
        options = {}
        if args.shared_policy:
            from app.services.news_history_authority import load_archive_authority
            options['authorization'] = load_archive_authority(args.shared_policy, args.shared_policy_sha256)
        result = historical_outputs(engine, package, trusted, policy=read_document(args.output_policy),
            policy_sha256=args.output_policy_sha256, confirmed_database=args.confirm_database,
            environment=settings.ENVIRONMENT, apply=args.mode == 'apply', **options)
        private.mkdir(parents=True, exist_ok=True)
        with (private/('output-'+uuid4().hex+'.json')).open('x', encoding='utf-8') as stream:
            json.dump(result, stream, ensure_ascii=False, allow_nan=False)
        print(json.dumps({'status': result['status'], 'outputs': len(result['outputs']),
            'outcomes': [o['outcome'] for o in result['outputs']],
            'database_writes_performed': result['database_writes_performed']}))
        return 0
    except Exception as exc:
        from app.services.news_historical_preparation import PreparationError
        print(json.dumps({'status': 'failed', 'error_code': str(exc) if isinstance(exc, PreparationError)
            else 'historical_output_failed'}))
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == '__main__':
    raise SystemExit(main())
