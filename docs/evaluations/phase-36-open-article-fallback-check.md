# Phase 36: Open article fallback check

> **Checked:** October 01, 2026, 12:59 PM (Asia/Manila)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Scope and result

The staff-only `GET /api/v1/admin/news/candidates/{article_id}/open-leads?retrieve_articles=true` path searches GDELT and can retrieve up to three approved alternate publisher bodies. It does not replace the blocked original or persist alternate evidence. This is an on-demand backend feature; automatic same-event matching and scheduled integration remain unfinished.

## Offline verification

Commands from `backend/`:

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_news_open_search.py tests/test_news_discovery.py tests/test_news_auto_ingestion.py -q -p no:cacheprovider
```

Initial retrieval and malformed-URL repairs passed 55 tests; the final combined suite after the pacing repair passed **70 tests**, with one existing `python_multipart` deprecation warning. `git diff --check` found no whitespace errors.

Coverage includes:

- Staff lookup authentication and candidate provenance checks.
- API serialization of alternate text, publisher ID, fetch time, and review status.
- Original article text, fetch error, review state, and stored article count remain unchanged after retrieval.
- Unapproved or disabled publishers and the original publisher are not fetched as independent evidence.
- At most three alternate articles are requested; off-domain redirects are rejected.
- Malformed indexed URLs are skipped without losing valid results.
- Invalid JSON, invalid article-list shape, oversized responses, and HTTP 429 surface errors.
- A failed title search does not trigger an immediate RSS-phrase search.
- Existing ingestion safety checks continue to reject unsupported activation.

Offline fixtures do not prove that live articles will be accessible, complete, or about the same event.

## Live checks

Read-only network checks used the prior Inquirer title, “Quezon City LGU gives evacuees antibiotics for leptospirosis treatment.” The initial sandbox request returned `ConnectError`; an enabled-network retry returned `ConnectTimeout`. A longer-timeout request reached an HTTP error, and a diagnostic request confirmed **HTTP 429** from the GDELT URL as observed from this environment. No index hits or live alternate bodies were recovered. This does not establish the source of the throttling or prove GDELT is globally unavailable.

The configured GMA news feed succeeded with **HTTP 200**, parsed **15 entries**, and reported no error using the same enabled-network environment. A separate web-tool GDELT open was also unsuccessful. No Cloud Run verification was performed.

## Repairs and remaining work

### Request pacing follow-up (October 1, 12:53 PM)

`news_open_search_service.py` now shares one gate across requests in each process. A successful query is cached for 600 seconds, with at most 32 entries. Uncached requests have a conservative 10-second gap after the previous request completes. Concurrent requests receive a deferred response instead of issuing parallel calls. The normal gap may wait at most 10 seconds in the synchronous endpoint; longer cooldowns return immediately.

Rate limits, including the provider's HTTP-200 plain-text throttle notice, and transient connection/server failures start a 60-second cooldown. Consecutive failures double the delay up to 900 seconds; success resets the failure count. A longer `Retry-After` (seconds or HTTP date) is honored. The lookup returns `retry_after_seconds`, and the API exposes `Retry-After` while retaining existing staff authentication and route limits. Provider bodies and private transport diagnostics are not included in API errors. Retry-After semantics follow [RFC 9110](https://datatracker.ietf.org/doc/html/rfc9110#section-10.2.3); 10 seconds is LANES's conservative policy, not a verified official GDELT quota.

A live request returned HTTP 429. An immediate repeated lookup was stopped locally with a 60-second cooldown; the instrumented HTTP client recorded **one outbound request total**. Thus repeat suppression works against a real failure, but live article retrieval success remains unverified.

A controlled single retry more than 60 seconds later returned `ConnectTimeout` without an HTTP response, and correctly entered a 60-second cooldown. Live index success remains unverified; no further requests were issued for this check.

Tests use a fake monotonic clock, so pacing/cooldown checks do not sleep or contact GDELT. Added coverage includes concurrent in-flight calls, cache expiry/eviction, safe copies of cached results, cached results during another query's cooldown, 60/120/240/480/900-second backoff, longer provider delays, HTTP-date headers, malformed headers, HTTP-200 throttling, server/connection failures, and API retry metadata.

The combined discovery, open-search, and ingestion safety suite after the pacing repair: **70 passed**, with the existing `python_multipart` deprecation warning. Whitespace verification passes.

This is **per-process coordination**. It resets on restart and cannot prevent combined traffic from multiple workers/Cloud Run instances or unrelated users sharing an egress IP. Before scheduled multi-instance operation, design shared coordination using the existing infrastructure; any schema changes require separate approval. No new schema, dependency, or paid service was added.

Malformed URL handling was repaired in `news_open_search_service.py`. HTTP errors now include their status code without exposing the response body; failed searches stop before the immediate phrase fallback. Regression coverage is in `test_news_open_search.py`, with retrieval-option integration coverage in `test_news_discovery.py`.

Before scheduled integration, confirm a successful GDELT lookup from the target runtime after throttling clears, coordinate pacing across replicas if deployed with multiple instances, broaden same-event discovery beyond exact title/excerpt phrases, and validate publication/observation date, location, and flood status from each fetched article. An index-seen time is not an event time. All fetched alternate bodies still require event review.
