"""Scale-oriented reads are bounded and preserve deterministic grouping."""
import random
from types import SimpleNamespace
import httpx
import pytest
from app.api import deps
from app.core.database import get_db
from app.main import app
from app.services.spatial_browse_service import parse_bbox
from app.services.zone_queue_service import indexed_zone_groups, zone_facts, related_zones
from app.services.spatial_grouping import complete_link_groups
from test_zone_queue import row


def test_indexed_grouping_matches_complete_link_on_randomized_inputs():
    randomizer = random.Random(3402)
    for _ in range(30):
        rows = [zone_facts(row(index, randomizer.randrange(1000), road=randomizer.choice(["A", "B", None]),
            city=randomizer.choice(["Pasig", "Cainta"])), projected=True) for index in range(1, 100)]
        expected = [[item["id"] for item in group] for group in complete_link_groups(rows, related_zones)]
        randomizer.shuffle(rows)
        assert [[item["id"] for item in group] for group in indexed_zone_groups(rows)] == expected


@pytest.mark.parametrize("count", [1000, 10000])
@pytest.mark.parametrize("length", [10, 1000])
def test_coincident_groups_do_not_require_quadratic_distance_checks(count, length, monkeypatch):
    from app.services import zone_queue_service as service
    from shapely.geometry import LineString
    facts = zone_facts(row(1), projected=True)
    facts["group_geometry"] = LineString([(0,0),(length,0)])
    rows = [{**facts, "id": index} for index in range(count)]
    calls = []
    original = service.related_zones
    def counted(a, b):
        calls.append(1)
        return original(a, b)
    monkeypatch.setattr(service, "related_zones", counted)
    assert len(indexed_zone_groups(rows)) == 1
    assert len(calls) <= count


@pytest.mark.parametrize("value", ["0,0,0,1", "nan,0,1,1", "0,0,1", "-181,0,1,1", "0,-90,1,1"])
def test_invalid_viewport_is_rejected(value):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as error:
        parse_bbox(value)
    assert error.value.status_code == 422


@pytest.mark.asyncio
async def test_new_reads_require_staff_without_touching_storage():
    paths = ["/admin/zones/count", "/admin/zones/map", "/admin/flood-events/records", "/admin/flood-events/map",
        "/admin/flood-events/1/inspection", "/admin/flood-events/1/inspection/reports", "/admin/zones/1/contributors"]
    app.dependency_overrides[get_db] = lambda: SimpleNamespace()
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            for path in paths:
                assert (await client.get("/api/v1"+path)).status_code == 401
            app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Commuter"))
            for path in paths:
                assert (await client.get("/api/v1"+path)).status_code == 403
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(deps.get_current_user, None)
