"""Synthetic mathematics and real evidence checks; neither proves field accuracy."""
from dataclasses import replace
import json
import math

import numpy as np
import pytest
from scipy.stats import lognorm

from app.services.cross_location_duration_model import (
    CrossLocationArtifact, CrossLocationObservation, fit_cross_location,
    predict_cross_location, prediction_parameters,
)
from app.services.flood_duration_model import DurationModelError, ModelNotIdentifiableError
from scripts.evaluate_cross_location_duration import (
    CANDIDATES, WET, evaluate, qualify_rows, split_fold,
)
from scripts.qualify_pasig_duration_data import read_csv


@pytest.fixture(scope="module")
def rows():
    result = []
    for location, offset in (("Maybunga", -.1), ("Santolan", .1)):
        for i in range(12):
            depth = (10, 30, 60)[i % 3]
            duration = math.exp(4 + .015*depth + offset + (-.15, .10, .05, -.08)[i % 4])
            result.append(CrossLocationObservation(f"{location}-{i}", location, f"event-{location}-{i}",
                f"episode-{location}-{i}", depth, duration, duration))
    return result


@pytest.fixture(scope="module")
def model(rows):
    return fit_cross_location(rows)


def test_shared_depth_effect_transfers_to_location_without_history(model):
    low = predict_cross_location(model, 10, "Ugong")
    high = predict_cross_location(model, 60, "Ugong")
    assert high["quantiles"][1]["remaining_minutes"] > low["quantiles"][1]["remaining_minutes"]
    assert high["local_effect"] == 0 and high["location_outcomes"] == 0
    assert high["unseen_location_variance"] == pytest.approx(.35**2)
    assert high["transfer_basis"] == "shared_depth_with_unseen_location_prior"
    assert not high["selected_for_primary"]


def test_smaller_location_prior_shrinks_local_offsets(rows,model):
    tight = fit_cross_location(rows, location_prior_sd=.02)
    assert np.linalg.norm(tight.coefficients[2:]) < np.linalg.norm(model.coefficients[2:])


def test_duplicate_shared_outcome_projections_do_not_add_weight(rows,model):
    duplicated = [replace(row, observation_id=row.observation_id+suffix) for row in rows for suffix in ("a","b")]
    duplicate_fit = fit_cross_location(duplicated)
    assert duplicate_fit.coefficients == pytest.approx(model.coefficients, abs=2e-5)
    assert duplicate_fit.depth_mean == pytest.approx(model.depth_mean)
    assert np.asarray(duplicate_fit.coefficient_covariance) == pytest.approx(np.asarray(model.coefficient_covariance), abs=2e-4)


def test_conditional_quantiles_match_independent_survival_calculation(model):
    p = prediction_parameters(model, 30, "Ugong")
    distribution = lognorm(s=p["predictive_log_scale"], scale=math.exp(p["log_duration_location"]))
    result = predict_cross_location(model, 30, "Ugong", elapsed_minutes=75, continuously_wet_confirmed=True)
    for row in result["quantiles"]:
        assert 1-distribution.sf(75+row["remaining_minutes"])/distribution.sf(75) == pytest.approx(row["quantile"],abs=1e-10)
    with pytest.raises(DurationModelError):
        predict_cross_location(model,30,"Ugong",elapsed_minutes=75)


def test_artifact_roundtrip_and_invalid_covariance(model):
    artifact = CrossLocationArtifact.from_dict(json.loads(json.dumps(model.to_dict())))
    assert prediction_parameters(artifact, 30,"Ugong") == prediction_parameters(model,30,"Ugong")
    invalid = model.to_dict()
    invalid["coefficient_covariance"] = [[1]]
    with pytest.raises(DurationModelError):
        CrossLocationArtifact.from_dict(invalid)
    invalid = model.to_dict(); invalid["shadow_only"] = False
    with pytest.raises(DurationModelError):
        CrossLocationArtifact.from_dict(invalid)


@pytest.mark.parametrize("depth", [True, -1, 0, float("nan"), 9, 61])
def test_missing_or_out_of_support_depth_cannot_be_substituted(model, depth):
    with pytest.raises(DurationModelError):
        prediction_parameters(model,depth,"Ugong")


def test_one_outcome_group_cannot_be_rescued_with_a_prior(rows):
    with pytest.raises(ModelNotIdentifiableError):
        fit_cross_location([replace(r,outcome_group="shared") for r in rows])


def test_censored_outcomes_fit_without_invented_endpoints(rows):
    censored = [replace(row, lower_minutes=0 if i%4==0 else row.lower_minutes,
        upper_minutes=None if i%4==1 else row.upper_minutes*1.2 if i%4==2 else row.upper_minutes)
        for i,row in enumerate(rows)]
    fitted=fit_cross_location(censored)
    assert math.isfinite(fitted.residual_scale) and fitted.lineage["production_training_admitted"]==0


def test_real_qualification_keeps_conditional_blockers_and_canonical_names():
    raw = read_csv(CANDIDATES)
    qualified, register = qualify_rows(raw,read_csv(WET/"pasig_wet_observations.csv"))
    assert len(qualified)==36 and sum(r["status"]=="rejected" for r in register)==1
    assert "Santa Lucia" in {r.location for r in qualified}
    assert all(not r["production_training_admitted"] for r in register)
    assert all("historical_predictor_availability_unverified" in r["qualification_blockers"] for r in register)
    for location in {r.location for r in qualified}:
        train,held=split_fold(qualified,"location",location)
        assert not {r.outcome_group for r in train}&{r.outcome_group for r in held}
        assert not {r.episode for r in train}&{r.episode for r in held}
        assert all(r.location!=location for r in train)


def test_bad_clocks_duplicate_labels_and_reference_depth_are_excluded():
    raw=read_csv(CANDIDATES); wet=read_csv(WET/"pasig_wet_observations.csv")
    bad=raw[0].copy(); bad["experimental_upper_minutes"]="1"
    rows,register=qualify_rows([bad],wet)
    assert not rows and register[0]["status"]=="rejected"
    rows,register=qualify_rows([raw[0],raw[0]],wet)
    assert not rows and all("duplicate_label_identity" in r["rejection_reasons"] for r in register)


def test_real_evaluator_reports_purged_failures_without_runtime_promotion(tmp_path):
    report=evaluate(tmp_path)
    assert report["qualified_rows"]==36 and report["shared_outcomes"]==3
    assert report["unsupported_model_folds"]>0
    assert not report["selected_for_primary"] and not report["runtime_baselines_modified"]
    for fold in report["folds"]:
        assert not set(fold["training_outcomes"])&set(fold["held_outcomes"])
        assert not set(fold["training_episodes"])&set(fold["held_episodes"])
    with pytest.raises(ValueError,match="new or empty"):
        evaluate(tmp_path)
