"""Rebuild evidence and compare research baselines by held-out shared summary.

This is conditional sensitivity, not independent-storm or prospective accuracy.
No database, network, runtime-model overwrite or zone mutation is performed.
"""
from __future__ import annotations

import argparse
import json
import math
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import scipy
from scipy.optimize import minimize_scalar

from app.services.flood_duration_model import (
    DurationObservation, fit_lognormal_aft, interval_log_likelihood,
    predict_duration_distribution,
)
from scripts.qualify_pasig_duration_data import ROOT, digest, read_csv
from scripts.train_pasig_duration import TARGET, build, grouped_observations, write_rows


def exponential_log_likelihood(lower: float, upper: float | None, mean: float) -> float:
    """Stable censored exponential likelihood; exact outcomes use density."""
    item = DurationObservation(lower, upper, 1.0)
    if isinstance(mean, bool) or not math.isfinite(mean) or mean <= 0:
        raise ValueError("Exponential mean must be finite and positive")
    if item.upper_minutes is None:
        return -item.lower_minutes / mean
    if item.upper_minutes == item.lower_minutes:
        return -math.log(mean) - item.lower_minutes / mean
    return -item.lower_minutes / mean + math.log(-math.expm1(
        -(item.upper_minutes - item.lower_minutes) / mean))


def fit_exponential(rows: Sequence[DurationObservation]) -> float:
    if not rows or not any(row.lower_minutes > 0 for row in rows) or not any(row.upper_minutes is not None for row in rows):
        raise ValueError("Evidence does not identify a positive finite exponential baseline")
    total_weight = math.fsum(row.weight for row in rows)
    def objective(log_mean: float) -> float:
        mean = math.exp(log_mean)
        return -math.fsum(row.weight * exponential_log_likelihood(
            row.lower_minutes, row.upper_minutes, mean) for row in rows) / total_weight
    # Reject, rather than publish, an optimizer-safeguard boundary solution.
    result = minimize_scalar(objective, bounds=(-20, 30), method="bounded",
                             options={"xatol": 1e-10})
    if not result.success or not math.isfinite(result.fun) or min(result.x + 20, 30 - result.x) < .001:
        raise ValueError("No supported finite exponential fit")
    return math.exp(result.x)


def evaluate(output: Path) -> dict[str, Any]:
    original = ROOT / "docs/evaluations/pasig-duration-model-20261007"
    runtime = ROOT / "backend/runtime_data/flood-duration/conditional_aft.json"
    followup = ROOT / "docs/evaluations/pasig-clearance-followup-20261007/dataset_manifest.json"
    inputs = [original / "conditional_training_candidates.csv", original / "conditional_aft.json", followup, runtime]
    before = {path.relative_to(ROOT).as_posix(): digest(path) for path in inputs}
    with tempfile.TemporaryDirectory(prefix="lanes-duration-evaluation-") as temporary:
        rebuilt = Path(temporary)
        build(rebuilt, None, False)  # Revalidates original dataset and captured-source hashes.
        if digest(rebuilt / "conditional_training_candidates.csv") != digest(inputs[0]):
            raise ValueError("Rebuilt candidates differ from recorded experiment")
        rows = read_csv(rebuilt / "conditional_training_candidates.csv")
        recreated = json.loads((rebuilt / "conditional_aft.json").read_text(encoding="utf-8"))
        recorded = json.loads(inputs[1].read_text(encoding="utf-8"))
        if (abs(recreated["coefficients"][0] - recorded["coefficients"][0]) > 1e-6
                or abs(recreated["scale"] - recorded["scale"]) > 1e-6):
            raise ValueError("Rebuilt fitted parameters differ from recorded experiment")
    groups = sorted({row["shared_outcome_group"] for row in rows})
    output.mkdir(parents=True, exist_ok=True)
    folds: list[dict[str, Any]] = []
    feature_audit = []
    for group in groups:
        training = [row for row in rows if row["shared_outcome_group"] != group]
        held = [row for row in rows if row["shared_outcome_group"] == group]
        training_groups = sorted({row["shared_outcome_group"] for row in training})
        assert group not in training_groups
        observations = grouped_observations(training)
        model = fit_lognormal_aft(observations, lineage={"held_out_summary": group,
            "training_summaries": training_groups, "deployment_eligible": False}, target_version=TARGET)
        (output / f"lognormal-without-{group}.json").write_text(
            json.dumps(model.to_dict(), indent=2, allow_nan=False) + "\n", encoding="utf-8")
        mean = fit_exponential(observations)
        quantiles = predict_duration_distribution(model, {})["quantiles"]
        for algorithm in ("lognormal_aft", "exponential"):
            likelihoods = [interval_log_likelihood(float(row["experimental_lower_minutes"]),
                float(row["experimental_upper_minutes"]), model.coefficients[0], model.scale)
                if algorithm == "lognormal_aft" else exponential_log_likelihood(
                    float(row["experimental_lower_minutes"]), float(row["experimental_upper_minutes"]), mean)
                for row in held]
            values = [item["total_minutes"] for item in quantiles] if algorithm == "lognormal_aft" else [
                -mean * math.log1p(-q) for q in (.1, .5, .9)]
            folds.append({"held_out_summary": group, "algorithm": algorithm,
                "training_summaries": "|".join(training_groups), "held_out_projections": len(held),
                "mean_interval_negative_log_likelihood": -math.fsum(likelihoods) / len(held),
                "p10_minutes": values[0], "median_minutes": values[1], "p90_minutes": values[2],
                "exponential_mean_minutes": mean if algorithm == "exponential" else "",
                "prospective_accuracy_established": False})
        feature_audit.append({"shared_outcome_group": group, "projections": len(held),
            "qualified_depth_rows": sum(bool(row["first_qualified_depth_cm_low"]) for row in held),
            "depth_qualifications": dict(Counter(row["first_depth_qualification"] for row in held)),
            "verified_pre_issuance_availability_rows": sum(
                row["historical_prospective_availability_verified"] == "true" for row in held),
            "verified_continuity_rows": sum(row["episode_continuity_verified"] == "true" for row in held)})
    write_rows(output / "held_summary_comparison.csv", folds)
    render_comparison(output, folds, groups)
    latest = json.loads(followup.read_text(encoding="utf-8"))["counts"]
    aggregate = {algorithm: math.fsum(row["mean_interval_negative_log_likelihood"]
        for row in folds if row["algorithm"] == algorithm) / len(groups)
        for algorithm in ("lognormal_aft", "exponential")}
    report = {"evaluation_version": "pasig-conditional-baseline-comparison-v1",
        "created_at": datetime.now(timezone.utc).isoformat(), "projection_count": len(rows),
        "shared_outcome_count": len(groups), "verified_independent_storm_count": 0,
        "new_followup_duration_pairs": latest["new_subsidence_duration_pairs"],
        "candidate_rebuild_and_parameter_reproduction_verified": True,
        "group_equal_mean_interval_negative_log_likelihood": aggregate,
        "lower_nll_is_better": True, "feature_audit": feature_audit,
        "feature_model_training_admitted": False, "prospective_accuracy_established": False,
        "deployment_eligible": False, "runtime_artifact_modified": False,
        "input_sha256": before, "scipy_version": scipy.__version__,
        "evaluator_sha256": digest(Path(__file__)),
        "limitations": ["three_shared_summaries_not_verified_independent_storms",
            "conditional_continuity_and_collective_scope", "outcome_selected_cohort",
            "unknown_pre_issuance_feature_availability", "summary_sensitivity_not_final_holdout",
            "interval_nll_not_minute_error_or_calibrated_accuracy"]}
    if any(digest(ROOT / name) != expected for name, expected in before.items()):
        raise ValueError("Research inputs or packaged model changed during evaluation")
    generated = [output / "held_summary_comparison.csv", output / "baseline_comparison.png",
                 output / "baseline_comparison.pdf"]
    generated.extend(output / f"lognormal-without-{group}.json" for group in groups)
    report["output_sha256"] = {path.name: digest(path) for path in generated}
    (output / "evaluation_report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report


def render_comparison(output: Path, folds: list[dict[str, Any]], groups: list[str]) -> None:
    """Saved scientific figure; three summaries are not three verified storms."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = {"OBS-7d1d5441f76ee802": "Dela Paz Aug 18",
             "OBS-aed0c046a22c54b0": "Listed areas Aug 30",
             "OBS-c33d857e974b018d": "Maybunga Aug 11"}
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for offset, algorithm, color in ((-.18, "lognormal_aft", "#246380"), (.18, "exponential", "#c87828")):
        values = [next(row["mean_interval_negative_log_likelihood"] for row in folds
                       if row["algorithm"] == algorithm and row["held_out_summary"] == group) for group in groups]
        ax.bar([index + offset for index in range(len(groups))], values, width=.34,
               label=algorithm.replace('_', ' ').title(), color=color)
    ax.set_xticks(range(len(groups)), [names[group] for group in groups])
    ax.set_ylabel("Held-summary mean interval negative log likelihood\nLower is better")
    ax.set_title("Conditional subsidence baseline comparison\nShared-summary sensitivity; not prospective accuracy")
    ax.legend()
    ax.grid(axis="y", alpha=.2)
    fig.tight_layout()
    fig.savefig(output / "baseline_comparison.png", dpi=200)
    fig.savefig(output / "baseline_comparison.pdf")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    result = evaluate(arguments.output.resolve())
    print(json.dumps({key: result[key] for key in ("projection_count", "shared_outcome_count",
        "group_equal_mean_interval_negative_log_likelihood", "deployment_eligible")}, indent=2))
