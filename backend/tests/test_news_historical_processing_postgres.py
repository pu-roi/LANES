"""E1.2 on cloned disposable PostGIS with fictional inputs/runtime, never inference."""
import asyncio
from contextlib import contextmanager
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from threading import Barrier
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import event, func, select, text

from app.crud.news_historical_processing import enqueue_historical_captures
from app.crud.news_processing import enqueue_input_snapshot, claim_due_run
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.models.setting import SystemSetting
from app.schemas.configuration import OperationalSettings
from app.services.configuration_service import CONFIG_KEY
from app.services import news_historical_processing as service
from app.services.news_ner_durable import processing
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner.location_pipeline import from_neural_mentions
from app.services.news_ner_runtime.supervisor import RuntimeFailure, Session as RealRuntime
from app.services.news_historical_preparation import save_private_package
from historical_processing_fixtures import fictional_documents
from test_news_ner_integration import c3b_db
from test_news_ner_durable import trusted, NOW, BODY, make_case
from app.services.news_sources import NewsSource

SOURCES = (NewsSource('fictional', 'Fictional', ('example.org',), ('https://example.org/feed',), NOW.date(), True),)


@pytest.fixture(autouse=True)
def isolation(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail('Historical software check attempted network or real neural session')
    monkeypatch.setattr(RealRuntime, 'start', forbidden)
    monkeypatch.setattr(httpx.Client, 'send', forbidden)
    monkeypatch.setattr(httpx.AsyncClient, 'send', forbidden)
    @contextmanager
    def timer(seconds):
        if seconds <= 0:
            raise processing.OperationDeadline()
        yield
    monkeypatch.setattr(processing, 'deadline', timer)
    # Runtime/platform checks are exercised independently; all requests here
    # use explicitly constructed responses and an instrumented test timer.
    monkeypatch.setattr(service, 'runtime_blockers', lambda _trusted: [])


@pytest.fixture
def historical(c3b_db, trusted, tmp_path):
    documents = fictional_documents(trusted)
    directory = tmp_path/'e0'
    save_private_package(directory, documents)
    package = service.load_historical_package(directory/'manifest.json', sha(documents['manifest.json']))
    with c3b_db() as db, db.begin():
        for row in documents['inventory.json']['sources']:
            snapshot = row['input_snapshot']
            db.add(NewsArticle(id=row['article_id'], canonical_url=snapshot['canonical_url'],
                publisher_source_id=snapshot['publisher'], title='Mutable latest title', excerpt='',
                article_text='Latest body must never be captured', published_at=NOW,
                content_fingerprint='0'*64, review_state='approved'))
            db.flush()
            db.add(NewsArticleVersion(id=row['version_id'], article_id=row['article_id'],
                input_fingerprint=row['input_fingerprint'], input_snapshot=snapshot))
    engine = c3b_db.kw['bind']
    class Runtime:
        starts = 0; requests = 0; closes = 0; state = 'new'; failure = None; after = None
        texts = []
        async def start(self):
            self.starts += 1; self.state = 'ready'
        async def request(self, request, *, timeout):
            assert timeout > 0
            self.requests += 1
            self.texts = self.texts + [request['text']]
            if self.failure:
                raise self.failure
            *_, inference, _result = make_case(trusted, request['text'])
            pure = from_neural_mentions({**request, 'mentions': inference['proposal']['neural_mentions']})
            if self.after:
                self.after()
            return {**pure, 'provenance': trusted.provenance, 'measurements': inference['measurements']}
        async def close(self):
            if self.state != 'closed':
                self.closes += 1; self.state = 'closed'
    runtime = Runtime()
    options = dict(assets_sha256=sha(trusted.manifest), confirmed_database=engine.url.database,
                   environment='test', sources=SOURCES)
    return SimpleNamespace(factory=c3b_db, engine=engine, package=package, trusted=trusted,
                           runtime=runtime, options=options, directory=directory)


def snapshot(h):
    with h.factory() as db:
        return {'versions': db.scalar(select(func.count()).select_from(NewsArticleVersion)),
            'runs': [(r.id, r.status, r.attempt_count, r.lease_token, r.result) for r in
                db.scalars(select(NewsExtractionRun).order_by(NewsExtractionRun.id))],
            'articles': [(r.id, r.review_state, r.article_text) for r in db.scalars(select(NewsArticle).order_by(NewsArticle.id))]}


def check_no_publication(h):
    with h.factory() as db:
        for table in ('news_claim_sources', 'news_claim_evaluations', 'news_claim_decisions',
                      'flood_events', 'flood_avoidance_zones'):
            assert db.scalar(text('SELECT count(*) FROM '+table)) == 0


def test_preflight_uses_read_only_transaction_no_model_or_writes(historical):
    h = historical
    before = snapshot(h)
    statements = []
    def observed(_conn, _cursor, statement, _params, _context, _many):
        statements.append(statement.strip())
    event.listen(h.engine, 'before_cursor_execute', observed)
    try:
        result = service.preflight_historical(h.engine, h.package, h.trusted, **h.options)
    finally:
        event.remove(h.engine, 'before_cursor_execute', observed)
    assert result['status'] == 'ready' and not result['blockers'], result['blockers']
    assert statements[0] == 'SET TRANSACTION READ ONLY'
    assert all(s.startswith(('SET', 'SELECT', 'SHOW')) for s in statements)
    assert snapshot(h) == before and h.runtime.starts == 0
    check_no_publication(h)


@pytest.mark.asyncio
async def test_exact_capture_completed_reuse_and_unrelated_pending_queue_preserved(historical):
    h = historical
    other = deepcopy(h.package.captures[0]['input_snapshot'])
    other['article_text'] += ' Unrelated input.'
    with h.factory() as db, db.begin():
        unrelated = enqueue_input_snapshot(db, 101, other, sha(other), mode='ner_rules_v1', pipeline_version=h.trusted.pipeline_version)
    original = snapshot(h)
    first = await service.process_historical(h.engine, h.package, h.trusted, runtime_factory=lambda _: h.runtime, clock=lambda: NOW, **h.options)
    assert first['status'] == 'completed' and h.runtime.requests == 2 and h.runtime.starts == h.runtime.closes == 1
    assert h.runtime.texts == [BODY, BODY]
    assert {r['article_id'] for r in first['runs']} == {101, 102}
    before_repeat = snapshot(h)
    second = await service.process_historical(h.engine, h.package, h.trusted,
        runtime_factory=lambda _: pytest.fail('completed run started inference'), **h.options)
    assert second['status'] == 'completed' and second['runs'] == first['runs']
    assert snapshot(h) == before_repeat
    assert before_repeat['articles'] == original['articles']
    with h.factory() as db:
        row = db.get(NewsExtractionRun, unrelated)
        assert row.status == 'pending' and row.attempt_count == 0 and row.result is None
    check_no_publication(h)


@pytest.mark.parametrize('setting,expected', [('news_processing_enabled', 'historical_processing_paused'),
    ('news_source_ids', 'historical_source_not_selected_or_approved')])
def test_processing_and_source_settings_block_before_capture(historical, setting, expected):
    h = historical
    config = OperationalSettings().model_dump(mode='json')
    config[setting] = False if setting == 'news_processing_enabled' else []
    with h.factory() as db, db.begin():
        db.add(SystemSetting(key=CONFIG_KEY, value={'revision': 1, 'settings': config}))
    before = snapshot(h)
    result = service.preflight_historical(h.engine, h.package, h.trusted, **h.options)
    assert expected in result['blockers'] and snapshot(h) == before


def test_multiple_preflight_blockers_and_changed_source_are_reported(historical, monkeypatch):
    h = historical
    with h.factory() as db, db.begin():
        db.get(NewsArticle, 101).publisher_source_id = 'unselected'
    monkeypatch.setattr(service, 'runtime_blockers', lambda _trusted: ['historical_linux_amd64_required'])
    result = service.preflight_historical(h.engine, h.package, h.trusted, **{**h.options, 'assets_sha256': '0'*64})
    assert {'historical_linux_amd64_required', 'historical_saved_source_mismatch',
        'historical_execution_assets_mismatch'} <= set(result['blockers'])
    assert h.runtime.starts == 0 and len(snapshot(h)['runs']) == 0


def test_missing_native_revision_reports_blocker_without_capture(historical):
    h = historical
    with h.engine.begin() as connection:
        connection.execute(text("UPDATE alembic_version SET version_num='d7e4b9a21c60'"))
    result = service.preflight_historical(h.engine, h.package, h.trusted, **h.options)
    assert 'historical_native_migration_required' in result['blockers']
    assert len(snapshot(h)['runs']) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('failure,code', [(RuntimeFailure('deadline'), 'ner_runtime_timeout'),
    (RuntimeFailure('worker_exit'), 'ner_runtime_failed'), (asyncio.CancelledError(), 'ner_runtime_cancelled')])
async def test_owned_failure_is_persisted_once_without_automatic_retry(historical, failure, code):
    h = historical; h.runtime.failure = failure
    result = await service.process_historical(h.engine, h.package, h.trusted, runtime_factory=lambda _: h.runtime,
        clock=lambda: NOW, **h.options)
    assert result['status'] == ('interrupted' if isinstance(failure, asyncio.CancelledError) else 'requires_attention')
    assert h.runtime.requests == 1 and h.runtime.starts == h.runtime.closes == 1
    with h.factory() as db:
        first = db.get(NewsExtractionRun, result['runs'][0]['run_id'])
        assert first.status == 'retry_wait' and first.error_code == code and first.attempt_count == 1
        # Keep the other pending input leased by another worker, so this repeat
        # proves it cannot take either retry-wait or even an expired foreign lease.
        other = db.get(NewsExtractionRun, result['runs'][1]['run_id'])
        from datetime import timedelta
        other.status='processing';other.lease_token=uuid4();other.lease_expires_at=NOW-timedelta(minutes=1)
        db.commit()
    before = snapshot(h)
    repeated = await service.process_historical(h.engine, h.package, h.trusted,
        runtime_factory=lambda _: pytest.fail('retry/leased run was automatically reclaimed'), **h.options)
    assert repeated['status'] == 'requires_attention' and snapshot(h) == before
    check_no_publication(h)


@pytest.mark.asyncio
async def test_cleanup_failure_keeps_completed_result_and_reports_attention(historical):
    h = historical
    async def bad_close():
        raise RuntimeFailure('cleanup_failed')
    h.runtime.close = bad_close
    result = await service.process_historical(h.engine, h.package, h.trusted, runtime_factory=lambda _: h.runtime,
        clock=lambda: NOW, **h.options)
    assert result['status'] == 'requires_attention'
    assert result['processing']['error_code'] == 'ner_runtime_cleanup_failed'
    assert all(r['status'] == 'completed' for r in result['runs'])


def test_concurrent_enqueue_has_one_version_and_run_per_capture(historical):
    h = historical; barrier = Barrier(2)
    def insert():
        with h.factory() as db, db.begin():
            barrier.wait(timeout=10)
            return enqueue_historical_captures(db, h.package.captures, h.trusted.pipeline_version)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: insert(), range(2)))
    assert results[0] == results[1] and len(set(results[0])) == 2
    assert snapshot(h)['versions'] == 4 and len(snapshot(h)['runs']) == 2


@pytest.mark.asyncio
async def test_lost_completion_lease_never_overwrites_new_owner(historical):
    h = historical; replacement = uuid4(); changed = []
    def replace():
        if changed:
            return
        with h.factory() as db, db.begin():
            row = db.scalar(select(NewsExtractionRun).where(NewsExtractionRun.status == 'processing'))
            row.lease_token = replacement; changed.append(row.id)
    h.runtime.after = replace
    result = await service.process_historical(h.engine, h.package, h.trusted, runtime_factory=lambda _: h.runtime,
        clock=lambda: NOW, **h.options)
    assert result['status'] == 'requires_attention' and result['processing']['lease_lost'] == 1
    with h.factory() as db:
        row = db.get(NewsExtractionRun, changed[0])
        assert row.status == 'processing' and row.lease_token == replacement and row.result is None


@pytest.mark.asyncio
async def test_failed_run_is_preserved_while_other_pending_input_completes(historical):
    h = historical
    with h.factory() as db, db.begin():
        ids = enqueue_historical_captures(db, h.package.captures, h.trusted.pipeline_version)
        row = db.get(NewsExtractionRun, ids[0]); row.status='failed';row.attempt_count=1;row.error_code='ner_runtime_failed'
    result = await service.process_historical(h.engine, h.package, h.trusted, runtime_factory=lambda _: h.runtime,
        clock=lambda: NOW, **h.options)
    assert result['status'] == 'requires_attention' and h.runtime.requests == 1
    with h.factory() as db:
        assert db.get(NewsExtractionRun, ids[0]).status == 'failed'
        assert db.get(NewsExtractionRun, ids[0]).attempt_count == 1


def test_empty_exact_claim_never_falls_back_to_general_queue(historical):
    h = historical
    with h.factory() as db, db.begin():
        ids = enqueue_historical_captures(db, h.package.captures, h.trusted.pipeline_version)
    before = snapshot(h)
    with h.factory() as db, db.begin():
        assert claim_due_run(db, NOW, mode='ner_rules_v1', pipeline_version=h.trusted.pipeline_version,
                             run_ids=(), pending_only=True) is None
    assert snapshot(h) == before and len(ids) == 2
