"""Frozen E0 handoff with disposable default and pinned processing-only origin policy."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import signal
import sys
import threading

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.services.news_historical_preparation import (PreparationError, SourceSpec, build_preparation)
from app.services.news_ner_durable.contracts import NativeInput, RunEvidence, sha

MAX_DOCUMENT_BYTES = 8 * 1024 * 1024
NATIVE_REVISION = 'e8a6f1c2d903'
COMPATIBLE_NATIVE_REVISIONS = {NATIVE_REVISION, 'f1a9c7e2b604'}


def require(condition: bool, code: str) -> None:
    if not condition:
        raise PreparationError(code)


def read_document(path: Path) -> dict:
    require(not path.is_symlink() and path.is_file() and path.stat().st_size <= MAX_DOCUMENT_BYTES,
            'historical_package_file_invalid')
    def pairs(items: list) -> dict:
        result = {}
        for key, value in items:
            require(key not in result, 'historical_duplicate_json_key')
            result[key] = value
        return result
    def nonfinite(_value: str) -> None:
        raise PreparationError('historical_nonfinite_json')
    value = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs, parse_constant=nonfinite)
    require(isinstance(value, dict), 'historical_package_file_invalid')
    return value


@dataclass(frozen=True)
class HistoricalPackage:
    manifest_sha256: str
    documents: dict[str, dict]
    _document_bindings: tuple[tuple[str, str], ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, '_document_bindings', tuple(sorted((name, sha(value))
            for name, value in self.documents.items())))

    @property
    def manifest(self) -> dict:
        return deepcopy(self.documents['manifest.json'])

    @property
    def captures(self) -> tuple[dict, ...]:
        return tuple(deepcopy(self.documents[i['native_capture_file']]) for i in self.manifest['inputs'])

    def validate(self) -> None:
        require(tuple(sorted((name, sha(value)) for name, value in self.documents.items())) == self._document_bindings,
                'historical_loaded_package_changed')
        require(sha(self.documents['manifest.json']) == self.manifest_sha256, 'historical_manifest_changed')
        receipt = self.documents['receipt.json']
        require(receipt['manifest_sha256'] == self.manifest_sha256, 'historical_receipt_mismatch')
        require(set(receipt['document_sha256']) == set(self.documents) - {'receipt.json'}, 'historical_package_set_invalid')
        for name, fingerprint in receipt['document_sha256'].items():
            require(sha(self.documents[name]) == fingerprint, 'historical_document_changed')


def load_historical_package(manifest_path: Path, expected_sha256: str) -> HistoricalPackage:
    require(manifest_path.name == 'manifest.json' and not manifest_path.parent.is_symlink(), 'historical_manifest_path_invalid')
    manifest = read_document(manifest_path)
    require(sha(manifest) == expected_sha256, 'historical_manifest_changed')
    inputs = manifest['inputs']
    require(1 <= len(inputs) <= 200 and len({i['article_id'] for i in inputs}) == len(inputs), 'historical_input_set_invalid')
    names = {'manifest.json', 'receipt.json', 'inventory.json'}
    for item in inputs:
        require(type(item['article_id']) is int and item['article_id'] > 0
            and item['native_capture_file'] == f"native-{item['article_id']}.json", 'historical_capture_path_invalid')
        names.add(item['native_capture_file'])
    require({p.name for p in manifest_path.parent.iterdir()} == names, 'historical_package_set_invalid')
    documents = {name: read_document(manifest_path.parent/name) for name in names}
    package = HistoricalPackage(expected_sha256, documents)
    package.validate()
    # Reconstruct E0 using its own frozen assets and inventory, never today's
    # application assets. The separately supplied parent hash authenticates pins.
    inventory = documents['inventory.json']
    rows = {r['version_id']: r for r in inventory['sources']}
    specs = tuple(SourceSpec(i['article_id'], i['source_version_id'], i['source_input_fingerprint'],
        i['source_text_sha256'], rows[i['source_version_id']]['input_snapshot']['canonical_url'],
        rows[i['source_version_id']]['input_snapshot']['publisher'],
        rows[i['source_version_id']]['input_snapshot']['published_at']) for i in inputs)
    candidates = tuple((c['article_id'], c['legacy_run_id'], c['legacy_claim_ordinal'], c['existing_zone_id'],
        c['role'], c['intended_disposition'], c['target']['road'], c['target']['city']) for c in manifest['candidates'])
    retained = None if all(i['retained_exact_text_match'] is None for i in inputs) else {
        i['source_text_sha256'] for i in inputs if i['retained_exact_text_match']}
    rebuilt = build_preparation(inventory, manifest['assets'], specs=specs, candidates=candidates,
                                retained_text_hashes=retained, dataset_id=manifest['dataset_id'])
    if 'retained_workload_sha256' in manifest:
        rebuilt['manifest.json']['retained_workload_sha256'] = manifest['retained_workload_sha256']
        rebuilt['receipt.json']['manifest_sha256'] = sha(rebuilt['manifest.json'])
        rebuilt['receipt.json']['document_sha256']['manifest.json'] = sha(rebuilt['manifest.json'])
    require(rebuilt == documents, 'historical_e0_reconstruction_failed')
    return package


def database_identity(engine: Engine) -> str:
    url = engine.url
    value = {'driver': url.drivername, 'host': url.host, 'port': url.port, 'database': url.database}
    if url.query:
        value['connection_query'] = dict(url.query)
    return sha(value)


def disposable_target(engine: Engine, environment: str) -> bool:
    from app.services.news_ner_durable.processing import require_local_target
    try:
        require_local_target(environment, engine.url.render_as_string(hide_password=False))
        return engine.url.host in {'127.0.0.1', 'localhost', '::1'} and not engine.url.query
    except ValueError:
        return False


def runtime_blockers(trusted) -> list[str]:
    result = []
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        result.append('historical_linux_amd64_required')
    elif (threading.current_thread() is not threading.main_thread()
          or signal.getitimer(signal.ITIMER_REAL)[0] != 0):
        result.append('historical_runtime_timer_unavailable')
    try:
        if importlib.metadata.version('spacy') != '3.7.5':
            result.append('historical_runtime_dependencies_unqualified')
    except importlib.metadata.PackageNotFoundError:
        result.append('historical_runtime_dependencies_unqualified')
    if sys.version_info[:2] != (3, 12):
        result.append('historical_python312_required')
    if platform.system() == 'Linux':
        try:
            if os.environ.get('LANES_HISTORY_RESOURCE_PROFILE') == 'cloud-run-v1':
                from app.services.news_history_resources import checkpoint
                checkpoint()
            else:
                memory = int(Path('/sys/fs/cgroup/memory.max').read_text().strip())
                quota, period = Path('/sys/fs/cgroup/cpu.max').read_text().split()
                if memory != 3 * 1024**3 or int(quota) / int(period) != 1:
                    raise ValueError('unqualified_envelope')
        except (OSError, ValueError, ZeroDivisionError):
            result.append('historical_resource_envelope_unqualified')
        try:
            from app.services.news_ner.bundle import verify_bundle
            verify_bundle(Path('/assets'), trusted.manifest['model']['bundle_sha256'])
        except (OSError, ValueError):
            result.append('historical_worker_asset_mount_unavailable')
    return result


def execution_manifest(package: HistoricalPackage, trusted, assets_sha256: str, engine: Engine,
                       environment: str, authorization: object | None = None) -> tuple[dict, list[str]]:
    package.validate()
    trusted.validate()
    current, original = trusted.manifest, package.manifest['assets']['manifest']
    blockers = []
    if sha(current) != assets_sha256:
        blockers.append('historical_execution_assets_mismatch')
    changed = {key: {'before_sha256': sha(original[key]), 'after_sha256': sha(current[key])}
        for key in current if original[key] != current[key]}
    if set(changed) - {'projection', 'source_check'}:
        blockers.append('historical_protected_assets_changed')
    origin = database_identity(engine) == package.manifest['database_identity_sha256']
    disposable = disposable_target(engine, environment)
    if not origin and not disposable:
        blockers.append('historical_database_identity_mismatch')
    if authorization is not None:
        from app.services.news_historical_policy import HistoricalAuthorization
        require(type(authorization) is HistoricalAuthorization, 'historical_target_policy_invalid')
        authorization.validate(engine)
        require(authorization.package.manifest_sha256 == package.manifest_sha256
                and authorization.trusted.manifest == trusted.manifest, 'historical_target_policy_binding_mismatch')
        require(authorization.policy.get('resource_profile') == os.environ.get(
            'LANES_HISTORY_RESOURCE_PROFILE', 'local-strict-v1'), 'historical_resource_profile_binding_mismatch')
    elif os.environ.get('LANES_HISTORY_RESOURCE_PROFILE') == 'cloud-run-v1':
        blockers.append('historical_resource_profile_authority_required')
    if not disposable and authorization is None:
        blockers.append('historical_cloud_processing_not_qualified')
    code_files = [Path(__file__), Path(__file__).parents[1]/'crud/news_historical_processing.py',
                  Path(__file__).parents[2]/'scripts/run_news_historical_processing.py']
    value = {'schema': 'lanes-historical-execution-v1',
        'parent_manifest_sha256': package.manifest_sha256,
        'dataset_id': package.manifest['dataset_id'],
        'demonstration_session_id': package.manifest['demonstration_session_id'],
        'source_database_identity_sha256': package.manifest['database_identity_sha256'],
        'target_database_identity_sha256': database_identity(engine),
        'target_kind': 'prepared_origin' if origin else 'disposable_mirror' if disposable else 'unrecognized',
        'processing_policy': 'disposable_only_no_publication', 'assets': current,
        'assets_sha256': sha(current), 'pipeline_version': trusted.pipeline_version,
        'changed_asset_families': changed,
        'operator_code_sha256': {p.relative_to(Path(__file__).parents[2]).as_posix():
            hashlib.sha256(p.read_bytes()).hexdigest() for p in code_files}}
    if authorization is not None:
        value['processing_policy'] = 'pinned_origin_processing_only_no_publication'
        value['target_policy_sha256'] = authorization.policy_sha256
    from app.services.news_historical_policy import historical_code_identity
    value['historical_adapter_application_sha256'] = historical_code_identity()
    return value, blockers


def inspect_sources(db, package: HistoricalPackage, trusted, sources: tuple | None = None) -> tuple[list[str], dict]:
    from app.crud.news_historical_processing import read_historical_state
    from app.services.configuration_service import read_configuration, selected_news_sources
    from app.services.news_evaluation_service import source_is_approved
    from app.schemas.news_extraction import NewsArticleExtractorInput
    from app.services.news_ner_durable.adapter import verify_saved_result
    state = read_historical_state(db, package.manifest['inputs'], trusted.pipeline_version)
    blockers = []
    if state['revision'] not in COMPATIBLE_NATIVE_REVISIONS:
        blockers.append('historical_native_migration_required')
    if not state['tables_present']:
        return blockers + ['historical_required_tables_missing'], state
    if not state['native_mode_supported']:
        blockers.append('historical_native_storage_incompatible')
    config = read_configuration(db)
    if not config.news_processing_enabled:
        blockers.append('historical_processing_paused')
    selected = selected_news_sources(db, sources)
    original_rows = {r['version_id']: r for r in package.documents['inventory.json']['sources']}
    actual_rows = {r['version_id']: r for r in state['sources']}
    for capture in package.captures:
        original = original_rows[capture['source_version_id']]
        actual = actual_rows.get(capture['source_version_id'])
        native = NativeInput.model_validate(capture['input_snapshot'])
        if (actual is None or any(actual[key] != original[key] for key in
                ('article_id', 'input_fingerprint', 'input_snapshot'))
                or actual['article_url'] != native.canonical_url or actual['article_publisher'] != native.publisher):
            blockers.append('historical_saved_source_mismatch')
        article = NewsArticleExtractorInput(article_id=capture['article_id'],
            **native.model_dump(exclude={'capture_schema', 'publication_evidence'}))
        if not source_is_approved(article, selected):
            blockers.append('historical_source_not_selected_or_approved')
    for run in state['runs']:
        from app.models.news import NewsArticleVersion
        version = db.get(NewsArticleVersion, run.article_version_id)
        capture = next((c for c in package.captures if c['article_id'] == version.article_id
            and c['native_input_fingerprint'] == version.input_fingerprint), None)
        try:
            context = RunEvidence.from_records(run, version)
            context.source()
            require(capture is not None and version.input_snapshot == capture['input_snapshot'],
                    'historical_saved_capture_invalid')
        except (ValueError, TypeError, KeyError):
            blockers.append('historical_saved_capture_invalid')
            continue
        if run.status == 'completed':
            try:
                verify_saved_result(context, run.result, trusted)
            except (ValueError, TypeError, KeyError):
                blockers.append('historical_saved_result_invalid')
    return sorted(set(blockers)), state


def preflight_historical(engine: Engine, package: HistoricalPackage, trusted, *, assets_sha256: str,
                         confirmed_database: str, environment: str, sources: tuple | None = None,
                         authorization: object | None = None) -> dict:
    from app.crud.news_historical_processing import readonly_historical_session
    require(engine.url.database == confirmed_database and bool(confirmed_database), 'historical_database_confirmation_mismatch')
    manifest, blockers = execution_manifest(package, trusted, assets_sha256, engine, environment, authorization)
    blockers.extend(runtime_blockers(trusted))
    from sqlalchemy.exc import SQLAlchemyError
    try:
        with readonly_historical_session(engine, confirmed_database) as db:
            source_blockers, state = inspect_sources(db, package, trusted, sources)
            blockers.extend(source_blockers)
            revision = state['revision']
    except SQLAlchemyError:
        blockers.append('historical_preflight_storage_unavailable')
        revision = None
    except (ValueError, TypeError, KeyError):
        blockers.append('historical_preflight_configuration_invalid')
        revision = None
    return {'schema': 'lanes-historical-attempt-v1', 'mode': 'preflight',
        'status': 'blocked' if blockers else 'ready', 'blockers': sorted(set(blockers)),
        'execution_manifest': manifest, 'execution_manifest_sha256': sha(manifest),
        'schema_revision': revision, 'database_writes_performed': False,
        'worker_isolation': 'not_started_checked_at_runtime_start',
        'warnings': [{'article_id': i['article_id'], 'code': 'original_feed_publication_proof_unknown'}
            for i in package.manifest['inputs'] if not i['publication_evidence']['timezone_known']]}


async def process_historical(engine: Engine, package: HistoricalPackage, trusted, *, assets_sha256: str,
                             confirmed_database: str, environment: str, sources: tuple | None = None,
                             runtime_factory=None, clock=None, authorization: object | None = None,
                             placement_service: object | None = None) -> dict:
    from app.services.news_ner_durable.processing import process_native_saved_news, transaction, deadline
    from app.crud.news_historical_processing import (enqueue_historical_captures, read_historical_run_records,
                                                    readonly_historical_session)
    from app.crud.news_processing import utc_now, MAX_ATTEMPTS
    if not disposable_target(engine, environment) and authorization is None:
        return {'mode': 'process', 'status': 'blocked', 'blockers': ['historical_cloud_processing_not_qualified'],
                'database_writes_performed': False}
    result = preflight_historical(engine, package, trusted, assets_sha256=assets_sha256,
        confirmed_database=confirmed_database, environment=environment, sources=sources, authorization=authorization)
    result['mode'] = 'process'
    if result['blockers']:
        return result
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    clock = clock or utc_now
    with transaction(factory) as db:
        package.validate(); trusted.validate()
        if authorization is not None:
            authorization.validate_session(db, sources=sources)
        blockers, _state = inspect_sources(db, package, trusted, sources)
        require(not blockers and _state['database'] == confirmed_database, 'historical_preflight_changed')
        run_ids = enqueue_historical_captures(db, package.captures, trusted.pipeline_version)
    result['database_writes_performed'] = True
    cancelled = False
    try:
        with readonly_historical_session(engine, confirmed_database) as db:
            rows = read_historical_run_records(db, run_ids)
            pending = tuple(r.id for r, _version in rows if r.status == 'pending' and r.attempt_count < MAX_ATTEMPTS)
        if pending:
            worker_options = {'historical_authorization': authorization} if authorization is not None else {}
            summary = await process_native_saved_news(factory, load_assets=lambda: trusted,
                environment=environment, database_url=engine.url.render_as_string(hide_password=False),
                run_ids=pending, limit=len(pending), sources=sources, runtime_factory=runtime_factory, clock=clock,
                **worker_options)
            result['processing'] = asdict(summary)
    except asyncio.CancelledError:
        cancelled = True
        result['error_code'] = 'ner_runtime_cancelled'
    except Exception:
        result['error_code'] = 'historical_processing_failed'
    finally:
        try:
            with readonly_historical_session(engine, confirmed_database) as db:
                result['runs'] = [{'run_id': run.id, 'article_id': version.article_id,
                    'article_version_id': version.id, 'status': run.status, 'attempt_count': run.attempt_count,
                    'result_sha256': sha(run.result) if run.result is not None else None}
                    for run, version in read_historical_run_records(db, run_ids)]
        except Exception:
            result['run_state_error_code'] = 'historical_run_state_unavailable'
    complete = (not result.get('error_code') and not result.get('run_state_error_code') and
        all(r['status'] == 'completed' for r in result.get('runs', [])) and len(result.get('runs', [])) == len(run_ids))
    result['status'] = ('interrupted' if cancelled else 'completed' if complete and
        not result.get('processing', {}).get('error_code') else 'requires_attention')
    result['historical_qualification_status'] = 'not_evaluated'
    if complete:
        from app.services.news_historical_interpretation import interpret_historical
        try:
            with deadline(60), readonly_historical_session(engine, confirmed_database) as db:
                result['historical_interpretations'] = [interpret_historical(run, version, trusted,
                    package, result['execution_manifest'], now=clock(), placement_service=placement_service)
                    for run, version in read_historical_run_records(db, run_ids)]
            result['historical_qualification_status'] = ('qualified' if any(
                i['status'] == 'qualified' for i in result['historical_interpretations']) else 'unresolved')
            groups = [g for i in result['historical_interpretations'] for g in i['groups']]
            result['historical_qualification_counts'] = {
                'source_qualified_groups': sum(g['qualification'] != 'unresolved' for g in groups),
                'unresolved_groups': sum(g['qualification'] == 'unresolved' for g in groups),
                'placement_previews': sum(g['placement'] is not None for g in groups)}
        except Exception:
            result['historical_qualification_status'] = 'failed'
            result['historical_qualification_error_code'] = 'historical_interpretation_failed'
            result['status'] = 'requires_attention'
    return result


def save_attempt(directory: Path, result: dict, attempt_id: str) -> None:
    require(bool(re.fullmatch(r'[A-Za-z0-9_-]{1,64}', attempt_id)), 'historical_attempt_identity_invalid')
    require(not directory.is_symlink(), 'historical_private_receipts_required')
    directory.mkdir(parents=True, exist_ok=True)
    for interpretation in result.get('historical_interpretations', []):
        filename = directory/f"interpretation-{sha(interpretation)}.json"
        try:
            with filename.open('x', encoding='utf-8') as stream:
                json.dump(interpretation, stream, ensure_ascii=False, sort_keys=True, allow_nan=False)
        except FileExistsError:
            require(read_document(filename) == interpretation, 'historical_interpretation_receipt_changed')
    execution = result.get('execution_manifest')
    if execution:
        filename = directory/f"execution-{sha(execution)}.json"
        if filename.exists():
            require(read_document(filename) == execution, 'historical_execution_receipt_changed')
        else:
            try:
                with filename.open('x', encoding='utf-8') as stream:
                    json.dump(execution, stream, ensure_ascii=False, sort_keys=True, allow_nan=False)
            except FileExistsError:
                require(read_document(filename) == execution, 'historical_execution_receipt_changed')
    with (directory/f'attempt-{attempt_id}.json').open('x', encoding='utf-8') as stream:
        json.dump({**result, 'recorded_at': datetime.now(timezone.utc).isoformat()}, stream,
                  ensure_ascii=False, sort_keys=True, allow_nan=False)
