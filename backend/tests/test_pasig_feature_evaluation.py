"""Whole-group evaluation and source ambiguity cannot be bridged or imputed."""
from scripts.evaluate_pasig_feature_models import depth_pairs, evaluate, OUTPUT


def row(clock,depth,id):
    return dict(observation_id=id,observation_at=clock,depth_qualification="usable_reported_numeric",
        qualified_depth_cm_low=str(depth),qualified_depth_cm_high=str(depth),candidate_timeline_id="same",
        candidate_reporting_episode="episode",qualified_barangay="Maybunga")


def test_conflicting_same_clock_breaks_adjacent_trajectory_instead_of_bridging():
    result=depth_pairs([row("2026-01-01T01:00:00+08:00",20,"a"),row("2026-01-01T02:00:00+08:00",10,"b"),
        row("2026-01-01T02:00:00+08:00",30,"c"),row("2026-01-01T03:00:00+08:00",5,"d")])
    assert result==[]


def test_depth_change_is_not_an_observed_dry_outcome():
    result=depth_pairs([row("2026-01-01T01:00:00+08:00",20,"a"),row("2026-01-01T02:00:00+08:00",10,"b")])
    assert len(result)==1 and result[0]["next_depth_cm"]==10 and not result[0]["physical_dry_outcome"]


def test_source_models_evaluate_real_groups_and_leave_runtime_baselines_unchanged(tmp_path):
    result=evaluate(tmp_path)
    assert result["qualified_aft_rows"]==36 and result["trajectory_pairs"]==251
    assert result["trajectory_episodes"]==3 and result["trajectory_directions"]["falling"]==13
    assert any(row["state"]=="unidentifiable" for row in result["aft_summary_holdouts"])
    for fold in result["trajectory_holdouts"]:
        assert fold["held_episode"] not in fold["training_episodes"]
        assert fold["depth_location_ridge_mae_cm"]>fold["persistence_baseline_mae_cm"]
    assert not result["observed_dry_labels_generated"] and not result["runtime_models_modified"]
    assert not result["depth_feature_model_selected"] and not result["trajectory_model_selected"]
