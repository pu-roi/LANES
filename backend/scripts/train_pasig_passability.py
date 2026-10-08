"""Separate conditional transport-recovery research fit; no invented dry labels.

Run from backend: python -m scripts.train_pasig_passability
The original subsidence artifact and reviewed source exports stay unchanged.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from app.services.flood_duration_model import (
    DurationObservation, PASSABILITY_TARGET_VERSION, ModelNotIdentifiableError,
    fit_lognormal_aft, interval_log_likelihood, predict_duration_distribution,
)
from scripts.clean_pasig_flood_history import barangay_key, load_barangay_reference
from scripts.qualify_pasig_duration_data import ROOT, digest, place_key, read_csv

BUNDLE = ROOT / "docs/evaluations/pasig-clearance-followup-20261007"
OUTPUT = ROOT / "docs/evaluations/pasig-passability-model-20261008"
RUNTIME = ROOT / "backend/runtime_data/flood-duration/passability_aft.json"


def candidates() -> tuple[list[dict], dict[str, str]]:
    manifest = json.loads((BUNDLE / "dataset_manifest.json").read_text(encoding="utf-8"))
    hashes = {(BUNDLE / "dataset_manifest.json").relative_to(ROOT).as_posix(): digest(BUNDLE / "dataset_manifest.json")}
    for name, expected in manifest["output_sha256"].items():
        path = BUNDLE / name
        if digest(path) != expected:
            raise ValueError("Reviewed passability export changed: " + name)
        hashes[path.relative_to(ROOT).as_posix()] = expected
    sources = json.loads((BUNDLE / "source_register.json").read_text(encoding="utf-8"))
    for source in sources.values():
        for kind in ("html", "text"):
            path = ROOT / source[f"{kind}_path"]
            if digest(path) != source[f"{kind}_sha256"]:
                raise ValueError("Reviewed capture changed")
            hashes[path.relative_to(ROOT).as_posix()] = digest(path)
    reference = load_barangay_reference(ROOT / "data/pasig_barangay_reference.csv")
    hashes["data/pasig_barangay_reference.csv"] = digest(ROOT / "data/pasig_barangay_reference.csv")
    observations = read_csv(BUNDLE / "observations.csv")
    by_id = {row["observation_id"]: row for row in observations}
    if len(by_id) != len(observations):
        raise ValueError("Duplicate observation ID")
    result = []
    for pair in read_csv(BUNDLE / "passability_followup_pairs.csv"):
        last = by_id[pair["reference_observation_id"]]
        outcome = by_id[pair["outcome_observation_id"]]
        if (pair["source_claim_reviewed"] != "true" or pair["independent_capture_review_completed"] != "true"
                or last["light_vehicle_passability"] != "not_passable"
                or outcome["light_vehicle_passability"] != "passable"):
            raise ValueError("A passability pair lacks reviewed matching endpoint meanings")
        location = place_key(last["location_raw"])
        episode = sources[last["source_id"]]["episode_group"]
        if sources[outcome["source_id"]]["episode_group"] != episode:
            raise ValueError("Outcome and reference are different episodes")
        # Conservative exact road key: no directional/section inference.
        eligible = [row for row in observations if row["light_vehicle_passability"] == "not_passable"
            and row["barangay"] == last["barangay"] and place_key(row["location_raw"]) == location
            and sources[row["source_id"]]["episode_group"] == episode
            and row["observation_at"] <= last["observation_at"]]
        first = min(eligible, key=lambda row: row["observation_at"])
        first_at, last_at, upper_at = (datetime.fromisoformat(row["observation_at"]) for row in (first, last, outcome))
        if not first_at <= last_at < upper_at:
            raise ValueError("Invalid passability observation chronology")
        barangay = reference[barangay_key(pair["barangay"])].name
        result.append({"pair_id": pair["pair_id"], "barangay": barangay, "location_raw": pair["location_raw"],
            "first_nonpassable_id": first["observation_id"], "first_nonpassable_at": first["observation_at"],
            "last_nonpassable_id": last["observation_id"], "last_nonpassable_at": last["observation_at"],
            "outcome_id": outcome["observation_id"], "reported_passability_upper_at": outcome["observation_at"],
            "lower_minutes": (last_at-first_at).total_seconds()/60,
            "upper_minutes": (upper_at-first_at).total_seconds()/60,
            "shared_outcome_group": pair["shared_outcome_group"], "scope_linkage_class": pair["scope_linkage_class"],
            "continuity_verified": False, "continuity_assumed_for_experiment": True,
            "historical_availability_verified": False, "production_training_admitted": False,
            "experimental_fit_included": True,
            "subsidence_label_admitted": False, "first_capture_path": first["capture_path"],
            "last_capture_path": last["capture_path"], "outcome_capture_path": outcome["capture_path"]})
    return result, hashes


def fit_rows(rows: list[dict], lineage: dict):
    groups = Counter(row["shared_outcome_group"] for row in rows)
    evidence = [DurationObservation(row["lower_minutes"], row["upper_minutes"],
        1/groups[row["shared_outcome_group"]], observation_id=row["pair_id"]) for row in rows]
    return fit_lognormal_aft(evidence, lineage=lineage, target_version=PASSABILITY_TARGET_VERSION)


def build(output: Path = OUTPUT, runtime: Path | None = RUNTIME) -> dict:
    rows, hashes = candidates()
    groups = sorted({row["shared_outcome_group"] for row in rows})
    reference = load_barangay_reference(ROOT / "data/pasig_barangay_reference.csv")
    lineage = {"city": "Pasig", "projection_count": len(rows), "shared_outcome_count": len(groups),
        "supported_barangays": sorted({row["barangay"] for row in rows}),
        "prediction_barangays": sorted(row.name for row in reference.values()),
        "geographic_policy": "pooled_pasig_experimental_transfer_not_barangay_validated",
        "reference_policy": "first_recorded_nonpassable_in_outcome_selected_timeline",
        "continuity_assumption_required": True, "deployment_eligible": False,
        "production_training_admitted": 0, "prospective_availability_verified": False,
        "reference_age_support_max_minutes": max(row["upper_minutes"] for row in rows),
        "input_sha256": hashes, "builder_sha256": digest(Path(__file__)),
        "limitations": ["two_shared_passability_outcomes", "outcome_selected_cohort", "assumed_continuous_nonpassability",
            "collective_scope_for_eight_projections", "unknown_pre_outcome_availability", "no_prospective_or_geographic_accuracy",
            "passable_does_not_mean_dry", "no_learned_depth_rainfall_or_locality_effects"]}
    model = fit_rows(rows, lineage)
    distribution = predict_duration_distribution(model, {})
    folds = []
    for group in groups:
        training = [row for row in rows if row["shared_outcome_group"] != group]
        held = [row for row in rows if row["shared_outcome_group"] == group]
        try:
            fitted = fit_rows(training, {**lineage, "held_out_group": group})
            score = -sum(interval_log_likelihood(row["lower_minutes"], row["upper_minutes"],
                fitted.coefficients[0], fitted.scale) for row in held)/len(held)
            folds.append({"held_out_group": group, "state": "fitted", "mean_interval_nll": score})
        except ModelNotIdentifiableError as exc:
            folds.append({"held_out_group": group, "state": "unidentifiable", "reason": str(exc)})
    output.mkdir(parents=True, exist_ok=True)
    with (output / "conditional_passability_candidates.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    artifact = json.dumps(model.to_dict(), indent=2, sort_keys=True, allow_nan=False) + "\n"
    (output / "passability_aft.json").write_text(artifact, encoding="utf-8")
    if any(digest(ROOT / path) != expected for path, expected in hashes.items()):
        raise ValueError("Evidence changed during fitting")
    if runtime is not None:
        runtime.parent.mkdir(parents=True, exist_ok=True)
        runtime.write_text(artifact, encoding="utf-8")
    report = {"target_version": PASSABILITY_TARGET_VERSION, "projections": len(rows), "shared_outcomes": len(groups),
        "training_barangays": lineage["supported_barangays"], "prediction_scope": lineage["geographic_policy"],
        "distribution": distribution, "summary_group_sensitivity": folds, "deployment_eligible": False,
        "observed_labels_imputed": False, "model_sha256": digest(output / "passability_aft.json"), "input_sha256": hashes}
    (output / "experiment_report.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+"\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
