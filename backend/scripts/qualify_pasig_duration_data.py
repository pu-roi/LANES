"""Rebuild reviewed Pasig evidence overlays; no network, application or DB access.

Original observations and captures are read-only. Review decisions are explicit in
review_rules.json. Candidate timelines/summary bounds are not physical-clearance
labels or proven meteorological storms.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "docs/evaluations/pasig-duration-cleanup-20261004"
DEFAULT_OUTPUT = ROOT / "docs/evaluations/pasig-duration-qualification-20261005"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normal(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def place_key(value: str) -> str:
    # Only punctuation/spacing and an explicit trailing barangay qualifier.
    # Do not combine streets, extensions, branches, directional lanes or typos.
    value = re.split(r"\b(?:Brgy\.?|Barangay)\s*", value, flags=re.I)[0]
    return re.sub(r"[^a-z0-9]", "", value.lower())


def key_id(prefix: str, parts: list[str]) -> str:
    return prefix + hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def source_inventory() -> dict[str, dict[str, Any]]:
    sources: dict[str, dict[str, Any]] = {}
    for bundle in ("flood-duration-pilot-20261004", "metro-manila-flood-duration-20261004"):
        directory = ROOT / "docs/evaluations" / bundle
        for name in ("source_manifest.json", "document_manifest.json"):
            path = directory / name
            if path.exists():
                for source in json.loads(path.read_text(encoding="utf-8-sig")):
                    sources[source["source_id"]] = {**source, "directory": directory}
    return sources


def verify_source(row: dict[str, str], sources: dict[str, dict[str, Any]], verified: dict[str, Any]) -> str:
    source = sources[row["source_id"]]
    sid = row["source_id"]
    if sid not in verified:
        artifacts = {}
        for kind in ("html", "text", "pdf"):
            if source.get(kind + "_path"):
                path = source["directory"] / source[kind + "_path"]
                actual = digest(path)
                if actual != source[kind + "_sha256"]:
                    raise ValueError(f"Capture hash mismatch: {sid} {kind}")
                artifacts[kind] = {"path": path.relative_to(ROOT).as_posix(), "sha256": actual}
        verified[sid] = {"artifacts": artifacts, "capture_version": source["capture_version"]}
    if row["capture_version"] != source["capture_version"] or row["source_url"] != source["url"]:
        raise ValueError(f"Source identity mismatch: {row['observation_id']}")
    path = source["directory"] / source["text_path"]
    text = normal(path.read_text(encoding="utf-8-sig"))
    if any(normal(part) not in text for part in row["evidence"].split(" | ")):
        raise ValueError(f"Evidence text mismatch: {row['observation_id']}")
    return path.relative_to(ROOT).as_posix()


def build(output: Path) -> dict[str, Any]:
    rules = json.loads((output / "review_rules.json").read_text(encoding="utf-8-sig"))
    input_names = ("flood_observations.csv", "clearance_observations.csv", "candidate_duration_intervals.csv", "historical_incidents.csv")
    original_hashes = {name: digest(INPUT / name) for name in input_names}
    wet, clear, intervals, history = (read_csv(INPUT / name) for name in input_names)
    all_observations = {row["observation_id"]: row for row in wet + clear + history}
    if len(all_observations) != 482 or len(wet) != 467 or len(intervals) != 37:
        raise ValueError("Unexpected input scope/counts; review this version before rebuilding")
    sources = source_inventory()
    verified: dict[str, Any] = {}
    paths = {oid: verify_source(row, sources, verified) for oid, row in all_observations.items()}
    overrides = rules["observation_overrides"]
    if set(overrides) - set(all_observations):
        raise ValueError("Review override references an unknown observation")
    observations = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw in wet:
        oid = raw["observation_id"]
        flags = set(filter(None, raw["flags"].split(";")))
        problems = []
        geography = "source_reported_locality"
        if flags & {"city_context_inferred", "street_alias_requires_review", "scope_and_alias_review"}:
            geography = "uncertain_section_or_alias"
            problems.append("Location context retained; no verified road-section correspondence.")
        timing = "usable_reported_snapshot_clock" if raw["observation_at"] else "uncertain_clock_date_only"
        if not raw["observation_at"]:
            problems.append("Keep reported date only; exclude from clock-based duration pairing.")
        low, high = raw["depth_cm_low"], raw["depth_cm_high"]
        if low or high:
            depth = "usable_reported_numeric"
        else:
            depth = "qualitative_only" if raw["depth_raw"] else "not_reported"
        if "shared_area_depth_upper_bound" in flags:
            depth = "usable_shared_upper_bound_not_road_measurement"
            low = ""
        if "source_alternate_units_disagree" in flags:
            depth, low, high = "uncertain_alternate_units", "", ""
        if "same_clock_depth_conflict" in flags:
            depth, low, high = "uncertain_same_clock_source_claims", "", ""
            problems.append("Same place/time has qualitative and numeric claims; retain both, do not average or select one.")
        override = overrides.get(oid, {})
        if raw["depth_raw"] == rules["rounding_review"]["raw_value"]:
            # A measurement feature retaining the reported metric, not a precise depth outcome.
            depth, low, high = "usable_reported_metric_with_rounding_qualifier", "20", "20"
            problems.append(rules["rounding_review"]["reason"])
        barangay = override.get("qualified_barangay", raw["barangay"])
        if override:
            depth = override.get("depth_status", depth)
            low = override.get("qualified_depth_cm_low", low)
            high = override.get("qualified_depth_cm_high", high)
            geography = override.get("geography_status", geography)
            if override.get("reason"):
                problems.append(override["reason"])
        episode = rules["episode_group_aliases"].get(raw["episode_group"], raw["episode_group"])
        timeline = key_id("TL-", [episode, raw["city"], barangay.lower(), place_key(raw["location_raw"])])
        snapshot = key_id("SNAP-", [timeline, raw["observation_at"] or raw["observation_date"], "" if raw["observation_at"] else raw["source_id"]])
        duplicate = "possible_shared_source_claim" if "possible_cross_source_duplicate" in flags else "none_flagged"
        reviewed = {
            **raw,
            "source_capture_path": paths[oid],
            "evidence_components_verified": "true",
            "wet_evidence_status": "usable",
            "timing_status": timing,
            "geography_status": geography,
            "qualified_barangay": barangay,
            "depth_qualification": depth,
            "qualified_depth_cm_low": low,
            "qualified_depth_cm_high": high,
            "candidate_reporting_episode": episode,
            "candidate_timeline_id": timeline,
            "candidate_snapshot_id": snapshot,
            "duplicate_review": override.get("duplicate_review", duplicate),
            "related_observation_ids": override.get("related_observation_ids", ""),
            "qualification_notes": " ".join(problems) or "Source-linked wet claim retained; no clearance inferred.",
            "duration_label_status": "excluded_wet_snapshot_alone_has_no_outcome",
            "training_admitted": "false",
        }
        observations.append(reviewed)
        grouped[timeline].append(reviewed)
    reviewed_by_id = {row["observation_id"]: row for row in observations}
    interval_reviews = []
    episode_members: dict[str, list[dict[str, str]]] = defaultdict(list)
    for raw in intervals:
        last = all_observations[raw["last_wet_observation_id"]]
        closure = all_observations[raw["clearance_observation_id"]]
        supports = [all_observations[oid] for oid in raw["support_observation_ids"].split(";")]
        if any(s["location_raw"] != raw["location_raw"] or s["barangay"] != raw["barangay"] for s in supports):
            raise ValueError(f"Candidate support identity mismatch: {raw['candidate_id']}")
        if last["observation_at"] != max(s["observation_at"] for s in supports):
            raise ValueError(f"Candidate last-wet mismatch: {raw['candidate_id']}")
        upper = datetime.fromisoformat(raw["reported_clearance_upper_at"])
        minutes = int((upper - datetime.fromisoformat(last["observation_at"])).total_seconds() / 60)
        if abs(float(raw["remaining_hours_high"]) - minutes / 60) > 0.000001:
            raise ValueError(f"Candidate interval arithmetic mismatch: {raw['candidate_id']}")
        interval_reviews.append({
            **raw,
            "candidate_timeline_id": reviewed_by_id[last["observation_id"]]["candidate_timeline_id"],
            "shared_outcome_group": closure["observation_id"],
            "last_wet_capture_path": paths[last["observation_id"]],
            "clearance_capture_path": paths[closure["observation_id"]],
            "conditional_remaining_minutes_low": 0,
            "conditional_remaining_minutes_high": minutes,
            "qualification_status": "uncertain",
            "descriptive_use": "usable_conditional_reported_subsidence_bound",
            "target_definition": "remaining_time_from_last_wet_to_reported_subsidence_if_summary_applies",
            "reason": "Summary is source-supported; individual physical road-section clearance/zero-water endpoint not verified. Unknown earlier continuity does not invalidate a last-wet-reference bound.",
            "training_admitted": "false",
        })
        episode_members[closure["observation_id"]].append(raw)
    episodes = []
    for closure in clear:
        oid = closure["observation_id"]
        members = episode_members[oid]
        review = rules["clearance_episode_reviews"][oid]
        minutes = next(row["conditional_remaining_minutes_high"] for row in interval_reviews if row["clearance_observation_id"] == oid)
        episodes.append({
            "shared_outcome_group": oid,
            "source_id": closure["source_id"],
            "source_url": closure["source_url"],
            "source_capture_path": paths[oid],
            "source_line_start": closure["source_line_start"],
            "summary_evidence": closure["evidence"],
            "reported_scope": review["reported_scope"],
            "summary_as_of_at": closure["observation_at"],
            "reference_last_wet_at": members[0]["last_observed_wet_at"],
            "reported_subsidence_upper_at": members[0]["reported_clearance_upper_at"],
            "upper_inclusive": members[0]["clearance_upper_inclusive"],
            "conditional_remaining_minutes_low": 0,
            "lower_inclusive": "false",
            "conditional_remaining_minutes_high": minutes,
            "linked_candidate_locations": len(members),
            "evidence_status": "usable",
            "analysis_role": "descriptive_reported_subsidence_summary",
            "physical_section_outcome_status": "uncertain",
            "source_linkage_basis": review["source_linkage_basis"],
            "meteorological_storm_independence": "not_established",
            "onset_at": "",
            "physical_clearance_at": "",
            "training_admitted": "false",
        })
    timelines = []
    for tid, members in sorted(grouped.items()):
        timed = sorted(set(row["observation_at"] for row in members if row["observation_at"]))
        linked = [row for row in interval_reviews if row["candidate_timeline_id"] == tid]
        timelines.append({
            "candidate_timeline_id": tid,
            "candidate_reporting_episode": members[0]["candidate_reporting_episode"],
            "city": "Pasig",
            "qualified_barangay": members[0]["qualified_barangay"],
            "location_mentions": ";".join(sorted(set(row["location_raw"] for row in members))),
            "wet_observation_count": len(members),
            "candidate_snapshot_count": len(set(row["candidate_snapshot_id"] for row in members)),
            "unique_reported_clocks": len(timed),
            "first_reported_wet_at": timed[0] if timed else "",
            "last_reported_wet_at": timed[-1] if timed else "",
            "elapsed_hours_between_snapshots": (datetime.fromisoformat(timed[-1]) - datetime.fromisoformat(timed[0])).total_seconds() / 3600 if timed else "",
            "observation_ids": ";".join(row["observation_id"] for row in members),
            "source_ids": ";".join(sorted(set(row["source_id"] for row in members))),
            "conditional_interval_candidate_ids": ";".join(row["candidate_id"] for row in linked),
            "physical_clearance_status": "uncertain_summary_link" if linked else "not_observed",
            "identity_status": "uncertain_alias_or_cross_day_identity" if any(row["geography_status"].startswith("uncertain") for row in members) else "candidate_same_reported_place",
            "continuous_flooding_between_snapshots": "not_established",
            "independent_storm_status": "not_established",
            "training_admitted": "false",
        })
    historical = [{
        **raw,
        "source_capture_path": paths[raw["observation_id"]],
        "evidence_status": "usable",
        "analysis_role": "historical_occurrence_and_status_context",
        "remaining_time_label_status": "excluded_no_timed_wet_snapshot_or_location_clearance_clock",
        "reason": "Occurrence clock is not a wet follow-up; latest Subsided is an untimed status. Report issue time cannot establish exact clearance or observation-reference duration.",
        "training_admitted": "false",
    } for raw in history]
    outputs = {
        "qualified_observations.csv": observations,
        "candidate_timelines.csv": timelines,
        "interval_qualification.csv": interval_reviews,
        "clearance_episode_review.csv": episodes,
        "historical_qualification.csv": historical,
    }
    for name, rows in outputs.items():
        write_csv(output / name, rows)
    if original_hashes != {name: digest(INPUT / name) for name in input_names}:
        raise ValueError("Original input files unexpectedly changed")
    summary = {
        "review_version": rules["review_version"],
        "review_date": "2026-10-05 Asia/Manila",
        "collection_cutoff": "2026-10-04 Asia/Manila (unchanged)",
        "source_scope": "Pasig City",
        "input_sha256": original_hashes,
        "review_rules_sha256": digest(output / "review_rules.json"),
        "builder_sha256": digest(Path(__file__)),
        "verified_source_count": len(verified),
        "verified_sources": verified,
        "output_rows": {name: len(rows) for name, rows in outputs.items()},
        "output_sha256": {name: digest(output / name) for name in outputs},
        "wet_evidence_status_counts": dict(Counter(row["wet_evidence_status"] for row in observations)),
        "timing_status_counts": dict(Counter(row["timing_status"] for row in observations)),
        "depth_qualification_counts": dict(Counter(row["depth_qualification"] for row in observations)),
        "geography_status_counts": dict(Counter(row["geography_status"] for row in observations)),
        "candidate_reporting_groups": sorted(set(row["candidate_reporting_episode"] for row in observations)),
        "shared_summary_outcomes": len(episodes),
        "candidate_wet_snapshot_groups": len(set(row["candidate_snapshot_id"] for row in observations)),
        "usable_exact_physical_duration_labels": 0,
        "training_admitted_examples": 0,
        "interpretation": "Source evidence qualified; timelines/conditional summary bounds are exploratory, not model-ready physical-clearance labels or independently verified storms.",
    }
    (output / "qualification_manifest.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {key: value for key, value in summary.items() if key not in {"verified_sources", "input_sha256", "output_sha256"}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2, ensure_ascii=False))
