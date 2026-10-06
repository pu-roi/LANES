"""Free index lookup yields article links, never complete flood evidence."""

import httpx
import pytest
from datetime import date, datetime, timedelta, timezone
from email.utils import format_datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Event

from app.services.news_open_search_service import append_publisher_feed_leads, assess_alternate_article_leads, retrieve_open_article_leads
from app.services.news_sources import NewsSource

from app.services.news_open_search_service import search_open_article_leads
from app.services import news_open_search_service as search_service


ARTICLE_URL = "https://newsinfo.inquirer.net/2287229/example-story/amp"
CANONICAL_URL = "https://newsinfo.inquirer.net/2287229/example-story"


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0
        self.pauses: list[float] = []

    def read(self) -> float:
        return self.now

    def pause(self, seconds: float) -> None:
        self.pauses.append(seconds)
        self.now += seconds


@pytest.fixture(autouse=True)
def search_clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    clock = FakeClock()
    monkeypatch.setattr(search_service, "_SEARCH_GATE", search_service._SearchGate(clock.read, clock.pause))
    return clock


def test_open_lookup_labels_original_and_other_sources_without_a_key() -> None:
    queries: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.gdeltproject.org"
        assert "x-subscription-token" not in request.headers
        queries.append(request.url.params["query"])
        return httpx.Response(200, json={"articles": [
            {"url": CANONICAL_URL, "title": "Example story", "seendate": "20260818T071000Z"},
            {"url": "https://www.pna.gov.ph/articles/123", "title": "Related report",
             "seendate": "20260818T081000Z"},
            {"url": CANONICAL_URL, "title": "Duplicate original"},
            {"url": "javascript:alert(1)", "title": "Bad link"},
        ]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = search_open_article_leads(ARTICLE_URL, "Example story", "", client)

    assert queries == ['"Example story"']
    assert result.evidence_status == "index_links_only_incomplete_article"
    assert len(result.results) == 2
    assert result.results[0].relationship == "indexed_publisher_page"
    assert result.results[0].seen_at.isoformat() == "2026-08-18T07:10:00+00:00"
    assert result.results[1].relationship == "possible_other_source"
    assert result.errors == ()


def test_open_lookup_uses_rss_phrase_only_when_original_not_found() -> None:
    queries: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        queries.append(request.url.params["query"])
        if len(queries) == 2:
            return httpx.Response(200, json={"articles": [{
                "url": CANONICAL_URL, "title": "Example story"
            }]})
        return httpx.Response(200, json={"articles": []})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = search_open_article_leads(
            ARTICLE_URL, "Example story", "Flooding was reported near the Manresa covered court", client,
        )
    assert len(queries) == 2
    assert result.results[0].query_kind == "rss_phrase"
    assert result.results[0].relationship == "indexed_publisher_page"


def test_open_search_failure_is_visible_and_does_not_create_evidence() -> None:
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        return httpx.Response(429, text="provider diagnostic")

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = search_open_article_leads(ARTICLE_URL, "Example story", "Flooding reported near the Manresa covered court", client)
    assert len(requests) == 1
    assert result.results == ()
    assert result.retry_after_seconds == 60
    assert result.errors == ("title search failed: HTTP 429 (GDELT rate limit); retry in 60 seconds",)
    assert "provider diagnostic" not in str(result.errors)


def test_alternate_retrieval_preserves_original_and_requires_event_review() -> None:
    requests: list[str] = []
    source = NewsSource("alternate", "Alternate", ("example.org",),
                        ("https://example.org/feed",), date(2026, 9, 24), True)

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if request.url.host == "api.gdeltproject.org":
            return httpx.Response(200, json={"articles": [
                {"url": CANONICAL_URL, "title": "Original"},
                {"url": "https://example.org/flood", "title": "Alternate"},
                {"url": "https://unapproved.org/flood", "title": "Unknown"},
            ]})
        return httpx.Response(200, headers={"content-type": "text/html"},
                              text="<article><p>" + "Flooding occurred in Pasig yesterday. " * 15 + "</p></article>")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        lookup = search_open_article_leads(ARTICLE_URL, "Original", "", client)
        result = retrieve_open_article_leads(lookup, (source,), client)
    assert len(requests) == 2
    assert result.article_url == ARTICLE_URL
    assert result.results[0].article_text is None
    assert result.results[1].article_text
    assert result.results[1].publisher_source_id == "alternate"
    assert result.results[1].match_status == "same_event_review_required"
    assert result.results[2].article_error == "Publisher is not approved for retrieval"
    assert lookup.results[1].article_text is None


def test_alternate_retrieval_bounds_requests_and_blocks_redirects() -> None:
    source = NewsSource("alternate", "Alternate", ("example.org",),
                        ("https://example.org/feed",), date(2026, 9, 24), True)
    fetched: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.gdeltproject.org":
            return httpx.Response(200, json={"articles": [
                {"url": f"https://example.org/flood/{i}", "title": "Alternate"} for i in range(5)
            ]})
        fetched.append(str(request.url))
        return httpx.Response(302, headers={"location": "https://unapproved.org/private"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        lookup = search_open_article_leads(ARTICLE_URL, "Original", "", client)
        result = retrieve_open_article_leads(lookup, (source,), client)
    assert len(fetched) == 3
    assert all(hit.article_text is None for hit in result.results)
    assert result.results[0].article_error == "Article redirect left the publisher domains"
    assert result.results[3].article_error == "Alternate article retrieval limit reached"


def test_malformed_index_urls_are_skipped_without_losing_valid_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"articles": [
            {"url": "https://[invalid/flood"},
            {"url": "https://example.org:bad/flood"},
            {"url": "https://example.org:8443/flood"},
            {"url": CANONICAL_URL, "title": "Valid original"},
        ]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = search_open_article_leads(ARTICLE_URL, "Original", "", client)
    assert len(result.results) == 1
    assert result.results[0].url == CANONICAL_URL
    assert result.errors == ()


@pytest.mark.parametrize("response", [
    httpx.Response(200, text="Provider temporarily unavailable"),
    httpx.Response(200, json={"articles": {"unexpected": "object"}}),
    httpx.Response(200, json={"message": "Unavailable"}),
    httpx.Response(200, json=[]),
    httpx.Response(200, content=b"x" * 250_001),
])
def test_bad_provider_responses_surface_errors(response: httpx.Response) -> None:
    with httpx.Client(transport=httpx.MockTransport(lambda request: response)) as client:
        result = search_open_article_leads(ARTICLE_URL, "Original", "", client)
    assert result.results == ()
    assert len(result.errors) == 1
    assert "title search failed:" in result.errors[0]


def test_alternate_retrieval_skips_same_publisher_and_disabled_sources() -> None:
    original = NewsSource("original", "Original", ("inquirer.net",),
                          ("https://www.inquirer.net/fullfeed/",), date(2026, 9, 24), True)
    disabled = NewsSource("disabled", "Disabled", ("example.org",),
                          ("https://example.org/feed",), date(2026, 9, 24), False)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.gdeltproject.org"
        return httpx.Response(200, json={"articles": [
            {"url": CANONICAL_URL},
            {"url": "https://www.inquirer.net/related-story"},
            {"url": "https://example.org/flood"},
        ]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        lookup = search_open_article_leads(ARTICLE_URL, "Original", "", client)
        result = retrieve_open_article_leads(lookup, (original, disabled), client)
    assert all(hit.fetched_at is None and hit.article_text is None for hit in result.results)
    assert result.results[2].article_error == "Publisher is not approved for retrieval"


def test_paces_different_queries_and_reuses_cached_results(search_clock: FakeClock) -> None:
    starts: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        starts.append(search_clock.now)
        return httpx.Response(200, json={"articles": [{"url": CANONICAL_URL, "title": "Original"}]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        for title in ("First", "Second", "First"):
            result = search_open_article_leads(ARTICLE_URL, title, "", client)
            assert not result.errors
        assert starts == [1000, 1010]
        search_clock.now += 600
        search_open_article_leads(ARTICLE_URL, "First", "", client)
    assert len(starts) == 3


def test_cooldown_blocks_network_and_backoff_grows_then_resets(search_clock: FakeClock) -> None:
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if len(requests) == 3:
            return httpx.Response(200, json={"articles": []})
        return httpx.Response(429)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        first = search_open_article_leads(ARTICLE_URL, "First", "", client)
        blocked = search_open_article_leads(ARTICLE_URL, "Other title", "", client)
        assert len(requests) == 1
        assert first.retry_after_seconds == blocked.retry_after_seconds == 60
        search_clock.now += 60
        second = search_open_article_leads(ARTICLE_URL, "First", "", client)
        assert second.retry_after_seconds == 120
        search_clock.now += 120
        recovered = search_open_article_leads(ARTICLE_URL, "First", "", client)
        assert recovered.retry_after_seconds is None
        fourth = search_open_article_leads(ARTICLE_URL, "New title", "", client)
        assert fourth.retry_after_seconds == 60
        assert len(requests) == 4


@pytest.mark.parametrize("header", ["180", "http_date", "invalid", "-5", "0"])
def test_honors_retry_after_or_uses_safe_default(header: str, search_clock: FakeClock) -> None:
    if header == "http_date":
        header = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=180), usegmt=True)
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(429, headers={"retry-after": header}))) as client:
        result = search_open_article_leads(ARTICLE_URL, "Original", "", client)
    if header == "180" or "GMT" in header:
        assert 179 <= result.retry_after_seconds <= 180
    else:
        assert result.retry_after_seconds == 60


def test_http_200_throttle_notice_applies_cooldown_without_phrase_retry() -> None:
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        return httpx.Response(200, text="Please limit requests to one every 5 seconds.")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = search_open_article_leads(ARTICLE_URL, "Original", "Flooding was reported near the Manresa covered court", client)
        blocked = search_open_article_leads(ARTICLE_URL, "Different query", "", client)
    assert len(requests) == 1
    assert result.retry_after_seconds == blocked.retry_after_seconds == 60
    assert "HTTP 200" in result.errors[0]


def test_concurrent_lookup_does_not_send_duplicate_requests() -> None:
    entered = Event()
    release = Event()
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        entered.set()
        assert release.wait(5)
        return httpx.Response(200, json={"articles": []})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client, ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(search_open_article_leads, ARTICLE_URL, "Original", "", client)
        try:
            assert entered.wait(5)
            other = search_open_article_leads(ARTICLE_URL, "Another title", "", client)
            assert other.retry_after_seconds == 10
            assert "already in progress" in other.errors[0]
            assert len(requests) == 1
        finally:
            release.set()
        assert first.result(timeout=5).errors == ()


def test_server_failure_applies_cooldown() -> None:
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        return httpx.Response(503, headers={"retry-after": "120"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = search_open_article_leads(ARTICLE_URL, "Original", "", client)
        blocked = search_open_article_leads(ARTICLE_URL, "Different query", "", client)
    assert len(requests) == 1
    assert result.retry_after_seconds == blocked.retry_after_seconds == 120


def test_cache_is_bounded_and_returns_independent_data(search_clock: FakeClock) -> None:
    gate = search_service._SEARCH_GATE
    result = gate.run("First", lambda: [{"title": "Original"}])
    result[0]["title"] = "Changed by caller"
    assert gate.run("First", lambda: pytest.fail("Cache missed"))[0]["title"] == "Original"
    for i in range(search_service.MAX_CACHED_SEARCHES):
        gate.run(f"Other {i}", lambda: [])
    assert len(gate._cache) == search_service.MAX_CACHED_SEARCHES
    assert "First" not in gate._cache


def test_network_failure_has_cooldown_and_does_not_retry() -> None:
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        raise httpx.ConnectTimeout("private transport diagnostic", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        failed = search_open_article_leads(ARTICLE_URL, "First", "", client)
        blocked = search_open_article_leads(ARTICLE_URL, "Second", "", client)
    assert len(requests) == 1
    assert failed.retry_after_seconds == blocked.retry_after_seconds == 60
    assert "ConnectTimeout" in failed.errors[0]
    assert "private transport diagnostic" not in str(failed.errors)


def test_backoff_caps_at_fifteen_minutes_but_honors_longer_provider_delay(search_clock: FakeClock) -> None:
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(429))) as client:
        for expected in (60, 120, 240, 480, 900, 900):
            result = search_open_article_leads(ARTICLE_URL, "First", "", client)
            assert result.retry_after_seconds == expected
            search_clock.now += expected
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(429, headers={"retry-after": "3600"}))) as client:
        result = search_open_article_leads(ARTICLE_URL, "First", "", client)
    assert result.retry_after_seconds == 3600


def test_valid_cached_results_remain_available_during_other_query_cooldown() -> None:
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if len(requests) == 1:
            return httpx.Response(200, json={"articles": [{"url": CANONICAL_URL, "title": "Original"}]})
        return httpx.Response(429)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        original = search_open_article_leads(ARTICLE_URL, "First", "", client)
        limited = search_open_article_leads(ARTICLE_URL, "Second", "", client)
        cached = search_open_article_leads(ARTICLE_URL, "First", "", client)
    assert len(requests) == 2
    assert cached.results == original.results
    assert cached.retry_after_seconds is None
    assert limited.retry_after_seconds == 60


def test_normal_article_title_does_not_trigger_plain_text_throttle_detection() -> None:
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"articles": [
        {"url": CANONICAL_URL, "title": "Please limit requests to one every minute"}
    ]}))) as client:
        result = search_open_article_leads(ARTICLE_URL, "Original", "", client)
    assert result.errors == ()
    assert len(result.results) == 1


def test_gdelt_has_its_own_connection_budget_instead_of_staff_client_default() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.extensions["timeout"]["connect"] == 15
        assert request.extensions["timeout"]["read"] == 20
        assert request.headers["user-agent"].startswith("LANES-NewsDiscovery/")
        return httpx.Response(200, json={"articles": []})

    with httpx.Client(transport=httpx.MockTransport(handler), timeout=httpx.Timeout(8.0, connect=3.0)) as client:
        result = search_open_article_leads(ARTICLE_URL, "Original", "", client)
    assert result.errors == ()


def test_provider_outage_recovers_an_alternate_body_from_approved_feed() -> None:
    now = datetime.now(timezone.utc) - timedelta(hours=1)
    source = NewsSource("alternate", "Alternate", ("example.org",),
                        ("https://example.org/feed",), date(2026, 9, 24), True)
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if request.url.host == "api.gdeltproject.org":
            return httpx.Response(429)
        if request.url.path == "/feed":
            xml = f'<rss><channel><item><title>Flooding in Quezon City</title><link>https://example.org/flood</link><pubDate>{format_datetime(now)}</pubDate></item></channel></rss>'
            return httpx.Response(200, text=xml)
        assert request.url.path == "/flood"
        return httpx.Response(200, headers={"content-type": "text/html"}, text="<article><p>" + "Flooding occurred in Quezon City near Manresa. " * 8 + "</p></article>")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        lookup = search_open_article_leads(ARTICLE_URL, "Quezon City evacuees", "", client)
        lookup = append_publisher_feed_leads(lookup, "Quezon City evacuees", "", now, (source,), client)
        result = retrieve_open_article_leads(lookup, (source,), client)
    assert len(requests) == 3
    assert len(result.results) == 1
    alternate = result.results[0]
    assert alternate.query_kind == "publisher_feed"
    assert alternate.seen_at is None
    assert alternate.published_at
    assert alternate.article_text
    assert alternate.match_status == "same_event_review_required"
    assert result.article_url == ARTICLE_URL
    assert result.retry_after_seconds == 60
    assert "HTTP 429" in result.errors[0]


@pytest.mark.parametrize("publication", [None, "historical", "future"])
def test_feed_fallback_does_not_poll_for_missing_or_ineligible_original_date(publication: str | None) -> None:
    now = datetime.now(timezone.utc)
    original_date = None if publication is None else now - timedelta(days=8) if publication == "historical" else now + timedelta(hours=1)
    source = NewsSource("alternate", "Alternate", ("example.org",),
                        ("https://example.org/feed",), date(2026, 9, 24), True)
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(429))) as client:
        lookup = search_open_article_leads(ARTICLE_URL, "Quezon City evacuees", "", client)
    with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail("Ineligible original caused feed request"))) as client:
        result = append_publisher_feed_leads(lookup, "Quezon City evacuees", "", original_date, (source,), client)
    assert result.results == ()
    assert "publication date" in result.errors[-1] if publication is None else "seven-day" in result.errors[-1]


def test_feed_fallback_skips_wrong_place_stale_unknown_and_nonflood_entries() -> None:
    now = datetime.now(timezone.utc) - timedelta(hours=1)
    source = NewsSource("alternate", "Alternate", ("example.org",),
                        ("https://example.org/feed",), date(2026, 9, 24), True)
    cases = [("Flood in Cebu", now), ("Flood in Quezon City", now-timedelta(days=3)),
             ("Flood in Quezon City", None), ("Sports in Quezon City", now)]
    items = ''.join(f'<item><title>{title}</title><link>https://example.org/{i}</link>' +
                    (f'<pubDate>{format_datetime(when)}</pubDate>' if when else '') + '</item>'
                    for i, (title, when) in enumerate(cases))
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"articles": []}))) as client:
        lookup = search_open_article_leads(ARTICLE_URL, "Quezon City evacuees", "", client)
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, text=f'<rss><channel>{items}</channel></rss>'))) as client:
        result = append_publisher_feed_leads(lookup, "Quezon City evacuees", "", now, (source,), client)
    assert result.results == ()
    assert "no matching recent flood leads" in result.errors[-1]


def test_feed_fallback_limits_entries_and_preserves_visible_feed_failures() -> None:
    now = datetime.now(timezone.utc) - timedelta(hours=1)
    source = NewsSource("alternate", "Alternate", ("example.org",),
                        ("https://example.org/feed",), date(2026, 9, 24), True)
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"articles": []}))) as client:
        lookup = search_open_article_leads(ARTICLE_URL, "Flood in Pasig", "", client)
    items = ''.join(f'<item><title>Flood in Pasig</title><link>https://example.org/{i}</link><pubDate>{format_datetime(now)}</pubDate></item>' for i in range(10))
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, text=f'<rss><channel>{items}</channel></rss>'))) as client:
        result = append_publisher_feed_leads(lookup, "Flood in Pasig", "", now, (source,), client)
    assert len(result.results) == 3
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(403, text="private provider diagnostic"))) as client:
        failed = append_publisher_feed_leads(lookup, "Flood in Pasig", "", now, (source,), client)
    assert any("HTTP 403" in error for error in failed.errors)
    assert "private provider diagnostic" not in str(failed.errors)


def test_feed_fallback_uses_newest_three_across_publishers_and_rejects_stale_boundary() -> None:
    from app.services.news_open_search_service import OpenSearchLookup
    now = datetime.now(timezone.utc)
    sources = tuple(NewsSource(str(index), str(index), (f"publisher{index}.org",),
                              (f"https://publisher{index}.org/feed",), date(2026, 9, 24), True)
                    for index in range(2))
    lookup = OpenSearchLookup(ARTICLE_URL, now, "no_leads", (), ())

    def handler(request: httpx.Request) -> httpx.Response:
        hours = [30, 20, 10] if request.url.host == "publisher0.org" else [3, 2, 1]
        items = ''.join(f'<item><title>Flood in Pasig</title><link>https://{request.url.host}/{hour}</link>'
                        f'<pubDate>{format_datetime(now-timedelta(hours=hour))}</pubDate></item>' for hour in hours)
        return httpx.Response(200, text=f'<rss><channel>{items}</channel></rss>')

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = append_publisher_feed_leads(lookup, "Flood in Pasig", "", now-timedelta(hours=2), sources, client)
    assert [hit.url for hit in result.results] == [f"https://publisher1.org/{hour}" for hour in [1, 2, 3]]
    # An original just inside seven days must not admit a lead eight days old.
    stale = now-timedelta(days=8)
    xml = f'<rss><channel><item><title>Flood in Pasig</title><link>https://publisher0.org/stale</link><pubDate>{format_datetime(stale)}</pubDate></item></channel></rss>'
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, text=xml))) as client:
        result = append_publisher_feed_leads(lookup, "Flood in Pasig", "", now-timedelta(days=6, hours=23), sources, client)
    assert not result.results


def test_feed_fallback_skips_network_if_index_already_has_approved_alternate() -> None:
    source = NewsSource("alternate", "Alternate", ("example.org",),
                        ("https://example.org/feed",), date(2026, 9, 24), True)
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"articles": [{"url":"https://example.org/flood"}]}))) as client:
        lookup = search_open_article_leads(ARTICLE_URL, "Quezon City evacuees", "", client)
    with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail("Unnecessary feed request"))) as client:
        result = append_publisher_feed_leads(lookup, "Quezon City evacuees", "", None, (source,), client)
    assert result is lookup


def test_empty_lookup_is_not_labeled_as_available_alternate_evidence() -> None:
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(429))) as client:
        lookup = search_open_article_leads(ARTICLE_URL, "Original", "", client)
        result = retrieve_open_article_leads(lookup, (), client)
    assert result.evidence_status == "alternate_article_unavailable"


def test_read_only_command_reports_failure_without_body_or_database_use(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import json
    import sys
    from scripts import run_news_discovery

    original_client = httpx.Client
    monkeypatch.setattr(run_news_discovery.httpx, "Client", lambda **kwargs: original_client(transport=httpx.MockTransport(lambda request: httpx.Response(429)), **kwargs))
    monkeypatch.setattr(run_news_discovery, "SessionLocal", lambda: pytest.fail("Read-only fallback opened a database session"))
    monkeypatch.setattr(sys, "argv", ["run_news_discovery", "--open-leads", "--article-url", ARTICLE_URL, "--title", "Quezon City evacuees", "--retrieve-articles", "--published-at", "2026-01-01T00:00:00+00:00"])
    assert run_news_discovery.main() == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["read_only"] is True
    assert payload["outcome"] == "no_alternate_body"
    assert payload["lookup"]["evidence_status"] == "alternate_article_unavailable"
    assert payload["lookup"]["retry_after_seconds"] == 60


def test_read_only_command_rejects_unapproved_article_url(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    from scripts import run_news_discovery

    monkeypatch.setattr(sys, "argv", ["run_news_discovery", "--open-leads", "--article-url", "https://unapproved.org/flood", "--title", "Flood in Pasig"])
    with pytest.raises(SystemExit) as exc:
        run_news_discovery.main()
    assert exc.value.code == 2


def test_event_context_query_finds_differently_titled_alternate_with_date_bounds(search_clock: FakeClock) -> None:
    now = datetime.now(timezone.utc) - timedelta(days=2)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(200, json={"articles": [{"url": CANONICAL_URL}]})
        assert request.url.params["query"] == '"Quezon City" (flood OR flooding OR baha)'
        assert "timespan" not in request.url.params
        assert request.url.params["startdatetime"] == (now-timedelta(days=2)).strftime("%Y%m%d%H%M%S")
        assert "enddatetime" in request.url.params
        return httpx.Response(200, json={"articles": [{"url": "https://www.philstar.com/nation/alternate", "title": "LIST: Flooded Metro Manila roads"}]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = search_open_article_leads(ARTICLE_URL, "Quezon City evacuees", "", client, now, True)
    assert len(requests) == 2
    assert search_clock.pauses == [10]
    assert result.results[1].query_kind == "event_context"
    assert result.results[1].relationship == "possible_other_source"


def test_event_context_does_not_retry_during_provider_cooldown() -> None:
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        return httpx.Response(429)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = search_open_article_leads(ARTICLE_URL, "Quezon City evacuees", "", client, datetime.now(timezone.utc), True)
    assert len(requests) == 1
    assert result.retry_after_seconds == 60


def test_event_context_cache_keeps_different_date_windows_separate() -> None:
    now = datetime.now(timezone.utc) - timedelta(days=2)
    event_requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if "startdatetime" in request.url.params:
            event_requests.append(request.url.params["startdatetime"])
        return httpx.Response(200, json={"articles": []})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        search_open_article_leads(ARTICLE_URL, "Quezon City evacuees", "", client, now, True)
        search_open_article_leads(ARTICLE_URL, "Quezon City evacuees", "", client, now-timedelta(days=1), True)
    assert len(event_requests) == 2
    assert event_requests[0] != event_requests[1]


@pytest.mark.parametrize("case,expected", [
    ("overlap", "possible_event_overlap"), ("different_city", "event_context_conflict"),
    ("different_road", "event_context_conflict"), ("different_date", "event_context_conflict"),
    ("unknown_publication", "insufficient_event_evidence"), ("different_depth", "event_context_conflict"),
    ("forecast", "event_context_conflict"), ("wrong_city_road", "event_context_conflict"),
])
def test_alternate_event_review_uses_places_roads_dates_and_flood_details(case: str, expected: str) -> None:
    from app.services.news_open_search_service import OpenSearchHit, OpenSearchLookup
    publication = datetime.now(timezone.utc) - timedelta(hours=2)
    city = "Quezon City" if case == "different_city" else "Pasig City"
    road = "Bernal Street" if case == "different_road" else "Laguna Street"
    depth = "waist-deep" if case == "different_depth" else "knee-deep"
    body = (f"Flooding affected {road} in {city}, with {depth} water. Residents were told to avoid the affected road. " * 2)
    if case == "forecast":
        body = "Posibleng bahain ang Laguna Street sa Pasig City dahil sa paparating na bagyo. " * 2
    if case == "wrong_city_road":
        body = "Flooding affected Laguna Street in Quezon City. Flooding affected Bernal Street in Pasig City. " * 2
    alternate_date = None if case == "unknown_publication" else publication-timedelta(days=3) if case == "different_date" else publication
    hit = OpenSearchHit("https://www.philstar.com/flood", "Different headline", datetime.now(timezone.utc),
                        "possible_other_source", "publisher_feed", publisher_source_id="feedspot-05",
                        article_text=body, published_at=alternate_date, match_status="same_event_review_required")
    lookup = OpenSearchLookup(ARTICLE_URL, datetime.now(timezone.utc), "alternate_articles_require_event_review", (hit,), ())
    result = assess_alternate_article_leads(lookup, "Flooding on Laguna Street in Pasig City", "Knee-deep flooding affected Laguna Street in Pasig City.", publication)
    review = result.results[0].event_review
    assert review.status == expected
    assert any("Original full article" in reason for reason in review.missing_evidence)
    assert result.results[0].match_status == "same_event_review_required"
    if case == "overlap":
        assert review.shared_places == ("pasig",)
        assert review.shared_roads == ("laguna street",)
    if case == "unknown_publication":
        assert any("index-seen time is not publication" in reason for reason in review.missing_evidence)


def test_copied_alternate_body_is_not_independent_confirmation() -> None:
    from dataclasses import asdict, replace
    from app.schemas.news_candidate import OpenSearchLookupSummary
    from app.services.news_open_search_service import OpenSearchHit, OpenSearchLookup
    publication = datetime.now(timezone.utc)-timedelta(hours=1)
    body = "Flooding affected Laguna Street in Pasig City, with knee-deep water. " * 3
    first = OpenSearchHit("https://www.philstar.com/first", "Different headline", None, "possible_other_source", "publisher_feed",
                          publisher_source_id="feedspot-05", article_text=body, published_at=publication)
    second = replace(first, url="https://www.gmanetwork.com/second", publisher_source_id="feedspot-01", article_text=body.upper())
    lookup = OpenSearchLookup(ARTICLE_URL, datetime.now(timezone.utc), "alternate_articles_require_event_review", (first, second), ())
    result = assess_alternate_article_leads(lookup, "Flooding on Laguna Street in Pasig City", "", publication)
    review = result.results[1].event_review
    assert review.status == "duplicate_body_requires_review"
    assert review.duplicate_of == first.url
    assert result.results[1].article_text == body.upper()
    serialized = OpenSearchLookupSummary.model_validate(asdict(result))
    assert serialized.results[1].event_review.duplicate_of == first.url


@pytest.mark.parametrize("case,decision", [
    ("rising", "possible_depth_status_update"),
    ("receding", "possible_depth_status_update"),
    ("clearance", "possible_clearance_update"),
    ("older_republished", "older_observation"),
    ("simultaneous_conflict", "same_time_conflict"),
    ("untimed", "observation_time_missing"),
    ("stale", "stale_observation"),
    ("different_segment", "segment_context_differs"),
    ("recurrence", "possible_recurrence"),
    ("corroboration", "newer_corroborating_observation"),
])
def test_flood_updates_follow_road_observation_time_not_publication(case: str, decision: str) -> None:
    from dataclasses import asdict
    from app.schemas.news_candidate import OpenSearchLookupSummary
    from app.services.news_open_search_service import OpenSearchHit, OpenSearchLookup

    ph = timezone(timedelta(hours=8))
    publication = datetime(2026, 10, 1, 10, 30, tzinfo=ph)
    alternate_publication = publication + timedelta(hours=2)
    now = datetime(2026, 10, 1, 13, 0, tzinfo=ph)
    previous = "Knee-deep flooding affected Laguna Street in Pasig City as of 10 a.m."
    body = "Chest-deep flooding affected Laguna Street in Pasig City as of 11 a.m."
    if case == "receding":
        previous = previous.replace("Knee-deep", "Chest-deep")
        body = body.replace("Chest-deep", "Knee-deep")
    elif case == "clearance":
        body = "Flooding on Laguna Street in Pasig City completely subsided as of 11 a.m."
    elif case == "older_republished":
        body = body.replace("11 a.m.", "9 a.m.")
    elif case == "simultaneous_conflict":
        body = body.replace("11 a.m.", "10 a.m.")
    elif case == "untimed":
        body = body.replace(" as of 11 a.m.", "")
    elif case == "stale":
        now += timedelta(hours=13)
    elif case == "different_segment":
        previous = previous.replace("in Pasig", "between First and Second Streets in Pasig")
        body = body.replace("in Pasig", "between Third and Fourth Streets in Pasig")
    elif case == "recurrence":
        previous = "Flooding on Laguna Street in Pasig City completely subsided as of 10 a.m."
    elif case == "corroboration":
        body = body.replace("Chest-deep", "Knee-deep")
    hit = OpenSearchHit("https://www.philstar.com/update", "Road flooding update", now,
                        "possible_other_source", "publisher_feed", publisher_source_id="feedspot-05",
                        article_text=body, published_at=alternate_publication,
                        match_status="same_event_review_required")
    lookup = OpenSearchLookup(ARTICLE_URL, now, "alternate_articles_require_event_review", (hit,), ())
    result = assess_alternate_article_leads(lookup, "Flood update", previous, publication, now=now)
    review = result.results[0].event_review
    update = next(item for item in review.road_updates if item.road == "laguna street")
    assert update.city == "pasig"
    assert update.decision == decision
    if case in {"rising", "receding", "clearance", "corroboration"}:
        assert review.status == "possible_observation_update"
        assert not review.conflicts
        assert update.alternate_observed_at > update.previous_observed_at
    if case == "older_republished":
        assert review.status == "older_or_stale_observation"
        assert update.alternate_observed_at < update.previous_observed_at
    assert any("Original full article" in reason for reason in review.missing_evidence)
    assert result.results[0].match_status == "same_event_review_required"
    assert OpenSearchLookupSummary.model_validate(asdict(result)).results[0].event_review.road_updates[0].decision == decision


def test_observation_matching_is_per_road_and_unrelated_warning_does_not_poison_update() -> None:
    from app.services.news_open_search_service import OpenSearchHit, OpenSearchLookup
    ph = timezone(timedelta(hours=8))
    publication = datetime(2026, 10, 1, 10, 30, tzinfo=ph)
    now = datetime(2026, 10, 1, 13, tzinfo=ph)
    previous = ("Knee-deep flooding affected Laguna Street in Pasig City as of 10 a.m.\n"
                "Waist-deep flooding affected Bernal Street in Pasig City as of 9 a.m.")
    body = ("Chest-deep flooding affected Laguna Street in Pasig City as of 11 a.m.\n"
            "Waist-deep flooding affected Bernal Street in Pasig City as of 8 a.m.\n"
            "Posibleng bahain ang Aurora Boulevard sa Quezon City dahil sa paparating na bagyo.")
    hit = OpenSearchHit("https://www.philstar.com/update", "Road update", None, "possible_other_source",
                        "publisher_feed", article_text=body, published_at=now)
    lookup = OpenSearchLookup(ARTICLE_URL, now, "alternate_articles_require_event_review", (hit,), ())
    result = assess_alternate_article_leads(lookup, "Flood update", previous, publication, now=now)
    review = result.results[0].event_review
    decisions = {item.road: item.decision for item in review.road_updates}
    assert decisions == {"laguna street": "possible_depth_status_update", "bernal street": "older_observation"}
    assert not review.conflicts
