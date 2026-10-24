"""Exact-selection manual authority, separate from ordinary and archive workers."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from sqlalchemy import select, text

from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.configuration_service import read_configuration, selected_news_sources
from app.services.news_evaluation_service import source_is_approved
from app.services.news_historical_processing import database_identity
from app.services.news_history_authority import valid_shared_connection
from app.services.news_ner_durable.contracts import NativeInput, sha
from app.services.news_ner_durable.resolution import ResolutionError


def pilot_application_identity() -> str:
    root = Path(__file__).resolve().parents[2]
    return sha({p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for folder in ('app', 'scripts') for p in sorted((root/folder).rglob('*.py'))})


@dataclass(frozen=True)
class PilotAuthority:
    policy: dict
    policy_sha256: str
    trusted: object

    def validate(self, engine: object) -> None:
        engine = getattr(engine, 'engine', engine)
        p = self.policy
        if p.get('schema_version') == 'tribune-saved-article-pilot-v1':
            from app.services.news_tribune_pilot import validate_authority
            return validate_authority(self, engine)
        if p.get('schema_version') in ('gma-inline-continuation-v1','gma-inline-finalize-v1'):
            from app.services.news_gma_inline_continuation import validate_authority
            return validate_authority(self,engine)
        if p.get('schema_version') == 'gma-heading-repair-v1':
            from app.services.news_gma_heading_repair import validate_authority
            return validate_authority(self, engine)
        if p.get('schema_version') == 'gma-source-repair-v1':
            from app.services.news_source_repair import validate_authority
            return validate_authority(self, engine)
        if p.get('schema_version')=='news-gma-scoped-continuation-v1':
            from app.services.news_gma_scoped_continuation import validate_authority
            return validate_authority(self,engine)
        if p.get('schema_version')=='news-gma-budget-review-v2':
            from app.services.news_gma_budget_review import validate_authority
            return validate_authority(self,engine)
        if p.get('schema_version')=='news-gma-review-v1':
            from app.services.news_gma_review import validate_authority
            return validate_authority(self,engine)
        self.trusted.validate()
        if (sha(p) != self.policy_sha256 or p.get('schema_version') != 'news-three-article-pilot-v1'
                or p.get('application_sha256') != pilot_application_identity()
                or p.get('database_identity_sha256') != database_identity(engine)
                or p.get('confirmed_database') != engine.url.database or not valid_shared_connection(engine)
                or p.get('assets_sha256') != sha(self.trusted.manifest)
                or p.get('pipeline_version') != self.trusted.pipeline_version
                or p.get('resource_profile') != 'cloud-run-v1'
                or p.get('live_publication_allowed') is not False
                or p.get('allowed_operations') not in (['ner'], ['resolve'], ['outputs'])
                or not isinstance(p.get('session_id'), str) or not p['session_id']):
            raise ResolutionError('pilot_authority_mismatch')
        inputs = p.get('inputs', [])
        if (len(inputs) != 3 or len({i['article_id'] for i in inputs}) != 3
                or len({i['source_version_id'] for i in inputs}) != 3):
            raise ResolutionError('pilot_three_inputs_required')
        for item in inputs:
            source = NativeInput.model_validate(item['input_snapshot'])
            if (sha(item['input_snapshot']) != item['native_input_fingerprint']
                    or hashlib.sha256(source.article_text.encode()).hexdigest() != item['body_sha256']):
                raise ResolutionError('pilot_input_changed')

    def validate_session(self, db: object, run_ids: tuple[int, ...] | None = None,
                         sources: tuple | None = None, *, operation: str = 'ner') -> None:
        if self.policy.get('schema_version') == 'tribune-saved-article-pilot-v1':
            from app.services.news_tribune_pilot import validate_session
            return validate_session(self, db, run_ids, sources, operation)
        if self.policy.get('schema_version') in ('gma-inline-continuation-v1','gma-inline-finalize-v1'):
            from app.services.news_gma_inline_continuation import validate_session
            return validate_session(self,db,run_ids,sources,operation)
        if self.policy.get('schema_version') == 'gma-heading-repair-v1':
            from app.services.news_gma_heading_repair import validate_session
            return validate_session(self,db,run_ids,sources,operation)
        if self.policy.get('schema_version') == 'gma-source-repair-v1':
            from app.services.news_source_repair import validate_session
            return validate_session(self, db, run_ids, sources, operation)
        if self.policy.get('schema_version')=='news-gma-scoped-continuation-v1':
            from app.services.news_gma_scoped_continuation import validate_session
            return validate_session(self,db,run_ids,sources,operation)
        if self.policy.get('schema_version')=='news-gma-budget-review-v2':
            from app.services.news_gma_budget_review import validate_session
            return validate_session(self,db,run_ids,sources,operation)
        if self.policy.get('schema_version')=='news-gma-review-v1':
            from app.services.news_gma_review import validate_session
            return validate_session(self,db,run_ids,sources,operation)
        self.validate(db.get_bind())
        if self.policy['allowed_operations'] != [operation]:
            raise ResolutionError('pilot_operation_not_authorized')
        if (db.scalar(text('SELECT current_database()')) != self.policy['confirmed_database']
                or db.scalar(text('SELECT version_num FROM alembic_version')) != 'f1a9c7e2b604'
                or not db.scalar(text('SELECT postgis_version()'))):
            raise ResolutionError('pilot_storage_mismatch')
        config = read_configuration(db)
        if any(getattr(config, k) is not False for k in (
                'news_collection_enabled', 'news_processing_enabled', 'news_publication_enabled',
                'automatic_expiry_enabled', 'pasig_ml_expiry_enabled')):
            raise ResolutionError('pilot_paused_configuration_changed')
        selected = selected_news_sources(db, sources)
        for item in self.policy['inputs']:
            version = db.get(NewsArticleVersion, item['source_version_id'])
            source = NativeInput.model_validate(item['input_snapshot'])
            if (version is None or version.article_id != item['article_id']
                    or version.input_fingerprint != item['source_input_fingerprint']
                    or sha(version.input_snapshot) != item['source_input_fingerprint']
                    or version.input_snapshot['article_text'] != source.article_text):
                raise ResolutionError('pilot_original_source_changed')
            from app.services.news_source_read_service import require_current_pilot_capture
            require_current_pilot_capture(db, version)
            article = NewsArticleExtractorInput(article_id=item['article_id'],
                **source.model_dump(exclude={'capture_schema', 'publication_evidence'}))
            if not source_is_approved(article, selected):
                raise ResolutionError('pilot_source_suppressed')
        if run_ids is not None:
            if not 1 <= len(run_ids) <= 1 or len(set(run_ids)) != len(run_ids):
                raise ResolutionError('pilot_one_article_per_invocation')
            rows = db.execute(select(NewsExtractionRun, NewsArticleVersion).join(NewsArticleVersion)
                              .where(NewsExtractionRun.id.in_(run_ids))).all()
            inputs = {(i['article_id'], i['native_input_fingerprint']): i['input_snapshot']
                      for i in self.policy['inputs']}
            pipeline = (self.policy['resolved_pipeline_version'] if operation == 'outputs'
                        else self.policy['pipeline_version'])
            if len(rows) != len(run_ids) or any(r.mode != 'ner_rules_v1' or r.pipeline_version != pipeline
                    or inputs.get((v.article_id, v.input_fingerprint)) != v.input_snapshot for r, v in rows):
                raise ResolutionError('pilot_run_selection_changed')


def load_pilot_authority(path: Path, pin: str, trusted: object) -> PilotAuthority:
    from app.services.news_historical_processing import read_document
    value = read_document(path)
    if sha(value) != pin:
        raise ResolutionError('pilot_authority_changed')
    return PilotAuthority(value, pin, trusted)
