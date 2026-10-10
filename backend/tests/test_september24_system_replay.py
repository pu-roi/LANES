"""Historical replay must reject shared DB targets before capture/session work."""
import pytest
from datetime import datetime
import xml.etree.ElementTree as ET

from scripts.replay_september24_pipeline import ARTICLES, available_articles, client, replay, sources


@pytest.mark.asyncio
@pytest.mark.parametrize("target", [
    "postgresql+psycopg://example.org/lanes_news_test",
    "postgresql+psycopg://127.0.0.1/lanes",
    "postgresql+psycopg://127.0.0.1/lanes_news_test?host=example.org",
])
async def test_actual_replay_rejects_shared_or_overridden_target_before_reading_capture(monkeypatch, tmp_path, target):
    from app.core.config import settings
    monkeypatch.setattr(settings, "DATABASE_URL", target)
    with pytest.raises(ValueError, match="loopback PostgreSQL"):
        await replay(tmp_path / "capture-must-not-be-opened")


def test_simulated_september24_cannot_fetch_later_articles(tmp_path):
    at = datetime.fromisoformat("2026-09-24T15:42:00+08:00")
    (tmp_path / "article-2.html").write_text("Original captured publisher HTML", encoding="utf-8")
    requests = []
    with client(tmp_path, requests, at=at) as publisher:
        rss = ET.fromstring(publisher.get(sources()[0].feed_urls[0]).content)
        assert [item.findtext("link") for item in rss.findall("./channel/item")] == [ARTICLES[0].url]
        assert publisher.get(ARTICLES[0].url).text == "Original captured publisher HTML"
        for future in ARTICLES[1:]:
            with pytest.raises(RuntimeError, match="uncaptured resource"):
                publisher.get(future.url)


def test_simulated_day_rollover_only_exposes_published_evidence():
    at = datetime.fromisoformat("2026-09-24T23:59:00+08:00")
    assert ARTICLES[-1] not in available_articles(at)
    first_available = datetime.fromisoformat("2026-09-25T04:41:00+08:00")
    assert ARTICLES[-1] in available_articles(first_available)
    with pytest.raises(ValueError, match="timezone offset"):
        available_articles(datetime(2026, 9, 24, 16))
