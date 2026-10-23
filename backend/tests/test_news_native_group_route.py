"""The existing native detail route accepts IDs emitted by both saved pipelines."""
from unittest.mock import patch

import httpx
import pytest

from app.api import deps
from app.core.database import get_db
from app.main import app


@pytest.mark.asyncio
@pytest.mark.parametrize('group_id',['g0','g12','resolved-n13','resolved-n50'])
async def test_saved_group_ids_reach_protected_reader(group_id):
    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[deps.get_current_active_admin] = lambda: object()
    try:
        with patch('app.api.v1.endpoints.admin_news.read_native_group',return_value=None) as reader:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
                response = await client.get('/api/v1/admin/news/results/380/groups/'+group_id)
            assert response.status_code == 404  # Valid ID, absent record; never path-validation 422.
            assert reader.call_args.args[1:3] == (380,group_id)
    finally:
        app.dependency_overrides.pop(get_db,None)
        app.dependency_overrides.pop(deps.get_current_active_admin,None)


@pytest.mark.asyncio
@pytest.mark.parametrize('group_id',['resolved-n-1','resolved-nx','other-n13','resolved-n'+'9'*30])
async def test_malformed_group_ids_remain_rejected(group_id):
    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[deps.get_current_active_admin] = lambda: object()
    try:
        with patch('app.api.v1.endpoints.admin_news.read_native_group') as reader:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
                response = await client.get('/api/v1/admin/news/results/380/groups/'+group_id)
            assert response.status_code == 422
            reader.assert_not_called()
    finally:
        app.dependency_overrides.pop(get_db,None)
        app.dependency_overrides.pop(deps.get_current_active_admin,None)


@pytest.mark.asyncio
async def test_corrected_group_detail_still_requires_admin_authentication():
    app.dependency_overrides[get_db] = lambda: None
    try:
        with patch('app.api.v1.endpoints.admin_news.read_native_group') as reader:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
                response = await client.get('/api/v1/admin/news/results/380/groups/resolved-n13')
            assert response.status_code == 401
            reader.assert_not_called()
    finally:
        app.dependency_overrides.pop(get_db,None)
