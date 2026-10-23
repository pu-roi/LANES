"""Pinned processing-only authority for the exact frozen historical workload."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.services.news_ner_durable.contracts import sha


def historical_code_identity() -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    names = ('app/services/news_historical_policy.py', 'app/services/news_historical_interpretation.py',
             'app/services/news_historical_processing.py', 'app/crud/news_historical_processing.py',
             'scripts/run_news_historical_processing.py')
    return {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names}


def expected_target_policy(package: object, trusted: object, engine: object, *,
                           resource_profile: str = 'local-strict-v1') -> dict:
    """Pure policy template; operators independently pin its canonical JSON hash."""
    from app.services.news_historical_processing import database_identity
    package.validate(); trusted.validate()
    from app.services.news_historical_processing import require
    require(resource_profile in {'local-strict-v1', 'cloud-run-v1'}, 'historical_resource_profile_invalid')
    if resource_profile == 'cloud-run-v1':
        require(package.manifest.get('policy', {}).get('archive_only') is True
            and len(package.captures) <= 2, 'historical_shared_archive_batch_required')
    return {'schema': 'lanes-historical-target-policy-v1',
        'parent_manifest_sha256': package.manifest_sha256,
        'dataset_id': package.manifest['dataset_id'],
        'demonstration_session_id': package.manifest['demonstration_session_id'],
        'target_database_identity_sha256': database_identity(engine),
        'confirmed_database': engine.url.database,
        'inputs': [{'article_id': c['article_id'], 'source_version_id': c['source_version_id'],
                    'native_input_fingerprint': c['native_input_fingerprint']} for c in package.captures],
        'assets_sha256': sha(trusted.manifest), 'pipeline_version': trusted.pipeline_version,
        'application_sha256': historical_code_identity(),
        'operations': ['enqueue_exact_native_captures', 'process_exact_native_runs', 'private_interpretation_receipts'],
        'publication_allowed': False, 'resource_profile': resource_profile}


@dataclass(frozen=True)
class HistoricalAuthorization:
    package: object
    trusted: object
    policy: dict
    policy_sha256: str

    def validate(self, engine: object) -> None:
        from app.services.news_historical_processing import database_identity, require
        from app.services.news_history_authority import valid_shared_connection
        require(sha(self.policy) == self.policy_sha256, 'historical_target_policy_changed')
        require(valid_shared_connection(engine),
                'historical_target_connection_invalid')
        require(database_identity(engine) == self.package.manifest['database_identity_sha256'],
                'historical_target_origin_required')
        require(sha(self.policy) == sha(expected_target_policy(self.package, self.trusted, engine,
            resource_profile=self.policy.get('resource_profile', 'local-strict-v1'))),
                'historical_target_policy_binding_mismatch')

    def validate_session(self, db: Session, run_ids: tuple[int, ...] | None = None,
                         sources: tuple | None = None) -> None:
        from app.models.news import NewsArticleVersion, NewsExtractionRun
        from app.services.news_historical_processing import require, inspect_sources
        self.validate(db.get_bind())
        require(db.scalar(text('SELECT current_database()')) == self.policy['confirmed_database'],
                'historical_database_confirmation_mismatch')
        # Recheck immutable legacy sources, selected sources/settings and native storage.
        blockers, _ = inspect_sources(db, self.package, self.trusted, sources)
        require(not blockers, 'historical_preflight_changed')
        if run_ids is not None:
            require(isinstance(run_ids, tuple) and len(run_ids) <= len(self.package.captures)
                    and all(type(i) is int and i > 0 for i in run_ids)
                    and len(set(run_ids)) == len(run_ids), 'historical_run_selection_invalid')
            rows = db.execute(select(NewsExtractionRun, NewsArticleVersion).join(NewsArticleVersion,
                NewsArticleVersion.id == NewsExtractionRun.article_version_id)
                .where(NewsExtractionRun.id.in_(run_ids))).all()
            captures = {(c['article_id'], c['native_input_fingerprint']): c['input_snapshot']
                        for c in self.package.captures}
            require(len(rows) == len(run_ids) and all(run.mode == 'ner_rules_v1'
                and run.pipeline_version == self.trusted.pipeline_version
                and captures.get((version.article_id, version.input_fingerprint)) == version.input_snapshot
                for run, version in rows), 'historical_run_selection_invalid')


def load_target_policy(path: Path, expected_sha256: str, package: object,
                       trusted: object, engine: object) -> HistoricalAuthorization:
    from app.services.news_historical_processing import read_document, require
    value = read_document(path)
    require(sha(value) == expected_sha256, 'historical_target_policy_hash_mismatch')
    authorization = HistoricalAuthorization(package, trusted, value, expected_sha256)
    authorization.validate(engine)
    return authorization
