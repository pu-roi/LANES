"""Publisher-body retrieval regressions with fictional reporting; no live HTTP."""
from datetime import datetime

import httpx
import pytest

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_discovery_service import discover_news, fetch_article_text
from app.services.news_sources import load_news_sources
from app.services.taglish_extraction_service import article_update_observation_anchor
from test_news_processing import queue_db


URL = "https://www.gmanetwork.com/news/topstories/metro/1234567/fictional-flood-report/story/"
SOURCE = next(source for source in load_news_sources() if source.id == "feedspot-01")
BODY = (
    "<p>Flooding affected Example Avenue in Quezon City on September 9, 2026.</p>"
    "<p>Quezon City (as of 2:47 p.m.)</p><p>Gutter-deep (8 inches)</p>"
    "<ul><li>Example Avenue - passable to all types of vehicles</li>"
    "<li>Sample Street - passable with caution</li></ul>"
    '<div id="mrect_related_content_holder"><div><p>RELATED WRONG ROAD</p></div></div>'
    '<script>window.fake = "SCRIPT WRONG ROAD";</script>'
    "<p>Final update: the floodwater on Sample Street had cleared by 3 p.m.</p>"
)


def publisher_html(layout: str, body: str = BODY) -> str:
    if layout == "standard":
        return (
            '<article class="container storyContainer"><div class="upper_article">'
            '<div class="story_title"><h1>HEADLINE SHOULD NOT REPEAT</h1>'
            '<div class="main-byline"><div>By GMA News</div></div>'
            '<div class="article-time"><time><strong>Published </strong>September 9, 2026 9:19am</time>'
            '<br/><time><strong>Updated </strong>September 9, 2026 3:09pm</time></div>'
            '<div class="cta-container">GOOGLE PROMOTION</div>'
            '<figure><figcaption>CAPTION WRONG ROAD</figcaption></figure></div>'
            f'<div class="story_main">{body}</div></div>'
            '<div class="lower_article">TAGS AND RECOMMENDATIONS</div></article>'
        )
    return (
        '<article><h1>HEADLINE SHOULD NOT REPEAT</h1><div id="story-container">'
        '<time class="article-date">Published September 09, 2026 09:19 AM</time>'
        '<time class="article-date">Updated September 09, 2026 03:09 PM</time>'
        '<span id="byline">By GMA News</span>'
        '<figure><figcaption>CAPTION WRONG ROAD</figcaption></figure>'
        f'<div id="article-text"><body>{body}</body></div></div>'
        '<aside>TAGS AND RECOMMENDATIONS</aside></article>'
    )


def retrieve(html: str, **kwargs) -> tuple[str | None, str | None]:
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, text=html, headers={"content-type": "text/html; charset=utf-8"}))
    with httpx.Client(transport=transport) as client:
        return fetch_article_text(SOURCE, URL, client, **kwargs)


@pytest.mark.parametrize("layout", ["standard", "amp"])
@pytest.mark.parametrize("preserve_whitespace", [False, True])
def test_gma_reads_full_reporting_body_and_keeps_supported_update_time(layout, preserve_whitespace):
    text, error = retrieve(publisher_html(layout), preserve_whitespace=preserve_whitespace)
    assert error is None and text is not None
    assert "Gutter-deep (8 inches)" in text
    assert "\nExample Avenue - passable to all types of vehicles\n" in text
    assert "\nSample Street - passable with caution\n" in text
    assert "floodwater on Sample Street had cleared by 3 p.m." in text
    for unwanted in ["HEADLINE", "GOOGLE", "CAPTION", "RELATED", "SCRIPT", "TAGS"]:
        assert unwanted not in text
    article = NewsArticleExtractorInput(
        article_id=-1, title="Fictional flood report", publisher="GMA News Online",
        canonical_url=URL, article_text=text,
        published_at=datetime.fromisoformat("2026-09-09T09:19:06+08:00"))
    assert article_update_observation_anchor(article) == datetime.fromisoformat("2026-09-09T15:09:00+08:00")


@pytest.mark.parametrize("layout", ["standard", "amp"])
def test_gma_ignores_subsequently_loaded_articles_and_their_time_headers(layout):
    html = publisher_html(layout) + publisher_html(layout, "<p>SECOND STORY WRONG ROAD</p>" * 20)
    text, error = retrieve(html)
    assert error is None and text is not None
    assert "SECOND STORY" not in text
    assert text.count("Published") == text.count("Updated") == 1


@pytest.mark.parametrize("html", [
    '<article><h1>Flooding in Manila</h1><p>PAGE CHROME ONLY</p></article>' * 20,
    publisher_html("standard", ""),
    publisher_html("amp", "<p>Too short.</p>"),
    '<script type="application/ld+json">' + '{"articleBody":"INDEX SUMMARY"}' * 20 + '</script>',
])
def test_gma_missing_or_incomplete_reporting_body_is_not_successful_capture(html):
    text, error = retrieve(html)
    assert text is None
    assert error == "Article text unavailable or too short"


def test_gma_collects_the_publisher_body_through_ordinary_feed_discovery():
    from dataclasses import replace
    from email.utils import format_datetime

    feed_url = SOURCE.feed_urls[0]
    source = replace(SOURCE, feed_urls=(feed_url,))
    published = format_datetime(datetime.now().astimezone())
    feed = (f'<rss><channel><item><title>Flooding in Quezon City</title><link>{URL}</link>'
            f'<guid>{URL}</guid><pubDate>{published}</pubDate></item></channel></rss>')
    requests = []

    def publisher(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if str(request.url) == feed_url:
            return httpx.Response(200, text=feed, headers={"content-type": "application/rss+xml"})
        assert str(request.url) == URL
        return httpx.Response(200, text=publisher_html("standard"), headers={"content-type": "text/html"})

    with httpx.Client(transport=httpx.MockTransport(publisher)) as client:
        run = discover_news((source,), client)
    assert len(run.candidates) == 1
    candidate = run.candidates[0]
    assert candidate.article_error is None
    assert candidate.article_text is not None
    assert "GOOGLE PROMOTION" not in candidate.article_text
    assert "floodwater on Sample Street had cleared by 3 p.m." in candidate.article_text
    assert requests == [feed_url, URL]


def test_clean_capture_creates_new_version_and_failed_refresh_preserves_evidence(queue_db):
    from dataclasses import replace
    from sqlalchemy import select
    from app.crud.news import save_candidate
    from app.models.news import NewsArticleVersion, NewsExtractionRun
    from app.services.news_discovery_service import NewsCandidate
    from app.services.news_feed_service import NewsEntry

    # SQLite drops timezone offsets; store UTC, as the existing queue fixtures do.
    published = datetime.fromisoformat("2026-09-09T01:19:06+00:00")
    entry = NewsEntry(SOURCE.id, SOURCE.publisher, SOURCE.feed_urls[0], URL,
                      "Fictional flood report in Quezon City", "", URL, published)
    legacy = "Saved legacy index snapshot with Google promotion and a different flood list."
    candidate = NewsCandidate(SOURCE.id, SOURCE.publisher, URL, URL, entry.title, "",
                              published, published, legacy, None)
    cleaned, error = retrieve(publisher_html("standard"))
    assert error is None and cleaned is not None
    with queue_db() as db, db.begin():
        article = save_candidate(db, entry, candidate)
        article_id = article.id
    with queue_db() as db, db.begin():
        current = replace(candidate, article_text=cleaned)
        article = save_candidate(db, entry, current)
        assert article.id == article_id and article.article_text == cleaned
        save_candidate(db, entry, current)  # Identical retrieval reuses its input.
    with queue_db() as db, db.begin():
        failed = replace(candidate, article_text=None, article_error="Article HTTP 403")
        article = save_candidate(db, entry, failed)
        assert article.article_text == cleaned
        assert article.article_error == "Article HTTP 403"
        versions = list(db.scalars(select(NewsArticleVersion).order_by(NewsArticleVersion.id)))
        assert [version.input_snapshot["article_text"] for version in versions] == [legacy, cleaned]
        assert len(list(db.scalars(select(NewsExtractionRun)))) == 2
