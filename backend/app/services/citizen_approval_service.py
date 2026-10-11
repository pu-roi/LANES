"""Conservative, transactional citizen approval using documented human history."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re

from geoalchemy2.shape import to_shape
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app import models
from app.models.audit import AuditLog
from app.schemas.report import FloodAvoidanceZoneCreate
from app.schemas.configuration import OperationalSettings
from app.services.configuration_service import configuration_lock, evidence_deadline, read_configuration, unexpired_deadline
from app.services.flood_depth import severity_for_flood_depth
from app.services.flood_event_service import create_verified_event_with_zone, link_supporting_report
from app.services.flood_feature_service import capture_features

OBSERVATION_ACTION = "CITIZEN_OBSERVATION"
APPROVAL_ACTION = "CITIZEN_AUTO_APPROVAL"
APPROVAL_LOCK = 614296503


def record_observation(db: Session, report: models.FloodReport, *, observed_at: datetime | None,
                       road_validated: bool, media_hashes: list[str]) -> None:
    clock = datetime.now(timezone.utc)
    db.add(AuditLog(action_type=OBSERVATION_ACTION, target_table="flood_reports", target_id=report.id,
        created_at=clock,
        metadata_json={"user_id": report.user_id, "observed_at": observed_at.isoformat() if observed_at else None,
            "road_validated": road_validated, "geometry_sha256": geometry_hash(report),
            "media_sha256": media_hashes, "geometry_provenance": "server_road_reconstruction" if road_validated else "unvalidated_submission",
            "prediction_features": capture_features(report.geometry,report.depth,observed_at=observed_at,now=clock)}))
    db.commit()


def geometry_hash(report: models.FloodReport) -> str | None:
    return hashlib.sha256(to_shape(report.geometry).wkb).hexdigest() if report.geometry is not None else None


def observation(db: Session, report_id: int) -> dict:
    return db.scalar(select(AuditLog.metadata_json).where(AuditLog.action_type == OBSERVATION_ACTION,
        AuditLog.target_id == report_id).order_by(AuditLog.id.desc()).limit(1)) or {}


def human_history(db: Session, user_id: int) -> tuple[int, float]:
    # One latest documented human decision per report; automatic outcomes never count.
    outcomes = db.execute(select(models.FloodReportModerationOutcome.report_id,
        models.FloodReportModerationOutcome.outcome).join(models.FloodReport,
        models.FloodReport.id == models.FloodReportModerationOutcome.report_id).where(
        models.FloodReport.user_id == user_id, models.FloodReportModerationOutcome.acted_by_user_id.is_not(None))
        .order_by(models.FloodReportModerationOutcome.report_id, models.FloodReportModerationOutcome.id.desc())).all()
    latest = {}
    for report_id, outcome in outcomes:
        latest.setdefault(report_id, outcome.value)
    accepted = sum(value in ("approved", "linked") for value in latest.values())
    return len(latest), accepted / len(latest) * 100 if latest else 0


def eligible_reason(db: Session, report: models.FloodReport, evidence: dict, config: OperationalSettings, now: datetime) -> str | None:
    if report.status != models.ReportStatus.PENDING or report.deleted_at is not None:
        return "report_already_reviewed"
    if report.source != models.ReportSource.USER_REPORT or not report.user or not report.user.is_active:
        return "not_authenticated_citizen_evidence"
    if not report.user.profile or report.user.profile.trust_score < config.citizen_min_trust:
        return "trust_below_threshold"
    count, accuracy = human_history(db, report.user_id)
    if count < config.citizen_min_human_reviews or accuracy < config.citizen_min_accuracy:
        return "human_review_history_below_threshold"
    try:
        observed = datetime.fromisoformat(evidence["observed_at"])
        if observed.tzinfo is None or not timedelta(0) <= now - observed <= timedelta(minutes=30):
            return "observation_not_current"
    except (KeyError, TypeError, ValueError):
        return "explicit_observation_time_required"
    if not report.depth or severity_for_flood_depth(report.depth) != report.severity:
        return "depth_and_severity_required"
    if (not evidence.get("road_validated") or report.geometry is None
            or evidence.get("geometry_sha256") != geometry_hash(report)):
        return "road_geometry_not_validated"
    shape = to_shape(report.geometry)
    if shape.geom_type not in ("LineString", "MultiLineString") or shape.is_empty or not shape.is_valid:
        return "road_geometry_not_validated"
    west, south, east, north = shape.bounds
    if not (120.90 <= west <= east <= 121.25 and 14.30 <= south <= north <= 14.85):
        return "outside_operational_coverage"
    from app.services.news_evidence_policy import METRO_CITY_PATTERN
    if not report.city or not re.fullmatch(METRO_CITY_PATTERN, report.city.strip().lower()) or not report.human_readable_location or report.survey is None:
        return "location_and_conditions_required"
    if not report.survey.passable_vehicles or report.survey.hidden_hazards.value == "unsure":
        return "known_access_and_hazards_required"
    tokens = {value.strip().lower() for value in report.survey.passable_vehicles.split(",")}
    light = {"bicycles / e-bikes", "motorcycles", "sedans / hatchbacks"}
    motor = light | {"suvs / pickups", "large trucks / buses", "truck"}
    known = motor | {"pedestrians", "no vehicles"}
    from app.services.flood_depth import get_flood_depth_measurement
    access = get_flood_depth_measurement(report.depth).accessibility_class
    if not tokens.issubset(known) or (access == "NPLV" and tokens & light) or (access == "NPATV" and tokens & motor):
        return "depth_and_access_conflict"
    if re.search(r"\b(maybe|possibly|baka|no\s+flood(?:ing)?|not\s+flood(?:ed|ing)?|hindi\s+binaha|yesterday|kahapon|subsided|humupa|wala(?:ng)?\s+baha|forecast|tomorrow|bukas|last\s+(?:week|month|year))\b", report.raw_text, re.I):
        return "condition_requires_review"
    return None


def same_conditions(first: models.FloodReport, second: models.FloodReport) -> bool:
    return (first.depth == second.depth and first.severity == second.severity
        and first.is_bidirectional == second.is_bidirectional and first.city == second.city
        and first.barangay == second.barangay and first.survey and second.survey
        and first.survey.passable_vehicles == second.survey.passable_vehicles
        and first.survey.hidden_hazards == second.survey.hidden_hazards)


def approve_citizen_report(db: Session, report_id: int, *, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    try:
        configuration_lock(db)
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": APPROVAL_LOCK})
        config = read_configuration(db)
        report = db.scalar(select(models.FloodReport).where(models.FloodReport.id == report_id).with_for_update())
        if report is None:
            return "report_not_found"
        if not config.citizen_auto_approval_enabled:
            return "automatic_approval_disabled"
        evidence = observation(db, report.id)
        reason = eligible_reason(db, report, evidence, config, now)
        if reason:
            return reason
        # Spatial proximity only shortlists; containment/conditions decide approval.
        zones = list(db.scalars(select(models.FloodAvoidanceZone).join(models.FloodEvent).where(
            models.FloodAvoidanceZone.is_active.is_(True), models.FloodEvent.status == models.FloodEventStatus.ACTIVE,
            unexpired_deadline(db, models.FloodAvoidanceZone.expires_at, now),
            func.ST_Intersects(models.FloodAvoidanceZone.geometry, report.geometry)).with_for_update()))
        if zones:
            if len(zones) != 1:
                return "ambiguous_active_zone"
            zone = zones[0]
            if (zone.depth != report.depth or zone.severity != report.severity.value
                    or zone.source_geometry is None
                    or not db.scalar(select(func.ST_Covers(zone.geometry, report.geometry)))
                    or not db.scalar(select(func.ST_Covers(zone.source_geometry, report.geometry)))
                    or zone.passable_vehicles != report.survey.passable_vehicles
                    or zone.hidden_hazards != report.survey.hidden_hazards):
                return "active_zone_conditions_conflict"
            observed = datetime.fromisoformat(evidence["observed_at"])
            deadline = evidence_deadline(config, observed, report.depth)
            if zone.curated_by_admin_id is None and zone.expires_at is not None:
                if db.scalar(select(func.ST_Equals(zone.source_geometry, report.geometry))):
                    # Only fresh full-section support can refresh a whole automatic zone.
                    zone.expires_at = max(zone.expires_at, deadline) if zone.expires_at else deadline
                else:
                    # A partial contribution keeps only its own supported road extent alive.
                    from app.crud.report import create_flood_avoidance_zone
                    road = func.ST_Transform(func.ST_Buffer(func.ST_Transform(report.geometry, 32651), 25), 4326)
                    polygon = json.loads(db.scalar(select(func.ST_AsGeoJSON(func.ST_Intersection(road, zone.geometry)))))
                    if polygon["type"] != "Polygon":
                        return "disconnected_supported_section"
                    original = zone
                    zone = create_flood_avoidance_zone(db, FloodAvoidanceZoneCreate(geometry=polygon,
                        source_geometry=json.loads(db.scalar(select(func.ST_AsGeoJSON(report.geometry)))),
                        is_active=True, expires_at=deadline), event_id=original.event_id, commit=False)
                    zone.depth_override, zone.severity_override = report.depth, report.severity
                    zone.passable_vehicles_override = report.survey.passable_vehicles
                    zone.hidden_hazards_override = report.survey.hidden_hazards
                    zone.merge_rationale = "Automatic current citizen support for a contained verified road section."
            link_supporting_report(db, report, zone.flood_event, zone, acted_by_user_id=None, commit=False, credit_reputation=False)
            approved = [(report, evidence)]
            reason = "existing_zone_corroborated"
        else:
            candidates = list(db.scalars(select(models.FloodReport).where(
                models.FloodReport.id != report.id, models.FloodReport.user_id != report.user_id,
                models.FloodReport.status == models.ReportStatus.PENDING, models.FloodReport.deleted_at.is_(None),
                models.FloodReport.created_at >= now - timedelta(minutes=30),
                func.ST_Intersects(models.FloodReport.geometry, report.geometry))
                .order_by(models.FloodReport.id).limit(50).with_for_update()))
            match = None
            for other in candidates:
                other_evidence = observation(db, other.id)
                if eligible_reason(db, other, other_evidence, config, now) or not same_conditions(report, other):
                    return "nearby_report_requires_review"
                if (set(evidence.get("media_sha256", [])) & set(other_evidence.get("media_sha256", []))
                    or re.sub(r"[^\w]+", " ", report.raw_text.casefold()).strip() == re.sub(r"[^\w]+", " ", other.raw_text.casefold()).strip()):
                    continue
                # Only the jointly reported continuous section is eligible; never a union/hull.
                common = db.scalar(select(func.ST_AsGeoJSON(func.ST_Intersection(report.geometry, other.geometry))))
                geo = json.loads(common)
                if geo["type"] == "LineString" and len(geo["coordinates"]) >= 2:
                    if match is not None:
                        return "ambiguous_corroborating_section"
                    match = (other, other_evidence, geo)
            if match is None:
                return "waiting_for_independent_corroboration"
            other, other_evidence, geo = match
            line = func.ST_SetSRID(func.ST_GeomFromGeoJSON(json.dumps(geo)), 4326)
            polygon = json.loads(db.scalar(select(func.ST_AsGeoJSON(func.ST_Transform(
                func.ST_Buffer(func.ST_Transform(line, 32651), 25), 4326)))))
            observed = min(datetime.fromisoformat(evidence["observed_at"]), datetime.fromisoformat(other_evidence["observed_at"]))
            event, zone = create_verified_event_with_zone(db,
                FloodAvoidanceZoneCreate(geometry=polygon, source_geometry=geo, is_active=True,
                    expires_at=evidence_deadline(config, observed, report.depth)),
                peak_severity=report.severity, peak_depth=report.depth, source_report=report, commit=False,
                first_reported_at=observed, credit_reputation=False,
                zone_attributes={"depth_override": report.depth, "severity_override": report.severity,
                    "passable_vehicles_override": report.survey.passable_vehicles,
                    "hidden_hazards_override": report.survey.hidden_hazards,
                    "merge_rationale": "Automatic approval: two qualifying independent current citizen road observations."})
            link_supporting_report(db, other, event, zone, acted_by_user_id=None, commit=False, credit_reputation=False)
            approved = [(report, evidence), (other, other_evidence)]
            reason = "independent_citizen_observations_agree"
        db.flush()
        supporting_ids = list(db.scalars(select(models.FloodReport.id).where(
            models.FloodReport.zone_id == zone.id, models.FloodReport.status == models.ReportStatus.APPROVED,
            models.FloodReport.deleted_at.is_(None)).order_by(models.FloodReport.id)))
        for item, captured in approved:
            db.add(models.FloodReportModerationOutcome(report_id=item.id,
                outcome=models.ReportModerationOutcomeType.APPROVED, event_id=zone.event_id, zone_id=zone.id,
                acted_by_user_id=None, internal_note="Automatic approval without reputation credit: " + reason))
            observed = datetime.fromisoformat(captured["observed_at"])
            deadline = evidence_deadline(config, observed, item.depth)
            db.add(AuditLog(action_type=APPROVAL_ACTION, target_table="flood_reports", target_id=item.id,
                metadata_json={"actor_kind": "automatic", "reason_code": reason, "zone_id": zone.id,
                    "event_id": zone.event_id, "observed_at": observed.isoformat(), "expires_at": deadline.isoformat(),
                    "policy": config.model_dump(mode="json"), "supporting_report_ids": supporting_ids,
                    "geometry_sha256": geometry_hash(item), "geometry_provenance": captured.get("geometry_provenance", "server_road_reconstruction")}))
            db.add(models.FloodEventTimelineEntry(event_id=zone.event_id, entry_type="citizen_auto_approved",
                summary="Current citizen observation automatically approved without reputation credit.",
                snapshot_json={"report_id": item.id, "zone_id": zone.id, "observed_at": observed.isoformat(),
                    "expires_at": deadline.isoformat(), "reason_code": reason}))
        db.flush()
        from app.services.pasig_ml_expiry_service import apply_zone_policy
        apply_zone_policy(db, zone.id, now=now)
        db.commit()
        return reason
    except Exception:
        db.rollback()
        raise
    finally:
        # Non-approval paths release locks too; approved writes have already committed.
        db.rollback()


def has_active_citizen_support(db: Session, zone_id: int, now: datetime) -> bool:
    """Apply the expiry policy to existing approved contributions, not new admissions."""
    expiry_enabled = read_configuration(db).automatic_expiry_enabled
    reports = list(db.scalars(select(models.FloodReport.id).where(models.FloodReport.zone_id == zone_id,
        models.FloodReport.status == models.ReportStatus.APPROVED, models.FloodReport.deleted_at.is_(None))))
    for report_id in reports:
        automated = db.scalar(select(AuditLog.metadata_json).where(AuditLog.action_type == APPROVAL_ACTION,
            AuditLog.target_id == report_id).order_by(AuditLog.id.desc()).limit(1))
        if automated is None:
            return True  # Explicit human approval keeps its staff-managed deadline.
        if not expiry_enabled or datetime.fromisoformat(automated["expires_at"]) > now:
            return True
    return False


def attach_automatic_evidence(db: Session, reports: list) -> list:
    if not reports:
        return reports
    rows = db.scalars(select(AuditLog).where(AuditLog.target_table == "flood_reports",
        AuditLog.target_id.in_([report.id for report in reports]),
        AuditLog.action_type.in_((OBSERVATION_ACTION, APPROVAL_ACTION))).order_by(AuditLog.id))
    captured = {}
    for row in rows:
        captured.setdefault(row.target_id, {})[row.action_type] = row.metadata_json
    for report in reports:
        evidence = captured.get(report.id, {})
        observed = evidence.get(OBSERVATION_ACTION, {}).get("observed_at")
        report.observed_at = datetime.fromisoformat(observed) if observed else None
        approval = evidence.get(APPROVAL_ACTION)
        report.approval_kind = "automatic" if approval else "human" if report.status == models.ReportStatus.APPROVED else "pending_review"
        report.automatic_review_reason = approval.get("reason_code") if approval else None
    return reports
