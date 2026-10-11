"""Public GDELT leads and approved alternate articles for staff event review."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from collections import OrderedDict
from copy import deepcopy
from email.utils import parsedate_to_datetime
from math import ceil
from threading import Lock
from time import monotonic, sleep
from typing import Callable
from urllib.parse import urlsplit

import httpx
import hashlib
import re
import unicodedata

from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput
from app.services.news_discovery_service import FLOOD_TERMS, MAX_NEWS_AGE, METRO_MANILA_TERMS, fetch_article_text
from app.services.news_feed_service import canonical_article_url, probe_feed
from app.services.news_sources import NewsSource


GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
MAX_RESULTS_PER_QUERY = 10
MAX_SEARCH_RESPONSE_BYTES = 250_000
SEARCH_INTERVAL_SECONDS = 10
SEARCH_CACHE_SECONDS = 600
MAX_CACHED_SEARCHES = 32
GDELT_CONNECT_TIMEOUT_SECONDS = 15
GDELT_READ_TIMEOUT_SECONDS = 20
MAX_FEED_FALLBACK_PROBES = 5


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
class OpenLeadRoadUpdate:
    city: str
    road: str
    decision: str
    previous_observed_at: datetime | None
    alternate_observed_at: datetime | None
    previous_depth: str | None
    alternate_depth: str | None
    previous_condition: str | None
    alternate_condition: str | None


@dataclass(frozen=True)
class OpenLeadEventReview:
    status: str
    shared_places: tuple[str, ...]
    shared_roads: tuple[str, ...]
    conflicts: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    duplicate_of: str | None = None
    road_updates: tuple[OpenLeadRoadUpdate, ...] = ()


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
    published_at: datetime | None = None
    event_review: OpenLeadEventReview | None = None


@dataclass(frozen=True)
class OpenSearchLookup:
    article_url: str
    searched_at: datetime
    evidence_status: str
    results: tuple[OpenSearchHit, ...]
    errors: tuple[str, ...]
    retry_after_seconds: int | None = None


def append_publisher_feed_leads(
    lookup: OpenSearchLookup,
    title: str,
    excerpt: str,
    published_at: datetime | None,
    sources: tuple[NewsSource, ...],
    client: httpx.Client,
) -> OpenSearchLookup:
    """Use reviewed publisher feeds when the index has no approved alternate.

    Publication date and matching Metro Manila/flood words only shortlist leads;
    they do not verify the observation date or establish a shared flood event.
    This recent-feed path cannot recover arbitrary historical articles.
    """
    original_source = next((source for source in sources
                            if canonical_article_url(lookup.article_url, source)), None)
    approved = tuple(source for source in sources if source.enabled and source.verified_at
                     and (original_source is None or source.id != original_source.id))
    if any(hit.relationship == "possible_other_source" and
           any(canonical_article_url(hit.url, source) for source in approved)
           for hit in lookup.results):
        return lookup
    errors = list(lookup.errors)
    if published_at is None:
        errors.append("Publisher feed fallback needs the original publication date")
        return replace(lookup, errors=tuple(errors))
    original_time = published_at.replace(tzinfo=timezone.utc) if published_at.tzinfo is None else published_at.astimezone(timezone.utc)
    now = datetime.now(timezone.utc)
    if not now - MAX_NEWS_AGE <= original_time <= now:
        errors.append("Original article is outside the seven-day publisher-feed fallback window")
        return replace(lookup, errors=tuple(errors))
    places = {" ".join(match.group().casefold().split())
              for match in METRO_MANILA_TERMS.finditer(f"{title[:500]} {excerpt[:5000]}")}
    if not places:
        errors.append("Publisher feed fallback needs a Metro Manila place clue")
        return replace(lookup, errors=tuple(errors))
    seen = {_article_identity(hit.url) for hit in lookup.results}
    seen.add(_article_identity(lookup.article_url))
    hits = list(lookup.results)
    probes = 0
    feed_hits: list[OpenSearchHit] = []
    for source in approved:
        # Preserve publisher diversity within the five-probe fallback budget.
        # Supplemental commuter feeds must not crowd out other publishers.
        for feed_url in source.feed_urls[:1]:
            if probes >= MAX_FEED_FALLBACK_PROBES:
                break
            probes += 1
            probe, entries = probe_feed(source, feed_url, client)
            if probe.status not in {"parsed", "empty"}:
                detail = f"HTTP {probe.http_status}" if probe.http_status else probe.status
                errors.append(f"{source.id} publisher feed lookup failed: {detail}")
                continue
            for entry in entries:
                text = f"{entry.title} {entry.excerpt}"
                entry_places = {" ".join(match.group().casefold().split()) for match in METRO_MANILA_TERMS.finditer(text)}
                identity = _article_identity(entry.article_url)
                if (identity is None or identity in seen or not FLOOD_TERMS.search(text)
                        or not places.intersection(entry_places) or entry.published_at is None
                        or abs(entry.published_at - original_time) > timedelta(days=2)
                        or not now - MAX_NEWS_AGE <= entry.published_at <= now):
                    continue
                seen.add(identity)
                feed_hits.append(OpenSearchHit(
                    url=entry.article_url, title=entry.title, seen_at=None,
                    relationship="possible_other_source", query_kind="publisher_feed",
                    publisher_source_id=source.id, published_at=entry.published_at,
                    match_status="same_event_review_required",
                ))
    # Choose the newest eligible coverage across the bounded feed set, rather
    # than spending all three retrieval slots on the first publisher's order.
    hits.extend(sorted(feed_hits, key=lambda hit: hit.published_at, reverse=True)[:3])
    if not feed_hits:
        errors.append("Approved publisher feeds contain no matching recent flood leads")
    return replace(lookup, results=tuple(hits), errors=tuple(errors),
                   evidence_status="publisher_feed_leads_require_event_review")


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
    status = "alternate_articles_require_event_review" if any(hit.article_text for hit in hits) else "alternate_article_unavailable"
    return replace(lookup, results=tuple(hits), evidence_status=status)


def assess_alternate_article_leads(
    lookup: OpenSearchLookup,
    title: str,
    excerpt: str,
    published_at: datetime | None,
    *,
    now: datetime | None = None,
) -> OpenSearchLookup:
    """Compare source-linked clues without declaring a verified shared event.

    Original metadata is incomplete evidence. Duplicate bodies across publisher
    domains cannot count as independent confirmation. No DB or auditor is used.
    """
    from app.services.taglish_extraction_service import extract_taglish_flood_facts

    now = now or datetime.now(timezone.utc)

    def utc(value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

    now = utc(now)

    def name_key(value: str) -> str:
        folded = unicodedata.normalize("NFKD", value).casefold()
        words = re.findall(r"\w+", "".join(char for char in folded if not unicodedata.combining(char)))
        aliases = {"ave": "avenue", "st": "street", "rd": "road", "blvd": "boulevard"}
        return " ".join(aliases.get(word, word) for word in words)

    def place_clues(text: str) -> set[str]:
        broad = {"metro manila", "national capital region", "ncr", "edsa"}
        return {name_key(match.group()) for match in METRO_MANILA_TERMS.finditer(text)
                if name_key(match.group()) not in broad}

    original = extract_taglish_flood_facts(NewsArticleExtractorInput(
        article_id=-1, canonical_url=lookup.article_url, publisher="Original metadata",
        title=title, excerpt=excerpt, published_at=published_at,
    ))
    original_places = place_clues(f"{title} {excerpt}")
    def road_pairs(claims: list[ExtractedClaim]) -> set[tuple[str, str]]:
        return {(place, name_key(claim.canonical_road or claim.raw_place_name))
                for claim in claims if claim.place_type == "street" and claim.flood_mentioned
                and (not claim.is_negated or claim.condition == "subsided") and not claim.is_forecast
                and not claim.is_historical
                and "photo_caption_only" not in claim.uncertainty_reasons
                for place in place_clues(claim.canonical_city or "")}

    def road_depths(claims: list[ExtractedClaim]) -> dict[tuple[str, str], set[str]]:
        depths: dict[tuple[str, str], set[str]] = {}
        for claim in claims:
            if claim.depth_canonical:
                for pair in road_pairs([claim]):
                    depths.setdefault(pair, set()).add(claim.depth_canonical)
        return depths

    original_pairs = road_pairs(original.claims)
    original_roads = {road for _, road in original_pairs}
    original_depths = road_depths(original.claims)
    def compare_road(pair: tuple[str, str], alternate_claims: list[ExtractedClaim],
                     alternate_publication: datetime | None) -> OpenLeadRoadUpdate:
        def latest(claims: list[ExtractedClaim]) -> tuple[ExtractedClaim | None, bool]:
            matching = [claim for claim in claims if pair in road_pairs([claim])]
            timed = [claim for claim in matching if claim.event_time_kind == "observation"
                     and claim.event_time_resolved is not None]
            if not timed:
                return (matching[0] if matching else None), False
            stamp = max(utc(claim.event_time_resolved) for claim in timed)
            latest_claims = [claim for claim in timed if utc(claim.event_time_resolved) == stamp]
            states = {(claim.depth_canonical, claim.condition, name_key(claim.road_segment_raw or ""),
                       name_key(claim.local_area_raw or "")) for claim in latest_claims}
            return latest_claims[0], len(states) > 1

        previous, previous_ambiguous = latest(original.claims)
        alternate, alternate_ambiguous = latest(alternate_claims)
        left = previous.event_time_resolved if previous and previous.event_time_kind == "observation" else None
        right = alternate.event_time_resolved if alternate and alternate.event_time_kind == "observation" else None
        decision = "observation_time_missing"
        if previous_ambiguous or alternate_ambiguous:
            decision = "ambiguous_road_observations"
        elif left and right:
            left, right = utc(left), utc(right)
            previous_segment = (name_key(previous.road_segment_raw or ""), name_key(previous.local_area_raw or ""))
            alternate_segment = (name_key(alternate.road_segment_raw or ""), name_key(alternate.local_area_raw or ""))
            states_match = (previous.depth_canonical, previous.condition) == (alternate.depth_canonical, alternate.condition)
            if (published_at is None or alternate_publication is None):
                decision = "publication_time_missing"
            elif (left > utc(published_at) or right > utc(alternate_publication)
                  or left > utc(now) or right > utc(now)
                  or utc(published_at) > utc(now) or utc(alternate_publication) > utc(now)):
                decision = "invalid_future_time"
            elif previous_segment != alternate_segment:
                decision = "segment_context_differs"
            elif abs(right-left) > timedelta(days=1):
                decision = "incident_continuity_unresolved"
            elif right < left:
                decision = "older_observation"
            elif utc(now)-right > timedelta(hours=12):
                decision = "stale_observation"
            elif right == left:
                decision = "same_observation" if states_match else "same_time_conflict"
            elif previous.condition == "subsided" and alternate.condition != "subsided":
                decision = "possible_recurrence"
            elif alternate.condition == "subsided":
                decision = "possible_clearance_update"
            elif alternate.condition not in {"active", "rising", "receding"} or alternate.depth_canonical is None:
                decision = "incomplete_flood_state"
            else:
                decision = "newer_corroborating_observation" if states_match else "possible_depth_status_update"
        return OpenLeadRoadUpdate(pair[0], pair[1], decision, left, right,
                                 previous.depth_canonical if previous else None,
                                 alternate.depth_canonical if alternate else None,
                                 previous.condition if previous else None,
                                 alternate.condition if alternate else None)
    hashes: dict[str, str] = {}
    hits: list[OpenSearchHit] = []
    for index, hit in enumerate(lookup.results, start=1):
        if not hit.article_text or hit.relationship != "possible_other_source":
            hits.append(hit)
            continue
        normalized_body = " ".join(re.findall(r"\w+", hit.article_text.casefold()))
        digest = hashlib.sha256(normalized_body.encode("utf-8")).hexdigest()
        duplicate_of = hashes.get(digest)
        hashes.setdefault(digest, hit.url)
        alternate = extract_taglish_flood_facts(NewsArticleExtractorInput(
            article_id=-index-1, canonical_url=hit.url, publisher=hit.publisher_source_id or "Alternate",
            title=hit.title, article_text=hit.article_text, published_at=hit.published_at,
        ))
        alternate_places = set().union(*(place_clues(claim.canonical_city or claim.raw_place_name)
                                        for claim in alternate.claims if claim.flood_mentioned
                                        and claim.condition in {"active", "rising", "receding", "subsided"}
                                        and "photo_caption_only" not in claim.uncertainty_reasons))
        alternate_pairs = road_pairs(alternate.claims)
        alternate_depths = road_depths(alternate.claims)
        alternate_roads = {road for _, road in alternate_pairs}
        updates = tuple(compare_road(pair, alternate.claims, hit.published_at)
                        for pair in sorted(original_pairs.intersection(alternate_pairs)))
        shared_places = tuple(sorted(original_places.intersection(alternate_places)))
        shared_roads = tuple(sorted({road for _, road in original_pairs.intersection(alternate_pairs)}))
        conflicts: list[str] = []
        missing = ["Original full article body is unavailable; same-event verification remains required"]
        if original_places and alternate_places and not shared_places:
            conflicts.append("Specific Metro Manila place clues differ")
        if original_roads and alternate_roads and not shared_roads:
            conflicts.append("Named road clues differ")
        missing.append("City and road names do not verify the affected segment or incident continuity")
        for update in updates:
            if update.decision in {"same_time_conflict", "invalid_future_time", "segment_context_differs",
                                   "ambiguous_road_observations", "incident_continuity_unresolved", "possible_recurrence"}:
                conflicts.append(f"{update.city} / {update.road}: {update.decision}")
            elif update.decision in {"observation_time_missing", "publication_time_missing", "incomplete_flood_state"}:
                missing.append(f"{update.city} / {update.road}: {update.decision}")
                pair = (update.city, update.road)
                if (pair in original_depths and pair in alternate_depths
                        and not original_depths[pair].intersection(alternate_depths[pair])):
                    conflicts.append("Different depths lack an explicit observation order for a shared road")
        if not shared_places:
            missing.append("No shared specific Metro Manila place clue")
        if not shared_roads:
            missing.append("No shared flood-road clue")
        dates_known = published_at is not None and hit.published_at is not None
        if dates_known:
            original_time = published_at.replace(tzinfo=timezone.utc) if published_at.tzinfo is None else published_at
            alternate_time = hit.published_at.replace(tzinfo=timezone.utc) if hit.published_at.tzinfo is None else hit.published_at
            if abs(original_time - alternate_time) > timedelta(days=2):
                conflicts.append("Publication dates are more than two days apart")
            if original_time > now or alternate_time > now:
                conflicts.append("A publication timestamp is in the future")
            if now - utc(alternate_time) > MAX_NEWS_AGE:
                missing.append("Alternate publication is outside the seven-day discovery window")
        else:
            missing.append("Publication-date comparison unavailable; index-seen time is not publication time")
        if not updates or any(update.decision == "observation_time_missing" for update in updates):
            missing.append("Explicit flood-observation time comparison unavailable")
        # A warning on a different road must not invalidate a timed update on
        # the shared road. Clearance is an observed state, not a contradiction.
        if any((claim.is_forecast or (claim.is_negated and claim.condition != "subsided"))
               and any((place, name_key(claim.canonical_road or claim.raw_place_name)) in original_pairs
                       for place in place_clues(claim.canonical_city or ""))
               for claim in alternate.claims):
            conflicts.append("Shared road contains forecast or negated claims without observed clearance")
        if not alternate.claims:
            missing.append("No structured flood claims extracted from alternate body")
        decisions = {update.decision for update in updates}
        status = ("duplicate_body_requires_review" if duplicate_of else "event_context_conflict" if conflicts
                  else "possible_observation_update" if decisions & {"possible_depth_status_update", "possible_clearance_update", "newer_corroborating_observation"}
                  else "older_or_stale_observation" if decisions & {"older_observation", "stale_observation"}
                  else "possible_event_overlap" if shared_places and shared_roads and dates_known
                  else "insufficient_event_evidence")
        review = OpenLeadEventReview(status, shared_places, shared_roads, tuple(conflicts), tuple(missing), duplicate_of, updates)
        hits.append(replace(hit, event_review=review))
    return replace(lookup, results=tuple(hits))


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


def _search(query: str, client: httpx.Client, start_at: datetime | None = None,
            end_at: datetime | None = None) -> list[object]:
    key = f"{query}|{start_at}|{end_at}"
    return _SEARCH_GATE.run(key, lambda: _fetch_search(query, client, start_at, end_at))


def _fetch_search(query: str, client: httpx.Client, start_at: datetime | None = None,
                  end_at: datetime | None = None) -> list[object]:
    params = {"query": query, "mode": "artlist", "format": "json",
              "maxrecords": MAX_RESULTS_PER_QUERY, "timespan": "3months"}
    if start_at is not None and end_at is not None:
        del params["timespan"]
        params.update(startdatetime=start_at.strftime("%Y%m%d%H%M%S"),
                      enddatetime=end_at.strftime("%Y%m%d%H%M%S"))
    with client.stream(
        "GET",
        GDELT_DOC_URL,
        params=params,
        follow_redirects=False,
        timeout=httpx.Timeout(GDELT_READ_TIMEOUT_SECONDS, connect=GDELT_CONNECT_TIMEOUT_SECONDS),
        headers={"User-Agent": "LANES-NewsDiscovery/0.1 (+https://github.com/pu-roi/LANES)"},
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
    results = payload.get("articles") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        raise ValueError("Search response has no article list")
    return results[:MAX_RESULTS_PER_QUERY]


def search_open_article_leads(
    article_url: str,
    title: str,
    excerpt: str,
    client: httpx.Client,
    published_at: datetime | None = None,
    include_event_context: bool = False,
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

    def collect(query_kind: str, query: str, start_at: datetime | None = None,
                end_at: datetime | None = None) -> bool:
        nonlocal original_found, retry_after_seconds
        try:
            raw_results = _search(query, client, start_at, end_at)
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
    if (include_event_context and not errors and published_at is not None
            and not any(hit.relationship == "possible_other_source" for hit in hits)):
        publication = published_at.replace(tzinfo=timezone.utc) if published_at.tzinfo is None else published_at.astimezone(timezone.utc)
        now = datetime.now(timezone.utc)
        places = list(dict.fromkeys(" ".join(match.group().split()) for match in
                                    METRO_MANILA_TERMS.finditer(f"{title[:500]} {excerpt[:5000]}")))[:3]
        if places and now - timedelta(days=90) <= publication <= now:
            place_query = f'"{places[0]}"' if len(places) == 1 else '(' + ' OR '.join(f'"{place}"' for place in places) + ')'
            collect("event_context", f'{place_query} (flood OR flooding OR baha)',
                    max(now - timedelta(days=90), publication - timedelta(days=2)),
                    min(now, publication + timedelta(days=2)))

    return OpenSearchLookup(
        article_url=article_url,
        searched_at=datetime.now(timezone.utc),
        evidence_status="index_links_only_incomplete_article",
        results=tuple(hits),
        errors=tuple(errors),
        retry_after_seconds=retry_after_seconds,
    )
