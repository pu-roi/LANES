"""The UI replay launcher cannot bind a shared database or expose future evidence."""
from datetime import datetime
import pytest
from scripts.serve_local_news_replay import simulation_clock, simulation_snapshot, simulation_reads, validate_target


@pytest.mark.parametrize("target", [
    "postgresql+psycopg://example.org/lanes_news_test",
    "postgresql+psycopg://127.0.0.1/lanes",
    "postgresql+psycopg://127.0.0.1/lanes_news_test?host=example.org",
])
def test_replay_server_refuses_shared_targets_before_app_or_database_reads(monkeypatch, target):
    from app.core.config import settings
    monkeypatch.setattr(settings, "DATABASE_URL", target)
    with pytest.raises(ValueError, match="loopback PostgreSQL"):
        validate_target()
    with pytest.raises(ValueError, match="loopback PostgreSQL"):
        simulation_snapshot()
    with pytest.raises(ValueError, match="loopback PostgreSQL"):
        with simulation_reads(datetime.fromisoformat("2026-09-25T04:42:00+08:00")):
            pytest.fail("Shared database must be rejected")


def test_replay_server_clock_is_aware_and_isolated(monkeypatch):
    monkeypatch.setenv("LANES_NEWS_SIMULATION_AT", "2026-09-24T16:59:00+08:00")
    assert simulation_clock() == datetime.fromisoformat("2026-09-24T16:59:00+08:00")
    monkeypatch.setenv("LANES_NEWS_SIMULATION_AT", "2026-09-24T16:59:00")
    with pytest.raises(ValueError, match="timezone offset"):
        simulation_clock()


def test_persisted_zone_reader_and_news_details_share_clock_and_restore(monkeypatch):
    from scripts import serve_local_news_replay as server
    from app import crud
    from app.crud import report
    from app.services import news_publication_read_service as reads, news_zone_projection_service as projection
    from app.services import zone_prediction_service as predictions
    from app.services import spatial_review_service as review
    monkeypatch.setattr(server, "validate_target", lambda: None)
    clock = datetime.fromisoformat("2026-09-25T04:42:00+08:00")
    recorded = []
    def reader(db, *, now=None):
        recorded.append(now)
        return [17]
    monkeypatch.setattr(report, "get_active_avoidance_zones", reader)
    monkeypatch.setattr(report, "get_all_avoidance_zones_filtered", lambda db, **kwargs: kwargs["now"])
    monkeypatch.setattr(predictions, "predict_zone", lambda db, zone_id, user, **kwargs: kwargs["now"])
    original_clock = reads.publication_read_clock
    original_projection_clock = projection.utc_now
    original_crud = crud.get_active_avoidance_zones
    with simulation_reads(clock):
        assert crud.get_active_avoidance_zones(None) == [17]
        assert report.get_active_avoidance_zones(None) == [17]
        assert recorded == [clock, clock]
        assert projection.utc_now() == reads.publication_read_clock() == clock
        assert review.review_clock() == clock
        assert crud.get_all_avoidance_zones_filtered(None, active_only=True) == clock
        assert report.get_all_avoidance_zones_filtered(None, archived=True) == clock
        assert predictions.predict_zone(None, 17, None) == clock
        later = datetime.fromisoformat("2026-09-25T07:00:00+08:00")
        report.get_active_avoidance_zones(None, now=later)
        assert recorded[-1] == later
    assert report.get_active_avoidance_zones is reader
    assert crud.get_active_avoidance_zones is original_crud
    assert reads.publication_read_clock is original_clock
    assert projection.utc_now is original_projection_clock


def test_persisted_reads_refuse_naive_clock(monkeypatch):
    from scripts import serve_local_news_replay as server
    monkeypatch.setattr(server, "validate_target", lambda: None)
    with pytest.raises(ValueError, match="timezone offset"):
        with simulation_reads(datetime(2026, 9, 25)):
            pytest.fail("Naive clock must be rejected")


def test_reconstruction_policy_is_shared_by_pipeline_and_staff_and_restored(monkeypatch):
    from scripts import serve_local_news_replay as server
    from app.services import news_evaluation_service as evaluation, news_pipeline_service as pipeline
    from app.api.v1.endpoints import admin_news_publication as staff
    monkeypatch.setattr(server, "validate_target", lambda: None)
    def policy(auditor, configuration=None, *, publication_admission_at=None):
        return publication_admission_at
    monkeypatch.setattr(evaluation, "evaluation_policy", policy)
    original_pipeline, original_staff = pipeline.evaluation_policy, staff.evaluation_policy
    observed = datetime.fromisoformat("2026-09-24T16:34:00+08:00")
    published = datetime.fromisoformat("2026-09-25T04:42:00+08:00")
    with simulation_reads(observed, publication_admission_at=published):
        assert evaluation.evaluation_policy(None) == published
        assert pipeline.evaluation_policy(None, publication_admission_at=None) == published
        assert staff.evaluation_policy(None) == published
    assert evaluation.evaluation_policy is policy
    assert pipeline.evaluation_policy is original_pipeline
    assert staff.evaluation_policy is original_staff
