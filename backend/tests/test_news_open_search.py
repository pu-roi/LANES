"""Free index lookup yields article links, never complete flood evidence."""

import httpx
import pytest
from datetime import date, datetime, timedelta, timezone
from email.utils import format_datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Event

from app.services.news_open_search_service import retrieve_open_article_leads
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
