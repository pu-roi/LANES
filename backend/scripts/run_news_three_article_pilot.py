"""Manual pilot operations; called only by the supervised verified cloud worker."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import asyncio
import json
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_three_article_pilot import PilotAuthority
from app.services.news_pilot_budget import GCSLedgerStore, PilotBudget


def run_pilot(args: object, release: dict) -> dict:
    from app.services.news_verified_cloud import assets_for_release, resolver_for_release
    from app.services.news_sources import load_news_sources
    if not args.authority_object or not args.authority_sha256:
        raise ResolutionError('pilot_authority_required')
    document, _ = GCSLedgerStore('lanes-storage', args.authority_object).read()
    if sha(document) != args.authority_sha256:
        raise ResolutionError('pilot_authority_changed')
    trusted = assets_for_release(release)
    authority = PilotAuthority(document, args.authority_sha256, trusted)
    if document['resolver'] != release['resolver'] or document['resolved_pipeline_version'] != release['resolved_pipeline_version']:
        raise ResolutionError('pilot_release_changed')
    engine = create_engine(settings.DATABASE_URL, hide_parameters=True, connect_args={'connect_timeout': 5})
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    sources = load_news_sources()
    try:
        authority.validate(engine)
        if args.mode == 'pilot-ner':
            from app.crud.news_historical_processing import enqueue_historical_captures
            from app.services.news_ner_durable.processing import process_native_saved_news
            selected = [i for i in document['inputs'] if i['article_id'] == args.article_id]
            if len(selected) != 1:
                raise ResolutionError('pilot_article_selection_invalid')
            with factory() as db, db.begin():
                authority.validate_session(db, sources=sources)
                ids = enqueue_historical_captures(db, tuple(selected), trusted.pipeline_version)
            result = asyncio.run(process_native_saved_news(factory, load_assets=lambda: trusted,
                environment=settings.ENVIRONMENT, database_url=settings.DATABASE_URL,
                limit=1, run_ids=ids, sources=sources, historical_authorization=authority))
            return {'status': 'completed' if result.completed or result.stop_reason == 'no_work' else 'requires_attention',
                    'ner': asdict(result), 'run_ids': ids}
        if len(args.run_id) != 1:
            raise ResolutionError('pilot_one_article_per_invocation')
        if args.mode == 'pilot-resolve':
            from app.services.news_ner_durable.resolution_worker import resolve_native_runs
            budget = PilotBudget(GCSLedgerStore('lanes-storage',
                os.environ['LANES_NEWS_PILOT_BUDGET_OBJECT']), os.environ['LANES_NEWS_PILOT_BUDGET_IDENTITY'])
            if (document['budget_identity'] != budget.identity
                    or document['budget_object'] != os.environ['LANES_NEWS_PILOT_BUDGET_OBJECT']):
                raise ResolutionError('pilot_budget_binding_changed')
            resolver = resolver_for_release(release)
            resolver.budget = budget
            result = asyncio.run(resolve_native_runs(factory, tuple(args.run_id), trusted=trusted,
                resolver=resolver, sources=sources, limit=1, pilot_authorization=authority))
            return {'status': 'completed' if result['completed'] or result['reused'] else 'requires_attention', **result}
        from app.services.news_pilot_outputs import pilot_outputs
        result = pilot_outputs(engine, authority, args.run_id[0], sources=sources,
                               apply=args.mode == 'pilot-apply')
        if result['status'] == 'preview':
            result.update(status='completed', preview_only=True)
        return result
    finally:
        engine.dispose()
