"""Audit retained evidence coverage without rewriting inputs or fitting a model.

Run from the repository root: python backend/scripts/audit_pasig_barangay_coverage.py
CSV outputs are analysis views, not newly admitted training observations.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from clean_pasig_flood_history import barangay_key, load_barangay_reference

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/evaluations/pasig-barangay-coverage-20261008"
FOLLOWUP = ROOT / "docs/evaluations/pasig-duration-followup-20261005"
OVERLAY = ROOT / "docs/evaluations/pasig-clearance-followup-20261007"
MODEL = ROOT / "docs/evaluations/pasig-duration-model-20261007"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build() -> dict:
    inputs: dict[str, str] = {}

    def retain(path: Path, expected: str | None = None) -> None:
        actual = digest(path)
        if expected is not None and actual != expected:
            raise ValueError(f"Evidence hash mismatch: {path.relative_to(ROOT)}")
        inputs[path.relative_to(ROOT).as_posix()] = actual

    # Existing manifest-bound exports/captures remain unchanged.
    ancestor = read_json(FOLLOWUP / "dataset_manifest.json")
    overlay_manifest = read_json(OVERLAY / "dataset_manifest.json")
    for directory, manifest in ((FOLLOWUP, ancestor), (OVERLAY, overlay_manifest)):
        retain(directory / "dataset_manifest.json")
        for name, expected in manifest["output_sha256"].items():
            retain(directory / name, expected)
    capture_paths: set[str] = set()
    for source in ancestor["verified_sources"].values():
        for artifact in source["artifacts"].values():
            retain(ROOT / artifact["path"], artifact["sha256"])
            capture_paths.add(artifact["path"])
    sources = read_json(OVERLAY / "source_register.json")
    for source in sources.values():
        for kind in ("html", "text"):
            path = source[f"{kind}_path"]
            retain(ROOT / path, source[f"{kind}_sha256"])
            capture_paths.add(path)

    reference_path = ROOT / "data/pasig_barangay_reference.csv"
    annual_path = ROOT / "data/flooded_areas_pasig_clean.csv"
    model_path = ROOT / "backend/runtime_data/flood-duration/conditional_aft.json"
    boundary_path = ROOT / "backend/runtime_data/barangay/boundaries.json"
    location_path = ROOT / "backend/runtime_data/flood-location/boundaries.json"
    for path in (reference_path, annual_path, model_path, boundary_path,
                 MODEL / "conditional_training_candidates.csv", MODEL / "experiment_report.json"):
        retain(path)
    experiment = read_json(MODEL / "experiment_report.json")
    if digest(model_path) != experiment["model_sha256"]:
        raise ValueError("Runtime model differs from the retained research experiment")
    for name, expected in experiment["input_sha256"].items():
        retain(ROOT / name, expected)

    reference = load_barangay_reference(reference_path)

    def canonical(value: str) -> str | None:
        if not value.strip():
            return None
        match = reference.get(barangay_key(value))
        if match is None:
            raise ValueError(f"Unknown barangay label requires review: {value!r}")
        return match.name

    layers = {
        "annual": (annual_path, "barangay_canonical"),
        "wet": (FOLLOWUP / "pasig_wet_observations.csv", "qualified_barangay"),
        "overlay_wet": (OVERLAY / "observations.csv", "barangay"),
        "conditional_duration": (MODEL / "conditional_training_candidates.csv", "barangay"),
        "passability": (OVERLAY / "passability_followup_pairs.csv", "barangay"),
    }
    counts, rows_by_layer, aliases = {}, {}, defaultdict(set)
    unknown_counts = {}
    for layer, (path, column) in layers.items():
        rows = read_rows(path)
        if layer == "overlay_wet":
            rows = [row for row in rows if row["status"] == "flood_observed"]
        rows_by_layer[layer] = rows
        counts[layer] = Counter()
        unknown_counts[layer] = 0
        for row in rows:
            name = canonical(row[column])
            if name is None:
                unknown_counts[layer] += 1
            else:
                counts[layer][name] += 1
                aliases[name].add(row[column])
    boundaries = {canonical(row["barangay"]) for row in read_json(boundary_path)["records"]
                  if row["city"] in {"Pasig", "City of Pasig", "Pasig City"}}
    prediction_locations: set[str] = set()
    if location_path.exists():
        location_manifest=location_path.parent/"manifest.json"
        retain(location_manifest)
        retain(location_path,read_json(location_manifest)["catalog_sha256"])
        prediction_locations={canonical(row["barangay"]) for row in read_json(location_path)["records"]}
    model = read_json(model_path)
    model_barangays = {canonical(name) for name in model["lineage"]["supported_barangays"]}
    transport_path = ROOT / "backend/runtime_data/flood-duration/passability_aft.json"
    transport_barangays: set[str] = set()
    if transport_path.exists():
        experiment_path = ROOT / "docs/evaluations/pasig-passability-model-20261008/experiment_report.json"
        retain(experiment_path)
        retain(transport_path, read_json(experiment_path)["model_sha256"])
        transport_barangays = {canonical(name) for name in read_json(transport_path)["lineage"]["supported_barangays"]}
    groups = defaultdict(set)
    for row in rows_by_layer["conditional_duration"]:
        groups[canonical(row["barangay"])].add(row["shared_outcome_group"])
    coverage = []
    for place in sorted(reference.values(), key=lambda item: item.name):
        name = place.name
        coverage.append({"barangay": name, "psgc_code": place.psgc_10_digit_code,
            "annual_location_depth_rows": counts["annual"][name],
            "main_wet_observation_rows": counts["wet"][name],
            "overlay_wet_observation_rows": counts["overlay_wet"][name],
            "conditional_duration_projections": counts["conditional_duration"][name],
            "shared_subsidence_summary_groups": len(groups[name]),
            "passability_projections_separate_target": counts["passability"][name],
            "boundary_catalog_present": name in boundaries,
            "prediction_location_catalog_present": name in prediction_locations,
            "current_research_model_cohort": name in model_barangays,
            "passability_research_model_cohort": name in transport_barangays,
            "pooled_pasig_experimental_prediction_identity": True,
            "production_training_admitted": False,
            "retained_label_spellings": " | ".join(sorted(aliases[name]))})

    ugong = []
    overlay_observations = {row["observation_id"]: row for row in read_rows(OVERLAY / "observations.csv")}
    for layer, (path, column) in layers.items():
        for row in rows_by_layer[layer]:
            if canonical(row[column]) != "Ugong":
                continue
            evidence = overlay_observations[row["reference_observation_id"]] if layer == "passability" else row
            outcome = overlay_observations.get(row.get("outcome_observation_id"), {})
            ugong.append({"evidence_layer": layer,
                "record_id": row.get("observation_id", row.get("pair_id", f"{row.get('source_year', '')}:{row.get('source_record_no', '')}")),
                "barangay": "Ugong", "location": row.get("location_raw", " ".join(filter(None, (row.get("street_raw"), row.get("landmark_raw"))))),
                "wet_observed_at": row.get("observation_at", row.get("reference_at", "")),
                "source_year": row.get("source_year", ""),
                "passable_upper_at_separate_target": row.get("reported_passability_upper_at", ""),
                "reported_subsidence_at": "", "duration_training_admitted": False,
                "source_dataset": path.relative_to(ROOT).as_posix(),
                "source_capture": evidence.get("source_capture_path", evidence.get("capture_path", "")),
                "source_url": evidence.get("source_url", ""),
                "source_line": evidence.get("source_line_start", evidence.get("evidence_lines", "")),
                "passability_outcome_record_id": row.get("outcome_observation_id", ""),
                "passability_outcome_capture": outcome.get("capture_path", ""),
                "passability_outcome_source_url": outcome.get("source_url", ""),
                "qualification_note": row.get("exclusion_reason", row.get("duration_label_status", "Annual location/depth context; no observation or outcome clock."))})

    report = {"audit_version": "pasig-barangay-coverage-v1", "audit_date": "2026-10-08",
        "counts": {"reference_barangays": len(reference),
            "annual_barangays": len(counts["annual"]), "main_wet_barangays": len(counts["wet"]),
            "combined_annual_and_main_wet_barangays": len(set(counts["annual"]) | set(counts["wet"])),
            "overlay_wet_barangays": len(counts["overlay_wet"]),
            "combined_main_and_overlay_wet_barangays": len(set(counts["wet"]) | set(counts["overlay_wet"])),
            "main_wet_rows_without_observation_clock": sum(not row["observation_at"] for row in rows_by_layer["wet"]),
            "model_cohort_barangays": len(model_barangays), "boundary_catalog_barangays": len(boundaries),
            "prediction_location_barangays":len(prediction_locations),
            "passability_model_cohort_barangays": len(transport_barangays),
            "pooled_experimental_prediction_barangays": len(reference),
            "conditional_projections": sum(counts["conditional_duration"].values()),
            "shared_subsidence_summary_groups": len(set().union(*groups.values())),
            "verified_source_capture_artifacts": len(capture_paths), "ugong_evidence_view_rows": len(ugong)},
        "unresolved_barangay_rows": unknown_counts,
        "all_counts_are_records_not_independent_events": True,
        "normalization_policy": "Existing annual-cleaner PSGC key: whitespace/case/Sta./Sto. aliases; no road inference or raw-label rewrite.",
        "missing_boundary_catalog_barangays": sorted({r.name for r in reference.values()} - boundaries),
        "missing_prediction_location_barangays":sorted({r.name for r in reference.values()} - prediction_locations),
        "model_sha256": digest(model_path), "input_sha256": dict(sorted(inputs.items())),
        "builder_sha256": digest(Path(__file__)), "model_retrained": False,
        "runtime_or_database_modified": False, "source_or_training_admission_modified": False}
    if any(digest(ROOT / path) != expected for path, expected in inputs.items()):
        raise ValueError("An input changed during coverage analysis")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_rows(OUTPUT / "barangay_coverage.csv", coverage)
    write_rows(OUTPUT / "ugong_evidence.csv", ugong)
    report["output_sha256"] = {name: digest(OUTPUT / name) for name in ("barangay_coverage.csv", "ugong_evidence.csv")}
    (OUTPUT / "coverage_audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(build()["counts"], sort_keys=True))
