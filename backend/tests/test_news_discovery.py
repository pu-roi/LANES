"""Offline RSS/Atom and safe-discovery contract tests."""

from dataclasses import replace
from datetime import date

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from app.api import deps
from app.main import app
from app.models.news import NewsArticle, NewsArticleFeedEntry, NewsFeedCheckpoint
from app.services.news_discovery_service import PASIG_BARANGAYS, discover_news, fetch_article_text, likely_pasig_flood, likely_philippine_flood
from app.services.news_feed_service import NewsEntry, parse_feed, probe_feed
from app.services.news_sources import NewsSource, load_news_sources


FEED_URL = "https://feeds.example.org/news.xml"
ARTICLE_URL = "https://news.example.org/pasig-flood"


def source(*, enabled: bool = True) -> NewsSource:
    return NewsSource("example", "Example News", ("news.example.org",), (FEED_URL,),
                      date(2026, 9, 24) if enabled else None, enabled)


def rss(items: str) -> bytes:
    return f'<rss version="2.0"><channel><title>News</title>{items}</channel></rss>'.encode()


def test_registry_enables_only_dated_verified_feeds() -> None:
    sources = load_news_sources()
    assert len(sources) == 51
    assert {"feedspot-01", "feedspot-50", "news5"}.issubset({item.id for item in sources})
    assert {item.id for item in sources if item.enabled} == {
        "feedspot-01", "feedspot-02", "feedspot-03", "feedspot-05", "feedspot-07", "feedspot-14"
    }
    assert all(item.verified_at is not None for item in sources if item.enabled)
    assert len(PASIG_BARANGAYS) == 30


def test_rss_and_atom_parse_publisher_links_and_dates() -> None:
    item = '<item><guid>g-1</guid><title>Baha sa Pasig</title><link>' + ARTICLE_URL + '</link>' \
           '<description>Lubog sa Manggahan</description><pubDate>Thu, 24 Sep 2026 10:00:00 +0800</pubDate></item>'
    entries = parse_feed(rss(item), source(), FEED_URL)
    assert len(entries) == 1
    assert entries[0].feed_id == "g-1"
    assert entries[0].published_at.isoformat() == "2026-09-24T02:00:00+00:00"
    assert likely_pasig_flood(entries[0])
    assert likely_pasig_flood(replace(entries[0], title="Lagpas tuhod sa Santa Lucia", excerpt=""))

    atom = f'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>a-1</id>
    <title>Flood in Pasig</title><summary>Roads affected</summary>
    <link href="{ARTICLE_URL}" rel="alternate"/><updated>2026-09-24T03:00:00Z</updated>
    </entry></feed>'''.encode()
    parsed = parse_feed(atom, source(), FEED_URL)
    assert len(parsed) == 1
    assert parsed[0].feed_id == "a-1"
    assert parsed[0].published_at.isoformat() == "2026-09-24T03:00:00+00:00"


def test_philippine_flood_filter_handles_nationwide_and_excludes_international() -> None:
    base = NewsEntry("example", "Example News", FEED_URL, "id-1", "", "", ARTICLE_URL, None)
    # Nationwide city outside Pasig
    assert likely_philippine_flood(replace(base, title="Heavy flooding hits Cebu City", excerpt="Several streets impassable"))
    assert likely_philippine_flood(replace(base, title="Baha sa Davao Oriental", excerpt="Ulan nagdulot ng pagbaha"))
    # Headline without explicit place (retained for full-text extraction)
    assert likely_philippine_flood(replace(base, title="Ilang lansangan lubog sa baha dahil sa habagat", excerpt="Motorista pinag-iingat"))
    # Explicit international flood without PH place (excluded)
    assert not likely_philippine_flood(replace(base, title="Deadly flood hits Spain", excerpt="Valencia submerged in floodwater"))
    assert not likely_philippine_flood(replace(base, title="Flash floods in Florida kill 3", excerpt="Heavy rainfall inundates roads"))
    # Non-flood article (excluded)
    assert not likely_philippine_flood(replace(base, title="PBA finals game 7 schedule", excerpt="Sports update"))


def test_external_article_url_and_xml_entity_are_rejected() -> None:
    bad_link = '<item><title>Flood in Pasig</title><link>https://other.example.org/story</link></item>'
    assert parse_feed(rss(bad_link), source(), FEED_URL) == ()
    with pytest.raises(ValueError, match="declaration"):
        parse_feed(b'<!DOCTYPE rss [<!ENTITY x "y">]><rss/>', source(), FEED_URL)


def test_publisher_subdomains_are_allowed_without_matching_lookalikes() -> None:
    assert source().accepts_article_host("metro.news.example.org")
    assert not source().accepts_article_host("news.example.org.evil.test")


def test_feed_redirect_accepts_www_alias_but_rejects_another_host() -> None:
    item = f'<item><title>Flood in Pasig</title><link>{ARTICLE_URL}</link></item>'

    def good_handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "feeds.example.org":
            return httpx.Response(301, headers={"location": "https://www.feeds.example.org/news.xml"})
        return httpx.Response(200, content=rss(item))

    with httpx.Client(transport=httpx.MockTransport(good_handler)) as client:
        probe, entries = probe_feed(source(), FEED_URL, client)
    assert probe.status == "parsed" and len(entries) == 1

    transport = httpx.MockTransport(lambda request: httpx.Response(
        302, headers={"location": "https://evil.example.com/feed.xml"}))
    with httpx.Client(transport=transport) as client:
        probe, entries = probe_feed(source(), FEED_URL, client)
    assert probe.status == "failed" and not entries


def test_article_redirect_outside_publisher_is_metadata_only() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(
        302, headers={"location": "https://evil.example.com/story"}))
    with httpx.Client(transport=transport) as client:
        text, error = fetch_article_text(source(), ARTICLE_URL, client)
    assert text is None
    assert error == "Article redirect left the publisher domains"


def test_probe_surfaces_http_error_and_conditional_304() -> None:
    statuses = [403, 304]
    headers_seen: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        headers_seen.append(dict(request.headers))
        return httpx.Response(statuses.pop(0))

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        first, _ = probe_feed(source(), FEED_URL, client)
        second, _ = probe_feed(source(), FEED_URL, client, etag='"abc"')
    assert first.status == "http_error" and first.http_status == 403
    assert second.status == "unchanged" and second.http_status == 304
    assert headers_seen[1]["if-none-match"] == '"abc"'


def test_stale_last_modified_is_not_saved_for_conditional_requests() -> None:
    item = f'<item><title>Flood in Pasig</title><link>{ARTICLE_URL}</link>' \
           '<pubDate>Thu, 24 Sep 2026 10:00:00 +0800</pubDate></item>'
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, content=rss(item), headers={"last-modified": "Tue, 16 Apr 2024 10:46:22 GMT"}))
    with httpx.Client(transport=transport) as client:
        result, _ = probe_feed(source(), FEED_URL, client)
    assert result.status == "parsed"
    assert result.last_modified is None


def test_discovery_filters_deduplicates_and_does_not_create_reports() -> None:
    flood = f'<item><guid>one</guid><title>Flood in Pasig</title><link>{ARTICLE_URL}</link></item>'
    duplicate = f'<item><guid>two</guid><title>Flood in Pasig</title><link>{ARTICLE_URL}</link></item>'
    irrelevant = '<item><title>Sports in Pasig</title><link>https://news.example.org/sports</link></item>'
    article = '<html><main><h1>Flood in Pasig</h1><p>' + ('Floodwater affected Pasig roads. ' * 8) + '</p></main></html>'
    requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url))
        if str(request.url) == FEED_URL:
            return httpx.Response(200, content=rss(flood + duplicate + irrelevant),
                                  headers={"content-type": "application/rss+xml"})
        if str(request.url) == ARTICLE_URL:
            return httpx.Response(200, text=article, headers={"content-type": "text/html"})
        raise AssertionError("Unexpected request")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        run = discover_news((source(),), client)
    assert len(run.probes) == 1
    assert len(run.candidates) == 1
    assert run.candidates[0].article_text is not None
    assert requested == [FEED_URL, ARTICLE_URL]


def test_unverified_source_never_fetches() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("Unverified source made a network request")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        run = discover_news((source(enabled=False),), client)
    assert not run.probes and not run.candidates


def test_staff_source_api_requires_authentication_and_lists_all_candidates() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/admin/news/sources").status_code == 401
        assert client.get("/api/v1/admin/news/feeds").status_code == 401
        assert client.get("/api/v1/admin/news/candidates").status_code == 401
        assert client.post("/api/v1/admin/news/runs").status_code == 401
        assert client.post("/api/v1/admin/news/manual-candidate", json={"title": "Test", "text": "Baha"}).status_code == 401
        app.dependency_overrides[deps.get_current_active_admin] = lambda: object()
        try:
            response = client.get("/api/v1/admin/news/sources")
            assert response.status_code == 200
            assert len(response.json()) == 51
            assert sum(item["enabled"] for item in response.json()) == 6
            assert client.post("/api/v1/admin/news/sources/news5/probe").status_code == 422
            manual = client.post("/api/v1/admin/news/manual-candidate", json={
                "title": "Baha sa Ortigas",
                "text": "Lagpas tuhod ang baha sa Ortigas Avenue dahil sa malakas na ulan.",
                "source_url": "https://facebook.com/drrmo/posts/12345"
            })
            assert manual.status_code == 200
            assert manual.json()["title"] == "Baha sa Ortigas"
            assert manual.json()["publisher_source_id"] == "Staff DRRMO / Social Post"
            assert manual.json()["canonical_url"] == "https://facebook.com/drrmo/posts/12345"
            assert manual.json()["review_state"] == "pending"
        finally:
            app.dependency_overrides.clear()


@compiles(JSONB, "sqlite")
def _sqlite_jsonb(_type: JSONB, _compiler: object, **_kw: object) -> str:
    return "JSON"


def test_persistent_discovery_reuses_checkpoint_and_article_evidence() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    tables = [NewsFeedCheckpoint.__table__, NewsArticle.__table__, NewsArticleFeedEntry.__table__]
    NewsArticle.metadata.create_all(engine, tables=tables)
    item = f'<item><guid>one</guid><title>Flood in Pasig</title><link>{ARTICLE_URL}</link>' \
           '<description>Baha sa Manggahan</description></item>'
    article = '<html><main><p>' + ('Floodwater affected Pasig roads. ' * 8) + '</p></main></html>'
    seen_headers: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == FEED_URL:
            seen_headers.append(dict(request.headers))
            if request.headers.get("if-none-match") == '"first"':
                return httpx.Response(304)
            return httpx.Response(200, content=rss(item), headers={"etag": '"first"'})
        if str(request.url) == ARTICLE_URL:
            return httpx.Response(200, text=article, headers={"content-type": "text/html"})
        raise AssertionError("Unexpected URL")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client, Session(engine) as db:
        first = discover_news((source(),), client, db)
        second = discover_news((source(),), client, db)
        assert len(first.candidates) == 1
        assert not second.candidates
        assert second.probes[0].status == "unchanged"
        assert seen_headers[1]["if-none-match"] == '"first"'
        assert db.scalar(select(func.count()).select_from(NewsFeedCheckpoint)) == 1
        assert db.scalar(select(func.count()).select_from(NewsArticle)) == 1
        assert db.scalar(select(func.count()).select_from(NewsArticleFeedEntry)) == 1
    engine.dispose()
