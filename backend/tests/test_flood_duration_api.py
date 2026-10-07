"""Staff preview authorization, abstention and visible artifact failures."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI

from app.api.deps import get_current_user
from app.api.v1.endpoints import flood_duration
from app.schemas.flood_subsidence import DurationPreviewRequest
from app.services import flood_subsidence_prediction_service as service


NOW = datetime(2026, 10, 7, tzinfo=timezone.utc)


def payload(**changes):
    return {'city': 'Pasig', 'barangay': 'Maybunga', 'reference_at': NOW.isoformat(),
        'prediction_as_of_at': NOW.isoformat(), 'reference_policy': 'first_recorded_wet_in_episode',
        'acknowledge_research_limitations': True, **changes}


@pytest.fixture
def api():
    application = FastAPI()
    application.include_router(flood_duration.router, prefix='/admin/news')
    return application


def staff(api, role='Officer', permissions=None):
    api.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        role=SimpleNamespace(name=role, permissions=permissions if permissions is not None else {'reports': 'view'}))


@pytest.mark.asyncio
async def test_unauthorized_requests_never_load_model(api, monkeypatch):
    def forbidden_load():
        raise AssertionError('Unauthorized model lookup')
    monkeypatch.setattr(flood_duration, 'load_research_model', forbidden_load)
    monkeypatch.setattr(service, 'load_research_model', forbidden_load)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url='http://test') as client:
        for role, permissions, status in [(None, None, 401), ('Commuter', {'reports': 'full'}, 403),
                                          ('Officer', {}, 403), ('Officer', {'reports': 'none'}, 403)]:
            if role:
                staff(api, role, permissions)
            assert (await client.get('/admin/news/duration-model')).status_code == status
            assert (await client.post('/admin/news/duration-preview', json=payload())).status_code == status


@pytest.mark.asyncio
async def test_staff_can_inspect_read_only_model_and_preview(api):
    staff(api)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url='http://test') as client:
        status = await client.get('/admin/news/duration-model')
        assert status.status_code == 200 and status.headers['cache-control'] == 'no-store'
        assert status.json()['shared_outcomes'] == 3
        response = await client.post('/admin/news/duration-preview', json=payload())
        assert response.status_code == 200 and response.headers['cache-control'] == 'no-store'
        body = response.json()
        assert body['status'] == 'research_estimate' and len(body['quantiles']) == 3
        assert body['changes_status_expiry_or_routing'] is False
        assert body['confirms_physical_dryness_or_passability'] is False
        assert body['model']['deployment_eligible'] is False


@pytest.mark.parametrize('changes,reason', [
    ({'acknowledge_research_limitations': False}, 'conditional_research_assumptions_not_acknowledged'),
    ({'city': 'Manila'}, 'outside_pasig_research_scope'),
    ({'barangay': 'Kapitolyo'}, 'barangay_not_represented_in_conditional_experiment'),
    ({'prediction_as_of_at': (NOW + timedelta(minutes=2)).isoformat()}, 'future_issuance_time'),
    ({'reference_at': (NOW - timedelta(minutes=1)).isoformat()}, 'elapsed_time_requires_explicit_uninterrupted_episode_assumption'),
    ({'reference_at': (NOW - timedelta(minutes=2001)).isoformat(), 'assume_continuous_wet': True}, 'reference_age_exceeds_experimental_evidence_support'),
])
def test_scope_and_evidence_abstentions(changes, reason):
    result = service.preview_subsidence(DurationPreviewRequest(**payload(**changes)), now=NOW)
    assert result.status == 'abstained' and result.abstention_reason == reason
    assert not result.quantiles and not result.horizon_probabilities


@pytest.mark.asyncio
@pytest.mark.parametrize('change', [{'reference_at': '2026-10-07T00:00:00'},
    {'prediction_as_of_at': (NOW - timedelta(minutes=1)).isoformat()}, {'unknown': 1}])
async def test_invalid_requests_are_visible_422(api, change):
    staff(api)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url='http://test') as client:
        assert (await client.post('/admin/news/duration-preview', json=payload(**change))).status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize('content', [b'{invalid', b'x' * 65537, b'{}'], ids=['malformed-json', 'oversized', 'missing-fields'])
async def test_invalid_artifact_returns_sanitized_503(api, monkeypatch, tmp_path, content):
    path = tmp_path / 'private-artifact.json'
    path.write_bytes(content)
    monkeypatch.setenv('LANES_FLOOD_DURATION_MODEL_PATH', str(path))
    staff(api)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url='http://test') as client:
        for response in (await client.get('/admin/news/duration-model'),
                         await client.post('/admin/news/duration-preview', json=payload())):
            assert response.status_code == 503
            assert str(path) not in response.text


def test_missing_artifact_abstains(monkeypatch, tmp_path):
    monkeypatch.setenv('LANES_FLOOD_DURATION_MODEL_PATH', str(tmp_path / 'missing.json'))
    result = service.preview_subsidence(DurationPreviewRequest(**payload()), now=NOW)
    assert result.abstention_reason == 'research_model_unavailable'


def test_checksum_pin_and_incompatible_lineage_reject(monkeypatch, tmp_path):
    original = service.DEFAULT_MODEL.read_bytes()
    path = tmp_path / 'model.json'
    path.write_bytes(original)
    monkeypatch.setenv('LANES_FLOOD_DURATION_MODEL_PATH', str(path))
    monkeypatch.setenv('LANES_FLOOD_DURATION_MODEL_SHA256', 'wrong')
    with pytest.raises(ValueError, match='checksum'):
        service.load_research_model()
    monkeypatch.setenv('LANES_FLOOD_DURATION_MODEL_SHA256', hashlib.sha256(original).hexdigest())
    assert service.load_research_model()[0] is not None
    changed = json.loads(original)
    changed['lineage']['deployment_eligible'] = True
    path.write_text(json.dumps(changed), encoding='utf-8')
    monkeypatch.delenv('LANES_FLOOD_DURATION_MODEL_SHA256')
    with pytest.raises(ValueError, match='incompatible'):
        service.load_research_model()


def test_preview_routes_are_registered_in_actual_application():
    from app.main import app
    routes = {route.path: route.methods for route in app.routes if hasattr(route, 'methods')}
    assert 'GET' in routes['/api/v1/admin/news/duration-model']
    assert 'POST' in routes['/api/v1/admin/news/duration-preview']
