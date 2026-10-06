"""Build a versioned Pasig evidence/proxy register; no fitting or database writes.

Preserves the original review layer and raw fields. Proxy admission is descriptive,
conditional on collective reporting scope; it is separate from training admission.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from qualify_pasig_duration_data import (
    INPUT, ROOT, digest, key_id, place_key, read_csv, source_inventory,
    verify_source, write_csv,
)

VERSION = "pasig-followup-register-v1"
TARGET = "remaining_time_from_supported_wet_reference_to_scope_matched_reported_subsidence_v1"
REVIEW = ROOT / "docs/evaluations/pasig-duration-qualification-20261005"
DEFAULT_OUTPUT = ROOT / "docs/evaluations/pasig-duration-followup-20261005"
SCOPES = {
    "OBS-c33d857e974b018d": (260, "true", "explicit_barangay_collective"),
    "OBS-7d1d5441f76ee802": (120, "false", "explicit_barangay_collective"),
    "OBS-aed0c046a22c54b0": (360, "true", "explicit_collective_list"),
}


def build(output: Path) -> dict[str, Any]:
    additional = output / "additional-reports"
    replay = output / "parser-v3-replay"
    inputs = [INPUT / name for name in (
        "flood_observations.csv", "clearance_observations.csv",
        "historical_incidents.csv", "candidate_duration_intervals.csv",
    )] + [REVIEW / name for name in (
        "qualified_observations.csv", "interval_qualification.csv",
        "clearance_episode_review.csv", "qualification_manifest.json", "review_rules.json",
    )] + [additional / "observations.csv", additional / "source_manifest.json", additional / "seeds.json",
           replay / "observations.csv", ROOT / "data/pasig_barangay_reference.csv",
           ROOT / "docs/plans/pasig-reported-subsidence-target.md",
           ROOT / "docs/evaluations/flood-duration-pilot-20261004/review_rules.json"]
    before = {path.relative_to(ROOT).as_posix(): digest(path) for path in inputs}
    previous_manifest = json.loads((REVIEW / "qualification_manifest.json").read_text(encoding="utf-8-sig"))
    for name, expected in previous_manifest["input_sha256"].items():
        if digest(INPUT / name) != expected:
            raise ValueError(f"Original review input changed: {name}")
    original = read_csv(INPUT / "flood_observations.csv")
    old = read_csv(REVIEW / "qualified_observations.csv")
    new = read_csv(additional / "observations.csv")
    intervals = read_csv(REVIEW / "interval_qualification.csv")
    clear = read_csv(INPUT / "clearance_observations.csv")
    history = read_csv(INPUT / "historical_incidents.csv")
    episodes = {row["shared_outcome_group"]: row for row in read_csv(REVIEW / "clearance_episode_review.csv")}
    v3 = {row["observation_id"]: row for row in read_csv(replay / "observations.csv")}
    if (len(original), len(old), len(new), len(intervals), len(clear), len(history)) != (467, 467, 352, 37, 3, 12):
        raise ValueError("Unexpected versioned input counts; review before changing this builder")
    if set(episodes) != set(SCOPES):
        raise ValueError("Unexpected reviewed proxy outcomes")
    sources = source_inventory()
    for item in json.loads((additional / "source_manifest.json").read_text(encoding="utf-8-sig")):
        if item["source_id"] in sources:
            raise ValueError("Additional source identity overlaps original inventory")
        sources[item["source_id"]] = {**item, "directory": additional}
    verified: dict[str, Any] = {}
    paths = {row["observation_id"]: verify_source(row, sources, verified) for row in original + new + clear + history}
    for sid, reviewed_source in previous_manifest["verified_sources"].items():
        if verified.get(sid) != reviewed_source:
            raise ValueError(f"Original reviewed source artifacts changed: {sid}")
    if len(v3) != 398 or len(verified) != 35 or sum(len(item["artifacts"]) for item in verified.values()) != 70:
        raise ValueError("Unexpected replay or source inventory count")
    old_by_id = {row["observation_id"]: row for row in old}
    for raw in original:
        if any(old_by_id[raw["observation_id"]].get(key) != value for key, value in raw.items()):
            raise ValueError(f"Original raw field changed: {raw['observation_id']}")
    merged: list[dict[str, Any]] = []
    parser_fields = ("barangay", "depth_cm_low", "depth_cm_high", "flags")
    for row in old + new:
        oid = row["observation_id"]
        if row["city"] != "Pasig" or row["status"] != "flood_observed":
            raise ValueError(f"Unexpected city/status: {oid}")
        fresh = oid not in old_by_id
        parsed = row if fresh else v3.get(oid)
        reviewed = dict(row)
        if fresh:
            episode = row["episode_group"]
            barangay = row["barangay"]
            timeline = key_id("TL-", [episode, row["city"], barangay.lower(), place_key(row["location_raw"])])
            depth_status = "usable_reported_numeric" if row["depth_cm_low"] or row["depth_cm_high"] else (
                "qualitative_only" if row["depth_raw"] else "not_reported")
            reviewed.update({
                "observation_date": row["observation_at"][:10],
                "source_bundle": additional.relative_to(ROOT).as_posix(),
                "source_capture_path": paths[oid],
                "evidence_components_verified": "true",
                "wet_evidence_status": "usable",
                "timing_status": "usable_reported_snapshot_clock",
                "geography_status": "source_reported_locality",
                "qualified_barangay": barangay,
                "depth_qualification": depth_status,
                "qualified_depth_cm_low": row["depth_cm_low"],
                "qualified_depth_cm_high": row["depth_cm_high"],
                "candidate_reporting_episode": episode,
                "candidate_timeline_id": timeline,
                "candidate_snapshot_id": key_id("SNAP-", [timeline, row["observation_at"], ""]),
                "duplicate_review": "none_flagged",
                "qualification_notes": "Captured source/evidence/clock reviewed; physical section and continuous episode identity remain unverified.",
                "duration_label_status": "excluded_wet_snapshot_alone_has_no_outcome",
                "training_admitted": "false",
            })
        if parsed:
            for field in ("source_id", "capture_version", "location_raw", "observation_at", "evidence", "status"):
                if parsed[field] != row[field]:
                    raise ValueError(f"Parser replay changed claim identity: {oid} {field}")
        reviewed.update({
            "register_version": VERSION,
            "origin_layer": "additional_official_capture_v3" if fresh else "preserved_qualification_v1",
            "parser_replay_version": "pasig-duration-pilot-v3" if parsed else "not_replayed_publisher_overlay_preserved",
            "reference_evidence_available_at": "",
            "availability_status": "publication_day_only_no_verified_pre_outcome_availability",
            **{"parser_v3_" + field: parsed[field] if parsed else "" for field in parser_fields},
        })
        merged.append(reviewed)
    wet_by_id = {row["observation_id"]: row for row in merged}
    if len(wet_by_id) != 819:
        raise ValueError("Observation IDs overlap; do not silently discard evidence")
    clear_by_id = {row["observation_id"]: row for row in clear}
    labels = []
    for row in intervals:
        wet = wet_by_id[row["last_wet_observation_id"]]
        closure = clear_by_id[row["clearance_observation_id"]]
        episode = episodes[closure["observation_id"]]
        minutes, inclusive, scope = SCOPES[closure["observation_id"]]
        reference = datetime.fromisoformat(wet["observation_at"])
        upper = datetime.fromisoformat(row["reported_clearance_upper_at"])
        if (upper - reference).total_seconds() != minutes * 60 or row["clearance_upper_inclusive"].lower() != inclusive:
            raise ValueError("Proxy bound differs from reviewed source-supported window")
        if wet["location_raw"] != row["location_raw"] or wet["qualified_barangay"] != row["barangay"]:
            raise ValueError("Proxy location differs from supported wet reference")
        labels.append({
            "label_id": "PROXY-" + row["candidate_id"], "candidate_id": row["candidate_id"],
            "target_version": TARGET, "review_rule_version": "collective-reported-subsidence-v1",
            "review_rule_id": row["review_rule_id"], "city": "Pasig",
            "qualified_barangay": wet["qualified_barangay"], "location_raw": wet["location_raw"],
            "reported_location_id": wet["candidate_timeline_id"], "section_id": "",
            "candidate_timeline_id": wet["candidate_timeline_id"],
            "reporting_episode_id": row["episode_group"], "shared_outcome_group": closure["observation_id"],
            "storm_group_id": "", "storm_identity_status": "not_established",
            "reference_observation_id": wet["observation_id"], "reference_at": wet["observation_at"],
            "reference_selection_policy": "retrospective_last_supported_wet_descriptive_only",
            "reference_clock_precision": "reported_minute", "prediction_as_of_at": "",
            "reference_evidence_available_at": "", "availability_status": "pre_outcome_availability_not_established",
            "subsidence_observation_id": closure["observation_id"], "summary_as_of_at": episode["summary_as_of_at"],
            "reported_scope": episode["reported_scope"], "scope_linkage_class": scope,
            "reported_subsidence_lower_at": wet["observation_at"], "reported_subsidence_upper_at": upper.isoformat(),
            "lower_minutes": 0, "lower_inclusive": "false", "upper_minutes": minutes, "upper_inclusive": inclusive,
            "censoring_type": "upper_bound_with_positive_time_support",
            "outcome_kind": "collective_reported_subsidence", "continuity_before_reference": "not_established",
            "recurrence_after_summary": "not_established", "physical_dry_status": "not_established",
            "passability_status": "not_established", "proxy_label_status": "admitted_collective_scope_conditional",
            "physical_section_label_status": "not_established", "training_admitted": "false",
            "training_exclusion_reason": "only_three_shared_outcomes;retrospective_reference;pre_outcome_feature_availability_unknown;section_identity_unverified",
            "wet_source_id": wet["source_id"], "subsidence_source_id": closure["source_id"],
            "wet_capture_path": paths[wet["observation_id"]], "subsidence_capture_path": paths[closure["observation_id"]],
            "wet_capture_sha256": verified[wet["source_id"]]["artifacts"]["text"]["sha256"],
            "subsidence_capture_sha256": verified[closure["source_id"]]["artifacts"]["text"]["sha256"],
            "wet_source_line_start": wet["source_line_start"], "subsidence_source_line_start": closure["source_line_start"],
            "wet_source_url": wet["source_url"], "subsidence_source_url": closure["source_url"],
            "scope_condition": "Summary must apply to this retained reported location; physical section identity is unverified.",
        })
    pairs = []
    morning = {row["location_raw"]: row for row in new if row["source_id"] == "PASIG-20250724-0600"}
    for later in new:
        if later["source_id"] != "PASIG-20250724-1100":
            continue
        earlier = morning[later["location_raw"]]
        gap = (datetime.fromisoformat(later["observation_at"]) - datetime.fromisoformat(earlier["observation_at"])).total_seconds() / 60
        if earlier["barangay"] != later["barangay"] or gap != 300:
            raise ValueError("Wet follow-up pair identity/time mismatch")
        pairs.append({
            "pair_id": key_id("PAIR-", [earlier["observation_id"], later["observation_id"]]),
            "city": "Pasig", "barangay": later["barangay"], "location_raw": later["location_raw"],
            "earlier_observation_id": earlier["observation_id"], "later_observation_id": later["observation_id"],
            "earlier_at": earlier["observation_at"], "later_at": later["observation_at"], "gap_minutes": int(gap),
            "earlier_depth_cm_low": earlier["depth_cm_low"], "earlier_depth_cm_high": earlier["depth_cm_high"],
            "later_depth_cm_low": later["depth_cm_low"], "later_depth_cm_high": later["depth_cm_high"],
            "earlier_capture_path": paths[earlier["observation_id"]], "later_capture_path": paths[later["observation_id"]],
            "interpretation": "Supported wet observation again five hours later, with lower reported depth.",
            "continuous_flooding_between_snapshots": "not_established", "clearance_status": "not_observed",
            "right_censored_label_admitted": "false", "training_admitted": "false",
            "reason": "No clearance inferred; recurrence/continuity must be reviewed before treating gap as survival censoring.",
        })
    if len(pairs) != 3:
        raise ValueError("Unexpected July 24 wet pair count")
    for name, rows in (("pasig_wet_observations.csv", merged), ("proxy_label_register.csv", labels), ("wet_followup_pairs.csv", pairs)):
        write_csv(output / name, rows)
    after = {path.relative_to(ROOT).as_posix(): digest(path) for path in inputs}
    if before != after:
        raise ValueError("Input bytes changed during export")
    manifest = {
        "register_version": VERSION, "target_version": TARGET, "review_date": "2026-10-05 Asia/Manila",
        "acquisition_cutoff": "2026-10-05 Asia/Manila; 2026 partial", "geography": "Pasig City",
        "counts": {"original_wet": 467, "additional_wet": 352, "merged_wet": len(merged),
                   "clearance_summaries": 3, "historical_context": 12, "evidence_records": len(merged) + 15,
                   "conditional_proxy_projections": len(labels), "shared_proxy_outcomes": 3,
                   "wet_followup_pairs": len(pairs), "training_admitted": 0},
        "wet_year_counts": dict(sorted(Counter(row["observation_date"][:4] for row in merged).items())),
        "2023_direct_report_coverage": "not_acquired",
        "original_raw_fields_preserved": True, "input_sha256": before,
        "builder_sha256": digest(Path(__file__)),
        "collector_sha256": digest(ROOT / "backend/scripts/collect_flood_duration_pilot.py"),
        "verified_source_count": len(verified),
        "verified_artifact_count": sum(len(source["artifacts"]) for source in verified.values()),
        "verified_sources": verified,
        "output_sha256": {name: digest(output / name) for name in (
            "pasig_wet_observations.csv", "proxy_label_register.csv", "wet_followup_pairs.csv")},
        "prediction_features_available_before_outcome": "not_established",
        "model_fitted": False, "runtime_changed": False,
    }
    (output / "dataset_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result = build(parser.parse_args().output.resolve())
    print(json.dumps({"counts": result["counts"], "verified_sources": result["verified_source_count"],
                      "verified_artifacts": result["verified_artifact_count"]}, indent=2))
