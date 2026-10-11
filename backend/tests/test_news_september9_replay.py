"""Historical replay safeguards and real discovery/queue handoff, without live I/O."""
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import func, select, text

from scripts import replay_september9_news as replay
from scripts.seed_local_news_replay import require_local_test_database
from app.crud import news_processing
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.services.news_discovery_service import discover_news
from app.services.news_feed_service import parse_feed
from app.services.news_processing_service import process_saved_news
from test_news_processing import queue_db


@pytest.mark.parametrize("url", [
    "postgresql+psycopg://user:password@db.example.org/lanes_news_test",
    "postgresql+psycopg://user:password@localhost/lanes",
    "postgresql+psycopg://user:password@localhost/lanes_news_test?host=db.example.org",
    "postgresql+psycopg://user:password@localhost/lanes_news_test?hostaddr=203.0.113.1",
    "postgresql+psycopg://user:password@localhost/lanes_news_test?service=production",
    "postgresql+psycopg://user:password@localhost/lanes_news_test?dbname=lanes",
    "sqlite:///lanes_news_test",
])
def test_replay_rejects_shared_targets_and_connection_overrides(url: str) -> None:
    with pytest.raises(ValueError, match="loopback PostgreSQL database lanes_news_test"):
        require_local_test_database(url)


@pytest.mark.asyncio
async def test_persist_guard_rejects_target_before_network_or_database_access(monkeypatch, tmp_path: Path) -> None:
    from app.core.config import settings
    monkeypatch.setattr(settings, "DATABASE_URL", "postgresql+psycopg://user:password@localhost/lanes")
    def forbidden(*args, **kwargs):
        pytest.fail("Unsafe replay reached fixture retrieval")
    monkeypatch.setattr(replay, "fixture_client", forbidden)
    with pytest.raises(ValueError, match="lanes_news_test"):
        await replay.persist(tmp_path)


def test_reconstructed_feed_preserves_published_time_and_discloses_later_snapshot() -> None:
    for source in replay.replay_sources():
        specs = tuple(spec for spec in replay.ARTICLES if spec.source_id == source.id)
        entries = parse_feed(replay.reconstructed_feed(specs), source, source.feed_urls[0])
        assert [entry.article_url for entry in entries] == [spec.url for spec in specs]
        assert [entry.published_at for entry in entries] == [spec.published_at for spec in specs]
        assert all("Historical September 9" in entry.excerpt for entry in entries)
    midday = replay.source_timing()[1]
    assert midday["published_at"] == "2026-09-09T09:19:06+08:00"
    assert midday["snapshot_available_no_earlier_than"] == "2026-09-09T15:09:00+08:00"
    assert replay.REPLAY_AT > replay.ARTICLES[-1].published_at


def make_captures(path: Path) -> None:
    for spec in replay.ARTICLES:
        # These paraphrases exercise the ordinary publisher-specific parser,
        # admission, queue and reader path; originals stay private/ignored.
        body = ("As of 2:47 p.m., gutter-deep flooding affected Marcos Highway in Marikina City. "
                "The road remained passable to all types of vehicles. Authorities monitored the floodwater.")
        html = (f'<article><div id="sports_article_writeup"><p>{body}</p></div></article>'
                if spec.source_id == "feedspot-05" else f'<article><p>{body}</p></article>')
        (path / f"article-{spec.number}.html").write_text(html, encoding="utf-8")


def test_simulated_discovery_uses_age_policy_without_weakening_current_clock(tmp_path: Path) -> None:
    make_captures(tmp_path)
    requests: list[str] = []
    with replay.replay_clock(), replay.fixture_client(tmp_path, requests) as client:
        result = discover_news(replay.replay_sources(), client)
    assert len(result.candidates) == 3
    assert all(candidate.fetched_at == replay.REPLAY_AT for candidate in result.candidates)
    assert len(requests) == 5  # Two real feed probes plus three article fetches.
    requests.clear()
    with replay.fixture_client(tmp_path, requests) as client:
        current = discover_news(replay.replay_sources(), client)
    assert not current.candidates
    assert len(requests) == 2  # Current seven-day gate stops before article retrieval.


@pytest.mark.asyncio
async def test_discovery_durable_processing_and_recollection_keep_identity(queue_db, tmp_path: Path) -> None:
    make_captures(tmp_path)
    initial_clock = news_processing.utc_now
    with replay.replay_clock(), replay.fixture_client(tmp_path, []) as client:
        with queue_db() as db:
            first = discover_news(replay.replay_sources(), client, db)
            ids = list(db.scalars(select(NewsArticle.id)))
        assert len(ids) == len(first.candidates) == 3
        results = [await process_saved_news(queue_db, article_id=id_, clock=lambda: replay.REPLAY_AT) for id_ in ids]
        assert sum(result.completed for result in results) == 3
        with queue_db() as db:
            before = tuple(db.scalar(select(func.count()).select_from(model))
                           for model in (NewsArticle, NewsArticleVersion, NewsExtractionRun))
            assert before == (3, 3, 3)
            for version in db.scalars(select(NewsArticleVersion)):
                assert datetime.fromisoformat(version.input_snapshot["published_at"]).date().isoformat() == "2026-09-09"
            for run in db.scalars(select(NewsExtractionRun)):
                assert run.status == "completed"
                assert datetime.fromisoformat(run.result["extracted_at"].replace("Z", "+00:00")) == replay.REPLAY_AT
                assert not any(claim["action_type"] == "auto_approved" for claim in run.result["claims"])
        with queue_db() as db:
            second = discover_news(replay.replay_sources(), client, db)
            after = tuple(db.scalar(select(func.count()).select_from(model))
                          for model in (NewsArticle, NewsArticleVersion, NewsExtractionRun))
        assert not second.candidates and before == after
        repeated = [await process_saved_news(queue_db, article_id=id_, clock=lambda: replay.REPLAY_AT) for id_ in ids]
        assert not any(result.completed or result.failed for result in repeated)
    assert news_processing.utc_now is initial_clock


@pytest.mark.asyncio
async def test_persist_preserves_prior_revision_and_uses_full_reader_claim(queue_db, tmp_path: Path, monkeypatch) -> None:
    """The dedicated write path can also run in explicitly substituted SQLite.

    Production guards are covered above. This test substitutes the session and
    guard only to exercise persistence/report DTO behavior without a live DB.
    """
    from app.core import database
    from app.core.config import settings
    from app.crud.news import save_candidate

    make_captures(tmp_path)
    monkeypatch.setattr(settings, "DATABASE_URL", "postgresql+psycopg://user:password@localhost/lanes_news_test")
    monkeypatch.setattr(database, "SessionLocal", queue_db)
    guarded_targets: list[str] = []
    monkeypatch.setattr(replay, "require_local_test_database", guarded_targets.append)
    # Only count operations touch public tables in the harness. These empty
    # disposable tables intentionally omit all spatial state.
    with queue_db() as db, db.begin():
        db.execute(text("CREATE TABLE flood_reports (id INTEGER PRIMARY KEY)"))
        db.execute(text("CREATE TABLE flood_avoidance_zones (id INTEGER PRIMARY KEY)"))
    monkeypatch.setattr(news_processing, "current_pipeline_version", lambda: "september9-test-v6")
    with replay.replay_clock(), replay.fixture_client(tmp_path, []) as client:
        candidate = discover_news(replay.replay_sources()[:1], client).candidates[0]
        source = replay.replay_sources()[0]
        entry = parse_feed(replay.reconstructed_feed(replay.ARTICLES[:1]), source, source.feed_urls[0])[0]
        old_label = "Philstar (local historical test)"
        with queue_db() as db, db.begin():
            row = save_candidate(db, replace(entry, source_id=old_label), replace(candidate, source_id=old_label))
            article_id = row.id
        processed = await process_saved_news(queue_db, article_id=article_id, clock=lambda: replay.REPLAY_AT)
        assert processed.completed == 1
    with queue_db() as db:
        old_run = db.scalar(select(NewsExtractionRun))
        old_id, old_result = old_run.id, old_run.result
        old_version_id = old_run.article_version_id
        old_snapshot = db.get(NewsArticleVersion, old_version_id).input_snapshot
    monkeypatch.setattr(news_processing, "current_pipeline_version", lambda: "september9-test-v7")
    result = await replay.persist(tmp_path)
    assert len(guarded_targets) == 2
    assert result["repeat_idempotent"] and result["zones_and_reports_unchanged"]
    assert result["readable_locations"] >= 3
    assert result["cycles"][0]["counts"] == result["cycles"][1]["counts"]
    assert result["cycles"][1]["counts"]["runs"] == 4
    assert result["cycles"][1]["counts"]["versions"] == 3
    assert not any(detail["claim"]["road_placement"]["may_affect_routing"] for detail in result["details"])
    with queue_db() as db:
        assert db.get(NewsExtractionRun, old_id).result == old_result
        assert db.get(NewsArticleVersion, old_version_id).input_snapshot == old_snapshot
        latest = db.scalar(select(NewsExtractionRun).join(NewsArticleVersion).where(
            NewsArticleVersion.article_id == article_id).order_by(NewsExtractionRun.id.desc()))
        assert latest.pipeline_version == "september9-test-v7" and latest.article_version_id == old_version_id
