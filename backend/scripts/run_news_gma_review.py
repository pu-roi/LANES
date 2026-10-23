"""Restricted GMA review; no neural inference, activation or other articles."""
from __future__ import annotations

import asyncio
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_pilot_budget import GCSLedgerStore, PilotBudget
from app.services.news_three_article_pilot import PilotAuthority


def run_gma_review(args: object, release: dict) -> dict:
    from app.services.news_verified_cloud import assets_for_release, resolver_for_release, preflight
    from app.services.news_sources import load_news_sources
    from app.services.news_gma_review import archive_outputs
    if not args.authority_object or not args.authority_sha256:
        raise ResolutionError('gma_authority_required')
    document, _ = GCSLedgerStore('lanes-storage', args.authority_object).read()
    if (sha(document) != args.authority_sha256 or document.get('schema_version') != 'news-gma-review-v1'
            or document.get('release_sha256') != sha(release)
            or document.get('resolver') != release['resolver']
            or document.get('resolved_pipeline_version') != release['resolved_pipeline_version']):
        raise ResolutionError('gma_release_authority_changed')
    trusted = assets_for_release(release)
    authority = PilotAuthority(document, args.authority_sha256, trusted)
    engine = create_engine(settings.DATABASE_URL, hide_parameters=True, connect_args={'connect_timeout':5})
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    sources = load_news_sources()
    try:
        authority.validate(engine)
        if args.mode == 'gma-preflight':
            with factory() as db:
                authority.validate_session(db, (375,), sources, operation='resolve')
            resolver = resolver_for_release(release)
            # Retained response authentication is read-only and makes no provider call.
            from app.services.news_gemini_receipts import replay_bundle
            bundle = resolver.batch_plan.cache_loader()
            replay = replay_bundle(bundle, sha(bundle), config=resolver.config)
            if replay['status'] != 'evidence_references_passed':
                raise ResolutionError('gma_cached_evidence_changed')
            result = preflight(release, database_url=settings.DATABASE_URL)
            return {**result, 'cached_batch_authenticated':True,
                'parent_run_id':375, 'remaining_max_provider_requests':6,
                'remaining_reservation_nanodollars':255209400}
        if args.mode == 'gma-resolve':
            if args.run_id != [375]:
                raise ResolutionError('gma_parent_selection_changed')
            from app.services.news_ner_durable.resolution_worker import resolve_native_runs
            budget = PilotBudget(GCSLedgerStore('lanes-storage',
                os.environ['LANES_NEWS_PILOT_BUDGET_OBJECT']), os.environ['LANES_NEWS_PILOT_BUDGET_IDENTITY'])
            if (document['budget_identity'] != budget.identity
                    or document['budget_object'] != os.environ['LANES_NEWS_PILOT_BUDGET_OBJECT']):
                raise ResolutionError('gma_budget_binding_changed')
            resolver = resolver_for_release(release)
            resolver.budget = budget
            try:
                result = asyncio.run(resolve_native_runs(factory, (375,), trusted=trusted,
                    resolver=resolver, sources=sources, limit=1, pilot_authorization=authority))
            finally:
                budget.stop('gma_review_stage_finished')
            return {'status':'completed' if result['completed'] or result['reused'] else 'requires_attention', **result}
        if args.mode not in ('gma-preview','gma-archive') or len(args.run_id) != 1:
            raise ResolutionError('gma_archive_selection_invalid')
        result = archive_outputs(engine, authority, args.run_id[0], sources=sources, apply=args.mode == 'gma-archive')
        # Full previews are private immutable evidence, never source text in logs.
        from app.services.news_gemini_receipts import GCSReceiptStore
        store = GCSReceiptStore(os.environ['LANES_NEWS_RECEIPTS_PREFIX'])
        key = sha({'mode':args.mode, 'authority':args.authority_sha256, 'result':result})+'/archive-output.json'
        # The compatible projection is repeated on each DB evaluation. Retain
        # it once in the private receipt and pin the complete canonical result.
        projections = {sha(o['read_projection']):o['read_projection'] for o in result['outputs'] if 'read_projection' in o}
        receipt = {**result, 'canonical_result_sha256':sha(result), 'read_projections':projections,
            'outputs':[{**{k:v for k,v in o.items() if k!='read_projection'},
                **({'read_projection_sha256':sha(o['read_projection'])} if 'read_projection' in o else {})} for o in result['outputs']]}
        store.put(key, receipt)
        from collections import Counter
        return {'status':'completed', 'preview_only':args.mode == 'gma-preview',
            'outputs_sha256':result.get('outputs_sha256'), 'private_output_object':store.prefix+key,
            'group_count':len(result['outputs']),
            'outcomes':dict(Counter(o['outcome'] for o in result['outputs'])), 'active_instances_created':0}
    finally:
        engine.dispose()
