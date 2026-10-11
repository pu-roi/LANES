"""Reproducible conditional cross-location experiments; no DB or runtime writes.

Run: python -m scripts.evaluate_cross_location_duration --output <new-directory>
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime
import json
import math
from pathlib import Path
from typing import Any

from app.services.cross_location_duration_model import (
    CrossLocationObservation, fit_cross_location, prediction_parameters,
)
from app.services.flood_duration_model import (
    DurationModelError, DurationObservation, ModelNotIdentifiableError,
    fit_lognormal_aft, interval_log_likelihood,
)
from app.services.philippine_location_service import get_philippine_location_service
from scripts.evaluate_pasig_duration import exponential_log_likelihood, fit_exponential
from scripts.qualify_pasig_duration_data import ROOT, digest, read_csv
from scripts.train_pasig_duration import write_rows

COMPARISON = ROOT / "docs/evaluations/pasig-location-feature-models-20261008/feature_comparison.json"
CANDIDATES = ROOT / "docs/evaluations/pasig-duration-model-20261007/conditional_training_candidates.csv"
WET = ROOT / "docs/evaluations/pasig-duration-followup-20261005"
PRIORS = (0.0, .15, .35, .70)
BLOCKERS = ["only_three_shared_outcomes", "no_verified_independent_storms",
            "outcome_selected_cohort", "collective_scope_and_continuity_assumed",
            "historical_predictor_availability_unverified", "no_prospective_calibration",
            "fixed_prior_and_residual_scale_uncertainty_not_fully_modelled"]


def qualify_rows(rows: list[dict[str, str]], wet: list[dict[str, str]]) -> tuple[list[CrossLocationObservation], list[dict[str, Any]]]:
    """Export conditional eligibility; never upgrade historical production admission."""
    sources = {r["observation_id"]: r for r in wet}
    ids = Counter(r.get("label_id") for r in rows)
    locations = get_philippine_location_service()
    qualified, register = [], []
    for row in rows:
        reasons = []
        name = locations.normalize_barangay_name(row.get("barangay", ""), "Pasig")
        source = sources.get(row.get("first_recorded_wet_id"))
        if row.get("city") != "Pasig" or name is None:
            reasons.append("unknown_or_outside_pasig_location")
        if ids[row.get("label_id")] != 1:
            reasons.append("duplicate_label_identity")
        if (row.get("first_depth_qualification") != "usable_reported_numeric"
                or not row.get("first_qualified_depth_cm_low")
                or row.get("first_qualified_depth_cm_low") != row.get("first_qualified_depth_cm_high")):
            reasons.append("depth_not_qualified_exact_numeric")
        if (source is None or source.get("observation_at") != row.get("first_recorded_wet_at")
                or source.get("qualified_depth_cm_low") != row.get("first_qualified_depth_cm_low")
                or locations.normalize_barangay_name(source.get("qualified_barangay", ""), "Pasig") != name):
            reasons.append("first_depth_snapshot_does_not_match_reference")
        observation = None
        try:
            first, last, end = [datetime.fromisoformat(row[k]) for k in (
                "first_recorded_wet_at", "last_supported_wet_at", "reported_subsidence_upper_at")]
            if any(t.tzinfo is None or t.utcoffset() is None for t in (first, last, end)) or not first <= last < end:
                raise ValueError("clock order")
            lower, upper = float(row["experimental_lower_minutes"]), float(row["experimental_upper_minutes"])
            if (not math.isclose(lower, (last-first).total_seconds()/60, abs_tol=1e-7)
                    or not math.isclose(upper, (end-first).total_seconds()/60, abs_tol=1e-7)):
                raise ValueError("duration clocks")
            observation = CrossLocationObservation(row["label_id"], name or "unknown",
                row["shared_outcome_group"], row["reporting_episode_id"],
                float(row["first_qualified_depth_cm_low"]), lower, upper)
        except (ValueError, TypeError, KeyError, OverflowError):
            reasons.append("invalid_depth_duration_or_episode")
        if not reasons and observation is not None:
            qualified.append(observation)
        register.append({"label_id": row.get("label_id"), "location": name,
                         "status": "rejected" if reasons else "conditional_research_only",
                         "rejection_reasons": "|".join(reasons), "production_training_admitted": False,
                         "qualification_blockers": "|".join(BLOCKERS),
                         "first_recorded_wet_at": row.get("first_recorded_wet_at"),
                         "reference_evidence_available_at": row.get("reference_evidence_available_at"),
                         "shared_outcome_group": row.get("shared_outcome_group"),
                         "episode": row.get("reporting_episode_id"),
                         "first_source_url": row.get("first_source_url")})
    return qualified, register


def split_fold(rows: list[CrossLocationObservation], mode: str, identity: str) -> tuple[list[CrossLocationObservation], list[CrossLocationObservation]]:
    held = [r for r in rows if (r.location if mode == "location" else r.outcome_group) == identity]
    groups = {r.outcome_group for r in held}
    episodes = {r.episode for r in held}
    train = [r for r in rows if r.outcome_group not in groups and r.episode not in episodes
             and (mode != "location" or r.location != identity)]
    if mode == "forward":
        # Episodes in the qualified snapshot encode chronological reporting IDs;
        # use supported endpoint clocks supplied by the caller in evaluate().
        raise ValueError("Forward folds need explicit outcome clocks.")
    return train, held


def evaluate_fold(train: list[CrossLocationObservation], held: list[CrossLocationObservation],
                  mode: str, identity: str) -> list[dict[str, Any]]:
    counts = Counter(r.outcome_group for r in train)
    observations = [DurationObservation(r.lower_minutes, r.upper_minutes, 1/counts[r.outcome_group]) for r in train]
    entries = []
    names = ["intercept_lognormal", "intercept_exponential"] + [f"cross_location_tau_{tau:g}" for tau in PRIORS]
    for name in names:
        entry = {"mode": mode, "held_identity": identity, "model": name,
                 "training_outcomes": sorted(counts), "training_episodes": sorted({r.episode for r in train}),
                 "held_rows": len(held), "held_outcomes": sorted({r.outcome_group for r in held}),
                 "held_episodes": sorted({r.episode for r in held}), "state": "unsupported"}
        try:
            if len(counts) < 2:
                raise ModelNotIdentifiableError("Fewer than two independent outcome-summary identities remain after purging.")
            if name == "intercept_lognormal":
                model = fit_lognormal_aft(observations, lineage={})
                scores = [interval_log_likelihood(r.lower_minutes, r.upper_minutes, model.coefficients[0], model.scale) for r in held]
            elif name == "intercept_exponential":
                mean = fit_exponential(observations)
                scores = [exponential_log_likelihood(r.lower_minutes, r.upper_minutes, mean) for r in held]
            else:
                tau = float(name.rsplit("_", 1)[1])
                candidate = fit_cross_location(train, location_prior_sd=tau)
                scores = []
                for r in held:
                    p = prediction_parameters(candidate, r.depth_cm, r.location)
                    scores.append(interval_log_likelihood(r.lower_minutes, r.upper_minutes,
                                                         p["log_duration_location"], p["predictive_log_scale"]))
                entry["training_depth_mean"] = candidate.depth_mean
                entry["training_depth_support"] = [candidate.depth_min, candidate.depth_max]
            by_group = {g: [s for r, s in zip(held, scores) if r.outcome_group == g]
                        for g in {r.outcome_group for r in held}}
            nll = -sum(sum(s)/len(s) for s in by_group.values())/len(by_group)
            if not math.isfinite(nll):
                raise DurationModelError("Nonfinite held-out likelihood.")
            entry.update(state="evaluated", group_equal_interval_nll=nll)
        except (DurationModelError, ValueError) as exc:
            entry["reason"] = str(exc)
        entries.append(entry)
    return entries


def evaluate(output: Path) -> dict[str, Any]:
    output = output.resolve()
    # Keep every research input immutable, including when callers specify output.
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new or empty output directory; recorded evaluations are immutable.")
    reviewed = json.loads(COMPARISON.read_text(encoding="utf-8"))
    input_hashes = reviewed["input_sha256"]
    for name, expected in input_hashes.items():
        if digest(ROOT/name) != expected:
            raise ValueError(f"Reviewed input checksum differs: {name}")
    manifest = json.loads((WET/"dataset_manifest.json").read_text(encoding="utf-8"))
    for source in manifest["verified_sources"].values():
        for capture in source["artifacts"].values():
            if digest(ROOT/capture["path"]) != capture["sha256"]:
                raise ValueError("Retained source capture checksum differs.")
    raw = read_csv(CANDIDATES)
    rows, register = qualify_rows(raw, read_csv(WET/"pasig_wet_observations.csv"))
    output.mkdir(parents=True, exist_ok=True)
    write_rows(output/"qualification.csv", register)
    write_rows(output/"conditional_candidates.csv", [asdict(row) for row in rows])
    artifacts = {}
    for tau in PRIORS:
        model = fit_cross_location(rows, location_prior_sd=tau, lineage={
            "input_sha256": input_hashes, "limitations": BLOCKERS,
            "reference_age_support_max_minutes": max(r.upper_minutes for r in rows),
            "reference_policy": "first_recorded_wet_in_outcome_selected_candidate_timeline"})
        name = f"candidate_tau_{tau:g}.json"
        (output/name).write_text(json.dumps(model.to_dict(), indent=2, allow_nan=False)+"\n", encoding="utf-8")
        artifacts[str(tau)] = {"filename": name, "sha256": digest(output/name)}
    folds = []
    for mode, identities in (("summary", {r.outcome_group for r in rows}), ("location", {r.location for r in rows})):
        for identity in sorted(identities):
            train, held = split_fold(rows, mode, identity)
            folds.extend(evaluate_fold(train, held, mode, identity))
    # Forward evaluation uses the reviewed outcome clocks, never future records.
    clocks = {r["shared_outcome_group"]: datetime.fromisoformat(r["reported_subsidence_upper_at"]) for r in raw}
    for group in sorted(clocks, key=clocks.get):
        held = [r for r in rows if r.outcome_group == group]
        episodes = {r.episode for r in held}
        train = [r for r in rows if clocks[r.outcome_group] < clocks[group] and r.episode not in episodes]
        folds.extend(evaluate_fold(train, held, "forward", group))
    failures = sum(f["state"] != "evaluated" for f in folds)
    report = {"schema_version": "pasig-cross-location-evaluation-v1", "qualified_rows": len(rows),
              "rejected_rows": len(raw)-len(rows), "shared_outcomes": len({r.outcome_group for r in rows}),
              "verified_independent_storms": 0, "production_training_admitted": 0,
              "prior_scales": list(PRIORS), "folds": folds, "unsupported_model_folds": failures,
              "selected_for_primary": False, "deployment_eligible": False,
              "selection_blockers": BLOCKERS, "artifacts": artifacts,
              "default_comparison_prior": .35, "default_prior_policy": "predeclared_not_holdout_selected",
              "input_sha256": input_hashes, "evaluator_sha256": digest(Path(__file__)),
              "kernel_sha256": digest(ROOT/"backend/app/services/cross_location_duration_model.py"),
              "runtime_baselines_modified": False,
              "sparse_history_and_prospective_calibration_established": False}
    for name, expected in input_hashes.items():
        if digest(ROOT/name) != expected:
            raise ValueError("A source input or runtime baseline changed during evaluation.")
    (output/"evaluation.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    result = evaluate(parser.parse_args().output)
    print(json.dumps({k: result[k] for k in ("qualified_rows", "rejected_rows", "shared_outcomes",
          "unsupported_model_folds", "selected_for_primary", "selection_blockers")}, indent=2))
