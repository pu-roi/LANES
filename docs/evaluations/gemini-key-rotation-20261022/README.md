# Personal Gemini key — rotation withheld after HTTP 400

> **Last Updated:** October 22, 2026, 8:38 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Subsequent decision:** the user withdrew personal-key replacement and chose the existing LANES-account credential. A read-only check confirms version 2 is enabled and selected by all three consumers; version 3 remains stored but unused. No key was deleted or provider request made. The execution record below preserves the attempted rotation; its conditional personal-key rollout is no longer the active plan.

The user authorized replacing the Gemini credential for all cloud Gemini features, with news acceptance first, weather acceptance second and API promotion only after both pass. **The new key is stored in Secret Manager version 3, but the rotation is not live.** The single authorized news request returned HTTP 400; tests stopped and both worker bindings were restored to version 2. No API canary was created or promoted, and no weather-generation request was made.

## Executed and verified

- Added a new version of existing secret `lanes-gemini-api-key` in deployment project `lanes-project-508809`; verified its contents against the supplied credential using an in-memory comparison. Plaintext was not written to source, local credential files, command arguments or receipts. The existing secret IAM policy was reused; no project/billing/model change was made.
- Temporarily pinned `lanes-news-discovery` and `lanes-news-verified` to version 3, preserving all other task settings. Discovery remained paused; the manual job retained read-only default, disabled general execution, one CPU/3 GiB, 600 seconds and zero automatic retries.
- Execution **`lanes-news-verified-5bnpz`** used the actual version-3 binding and unchanged `gemini-3.5-flash-lite` configuration. Read-only cloud preflight passed. The fictional source-authored-mention probe made exactly one generation request and received **HTTP 400**, safe code `native_resolution_http_error`, with no retry, neural inference or database write. No accepted structured correction is claimed.
- The probe deliberately excludes provider error bodies from logs/receipts. HTTP 400 alone does not establish whether the supplied credential, provider request/schema or another request condition caused rejection. It is not evidence that the key is invalid or that billing succeeded. No second request was made to isolate the cause.
- Followed the agreed stop condition: skipped weather and public API rollout. Restored both worker bindings to version 2 and verified their full task configuration against baseline. All three consumers now use version 2: `lanes-api`, `lanes-news-discovery`, `lanes-news-verified`. Versions 2 and 3 remain enabled; no key/version was destroyed.

## Preservation and acceptance limits

API revision **`lanes-api-gemini-20261022-v4`** still serves 100% of backend traffic. Models, images, resources and unrelated environment/task settings match baseline. The historical seed job is unchanged. News scheduler and collection/processing/publication remain paused; both automatic expiry and Pasig ML expiry remain OFF, as the user configured them.

Complete database row fingerprints, constraints, trigger states and sequences match the pre-operation snapshot. Retained: eight accounts, 37 community posts, 174 articles and 224 source versions. Flood events/reports/zones and extraction runs remain empty. Authenticated news/history/zone GETs return their existing empty states; collection returns 174, and unauthenticated admin access returns 401. Final checks make no Gemini requests. No application/UI/schema/dependency change, article replay or seeding occurred.

The news attempt was bounded by one request, 30 seconds and the existing output limit; its conservative reservation is US$0.03 within the agreed US$1 news-pilot allowance. No actual charge or balance is asserted without billing evidence. Weather spending remains outside that pilot allowance if the personal key is later activated for all features.

## Evidence and next gate

Private access-restricted directory: `data/gemini-key-rotation-20261022/`. It retains deployment baselines, new-version confirmation, exact execution/log receipts, dispatch marker, recovery confirmation, final configuration and database snapshots. [Sanitized summary](summary.json) contains IDs, safe outcomes and receipt hashes without the credential.

Investigate the failed request before another explicitly controlled provider test. Do not promote version 3 or run the weather/seeding stages as though news acceptance passed. After successful news and weather acceptance, pin the same tested secret version across all three consumers and promote the API. Retain version 2 and the previous serving revision for rollback.
