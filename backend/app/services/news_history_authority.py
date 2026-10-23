"""Explicit, hash-pinned archive-only authority; never a general cloud bypass."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from pathlib import Path

from app.services.news_ner_durable.contracts import sha

OPERATIONS = {'register_captures', 'save_archives'}


def valid_shared_connection(engine: object) -> bool:
    url = engine.url
    return url.get_backend_name() == 'postgresql' and (not url.query or (
        url.host is None and set(url.query) == {'host'} and isinstance(url.query['host'], str)
        and re.fullmatch(r'/cloudsql/[a-z0-9-]+:[a-z0-9-]+:[a-z0-9-]+', url.query['host']) is not None))


def application_identity() -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    files = [root/'app/services'/name for name in (
        'news_history_authority.py', 'news_history_capture_registration.py',
        'news_historical_outputs.py', 'news_historical_interpretation.py',
        'news_historical_processing.py', 'news_historical_policy.py',
        'news_history_incident_matching.py', 'news_history_resources.py', 'news_history_protection.py')]
    files.extend(root/'scripts'/name for name in ('run_news_history_seed.py',
        'register_news_history_captures.py', 'materialize_news_historical_outputs.py'))
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def expected_authority(engine: object, operation: str, selection_sha256: str,
                       assets_sha256: str | None = None) -> dict:
    from app.services.news_historical_processing import database_identity, require
    require(operation in OPERATIONS, 'historical_shared_operation_invalid')
    require(len(selection_sha256) == 64, 'historical_shared_selection_invalid')
    return {'schema_version': 'historical-shared-archive-authority-v1',
        'operation': operation, 'selection_sha256': selection_sha256,
        'database_identity_sha256': database_identity(engine),
        'confirmed_database': engine.url.database, 'assets_sha256': assets_sha256,
        'application_sha256': application_identity(),
        'archive_only': True, 'live_publication_allowed': False, 'active_output_allowed': False}


@dataclass(frozen=True)
class ArchiveAuthority:
    policy: dict
    policy_sha256: str

    def validate(self, engine: object, operation: str, selection_sha256: str,
                 assets_sha256: str | None = None) -> None:
        from app.services.news_historical_processing import require
        require(valid_shared_connection(engine),
                'historical_shared_target_invalid')
        require(sha(self.policy) == self.policy_sha256 and self.policy == expected_authority(
            engine, operation, selection_sha256, assets_sha256), 'historical_shared_authority_mismatch')


def load_archive_authority(path: Path, pin: str) -> ArchiveAuthority:
    from app.services.news_historical_processing import read_document, require
    policy = read_document(path)
    require(sha(policy) == pin, 'historical_shared_authority_changed')
    return ArchiveAuthority(policy, pin)
