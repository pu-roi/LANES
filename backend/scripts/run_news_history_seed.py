"""Manual archive-only Cloud Run worker over pinned retained full articles.

No discovery, retrieval, scheduled processing, active instances or public API.
Private inputs stay in the image/database; stdout contains bounded audit receipts.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from uuid import uuid4


def emit(stage: str, result: dict) -> None:
    from app.services.news_ner_durable.contracts import sha
    public = {k: v for k, v in result.items() if k not in (
        'execution_manifest', 'historical_interpretations', 'selection', 'outputs')}
    public['receipt_sha256'] = sha(result)
    if 'outputs' in result:
        public['outputs'] = [{k: o.get(k) for k in ('article_id', 'run_id', 'group_id',
            'outcome', 'reasons', 'event_id', 'zone_ids', 'reused_existing_event')} for o in result['outputs']]
    print(json.dumps({'schema': 'news-history-seed-receipt-v1', 'stage': stage,
        'attempt_id': os.environ.get('CLOUD_RUN_EXECUTION', uuid4().hex), **public},
        allow_nan=False, default=str), flush=True)


def package_for_versions(engine: object, trusted: object, versions: tuple[int, ...], dataset: str):
    from app.crud.news_historical_preparation import read_preparation_inventory
    from app.services.news_historical_preparation import SourceSpec, build_preparation, text_sha
    from app.services.news_historical_processing import HistoricalPackage, require
    from app.services.news_ner_durable.contracts import sha
    require(1 <= len(versions) <= 2, 'historical_shared_archive_batch_required')
    inventory = read_preparation_inventory(engine, engine.url.database, version_ids=versions)
    require(len(inventory['sources']) == len(versions), 'historical_selected_version_missing')
    specs = tuple(SourceSpec(r['article_id'], r['version_id'], r['input_fingerprint'],
        text_sha(r['input_snapshot']['article_text']), r['input_snapshot']['canonical_url'],
        r['input_snapshot']['publisher'], r['input_snapshot']['published_at']) for r in inventory['sources'])
    documents = build_preparation(inventory, {'manifest': trusted.manifest,
        'manifest_sha256': sha(trusted.manifest), 'pipeline_version': trusted.pipeline_version,
        'preparation_code_sha256': sha(__import__('app.services.news_historical_policy',
            fromlist=['historical_code_identity']).historical_code_identity())},
        specs=specs, candidates=(), dataset_id=dataset)
    return HistoricalPackage(sha(documents['manifest.json']), documents)


def execute(config: dict, mode: str, batch: int) -> dict:
    from sqlalchemy import create_engine, select, text
    from app.core.config import settings
    from app.models.news import NewsArticleVersion
    from app.services.news_historical_processing import database_identity, require, read_document, process_historical, preflight_historical
    from app.services.news_ner_durable.assets import load_trusted_assets, with_placement_assets
    from app.services.news_ner_durable.contracts import sha
    from app.services.news_history_authority import load_archive_authority
    from app.services.news_history_capture_registration import register_captures
    from app.services.news_history_protection import protected_fingerprints, verify_protected
    from app.crud.news_historical_processing import readonly_historical_session
    require(os.environ.get('CLOUD_RUN_TASK_ATTEMPT', '0') == '0'
        and os.environ.get('CLOUD_RUN_TASK_COUNT', '1') == '1'
        and os.environ.get('CLOUD_RUN_TASK_INDEX', '0') == '0', 'historical_single_attempt_required')
    engine = create_engine(settings.DATABASE_URL, connect_args={'connect_timeout': 8}, pool_timeout=8)
    try:
        require(database_identity(engine) == config['database_identity_sha256']
            and engine.url.database == config['confirmed_database'], 'historical_seed_target_mismatch')
        with readonly_historical_session(engine, engine.url.database) as db:
            before = protected_fingerprints(db)
        if mode == 'inspect':
            with readonly_historical_session(engine, engine.url.database) as db:
                return {'status': 'ready', 'read_only': True, 'baseline': before,
                    'revision': db.scalar(text('SELECT version_num FROM alembic_version'))}
        trusted = with_placement_assets(load_trusted_assets(Path('/assets'), config['bundle_sha256'],
            expected_worker_code_sha256=config['worker_code_sha256']))
        require(sha(trusted.manifest) == config['assets_sha256'], 'historical_seed_assets_changed')
        if mode == 'register':
            captures = read_document(Path('/seed/training-captures.json'))['captures']
            authority = load_archive_authority(Path('/seed/registration-authority.json'), config['registration_authority_sha256'])
            result = register_captures(engine, captures, captures_sha256=config['captures_sha256'],
                target_sha256=config['database_identity_sha256'], confirmed_database=engine.url.database,
                environment=settings.ENVIRONMENT, apply=True, authorization=authority)
            result.pop('selection', None)
        else:
            require(0 <= batch < len(config['batches']), 'historical_seed_batch_invalid')
            selected = config['batches'][batch]
            from app.services.news_historical_processing import load_historical_package
            package = load_historical_package(Path('/seed')/selected['package']/'manifest.json', selected['manifest_sha256'])
            require(len(package.captures) <= 2 and package.manifest.get('policy', {}).get('archive_only') is True,
                'historical_shared_archive_batch_required')
            from app.services.news_historical_policy import load_target_policy
            authorization = load_target_policy(Path('/seed')/selected['processing_policy'],
                selected['processing_policy_sha256'], package, trusted, engine)
            options = dict(assets_sha256=config['assets_sha256'], confirmed_database=engine.url.database,
                environment=settings.ENVIRONMENT, authorization=authorization)
            if mode in ('preflight', 'process', 'batch'):
                result = (preflight_historical(engine, package, trusted, **options) if mode == 'preflight'
                    else asyncio.run(process_historical(engine, package, trusted, **options)))
                if mode == 'batch':
                    emit('process', result)
                    if result['status'] != 'completed':
                        return result
            if mode in ('preview', 'apply', 'batch'):
                from app.services.news_historical_outputs import historical_outputs
                output_policy = read_document(Path('/seed')/selected['output_policy'])
                authority = load_archive_authority(Path('/seed')/selected['output_authority'], selected['output_authority_sha256'])
                if mode == 'batch':
                    preview = historical_outputs(engine, package, trusted, policy=output_policy,
                        policy_sha256=selected['output_policy_sha256'], confirmed_database=engine.url.database,
                        environment=settings.ENVIRONMENT, apply=False, authorization=authority)
                    emit('preview', preview)
                result = historical_outputs(engine, package, trusted, policy=output_policy,
                    policy_sha256=selected['output_policy_sha256'], confirmed_database=engine.url.database,
                    environment=settings.ENVIRONMENT, apply=mode in ('apply', 'batch'), authorization=authority)
            result['batch'] = batch
            result['parent_manifest_sha256'] = package.manifest_sha256
        with readonly_historical_session(engine, engine.url.database) as db:
            verify_protected(before, protected_fingerprints(db))
        result['protected_existing_rows_unchanged'] = True
        return result
    finally:
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('inspect', 'register', 'preflight', 'process', 'preview', 'apply', 'batch'))
    parser.add_argument('--batch', type=int, default=0)
    parser.add_argument('--config', type=Path, default=Path('/seed/config.json'))
    parser.add_argument('--config-sha256', required=True)
    args = parser.parse_args()
    try:
        from app.services.news_historical_processing import read_document, require
        from app.services.news_ner_durable.contracts import sha
        config = read_document(args.config)
        require(sha(config) == args.config_sha256, 'historical_seed_config_changed')
        result = execute(config, args.mode, args.batch)
        result.setdefault('status', 'completed' if result.get('database_writes_performed') else 'ready')
        emit(args.mode, result)
        return 0 if result['status'] in ('ready', 'completed') else 1
    except Exception as exc:
        from app.services.news_historical_preparation import PreparationError
        emit(args.mode, {'status': 'failed', 'error_code': str(exc) if isinstance(exc, PreparationError)
            else 'historical_seed_failed', 'error_type': type(exc).__name__})
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
