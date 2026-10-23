"""GMA shared-depth archive commands: no provider or inference dispatch."""
from __future__ import annotations

from collections import Counter
import os
from uuid import uuid4

from sqlalchemy import create_engine

from app.core.config import settings
from app.services.news_gma_shared_history import SharedHistoryAuthority, VERSION, archive_outputs
from app.services.news_gemini_receipts import GCSReceiptStore
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_pilot_budget import GCSLedgerStore


def run_shared_history(args: object, release: dict) -> dict:
    from app.services.news_verified_cloud import preflight, assets_for_release
    from app.services.news_gma_scoped_budget import effective_commitment
    from app.services.news_gma_scoped_continuation import batch_manifest
    if args.mode not in ('gma-shared-preview', 'gma-shared-archive') or args.run_id != [380]:
        raise ResolutionError('shared_history_command_invalid')
    p, _ = GCSLedgerStore('lanes-storage', args.authority_object).read()
    if (sha(p) != args.authority_sha256 or p.get('schema_version') != VERSION
            or p.get('release_sha256') != sha(release) or p.get('resolver') != release['resolver']
            or p.get('receipts_prefix') != os.environ.get('LANES_NEWS_RECEIPTS_PREFIX')
            or p.get('historical_depth_policy') != release.get('shared_history_policy')):
        raise ResolutionError('shared_history_release_authority_changed')
    ledger = GCSLedgerStore('lanes-storage', p['budget_object'])
    before, _ = ledger.read()
    if (sha(before) != p['ledger_baseline_sha256'] or before['status'] != 'stopped'
            or len(before['attempts']) != 36 or any(a['status'] == 'in_flight' for a in before['attempts'])
            or effective_commitment(before, batch_manifest()['accounting_extension']) != 731_469_600):
        raise ResolutionError('shared_history_ledger_changed')
    journal = GCSReceiptStore(p['receipts_prefix'])
    key = sha({'authority_sha256': sha(p), 'mode': args.mode, 'invocation': str(uuid4())})
    journal.put(key + '/archive-intent.json', {'schema_version': VERSION, 'mode': args.mode,
        'authority_sha256': sha(p), 'release_sha256': sha(release), 'run_id': 380,
        'ledger_sha256': sha(before), 'provider_requests_permitted': 0})
    preflight(release, database_url=settings.DATABASE_URL)
    authority = SharedHistoryAuthority(p, sha(p), assets_for_release(release))
    engine = create_engine(settings.DATABASE_URL, hide_parameters=True,
        connect_args={'connect_timeout': 5}, pool_timeout=5)
    try:
        result = archive_outputs(engine, authority, apply=args.mode == 'gma-shared-archive')
        after, _ = ledger.read()
        if after != before:
            raise ResolutionError('shared_history_ledger_changed')
        projections = {sha(o['read_projection']): o['read_projection'] for o in result['outputs']
            if 'read_projection' in o}
        private = {**result, 'canonical_result_sha256': sha(result), 'read_projections': projections,
            'outputs': [{**{k: v for k, v in o.items() if k != 'read_projection'},
                **({'read_projection_sha256': sha(o['read_projection'])} if 'read_projection' in o else {})}
                for o in result['outputs']]}
        journal.put(key + '/archive-output.json', private)
        return {'status': 'completed', 'outputs_sha256': result.get('outputs_sha256'),
            'private_output_object': p['receipts_prefix'] + key + '/archive-output.json',
            'group_count': len(result['outputs']), 'outcomes': dict(Counter(o['outcome'] for o in result['outputs'])),
            'active_instances_created': 0, 'provider_requests': 0, 'ner_requests': 0,
            'database_writes': result['database_writes'], 'ledger_unchanged_stopped': True}
    except Exception as error:
        journal.put(key + '/archive-failure.json', {'schema_version': VERSION,
            'error_type': type(error).__name__,
            'error_code': error.code if isinstance(error, ResolutionError) else 'shared_history_stage_failed',
            'database_commit': 'inspect_durable_database_evidence_before_resuming', 'provider_requests': 0})
        raise
    finally:
        engine.dispose()
