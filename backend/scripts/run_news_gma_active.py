"""Manual zero-provider active-only preview/apply, with private immutable receipts."""
from __future__ import annotations

import os
from uuid import uuid4

from sqlalchemy import create_engine

from app.core.config import settings
from app.services.news_gemini_receipts import GCSReceiptStore
from app.services.news_gma_active_outputs import active_outputs, require
from app.services.news_ner_durable.assets import with_resolution_assets
from app.services.news_ner_durable.contracts import sha
from app.services.news_pilot_budget import GCSLedgerStore


def run_active(args: object, release: dict) -> dict:
    from app.services.news_verified_cloud import preflight, assets_for_release
    require(bool(args.authority_object and args.authority_sha256) and args.run_id == [388],
            'gma_active_authority_required')
    authority, _ = GCSLedgerStore('lanes-storage', args.authority_object).read()
    require(sha(authority) == args.authority_sha256 and authority.get('release_sha256') == sha(release)
        and authority.get('receipts_prefix') == os.environ.get('LANES_NEWS_RECEIPTS_PREFIX'), 'gma_active_release_changed')
    ledger = GCSLedgerStore('lanes-storage', authority['budget_object'])
    before, generation = ledger.read()
    require(before['status'] == 'stopped' and len(before['attempts']) == 42
        and sha(before) == authority['stopped_ledger_sha256'], 'gma_active_ledger_changed')
    preflight(release, database_url=settings.DATABASE_URL)
    trusted = with_resolution_assets(assets_for_release(release), release['resolver'])
    placement = None
    from app.services.news_gma_active_outputs import CONNECTED_VERSION
    if authority.get('schema_version') == CONNECTED_VERSION:
        from pathlib import Path
        from app.services.news_connected_road_service import ConnectedRoadService
        from app.services.news_road_placement_service import DEFAULT_CATALOG_DIR
        from app.services.noah_vector_catalog_service import DEFAULT_DIRECTORY
        feature_path = Path(release['connected_road_feature_path'])
        require(feature_path.is_absolute() and str(feature_path).startswith('/release/'),
                'gma_active_feature_path_invalid')
        placement = ConnectedRoadService(DEFAULT_CATALOG_DIR, DEFAULT_DIRECTORY,
            feature_path=feature_path, feature_sha256=release['connected_road_feature_sha256'])
        # Authenticate the untouched result with its original resolved assets.
        # The separately pinned spatial policy derives output, not a new extraction.
        require(authority['saved_assets_sha256'] == sha(trusted.manifest), 'gma_active_original_assets_changed')
    journal = GCSReceiptStore(authority['receipts_prefix'])
    key = sha({'authority': args.authority_sha256, 'invocation': str(uuid4())})
    journal.put(key + '/stage-intent.json', {'schema_version': authority['schema_version'],
        'authority_sha256': args.authority_sha256, 'provider_requests_allowed': 0, 'mode': args.mode})
    engine = create_engine(settings.DATABASE_URL, hide_parameters=True, connect_args={'connect_timeout': 5})
    try:
        result = active_outputs(engine, authority, args.authority_sha256, trusted,
                                apply=args.mode == 'gma-active-apply', placement_service=placement)
        require(ledger.read() == (before, generation), 'gma_active_spending_changed')
        journal.put(key + '/stage-output.json', result)
        return {'status': 'completed', 'stage': result['stage'], 'provider_requests': 0,
                'private_output_object': authority['receipts_prefix'] + key + '/stage-output.json',
                'result_sha256': sha(result), 'all_three_qualified': result.get('all_three_qualified')}
    finally:
        engine.dispose()
