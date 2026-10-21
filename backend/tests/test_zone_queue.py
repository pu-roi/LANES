"""Spatial queue groups retain distinct records and never write lifecycle state."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from shapely.geometry import LineString, box, mapping
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError

from app.api import deps
from app.core.database import get_db
from app.crud.zone_queue import queue_metadata
from app.main import app
from app.services import zone_queue_service as service
from app.services.spatial_grouping import complete_link_groups

NOW = datetime(2026, 10, 21, tzinfo=timezone.utc)


def row(id, x=0, *, road="Test Avenue", city="Pasig", barangay="Maybunga", source="direct_user", **changes):
    original = mapping(LineString([(x, 0), (x + 10, 0)]))
    reports = [] if source in {"official", "news"} else [{"id": id, "source": source,
        "human_readable_location": road, "city": city, "barangay": barangay, "raw_text": f"Evidence {id}",
        "severity": "medium", "depth": "knee", "geometry": original}]
    news = [{"claim": {"canonical_road": road, "canonical_city": city, "canonical_barangay": barangay},
             "snapshot": {"public": {"evidence_excerpt": f"News evidence {id}"}}}] if source == "news" else []
    return {"id": id, "geometry": mapping(box(x, 0, x + 10, 10)), "source_geometry": original,
        "reports": reports, "news": news,
        "created_at": NOW + timedelta(hours=id * 4), "name": f"Zone {id}", "curated_by_admin_id": 7 if source == "official" else None,
        "severity_override": None, "depth_override": None, "admin_notes": None, **changes}


def grouped(rows):
    facts = [service.zone_facts(item, projected=True) for item in rows]
    return complete_link_groups(facts, service.related_zones)


@pytest.mark.parametrize("gap, expected", [(0, 1), (50, 1), (50.01, 2), (500, 2)])
def test_matching_road_original_distance_and_no_time_cutoff(gap, expected):
    assert len(grouped([row(1), row(2, 10 + gap, road="Test Ave.", city="Pasig City")])) == expected


@pytest.mark.parametrize("change", [{"road": "Other Street"}, {"city": "Cainta"}, {"road": None}, {"city": None}, {"source": "official"}])
def test_different_or_missing_locations_stay_separate_even_when_overlapping(change):
    assert len(grouped([row(1), row(2, **change)])) == 2
    assert len(grouped([row(1), row(2, 60, **change)])) == 2
    assert len(grouped([row(1), row(2, 60.01, **change)])) == 2


def test_overlap_cross_source_cross_barangay_invalid_geometry_and_chain():
    official = row(2, 5, source="manual_seeder", curated_by_admin_id=7)
    assert len(grouped([row(1), official, row(3, 8, source="news", barangay="Rosario")])) == 1
    assert [len(group) for group in grouped([row(1), row(2, 50), row(3, 100)])] == [2, 1]
    for invalid in (None, "invalid", mapping(LineString())):
        other = row(2, source_geometry=invalid)
        other["reports"][0]["geometry"] = invalid
        assert len(grouped([row(1), other])) == 2


@pytest.mark.parametrize("location", [{"human_readable_location": "Other Road"}, {"city": "Cainta"}, {"city": None}])
def test_ambiguous_or_incomplete_locations_cannot_group(location):
    other = row(2)
    other["reports"].append({**other["reports"][0], **location})
    assert len(grouped([row(1), other])) == 2


def test_original_geometry_precedence_and_combined_report_fallback():
    other = row(2, 100)
    other["reports"][0]["geometry"] = row(1)["source_geometry"]
    assert len(grouped([row(1), other])) == 2  # Saved source takes precedence.
    for invalid in (None, "invalid"):
        other["source_geometry"] = invalid
        assert len(grouped([row(1), other])) == 1
    other["reports"][0]["geometry"] = row(2, 200)["source_geometry"]
    other["reports"].append({**other["reports"][0], "id": 3, "geometry": row(3)["source_geometry"]})
    assert len(grouped([row(1), other])) == 1  # All valid report extents participate.
    other["reports"][0]["geometry"] = "invalid"
    assert len(grouped([row(1), other])) == 1


def test_short_segment_within_long_segment_does_not_require_matching_centres():
    long = row(1, source_geometry=mapping(LineString([(0, 0), (1000, 0)])))
    assert len(grouped([long, row(2, 5)])) == 1


def test_expanded_polygons_do_not_make_distant_original_geometry_qualify():
    first = row(69, road="M. H. del Pilar Street", source_geometry=mapping(LineString([(0, 0), (200, 0)])),
                geometry=mapping(box(-25, -25, 225, 25)))
    second = row(70, road="Doctor Pilapil Street", source_geometry=mapping(LineString([(0, 77.5), (200, 77.5)])),
                 geometry=mapping(box(-25, 52.5, 225, 102.5)))
    assert len(grouped([first, second])) == 2
    second["reports"][0]["human_readable_location"] = "M. H. del Pilar Street"
    assert len(grouped([first, second])) == 2  # Still outside 50 m on the same road.


def test_news_without_original_geometry_cannot_use_the_avoidance_polygon():
    assert len(grouped([row(1), row(2, source="news", source_geometry=None)])) == 2


@pytest.fixture
def queue(monkeypatch):
    rows = [row(1), row(2, 30, barangay="Rosario", severity_override="high", depth_override="waist"),
            row(3, 35, source="manual_seeder", curated_by_admin_id=7), row(4, 45, source="news"), row(5, 5000, source="facebook")]
    db = SimpleNamespace(get_bind=lambda: SimpleNamespace(dialect=SimpleNamespace(name="postgresql")))
    monkeypatch.setattr(service, "queue_metadata", lambda _db, active_only: rows)
    monkeypatch.setattr(service, "zone_details", lambda _db, selected, **_options: [])
    return db, rows


def test_filter_any_member_preserves_whole_group_and_counts(queue):
    db, _ = queue
    result = service.browse_zone_queue(db, q="Evidence 2", city="Pasig", barangay="Rosario", severity="high", page_size=1)
    assert result.total == 1 and result.item_total == 4 and result.items[0].zone_id == 1
    assert result.items[0].member_count == 4
    assert set(result.items[0].sources) == {"user_reports", "news", "official"}
    assert result.items[0].severity_levels == ["medium", "high"]
    assert result.counts == {"all": 5, "user_reports": 2, "news": 1, "official": 1, "other": 1}
    # Do not combine attributes from different zones or different location rows.
    assert service.browse_zone_queue(db, source="official", severity="high").total == 0
    assert service.browse_zone_queue(db, city="Pasig", barangay="Rosario", q="Evidence 1").total == 0
    assert service.browse_zone_queue(db, source="news").items[0].member_count == 4


def test_ordering_group_pages_members_and_history(queue):
    db, _ = queue
    first = service.browse_zone_queue(db, page_size=1)
    last = service.browse_zone_queue(db, page=999, page_size=1)
    assert first.items[0].zone_id == 5 and last.items[0].zone_id == 1
    assert last.page == 2 and last.pages == 2
    assert service.browse_zone_members(db, 4, page=999, page_size=2).zone_id == 1
    assert service.browse_zone_members(db, 4, page=999, page_size=2).page == 2
    assert service.browse_zone_members(db, 4, page_size=2).page == 2
    assert service.browse_zone_members(db, 999) is None
    history = service.browse_zone_queue(db, active_only=False)
    assert history.total == history.item_total == 5
    assert all(item.member_count == 1 for item in history.items)


def test_search_includes_secondary_report_ids_roads_and_news_titles(queue):
    db, rows = queue
    rows[0]["reports"].append({**rows[0]["reports"][0], "id": 42, "raw_text": "Secondary witness evidence"})
    rows[3]["news"][0]["snapshot"]["public"]["source_title"] = "Original source headline"
    assert service.browse_zone_queue(db, q="Report #42").total == 1
    assert service.browse_zone_queue(db, q="Secondary witness").total == 1
    assert service.browse_zone_queue(db, q="Original source headline").total == 1
    assert service.browse_zone_queue(db, q="Test Avenue").item_total == 5


def test_camera_bounds_include_all_members_before_pagination_and_filtering(queue):
    db, rows = queue
    for index, item in enumerate(rows[:4]):
        item["map_geometry"] = mapping(box(121.08 + index * .0001, 14.57, 121.0801 + index * .0001, 14.5701))
    result = service.browse_zone_queue(db, q="Evidence 2", page_size=1)
    assert result.items[0].member_count == 4
    assert result.items[0].bounds == pytest.approx((121.08, 14.57, 121.0804, 14.5701))
    # A displayed group's extent is independent of the selected member page.
    service.browse_zone_members(db, 4, page=2, page_size=2)
    assert service.browse_zone_queue(db, q="Evidence 2").items[0].bounds == result.items[0].bounds
    rows[0]["map_geometry"] = None
    assert service.browse_zone_queue(db, q="Evidence 2").items[0].bounds[0] == pytest.approx(121.0801)


def test_camera_bounds_unavailable_or_out_of_range_are_not_guessed(queue):
    db, rows = queue
    assert all(item.bounds is None for item in service.browse_zone_queue(db).items)
    rows[0]["map_geometry"] = mapping(box(200, 14, 201, 15))
    assert service.browse_zone_queue(db, q="Evidence 1").items[0].bounds is None


def test_metadata_uses_shared_eligibility_and_projected_geometry(monkeypatch):
    from app.crud.report import avoidance_zones_query
    db = Mock()
    db.get_bind.return_value.dialect.name = "postgresql"
    monkeypatch.setattr("app.services.configuration_service.read_configuration", lambda _db: SimpleNamespace(automatic_expiry_enabled=True))
    monkeypatch.setattr("app.services.local_news_scenario_service.sql_clock", lambda _id, _kind, clock: clock)
    # Compile the real eligibility expression instead of replacing it with test logic.
    from sqlalchemy.orm import Session
    session = Session()
    query = avoidance_zones_query(session, active_only=True, now=NOW)
    sql = str(query.statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    assert "is_active = true" in sql and "expires_at >" in sql
    query_stub = Mock()
    query_stub.with_entities.return_value.all.return_value = []
    monkeypatch.setattr("app.crud.zone_queue.avoidance_zones_query", lambda *_args, **_kw: query_stub)
    queue_metadata(db, active_only=True)
    geometry = query_stub.with_entities.call_args.args[-1]
    assert "ST_Transform" in str(geometry.compile(dialect=postgresql.dialect()))
    source = query_stub.with_entities.call_args.args[-3]
    assert "ST_Transform(flood_avoidance_zones.source_geometry" in str(source.compile(dialect=postgresql.dialect()))
    session.close()


@pytest.mark.asyncio
async def test_routes_auth_validation_failures_and_no_mutations(queue, monkeypatch):
    db, rows = queue
    original = repr(rows)
    app.dependency_overrides[get_db] = lambda: db
    paths = ["/api/v1/admin/zones/queue", "/api/v1/admin/zones/groups/4/members"]
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            for path in paths:
                assert (await client.get(path)).status_code == 401
            app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Commuter"))
            for path in paths:
                assert (await client.get(path)).status_code == 403
            app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Admin"))
            for path in paths:
                response = await client.get(path)
                assert response.status_code == 200, response.text
                assert response.json()["read_only"] is True
            for params in [{"page": 0}, {"page_size": 101}, {"source": "invalid"}, {"severity": "invalid"}, {"q": "x" * 121}]:
                assert (await client.get(paths[0], params=params)).status_code == 422
            assert (await client.get("/api/v1/admin/zones/groups/999/members")).status_code == 404
            monkeypatch.setattr(service, "queue_metadata", Mock(side_effect=SQLAlchemyError("storage offline")))
            for path in paths:
                assert (await client.get(path)).status_code == 503
        assert repr(rows) == original
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(deps.get_current_user, None)
