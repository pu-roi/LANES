"""Pinned manual cloud NER/Gemini release. Preflight never invokes a provider."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.services.news_claim_auditor import AuditorConfig
from app.services.news_historical_processing import database_identity
from app.services.news_ner_durable.assets import load_trusted_assets, with_placement_assets, with_resolution_assets
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.gemini_resolution import GeminiResolver
from app.services.news_ner_durable.resolution import ResolutionError


def release_file(path: Path, expected_sha256: str) -> dict:
    value = json.loads(path.read_text(encoding='utf-8'))
    if sha(value) != expected_sha256 or value.get('schema_version') != 'news-verified-cloud-release-v1':
        raise ResolutionError('verified_release_invalid')
    root = Path(__file__).resolve().parents[2]
    for name, digest in value['application_files'].items():
        file = (root/name).resolve()
        if not file.is_relative_to(root) or hashlib.sha256(file.read_bytes()).hexdigest() != digest:
            raise ResolutionError('verified_release_code_changed')
    return value


def resolver_for_release(release: dict) -> GeminiResolver:
    configured = replace(AuditorConfig.from_environment(), provider='gemini', model=release['resolver']['model'])
    batch_plan = None
    if 'inline_batch_manifest' in release:
        from app.services.news_gma_inline_continuation import InlineBatchPlan,CACHE_PINS
        from app.services.news_pilot_budget import GCSLedgerStore
        def cached_inline(index: int) -> dict:
            reference=release['inline_cache_references'][index]
            bundle,_=GCSLedgerStore('lanes-storage',reference['object']).read()
            pin=release['inline_batch_manifest']['adopted_bundle_sha256s'][index]
            if sha(bundle)!=pin or reference['sha256']!=pin:
                raise ResolutionError('inline_cached_evidence_changed')
            return bundle
        batch_plan=InlineBatchPlan(release['inline_batch_manifest'],cache_loader=cached_inline)
    elif 'heading_batch_manifest' in release:
        from app.services.news_gma_heading_repair import HeadingBatchPlan
        batch_plan = HeadingBatchPlan(release['heading_batch_manifest'])
    if 'gma_batch_manifest' in release:
        from app.services.news_gma_review import GmaBatchPlan, CACHE_PIN
        if release['gma_batch_manifest'].get('schema_version')=='gma-scoped-batches-v1':
            from app.services.news_gma_scoped_continuation import ScopedGmaBatchPlan as GmaBatchPlan, CACHE_PIN
        elif release['gma_batch_manifest'].get('schema_version')=='gma-budget-review-batches-v2':
            from app.services.news_gma_budget_review import GmaBudgetBatchPlan as GmaBatchPlan
        from app.services.news_pilot_budget import GCSLedgerStore
        def cached_bundle() -> dict:
            reference = release['gma_cache_reference']
            value, _ = GCSLedgerStore('lanes-storage', reference['object']).read()
            if sha(value) != reference['sha256'] or reference['sha256'] != CACHE_PIN:
                raise ResolutionError('gma_cached_evidence_changed')
            return value
        batch_plan = GmaBatchPlan(release['gma_batch_manifest'], cache_loader=cached_bundle)
    resolver_class = GeminiResolver
    if release['resolver'].get('request_serialization') == 'canonical-document-v1':
        from app.services.news_source_repair_resolver import SourceRepairResolver
        resolver_class = SourceRepairResolver
    resolver = resolver_class(configured, batch_plan=batch_plan,
        evidence_contract=release['resolver'].get('evidence_contract','quote-option-enum-v1'))
    if resolver.identity != release['resolver'] or configured.gemini_api_key.startswith('encrypted:'):
        raise ResolutionError('verified_resolver_configuration_mismatch')
    prefix = os.environ.get('LANES_NEWS_RECEIPTS_PREFIX')
    if prefix:
        from app.services.news_gemini_receipts import BatchJournal, GCSReceiptStore
        resolver.receipts = BatchJournal(GCSReceiptStore(prefix), secrets=(configured.gemini_api_key,))
    return resolver


def assets_for_release(release: dict) -> object:
    trusted = with_placement_assets(load_trusted_assets(Path(release['bundle']), release['bundle_sha256'],
        expected_worker_code_sha256=release['worker_code_sha256']))
    if sha(trusted.manifest) != release['base_assets_sha256']:
        raise ResolutionError('verified_assets_mismatch')
    if with_resolution_assets(trusted, release['resolver']).pipeline_version != release['resolved_pipeline_version']:
        raise ResolutionError('verified_projection_mismatch')
    return trusted


def preflight(release: dict, *, database_url: str) -> dict:
    """Exact cloud storage/reader/secret/resource readiness with read-only SQL."""
    trusted = assets_for_release(release)
    resolver = resolver_for_release(release)
    from app.services.news_native_read_context import configured_native_read_context
    reader = configured_native_read_context()
    if (reader is None or reader.pipeline_version != release['resolved_pipeline_version']
            or reader.fallback_pipeline_versions != tuple(release.get('reader_fallback_pipeline_versions', [trusted.pipeline_version]))):
        raise ResolutionError('verified_reader_configuration_mismatch')
    engine = create_engine(database_url, hide_parameters=True, connect_args={'connect_timeout':5}, pool_timeout=5)
    try:
        with Session(bind=engine) as session:
            db=session.connection(execution_options={'isolation_level':'REPEATABLE READ'})
            db.execute(text('SET TRANSACTION READ ONLY'))
            db.execute(text("SET LOCAL statement_timeout='5000'"))
            if (database_identity(engine) != release['database_identity_sha256']
                    or db.scalar(text('SELECT current_database()')) != release['confirmed_database']
                    or engine.url.database != release['confirmed_database']
                    or db.scalar(text('SELECT version_num FROM alembic_version')) != 'f1a9c7e2b604'
                    or not db.scalar(text('SELECT postgis_version()'))):
                raise ResolutionError('verified_storage_mismatch')
            reader.validate(session)
            flags = db.scalar(text("SELECT value->'settings' FROM system_settings WHERE key='operational_configuration_v1'"))
            if not all(flags.get(k) is False for k in (
                    'news_collection_enabled','news_processing_enabled','news_publication_enabled')):
                raise ResolutionError('verified_automation_not_paused')
            tables = ('news_articles','news_article_versions','news_extraction_runs',
                      'flood_events','flood_reports','flood_avoidance_zones','community_posts','users')
            counts = {name:db.scalar(text('SELECT count(*) FROM public.'+name)) for name in tables}
            if db.scalar(text('SHOW transaction_read_only')) != 'on':
                raise ResolutionError('verified_read_only_required')
        return {'status':'preflight_passed','database_read_only':True,'database_writes':0,
                'external_provider_requests':0,'credential_binding_configured':True,
                'provider_key_validity':'not_tested','provider_model_access':'not_tested',
                'model':resolver.identity['model'],'raw_pipeline_version':trusted.pipeline_version,
                'resolved_pipeline_version':release['resolved_pipeline_version'],'counts':counts,
                'provider_execution_enabled':os.environ.get('LANES_NEWS_GEMINI_EXECUTION_ENABLED')=='1'}
    finally:
        engine.dispose()


def require_provider_execution(release: dict, *, authority: Path | None, authority_sha256: str | None) -> None:
    """Deployment is not authorization to incur Gemini fees or seed data."""
    if os.environ.get('LANES_NEWS_GEMINI_EXECUTION_ENABLED') != '1':
        raise ResolutionError('verified_provider_execution_disabled')
    if authority is None or not authority_sha256:
        raise ResolutionError('native_resolution_authority_required')
