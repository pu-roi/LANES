"""Pinned-origin policy exercised only on owned disposable PostGIS databases."""
import json

import pytest
from sqlalchemy import event

from app.crud.news_historical_processing import enqueue_historical_captures
from app.services import news_historical_processing as service
from app.services.news_ner_durable import processing
from app.services.news_ner_durable.contracts import NerEvidenceError
from app.services.news_historical_preparation import PreparationError
from test_news_historical_e1 import origin_package, authorization
from test_news_historical_processing_postgres import (historical, isolation, snapshot, check_no_publication,
                                                      SOURCES, c3b_db, trusted, NOW)


def origin(h, tmp_path):
    package = origin_package(h.trusted, tmp_path, h.engine)
    auth = authorization(package, h.trusted, h.engine, tmp_path)
    options = {**h.options, 'environment': 'production', 'authorization': auth}
    return package, auth, options


@pytest.mark.asyncio
async def test_origin_policy_readonly_preflight_and_exact_owned_processing(historical, tmp_path):
    h = historical
    package, auth, options = origin(h, tmp_path)
    before = snapshot(h); statements = []
    def observed(_conn, _cursor, statement, _params, _context, _many):
        statements.append(statement.strip())
    event.listen(h.engine, 'before_cursor_execute', observed)
    try:
        result = service.preflight_historical(h.engine, package, h.trusted, **options)
    finally:
        event.remove(h.engine, 'before_cursor_execute', observed)
    assert result['status'] == 'ready' and snapshot(h) == before
    assert statements[0] == 'SET TRANSACTION READ ONLY'
    assert all(s.startswith(('SET', 'SELECT', 'SHOW')) for s in statements)
    result = await service.process_historical(h.engine, package, h.trusted,
        runtime_factory=lambda _: h.runtime, clock=lambda: NOW, **options)
    assert result['status'] == 'completed', result
    assert result['historical_qualification_status'] == 'qualified'
    assert h.runtime.requests == 2
    after = snapshot(h)
    repeated = await service.process_historical(h.engine, package, h.trusted,
        runtime_factory=lambda _: pytest.fail('completed historical run inferred again'), clock=lambda: NOW, **options)
    assert repeated['status'] == 'completed' and repeated['runs'] == result['runs']
    assert repeated['historical_interpretations'] == result['historical_interpretations']
    assert snapshot(h) == after
    check_no_publication(h)


@pytest.mark.asyncio
async def test_ordinary_worker_cannot_use_origin_without_bound_authority(historical, tmp_path):
    h = historical
    package, auth, _ = origin(h, tmp_path)
    with pytest.raises(NerEvidenceError, match='ner_configuration_invalid'):
        await processing.process_native_saved_news(h.factory, load_assets=lambda: h.trusted,
            environment='production', database_url=h.engine.url.render_as_string(hide_password=False), run_ids=())
    with pytest.raises(NerEvidenceError, match='ner_configuration_invalid'):
        await processing.process_native_saved_news(h.factory, load_assets=lambda: h.trusted,
            environment='production', database_url=h.engine.url.render_as_string(hide_password=False),
            historical_authorization=auth)  # No exact selection is forbidden.
    before = snapshot(h)
    with h.factory() as db:
        with pytest.raises(PreparationError, match='historical_run_selection_invalid'):
            auth.validate_session(db, (99999,), SOURCES)
    assert snapshot(h) == before and h.runtime.starts == 0
    check_no_publication(h)


@pytest.mark.asyncio
async def test_policy_change_between_preflight_and_enqueue_prevents_writes(historical, tmp_path, monkeypatch):
    h = historical
    package, auth, options = origin(h, tmp_path)
    before = snapshot(h)
    original = service.preflight_historical
    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        auth.policy['publication_allowed'] = True
        return result
    monkeypatch.setattr(service, 'preflight_historical', changed)
    with pytest.raises(PreparationError, match='historical_target_policy_changed'):
        await service.process_historical(h.engine, package, h.trusted,
            runtime_factory=lambda _: h.runtime, **options)
    assert snapshot(h) == before and h.runtime.starts == 0


def test_authority_rejects_unrelated_native_run_even_in_same_database(historical, tmp_path):
    h = historical
    package, auth, _ = origin(h, tmp_path)
    from copy import deepcopy
    from app.crud.news_processing import enqueue_input_snapshot
    from app.services.news_ner_durable.contracts import sha
    with h.factory() as db, db.begin():
        selected = enqueue_historical_captures(db, package.captures, h.trusted.pipeline_version)
        other = deepcopy(package.captures[0]['input_snapshot'])
        other['article_text'] += ' This is not a selected frozen source.'
        run_id = enqueue_input_snapshot(db, 101, other, sha(other), mode='ner_rules_v1',
                                        pipeline_version=h.trusted.pipeline_version)
    with h.factory() as db:
        auth.validate_session(db, selected, SOURCES)
        with pytest.raises(PreparationError, match='historical_run_selection_invalid'):
            auth.validate_session(db, (run_id,), SOURCES)
    check_no_publication(h)


@pytest.mark.asyncio
async def test_interpretation_failure_keeps_completed_evidence_and_surfaces_attention(historical, monkeypatch):
    h = historical
    from app.services import news_historical_interpretation as adapter
    original = adapter.interpret_historical
    def failed(*_args, **_kwargs):
        raise ValueError('private fixture detail must not reach stdout')
    monkeypatch.setattr(adapter, 'interpret_historical', failed)
    result = await service.process_historical(h.engine, h.package, h.trusted,
        runtime_factory=lambda _: h.runtime, clock=lambda: NOW, **h.options)
    assert result['status'] == 'requires_attention'
    assert result['historical_qualification_status'] == 'failed'
    assert result['historical_qualification_error_code'] == 'historical_interpretation_failed'
    assert all(r['status'] == 'completed' for r in result['runs'])
    assert 'private fixture detail' not in json.dumps(result)
    before = snapshot(h)
    monkeypatch.setattr(adapter, 'interpret_historical', original)
    repeated = await service.process_historical(h.engine, h.package, h.trusted,
        runtime_factory=lambda _: pytest.fail('Qualification failure retried model'), clock=lambda: NOW, **h.options)
    assert repeated['status'] == 'completed' and snapshot(h) == before
    check_no_publication(h)
