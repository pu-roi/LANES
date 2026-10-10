"""Audited experimental ML expiry policy; model qualification remains unchanged.

The upper prediction quantile schedules an Unconfirmed expiry, never a dry label.
The original fixed deadline is retained in audit storage for reversible fallback.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import math

from geoalchemy2.shape import to_shape
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.audit import AuditLog
from app.models.report import FloodAvoidanceZone, FloodReport
from app.schemas.cross_location_prediction import CrossLocationPrediction
from app.services.configuration_service import configuration_lock, read_configuration
from app.services.flood_duration_model import DurationModelError
from app.services import zone_prediction_service as predictions
from app.services.cross_location_prediction_service import compare_resolved_zone
from app.services.local_news_scenario_service import scoped_clock
from app.services.spatial_review_grouping import utc

ACTION = "APPLY_ZONE_EXPIRY_POLICY"
POLICY_VERSION = "pasig-experimental-ml-expiry-v2"
QUANTILE = 0.9
MAX_POLICY_HOURS = 48


def latest_policy(db: Session, zone_id: int) -> AuditLog | None:
    return db.scalar(select(AuditLog).where(AuditLog.action_type == ACTION,
        AuditLog.target_table == "flood_avoidance_zones", AuditLog.target_id == zone_id)
        .order_by(AuditLog.id.desc()).limit(1))


def _source_signature(db: Session, zone: FloodAvoidanceZone) -> str:
    reports = predictions.store.linked_reports(db, zone.id)
    report_ids = [r.id for r in reports]
    source_ids = select(AuditLog.id).where(AuditLog.target_table == "flood_reports",
        AuditLog.target_id.in_(report_ids))
    revision = db.scalar(select(func.max(AuditLog.id)).where(AuditLog.action_type != ACTION,
        or_((AuditLog.target_table == "flood_avoidance_zones") & (AuditLog.target_id == zone.id),
            (AuditLog.target_table == "flood_reports") & AuditLog.target_id.in_(report_ids),
            (AuditLog.target_table == "audit_logs") & AuditLog.target_id.in_(source_ids))))
    news = predictions.store.current_news(db, zone.id)
    from app.services.cross_location_prediction_service import BUNDLE_DIRECTORY
    model_inputs = {}
    for name in ("conditional_aft.json", "cross_location_manifest.json", "cross_location_aft.json", "cross_location_evaluation.json"):
        try:
            with (BUNDLE_DIRECTORY/name).open("rb") as handle:
                model_inputs[name] = hashlib.sha256(handle.read(131073)).hexdigest()
        except OSError:
            model_inputs[name] = "unavailable"
    payload = {"geometry": to_shape(zone.geometry).wkb_hex, "event": zone.event_id,
        "models": model_inputs,
        "depth": zone.depth, "depth_override": zone.depth_override, "revision": revision,
        "reports": [(r.id, str(r.status), str(r.updated_at), r.event_id) for r in reports],
        "news": [(d.id, d.revision, d.public_state, d.review_state) for d in news]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def choose_deadline(result: predictions.ZonePrediction, comparison: CrossLocationPrediction | None,
                    fallback: datetime | None) -> dict:
    """Pure fixed-issuance policy, independent of the wall clock at refresh."""
    decision = {"method": "fixed_fallback", "deadline": fallback,
        "reason": "; ".join(result.reasons) or "No eligible model estimate.",
        "reference_basis": None, "model_sha256": None}
    if result.city != "Pasig":
        decision.update(method="fixed", reason="Outside verified Pasig coverage.")
        return decision
    if result.state in {"needs_review", "inactive"}:
        return decision
    simulation = result.submission_simulation or result.registration_simulation
    quantiles = result.quantiles if result.state == "estimated" else (simulation.quantiles if simulation else [])
    model = result.model if result.state == "estimated" else (simulation.model if simulation else None)
    issuance = result.prediction_as_of_at if result.state == "estimated" else (simulation.prediction_as_of_at if simulation else None)
    basis = "observed_reference" if result.state == "estimated" else (
        "submission_proxy" if result.submission_simulation else "registration_proxy")
    method = "ml_pooled"
    if comparison is not None and comparison.status == "research_comparison":
        quantiles, issuance, basis = comparison.quantiles, comparison.prediction_as_of_at, comparison.reference_basis
        checksum, method = comparison.model_sha256, "ml_cross_location"
    else:
        checksum = model.model_sha256 if model else None
    upper = next((q for q in quantiles if math.isclose(q.quantile, QUANTILE)), None)
    if upper is None or issuance is None or not checksum:
        return decision
    deadline = utc(upper.estimated_reported_subsidence_at)
    # Bound the policy independently of the training support; this is not a
    # fitted scientific maximum duration. Never roll deadlines from now().
    if not utc(issuance) < deadline <= utc(issuance) + timedelta(hours=MAX_POLICY_HOURS):
        decision["reason"] = "The model deadline exceeds the 48-hour operational policy bound."
        return decision
    decision.update(method=method, deadline=deadline, reason="Experimental upper-quantile expiry; current condition becomes Unconfirmed.",
        reference_basis=basis, model_sha256=checksum,
        prediction_as_of_at=utc(issuance).isoformat(),
        quantiles=[q.model_dump(mode="json") for q in quantiles])
    return decision


def apply_zone_policy(db: Session, zone_id: int, *, now: datetime | None = None) -> dict | None:
    """Caller owns commit. Lock ordering matches the expiry worker/configuration."""
    configuration_lock(db)
    config = read_configuration(db)
    zone = db.scalar(select(FloodAvoidanceZone).where(FloodAvoidanceZone.id == zone_id)
        .with_for_update().execution_options(populate_existing=True))
    if zone is None or not zone.is_active:
        return None
    clock = scoped_clock(zone.id, "zone", now or datetime.now(timezone.utc))
    if not config.automatic_expiry_enabled:
        return None
    signature = _source_signature(db, zone)
    prior = latest_policy(db, zone_id)
    saved = prior.metadata_json if prior else {}
    if (saved.get("policy_version") == POLICY_VERSION and saved.get("source_signature") == signature
            and saved.get("ml_enabled") == config.pasig_ml_expiry_enabled
            and saved.get("deadline") == (utc(zone.expires_at).isoformat() if zone.expires_at else None)):
        return saved
    current = utc(zone.expires_at) if zone.expires_at else None
    fallback = current
    if saved.get("method", "").startswith("ml_") and saved.get("deadline") == (current.isoformat() if current else None):
        fallback = datetime.fromisoformat(saved["fixed_deadline"]) if saved.get("fixed_deadline") else None
    if not config.pasig_ml_expiry_enabled:
        decision = {"method": "fixed", "deadline": fallback, "reason": "Pasig ML expiry is disabled.",
            "reference_basis": None, "model_sha256": None}
    else:
        try:
            resolved = predictions.resolve_zone_prediction(db, zone.id, now=clock,
                ignore_deadline=True, recover_issuance=True)
            comparison = compare_resolved_zone(db, resolved, now=clock) if resolved.city == "Pasig" else None
            decision = choose_deadline(resolved, comparison, fallback)
        except (OSError, ValueError, TypeError, KeyError, OverflowError, DurationModelError) as exc:
            # A qualified evidence/model failure is an explicit audited fallback;
            # database/transaction failures propagate and fail the worker/API.
            decision = {"method": "fixed_fallback", "deadline": fallback,
                "reason": f"Model or source validation unavailable ({type(exc).__name__}); fixed deadline retained.",
                "reference_basis": None, "model_sha256": None}
    manual = db.scalar(select(AuditLog).where(AuditLog.action_type == "UPDATE_ZONE",
        AuditLog.target_table == "flood_avoidance_zones", AuditLog.target_id == zone.id)
        .order_by(AuditLog.id.desc()).limit(1))
    if manual is not None and (manual.metadata_json or {}).get("expires_at") is not None:
        decision = {"method": "fixed", "deadline": current,
            "reason": "Explicit staff deadline retained.", "reference_basis": None, "model_sha256": None}
    deadline = decision.pop("deadline")
    metadata = {"policy_version": POLICY_VERSION, "source_signature": signature,
        "ml_enabled": config.pasig_ml_expiry_enabled, **decision,
        "deadline": deadline.isoformat() if deadline else None,
        "fixed_deadline": fallback.isoformat() if fallback else None,
        "quantile": QUANTILE if decision["method"].startswith("ml_") else None,
        "experimental": decision["method"].startswith("ml_"), "accuracy_verified": False,
        "expires_as": "Unconfirmed", "applied_at": clock.isoformat()}
    zone.expires_at = deadline
    # Deadline policy writes have their own audit clock. Preserve the source
    # edit clock so applying/pausing policy cannot invalidate a source proxy.
    flag_modified(zone, "updated_at")
    db.add(AuditLog(action_type=ACTION, target_table="flood_avoidance_zones", target_id=zone.id,
        created_at=clock, metadata_json=metadata))
    db.flush()
    return metadata


def synchronize_active_zones(db: Session, *, now: datetime | None = None) -> int:
    """Schedule before deadline checks, including existing active zones."""
    if not read_configuration(db).automatic_expiry_enabled:
        return 0
    ids = list(db.scalars(select(FloodAvoidanceZone.id).where(FloodAvoidanceZone.is_active.is_(True))
        .order_by(FloodAvoidanceZone.id)))
    for zone_id in ids:
        apply_zone_policy(db, zone_id, now=now)
    return len(ids)


def expiry_status(db: Session, zone_id: int) -> dict:
    zone = db.get(FloodAvoidanceZone, zone_id)
    if zone is None:
        from app.services.flood_followup_service import FollowupError
        raise FollowupError(404, "Flood Zone not found.")
    config, prior = read_configuration(db), latest_policy(db, zone_id)
    saved = prior.metadata_json if prior else {}
    matches = (saved.get("policy_version") == POLICY_VERSION and saved.get("ml_enabled") == config.pasig_ml_expiry_enabled
        and saved.get("deadline") == (utc(zone.expires_at).isoformat() if zone.expires_at else None))
    return {"automatic_expiry_enabled": config.automatic_expiry_enabled,
        "pasig_ml_expiry_enabled": config.pasig_ml_expiry_enabled,
        "method": saved.get("method", "fixed") if matches else "pending_sync",
        "deadline": zone.expires_at, "reason": saved.get("reason") if matches else "Waiting for the expiry worker to synchronize this zone.",
        "reference_basis": saved.get("reference_basis") if matches else None,
        "experimental": bool(saved.get("experimental")) if matches else False,
        "zone_is_active": zone.is_active,
        "prediction_as_of_at": saved.get("prediction_as_of_at") if matches else None,
        "quantiles": saved.get("quantiles", []) if matches else [],
        "model_sha256": saved.get("model_sha256") if matches else None,
        "accuracy_verified": False, "expires_as": "Unconfirmed"}
