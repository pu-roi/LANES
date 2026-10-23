"""E1.1 real lifecycle/locking checks on owned disposable PostGIS only."""
from datetime import timedelta

import httpx
import pytest
from sqlalchemy import func, select

from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimCase, NewsClaimDecision
from app.models.report import FloodAvoidanceZone, FloodEvent
from app.models.setting import SystemSetting
from app.schemas.configuration import OperationalSettings, ConfigurationRuntime
from app.services.configuration_service import CONFIG_KEY, RUNTIME_KEY
from app.services.news_claim_auditor import AuditorConfigurationError, NewsClaimAuditor
from app.services.news_pipeline_service import run_news_pipeline
from app.services.news_publication_service import process_news_expiry
from test_news_ner_integration import c3b_db
from test_news_publication_lifecycle_postgres import (
    seed_evaluation, publish, activation, POLICY, SOURCES, NOW,
    trusted_synthetic_footprint_assets, fixed_expiry_regression_policy,
)


@pytest.fixture(autouse=True)
def no_network_or_neural_work(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail('Maintenance test attempted provider, article processing or model inference')
    from app.services import news_pipeline_service as pipeline
    from app.services.news_ner_runtime.supervisor import Session
    monkeypatch.setattr(httpx.Client, 'send', forbidden)
    monkeypatch.setattr(httpx.AsyncClient, 'send', forbidden)
    monkeypatch.setattr(NewsClaimAuditor, '_request', forbidden)
    monkeypatch.setattr(Session, 'start', forbidden)
    for name in ('process_saved_news', 'seed_claim_evaluations', 'evaluate_news_claims', 'process_news_footprints'):
        monkeypatch.setattr(pipeline, name, forbidden)


def seed_zone(factory):
    evaluation_id, case_id, _ = seed_evaluation(factory, depth='gutter',
        road_passability='passable_all', audit_access=True)
    publish(factory, evaluation_id)
    activation(factory, case_id)
    return case_id


def snapshot(factory):
    with factory() as db:
        return {
            'cases': [(r.id, r.revision) for r in db.scalars(select(NewsClaimCase).order_by(NewsClaimCase.id))],
            'decisions': [(r.id, r.case_id, r.revision, r.public_state, r.snapshot)
                for r in db.scalars(select(NewsClaimDecision).order_by(NewsClaimDecision.id))],
            'zones': [(r.id, r.is_active, r.expires_at, bytes(r.geometry.data))
                for r in db.scalars(select(FloodAvoidanceZone).order_by(FloodAvoidanceZone.id))],
            'events': [(r.id, r.status) for r in db.scalars(select(FloodEvent).order_by(FloodEvent.id))],
            'versions': db.scalar(select(func.count()).select_from(NewsArticleVersion)),
            'runs': db.scalar(select(func.count()).select_from(NewsExtractionRun)),
        }


@pytest.mark.asyncio
@pytest.mark.parametrize('enabled', [False, True])
async def test_invalid_configuration_maintains_real_zone_only_when_expiry_enabled(c3b_db, monkeypatch, enabled):
    case_id = seed_zone(c3b_db)
    config = OperationalSettings(news_collection_enabled=False, automatic_expiry_enabled=enabled,
                                pasig_ml_expiry_enabled=False)
    with c3b_db() as db, db.begin():
        db.add(SystemSetting(key=CONFIG_KEY, value={'revision': 1, 'settings': config.model_dump(mode='json')}))
    before = snapshot(c3b_db)
    monkeypatch.setenv('LANES_NEWS_AUDITOR_BATCH_SIZE', 'private-invalid-setting')
    results = []
    for _ in range(2):
        with pytest.raises(AuditorConfigurationError) as caught:
            await run_news_pipeline(c3b_db, clock=lambda: NOW + timedelta(days=2), sources=SOURCES)
        assert caught.value.code == 'auditor_configuration_invalid'
        results.append(caught.value.maintenance_summary)
    after = snapshot(c3b_db)
    assert after['versions'] == before['versions'] and after['runs'] == before['runs']
    assert not results[0].skipped and not results[1].skipped
    if enabled:
        assert [r.expired for r in results] == [1, 0]
        assert len(after['decisions']) == len(before['decisions']) + 1
        assert dict(after['cases'])[case_id] == dict(before['cases'])[case_id] + 1
        assert all(not z[1] for z in after['zones'])
        assert all(e[1] == 'ended' for e in after['events'])
        assert [z[3] for z in after['zones']] == [z[3] for z in before['zones']]
    else:
        assert [r.expired for r in results] == [0, 0]
        assert before == after


def test_repeated_independent_expiry_preserves_case_deadlines(c3b_db):
    evaluation_id, case_id, _ = seed_evaluation(c3b_db)
    publish(c3b_db, evaluation_id)
    before = snapshot(c3b_db)
    assert process_news_expiry(c3b_db, clock=lambda: NOW).expired == 0
    assert snapshot(c3b_db) == before
    assert process_news_expiry(c3b_db, clock=lambda: NOW + timedelta(hours=2)).expired == 1
    after = snapshot(c3b_db)
    assert process_news_expiry(c3b_db, clock=lambda: NOW + timedelta(hours=2)).expired == 0
    assert snapshot(c3b_db) == after


@pytest.mark.asyncio
async def test_real_scheduler_retains_configuration_failure_and_expired_count(c3b_db, monkeypatch):
    from app.services.news_scheduler_service import run_scheduled_news_tick
    seed_zone(c3b_db)
    previous = NOW - timedelta(days=1)
    config = OperationalSettings(news_collection_enabled=False, automatic_expiry_enabled=True,
                                pasig_ml_expiry_enabled=False)
    with c3b_db() as db, db.begin():
        db.add(SystemSetting(key=CONFIG_KEY, value={'revision': 1, 'settings': config.model_dump(mode='json')}))
        db.add(SystemSetting(key=RUNTIME_KEY, value=ConfigurationRuntime(last_successful_at=previous).model_dump(mode='json')))
    monkeypatch.setenv('LANES_NEWS_AUDITOR_BATCH_SIZE', 'private-invalid-setting')
    result = await run_scheduled_news_tick(c3b_db, sources=SOURCES, clock=lambda: NOW + timedelta(days=2))
    assert result['outcome'] == 'requires_attention' and result['error_code'] == 'auditor_configuration_invalid'
    assert result['maintenance']['expired'] == 1
    assert result['stage_errors']['pipeline'] == ['auditor_configuration_invalid']
    with c3b_db() as db:
        runtime = ConfigurationRuntime.model_validate(db.get(SystemSetting, RUNTIME_KEY).value)
        assert runtime.last_successful_at == previous and runtime.last_cycle.outcome == 'requires_attention'
        assert runtime.last_cycle.counts['maintenance']['expired'] == 1
    assert 'private-invalid-setting' not in str(result) + runtime.model_dump_json()
