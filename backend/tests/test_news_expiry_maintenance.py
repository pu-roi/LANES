"""Auditor-independent maintenance boundaries; actual lifecycle checks use PostGIS."""
from contextlib import nullcontext
from datetime import datetime, timezone
from types import SimpleNamespace
from datetime import timedelta

import pytest
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.services import news_publication_service as publication
from app.crud.news_publication import NewsPublicationError
from test_news_automation import status_db

NOW = datetime(2026, 10, 22, tzinfo=timezone.utc)


class FakeSession:
    def __init__(self, rows=()):
        self.rows = rows
        self.reads = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass

    def begin(self):
        return nullcontext()

    def scalars(self, query):
        self.reads.append(query)
        return self.rows


def test_expiry_off_does_not_even_select_cases_or_touch_lifecycle(monkeypatch):
    db = FakeSession([1])
    monkeypatch.setattr(publication, 'read_configuration', lambda _db: SimpleNamespace(automatic_expiry_enabled=False))
    monkeypatch.setattr(publication, 'expire_case', lambda *_args, **_kwargs: pytest.fail('expiry disabled'))
    summary = publication.process_news_expiry(lambda: db, clock=lambda: NOW)
    assert summary == publication.PublicationSummary() and not db.reads


def test_pause_after_selection_stops_expiry(monkeypatch):
    switches = iter([True, False])
    monkeypatch.setattr(publication, 'read_configuration', lambda _db: SimpleNamespace(automatic_expiry_enabled=next(switches)))
    monkeypatch.setattr(publication, 'expire_case', lambda *_args, **_kwargs: pytest.fail('operator paused expiry'))
    assert publication.process_news_expiry(lambda: FakeSession([1, 2]), clock=lambda: NOW).expired == 0


@pytest.mark.parametrize('limit', [0, 201])
def test_invalid_limit_does_not_open_storage(limit):
    with pytest.raises(ValueError, match='Invalid publication limit'):
        publication.process_news_expiry(lambda: pytest.fail('invalid limit opened storage'), limit=limit)


def test_storage_failure_at_selection_is_bounded(monkeypatch):
    def unavailable():
        raise SQLAlchemyError('private credentials in underlying exception')
    summary = publication.process_news_expiry(unavailable, clock=lambda: NOW)
    assert summary.skipped == [{'reason_code': 'maintenance_storage_unavailable'}]
    assert 'private' not in str(summary)


def test_case_failures_are_separate_and_do_not_undo_other_expiry(monkeypatch):
    monkeypatch.setattr(publication, 'read_configuration', lambda _db: SimpleNamespace(automatic_expiry_enabled=True))
    def expire(_db, case_id, *, now):
        assert now == NOW
        if case_id == 1:
            raise SQLAlchemyError('private details')
        if case_id == 2:
            raise NewsPublicationError('stale_case_revision')
        return object() if case_id == 3 else None
    monkeypatch.setattr(publication, 'expire_case', expire)
    summary = publication.process_news_expiry(lambda: FakeSession([1, 2, 3, 4]), clock=lambda: NOW)
    assert summary.expired == 1
    assert summary.skipped == [{'case_id': 1, 'reason_code': 'maintenance_storage_unavailable'},
                               {'case_id': 2, 'reason_code': 'stale_case_revision'}]
    assert summary.published == summary.cleared == summary.needs_review == 0


def test_normal_publication_calls_shared_expiry_once_and_combines_results(monkeypatch):
    monkeypatch.setattr(publication, 'read_configuration', lambda _db: SimpleNamespace(news_publication_enabled=True))
    monkeypatch.setattr(publication, 'selected_news_sources', lambda *_args: ())
    calls = []
    def maintain(factory, **kwargs):
        calls.append(kwargs)
        return publication.PublicationSummary(expired=3, skipped=[{'reason_code': 'maintenance_storage_unavailable'}])
    monkeypatch.setattr(publication, 'process_news_expiry', maintain)
    summary = publication.process_news_publications(lambda: FakeSession(), policy=SimpleNamespace(fingerprint='test'),
        clock=lambda: NOW, limit=17)
    assert summary.expired == 3 and summary.skipped == [{'reason_code': 'maintenance_storage_unavailable'}]
    assert len(calls) == 1 and calls[0]['limit'] == 17 and calls[0]['clock']() == NOW


@pytest.mark.asyncio
@pytest.mark.parametrize('errors', [[], [{'reason_code': 'maintenance_storage_unavailable'}]])
async def test_scheduler_keeps_maintenance_and_configuration_outcomes_separate(status_db, monkeypatch, errors):
    from app.models.setting import SystemSetting
    from app.schemas.configuration import ConfigurationRuntime, NewsStageHealth, OperationalSettings
    from app.services.configuration_service import CONFIG_KEY, RUNTIME_KEY
    from app.services.news_scheduler_service import run_scheduled_news_tick
    from app.services.news_sources import load_news_sources
    import app.services.flood_event_service as events
    import app.services.news_weather_controller_service as weather
    import app.services.news_pipeline_service as pipeline
    from app.services.news_claim_auditor import NewsClaimAuditor

    factory = sessionmaker(bind=status_db.get_bind())
    # SQLite-only monitoring fixture: emulate the job's outer advisory lock.
    # Native PostGIS lifecycle tests cover real case/configuration locks.
    def locks(_connection, _cursor, statement, parameters, _context, _many):
        if statement.startswith(('SELECT pg_try_advisory_lock', 'SELECT pg_advisory_unlock')):
            return 'SELECT 1', ()
        return statement, parameters
    event.listen(status_db.get_bind(), 'before_cursor_execute', locks, retval=True)
    monkeypatch.setattr(weather, 'adaptive_decision', lambda *_args: SimpleNamespace(interval_minutes=30))
    monkeypatch.setattr(events, 'expire_due_zones', lambda *_args, **_kwargs: 0)
    def forbidden(*_args, **_kwargs):
        pytest.fail('Invalid configuration reached dependent work or network')
    for name in ('process_saved_news', 'seed_claim_evaluations', 'evaluate_news_claims', 'process_news_footprints'):
        monkeypatch.setattr(pipeline, name, forbidden)
    monkeypatch.setattr(NewsClaimAuditor, '_request', forbidden)
    monkeypatch.setattr(publication, 'process_news_publications', forbidden)
    monkeypatch.setattr(publication, 'process_news_expiry', lambda *_args, **_kwargs:
        publication.PublicationSummary(expired=0 if errors else 2, skipped=errors))
    monkeypatch.setenv('LANES_NEWS_AUDITOR_BATCH_SIZE', 'private-invalid-setting')
    previous = NOW - timedelta(days=1)
    runtime = ConfigurationRuntime(last_successful_at=previous, stages={
        'maintenance': NewsStageHealth(last_success_at=previous)})
    status_db.add(SystemSetting(key=RUNTIME_KEY, value=runtime.model_dump(mode='json')))
    sources = (load_news_sources()[0],)
    config = OperationalSettings(news_collection_enabled=False, news_source_ids=[sources[0].id])
    status_db.add(SystemSetting(key=CONFIG_KEY, value={'revision': 1, 'settings': config.model_dump(mode='json')}))
    status_db.commit()
    try:
        result = await run_scheduled_news_tick(factory, sources=sources, clock=lambda: NOW)
        assert result['outcome'] == 'requires_attention' and result['error_code'] == 'auditor_configuration_invalid'
        assert result['stage_errors']['pipeline'] == ['auditor_configuration_invalid']
        assert result['maintenance']['expired'] == (0 if errors else 2)
        assert result['stage_errors']['maintenance'] == (['maintenance_storage_unavailable'] if errors else [])
        assert result['stage_outcomes']['maintenance'] == ('requires_attention' if errors else 'completed')
        with factory() as db:
            saved = ConfigurationRuntime.model_validate(db.get(SystemSetting, RUNTIME_KEY).value)
        assert saved.last_successful_at == previous
        assert saved.stages['maintenance'].last_success_at == (previous if errors else NOW)
        assert saved.stage_counts['maintenance']['expired'] == result['maintenance']['expired']
        assert saved.last_cycle.outcome == 'requires_attention' and not saved.running
        assert saved.last_cycle.counts['maintenance']['expired'] == result['maintenance']['expired']
        assert 'private-invalid-setting' not in str(result) + saved.model_dump_json()
    finally:
        event.remove(status_db.get_bind(), 'before_cursor_execute', locks)
