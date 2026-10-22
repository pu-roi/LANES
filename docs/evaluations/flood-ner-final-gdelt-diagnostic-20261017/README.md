# Final GDELT diagnostic — October 17, 2026

The hardening is complete; **the diagnostic was blocked locally before dispatch: 0 outbound GDELT GETs**, outcome `not_contacted_pre_dispatch_guard_failure`. There is no new provider response. The sole diagnostic operation is closed; no retry was made after its local guard failure. Stop GDELT troubleshooting after this task. No publisher request, article capture, passage selection or further acquisition was performed.

The proposal remains **345 training / 60 validation / 42 conditional test passages**, short **six English and twelve Taglish positive test passages**. The jointly compatible witness remains 21 English positives + three genuine negatives and 15 Taglish positives + three genuine negatives. A metadata response cannot qualify a passage or establish readiness. References remain AI-assisted silver; no human gold verification or model improvement is claimed.

## Architecture and request controls

Changes stay inside the [offline adapter](../../../backend/training/flood_ner/bounded_discovery.py) and [focused tests](../../../backend/tests/test_flood_ner_bounded_discovery.py). Timing, HTTP receipt handling and budget journaling are separate internal responsibilities. No new framework, file moves, production ingestion changes or dependency updates.

The adapter now owns its client: `User-Agent: LANES-NER-Research/1.0`, `Accept: application/json`, verified TLS, 30-second HTTPX timeouts, redirects disabled and transport retries zero. Public discovery calls no longer accept an arbitrary client. Mock transport/clock replacement is limited to constructed tests; none is used for the live diagnostic. Old frozen private driver scripts remain historical and must not be rerun against the changed interface.

A persistent exclusive pacing gate is shared by research sessions within this checkout. The first dispatch requires a 30-second quiet window; subsequent cooldowns start at response completion. The later supported provider deadline wins. A wait over 60 seconds defers with an earliest UTC time, without a request or scheduler. Hash-chained pacing state survives restarts; competing writers, unresolved interrupted sends, malformed timing and backward wall-clock movement stop dispatch. This controls our checkout's research traffic, not unrelated programs or machines sharing its public IP. **Thirty seconds is a conservative project setting, not a verified GDELT service requirement.**

The explicit final diagnostic authorization binds the latest predecessor journal and imports 204 actual raw identities, four uncertain slots and 66 article requests. Its persistent claim is single-use across outputs/restarts; the ordinary no-continuation-chain guard remains. A process-local launch grant is consumed at the first diagnostic operation, including preflight rejection; reopening an initialize-only journal cannot restore permission. It reserves three additional URL slots before possible I/O. Its request count is consumed on dispatch, including timeouts; success does not permit a second call. Publisher transport is explicitly forbidden in this mode.

## Retry and response evidence

The diagnostic operation elapsed **30.172 seconds**, but the guard did not validate dispatch. There is **no response**, so Retry-After/header presence and provider deadline are **unavailable**, not evidence that a responding server omitted them. No discovery reservation or pacing-start event was written. The final authorization claim remains closed. See the [curator aggregate](curator-aggregate-status.json) for sanitized diagnostic details.

The initial wrapper retained the exception type (`BoundaryError`) but lost its message. Therefore the exact original guard is unknown. Read-only postmortem found a platform-sensitive condition: this Python's `time.monotonic()` uses Windows GetTickCount64 with 15.625 ms resolution, while the original elapsed-wait comparison allowed only 1 ms. A constructed test reproduces that false-failure condition; it does not prove which guard aborted the original operation. The helper now uses high-resolution `perf_counter()` plus a bounded remaining-wait loop instead of treating a short clock quantum as a failed quiet window. Backward clock movement still cannot shorten the wait or exceed the 60-second cap. The correction was tested with mocks only; **no live request or second diagnostic operation followed**. The exact dispatched source and its original test/gate hashes are preserved separately from the corrected source. A separate real-clock check of the corrected path waited 30.0005 seconds and reached one HTTPX MockTransport response, with zero real network requests. This validates the local timing path; it is not a GDELT response or a live retry.

Status, header receipt timestamps and a finite header allowlist are saved before streaming the body: Retry-After, Date, Age, Cache-Control, Content-Type and recognized RateLimit/X-RateLimit fields. Cookies, credentials and unknown headers are excluded. Valid Retry-After delay-seconds and HTTP dates are supported; missing is recorded, not fabricated. Conflicting or malformed values prevent another dispatch. Partial bodies retain their header receipt and received bytes, marked incomplete; the 4 MiB cap does not imply a complete capture of an oversized or interrupted stream.

| Accounting | Outcome |
| --- | ---: |
| Diagnostic GETs | 0 |
| New publisher requests / captures / proposals | 0 / 0 / 0 |
| Actual cumulative exposed URLs | 204 |
| Total uncertain reserved slots | 4 |
| Conservative possible exposure / ceiling | 208 / 300 |
| Remaining unreserved URL slots | 92 |
| Cumulative article requests / remaining attempts | 66 / 34 |

All received identities are counted before relevance filtering; raw aliases remain private. Earlier uncertain slots are never automatically refunded. The historical 202/200 breach stays recorded. Remaining numerical allowance is not authorization for another request.

## Verification and research limits

**101 focused unit tests pass; one Windows symlink test skips**, including 87 adapter tests. The dispatched build had previously passed 96 focused tests / one skip; the final corrected build adds three clock-quantum/rollback regressions and two launch-ownership regressions, with no live rerun. Constructed tests cover owned headers/timeouts, no arbitrary-client bypass, pacing across sessions/restarts, completion-based cooldowns, simultaneous writers, interrupted sends, tampered pacing state, backward clocks, header preservation before body timeout, allowlisting, duplicate/conflicting Retry-After, HTTP dates, deferral without reservation, inherited debits, stale checkpoints, aliases, over-return, redirects and single-use success/failure/reopen behavior.

All **6,219 protected coordinator files** and **412 curator predecessor files** verify unchanged. The separate read-only postmortem preserves all 13 completed diagnostic/pacing/claim files and passes three constructed mock cases on the exact dispatched source, with zero real HTTP transport or waits. It confirms no fake-clock, sleep or transport replacement in the original driver; the original exception message cannot be recovered. Original datasets, previous journals/claims, reviews, tokenizer, models and scores remain preserved. Previous complete-reference validation (92 records / 116 spans) is reused as predecessor evidence, not presented as a new annotation review or model run. No new article reference was scored. The development tokenizer failure remains held; 12 recorded metadata/helper payloads and scoped history limitations remain unresolved. This task does not claim history completeness or repeat history collection.

Only two curator-approved aggregate/verification files reached the coordinator. Individual fresh-test identities, texts, titles, labels, raw responses and journals remain private and Git-ignored. The [operator guide](../../guides/ner-bounded-test-discovery.md) records the updated interface and stop boundary.

The [official GDELT API documentation](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) documents ArticleList/JSON/MAXRECORDS, not a guarantee that our request will succeed. A [client maintainer's User-Agent discussion](https://github.com/alex9smith/gdelt-doc-api/issues/22) motivates honest identification. Another project's [report of widely spaced 429s](https://github.com/koala73/worldmonitor/issues/5843) suggests service-side constraints can occur; its overload diagnosis is that author's hypothesis, not official confirmation of our cause. Timing follows [HTTP Retry-After semantics](https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after); transport settings follow [HTTPX documentation](https://www.python-httpx.org/advanced/transports/). Neither the header change nor longer spacing is claimed as a guaranteed fix.

## Return to NER planning

**Stop GDELT troubleshooting here.** Plan a separately scoped bounded non-GDELT route or directly supplied source identities for the remaining eighteen positive test passages, while resolving material source-use/reference/history requirements. Do not weaken language/positive quotas, source caps, non-overlap or independence guards. Admission, freeze, qualified exports and desktop GPU handoff remain separate work after the independent-test requirements pass. **The desktop can remain off.**

No public API or database schema changes; no article collection, corpus admission, partition freeze, test sealing, training export, inference, training, upload, commit or push occurred.

Evidence: [safe aggregate](curator-aggregate-status.json), [safe curator verification](curator-verification-manifest.json), [safe postmortem](postmortem-aggregate-status.json), [postmortem verification](postmortem-verification-manifest.json), [readiness](readiness.json), [tool/preservation verification](verification.json), [hash manifest](metadata_hash_manifest.json). [Predecessor outcome](../flood-ner-controlled-retry-20261017/README.md) remains unchanged.
