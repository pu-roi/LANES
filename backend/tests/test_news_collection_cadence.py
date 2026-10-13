"""Scheduling regression for real recorded jitter, without external services."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest

from app.schemas.news_weather import NewsWeatherController, WeatherProvider
from app.services.news_collection_cadence_service import collection_is_due, next_collection_due, scheduler_slot
from app.services import news_weather_controller_service as controller


COLLECTED = datetime.fromisoformat("2026-10-13T13:45:20.492870+00:00")


@pytest.mark.parametrize("interval,next_tick", [(15, "14:00"), (30, "14:15"), (60, "14:45")])
def test_worker_delay_does_not_add_an_extra_scheduler_tick(interval, next_tick):
    due = datetime.fromisoformat(f"2026-10-13T{next_tick}:00+00:00")
    assert next_collection_due(COLLECTED, interval) == due
    assert not collection_is_due(COLLECTED, due - timedelta(microseconds=1), interval)
    assert collection_is_due(COLLECTED, due + timedelta(seconds=3), interval)
    assert collection_is_due(COLLECTED, due + timedelta(seconds=19), interval)
    assert COLLECTED.isoformat() == "2026-10-13T13:45:20.492870+00:00"


def test_same_slot_repeat_future_clock_and_midnight():
    assert not collection_is_due(COLLECTED, COLLECTED + timedelta(minutes=5), 15)
    assert not collection_is_due(COLLECTED, COLLECTED - timedelta(seconds=1), 15)
    late = datetime.fromisoformat("2026-10-13T23:45:24+08:00")
    assert next_collection_due(late, 15) == datetime.fromisoformat("2026-10-14T00:00:00+08:00")
    with pytest.raises(ValueError, match="timezone"):
        collection_is_due(None, datetime(2026, 10, 13), 15)
    with pytest.raises(ValueError, match="interval"):
        next_collection_due(COLLECTED, 0)


@pytest.mark.parametrize("execution_state,operation,expected", [
    ("finished", "existing-operation", "dispatched"),
    ("running", "existing-operation", "dispatch_pending"),
    ("unknown", "existing-operation", "dispatch_pending"),
    ("absent", None, "dispatch_pending"),
])
def test_next_slot_reconciles_known_operations_without_duplicate_launch(monkeypatch, execution_state, operation, expected):
    state = NewsWeatherController(last_tick_at=datetime.fromisoformat("2026-10-13T13:45:03.675142+00:00"),
        dispatch_reserved_at=datetime.fromisoformat("2026-10-13T13:45:03.675142+00:00"),
        dispatch_state="submitted" if operation else "unknown", dispatch_operation=operation,
        dispatch_token="existing-token", worker_starts=1)
    snapshots, starts, reconciled = [], [], []
    now = datetime.fromisoformat("2026-10-13T14:00:03.094828+00:00")
    class Session:
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def connection(self): return self
        def scalar(self, *_): return True
        def execute(self, *_): pass
    class Gateway:
        def reconcile(self, *args):
            reconciled.append(args)
            return execution_state
        def start(self, token):
            assert snapshots[-1].dispatch_state == "reserved"
            assert snapshots[-1].dispatch_token == token
            starts.append(token)
            return "new-operation"
    monkeypatch.setattr(controller, "read_controller", lambda _: state)
    monkeypatch.setattr(controller, "save_controller", lambda _, value: snapshots.append(deepcopy(value)))
    monkeypatch.setattr(controller, "fetch_weather", lambda *_args, **_kwargs: [WeatherProvider(
        name="Open-Meteo", source_url="https://example.invalid", checked_at=now, status="risk")])
    monkeypatch.setattr(controller, "current_flood_until", lambda *_: None)
    monkeypatch.setattr(controller, "latest_collection_at", lambda _: COLLECTED)
    monkeypatch.setattr(controller, "read_configuration", lambda _: SimpleNamespace(news_collection_enabled=True))
    monkeypatch.setattr(controller, "selected_news_sources", lambda _: (SimpleNamespace(id="publisher"),))
    monkeypatch.setattr(controller, "pending_pipeline_work", lambda *_args, **_kwargs: False)
    from app.services import news_evaluation_service
    monkeypatch.setattr(news_evaluation_service, "evaluation_policy", lambda *_: SimpleNamespace(fingerprint="fixture"))
    with httpx.Client() as client:
        gateway = Gateway()
        result = controller.run_weather_tick(Session, now=now, client=client, gateway=gateway)
        assert result["outcome"] == expected
        assert len(starts) == (1 if expected == "dispatched" else 0)
        assert len(reconciled) == (1 if operation else 0)
        assert controller.run_weather_tick(Session, now=now + timedelta(seconds=2), client=client,
            gateway=gateway)["outcome"] == "duplicate_tick"
        assert len(starts) == (1 if expected == "dispatched" else 0)
