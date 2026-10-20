"""Allowed-mode migration on fresh owned local PostGIS only; no inference or APIs."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from io import StringIO
import json
import os
from pathlib import Path
import time
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from geoalchemy2 import WKTElement
from sqlalchemy import create_engine, inspect, insert, select, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base
from app.models import (FloodAvoidanceZone, NewsArticle, NewsArticleVersion, NewsExtractionRun,
                        NewsClaimCase, NewsClaimSource, NewsClaimEvaluation, NewsClaimDecision, NewsClaimZoneLink)

PREVIOUS = 'd7e4b9a21c60'
REVISION = 'e8a6f1c2d903'
CHECK = 'ck_news_extraction_runs_rules_only_mode'
NOW = datetime(2026, 10, 20, tzinfo=timezone.utc)
METRICS = []
EVIDENCE_TABLES = ('news_articles', 'news_article_versions', 'news_extraction_runs', 'news_claim_cases',
                   'news_claim_sources', 'news_claim_evaluations', 'news_claim_decisions', 'news_claim_zone_links',
                   'flood_avoidance_zones')


def config() -> Config:
    return Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))


def migrate(engine, target: str, *, down: bool = False) -> None:
    previous = settings.DATABASE_URL
    settings.DATABASE_URL = engine.url.render_as_string(hide_password=False)
    started = time.monotonic()
    success = False
    try:
        (command.downgrade if down else command.upgrade)(config(), target)
        success = True
    finally:
        settings.DATABASE_URL = previous
        METRICS.append({'action': 'downgrade' if down else 'upgrade', 'target': target,
                        'success': success, 'seconds': time.monotonic() - started})


@pytest.fixture(scope='module')
def database_factory():
    value = os.getenv('LANES_NER_MODE_TEST_DATABASE_URL')
    if not value:
        pytest.skip('Owned disposable local mode-schema database required')
    url = make_url(value)
    assert url.drivername == 'postgresql+psycopg' and url.host in ('127.0.0.1', 'localhost', '::1')
    assert (url.database or '').startswith('lanes_ner_mode_test_')
    admin = create_engine(url.set(database='postgres'), poolclass=NullPool, isolation_level='AUTOCOMMIT')
    engines = []
    def create(revision='head'):
        name = 'lanes_ner_mode_test_' + uuid4().hex
        with admin.connect() as connection:
            connection.exec_driver_sql('CREATE DATABASE ' + admin.dialect.identifier_preparer.quote(name))
        engine = create_engine(url.set(database=name), poolclass=NullPool)
        engines.append(engine)
        assert not set(inspect(engine).get_table_names()) - {'spatial_ref_sys'}
        if revision is not None:
            migrate(engine, revision)
        return engine
    def cleanup():
        for engine in engines:
            name = engine.url.database
            assert name.startswith('lanes_ner_mode_test_') and len(name.removeprefix('lanes_ner_mode_test_')) == 32
            engine.dispose()
            with admin.connect() as connection:
                connection.exec_driver_sql('DROP DATABASE ' + admin.dialect.identifier_preparer.quote(name))
        engines.clear()
    create.cleanup = cleanup
    try:
        yield create
    finally:
        cleanup()
        admin.dispose()
        destination = os.getenv('LANES_NER_MODE_TEST_RECEIPTS')
        if destination:
            path = Path(destination).resolve()
            expected = Path(__file__).resolve().parents[1] / 'training/flood_ner/artifacts'
            assert path.parent == expected.resolve() and path.name.startswith('news-ner-mode-schema-')
            with (path / 'migration-measurements.json').open('x', encoding='utf-8') as stream:
                json.dump(METRICS, stream, indent=2); stream.write('\n')


@pytest.fixture
def database(database_factory):
    try:
        yield database_factory
    finally:
        # Only fresh UUID-named fixture databases created by this factory.
        database_factory.cleanup()


def current_revision(engine) -> str:
    with engine.connect() as connection:
        return connection.scalar(text('SELECT version_num FROM alembic_version'))


def checks(engine) -> dict:
    return {c['name']: c['sqltext'] for c in inspect(engine).get_check_constraints('news_extraction_runs')}


def schema(engine, *, omit_mode=False) -> dict:
    with engine.connect() as connection:
        columns = connection.execute(text("""SELECT table_name,column_name,ordinal_position,is_nullable,
            data_type,udt_name,character_maximum_length,column_default
            FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position""")).all()
        constraints = connection.execute(text("""SELECT r.relname,c.conname,c.contype,pg_get_constraintdef(c.oid),c.convalidated
            FROM pg_constraint c JOIN pg_class r ON r.oid=c.conrelid
            WHERE c.connamespace='public'::regnamespace ORDER BY r.relname,c.conname""")).all()
        indexes = connection.execute(text("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY tablename,indexname")).all()
        triggers = connection.execute(text("""SELECT r.relname,t.tgname,pg_get_triggerdef(t.oid)
            FROM pg_trigger t JOIN pg_class r ON r.oid=t.tgrelid WHERE NOT t.tgisinternal
            AND r.relnamespace='public'::regnamespace ORDER BY r.relname,t.tgname""")).all()
    return {'columns': columns, 'constraints': [c for c in constraints if not (omit_mode and c[1] == CHECK)],
            'indexes': indexes, 'triggers': triggers}


def evidence(engine) -> dict:
    with engine.connect() as connection:
        return {table: connection.execute(text(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')).scalars().all()
                for table in EVIDENCE_TABLES}


def run_values(version_id: int, *, mode='rules_only', status='pending', **changes) -> dict:
    result = {'article_version_id': version_id, 'pipeline_version': 'fixture-' + uuid4().hex,
              'mode': mode, 'status': status, 'attempt_count': 0, 'created_at': NOW, 'updated_at': NOW}
    if status == 'processing':
        result.update(lease_token=uuid4(), lease_expires_at=NOW + timedelta(minutes=5))
    if status in ('completed', 'failed'):
        result.update(completed_at=NOW, result={'claims': [], 'fixture': '🚦 Niño'}, error_code='fixture' if status == 'failed' else None)
    result.update(changes)
    return result


def seed(engine, *, publication=False) -> dict:
    with Session(engine) as db, db.begin():
        article = NewsArticle(canonical_url='https://example.org/schema/' + uuid4().hex,
            publisher_source_id='fixture', title='Fictional source', article_text='  🚦 Baha sa Calle Niño.\n',
            content_fingerprint='a' * 64)
        db.add(article); db.flush()
        version = NewsArticleVersion(article_id=article.id, input_fingerprint=uuid4().hex * 2,
                                     input_snapshot={'article_text': article.article_text})
        db.add(version); db.flush()
        run = NewsExtractionRun(**run_values(version.id, status='completed'))
        db.add(run); db.flush()
        ids = {'article': article.id, 'version': version.id, 'run': run.id}
        if publication:
            case = NewsClaimCase(revision=2)
            db.add(case); db.flush()
            source = NewsClaimSource(case_id=case.id, extraction_run_id=run.id, claim_ordinal=0, claim_sha256='b' * 64)
            db.add(source); db.flush()
            evaluation = NewsClaimEvaluation(claim_source_id=source.id, policy_fingerprint='c' * 64,
                status='completed', completed_at=NOW, result={'fixture': 'saved assessment'})
            db.add(evaluation); db.flush()
            zone = FloodAvoidanceZone(geometry=WKTElement('POLYGON((121 14,121.001 14,121.001 14.001,121 14))', srid=4326),
                                      is_active=False, expires_at=NOW + timedelta(hours=1))
            db.add(zone); db.flush()
            decision = NewsClaimDecision(case_id=case.id, revision=1, request_id=uuid4(), evaluation_id=evaluation.id,
                actor_kind='automatic', operation='evaluate', public_state='active_zone', review_state='resolved',
                reason_code='fixture_evaluation', snapshot={'fixture': 'original history'}, observed_at=NOW,
                expires_at=NOW + timedelta(hours=1))
            db.add(decision); db.flush()
            db.add(NewsClaimZoneLink(decision_id=decision.id, zone_id=zone.id, relation='created'))
            db.add(NewsClaimDecision(case_id=case.id, revision=2, request_id=uuid4(), actor_kind='maintenance',
                operation='expire', public_state='expired', review_state='resolved', reason_code='fixture_expired',
                snapshot={'fixture': 'later history'}))
    return ids


def offline(direction: str) -> str:
    buffer = StringIO()
    context = MigrationContext.configure(dialect_name='postgresql', opts={'as_sql': True, 'output_buffer': buffer,
                                                                       'target_metadata': Base.metadata})
    migration = ScriptDirectory.from_config(config()).get_revision(REVISION).module
    with Operations.context(context):
        getattr(migration, direction)()
    return buffer.getvalue()


def test_single_head_and_offline_guard_order():
    scripts = ScriptDirectory.from_config(config())
    assert scripts.get_heads() == [REVISION] and scripts.get_revision(REVISION).down_revision == PREVIOUS
    for direction in ('upgrade', 'downgrade'):
        sql = offline(direction)
        assert sql.index('LOCK TABLE') < sql.index('pg_constraint') < sql.index('IS DISTINCT FROM') < sql.index('DROP CONSTRAINT')
        assert sql.count('ADD CONSTRAINT ' + CHECK) == 1 and 'ck_news_extraction_runs_ck_' not in sql
        assert 'RAISE EXCEPTION' in sql and 'DELETE FROM' not in sql and 'CREATE TABLE' not in sql


def test_fresh_upgrade_repeat_and_reflected_model(database):
    engine = database(None)
    migrate(engine, 'head'); migrate(engine, 'head')
    assert current_revision(engine) == REVISION
    inspector = inspect(engine)
    assert len([c for c in inspector.get_check_constraints('news_extraction_runs') if c['name'] == CHECK]) == 1
    assert 'ner_rules_v1' in checks(engine)[CHECK]
    actual = {column['name']: column for column in inspector.get_columns('news_extraction_runs')}
    for column in NewsExtractionRun.__table__.columns:
        assert actual[column.name]['nullable'] == column.nullable
        assert str(actual[column.name]['type'].compile(dialect=engine.dialect)) == str(column.type.compile(dialect=engine.dialect))
    assert actual['mode']['default'] is None and NewsExtractionRun.__table__.c.mode.default.arg == 'rules_only'


def test_legacy_rows_links_and_schema_survive_roundtrip(database):
    engine = database(PREVIOUS)
    seed(engine, publication=True)
    before, objects = evidence(engine), schema(engine, omit_mode=True)
    migrate(engine, 'head')
    assert evidence(engine) == before and schema(engine, omit_mode=True) == objects
    migrate(engine, PREVIOUS, down=True)
    assert current_revision(engine) == PREVIOUS and 'ner_rules_v1' not in checks(engine)[CHECK]
    assert evidence(engine) == before and schema(engine, omit_mode=True) == objects
    migrate(engine, 'head')
    assert current_revision(engine) == REVISION and evidence(engine) == before


def test_allowed_modes_defaults_identity_and_native_json(database):
    engine = database(); ids = seed(engine)
    payload = {'schema': 'fictional_native_storage_fixture', 'claims': [], 'graph': {'unresolved': ['🚦 Niño', None]}}
    native = run_values(ids['version'], mode='ner_rules_v1', status='completed', pipeline_version='coexist', result=payload)
    with engine.begin() as connection:
        connection.execute(insert(NewsExtractionRun).values(**{**native, 'mode': 'rules_only'}))
        identity = connection.scalar(insert(NewsExtractionRun).values(**native).returning(NewsExtractionRun.id))
    with engine.connect() as connection:
        assert connection.scalar(select(NewsExtractionRun.result).where(NewsExtractionRun.id == identity)) == payload
    with pytest.raises(IntegrityError):
        with engine.begin() as connection: connection.execute(insert(NewsExtractionRun).values(**native))
    with Session(engine) as db, db.begin():
        default = run_values(ids['version']); default.pop('mode')
        row = NewsExtractionRun(**default); db.add(row); db.flush(); assert row.mode == 'rules_only'


@pytest.mark.parametrize('values', [
    {'mode': 'unknown'}, {'mode': ''}, {'mode': None}, {'attempt_count': -1}, {'attempt_count': 6},
    {'status': 'unknown'}, {'status': 'processing', 'lease_token': None, 'lease_expires_at': None},
    {'status': 'pending', 'lease_token': uuid4()}, {'status': 'completed', 'result': None},
    {'status': 'completed', 'completed_at': None},
], ids=['unknown_mode', 'blank_mode', 'null_mode', 'negative_attempts', 'excess_attempts', 'bad_status',
        'missing_lease', 'unexpected_lease', 'missing_result', 'missing_completed_at'])
def test_existing_constraints_still_reject_invalid_rows(database, values):
    engine = database(); ids = seed(engine)
    changes = dict(values); status = changes.pop('status', 'pending')
    candidate = run_values(ids['version'], status=status, **changes)
    with pytest.raises(IntegrityError):
        with engine.begin() as connection: connection.execute(insert(NewsExtractionRun).values(**candidate))
    with pytest.raises(DBAPIError, match='immutable'):
        with engine.begin() as connection:
            connection.execute(update(NewsArticleVersion).where(NewsArticleVersion.id == ids['version']).values(input_snapshot={'changed': True}))


@pytest.mark.parametrize('status', ['pending', 'failed', 'completed'])
def test_native_rows_block_downgrade_atomically(database, status):
    engine = database(); ids = seed(engine, publication=True)
    with engine.begin() as connection:
        connection.execute(insert(NewsExtractionRun).values(**run_values(ids['version'], mode='ner_rules_v1', status=status)))
    before, objects = evidence(engine), schema(engine)
    with pytest.raises(DBAPIError, match='Cannot downgrade.*preserve NER history'):
        migrate(engine, PREVIOUS, down=True)
    assert current_revision(engine) == REVISION and evidence(engine) == before and schema(engine) == objects


@pytest.mark.parametrize('drift', ['missing', 'wrong_expression', 'unvalidated'])
def test_upgrade_refuses_constraint_drift_without_changes(database, drift):
    engine = database(PREVIOUS); ids = seed(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql('ALTER TABLE news_extraction_runs DROP CONSTRAINT ' + CHECK)
        if drift != 'missing':
            expression = "mode IN ('rules_only','ner_rules_v1','unexpected')" if drift == 'wrong_expression' else "mode = 'rules_only'"
            connection.exec_driver_sql('ALTER TABLE news_extraction_runs ADD CONSTRAINT ' + CHECK + ' CHECK (' + expression + ')' + (' NOT VALID' if drift == 'unvalidated' else ''))
        if drift == 'wrong_expression':
            connection.execute(insert(NewsExtractionRun).values(**run_values(ids['version'], mode='ner_rules_v1')))
    before, objects = evidence(engine), schema(engine)
    with pytest.raises(DBAPIError, match='news_extraction_mode_constraint_drift'):
        migrate(engine, 'head')
    assert current_revision(engine) == PREVIOUS and evidence(engine) == before and schema(engine) == objects


def test_downgrade_refuses_drift(database):
    engine = database(); seed(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql('ALTER TABLE news_extraction_runs DROP CONSTRAINT ' + CHECK)
        connection.exec_driver_sql('ALTER TABLE news_extraction_runs ADD CONSTRAINT ' + CHECK + " CHECK (mode IN ('rules_only','ner_rules_v1','unexpected'))")
    objects = schema(engine)
    with pytest.raises(DBAPIError, match='news_extraction_mode_constraint_drift'):
        migrate(engine, PREVIOUS, down=True)
    assert current_revision(engine) == REVISION and schema(engine) == objects


def test_generated_sql_executes_and_retains_rollback_guard(database):
    engine = database(PREVIOUS); ids = seed(engine)
    with engine.begin() as connection: connection.exec_driver_sql(offline('upgrade'))
    assert 'ner_rules_v1' in checks(engine)[CHECK]
    with engine.begin() as connection:
        connection.execute(insert(NewsExtractionRun).values(**run_values(ids['version'], mode='ner_rules_v1')))
    before, objects = evidence(engine), schema(engine)
    with pytest.raises(DBAPIError, match='Cannot downgrade.*preserve NER history'):
        with engine.begin() as connection: connection.exec_driver_sql(offline('downgrade'))
    assert evidence(engine) == before and schema(engine) == objects


def test_concurrent_native_insert_cannot_race_downgrade_guard(database):
    engine = database(); ids = seed(engine)
    with engine.connect() as writer:
        transaction = writer.begin()
        writer.execute(insert(NewsExtractionRun).values(**run_values(ids['version'], mode='ner_rules_v1')))
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(migrate, engine, PREVIOUS, down=True)
            observed_wait = False
            deadline = time.monotonic() + 10
            try:
                while time.monotonic() < deadline:
                    with engine.connect() as monitor:
                        observed_wait = bool(monitor.scalar(text("""SELECT count(*) FROM pg_stat_activity
                            WHERE datname=current_database() AND wait_event_type='Lock'
                            AND query LIKE 'LOCK TABLE news_extraction_runs IN ACCESS EXCLUSIVE MODE%'""")))
                    if observed_wait: break
                    time.sleep(.02)
                assert observed_wait, 'Migration did not wait for the in-flight writer'
            finally:
                transaction.commit()
            with pytest.raises(DBAPIError, match='Cannot downgrade.*preserve NER history'):
                future.result(timeout=15)
    assert current_revision(engine) == REVISION
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM news_extraction_runs WHERE mode='ner_rules_v1'")) == 1
