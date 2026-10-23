"""Hash-pinned saved-result selection; does not enable collection or inference."""
from dataclasses import dataclass
import os
from pathlib import Path

from sqlalchemy import text
from app.services.news_historical_processing import read_document, database_identity
from app.services.news_ner_durable.contracts import sha
from app.services.news_processing_identity import validate_processing_identity


@dataclass(frozen=True)
class SavedNativeReadContext:
    pipeline_version: str
    database_identity_sha256: str
    fallback_pipeline_versions: tuple[str, ...] = ()

    @property
    def pipeline_selection(self) -> str | tuple[str, ...]:
        return (self.pipeline_version,*self.fallback_pipeline_versions) if self.fallback_pipeline_versions else self.pipeline_version

    def validate(self, db: object) -> None:
        validate_processing_identity('ner_rules_v1', self.pipeline_version)
        if len(self.fallback_pipeline_versions)>8 or len(set((self.pipeline_version,*self.fallback_pipeline_versions)))!=1+len(self.fallback_pipeline_versions):
            raise ValueError('news_native_reader_unavailable')
        for version in self.fallback_pipeline_versions:
            validate_processing_identity('ner_rules_v1',version)
        if (db.get_bind().dialect.name != 'postgresql'
                or database_identity(db.get_bind()) != self.database_identity_sha256
                or db.scalar(text('SELECT current_database()')) != db.get_bind().url.database):
            raise ValueError('news_native_reader_unavailable')


def configured_native_read_context() -> SavedNativeReadContext | None:
    path = os.environ.get('LANES_NEWS_NATIVE_READ_CONTEXT')
    pin = os.environ.get('LANES_NEWS_NATIVE_READ_CONTEXT_SHA256')
    if not path and not pin:
        return None
    from app.services.news_saved_run_service import SavedRunReadError
    try:
        if not path or not pin:
            raise ValueError('missing_pin')
        value = read_document(Path(path))
        fields={'schema_version','pipeline_version','database_identity_sha256'}
        version=value.get('schema_version')
        if (sha(value)!=pin or version not in {'saved-native-read-context-v1','saved-native-read-context-v2'}
                or set(value)!=(fields|{'fallback_pipeline_versions'} if version=='saved-native-read-context-v2' else fields)):
            raise ValueError('invalid_context')
        validate_processing_identity('ner_rules_v1', value['pipeline_version'])
        fallback=value.get('fallback_pipeline_versions',[])
        if not isinstance(fallback,list) or len(fallback)>8 or len(set(fallback))!=len(fallback) or value['pipeline_version'] in fallback:
            raise ValueError('invalid_context')
        for item in fallback:validate_processing_identity('ner_rules_v1',item)
        return SavedNativeReadContext(value['pipeline_version'], value['database_identity_sha256'],tuple(fallback))
    except (OSError, ValueError, KeyError, TypeError):
        raise SavedRunReadError('news_native_reader_unavailable') from None


def reader_pipeline_selection(context: object) -> str | tuple[str, ...]:
    return getattr(context,'pipeline_selection',context.pipeline_version)
