"""Successful publisher corrections replace current evidence, preserving history."""
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import httpx
import pytest
from sqlalchemy import func, select

from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.models.news_telemetry import NewsDiscoveryFeedRun
from app.services.news_discovery_service import discover_news
from app.services.news_processing_service import process_saved_news
from app.services.news_results_service import browse_news_results
from app.services.news_sources import NewsSource
from test_news_processing import queue_db

URL = "https://example.org/metro-flood"
FEED = "https://example.org/rss"
SOURCE = NewsSource("correction-fixture", "Example News", ("example.org",), (FEED,), datetime.now().date(), True)
ORIGINAL = "As of 10 AM, knee-deep flooding affected Ortigas Avenue in Pasig City. Authorities monitored the flooded road and residents used another route."
CORRECTIONS = (
    "Officials corrected the earlier report: Ortigas Avenue in Pasig City was not flooded. Authorities confirmed that the road remained dry and normal traffic continued.",
    "A forecast says Ortigas Avenue in Pasig City may be flooded tomorrow. Officials corrected the earlier statement and explained this was a warning rather than an observation.",
    "Officials corrected the city in an earlier report. Knee-deep flooding affected Osmena Boulevard in Cebu City; the report concerned a different event outside Metro Manila.",
    "Officials withdrew the earlier report about Ortigas Avenue in Pasig City. The photograph concerned a drainage exercise, and no current flood observation was established.",
)


def client(body: str, published: datetime, revision: int, status: int = 200,
           title: str = "Pasig flood update", excerpt: str | None = None) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == FEED:
            xml = (f'<rss><channel><item><title>{title}</title><link>{URL}</link>'
                   f'<description>{excerpt if excerpt is not None else f"Metro Manila flood bulletin revision {revision}"}</description>'
                   f'<pubDate>{format_datetime(published)}</pubDate></item></channel></rss>')
            return httpx.Response(200, text=xml, headers={"content-type": "application/rss+xml"})
        return httpx.Response(status, text=f"<article><p>{body}</p></article>", headers={"content-type": "text/html"})
    return httpx.Client(transport=httpx.MockTransport(handler))


def results(db):
    return browse_news_results(db, page=1, page_size=50, search="", publisher=None,
                              condition=None, placement=None, order="publication_newest")


@pytest.mark.asyncio
@pytest.mark.parametrize("correction", CORRECTIONS)
async def test_revised_body_removes_prior_claim_from_latest_reader_and_preserves_history(queue_db, correction: str) -> None:
    published = datetime.now(timezone.utc) - timedelta(hours=1)
    with client(ORIGINAL, published, 0) as http, queue_db() as db:
        first = discover_news((SOURCE,), http, db)
        assert len(first.candidates) == 1
        article_id = db.scalar(select(NewsArticle.id))
    assert (await process_saved_news(queue_db)).completed == 1
    with queue_db() as db:
        old_run = db.scalar(select(NewsExtractionRun))
        old_run_id, old_result = old_run.id, old_run.result
        old_version = db.get(NewsArticleVersion, old_run.article_version_id)
        old_version_id, old_snapshot = old_version.id, old_version.input_snapshot
        assert results(db).total == 1
    with client(correction, published, 1) as http, queue_db() as db:
        revised = discover_news((SOURCE,), http, db)
        assert len(revised.candidates) == 1
        assert revised.candidates[0].article_text == correction
        assert any("No body-grounded" in notice.reason for notice in revised.notices)
        feed = db.scalar(select(NewsDiscoveryFeedRun).order_by(NewsDiscoveryFeedRun.id.desc()))
        assert feed.candidates_saved == 1 and feed.body_errors == 0
    assert (await process_saved_news(queue_db)).completed == 1
    with queue_db() as db:
        assert db.get(NewsArticle, article_id).article_text == correction
        assert results(db).total == 0
        assert db.get(NewsExtractionRun, old_run_id).result == old_result
        assert db.get(NewsArticleVersion, old_version_id).input_snapshot == old_snapshot
        assert db.scalar(select(func.count()).select_from(NewsArticleVersion)) == 2
    # Further corrections remain capturable after the current body itself has
    # ceased to qualify. A successful replacement must not depend on stale text.
    second_correction = correction + " Officials published a second clarification."
    with client(second_correction, published, 2) as http, queue_db() as db:
        assert len(discover_news((SOURCE,), http, db).candidates) == 1
    assert (await process_saved_news(queue_db)).completed == 1
    with queue_db() as db:
        assert results(db).total == 0
        assert db.scalar(select(func.count()).select_from(NewsArticleVersion)) == 3


@pytest.mark.parametrize("body,status", [(body, 200) for body in CORRECTIONS] + [(ORIGINAL, 403)])
def test_new_unqualified_or_unreadable_article_still_never_enters_collection(queue_db, body: str, status: int) -> None:
    with client(body, datetime.now(timezone.utc) - timedelta(minutes=1), 0, status) as http, queue_db() as db:
        run = discover_news((SOURCE,), http, db)
        assert not run.candidates
        assert db.scalar(select(func.count()).select_from(NewsArticle)) == 0
        assert db.scalar(select(func.count()).select_from(NewsArticleVersion)) == 0


@pytest.mark.asyncio
async def test_unreadable_refresh_preserves_the_original_successful_body(queue_db) -> None:
    published = datetime.now(timezone.utc) - timedelta(hours=1)
    with client(ORIGINAL, published, 0) as http, queue_db() as db:
        discover_news((SOURCE,), http, db)
    assert (await process_saved_news(queue_db)).completed == 1
    with client(CORRECTIONS[0], published, 1, 403) as http, queue_db() as db:
        assert not discover_news((SOURCE,), http, db).candidates
        article = db.scalar(select(NewsArticle))
        assert article.article_text == ORIGINAL and article.article_error == "Article HTTP 403"
        assert db.scalar(select(func.count()).select_from(NewsArticleVersion)) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("title,excerpt,body", [
    ("Officials: Ortigas Avenue stayed dry", "The earlier bulletin was incorrect.", CORRECTIONS[0]),
    ("Cebu flooding correction", "Officials clarified that flooding affected Cebu City.", CORRECTIONS[2]),
])
async def test_changed_metadata_cannot_hide_correction_of_known_verified_article(queue_db, title: str, excerpt: str, body: str) -> None:
    published = datetime.now(timezone.utc) - timedelta(hours=1)
    with client(ORIGINAL, published, 0) as http, queue_db() as db:
        discover_news((SOURCE,), http, db)
    assert (await process_saved_news(queue_db)).completed == 1
    for revision in (1, 2):
        with client(body + f" Further clarification number {revision}.", published, revision, title=title,
                    excerpt=excerpt + f" Revision {revision}.") as http, queue_db() as db:
            assert len(discover_news((SOURCE,), http, db).candidates) == 1
        assert (await process_saved_news(queue_db)).completed == 1
        with queue_db() as db:
            assert results(db).total == 0
            assert db.scalar(select(NewsArticle)).title == title


@pytest.mark.parametrize("title,excerpt", [
    ("Officials: Ortigas Avenue stayed dry", "The earlier bulletin was incorrect."),
    ("Cebu flooding correction", "Officials clarified that flooding affected Cebu City."),
])
def test_unqualified_metadata_cannot_admit_a_new_article(queue_db, title: str, excerpt: str) -> None:
    with client(CORRECTIONS[0], datetime.now(timezone.utc) - timedelta(minutes=1), 0,
                title=title, excerpt=excerpt) as http, queue_db() as db:
        assert not discover_news((SOURCE,), http, db).candidates
        assert db.scalar(select(func.count()).select_from(NewsArticle)) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("title,excerpt", [
    ("Pasig flood update", "Metro Manila flood bulletin revision 2"),
    ("Flood bulletin", "Authorities provided another clarification."),
])
async def test_failed_refresh_after_publisher_denial_remains_visible_without_reviving_old_results(queue_db, title: str, excerpt: str) -> None:
    from app.services.news_collection_service import browse_news_collection
    published = datetime.now(timezone.utc) - timedelta(hours=1)
    for revision, body in enumerate((ORIGINAL, CORRECTIONS[0])):
        with client(body, published, revision) as http, queue_db() as db:
            assert len(discover_news((SOURCE,), http, db).candidates) == 1
        assert (await process_saved_news(queue_db)).completed == 1
    with client("", published, 2, 503, title=title, excerpt=excerpt) as http, queue_db() as db:
        failed = discover_news((SOURCE,), http, db)
        assert not failed.candidates
        article = db.scalar(select(NewsArticle))
        assert article.article_text == CORRECTIONS[0]
        assert article.article_error == "Article HTTP 503"
        assert db.scalar(select(func.count()).select_from(NewsArticleVersion)) == 2
        assert results(db).total == 0
        attention = browse_news_collection(db, page=1, page_size=50, search="", publisher=None, status="attention")
        assert attention.total == 1
        assert attention.items[0].collection_status == "retrieval_failed"
        assert attention.items[0].location_count == 0
