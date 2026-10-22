"""Scale and compatibility acceptance on an owned disposable database only."""
import json
import time
import os
import statistics
from datetime import datetime, timezone
from geoalchemy2.shape import from_shape
from shapely.geometry import box
from sqlalchemy import text, event as sql_event
from fastapi.testclient import TestClient
import pytest
from app import models
from app.api import deps
from app.core.database import get_db
from app.main import app
from app.services.spatial_browse_service import history_cards, map_read
from app.services.zone_queue_service import browse_zone_queue
from test_operational_settings_postgres import isolated_db


@pytest.mark.parametrize("count", [1000, 10000])
def test_complete_history_and_bounded_viewport_at_scale(isolated_db, count):
    db, staff = isolated_db
    events = db.execute(text("""INSERT INTO flood_events
        (status,verified_at,ended_at,peak_severity,created_at,updated_at)
        SELECT 'ended',now(),now(),'medium',now(),now() FROM generate_series(1,:count) RETURNING id"""), {"count": count}).scalars().all()
    db.execute(text("""INSERT INTO flood_avoidance_zones
        (event_id,geometry,source_geometry,is_active,severity_override,created_at,updated_at)
        SELECT id, ST_MakeEnvelope(121.08,14.57,121.0801,14.5701,4326),
          ST_GeomFromText('LINESTRING(121.08 14.57,121.0801 14.57)',4326),true,'medium',now(),now()
        FROM flood_events"""))
    db.execute(text("""INSERT INTO flood_reports
        (zone_id,event_id,raw_text,source,severity,status,human_readable_location,city,is_public,is_bidirectional,created_at,updated_at)
        SELECT id,event_id,'Scale evidence','direct_user','medium','approved','Scale Road','Pasig',false,false,now(),now()
        FROM flood_avoidance_zones"""))
    db.commit()
    # Bulk fixture inserts precede autovacuum; give the planner the statistics
    # a maintained production database normally has before timing reads.
    for table in ("flood_events", "flood_avoidance_zones", "flood_reports"):
        db.execute(text("ANALYZE " + table))
    statements = []
    def record(_connection, _cursor, statement, _parameters, _context, _many): statements.append(statement)
    connection = db.connection(); sql_event.listen(connection, "before_cursor_execute", record)
    filters = {"status_filter": "all"}
    try:
        metrics = {}
        for page in (1, count//20):
            statements.clear(); start=time.perf_counter()
            result = history_cards(db, filters, page=page, focus_event_id=None)
            assert result.total == count and result.pages == count//20 and len(result.items) == 20
            assert len(statements) <= 7
            assert all("zones" not in item.model_dump() for item in result.items)
            metrics[f"page_{page}"] = round(time.perf_counter()-start,4)
        focus = history_cards(db, filters, page=1, focus_event_id=min(events))
        assert focus.page == count//20
        summary = map_read(db, filters=filters, bbox=None, zoom=12, cursor=0)
        assert summary.total == summary.mapped_count == count and summary.bounds
        overview = map_read(db, filters=filters, bbox="121,14,122,15", zoom=10, cursor=0)
        assert len(overview.heatmap_features) <= 4096
        assert sum(feature.properties["zone_count"] for feature in overview.heatmap_features) == count
        assert sum(feature.properties["weight"] for feature in overview.heatmap_features) == count*2
        assert all("event_id" not in feature.properties for feature in overview.heatmap_features)
        cursor, seen = 0, []
        while True:
            chunk = map_read(db, filters=filters, bbox="121,14,122,15", zoom=15, cursor=cursor)
            assert len(chunk.features) <= 250
            seen.extend(feature.properties["zone_id"] for feature in chunk.features)
            if chunk.next_cursor is None: break
            cursor = chunk.next_cursor
        assert len(seen) == len(set(seen)) == count
        start=time.perf_counter(); queue = browse_zone_queue(db)
        metrics["group_queue"] = round(time.perf_counter()-start,4)
        assert queue.total == 1 and queue.items[0].member_count == count
        operational = map_read(db, filters=None, bbox="121,14,122,15", zoom=15, cursor=0)
        assert len(operational.features) == 250 and operational.next_cursor
        assert operational.features[0].properties["report_geometry"]["type"] == "LineString"
        metrics["bytes"] = {"cards": len(result.model_dump_json().encode()), "operational_chunk": len(operational.model_dump_json().encode()),
            "historical_chunk": len(chunk.model_dump_json().encode()), "overview": len(overview.model_dump_json().encode())}
        if os.getenv("LANES_BROWSE_BENCHMARK") == "1":
            measurements = {"cards": [], "groups": [], "map_first_chunk": []}
            for _ in range(20):
                for name, call in [("cards", lambda: history_cards(db,filters,page=count//20,focus_event_id=None)),
                    ("groups", lambda: browse_zone_queue(db)),
                    ("map_first_chunk", lambda: map_read(db,filters=filters,bbox="121,14,122,15",zoom=15,cursor=0))]:
                    start=time.perf_counter(); call(); measurements[name].append(time.perf_counter()-start)
            metrics["warm"] = {name: {"p50":round(statistics.median(samples),4), "p95":round(sorted(samples)[18],4)}
                for name,samples in measurements.items()}
            import tracemalloc
            tracemalloc.start()
            cpu_start=time.process_time(); browse_zone_queue(db)
            metrics["group_cpu_seconds_profiled"] = round(time.process_time()-cpu_start,4)
            metrics["group_peak_python_heap_bytes"] = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()
        assert not any(s.lstrip().split()[0].upper() in {"INSERT","UPDATE","DELETE"} for s in statements)
        print("SCALE_BROWSE", json.dumps({"records": count, "seconds": metrics}))
    finally:
        sql_event.remove(connection,"before_cursor_execute",record)


def test_staff_http_reads_and_inspection_collections(isolated_db):
    db, staff = isolated_db
    now = datetime.now(timezone.utc)
    item = models.FloodEvent(status=models.FloodEventStatus.ACTIVE, verified_at=now, peak_severity=models.ReportSeverity.HIGH)
    db.add(item); db.flush()
    zone = models.FloodAvoidanceZone(event_id=item.id, geometry=from_shape(box(121,14,121.001,14.001),srid=4326),is_active=True)
    db.add(zone); db.flush()
    for index in range(1000):
        db.add(models.FloodReport(zone_id=zone.id,event_id=item.id,user_id=staff.id,source=models.ReportSource.USER_REPORT,
            severity=models.ReportSeverity.EXTREME if index == 999 else models.ReportSeverity.LOW,
            status=models.ReportStatus.APPROVED,raw_text=f"Evidence {index}"))
    db.commit()
    app.dependency_overrides[get_db]=lambda:db
    app.dependency_overrides[deps.get_current_active_admin]=lambda:staff
    try:
        client=TestClient(app)
        paths=["/zones/count", "/zones/map?summary_only=true", "/zones/map?bbox=120,13,122,15",
            "/flood-events/records", "/flood-events/map?bbox=120,13,122,15&zoom=14",
            f"/flood-events/{item.id}/inspection",f"/flood-events/{item.id}/inspection/zones",
            f"/flood-events/{item.id}/inspection/timeline"]
        for path in paths:
            response=client.get("/api/v1/admin"+path)
            assert response.status_code==200, response.text
        first=client.get(f"/api/v1/admin/flood-events/{item.id}/inspection/reports").json()
        second=client.get(f"/api/v1/admin/zones/{zone.id}/contributors?page=2").json()
        assert first["total"]==second["total"]==1000 and len(first["items"])==len(second["items"])==20
        last=client.get(f"/api/v1/admin/zones/{zone.id}/contributors?page=50").json()
        assert last["pages"]==50 and len(last["items"])==20
        response=client.get(f"/api/v1/admin/zones/groups/{zone.id}/members?summary=true")
        assert response.status_code==200, response.text
        member=response.json()["zones"][0]
        assert member["contributor_count"]==1000 and len(member["contributors"])==20
        assert member["severity"]=="extreme"
        history_zone=client.get(f"/api/v1/admin/flood-events/{item.id}/inspection/zones").json()["items"][0]
        assert history_zone["severity"]=="extreme" and history_zone["contributor_count"]==1000
    finally:
        app.dependency_overrides.pop(get_db,None)
        app.dependency_overrides.pop(deps.get_current_active_admin,None)


def test_grouping_projects_only_selected_news_claim_from_large_saved_evidence(isolated_db):
    from uuid import uuid4
    from datetime import timedelta
    from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
    from app.models.news_publication import NewsClaimCase, NewsClaimSource, NewsClaimDecision, NewsClaimZoneLink
    from app.crud.news_publication import reserve_decision_id
    from app.crud.zone_queue import queue_metadata
    db, staff=isolated_db
    now=datetime.now(timezone.utc)
    article=NewsArticle(canonical_url="https://example.invalid/scale",publisher_source_id="fixture",title="Scale",content_fingerprint="1"*64)
    db.add(article);db.flush()
    version=NewsArticleVersion(article_id=article.id,input_fingerprint="2"*64,input_snapshot={})
    db.add(version);db.flush()
    run=NewsExtractionRun(article_version_id=version.id,pipeline_version="fixture",mode="rules_only",status="completed",completed_at=now,
        result={"oversized": "x"*1_500_000,"claims":[{"canonical_road":"Wrong road"},{"canonical_road":"Correct Road","canonical_city":"Pasig","canonical_barangay":"Maybunga","oversized":"y"*1_500_000}]})
    case=NewsClaimCase(revision=1)
    zone=models.FloodAvoidanceZone(geometry=from_shape(box(121,14,121.001,14.001),srid=4326),is_active=True)
    db.add_all([run,case,zone]);db.flush()
    source=NewsClaimSource(case_id=case.id,extraction_run_id=run.id,claim_ordinal=1,claim_sha256="3"*64)
    db.add(source);db.flush()
    decision=NewsClaimDecision(id=reserve_decision_id(db),case_id=case.id,revision=1,request_id=uuid4(),actor_kind="staff",actor_user_id=staff.id,
        operation="correct",public_state="active_zone",review_state="resolved",reason_code="fixture",observed_at=now,expires_at=now+timedelta(hours=1),decided_at=now,
        snapshot={"claim_source_id":source.id,"oversized":"z"*40_000,"public":{"evidence_excerpt":"Saved evidence","location_label":"Correct Road","source_title":"Fixture"}})
    db.add(decision);db.flush();db.add(NewsClaimZoneLink(decision_id=decision.id,zone_id=zone.id,relation="created"))
    repeated=models.FloodAvoidanceZone(geometry=from_shape(box(121,14,121.001,14.001),srid=4326),is_active=True)
    db.add(repeated);db.flush();db.add(NewsClaimZoneLink(decision_id=decision.id,zone_id=repeated.id,relation="created"));db.commit()
    rows=queue_metadata(db,active_only=True)
    assert len(rows)==2 and all(row["news"][0]["claim"]["canonical_road"]=="Correct Road" for row in rows)
    assert rows[0]["news"][0]["claim"]["canonical_road"]=="Correct Road"
    assert rows[0]["news"][0]["snapshot"]["public"]["evidence_excerpt"]=="Saved evidence"
    assert "oversized" not in repr(rows)
    assert len(repr(rows))<10_000
    mapped=map_read(db,filters=None,bbox="120,13,122,15",zoom=15,cursor=0)
    assert len(mapped.features)==2 and all(feature.properties["report_source"]=="news" for feature in mapped.features)


def test_sql_analytics_preserves_legacy_metrics_and_exports(isolated_db):
    from datetime import timedelta
    from app.services.spatial_browse_service import history_query, planning_metrics
    from app.services.flood_event_service import get_flood_event_planning_analytics
    db, staff = isolated_db
    now = datetime(2026, 10, 20, 23, 30, tzinfo=timezone.utc)
    for index, minutes in enumerate((30, 90, 240, 500, None)):
        item = models.FloodEvent(status=models.FloodEventStatus.ENDED if minutes is not None else models.FloodEventStatus.ACTIVE,
            verified_at=now+timedelta(days=index), ended_at=now+timedelta(days=index, minutes=minutes) if minutes is not None else None,
            peak_severity=models.ReportSeverity.HIGH if index % 2 else models.ReportSeverity.MEDIUM)
        db.add(item); db.flush()
        db.add(models.FloodEventLocation(event_id=item.id, location_type=models.FloodEventLocationType.ROAD,
            display_name="Scale Road", normalized_name="scale road"))
        db.add(models.FloodReport(event_id=item.id, user_id=staff.id, raw_text="Approved evidence", source=models.ReportSource.USER_REPORT,
            severity=models.ReportSeverity.HIGH, status=models.ReportStatus.APPROVED, created_at=now, approved_at=now))
        db.add(models.FloodReport(event_id=item.id, user_id=staff.id, raw_text="Rejected evidence", source=models.ReportSource.USER_REPORT,
            severity=models.ReportSeverity.HIGH, status=models.ReportStatus.REJECTED, created_at=now))
    db.commit()
    for filters in ({"status_filter":"all"}, {"status_filter":"ended"}, {"status_filter":"active"},
                    {"status_filter":"all", "severity":"high"}, {"status_filter":"all", "search":"No matching place"}):
        query = history_query(db,filters)
        assert planning_metrics(db,query) == get_flood_event_planning_analytics(db,query.all())
    app.dependency_overrides[get_db]=lambda:db
    app.dependency_overrides[deps.get_current_active_admin]=lambda:staff
    try:
        client=TestClient(app)
        response=client.get("/api/v1/admin/flood-events/analytics?status_filter=all")
        assert response.status_code==200, response.text
        exported=client.get("/api/v1/admin/flood-events/export?status_filter=all&export_type=analytics&export_format=json")
        assert exported.status_code==200, exported.text
        assert exported.json()==response.json()
    finally:
        app.dependency_overrides.pop(get_db,None)
        app.dependency_overrides.pop(deps.get_current_active_admin,None)
