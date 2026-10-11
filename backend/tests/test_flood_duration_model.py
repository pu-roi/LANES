"""Numerical correctness tests; synthetic cases never establish field accuracy."""
import math

import numpy as np
import pytest
from scipy.stats import expon, lognorm, norm

from app.services.flood_duration_model import (
    DurationModelArtifact, DurationModelError, DurationObservation,
    ModelNotIdentifiableError, fit_lognormal_aft, interval_log_likelihood,
    predict_duration_distribution,
)
from scripts.evaluate_pasig_duration import exponential_log_likelihood, fit_exponential


def artifact(mu=math.log(120), sigma=.6):
    return DurationModelArtifact((), (), (), (), (mu,), sigma, {}, {})


@pytest.mark.parametrize("lower,upper", [(120, 120), (0, 120), (120, None), (60, 180), (1, 5), (500, 800)])
def test_log_likelihood_matches_independent_distribution(lower, upper):
    distribution = lognorm(s=.6, scale=120)
    expected = (distribution.logpdf(lower) if lower == upper else distribution.logsf(lower)
        if upper is None else distribution.logcdf(upper) if lower == 0 else
        math.log(distribution.cdf(upper) - distribution.cdf(lower)))
    assert interval_log_likelihood(lower, upper, math.log(120), .6) == pytest.approx(expected, abs=1e-10)


def test_far_tail_interval_retains_nonzero_probability():
    assert norm.cdf(10.01) - norm.cdf(10) == 0
    expected = math.log(norm.sf(10) - norm.sf(10.01))
    assert interval_log_likelihood(math.exp(10), math.exp(10.01), 0, 1) == pytest.approx(expected)


@pytest.mark.parametrize("lower,upper,weight", [(-1, 4, 1), (0, None, 1), (5, 4, 1), (0, 0, 1),
    (1, 2, 0), (True, 2, 1), (1, float('inf'), 1), (1, 2, float('nan'))])
def test_invalid_observations_are_rejected(lower, upper, weight):
    with pytest.raises(DurationModelError):
        DurationObservation(lower, upper, weight)


@pytest.mark.parametrize("age", [0, 60, 240, 1000])
def test_conditioned_quantiles_and_horizons_match_survival_ratio(age):
    model = artifact()
    distribution = lognorm(s=model.scale, scale=math.exp(model.coefficients[0]))
    result = predict_duration_distribution(model, {}, elapsed_minutes=age,
        continuously_wet_confirmed=age > 0, horizons_minutes=(0, 60, 120, 240))
    for row in result['quantiles']:
        probability = 1 - distribution.sf(age + row['remaining_minutes']) / distribution.sf(age)
        assert probability == pytest.approx(row['quantile'], abs=1e-10)
        assert row['remaining_minutes'] > 0
    for row in result['horizon_probabilities']:
        assert row['probability_reported_subsidence'] == pytest.approx(
            1 - distribution.sf(age + row['horizon_minutes']) / distribution.sf(age), abs=1e-10)
    assert result['shadow_only'] is True
    assert result['physical_dry_or_passability_established'] is False


def test_elapsed_time_requires_continuity_and_is_not_unconditional_subtraction():
    model = artifact()
    with pytest.raises(DurationModelError):
        predict_duration_distribution(model, {}, elapsed_minutes=240)
    result = predict_duration_distribution(model, {}, elapsed_minutes=240, continuously_wet_confirmed=True)
    assert result['quantiles'][1]['remaining_minutes'] > 0  # unconditional median - age is negative


@pytest.mark.parametrize("change", [{"quantiles": [0]}, {"quantiles": [1]}, {"quantiles": [True]},
    {"horizons_minutes": [-1]}, {"horizons_minutes": [float('nan')]}, {"elapsed_minutes": -1}])
def test_invalid_prediction_arguments(change):
    with pytest.raises(DurationModelError):
        predict_duration_distribution(artifact(), {}, **change)


def test_exact_synthetic_fit_matches_known_mle_and_roundtrips():
    values = np.exp(np.array([4, 4.3, 4.5, 4.9, 5.2, 5.6, 6, 6.4]))
    model = fit_lognormal_aft([DurationObservation(value, value, 1) for value in values], lineage={'synthetic_test': True})
    assert model.coefficients[0] == pytest.approx(float(np.log(values).mean()), abs=1e-5)
    assert model.scale == pytest.approx(float(np.log(values).std()), abs=1e-5)
    assert DurationModelArtifact.from_dict(model.to_dict()).to_dict() == model.to_dict()
    assert model.fit_diagnostics['predictive_validation_established'] is False


@pytest.mark.parametrize("rows", [
    [DurationObservation(0, upper, 1) for upper in (10, 50, 100)],
    [DurationObservation(lower, None, 1) for lower in (10, 50, 100)],
    [DurationObservation(10, 20, 1, {'depth': 2}) for _ in range(4)],
])
def test_unidentifiable_evidence_is_rejected(rows):
    with pytest.raises(ModelNotIdentifiableError):
        fit_lognormal_aft(rows, tuple(rows[0].features), lineage={})


@pytest.mark.parametrize("change", [{'shadow_only': False}, {'scale': 0}, {'scale': float('nan')},
    {'surprise': 1}, {'coefficients': []}, {'schema_version': 'unknown'}])
def test_invalid_artifacts_cannot_be_loaded(change):
    with pytest.raises(DurationModelError):
        DurationModelArtifact.from_dict({**artifact().to_dict(), **change})


def test_feature_scaler_uses_training_values_and_requires_exact_prediction_features():
    model = DurationModelArtifact(('depth',), (10,), (2,), (), (math.log(120), .5), .6, {}, {})
    assert predict_duration_distribution(model, {'depth': 12})['quantiles'][1]['total_minutes'] == pytest.approx(120 * math.exp(.5))
    for features in ({}, {'depth': None}, {'depth': 12, 'extra': 1}):
        with pytest.raises(DurationModelError):
            predict_duration_distribution(model, features)


def test_feature_fit_learns_effect_and_retains_training_only_scaler():
    depths = np.array([2., 4., 6., 8., 10., 12., 14., 16.])
    rows = [DurationObservation(math.exp(4 + .1 * depth + residual),
        math.exp(4 + .1 * depth + residual), 1, {'depth': depth})
        for depth in depths for residual in (-.2, .2)]
    model = fit_lognormal_aft(rows, ['depth'], lineage={'synthetic_test': True})
    assert model.feature_means == pytest.approx((float(depths.mean()),))
    assert model.feature_scales == pytest.approx((float(depths.std()),))
    assert model.coefficients[1] / model.feature_scales[0] == pytest.approx(.1, abs=1e-5)
    assert model.scale == pytest.approx(.2, abs=1e-5)
    assert predict_duration_distribution(model, {'depth': 18})['quantiles'][1]['total_minutes'] == pytest.approx(math.exp(5.8), rel=1e-5)


def test_collinear_features_are_rejected():
    rows = [DurationObservation(value, value, 1, {'a': value, 'b': 2 * value}) for value in (10, 30, 60, 100, 160)]
    with pytest.raises(ModelNotIdentifiableError, match='rank deficient'):
        fit_lognormal_aft(rows, ['a', 'b'], lineage={})


@pytest.mark.parametrize("lower,upper", [(60, 60), (0, 60), (60, None), (60, 180)])
def test_exponential_comparator_matches_independent_distribution(lower, upper):
    distribution = expon(scale=120)
    expected = (distribution.logpdf(lower) if lower == upper else distribution.logsf(lower)
        if upper is None else math.log(distribution.cdf(upper) - distribution.cdf(lower)))
    assert exponential_log_likelihood(lower, upper, 120) == pytest.approx(expected)


def test_exponential_exact_fit_has_sample_mean():
    rows = [DurationObservation(value, value, 1) for value in (10, 40, 70, 120)]
    assert fit_exponential(rows) == pytest.approx(60, rel=1e-6)


def test_shared_summary_weights_sum_to_one_per_summary():
    from scripts.train_pasig_duration import grouped_observations
    rows = [{'shared_outcome_group': group, 'experimental_lower_minutes': 10,
             'experimental_upper_minutes': 20, 'label_id': str(index)}
            for index, group in enumerate(('a', 'a', 'a', 'b'))]
    observations = grouped_observations(rows)
    assert sum(row.weight for row in observations[:3]) == pytest.approx(1)
    assert observations[3].weight == 1
