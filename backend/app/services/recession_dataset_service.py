"""Offline qualification of reviewed, same-section recession evidence.

This pairs existing exports only after an explicit episode review. It does not
verify a human statement, admit production labels, fit a model or write to DB.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

from app.schemas.flood_followup import FloodFollowupResponse, FloodFollowupsExportResponse

TARGET = "first_reviewed_recorded_wet_to_reported_same_section_subsidence_v1"


class EpisodeReview(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    episode_id: str = Field(min_length=1, max_length=100)
    reference_id: int = Field(gt=0)
    endpoint_id: int = Field(gt=0)
    reviewer_id: int = Field(gt=0)
    reviewed_at: datetime
    sample_kind: Literal["field_verified", "test", "unclassified"] = "unclassified"
    same_section_verified: StrictBool = False
    continuity_verified: StrictBool = False
    storm_group: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("reviewed_at", mode="before")
    @classmethod
    def aware_clock(cls, value: Any) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Episode review requires an explicit timezone.")
        return value.astimezone(timezone.utc)


def complete_followup_export(envelope: dict[str, Any], now: datetime) -> list[FloodFollowupResponse]:
    """Validate declared all-state export pagination, including pending claims.

    Selection provenance is a caller declaration, not cryptographic proof that
    the files originated from LANES. Input hashes make subsequent changes clear.
    """
    if (not isinstance(envelope, dict) or envelope.get("schema_version") != 1 or envelope.get("selection") != {
            "review_state": "all", "first_before_id": None}):
        raise ValueError("An all-review-state export starting at the first page is required.")
    pages = envelope.get("pages")
    if not isinstance(pages, list) or not 1 <= len(pages) <= 1000:
        raise ValueError("Supply all export pages in order.")
    rows: list[FloodFollowupResponse] = []
    previous_cursor = None
    for index, raw in enumerate(pages):
        page = FloodFollowupsExportResponse.model_validate(raw)
        if page.generated_at.tzinfo is None or page.generated_at > now:
            raise ValueError("Export availability must be timezone-aware and not future-dated.")
        ids = [row.id for row in page.follow_ups]
        if any(value <= 0 for value in ids) or ids != sorted(set(ids), reverse=True) or (previous_cursor is not None
                and any(value >= previous_cursor for value in ids)):
            raise ValueError("Export pages must have unique descending IDs and consistent cursors.")
        if index < len(pages) - 1:
            if not ids or page.next_before_id != ids[-1]:
                raise ValueError("Export pagination is incomplete or inconsistent.")
        elif page.next_before_id is not None:
            raise ValueError("The final export page is incomplete.")
        for row in page.follow_ups:
            if (row.observed_at.tzinfo is None or row.submitted_at.tzinfo is None
                    or row.observed_at > row.submitted_at or row.submitted_at > page.generated_at):
                raise ValueError("A source was not available at export time.")
            if row.review and (row.review.reviewed_at.tzinfo is None
                    or row.review.reviewed_at > page.generated_at):
                raise ValueError("A review was not available at export time.")
        rows.extend(page.follow_ups)
        previous_cursor = page.next_before_id
    if len({row.id for row in rows}) != len(rows):
        raise ValueError("Duplicate observation identities in the export.")
    return rows


def _source_blockers(row: FloodFollowupResponse) -> list[str]:
    problems = []
    review = row.review
    if (row.review_state != "accepted" or review is None or review.decision != "accepted"
            or not review.same_location_verified or review.reviewer_id == row.user_id):
        problems.append("independent_accepted_source_review_missing")
    if not row.same_location_confirmed:
        problems.append("source_section_not_confirmed")
    if (row.condition == "subsided" and row.depth_cm not in (None, 0)
            or row.condition == "still_flooded" and row.depth_cm == 0):
        problems.append("condition_depth_conflict")
    clocks = [row.observed_at, row.submitted_at] + ([review.reviewed_at] if review else [])
    if any(t.tzinfo is None for t in clocks) or clocks != sorted(clocks):
        problems.append("invalid_source_chronology")
    snapshot = row.location_snapshot
    if (snapshot.report_id != row.report_id or snapshot.city != "Pasig"
            or not snapshot.event_id or not snapshot.zone_id
            or not re.fullmatch(r"[0-9a-f]{64}", snapshot.geometry_sha256)):
        problems.append("same_section_pasig_episode_identity_missing")
    return problems


def qualify_recession_episodes(envelope: dict[str, Any], reviews: list[EpisodeReview],
                               *, now: datetime | None = None) -> dict[str, Any]:
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        raise ValueError("Qualification time requires a timezone.")
    rows = complete_followup_export(envelope, clock)
    by_id = {row.id: row for row in rows}
    episode_counts = Counter(rule.episode_id for rule in reviews)
    reference_counts = Counter(rule.reference_id for rule in reviews)
    endpoint_counts = Counter(rule.endpoint_id for rule in reviews)
    candidates, decisions = [], []
    for rule in reviews:
        blockers = []
        if rule.sample_kind != "field_verified":
            blockers.append("test_or_unverified_field_observations")
        if not rule.same_section_verified or not rule.continuity_verified:
            blockers.append("section_or_episode_continuity_not_reviewed")
        if rule.reviewed_at > clock:
            blockers.append("episode_review_is_future_dated")
        if (episode_counts[rule.episode_id] != 1 or reference_counts[rule.reference_id] != 1
                or endpoint_counts[rule.endpoint_id] != 1):
            blockers.append("duplicate_episode_or_shared_endpoint_requires_group_review")
        first, end = by_id.get(rule.reference_id), by_id.get(rule.endpoint_id)
        if first is None or end is None:
            blockers.append("selected_observation_not_in_complete_export")
        else:
            if first.condition != "still_flooded" or end.observed_at <= first.observed_at:
                blockers.append("invalid_wet_reference_or_endpoint_order")
            if first.location_snapshot != end.location_snapshot or first.report_id != end.report_id:
                blockers.append("section_or_episode_snapshot_changed")
            window = [row for row in rows if row.report_id == first.report_id
                and first.observed_at <= row.observed_at <= end.observed_at]
            if end.condition == "still_flooded" and any(row.report_id == first.report_id
                    and row.observed_at > end.observed_at and row.review_state != "rejected" for row in rows):
                blockers.append("later_claim_requires_censoring_or_episode_review")
            for row in window:
                blockers.extend(_source_blockers(row))
                if row.location_snapshot != first.location_snapshot:
                    blockers.append("section_or_episode_snapshot_changed")
                if row.user_id == rule.reviewer_id:
                    blockers.append("episode_reviewer_is_source_author")
                if row.review and row.review.reviewed_at > rule.reviewed_at:
                    blockers.append("episode_review_precedes_source_review")
                if row.condition == "subsided" and row.id != end.id:
                    blockers.append("intervening_clearance_or_recurrence")
            features = first.prediction_features or {}
            try:
                captured = datetime.fromisoformat(features.get("recorded_at", "").replace("Z", "+00:00"))
                observed = datetime.fromisoformat(features.get("observed_at", "").replace("Z", "+00:00"))
                valid_clock = captured.tzinfo is not None and captured <= first.submitted_at and observed == first.observed_at
            except (ValueError, TypeError, AttributeError):
                valid_clock = False
            depth = first.depth_cm
            coordinates = features.get("coordinates")
            valid_coordinates = (isinstance(coordinates, list) and len(coordinates) == 2
                and all(type(v) in (int, float) and math.isfinite(v) for v in coordinates)
                and -180 <= coordinates[0] <= 180 and -90 <= coordinates[1] <= 90)
            if (type(depth) not in (float, int) or not math.isfinite(depth) or not 0 < depth <= 1000
                    or type(features.get("depth_cm")) not in (float, int) or not valid_coordinates
                    or features.get("depth_cm") != depth or features.get("depth_basis") != "reported_numeric_centimeters"
                    or features.get("geometry_sha256") != first.location_snapshot.geometry_sha256
                    or features.get("errors") != [] or not features.get("boundary_revision")
                    or len(features.get("barangays") or []) != 1 or not valid_clock):
                blockers.append("frozen_numeric_depth_and_pasig_features_unqualified")
            # Retrospective source review qualifies evidence, but cannot create
            # an actual historical forecast. A hindcast uses only features
            # recorded at submission, with explicit simulation provenance.
            issuance = first.submitted_at
            if issuance >= end.observed_at:
                blockers.append("endpoint_already_observed_at_simulated_issuance")
            if not blockers:
                wet = [row for row in window if row.condition == "still_flooded"]
                last = max(wet, key=lambda row: (row.observed_at, row.id))
                lower = (last.observed_at - first.observed_at).total_seconds() / 60
                upper = (end.observed_at - first.observed_at).total_seconds() / 60 if end.condition == "subsided" else None
                if upper is not None and upper <= lower:
                    blockers.append("simultaneous_or_reversed_wet_clearance_claims")
                elif upper is None and lower <= 0:
                    blockers.append("right_censoring_requires_later_verified_wet")
                else:
                    candidates.append({"episode_id": rule.episode_id, "report_id": first.report_id,
                        "event_id": first.location_snapshot.event_id, "geometry_sha256": first.location_snapshot.geometry_sha256,
                        "location": features["barangays"][0], "depth_cm": depth, "depth_basis": features["depth_basis"],
                        "boundary_revision": features["boundary_revision"], "feature_recorded_at": features["recorded_at"],
                        "source_features_sha256": hashlib.sha256(json.dumps(features, sort_keys=True, allow_nan=False).encode()).hexdigest(),
                        "reference_id": first.id, "last_wet_id": last.id, "endpoint_id": end.id,
                        "source_review_ids": sorted(row.review.id for row in window),
                        "episode_reviewer_id": rule.reviewer_id, "episode_reviewed_at": rule.reviewed_at.isoformat(),
                        "reference_observed_at": first.observed_at.isoformat(),
                        "simulated_prediction_issuance_at": issuance.isoformat(), "actual_issued_forecast": False,
                        "reference_reviewed_at": first.review.reviewed_at.isoformat(),
                        "endpoint_observed_at": end.observed_at.isoformat(),
                        "outcome_available_at": max(rule.reviewed_at, *(row.review.reviewed_at for row in window)).isoformat(),
                        "lower_minutes": lower, "lower_inclusive": False, "upper_minutes": upper,
                        "upper_inclusive": upper is not None, "censoring": "interval" if upper is not None else "right",
                        "outcome_group": f"followup:{end.id}", "storm_group": rule.storm_group,
                        "target_version": TARGET, "true_onset_known": False, "conditional_research_eligible": True,
                        "production_training_admitted": False})
        decisions.append({"episode_id": rule.episode_id, "reference_id": rule.reference_id,
            "endpoint_id": rule.endpoint_id, "conditional_research_eligible": not blockers,
            "blockers": sorted(set(blockers)), "production_training_admitted": False})
    return {"schema_version": 1, "target_version": TARGET, "source_observations": len(rows),
        "source_reports": len({row.report_id for row in rows}), "episode_reviews": len(reviews),
        "source_review_states": dict(Counter(row.review_state for row in rows)),
        "numeric_depth_sources": sum(row.depth_cm is not None for row in rows),
        "source_blocker_counts": dict(Counter(reason for row in rows for reason in _source_blockers(row))),
        "candidates": candidates, "qualification": decisions,
        "reports_without_episode_review": sorted({row.report_id for row in rows}
            - {by_id[r.reference_id].report_id for r in reviews if r.reference_id in by_id}),
        "production_training_admitted": False, "changes_status_expiry_or_routing": False,
        "limits": ["human field/scope/continuity declarations are not automatically verified",
            "unknown true onset; target begins at first selected recorded wet observation",
            "source and episode reviews do not establish prospective calibration",
            "one locality and frozen numeric depth required; environmental predictors not admitted"]}
