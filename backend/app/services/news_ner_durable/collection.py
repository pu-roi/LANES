"""Explicit local native discovery identity and body-bound feed provenance."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .assets import TrustedAssets
from .contracts import NerEvidenceError, PublicationEvidence


@dataclass(frozen=True)
class NativeCollectionContext:
    trusted: TrustedAssets
    environment: str
    database_url: str

    @property
    def pipeline_version(self) -> str:
        return self.trusted.pipeline_version

    def validate(self, db: Session) -> None:
        from .processing import require_local_target
        require_local_target(self.environment, self.database_url)
        self.trusted.validate()
        from sqlalchemy.engine import make_url
        if (db.get_bind().dialect.name != 'postgresql'
                or db.scalar(text('SELECT current_database()')) != make_url(self.database_url).database):
            raise NerEvidenceError('ner_configuration_invalid')


def body_binding(article: object) -> dict:
    published = article.published_at
    if published is not None:
        from datetime import timezone
        published = (published.replace(tzinfo=timezone.utc) if published.utcoffset() is None else published).astimezone(timezone.utc).isoformat()
    return {'title': article.title, 'excerpt': article.excerpt or '', 'published_at': published,
            'publisher': article.publisher_source_id,
            'body_sha256': hashlib.sha256((article.article_text or '').encode('utf-8')).hexdigest()}


def require_native_storage(db: Session) -> None:
    from app.core.config import settings
    from .processing import require_local_target
    require_local_target(settings.ENVIRONMENT, db.get_bind().url.render_as_string(hide_password=False))
    if (db.get_bind().dialect.name != 'postgresql'
            or db.scalar(text('SELECT current_database()')) != db.get_bind().url.database):
        raise NerEvidenceError('ner_configuration_invalid')


def entry_publication(entry: object) -> PublicationEvidence:
    raw = entry.publication_raw
    return PublicationEvidence(raw=raw, timezone_known=entry.publication_timezone_known,
                               basis='publisher_feed') if raw is not None else PublicationEvidence()


def saved_publication(db: Session, article: object) -> PublicationEvidence:
    from app.models.news import NewsArticleFeedEntry
    binding = body_binding(article)
    values = []
    for metadata in db.scalars(select(NewsArticleFeedEntry.raw_metadata).where(
            NewsArticleFeedEntry.article_id == article.id,
            NewsArticleFeedEntry.source_id == article.publisher_source_id).order_by(NewsArticleFeedEntry.id)):
        captured = (metadata or {}).get('captured_input', {})
        if captured.get('binding') == binding:
            try:
                values.append(PublicationEvidence.model_validate(captured['publication_evidence']))
            except (ValueError, KeyError, TypeError) as exc:
                raise NerEvidenceError('ner_input_binding_invalid') from exc
    # Different feeds can express the same publisher instant in RFC/ISO forms.
    # Retain the oldest matching explicit proof rather than downgrade it because
    # its wording differs. NativeInput independently checks raw/time agreement.
    known = [value for value in values if value.timezone_known]
    return known[0] if known else values[0] if values else PublicationEvidence()


def had_native_flood_evidence(db: Session, article_id: int, trusted: TrustedAssets) -> bool:
    """A bound saved result, never an unverified JSON manifest authenticating itself."""
    from app.models.news import NewsArticleVersion, NewsExtractionRun
    from .adapter import verify_saved_result
    from .contracts import RunEvidence
    rows = db.execute(select(NewsExtractionRun, NewsArticleVersion).join(NewsArticleVersion).where(
        NewsArticleVersion.article_id == article_id, NewsExtractionRun.mode == 'ner_rules_v1',
        NewsExtractionRun.pipeline_version == trusted.pipeline_version,
        NewsExtractionRun.status == 'completed').order_by(NewsExtractionRun.id.desc()))
    for run, version in rows:
        result = verify_saved_result(RunEvidence.from_records(run, version), run.result, trusted)
        if result.claims:
            return True
    return False
