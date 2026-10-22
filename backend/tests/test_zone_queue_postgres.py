"""Real PostGIS queue eligibility, geometry, batch detail and read-only acceptance."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from geoalchemy2.shape import from_shape
import pytest
from shapely.geometry import LineString, box
from sqlalchemy import event, func, select

from app import models
from app.models.audit import AuditLog
from app.services.zone_queue_service import browse_zone_queue, browse_zone_members
from test_operational_settings_postgres import isolated_db, citizen, report


def test_native_queue_reads_preserve_geometry_lifecycle_and_evidence(isolated_db):
    db, staff = isolated_db
    now = datetime.now(timezone.utc)
    zones = []
    for index in range(4):
        zones.append(models.FloodAvoidanceZone(geometry=from_shape(box(121.08 + index * .0002, 14.57,
            121.0801 + index * .0002, 14.5701), srid=4326), name=f"Native zone {index}",
            is_active=index != 2, expires_at=now + timedelta(hours=2) if index != 3 else now - timedelta(hours=1),
            created_at=now - timedelta(hours=index * 4), curated_by_admin_id=staff.id if index else None,
            severity_override=models.ReportSeverity.HIGH, depth_override="waist"))
    db.add_all(zones); db.commit()
    witness = citizen(db, staff.role_id)
    item = report(db, witness)
    item.zone_id = zones[0].id
    item.status = models.ReportStatus.APPROVED
    item.media_urls = ["https://example.org/original.png"]
    official_evidence = report(db, witness)
    official_evidence.zone_id = zones[1].id
    official_evidence.source = models.ReportSource.MANUAL_SEEDER
    official_evidence.status = models.ReportStatus.APPROVED
    db.commit()
    ids = [zone.id for zone in zones]
    for zone in zones:
        db.refresh(zone)
    original = [(zone.id, zone.updated_at, zone.expires_at, zone.is_active, bytes(zone.geometry.data)) for zone in zones]
    statements = []
    def record(_connection, _cursor, statement, _parameters, _context, _many):
        statements.append(statement)
    connection = db.connection()
    event.listen(connection, "before_cursor_execute", record)
    try:
        queue = browse_zone_queue(db)
        assert queue.total == 1 and queue.item_total == 2
        assert queue.items[0].zone_id == ids[0] and queue.items[0].member_count == 2
        assert queue.items[0].bounds == pytest.approx((121.08,14.57,121.0803,14.5701))
        assert set(queue.items[0].sources) == {"user_reports", "official"}
        members = browse_zone_members(db, ids[1])
        assert [zone.id for zone in members.zones] == ids[:2]
        assert members.zones[0].report_media_urls == item.media_urls
        assert members.zones[0].contributors[0].report_id == item.id
        assert members.zones[1].contributors[0].report_id == official_evidence.id
        history = browse_zone_queue(db, active_only=False)
        assert history.total == history.item_total == 4 and len(history.zones) == 4
        assert {zone.id for zone in history.zones if zone.is_active} == set(ids[:2])
        assert browse_zone_members(db, ids[2]) is None
        assert browse_zone_members(db, ids[3]) is None
        db.expire_all()
        refreshed = [db.get(models.FloodAvoidanceZone, id) for id in ids]
        assert [(zone.id, zone.updated_at, zone.expires_at, zone.is_active, bytes(zone.geometry.data)) for zone in refreshed] == original
        assert not any(statement.lstrip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE"} for statement in statements)
    finally:
        event.remove(connection, "before_cursor_execute", record)


@pytest.mark.parametrize("same_road", [False, True])
def test_original_road_gap_is_not_reduced_by_saved_polygon_buffers(isolated_db, same_road):
    db, staff = isolated_db
    witness = citizen(db, staff.role_id)
    zones = []
    for index, northing in enumerate((1600000, 1600077.5)):
        original = from_shape(LineString([(500000, northing), (500200, northing)]), srid=32651)
        zone = models.FloodAvoidanceZone(
            geometry=func.ST_Transform(func.ST_Buffer(original, 25), 4326),
            source_geometry=func.ST_Transform(original, 4326), is_active=True,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=2))
        db.add(zone); db.flush()
        evidence = report(db, witness)
        evidence.zone_id = zone.id
        evidence.human_readable_location = "M. H. del Pilar Street" if same_road or index == 0 else "Doctor Pilapil Street"
        evidence.geometry = func.ST_Transform(original, 4326)
        evidence.status = models.ReportStatus.APPROVED
        zones.append(zone)
    db.commit()
    polygon_gap = db.scalar(select(func.ST_Distance(func.ST_Transform(zones[0].geometry, 32651),
                                                  func.ST_Transform(zones[1].geometry, 32651))))
    assert polygon_gap == pytest.approx(27.5, abs=.01)
    queue = browse_zone_queue(db)
    assert queue.total == queue.item_total == 2
    assert all(item.member_count == 1 for item in queue.items)
    assert browse_zone_members(db, zones[0].id).total == 1


def test_saved_source_geometry_takes_precedence_over_linked_report_geometry(isolated_db):
    db, staff = isolated_db
    witness = citizen(db, staff.role_id)
    for northing in (1600000, 1600100):
        original = from_shape(LineString([(500000, northing), (500010, northing)]), srid=32651)
        zone = models.FloodAvoidanceZone(geometry=func.ST_Transform(func.ST_Buffer(original, 25), 4326),
            source_geometry=func.ST_Transform(original, 4326), is_active=True,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=2))
        db.add(zone); db.flush()
        evidence = report(db, witness)  # Identical report lines cannot override saved zone cores.
        evidence.zone_id = zone.id
        evidence.status = models.ReportStatus.APPROVED
    db.commit()
    queue = browse_zone_queue(db)
    assert queue.total == queue.item_total == 2


def test_batch_metadata_query_count_does_not_grow_per_card(isolated_db):
    db, staff = isolated_db
    now = datetime.now(timezone.utc)
    for index in range(25):
        db.add(models.FloodAvoidanceZone(geometry=from_shape(box(121 + index * .01,14.57,121.0001 + index * .01,14.5701),srid=4326),
            curated_by_admin_id=staff.id, is_active=True, created_at=now, severity_override=models.ReportSeverity.MEDIUM))
    db.commit()
    statements = []
    def record(_connection, _cursor, statement, _parameters, _context, _many): statements.append(statement)
    connection = db.connection()
    event.listen(connection, "before_cursor_execute", record)
    try:
        first = browse_zone_queue(db)
        assert len(first.items) == 20 and first.total == 25 and first.pages == 2
        first_queries = len(statements)
        statements.clear()
        all_items = browse_zone_queue(db, page_size=100)
        assert len(all_items.items) == 25
        assert len(statements) == first_queries
    finally:
        event.remove(connection, "before_cursor_execute", record)


def test_news_zone_retains_publisher_evidence_and_estimate_provenance(isolated_db):
    from app.crud.news_publication import reserve_decision_id
    from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimZoneLink
    from app.schemas.news_publication import NewsDecisionSnapshot, PublicNewsAlert
    db, staff = isolated_db
    now = datetime.now(timezone.utc)
    zone = models.FloodAvoidanceZone(geometry=from_shape(box(121.08,14.57,121.0801,14.5701),srid=4326),
        is_active=True, expires_at=now+timedelta(hours=1), created_at=now, severity_override=models.ReportSeverity.MEDIUM)
    case = NewsClaimCase(revision=1)
    db.add_all([zone, case]); db.flush()
    decision = NewsClaimDecision(id=reserve_decision_id(db), case_id=case.id, revision=1, request_id=uuid4(),
        actor_kind="staff", actor_user_id=staff.id, operation="correct", public_state="active_zone", review_state="resolved",
        reason_code="estimated_road_corridor", snapshot={}, observed_at=now-timedelta(minutes=10),
        expires_at=zone.expires_at, decided_at=now)
    public = PublicNewsAlert(case_id=case.id, decision_id=decision.id, revision=1, status="Active",
        location_label="Fixture road", condition_label="Reported flooding", passability_label="Unknown",
        observed_at=decision.observed_at, expires_at=zone.expires_at, updated_at=now,
        source_title="Source article", source_publisher="Fixture Publisher", source_url="https://example.com/flood",
        evidence_excerpt="Original recorded source evidence", geometry_precision="operational_polygon",
        affects_routing=True, geometry_basis="estimated_road_corridor")
    decision.snapshot = NewsDecisionSnapshot(request_sha256="1"*64, policy_fingerprint="2"*64,
        claim_source_id=1, input_sha256="3"*64, claim_sha256="4"*64, incident_identity="5"*64,
        article_id=1, public=public, linked_zone_ids=[zone.id], geometry_reason="estimated_road_corridor").model_dump(mode="json")
    db.add(decision); db.flush()
    db.add(NewsClaimZoneLink(decision_id=decision.id, zone_id=zone.id, relation="created")); db.commit()
    queue = browse_zone_queue(db, source="news")
    assert queue.item_total == 1 and queue.items[0].sources == ["news"]
    result = browse_zone_members(db, zone.id).zones[0]
    assert result.report_source == "news" and result.contributors == []
    assert result.report_text == public.evidence_excerpt and result.reporter_name == public.source_publisher
    assert result.news[0].geometry_basis == "estimated_road_corridor"


def test_paused_expiry_policy_is_shared_with_existing_zone_reader(isolated_db):
    from app.schemas.configuration import OperationalSettings, ConfigurationUpdate
    from app.services.configuration_service import save_configuration
    db, staff = isolated_db
    now = datetime.now(timezone.utc)
    zone = models.FloodAvoidanceZone(geometry=from_shape(box(121.08,14.57,121.0801,14.5701),srid=4326),
        is_active=True, expires_at=now-timedelta(hours=2), created_at=now)
    db.add(zone); db.commit()
    assert browse_zone_queue(db).item_total == 0
    save_configuration(db, ConfigurationUpdate(revision=0, settings=OperationalSettings(automatic_expiry_enabled=False)), actor_id=staff.id)
    assert browse_zone_queue(db).item_total == 1
    assert browse_zone_members(db, zone.id).zones[0].is_active
