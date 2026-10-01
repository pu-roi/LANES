"""Offline RSS/Atom and safe-discovery contract tests."""

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api import deps
from app.core.database import get_db
from app.main import app
from app.models.news import NewsArticle, NewsArticleFeedEntry, NewsFeedCheckpoint, NewsArticleVersion, NewsExtractionRun
from app.services.news_discovery_service import PASIG_BARANGAYS, discover_news, fetch_article_text, likely_metro_manila_flood, likely_pasig_flood
from app.services.news_open_search_service import OpenSearchHit, OpenSearchLookup
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
    assert len(sources) == 6
    assert {item.id for item in sources} == {
        "feedspot-01", "feedspot-02", "feedspot-03", "feedspot-05", "feedspot-07", "feedspot-14"
    }
    assert all(item.enabled and item.verified_at is not None and len(item.feed_urls) == 1 for item in sources)
    assert len(PASIG_BARANGAYS) == 30


@pytest.mark.parametrize("content,headers,expected", [
    (b"<rss><channel>", {}, "Invalid feed XML"),
    (b"<!DOCTYPE html><html><body>Just a moment...</body></html>",
     {"content-type": "text/html"}, "Feed response is HTML, not RSS/Atom"),
    (b"<html></html>", {"cf-mitigated": "challenge"}, "Feed access blocked by publisher challenge (HTTP 200)"),
])
def test_diagnostic_feed_parse_failure_keeps_http_status(content: bytes, headers: dict, expected: str) -> None:
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=content, headers=headers))) as client:
        probe, entries = probe_feed(source(), FEED_URL, client)
    assert probe.status == "failed"
    assert probe.http_status == 200
    assert probe.error == expected
    assert not entries


def test_feed_html_entities_preserve_xml_escaping_and_cdata() -> None:
    item = (f'<item><title>Quezon City&rsquo;s flood&nbsp;update&hellip; &amp; response</title>'
            f'<link>{ARTICLE_URL}?a=1&amp;b=2</link>'
            '<description><![CDATA[<p>Baha&nbsp;sa Pasig &amp; Maybunga</p>]]></description></item>')
    entries = parse_feed(rss(item), source(), FEED_URL)
    assert entries[0].title == "Quezon City’s flood update… & response"
    assert entries[0].article_url == ARTICLE_URL + "?a=1&b=2"
    assert entries[0].excerpt == "Baha sa Pasig & Maybunga"


@pytest.mark.parametrize("content", [
    b'<rss><channel><title>&unregistered;</title></channel></rss>',
    b'<!DOCTYPE rss [<!ENTITY custom "value">]><rss><channel><title>&custom;</title></channel></rss>',
    b'<!DOCTYPE rss SYSTEM "https://private.example.org/entity"><rss><channel/></rss>',
])
def test_html_entity_compatibility_does_not_enable_custom_xml_entities(content: bytes) -> None:
    with pytest.raises(ValueError):
        parse_feed(content, source(), FEED_URL)


@pytest.mark.parametrize("blocked", [False, True])
def test_diagnostic_collection_to_extraction_has_no_database_or_auditor_calls(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], blocked: bool,
) -> None:
    import json
    import sys
    from email.utils import format_datetime
    from scripts import run_news_discovery
    from app.services.hybrid_extraction_service import HybridExtractionService

    publication = datetime.now(timezone.utc)
    item = (f'<item><guid>diagnostic-1</guid><title>Baha sa Maybunga, Pasig City</title>'
            f'<link>{ARTICLE_URL}</link><pubDate>{format_datetime(publication)}</pubDate></item>')
    body = ("Binaha ang Barangay Maybunga sa Pasig City, abot-tuhod ang tubig kanina. "
            "Patuloy ang pagbaha sa lugar at pinapayuhan ang mga residente na mag-ingat.")
    requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url))
        if str(request.url) == FEED_URL:
            return httpx.Response(200, content=rss(item))
        assert str(request.url) == ARTICLE_URL
        if blocked:
            return httpx.Response(403, headers={"cf-mitigated": "challenge"})
        return httpx.Response(200, text=f"<article><p>{body}</p></article>", headers={"content-type": "text/html"})

    original_client = httpx.Client
    monkeypatch.setattr(run_news_discovery.httpx, "Client", lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs))
    monkeypatch.setattr(run_news_discovery, "load_news_sources", lambda _: (source(),))
    monkeypatch.setattr(run_news_discovery, "SessionLocal", lambda: pytest.fail("Diagnostic opened a database session"))
    monkeypatch.setattr(HybridExtractionService, "audit_claim_with_llm", lambda *args, **kwargs: pytest.fail("Diagnostic called external audit"))
    monkeypatch.setattr(sys, "argv", ["run_news_discovery", "--discover", "--dry-run", "--extract"])

    assert run_news_discovery.main() == (1 if blocked else 0)
    payload = json.loads(capsys.readouterr().out)
    assert requested == [FEED_URL, ARTICLE_URL]
    assert payload["read_only"] is True
    assert payload["extraction_mode"] == "rules_only"
    extraction = payload["extractions"][0]
    if blocked:
        assert payload["outcome"] == "extraction_errors"
        assert extraction["claim_count"] == 0
        assert "publisher challenge" in extraction["error"]
    else:
        assert payload["outcome"] == "claims_extracted"
        assert extraction["metadata_only"] is False
        assert extraction["error"] is None
        assert any(claim["barangay"] == "Maybunga" and claim["depth"] == "knee" for claim in extraction["claims"])
        assert set(extraction["actions"]) == {"flagged_review"}
        assert all(claim["geometry_provenance"] != "verified_segment" for claim in extraction["claims"])


@pytest.mark.parametrize("args", [["--discover", "--extract"], ["--probe", "--extract"]])
def test_diagnostic_extraction_rejects_non_dry_run_modes(monkeypatch: pytest.MonkeyPatch, args: list[str]) -> None:
    import sys
    from scripts import run_news_discovery
    monkeypatch.setattr(sys, "argv", ["run_news_discovery", *args])
    monkeypatch.setattr(run_news_discovery, "SessionLocal", lambda: pytest.fail("Invalid mode opened a database session"))
    with pytest.raises(SystemExit) as exc:
        run_news_discovery.main()
    assert exc.value.code == 2


def test_diagnostic_empty_feed_does_not_claim_extraction_success(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import json
    import sys
    from scripts import run_news_discovery

    original_client = httpx.Client
    monkeypatch.setattr(run_news_discovery.httpx, "Client", lambda **kwargs: original_client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=rss(""))), **kwargs))
    monkeypatch.setattr(run_news_discovery, "load_news_sources", lambda _: (source(),))
    monkeypatch.setattr(run_news_discovery, "SessionLocal", lambda: pytest.fail("Empty diagnostic opened a database session"))
    monkeypatch.setattr(sys, "argv", ["run_news_discovery", "--discover", "--dry-run", "--extract"])
    assert run_news_discovery.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["outcome"] == "no_candidates"
    assert payload["extractions"] == []


@pytest.mark.asyncio
async def test_diagnostic_extraction_failure_preserves_next_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.schemas.news_extraction import NewsExtractionResult
    from app.services.hybrid_extraction_service import HybridExtractionService
    from app.services.news_discovery_service import DiscoveryRun, NewsCandidate, extract_discovery_candidates

    async def extract(self, article, mode):
        assert mode == "rules_only"
        if article.article_id == -1:
            raise RuntimeError("private exception detail")
        return NewsExtractionResult(article_id=article.article_id, canonical_url=article.canonical_url,
                                    is_metadata_only=False, processed_text_length=200, claims=[])

    monkeypatch.setattr(HybridExtractionService, "extract_hybrid", extract)
    candidate = NewsCandidate("example", "Example", "id", ARTICLE_URL, "Baha sa Pasig", "",
                              datetime.now(timezone.utc), datetime.now(timezone.utc), "Body " * 40, None)
    results = await extract_discovery_candidates(DiscoveryRun((), (candidate, replace(candidate, article_url=ARTICLE_URL + "-2"))))
    assert results[0].error == "Extraction failed: RuntimeError"
    assert "private" not in results[0].error
    assert results[1].error is None
    assert results[1].extraction is not None


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


def test_metro_manila_flood_filter_requires_local_place_and_flood_terms() -> None:
    base = NewsEntry("example", "Example News", FEED_URL, "id-1", "", "", ARTICLE_URL, None)
    assert likely_metro_manila_flood(replace(base, title="Heavy flooding hits Quezon City", excerpt="Several streets impassable"))
    assert likely_metro_manila_flood(replace(base, title="Baha sa Pasig", excerpt="C. Raymundo Avenue binaha"))
    assert likely_metro_manila_flood(replace(base, title="Flood in Metro Manila", excerpt="Roads impassable"))
    assert likely_metro_manila_flood(replace(base, title="Baha sa Las Piñas", excerpt=""))
    assert likely_metro_manila_flood(replace(base, title="Flood on EDSA", excerpt=""))
    assert not likely_metro_manila_flood(replace(base, title="Heavy flooding hits Cebu City", excerpt="Several streets impassable"))
    assert not likely_metro_manila_flood(replace(base, title="Baha sa Davao Oriental", excerpt="Ulan nagdulot ng pagbaha"))
    assert not likely_metro_manila_flood(replace(base, title="Ilang lansangan lubog sa baha dahil sa habagat", excerpt="Motorista pinag-iingat"))
    assert not likely_metro_manila_flood(replace(base, title="Deadly flood hits Spain", excerpt="Valencia submerged in floodwater"))
    assert not likely_metro_manila_flood(replace(base, title="PBA finals game 7 schedule", excerpt="Sports update"))


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


def test_publisher_challenge_is_reported_as_incomplete_article() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(
        403, text="Just a moment...", headers={"cf-mitigated": "challenge"}))
    with httpx.Client(transport=transport) as client:
        text, error = fetch_article_text(source(), ARTICLE_URL, client)
    assert text is None
    assert error == "Article access blocked by publisher challenge (HTTP 403)"


def test_article_fetch_preserves_individual_flood_list_items() -> None:
    html = (
        "<article><h2>Impassable to all vehicles</h2><p>Quezon City</p>"
        "<ul><li>Brgy. Sienna<ul>"
        "<li>NS Amoranto cor Don Jose St. - 37 inches</li>"
        "<li>NS Amoranto cor Banawe St. - 26 inches</li>"
        "</ul></li></ul></article>"
    )
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, text=html, headers={"content-type": "text/html; charset=utf-8"}))
    with httpx.Client(transport=transport) as client:
        text, error = fetch_article_text(source(), ARTICLE_URL, client)
    assert error is None
    assert text is not None
    assert "Quezon City\nBrgy. Sienna\nNS Amoranto cor Don Jose St. - 37 inches\n" in text
    assert "\nNS Amoranto cor Banawe St. - 26 inches" in text


def test_article_fetch_excludes_gma_related_story_widget_inside_reporting_body() -> None:
    html = (
        "<main><p>Flooding was reported on Taft Avenue in Manila as of 4 p.m.</p>"
        '<div id="mrect_related_content_holder"><div class="stories">'
        "<h2>Other Stories</h2><h3>Antipolo flooding in another report</h3>"
        "</div></div>"
        "<p>Taft Avenue flooding had subsided as of 5 p.m. after the road update.</p></main>"
    )
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, text=html, headers={"content-type": "text/html; charset=utf-8"},
    ))
    with httpx.Client(transport=transport) as client:
        text, error = fetch_article_text(source(), ARTICLE_URL, client)
    assert error is None
    assert text is not None
    assert "Antipolo" not in text
    assert "Taft Avenue flooding had subsided" in text


def test_article_fetch_keeps_reporting_after_old_30000_character_cutoff() -> None:
    article_body = ("Flooding reported in Pasig. " * 1500) + "Final report: Laguna Street is flooded."
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, text=f"<article><p>{article_body}</p></article>",
        headers={"content-type": "text/html; charset=utf-8"},
    ))
    with httpx.Client(transport=transport) as client:
        text, error = fetch_article_text(source(), ARTICLE_URL, client)
    assert error is None
    assert text is not None and len(text) > 30_000
    assert text.endswith("Final report: Laguna Street is flooded.")


def test_article_fetch_rejects_oversize_text_instead_of_silent_partial_body() -> None:
    article_body = "Flooding reported in Pasig. " * 4200
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, text=f"<article><p>{article_body}</p></article>",
        headers={"content-type": "text/html; charset=utf-8"},
    ))
    with httpx.Client(transport=transport) as client:
        text, error = fetch_article_text(source(), ARTICLE_URL, client)
    assert text is None
    assert error == "Article text exceeds processing limit; full body was not extracted"


def test_article_fetch_rejects_explicit_continuation_page() -> None:
    html = (
        '<link rel="next" href="/story?page=2">'
        '<article><p>Flooding was reported on Laguna Street in Pasig City.</p>'
        '<a rel="next" href="/story?page=2">Continue reading</a></article>'
    )
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, text=html, headers={"content-type": "text/html; charset=utf-8"},
    ))
    with httpx.Client(transport=transport) as client:
        text, error = fetch_article_text(source(), ARTICLE_URL, client)
    assert text is None
    assert error == "Article has a continuation page; full body was not extracted"


def test_philstar_writeup_is_extracted_without_article_or_main_tags() -> None:
    philstar = NewsSource("feedspot-05", "Philstar.com", ("philstar.com",),
                          ("https://www.philstar.com/rss/headlines",), date(2026, 9, 24), True)
    url = "https://www.philstar.com/headlines/2026/09/28/2559554/example"
    html = (
        '<div id="sports_article_content"><div id="sports_article_writeup">'
        '<p>Flooding was reported on C. Raymundo Avenue in Pasig City at 3 p.m.</p>'
        '<p>A later update said that traffic had returned to normal by 6 p.m. on the same road.</p>'
        '<div id="related_block"><h4>Unrelated story about flooding in a different city</h4></div>'
        '</div></div><div class="next"><a href="/lazy_section.php?page=1&article=2559554">next</a></div>'
    )
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, text=html, headers={"content-type": "text/html; charset=utf-8"}))
    with httpx.Client(transport=transport) as client:
        text, error = fetch_article_text(philstar, url, client)
    assert error is None
    assert text is not None and "traffic had returned to normal" in text
    assert "\nA later update" in text
    assert "Unrelated story" not in text


@pytest.mark.parametrize("source_id,body_class", [
    ("feedspot-03", "post-single__content entry-content"),
    ("feedspot-07", "entry-content"),
])
def test_publisher_body_container_excludes_main_page_sidebars(source_id: str, body_class: str) -> None:
    publisher = NewsSource(source_id, "News", ("news.example.org",), (FEED_URL,), date(2026, 9, 24), True)
    related = ('<h6 id="h-also-on-rappler">ALSO ON RAPPLER</h6>'
               '<ul><li>Unrelated sidebar about another flood in Manila</li></ul>') if source_id == "feedspot-03" else ""
    html = (
        '<main><h1>Headline</h1><p>Unrelated flood story in Manila with a wrong road location.</p>'
        f'<div class="{body_class}"><p>Flooding was reported on C. Raymundo Avenue in Pasig City.</p>'
        '<p>A later update said the road cleared by 6 p.m. after the flood receded.</p>'
        f'{related}'
        '</div><p>Another unrelated main-page story.</p></main>'
    )
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, text=html, headers={"content-type": "text/html; charset=utf-8"}))
    with httpx.Client(transport=transport) as client:
        text, error = fetch_article_text(publisher, ARTICLE_URL, client)
    assert error is None
    assert text is not None and "road cleared by 6 p.m." in text
    assert "Unrelated" not in text


def test_registered_publisher_missing_body_container_stays_incomplete() -> None:
    publisher = NewsSource("feedspot-03", "Rappler", ("news.example.org",),
                           (FEED_URL,), date(2026, 9, 24), True)
    html = "<main><p>Unrelated page recommendations about flooding in Pasig City. " * 6 + "</p></main>"
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, text=html, headers={"content-type": "text/html; charset=utf-8"}))
    with httpx.Client(transport=transport) as client:
        text, error = fetch_article_text(publisher, ARTICLE_URL, client)
    assert text is None
    assert error == "Article text unavailable or too short"


def test_rappler_related_heading_without_list_keeps_following_reporting_list() -> None:
    publisher = NewsSource("feedspot-03", "Rappler", ("news.example.org",),
                           (FEED_URL,), date(2026, 9, 24), True)
    html = (
        '<div class="post-single__content"><p>Flooding was reported in Pasig City at 3 p.m.</p>'
        '<h6 id="h-also-on-rappler">ALSO ON RAPPLER</h6>'
        '<p>The later advisory reported these still-flooded sites:</p>'
        '<ul><li>C. Raymundo Avenue in Pasig City</li><li>Laguna Street in Pasig City</li></ul>'
        '</div>'
    )
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, text=html, headers={"content-type": "text/html; charset=utf-8"}))
    with httpx.Client(transport=transport) as client:
        text, error = fetch_article_text(publisher, ARTICLE_URL, client)
    assert error is None
    assert text is not None and "\nC. Raymundo Avenue" in text and "\nLaguna Street" in text


@pytest.mark.parametrize("href", ["?page=2", "?next=2", "/pasig-flood/page/2", "/pasig-flood/2"])
def test_article_fetch_rejects_unlabeled_same_article_continuation(href: str) -> None:
    html = (
        '<article><p>Flooding was reported on Laguna Street in Pasig City and on nearby roads.</p>'
        '<p>Additional flood updates appear on the second page of this report.</p></article>'
        f'<div class="pagination"><a href="{href}">2</a></div>'
    )
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, text=html, headers={"content-type": "text/html; charset=utf-8"}))
    with httpx.Client(transport=transport) as client:
        text, error = fetch_article_text(source(), "https://news.example.org/pasig-flood", client)
    assert text is None
    assert error == "Article has a continuation page; full body was not extracted"


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
    outside_scope = '<item><title>Flood in Cebu City</title><link>https://news.example.org/cebu-flood</link></item>'
    unspecified = '<item><title>Several roads flooded</title><link>https://news.example.org/unspecified-flood</link></item>'
    article = '<html><main><h1>Flood in Pasig</h1><p>' + ('Floodwater affected Pasig roads. ' * 8) + '</p></main></html>'
    requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url))
        if str(request.url) == FEED_URL:
            return httpx.Response(200, content=rss(flood + duplicate + irrelevant + outside_scope + unspecified),
                                  headers={"content-type": "application/rss+xml"})
        if str(request.url) == ARTICLE_URL:
            return httpx.Response(200, text=article, headers={"content-type": "text/html"})
        if str(request.url) == "https://news.example.org/unspecified-flood":
            outside_body = "Floodwater affected roads in Cebu City. " * 5
            return httpx.Response(200, text=f"<article><p>{outside_body}</p></article>", headers={"content-type": "text/html"})
        raise AssertionError("Unexpected request")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        run = discover_news((source(),), client)
    assert len(run.probes) == 1
    assert len(run.candidates) == 1
    assert run.candidates[0].article_text is not None
    assert requested == [FEED_URL, ARTICLE_URL, "https://news.example.org/unspecified-flood"]


def test_unverified_source_never_fetches() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("Unverified source made a network request")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        run = discover_news((source(enabled=False),), client)
    assert not run.probes and not run.candidates


@pytest.mark.parametrize("case,expected", [("local", True), ("outside_with_manila_weather", False), ("blocked", False)])
def test_missing_headline_location_is_checked_against_article_flood_claims(case: str, expected: bool) -> None:
    item = f'<item><title>Several roads flooded after heavy rain</title><link>{ARTICLE_URL}</link></item>'
    local = "Flooding affected Laguna Street in Pasig City. Residents reported knee-deep water this afternoon. " * 2
    outside = "Flooding affected roads in Cebu City. The Manila weather office monitored rainfall across the country. " * 2

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == FEED_URL:
            return httpx.Response(200, content=rss(item))
        if case == "blocked":
            return httpx.Response(403, headers={"cf-mitigated": "challenge"})
        return httpx.Response(200, text=f'<article><p>{local if case == "local" else outside}</p></article>', headers={"content-type": "text/html"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        run = discover_news((source(),), client)
    assert bool(run.candidates) is expected
    if expected:
        assert run.candidates[0].article_text == local.strip()
    elif case == "blocked":
        assert "publisher challenge" in run.notices[0].reason
    else:
        assert run.notices[0].reason == "No body-grounded Metro Manila flood claim"


def test_location_probe_budget_is_run_wide_and_does_not_skip_metadata_local_leads(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import news_discovery_service
    monkeypatch.setattr(news_discovery_service, "MAX_LOCATION_BODY_PROBES", 2)
    second_feed = "https://feeds.example.org/second.xml"
    second = replace(source(), id="second", feed_urls=(second_feed,))
    fetched: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url in {FEED_URL, second_feed}:
            prefix = "first" if url == FEED_URL else "second"
            items = ''.join(f'<item><title>Several roads flooded</title><link>https://news.example.org/{prefix}-{i}</link></item>' for i in range(4))
            items += f'<item><title>Flood in Pasig</title><link>https://news.example.org/{prefix}-local</link></item>'
            return httpx.Response(200, content=rss(items))
        fetched.append(url)
        body = ("Flooding affected Laguna Street in Pasig City. " if url.endswith("local") else "Flooding affected roads in Cebu City. ") * 4
        return httpx.Response(200, text=f"<article><p>{body}</p></article>", headers={"content-type": "text/html"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        run = discover_news((source(), second), client)
    assert len(fetched) == 4
    assert len(run.candidates) == 2
    assert fetched[0].endswith("first-local")
    assert sum("limit reached" in notice.reason for notice in run.notices) == 6


def test_unknown_scope_flood_control_story_is_not_saved_as_local_flood() -> None:
    item = f'<item><title>Flood control investigation continues</title><link>{ARTICLE_URL}</link></item>'
    body = ("Officials discussed an investigation into flood control projects in Taguig City. "
            "The inquiry concerns contracts and project funding. ")

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == FEED_URL:
            return httpx.Response(200, content=rss(item))
        return httpx.Response(200, text=f'<article><p>{body}</p></article>',
                              headers={"content-type": "text/html"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        run = discover_news((source(),), client)
    assert not run.candidates
    assert run.notices[0].reason == "No body-grounded Metro Manila flood claim"


def test_future_flood_article_is_visible_but_not_fetched() -> None:
    from email.utils import format_datetime
    item = f'<item><title>Flood in Pasig</title><link>{ARTICLE_URL}</link><pubDate>{format_datetime(datetime.now(timezone.utc)+timedelta(days=1))}</pubDate></item>'
    requests: list[str] = []
    with httpx.Client(transport=httpx.MockTransport(lambda request: (requests.append(str(request.url)) or httpx.Response(200, content=rss(item))))) as client:
        run = discover_news((source(),), client)
    assert requests == [FEED_URL]
    assert not run.candidates
    assert run.notices[0].reason == "Publication time is in the future"


def test_location_probe_prefers_newer_publications_to_feed_order(monkeypatch: pytest.MonkeyPatch) -> None:
    from email.utils import format_datetime
    from app.services import news_discovery_service
    monkeypatch.setattr(news_discovery_service, "MAX_LOCATION_BODY_PROBES", 1)
    now = datetime.now(timezone.utc)
    items = ''.join(f'<item><title>Several roads flooded</title><link>https://news.example.org/{label}</link>'
                    f'<pubDate>{format_datetime(now-timedelta(hours=hours))}</pubDate></item>'
                    for label, hours in [("old", 24), ("new", 1)])
    fetched: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == FEED_URL:
            return httpx.Response(200, content=rss(items))
        fetched.append(str(request.url))
        return httpx.Response(200, text='<article><p>' + 'Flooding affected Laguna Street in Pasig City. ' * 4 + '</p></article>', headers={"content-type": "text/html"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        run = discover_news((source(),), client)
    assert fetched == ["https://news.example.org/new"]
    assert run.candidates[0].article_url.endswith("/new")
    assert run.notices[0].article_url.endswith("/old")


@pytest.mark.parametrize("blocked_refresh", [False, True])
def test_same_url_new_publication_refreshes_body_and_preserves_failed_snapshot(blocked_refresh: bool) -> None:
    from email.utils import format_datetime
    engine = create_engine("sqlite+pysqlite:///:memory:")
    tables = [NewsFeedCheckpoint.__table__, NewsArticle.__table__, NewsArticleFeedEntry.__table__, NewsArticleVersion.__table__, NewsExtractionRun.__table__]
    NewsArticle.metadata.create_all(engine, tables=tables)
    initial_publication = datetime.now(timezone.utc).replace(microsecond=0)-timedelta(hours=2)
    revision = 0
    body_requests = 0
    initial_body = "Knee-deep flooding affected Laguna Street in Pasig City. " * 4
    updated_body = "Chest-deep flooding affected Laguna Street in Pasig City. " * 4

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal body_requests
        if str(request.url) == FEED_URL:
            pub = initial_publication + timedelta(hours=revision)
            # Even duplicate entries must not relabel a failed refresh's old body.
            item = f'<item><guid>same</guid><title>Flood in Pasig</title><link>{ARTICLE_URL}</link><pubDate>{format_datetime(pub)}</pubDate></item>'
            return httpx.Response(200, content=rss(item * 2))
        body_requests += 1
        if revision == 1 and blocked_refresh:
            return httpx.Response(403)
        body = updated_body if revision else initial_body
        return httpx.Response(200, text=f'<article><p>{body}</p></article>', headers={"content-type": "text/html"})

    try:
        with httpx.Client(transport=httpx.MockTransport(handler)) as client, Session(engine) as db:
            discover_news((source(),), client, db)
            revision = 1
            changed = discover_news((source(),), client, db)
            assert len(changed.candidates) == 1
            assert body_requests == 2
            stored = db.scalar(select(NewsArticle))
            if blocked_refresh:
                assert stored.article_text == initial_body.strip()
                assert stored.published_at.replace(tzinfo=timezone.utc) == initial_publication
                assert stored.article_error == "Article HTTP 403"
                retried = discover_news((source(),), client, db)
                assert len(retried.candidates) == 1
                assert body_requests == 3
            else:
                assert stored.article_text == updated_body.strip()
                assert stored.published_at.replace(tzinfo=timezone.utc) == initial_publication + timedelta(hours=1)
                revision = 0
                older = discover_news((source(),), client, db)
                assert not older.candidates
                assert any("Older feed revision" in notice.reason for notice in older.notices)
                assert body_requests == 2
                assert stored.article_text == updated_body.strip()
    finally:
        engine.dispose()


@pytest.mark.parametrize("fallback_path", ["index", "publisher_feed"])
@pytest.mark.parametrize("retained_body", [None, "Previous article body retained after a blocked refresh."])
def test_staff_source_api_requires_authentication_and_lists_runtime_sources(monkeypatch: pytest.MonkeyPatch, fallback_path: str, retained_body: str | None) -> None:
    from app.core.limiter import limiter
    limiter.reset()
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [NewsArticle.__table__, NewsArticleFeedEntry.__table__, NewsArticleVersion.__table__, NewsExtractionRun.__table__]
    NewsArticle.metadata.create_all(engine, tables=tables)

    def test_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    try:
        with TestClient(app) as client:
            assert client.get("/api/v1/admin/news/sources").status_code == 401
            assert client.get("/api/v1/admin/news/feeds").status_code == 401
            assert client.get("/api/v1/admin/news/candidates").status_code == 401
            assert client.get("/api/v1/admin/news/candidates/1/open-leads").status_code == 401
            assert client.post("/api/v1/admin/news/runs").status_code == 401
            assert client.post("/api/v1/admin/news/manual-candidate", json={"title": "Test", "text": "Baha"}).status_code == 401
            app.dependency_overrides[deps.get_current_active_admin] = lambda: object()
            try:
                response = client.get("/api/v1/admin/news/sources")
                assert response.status_code == 200
                assert len(response.json()) == 6
                assert sum(item["enabled"] for item in response.json()) == 6
                assert client.post("/api/v1/admin/news/sources/news5/probe").status_code == 404
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
                blocked_url = "https://newsinfo.inquirer.net/2287229/test-story"
                with Session(engine) as db:
                    blocked = NewsArticle(
                        canonical_url=blocked_url,
                        publisher_source_id="feedspot-02",
                        title="Flood in Pasig",
                        published_at=datetime.now(timezone.utc),
                        excerpt="Baha sa Manggahan",
                        article_text=retained_body,
                        article_error="Article access blocked by publisher challenge (HTTP 403)",
                        content_fingerprint="0" * 64,
                    )
                    db.add(blocked)
                    db.flush()
                    db.add(NewsArticleFeedEntry(
                        article_id=blocked.id,
                        source_id="feedspot-02",
                        feed_url="https://www.inquirer.net/fullfeed/",
                        feed_guid="blocked-1",
                    ))
                    db.commit()
                    blocked_id = blocked.id
                assert client.get("/api/v1/admin/news/candidates/99999/open-leads").status_code == 404
                monkeypatch.setattr("app.api.v1.endpoints.admin_news.search_open_article_leads", lambda *args, **kwargs: OpenSearchLookup(
                    article_url=blocked_url,
                    searched_at=datetime.now(timezone.utc),
                    evidence_status="index_links_only_incomplete_article",
                    results=(OpenSearchHit(
                        url=blocked_url,
                        title="Indexed Pasig story",
                        seen_at=None,
                        relationship="indexed_publisher_page",
                        query_kind="title",
                    ), OpenSearchHit(
                        url="https://www.philstar.com/nation/2026/08/17/2549888/related-flood-story",
                        title="Alternate flood report",
                        seen_at=None,
                        relationship="possible_other_source",
                        query_kind="title",
                    )),
                    errors=("GDELT cooldown; retry in 180 seconds",),
                    retry_after_seconds=180,
                ))
                lookup = client.get(f"/api/v1/admin/news/candidates/{blocked_id}/open-leads")
                assert lookup.status_code == 200
                assert lookup.json()["evidence_status"] == "index_links_only_incomplete_article"
                assert lookup.json()["retry_after_seconds"] == 180
                assert int(lookup.headers["retry-after"]) >= 179
                assert lookup.json()["results"][0]["relationship"] == "indexed_publisher_page"
                if fallback_path == "publisher_feed":
                    monkeypatch.setattr("app.api.v1.endpoints.admin_news.search_open_article_leads", lambda *args, **kwargs: OpenSearchLookup(
                        article_url=blocked_url, searched_at=datetime.now(timezone.utc),
                        evidence_status="index_links_only_incomplete_article", results=(),
                        errors=("title search failed: HTTP 429",), retry_after_seconds=180,
                    ))

                    def feed_lookup(source: NewsSource, feed_url: str, _client: httpx.Client):
                        now = datetime.now(timezone.utc)
                        entries = (NewsEntry(source.id, source.publisher, feed_url, "alternate-feed-entry",
                                             "Flood in Pasig", "Baha sa Manggahan",
                                             "https://www.philstar.com/nation/2026/08/17/2549888/related-flood-story", now),) if source.id == "feedspot-05" else ()
                        from app.services.news_feed_service import FeedProbe
                        return FeedProbe(source.id, source.publisher, feed_url, "parsed" if entries else "empty",
                                         200, len(entries), len(entries), now if entries else None), entries

                    monkeypatch.setattr("app.services.news_open_search_service.probe_feed", feed_lookup)
                fetched: list[str] = []

                def fake_article_fetch(source: NewsSource, url: str, _client: httpx.Client):
                    fetched.append(url)
                    assert source.id == "feedspot-05"
                    return "Independent report of flooding in Pasig.", None

                monkeypatch.setattr("app.services.news_open_search_service.fetch_article_text", fake_article_fetch)
                retrieved = client.get(f"/api/v1/admin/news/candidates/{blocked_id}/open-leads?retrieve_articles=true")
                assert retrieved.status_code == 200
                assert len(fetched) == 1
                alternate = retrieved.json()["results"][-1]
                assert alternate["article_text"] == "Independent report of flooding in Pasig."
                assert alternate["publisher_source_id"] == "feedspot-05"
                assert alternate["fetched_at"]
                assert alternate["match_status"] == "same_event_review_required"
                if fallback_path == "index":
                    assert retrieved.json()["results"][0]["article_text"] is None
                else:
                    assert alternate["query_kind"] == "publisher_feed"
                    assert alternate["published_at"]
                    assert "HTTP 429" in retrieved.json()["errors"][0]
                with Session(engine) as db:
                    original = db.get(NewsArticle, blocked_id)
                    assert original.article_text == retained_body
                    assert original.article_error == "Article access blocked by publisher challenge (HTTP 403)"
                    assert original.review_state == "pending"
                    assert db.scalar(select(func.count()).select_from(NewsArticle)) == 2
            finally:
                app.dependency_overrides.pop(deps.get_current_active_admin, None)
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


@compiles(JSONB, "sqlite")
def _sqlite_jsonb(_type: JSONB, _compiler: object, **_kw: object) -> str:
    return "JSON"


def test_persistent_discovery_reuses_checkpoint_and_article_evidence() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    tables = [NewsFeedCheckpoint.__table__, NewsArticle.__table__, NewsArticleFeedEntry.__table__, NewsArticleVersion.__table__, NewsExtractionRun.__table__]
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


@pytest.mark.parametrize("local", [True, False])
def test_body_scope_decision_survives_duplicate_entries_and_repeat_collection(local: bool) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    tables = [NewsFeedCheckpoint.__table__, NewsArticle.__table__, NewsArticleFeedEntry.__table__, NewsArticleVersion.__table__, NewsExtractionRun.__table__]
    NewsArticle.metadata.create_all(engine, tables=tables)
    items = ''.join(f'<item><guid>{i}</guid><title>Several roads flooded</title><link>{ARTICLE_URL}</link></item>' for i in range(2))
    requested: list[str] = []
    body = ("Flooding affected Laguna Street in Pasig City. " if local else "Flooding affected roads in Cebu City. ") * 4

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url))
        if str(request.url) == FEED_URL:
            return httpx.Response(200, content=rss(items))
        return httpx.Response(200, text=f"<article><p>{body}</p></article>", headers={"content-type": "text/html"})

    try:
        with httpx.Client(transport=httpx.MockTransport(handler)) as client, Session(engine) as db:
            first = discover_news((source(),), client, db)
            second = discover_news((source(),), client, db)
            assert len(first.candidates) == int(local)
            assert not second.candidates if local else len(second.notices) == 1
            assert requested.count(ARTICLE_URL) == (1 if local else 2)
            assert db.scalar(select(func.count()).select_from(NewsArticle)) == int(local)
            assert db.scalar(select(func.count()).select_from(NewsArticleFeedEntry)) == (2 if local else 0)
    finally:
        engine.dispose()
