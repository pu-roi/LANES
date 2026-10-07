"""Fit an explicitly conditional Pasig research baseline from captured evidence.

Run from backend: python -m scripts.train_pasig_duration --output ../docs/evaluations/pasig-duration-model-20261007
No database, network, fabricated outcome or operational-expiry write occurs.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.flood_duration_model import (
    DurationObservation, ModelNotIdentifiableError, fit_lognormal_aft,
    interval_log_likelihood, predict_duration_distribution,
)
from scripts.qualify_pasig_duration_data import ROOT, digest, read_csv, source_inventory, verify_source

TARGET = "remaining_time_from_first_recorded_wet_to_reported_subsidence_continuity_assumed_v1"
INPUT = ROOT / "docs/evaluations/pasig-duration-followup-20261005"


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def grouped_observations(rows: list[dict[str, Any]]) -> list[DurationObservation]:
    counts = Counter(row["shared_outcome_group"] for row in rows)
    return [DurationObservation(float(row["experimental_lower_minutes"]), float(row["experimental_upper_minutes"]),
        1.0 / counts[row["shared_outcome_group"]], observation_id=row["label_id"]) for row in rows]


def build(output: Path, runtime_output: Path | None, figures: bool) -> dict[str, Any]:
    inputs = [INPUT / name for name in ("pasig_wet_observations.csv", "proxy_label_register.csv", "dataset_manifest.json")]
    input_hashes = {path.relative_to(ROOT).as_posix(): digest(path) for path in inputs}
    manifest = json.loads(inputs[-1].read_text(encoding="utf-8"))
    for name in ("pasig_wet_observations.csv", "proxy_label_register.csv"):
        if digest(INPUT / name) != manifest["output_sha256"][name]:
            raise ValueError(f"Working dataset hash differs from source-reviewed manifest: {name}")
    for source in manifest["verified_sources"].values():
        for artifact in source["artifacts"].values():
            if digest(ROOT / artifact["path"]) != artifact["sha256"]:
                raise ValueError("A captured evidence artifact has changed")
    wet = read_csv(inputs[0])
    labels = read_csv(inputs[1])
    if len(wet) != 819 or len(labels) != 37:
        raise ValueError("This versioned experiment expects the reviewed 819/37 evidence snapshot")
    wet_by_id = {row["observation_id"]: row for row in wet}
    if len(wet_by_id) != len(wet):
        raise ValueError("Duplicate observation identity")
    sources = source_inventory()
    additional = INPUT / "additional-reports"
    for source in json.loads((additional / "source_manifest.json").read_text(encoding="utf-8")):
        sources[source["source_id"]] = {**source, "directory": additional}
    verified: dict[str, Any] = {}
    candidates = []
    for proxy in labels:
        last = wet_by_id[proxy["reference_observation_id"]]
        # Deterministic reference selection considers timed wet snapshots only,
        # not depths/outcome clocks. The cohort itself is outcome-selected.
        available = [row for row in wet if row["candidate_timeline_id"] == proxy["candidate_timeline_id"]
                     and row["observation_at"] and row["observation_at"] <= last["observation_at"]]
        first = min(available, key=lambda row: (row["observation_at"], row["observation_id"]))
        first_at = datetime.fromisoformat(first["observation_at"])
        last_at = datetime.fromisoformat(last["observation_at"])
        upper_at = datetime.fromisoformat(proxy["reported_subsidence_upper_at"])
        lower, upper = (last_at - first_at).total_seconds() / 60, (upper_at - first_at).total_seconds() / 60
        if lower < 0 or upper <= lower or first["qualified_barangay"].casefold() != proxy["qualified_barangay"].casefold():
            raise ValueError("Invalid experimental interval or locality correspondence")
        first_path = verify_source(first, sources, verified)
        candidates.append({
            "label_id": proxy["label_id"], "source_proxy_target_version": proxy["target_version"],
            "experimental_target_version": TARGET, "city": "Pasig",
            "barangay": proxy["qualified_barangay"], "location_raw": proxy["location_raw"],
            "candidate_timeline_id": proxy["candidate_timeline_id"],
            "reporting_episode_id": proxy["reporting_episode_id"], "shared_outcome_group": proxy["shared_outcome_group"],
            "first_recorded_wet_id": first["observation_id"], "first_recorded_wet_at": first["observation_at"],
            "last_supported_wet_id": last["observation_id"], "last_supported_wet_at": last["observation_at"],
            "reported_subsidence_upper_at": proxy["reported_subsidence_upper_at"],
            "experimental_lower_minutes": lower, "lower_inclusive": "false",
            "experimental_upper_minutes": upper, "upper_inclusive": proxy["upper_inclusive"],
            "first_qualified_depth_cm_low": first["qualified_depth_cm_low"],
            "first_qualified_depth_cm_high": first["qualified_depth_cm_high"],
            "first_depth_qualification": first["depth_qualification"],
            "reference_selection_policy": "earliest_timed_wet_in_outcome_selected_candidate_timeline",
            "continuity_assumption": "No intervening subsidence and re-flooding between first and last recorded wet snapshots.",
            "scope_condition": proxy["scope_condition"], "episode_continuity_verified": "false",
            "reference_evidence_available_at": "", "prediction_as_of_at": "",
            "historical_prospective_availability_verified": "false",
            "experimental_fit_included": "true", "production_training_admitted": "false",
            "first_capture_path": first_path, "first_capture_sha256": digest(ROOT / first_path),
            "first_source_url": first["source_url"], "first_source_line_start": first["source_line_start"],
            "last_capture_path": proxy["wet_capture_path"], "last_capture_sha256": proxy["wet_capture_sha256"],
            "subsidence_capture_path": proxy["subsidence_capture_path"],
            "subsidence_capture_sha256": proxy["subsidence_capture_sha256"],
            "subsidence_source_url": proxy["subsidence_source_url"],
        })
    group_sizes = Counter(row["shared_outcome_group"] for row in candidates)
    for row in candidates:
        row["group_balanced_weight"] = 1.0 / group_sizes[row["shared_outcome_group"]]
    lineage = {
        "experiment_version": "pasig-conditional-aft-research-v1", "city": "Pasig",
        "created_at": datetime.now(timezone.utc).isoformat(), "input_sha256": input_hashes,
        "builder_sha256": digest(Path(__file__)),
        "kernel_sha256": digest(ROOT / "backend/app/services/flood_duration_model.py"),
        "reference_policy": "first_recorded_wet_in_outcome_selected_candidate_timeline",
        "continuity_assumption_required": True, "continuity_verified": False,
        "projection_count": len(candidates), "shared_outcome_count": len(group_sizes),
        "independent_storm_count": None, "production_training_admitted": 0,
        "deployment_eligible": False, "prospective_availability_verified": False,
        "feature_policy": "intercept_only_no_depth_location_rainfall_effects_learned",
        "validation_status": "conditional_summary_group_sensitivity_only_not_prospective_validation",
        "supported_barangays": sorted(set(row["barangay"] for row in candidates)),
        "reference_age_support_max_minutes": max(row["experimental_upper_minutes"] for row in candidates),
        "limitations": ["assumed_uninterrupted_episode", "conditional_collective_scope", "only_three_shared_summaries",
                        "outcome_selected_cohort", "unknown_historical_feature_availability", "no_independent_final_holdout",
                        "reported_subsidence_not_measured_dry_or_passable"],
    }
    model = fit_lognormal_aft(grouped_observations(candidates), lineage=lineage, target_version=TARGET)
    distribution = predict_duration_distribution(model, {})
    sensitivities = []
    for held_group in sorted(group_sizes):
        train = [row for row in candidates if row["shared_outcome_group"] != held_group]
        held = [row for row in candidates if row["shared_outcome_group"] == held_group]
        try:
            fitted = fit_lognormal_aft(grouped_observations(train), lineage={**lineage, "held_out_summary": held_group}, target_version=TARGET)
        except ModelNotIdentifiableError as exc:
            sensitivities.append({"held_out_summary": held_group, "status": "unidentifiable",
                                  "reason": str(exc), "prospective_accuracy_established": "false"})
            continue
        estimates = predict_duration_distribution(fitted, {})["quantiles"]
        held_nll = -sum(interval_log_likelihood(float(row["experimental_lower_minutes"]),
            float(row["experimental_upper_minutes"]), fitted.coefficients[0], fitted.scale) for row in held) / len(held)
        sensitivities.append({"held_out_summary": held_group, "status": "fitted_sensitivity",
            "training_shared_summaries": len(group_sizes) - 1, "held_out_projections": len(held),
            "held_out_mean_interval_negative_log_likelihood": held_nll,
            "p10_minutes": estimates[0]["total_minutes"], "median_minutes": estimates[1]["total_minutes"],
            "p90_minutes": estimates[2]["total_minutes"], "prospective_accuracy_established": "false"})
    # Actual original upper-only evidence: show location collapse with scale held
    # fixed for an identifiability diagnostic. These medians are hypotheses, not fits.
    diagnostic = []
    for median in (0.1, 1, 5, 15, 30, 60, 120, 240, 480, 960, 1920):
        nll = -sum(interval_log_likelihood(float(row["lower_minutes"]), float(row["upper_minutes"]),
            math.log(median), 1.0) / group_sizes[row["shared_outcome_group"]] for row in labels) / len(group_sizes)
        diagnostic.append({"hypothesized_median_minutes": median, "fixed_log_scale": 1.0,
            "original_upper_only_group_balanced_negative_log_likelihood": nll,
            "interpretation": "likelihood_diagnostic_not_a_trained_model"})
    output.mkdir(parents=True, exist_ok=True)
    write_rows(output / "conditional_training_candidates.csv", candidates)
    write_rows(output / "summary_group_sensitivity.csv", sensitivities)
    write_rows(output / "upper_bound_likelihood.csv", diagnostic)
    artifact = model.to_dict()
    (output / "conditional_aft.json").write_text(json.dumps(artifact, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if runtime_output:
        runtime_output.parent.mkdir(parents=True, exist_ok=True)
        runtime_output.write_text(json.dumps(artifact, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if figures:
        render_figures(output, candidates, sensitivities, diagnostic, distribution)
    report = {
        "experiment_version": lineage["experiment_version"], "target_version": TARGET,
        "status": "conditional_research_baseline_fitted", "model_fitted": True,
        "operational_prediction_finished": False, "deployment_eligible": False,
        "original_wet_count": len(wet), "experimental_projections": len(candidates),
        "positive_lower_bound_projections": sum(row["experimental_lower_minutes"] > 0 for row in candidates),
        "shared_outcomes": len(group_sizes), "production_training_admitted": 0,
        "assumptions": lineage["limitations"], "distribution_from_first_recorded_wet": distribution,
        "fit_diagnostics": dict(model.fit_diagnostics), "sensitivity": sensitivities,
        "model_sha256": digest(output / "conditional_aft.json"), "input_sha256": input_hashes,
        "verified_capture_artifacts": sum(len(source["artifacts"]) for source in manifest["verified_sources"].values()),
        "automated_tests_run": False, "runtime_expiry_modified": False,
    }
    if any(digest(ROOT / name) != expected for name, expected in input_hashes.items()):
        raise ValueError("Original dataset bytes changed during experiment")
    (output / "experiment_report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report


def render_figures(output: Path, candidates: list[dict[str, Any]], sensitivities: list[dict[str, Any]],
                   diagnostic: list[dict[str, Any]], distribution: dict[str, Any]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    grouped: dict[tuple[str, float, float], int] = Counter((row["shared_outcome_group"],
        row["experimental_lower_minutes"], row["experimental_upper_minutes"]) for row in candidates)
    group_names = {"OBS-c33d857e974b018d": "Maybunga Aug 11", "OBS-7d1d5441f76ee802": "Dela Paz Aug 18",
                   "OBS-aed0c046a22c54b0": "Listed areas Aug 30"}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    keys = list(grouped)
    labels = []
    for index, (group, low, high) in enumerate(keys):
        axes[0].plot([low / 60, high / 60], [index, index], linewidth=5, color="#246380")
        labels.append(f"{group_names[group]}: {grouped[(group, low, high)]} projections")
    axes[0].set_yticks(range(len(keys)), labels)
    axes[0].set_xlabel("Hours from first recorded wet observation")
    axes[0].set_title("Conditional intervals\nUninterrupted flooding assumed")
    axes[0].grid(axis="x", alpha=.2)
    axes[1].semilogx([row["hypothesized_median_minutes"] for row in diagnostic],
        [row["original_upper_only_group_balanced_negative_log_likelihood"] for row in diagnostic], marker="o")
    axes[1].set_xlabel("Hypothesized median (minutes)")
    axes[1].set_ylabel("Mean negative log likelihood")
    axes[1].set_title("Original upper-only evidence\nBetter likelihood toward zero duration")
    axes[1].grid(alpha=.2)
    fig.suptitle("Pasig duration evidence and model identifiability")
    fig.tight_layout()
    fig.savefig(output / "duration_evidence.png", dpi=180)
    fig.savefig(output / "duration_evidence.pdf")
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    full = distribution["quantiles"]
    rows = [("All three summaries", full[0]["total_minutes"], full[1]["total_minutes"], full[2]["total_minutes"])]
    rows += [(f"Without {group_names[row['held_out_summary']]}", row["p10_minutes"], row["median_minutes"], row["p90_minutes"])
             for row in sensitivities if row["status"] == "fitted_sensitivity"]
    for index, (label, low, middle, high) in enumerate(rows):
        ax.plot([low / 60, high / 60], [index, index], linewidth=4, color="#246380")
        ax.plot(middle / 60, index, "o", color="#c87828")
    ax.set_yticks(range(len(rows)), [row[0] for row in rows])
    ax.set_xlabel("Hours from first recorded wet observation (p10 / median / p90)")
    ax.set_title("Conditional AFT baseline sensitivity\nModel quantiles, not validated confidence or safety intervals")
    ax.grid(axis="x", alpha=.2)
    fig.tight_layout()
    fig.savefig(output / "model_sensitivity.png", dpi=180)
    fig.savefig(output / "model_sensitivity.pdf")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--runtime-output", type=Path)
    parser.add_argument("--skip-figures", action="store_true")
    args = parser.parse_args()
    report = build(args.output.resolve(), args.runtime_output.resolve() if args.runtime_output else None, not args.skip_figures)
    print(json.dumps({key: report[key] for key in ("status", "model_fitted", "deployment_eligible",
        "experimental_projections", "shared_outcomes", "production_training_admitted", "fit_diagnostics")}, indent=2))
