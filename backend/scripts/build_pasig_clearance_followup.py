"""Build a reviewed retrospective evidence overlay without changing ML inputs.

Uses only stdlib and cached captures. Run from repo root with Python. No network,
database, model fitting, expiry update, or application publication occurs.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "docs/evaluations/pasig-clearance-followup-20261007"
ANCESTOR = ROOT / "docs/evaluations/pasig-duration-followup-20261005"
VERSION = "pasig-clearance-followup-overlay-v2-independent-review"
PASSABILITY_TARGET = "elapsed_from_supported_nonpassable_reference_to_reported_light_vehicle_passability_v1"
SUBSIDENCE_TARGET = "remaining_time_from_supported_wet_reference_to_scope_matched_reported_subsidence_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def build() -> dict:
    rules_path = BUNDLE / "review_rules.json"
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    reviewed = rules["independent_capture_review_completed"] is True
    review_path = BUNDLE / "independent_review.json"
    review = json.loads(review_path.read_text(encoding="utf-8")) if reviewed else None
    if reviewed and (review["independent_capture_review_completed"] is not True
            or review["source_text_sha256"] != rules["source_text_sha256"]):
        raise ValueError("Independent review belongs to different evidence")
    review_flag = "true" if reviewed else "false"
    if rules["version"] != "pasig-clearance-followup-review-v1":
        raise ValueError("Unsupported review version")
    inputs = {path.relative_to(ROOT).as_posix(): digest(path) for path in (
        rules_path, BUNDLE / "pasig-seeds.json", BUNDLE / "publisher-seeds.json", review_path,
        BUNDLE / "official/source_manifest.json", BUNDLE / "publishers/source_manifest.json",
        Path(__file__).resolve(), ROOT / "backend/scripts/collect_flood_duration_pilot.py",
        ROOT / "backend/scripts/collect_flood_report_archive.py",
        ANCESTOR / "dataset_manifest.json", ANCESTOR / "pasig_wet_observations.csv",
        ANCESTOR / "proxy_label_register.csv",
        ROOT / "backend/runtime_data/flood-duration/conditional_aft.json",
    )}
    ancestor = json.loads((ANCESTOR / "dataset_manifest.json").read_text(encoding="utf-8"))
    for name in ("pasig_wet_observations.csv", "proxy_label_register.csv"):
        if digest(ANCESTOR / name) != ancestor["output_sha256"][name]:
            raise ValueError("Original dataset changed: " + name)
    ancestor_captures = 0
    for source in ancestor["verified_sources"].values():
        for artifact in source["artifacts"].values():
            if digest(ROOT / artifact["path"]) != artifact["sha256"]:
                raise ValueError("Original source changed: " + artifact["path"])
            ancestor_captures += 1
    if ancestor_captures != 70:
        raise ValueError("Expected original 70 captures")

    sources, texts = {}, {}
    for directory in ("official", "publishers"):
        for source in json.loads((BUNDLE / directory / "source_manifest.json").read_text(encoding="utf-8")):
            sid = source["source_id"]
            if sid in sources or source["status"] != "captured":
                raise ValueError("Missing/duplicate captured source: " + sid)
            normalized = {**source, "publisher": "City Government of Pasig" if directory == "official" else "GMA News Online"}
            for kind in ("html", "text"):
                path = BUNDLE / directory / source[f"{kind}_path"]
                if digest(path) != source[f"{kind}_sha256"]:
                    raise ValueError("Capture checksum mismatch: " + sid)
                normalized[f"{kind}_path"] = path.relative_to(ROOT).as_posix()
            if source["text_sha256"] != rules["source_text_sha256"][sid]:
                raise ValueError("Reviewed rules belong to another capture: " + sid)
            normalized["source_notes"] = rules["source_notes"].get(sid, "")
            normalized["historical_availability_verified"] = False
            normalized["independent_capture_review_completed"] = rules["independent_capture_review_completed"]
            if directory == "publishers":
                html = (ROOT / normalized["html_path"]).read_text(encoding="utf-8")
                for field in ("datePublished", "dateModified"):
                    match = re.search(r'"' + field + r'"\s*:\s*"([^"{}]+)"', html)
                    normalized[field] = match.group(1) if match else None
                normalized["publication_metadata_provenance"] = "captured HTML JSON-LD; not historical-version proof"
                if normalized["datePublished"] != "2025-10-10T13:18:20+08:00":
                    raise ValueError("GMA source date requires renewed review")
            sources[sid] = normalized
            texts[sid] = (ROOT / normalized["text_path"]).read_text(encoding="utf-8").splitlines()
    if set(sources) != set(rules["source_text_sha256"]):
        raise ValueError("Reviewed/captured source inventory differs")

    observations = []
    index = {}

    def add(sid: str, line: int, at: str, status: str, barangay: str,
            location: str, evidence_lines: list[int], clock_line: int,
            passability: str = "unknown", depth: str = "", note: str = "") -> dict:
        references = sorted(set(evidence_lines))
        selected = [texts[sid][number - 1] for number in references]
        # Versions, line and state distinguish claims without count inflation.
        identity = f"{sid}|{sources[sid]['capture_version']}|{line}|{at}|{status}"
        row = {
            "observation_id": "OBS-" + hashlib.sha256(identity.encode()).hexdigest()[:16],
            "source_id": sid, "capture_version": sources[sid]["capture_version"],
            "city": "Pasig", "barangay": barangay, "location_raw": location,
            "status": status, "observation_at": at, "clock_precision": "minute",
            "clock_evidence": texts[sid][clock_line - 1],
            "evidence_lines": ";".join(map(str, references)), "evidence": " | ".join(selected),
            "light_vehicle_passability": passability, "raw_depth": depth,
            "source_url": sources[sid]["url"], "capture_path": sources[sid]["text_path"],
            "capture_sha256": sources[sid]["text_sha256"],
            "source_claim_reviewed": "true", "independent_capture_review_completed": review_flag,
            "historical_availability_verified": "false", "production_training_admitted": "false",
            "review_notes": note,
        }
        key = (sid, line, at)
        if key in index:
            raise ValueError("Duplicate reviewed observation")
        observations.append(row)
        index[key] = row
        return row

    for frame in rules["wet_frames"]:
        sid = frame["source_id"]
        status_text = texts[sid][frame["status_line"] - 1]
        if "NOT PASSABLE" not in status_text or "flooding" not in status_text:
            raise ValueError("Wet/nonpassable claim meaning changed")
        for line, barangay in frame["locations"]:
            raw = texts[sid][line - 1].lstrip("- �")
            location = "Infant Jesus St., Metroville, Brgy. Manggahan" if sid == "PASIG-20240903-1200" and line == 12 else raw
            add(sid, line, frame["observation_at"], "flood_observed", barangay, location,
                [frame["clock_line"], frame["status_line"], line], frame["clock_line"], "not_passable",
                note="Multi-road/group source labels remain unsplit; a road name is not a verified spatial section.")

    pairs = []
    for recovery in rules["passability_recovery"]:
        sid, line = recovery["source_id"], recovery["outcome_line"]
        text = texts[sid][line - 1]
        if "passable" not in text.casefold() or "not passable" in text.casefold():
            raise ValueError("Recovery statement meaning changed")
        direct = recovery["scope_linkage_class"] == "direct_location"
        outcome = add(sid, line, recovery["outcome_at"], "flood_observed" if direct else "passability_recovered_summary",
            "Manggahan" if direct else "", recovery["scope"], [line, recovery["clock_line"]],
            recovery["clock_line"], "passable", recovery.get("raw_depth", ""),
            "Water remains; raw 2-3 inches and gutter-deep qualifier are preserved without reconciliation." if direct
            else "Collective light-vehicle passability statement does not assert dry roads.")
        for wet_line in recovery["wet_lines"]:
            reference = index[(sid, wet_line, recovery["wet_clock"])]
            minutes = (datetime.fromisoformat(outcome["observation_at"]) - datetime.fromisoformat(reference["observation_at"])).total_seconds() / 60
            if minutes <= 0:
                raise ValueError("Nonchronological reported recovery")
            pairs.append({
                "pair_id": "PAIR-" + hashlib.sha256((reference["observation_id"] + outcome["observation_id"]).encode()).hexdigest()[:16],
                "target_version": PASSABILITY_TARGET,
                "reference_observation_id": reference["observation_id"], "outcome_observation_id": outcome["observation_id"],
                "city": "Pasig", "barangay": reference["barangay"], "location_raw": reference["location_raw"],
                "reference_at": reference["observation_at"], "reported_passability_upper_at": outcome["observation_at"],
                "lower_minutes": 0, "upper_minutes": minutes, "lower_inclusive": "false", "upper_inclusive": "true",
                "censoring_type": "upper_bound_on_reported_passability_after_reference",
                "scope_linkage_class": recovery["scope_linkage_class"], "reporting_episode_id": sources[sid]["episode_group"],
                "shared_outcome_group": outcome["observation_id"], "storm_independence_verified": "false",
                "continuity_status": "unverified; no first-recovery event time inferred",
                "reference_available_at": "", "prediction_as_of_at": "", "historical_availability_verified": "false",
                "source_claim_reviewed": "true", "descriptive_only": "true", "independent_capture_review_completed": review_flag,
                "experimental_fit_included": "false", "production_training_admitted": "false",
                "subsidence_label_admitted": "false",
                "exclusion_reason": "different target: reported light-vehicle passability does not establish subsidence; source availability/continuity unverified",
            })

    outcomes = []
    for rule in rules["subsidence_outcomes"]:
        sid, line = rule["source_id"], rule["outcome_line"]
        if texts[sid][rule["city_line"] - 1] != "Pasig City" or "subsided as of 12:49 p.m." not in texts[sid][line - 1]:
            raise ValueError("City or subsidence claim changed")
        observation = add(sid, line, rule["outcome_at"], "reported_subsidence", rule["barangay"], rule["location_raw"],
            [rule["city_line"], line], line, "passable", rule["raw_depth"],
            "Explicit road outcome; prior wet time unresolved. Retained depth is not a clocked pre-outcome feature.")
        outcomes.append({
            "outcome_id": observation["observation_id"], "target_version": SUBSIDENCE_TARGET,
            "city": "Pasig", "barangay": "", "location_raw": rule["location_raw"],
            "reported_subsidence_upper_at": rule["outcome_at"], "upper_inclusive": "true", "exact_end_known": "false",
            "reference_observation_id": "", "reference_at": "", "duration_lower_minutes": "", "duration_upper_minutes": "",
            "pair_status": "outcome_only_missing_preceding_wet_clock", "source_claim_reviewed": "true",
            "independent_capture_review_completed": review_flag, "historical_availability_verified": "false",
            "reporting_episode_id": sources[sid]["episode_group"], "shared_outcome_group": observation["observation_id"],
            "experimental_fit_included": "false", "production_training_admitted": "false",
            "exclusion_reason": rule["reference_status"], "endpoint_interpretation": rule["endpoint_interpretation"],
            "source_id": sid, "source_url": sources[sid]["url"], "evidence_lines": observation["evidence_lines"],
        })
    for rule in rules["context"]:
        add(rule["source_id"], rule["evidence_line"], rule["observation_at"], "city_flood_context", "",
            rule["location_raw"], [rule["clock_line"], rule["evidence_line"]], rule["evidence_line"], note=rule["reason"])
    if len({row["observation_id"] for row in observations}) != len(observations):
        raise ValueError("Duplicate observation ID")
    for name, rows in (("observations.csv", observations), ("passability_followup_pairs.csv", pairs), ("subsidence_outcomes.csv", outcomes)):
        write_csv(BUNDLE / name, rows, list(rows[0]))
    write_json(BUNDLE / "source_register.json", sources)
    counts = {
        "new_captured_sources": len(sources), "new_capture_artifacts": len(sources) * 2,
        "reviewed_observations": len(observations), "wet_observations": sum(row["status"] == "flood_observed" for row in observations),
        "new_explicit_subsidence_outcomes": len(outcomes), "new_subsidence_duration_pairs": 0,
        "passability_projections": len(pairs), "passability_shared_outcomes": len({row["shared_outcome_group"] for row in pairs}),
        "passability_direct_location_projections": sum(row["scope_linkage_class"] == "direct_location" for row in pairs),
        "passability_collective_projections": sum(row["scope_linkage_class"] == "collective_conditional" for row in pairs),
        "verified_independent_storms": 0, "production_training_admitted": 0,
    }
    manifest = {
        "register_version": VERSION, "built_at": datetime.now(timezone.utc).isoformat(), "geography": "Pasig City",
        "counts": counts, "status_counts": dict(Counter(row["status"] for row in observations)),
        "ancestor_dataset_preserved": True, "verified_ancestor_capture_artifacts": ancestor_captures,
        "source_review": "coordinator reconstructed exact captured source lines and clocks",
        "independent_capture_review_completed": reviewed,
        "independent_reviewer": review["reviewer"] if reviewed else None,
        "review_limitation": "Source accuracy review does not establish continuity, historical availability, storm independence or training eligibility.",
        "input_sha256": inputs,
        "output_sha256": {name: digest(BUNDLE / name) for name in ("observations.csv", "passability_followup_pairs.csv", "subsidence_outcomes.csv", "source_register.json")},
        "model_retrained": False, "runtime_expiry_modified": False, "automated_tests_run": False,
        "prospective_prediction_admitted": False,
    }
    write_json(BUNDLE / "dataset_manifest.json", manifest)
    return counts


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
