"""Related display groups never collapse evidence, conflicts or distant events."""
import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from unittest.mock import Mock

from app.services.spatial_review_grouping import group_review_identities
from app.services import spatial_review_service
from test_spatial_review import review_db
from test_news_browsing import evidence_db

NOW = datetime(2026, 10, 4, tzinfo=timezone.utc)


def report(record_id, x=0, **change):
    return {"id": record_id, "city": "Pasig", "barangay": "Maybunga",
        "human_readable_location": "Dr. Sixto Antonio Avenue", "created_at": NOW,
        "geometry": {"type": "Point", "coordinates": [x, 0]}, **change}


def grouped(reports, extra=()):
    identities = [{"source": "user_report", "record_id": row["id"], "claim_index": -1, "queued_at": row["created_at"]} for row in reports]
    return group_review_identities(identities + list(extra), reports, projected=True)


def test_nearby_same_road_group_preserves_each_identity_and_news_separation():
    rows = [report(2), report(3, 150, human_readable_location="Dr Sixto Antonio Ave."), report(4, 300), report(6, 1000)]
    news = {"source": "news_claim", "record_id": 2, "claim_index": 0, "queued_at": NOW}
    groups = grouped(rows, [news])
    assert sorted(len(group.identities) for group in groups) == [1, 1, 3]
    group = next(group for group in groups if len(group.identities) == 3)
    assert group.key == "user_report:2"
    assert group.identities == [("user_report", 2, -1), ("user_report", 3, -1), ("user_report", 4, -1)]
    assert group.reason and "before merging" in group.reason


@pytest.mark.parametrize("change", [
    {"geometry": {"type": "Point", "coordinates": [501, 0]}},
    {"created_at": NOW + timedelta(hours=2, seconds=1)},
    {"city": "Quezon City"}, {"city": None},
    {"human_readable_location": "Kaginhawahan Bridge"},
    {"human_readable_location": None}, {"geometry": None}, {"geometry": "invalid"},
])
def test_proximity_alone_unknown_locations_and_old_observations_cannot_group(change):
    assert len(grouped([report(2), report(3, 100, **change)])) == 2


def test_complete_link_prevents_chained_distance_or_time_groups():
    assert sorted(len(group.identities) for group in grouped([report(2), report(3, 400), report(4, 800)])) == [1, 2]
    assert sorted(len(group.identities) for group in grouped([report(2), report(3, 10, created_at=NOW + timedelta(hours=2)), report(4, 20, created_at=NOW + timedelta(hours=4))])) == [1, 2]
    assert len(grouped([report(2), report(3, 500, created_at=(NOW + timedelta(hours=2)).replace(tzinfo=None), city="Pasig City")])) == 1


def test_native_group_geometry_uses_projected_metres():
    from app.crud.spatial_review import list_report_group_metadata
    db = Mock()
    db.get_bind.return_value.dialect.name = "postgresql"
    db.execute.return_value.mappings.return_value = []
    list_report_group_metadata(db)
    sql = str(db.execute.call_args.args[0].compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    assert "ST_AsGeoJSON(ST_Transform" in sql and "32651" in sql
    assert "deleted_at IS NULL" in sql


def test_group_pagination_counts_members_and_preserves_conflicting_measurements(review_db):
    from app.main import app
    from app.core.database import get_db
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    for record_id, offset in [(2, 0), (90, .001)]:
        geometry = json.dumps({"type": "Point", "coordinates": [121.08 + offset, 14.57]})
        db.execute(text("UPDATE flood_reports SET geometry=:geometry, barangay='Maybunga', human_readable_location='Dr Sixto Antonio Avenue', severity=:severity, depth=:depth WHERE id=:id"),
            {"geometry": geometry, "id": record_id, "severity": "low" if record_id == 2 else "high", "depth": "ankle" if record_id == 2 else "waist"})
    for record_id in range(100, 123):
        db.execute(text("INSERT INTO flood_reports SELECT :id, status, deleted_at, created_at, human_readable_location, barangay, city, raw_text, severity, depth, geometry FROM flood_reports WHERE id=2"), {"id": record_id})
    db.commit()
    review_db.clear()
    page = spatial_review_service.browse_spatial_review(db, source="user_reports", page=999, page_size=1)
    assert page.counts == {"all": 27, "user_reports": 25, "news_claims": 2}
    assert page.total == 1 and page.item_total == 25 and page.page == 1
    group = page.items[0]
    assert group.member_count == 25 and len(group.members) == 3
    assert {member.severity for member in group.members} == {"low", "high"}
    members = spatial_review_service.browse_review_members(db, group.key, page=1, page_size=20)
    other = spatial_review_service.browse_review_members(db, group.key, page=2, page_size=20)
    assert members.total == 25 and members.pages == 2 and len(members.items) == 20
    assert len(other.items) == 5
    assert len({item.key for item in members.items + other.items}) == 25
    for key in ("user_report:90", "user_report:122"):
        selected_member = spatial_review_service.browse_review_members(db, key, page=2, page_size=20)
        assert selected_member.key == group.key
        assert selected_member.group_reason == group.group_reason
        assert selected_member.items == other.items
    assert spatial_review_service.browse_review_members(db, "user_report:999", page=1, page_size=20) is None
    generator.close()


@pytest.mark.asyncio
async def test_selected_member_resolves_cross_barangay_group(review_db):
    import httpx
    from app.main import app
    from app.core.database import get_db
    from test_news_browsing import staff
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    for record_id in (3, 4):
        db.execute(text("INSERT INTO flood_reports SELECT :id, status, deleted_at, created_at, human_readable_location, barangay, city, raw_text, severity, depth, geometry FROM flood_reports WHERE id=2"), {"id": record_id})
    for record_id in (2, 3, 4):
        db.execute(text("UPDATE flood_reports SET geometry=:geometry, barangay=:barangay, human_readable_location='Dr Sixto Antonio Avenue' WHERE id=:id"), {
            "id": record_id, "barangay": "Rosario" if record_id == 3 else "Maybunga",
            "geometry": json.dumps({"type": "Point", "coordinates": [121.08 + (record_id - 2) * .0007, 14.57]}),
        })
    db.commit()
    generator.close()
    review_db.clear()
    staff()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        for record_id, expected in ((2, [2, 3, 4]), (4, [2, 3, 4]), (3, [2, 3, 4])):
            response = await client.get(f"/api/v1/admin/review/groups/user_report:{record_id}/members")
            assert response.status_code == 200, response.text
            body = response.json()
            assert [item["report_id"] for item in body["items"]] == expected
            assert body["key"] == f"user_report:{expected[0]}"
            assert bool(body["group_reason"]) == (len(expected) > 1)


def test_cross_street_geometry_and_cross_barangay_names_allow_review():
    assert len(grouped([report(2), report(3, 150, barangay="Rosario")])) == 1
    assert len(grouped([report(2), report(3, 49, human_readable_location="Second Street")])) == 1
    assert len(grouped([report(2), report(3, 51, human_readable_location="Second Street")])) == 2
