"""Public GDELT leads and approved alternate articles for staff event review."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from collections import OrderedDict
from copy import deepcopy
from email.utils import parsedate_to_datetime
from math import ceil
from threading import Lock
from time import monotonic, sleep
from typing import Callable
from urllib.parse import urlsplit

import httpx

from app.services.news_discovery_service import fetch_article_text
from app.services.news_feed_service import canonical_article_url
from app.services.news_sources import NewsSource


GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
MAX_RESULTS_PER_QUERY = 10
MAX_SEARCH_RESPONSE_BYTES = 250_000
SEARCH_INTERVAL_SECONDS = 10
SEARCH_CACHE_SECONDS = 600
MAX_CACHED_SEARCHES = 32


class _ProviderRateLimit(Exception):
    def __init__(self, retry_after: int = 0, status_code: int = 429) -> None:
        self.retry_after = retry_after
        self.status_code = status_code


class _SearchDeferred(Exception):
    def __init__(self, reason: str, retry_after: int) -> None:
        self.reason = reason
        self.retry_after = retry_after


def _retry_delay(value: str | None) -> int:
    """Read Retry-After seconds or an HTTP date without exposing headers."""
    if not value:
        return 0
    try:
        if value.strip().isascii() and value.strip().isdigit() and len(value.strip()) <= 10:
            return int(value.strip())
        retry_at = parsedate_to_datetime(value)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(0, ceil((retry_at - datetime.now(timezone.utc)).total_seconds()))
    except (ValueError, TypeError, OverflowError):
        return 0


class _SearchGate:
    """One in-flight GDELT query per process, paced and bounded in memory.

    Long cooldowns return immediately. Only the normal 10-second gap may
    wait inside the existing synchronous staff endpoint. This is not a
    distributed limiter across processes/Cloud Run instances.
    """
    def __init__(self, clock: Callable[[], float] = monotonic,
                 pause: Callable[[float], None] = sleep) -> None:
        self._clock = clock
        self._pause = pause
        self._lock = Lock()
        self._next_request = 0.0
        self._cooldown_until = 0.0
        self._failures = 0
        self._cache: OrderedDict[str, tuple[float, list[object]]] = OrderedDict()

    def run(self, query: str, fetch: Callable[[], list[object]]) -> list[object]:
        if not self._lock.acquire(blocking=False):
            raise _SearchDeferred("GDELT lookup already in progress", SEARCH_INTERVAL_SECONDS)
        try:
            now = self._clock()
            cached = self._cache.get(query)
            if cached is not None:
                if cached[0] > now:
                    self._cache.move_to_end(query)
                    return deepcopy(cached[1])
                del self._cache[query]
            if self._cooldown_until > now:
                raise _SearchDeferred("GDELT cooldown", ceil(self._cooldown_until - now))
            while True:
                remaining = self._next_request - self._clock()
                if remaining <= 0:
                    break
                self._pause(min(SEARCH_INTERVAL_SECONDS, remaining))
            try:
                result = fetch()
            except _ProviderRateLimit as exc:
                delay = self._backoff(exc.retry_after)
                raise _SearchDeferred(f"HTTP {exc.status_code} (GDELT rate limit)", delay) from exc
            except httpx.HTTPError as exc:
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code < 500:
                    raise
                requested_delay = _retry_delay(exc.response.headers.get("retry-after")) if isinstance(exc, httpx.HTTPStatusError) else 0
                delay = self._backoff(requested_delay)
                reason = f"HTTP {exc.response.status_code}" if isinstance(exc, httpx.HTTPStatusError) else exc.__class__.__name__
                raise _SearchDeferred(reason, delay) from exc
            finally:
                self._next_request = self._clock() + SEARCH_INTERVAL_SECONDS
            self._failures = 0
            self._cooldown_until = 0.0
            self._cache[query] = (self._clock() + SEARCH_CACHE_SECONDS, deepcopy(result))
            self._cache.move_to_end(query)
            while len(self._cache) > MAX_CACHED_SEARCHES:
                self._cache.popitem(last=False)
            return result
        finally:
            self._lock.release()

    def _backoff(self, requested_delay: int) -> int:
        self._failures = min(self._failures + 1, 5)
        delay = max(requested_delay, min(60 * 2 ** (self._failures - 1), 900))
        self._cooldown_until = self._clock() + delay
        return delay


_SEARCH_GATE = _SearchGate()


@dataclass(frozen=True)
class OpenSearchHit:
    url: str
    title: str
    seen_at: datetime | None
    relationship: str
    query_kind: str
    publisher_source_id: str | None = None
    article_text: str | None = None
    article_error: str | None = None
    fetched_at: datetime | None = None
    match_status: str = "unverified_index_lead"


@dataclass(frozen=True)
class OpenSearchLookup:
    article_url: str
    searched_at: datetime
    evidence_status: str
    results: tuple[OpenSearchHit, ...]
    errors: tuple[str, ...]
    retry_after_seconds: int | None = None


def retrieve_open_article_leads(
    lookup: OpenSearchLookup,
    sources: tuple[NewsSource, ...],
    client: httpx.Client,
) -> OpenSearchLookup:
    """Fetch at most three approved alternate articles for same-event review.

    Keep alternate bodies separate from the blocked original. Index timestamps
    cannot establish publication dates, event dates, or current flood status.
    """
    hits: list[OpenSearchHit] = []
    attempts = 0
    original_host = _article_identity(lookup.article_url)[0]
    original_source = next((source for source in sources
                            if canonical_article_url(lookup.article_url, source) is not None), None)
    for hit in lookup.results:
        source = next((source for source in sources if source.enabled and source.verified_at
                       and canonical_article_url(hit.url, source) is not None), None)
        if (hit.relationship != "possible_other_source" or _article_identity(hit.url)[0] == original_host
                or (source is not None and original_source is not None and source.id == original_source.id)):
            hits.append(hit)
            continue
        if source is None:
            hits.append(replace(hit, article_error="Publisher is not approved for retrieval"))
            continue
        if attempts >= 3:
            hits.append(replace(hit, article_error="Alternate article retrieval limit reached"))
            continue
        attempts += 1
        body, error = fetch_article_text(source, hit.url, client)
        hits.append(replace(hit, publisher_source_id=source.id, article_text=body,
                            article_error=error, fetched_at=datetime.now(timezone.utc),
                            match_status="same_event_review_required" if body else "article_unavailable"))
    return replace(lookup, results=tuple(hits), evidence_status="alternate_articles_require_event_review")


def _article_identity(url: str) -> tuple[str, str] | None:
    try:
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                or parsed.port not in (None, 443)):
            return None
    except ValueError:
        return None
    host = parsed.hostname.casefold().removeprefix("www.")
    path = parsed.path.rstrip("/")
    if path.endswith("/amp"):
        path = path[:-4]
    return host, path


def _bounded_text(value: object, limit: int) -> str:
    return " ".join(value.split())[:limit] if isinstance(value, str) else ""


def _seen_at(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _search(query: str, client: httpx.Client) -> list[object]:
    return _SEARCH_GATE.run(query, lambda: _fetch_search(query, client))


def _fetch_search(query: str, client: httpx.Client) -> list[object]:
    with client.stream(
        "GET",
        GDELT_DOC_URL,
        params={"query": query, "mode": "artlist", "format": "json",
                "maxrecords": MAX_RESULTS_PER_QUERY, "timespan": "3months"},
        follow_redirects=False,
    ) as response:
        if response.status_code == 429:
            raise _ProviderRateLimit(_retry_delay(response.headers.get("retry-after")))
        response.raise_for_status()
        body = bytearray()
        for chunk in response.iter_bytes():
            body.extend(chunk)
            if len(body) > MAX_SEARCH_RESPONSE_BYTES:
                raise ValueError("Search response exceeds size limit")
    # GDELT can return a plain-text throttle notice with HTTP 200.
    if not bytes(body).lstrip().startswith(b"{") and b"please limit requests to one every" in bytes(body).lower():
        raise _ProviderRateLimit(status_code=200)
    payload = httpx.Response(200, content=bytes(body)).json()
    results = payload.get("articles", [])
    if not isinstance(results, list):
        raise ValueError("Search response has no article list")
    return results[:MAX_RESULTS_PER_QUERY]


def search_open_article_leads(
    article_url: str,
    title: str,
    excerpt: str,
    client: httpx.Client,
) -> OpenSearchLookup:
    """Find related links by title, then RSS phrase if the original is absent.

    GDELT returns index metadata, not a fetched article body or verified flood facts.
    """
    original_identity = _article_identity(article_url)
    if original_identity is None:
        raise ValueError("A valid HTTPS publisher article URL is required")
    title_phrase = _bounded_text(title, 180).replace('"', "")
    excerpt_phrase = _bounded_text(excerpt, 100).replace('"', "")

    seen: set[tuple[str, str]] = set()
    hits: list[OpenSearchHit] = []
    errors: list[str] = []
    original_found = False
    retry_after_seconds: int | None = None

    def collect(query_kind: str, query: str) -> bool:
        nonlocal original_found, retry_after_seconds
        try:
            raw_results = _search(query, client)
        except _SearchDeferred as exc:
            retry_after_seconds = exc.retry_after
            errors.append(f"{query_kind} search failed: {exc.reason}; retry in {exc.retry_after} seconds")
            return False
        except httpx.HTTPStatusError as exc:
            errors.append(f"{query_kind} search failed: HTTP {exc.response.status_code}")
            return False
        except (httpx.HTTPError, ValueError, AttributeError, TypeError) as exc:
            errors.append(f"{query_kind} search failed: {exc.__class__.__name__}")
            return False
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            result_url = item.get("url")
            identity = _article_identity(result_url) if isinstance(result_url, str) else None
            if identity is None or identity in seen:
                continue
            seen.add(identity)
            mobile_url = item.get("url_mobile")
            is_original = identity == original_identity or (
                isinstance(mobile_url, str) and _article_identity(mobile_url) == original_identity
            )
            original_found |= is_original
            hits.append(OpenSearchHit(
                url=result_url,
                title=_bounded_text(item.get("title"), 300),
                seen_at=_seen_at(item.get("seendate")),
                relationship="indexed_publisher_page" if is_original else "possible_other_source",
                query_kind=query_kind,
            ))
        return True

    title_search_succeeded = True
    if title_phrase:
        title_search_succeeded = collect("title", f'"{title_phrase}"')
    if title_search_succeeded and not original_found and len(excerpt_phrase) >= 25:
        collect("rss_phrase", f'"{excerpt_phrase}"')

    return OpenSearchLookup(
        article_url=article_url,
        searched_at=datetime.now(timezone.utc),
        evidence_status="index_links_only_incomplete_article",
        results=tuple(hits),
        errors=tuple(errors),
        retry_after_seconds=retry_after_seconds,
    )
