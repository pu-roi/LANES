"""Source/group-aware feature comparisons; do not promote failed candidates.

Run from backend: python -m scripts.evaluate_pasig_feature_models
No runtime artifact, source label, database or operational policy is changed.
"""
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from app.services.flood_duration_model import DurationObservation, ModelNotIdentifiableError, fit_lognormal_aft, interval_log_likelihood
from scripts.clean_pasig_flood_history import barangay_key, load_barangay_reference
from scripts.qualify_pasig_duration_data import ROOT, digest, read_csv

OUTPUT = ROOT/"docs/evaluations/pasig-location-feature-models-20261008"
WET = ROOT/"docs/evaluations/pasig-duration-followup-20261005"
MODEL = ROOT/"docs/evaluations/pasig-duration-model-20261007"


def depth_pairs(rows: list[dict]) -> list[dict]:
    reference=load_barangay_reference(ROOT/"data/pasig_barangay_reference.csv")
    by_timeline=defaultdict(list)
    for row in rows:
        if (row["depth_qualification"]=="usable_reported_numeric" and row["observation_at"]
                and row["candidate_timeline_id"] and row["qualified_depth_cm_low"]
                and row["qualified_depth_cm_low"]==row["qualified_depth_cm_high"]):
            by_timeline[row["candidate_timeline_id"]].append(row)
    pairs=[]
    for timeline, items in by_timeline.items():
        by_clock=defaultdict(list)
        for row in items:by_clock[row["observation_at"]].append(row)
        ordered=[]
        for clock, observations in sorted(by_clock.items()):
            # Conflicting same-clock reports break adjacency; do not bridge them.
            if len({row["qualified_depth_cm_low"] for row in observations})>1:
                ordered.append(None)
            else:ordered.append(min(observations,key=lambda row:row["observation_id"]))
        for first,last in zip(ordered,ordered[1:]):
            if first is None or last is None:continue
            hours=(datetime.fromisoformat(last["observation_at"])-datetime.fromisoformat(first["observation_at"])).total_seconds()/3600
            if not 0<hours<=6 or first["qualified_barangay"]!=last["qualified_barangay"]:continue
            if first["candidate_reporting_episode"] != last["candidate_reporting_episode"]:continue
            name=reference.get(barangay_key(first["qualified_barangay"]))
            if name is None:continue
            pairs.append(dict(first_id=first["observation_id"],next_id=last["observation_id"],
                timeline=timeline,reporting_episode=first["candidate_reporting_episode"],barangay=name.name,
                first_at=first["observation_at"],next_at=last["observation_at"],
                first_depth_cm=float(first["qualified_depth_cm_low"]),
                next_depth_cm=float(last["qualified_depth_cm_low"]),elapsed_hours=hours,
                physical_dry_outcome=False,production_training_admitted=False))
    return pairs


def aft_fit(rows: list[dict], with_depth: bool):
    groups=Counter(row["shared_outcome_group"] for row in rows)
    evidence=[DurationObservation(float(row["experimental_lower_minutes"]),float(row["experimental_upper_minutes"]),
        1/groups[row["shared_outcome_group"]], observation_id=row["label_id"],
        features={"depth_cm":float(row["first_qualified_depth_cm_low"])} if with_depth else {}) for row in rows]
    return fit_lognormal_aft(evidence,feature_names=("depth_cm",) if with_depth else (),
        target_version=rows[0]["experimental_target_version"],lineage={"experiment":"qualified_first_depth_comparison",
            "deployment_eligible":False,"production_training_admitted":0,"prospective_accuracy_established":False})


def evaluate(output: Path=OUTPUT) -> dict:
    paths=[MODEL/"conditional_training_candidates.csv",MODEL/"experiment_report.json",
        WET/"pasig_wet_observations.csv",WET/"dataset_manifest.json",ROOT/"data/pasig_barangay_reference.csv",
        ROOT/"backend/runtime_data/flood-duration/conditional_aft.json",ROOT/"backend/runtime_data/flood-duration/passability_aft.json"]
    inputs={p.relative_to(ROOT).as_posix():digest(p) for p in paths}
    manifest=json.loads((WET/"dataset_manifest.json").read_text(encoding="utf-8"))
    if digest(WET/"pasig_wet_observations.csv") != manifest["output_sha256"]["pasig_wet_observations.csv"]:
        raise ValueError("Reviewed wet export changed")
    for source in manifest["verified_sources"].values():
        for artifact in source["artifacts"].values():
            if digest(ROOT/artifact["path"]) != artifact["sha256"]:raise ValueError("Retained capture changed")
    rows=read_csv(MODEL/"conditional_training_candidates.csv")
    usable=[r for r in rows if r["first_depth_qualification"]=="usable_reported_numeric"
        and r["first_qualified_depth_cm_low"] and r["first_qualified_depth_cm_low"]==r["first_qualified_depth_cm_high"]]
    output.mkdir(parents=True,exist_ok=True)
    full=aft_fit(usable,True)
    (output/"depth_feature_aft.json").write_text(json.dumps(full.to_dict(),indent=2,sort_keys=True)+"\n",encoding="utf-8")
    folds=[]
    for group in sorted({r["shared_outcome_group"] for r in usable}):
        training=[r for r in usable if r["shared_outcome_group"]!=group]
        held=[r for r in usable if r["shared_outcome_group"]==group]
        for name,features in (("intercept_aft",False),("depth_feature_aft",True)):
            try:
                model=aft_fit(training,features)
                scores=[]
                for row in held:
                    location=model.coefficients[0]
                    if features:location+=model.coefficients[1]*(float(row["first_qualified_depth_cm_low"])-model.feature_means[0])/model.feature_scales[0]
                    scores.append(-interval_log_likelihood(float(row["experimental_lower_minutes"]),float(row["experimental_upper_minutes"]),location,model.scale))
                folds.append(dict(held_summary=group,model=name,state="fitted",mean_interval_nll=float(np.mean(scores)),held_rows=len(held)))
            except ModelNotIdentifiableError as exc:
                folds.append(dict(held_summary=group,model=name,state="unidentifiable",reason=str(exc),held_rows=len(held)))
    pairs=depth_pairs(read_csv(WET/"pasig_wet_observations.csv"))
    x=np.asarray([[p["first_depth_cm"],p["elapsed_hours"],p["barangay"]] for p in pairs],dtype=object)
    y=np.asarray([p["next_depth_cm"] for p in pairs]);groups=np.asarray([p["reporting_episode"] for p in pairs])
    trajectory=[]
    for train,test in LeaveOneGroupOut().split(x,y,groups):
        model=Pipeline([("features",ColumnTransformer([("numeric",StandardScaler(),[0,1]),
            ("location",OneHotEncoder(handle_unknown="ignore"),[2])])),("ridge",Ridge(alpha=10,solver="lsqr"))])
        model.fit(x[train],y[train])
        prediction=model.predict(x[test])
        trajectory.append(dict(held_episode=str(groups[test][0]),training_episodes=sorted(set(groups[train])),
            held_pairs=len(test),depth_location_ridge_mae_cm=float(mean_absolute_error(y[test],prediction)),
            persistence_baseline_mae_cm=float(mean_absolute_error(y[test],x[test,0].astype(float)))))
    with (output/"depth_trajectory_pairs.csv").open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(pairs[0]),lineterminator="\n");writer.writeheader();writer.writerows(pairs)
    report=dict(qualified_aft_rows=len(usable),excluded_unknown_or_uncertain_depth_rows=len(rows)-len(usable),
        aft_features=list(full.feature_names),full_fit_coefficients=list(full.coefficients),aft_summary_holdouts=folds,
        trajectory_pairs=len(pairs),trajectory_episodes=len(set(groups)),trajectory_holdouts=trajectory,
        trajectory_directions=dict(Counter("falling" if p["next_depth_cm"]<p["first_depth_cm"] else "rising" if p["next_depth_cm"]>p["first_depth_cm"] else "unchanged" for p in pairs)),
        depth_feature_model_selected=False,trajectory_model_selected=False,
        selection_reason="Insufficient independent outcomes, an unidentifiable AFT fold and worse held-episode trajectory errors; retain current research baselines.",
        street_drainage_capacity_learned=False,terrain_rainfall_effects_learned=False,
        observed_dry_labels_generated=False,prospective_accuracy_established=False,
        input_sha256=inputs,builder_sha256=digest(Path(__file__)),runtime_models_modified=False)
    if any(digest(ROOT/name)!=expected for name,expected in inputs.items()):raise ValueError("An input/runtime model changed")
    (output/"feature_comparison.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return report


if __name__=="__main__":
    print(json.dumps(evaluate(),indent=2))
