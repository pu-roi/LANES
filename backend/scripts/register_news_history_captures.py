"""Preflight or register pinned complete training captures on disposable storage."""
import argparse
import json
from pathlib import Path


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures',type=Path,required=True)
    parser.add_argument('--captures-sha256',required=True)
    parser.add_argument('--target-sha256',required=True)
    parser.add_argument('--confirm-database',required=True)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--shared-policy', type=Path)
    parser.add_argument('--shared-policy-sha256')
    args=parser.parse_args()
    from sqlalchemy import create_engine
    from app.core.config import settings
    from app.services.news_historical_processing import read_document
    from app.services.news_history_capture_registration import register_captures
    value=read_document(args.captures)
    captures=value['captures']
    engine=create_engine(settings.DATABASE_URL,connect_args={'connect_timeout':8})
    try:
        from app.services.news_historical_processing import require
        require(bool(args.shared_policy) == bool(args.shared_policy_sha256), 'historical_shared_arguments_invalid')
        options = {}
        if args.shared_policy:
            from app.services.news_history_authority import load_archive_authority
            options['authorization'] = load_archive_authority(args.shared_policy, args.shared_policy_sha256)
        result=register_captures(engine,captures,captures_sha256=args.captures_sha256,
            target_sha256=args.target_sha256,confirmed_database=args.confirm_database,
            environment=settings.ENVIRONMENT,apply=args.apply, **options)
        # The review names identities/outcomes; publisher bodies stay private.
        print(json.dumps({**result,'selection':[{k:v for k,v in row.items() if k!='snapshot'} for row in result['selection']]}))
    finally:
        engine.dispose()
    return 0


if __name__=='__main__':
    raise SystemExit(main())
