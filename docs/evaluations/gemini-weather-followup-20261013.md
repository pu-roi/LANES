# Gemini limits and public weather error follow-up — October 13, 2026

> **Last Updated:** October 13, 2026, 4:21 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Weather repair implemented locally on roi-branch; news live qualification blocked. Developer-authorized publication to roi-branch; no new deployment.

## Branch scope

The preceding approved plan required an isolated feature worktree based on the deployed commit and feature-branch publication. That explains `codex/gemini-audit-repair`, whose pushed head is `df16a02`. It was not merged into roi-branch, and its schema/circuit changes remain unqualified for production. The developer now prefers roi-branch; this weather repair is made directly in the primary roi-branch checkout. Existing encrypted configuration, feed/sidebar/local-news edits and earlier documentation remain preserved. No extra branch or automatic integration of the unqualified news repair.

## Actual news check and worker evidence

After the recorded cooldown expired, the developer explicitly requested a fresh gathered-news check. One additional live POST used Gemini 3.8 Flash and the compact schema against the exact captured Santo Domingo morning claim; it returned **HTTP 429 in 625 ms**, `auditor_rate_limited`, with no validated evidence. The original ledger is preserved before continuation, and the shared count remains **3 of 12**, not reset. Stop again; no model/profile switch, weather generation probe or publication/database writes. Original single/eight-claim evidence qualification and automatic zone/depth-update replay remain unverified.

Read-only Cloud Logging inspection finds the scheduled worker at `2026-10-12T19:00:48.691788Z` (October 13, 03:00 Manila) completed extraction for **11 captured articles**, zero failed extractions, **zero audit requests/claims dispatched**, zero publications and zero footprints activated. Worker completion proves that stage ran, not that Gemini auditing succeeded. Earlier 16:00 UTC worker also dispatched zero audits. The read receipts are ignored under `data/gemini-weather-followup/`.

## Official Google documentation and project measurements

Google's [rate-limit guide](https://ai.google.dev/gemini-api/docs/rate-limits) distinguishes requests/minute, input tokens/minute and requests/day. Limits are project-scoped; replacing a key in the same project does not reset allowance. Daily quotas reset at midnight Pacific, **15:00 Manila on October 13**. This is the documented reset time, not proof that this 429 was daily exhaustion.

Using the documented [Service Usage consumer-quota API](https://docs.cloud.google.com/service-usage/docs/reference/rest/v1beta1/services.consumerQuotaMetrics/list), a read-only authenticated GET for issuing project `gen-lang-client-0723504039` / `32816280739` returns these effective free-tier limits:

| Model | Requests/minute | Requests/day | Input tokens/minute |
| --- | ---: | ---: | ---: |
| Gemini 3.8 Flash | 5 | 20 | 250,000 |
| Gemini 3.5 Flash-Lite | 15 | 500 | 250,000 |

These are this project's **configured limits**, not current remaining counters or guaranteed capacity. A Cloud Monitoring read returns no quota-usage series; absence does not mean zero consumption. The saved bounded 429 audit receipt contains no QuotaFailure detail, so daily vs minute vs token exhaustion remains unproved. Check actual Gemini 3.8 usage in [AI Studio's rate-limit dashboard](https://aistudio.google.com/rate-limit), selecting this issuing project. Free availability does not imply unlimited requests. Billing stays disabled; no billing, quota override or key changes were made. Flash-Lite's larger configured limit is not permission to bypass the 429 or promote an unqualified model.

The [troubleshooting guide](https://ai.google.dev/gemini-api/docs/troubleshooting) recommends bounded backoff for transient failures and avoiding retries for permanent request errors. [Google RPC RetryInfo/QuotaFailure](https://docs.cloud.google.com/service-infrastructure/docs/service-control/reference/rpc/google.rpc) provides structured retry delays and violated-quota details. The new weather service uses bounded RetryInfo and Retry-After; a specifically identified free daily quota waits until Pacific midnight. Unknown 429s pause 15 minutes; permanent request/auth/billing rejection pauses at least an hour. The original stopped news campaign remains stopped.

The [structured-output guide](https://ai.google.dev/gemini-api/docs/structured-output) documents a JSON Schema subset and warns about large/deep schemas. The [generateContent reference](https://ai.google.dev/api/generate-content#v1beta.GenerationConfig) documents refs/defs/anyOf/additionalProperties and inclusive bounds; the separate OpenAPI `responseSchema` contract must not be confused with JSON Schema. An offline allowlist audit of all three implemented projections finds **no undocumented keywords**. This does not prove the compiler accepts the full combination or resulting evidence. Normalized still returned 400; compact is untested for compatibility because both compact dispatches returned 429; inline remains untested. Do not invent a specific rejected keyword. The current reference also recommends `responseFormat` for deprecated response-format fields; a future controlled comparison can test that envelope while retaining the canonical validator, after allowance is confirmed. No new endpoint transport or model fallback was silently selected.

## Public weather repair

The reported screenshot is a separate endpoint: `/api/v1/weather/insights` directly hardcoded `openrouter/free`, forwarded the entire upstream failure via HTTPException.detail, and the public modal rendered that detail. Changing the news provider therefore did not change weather insights.

- Move generation into `weather_insights_service.py` with server-only `GEMINI_API_KEY`; independent `LANES_WEATHER_GEMINI_MODEL` defaults to Gemini 3.8 Flash. No OpenRouter generation/quota endpoint remains in this weather path. No implicit model fallback.
- Preserve response shape `{insights:{storm_risk,environment},model}` with strict two-string output validation. Bound request forecast/location/numeric fields, upstream bytes and deadlines, reject truncated/incomplete/invalid output, and ignore explicit thinking text.
- Cache matching first-four-hour explanations for 15 minutes, bounded to 64 entries per process. Single-flight locking avoids duplicate concurrent calls. Credential/model identities scope bounded cooldowns; rotation does not inherit a previous credential's block. These in-memory controls do not fabricate project allowance or coordinate all Cloud Run instances.
- Public failures return only `AI weather insights are temporarily unavailable. You can still view the forecast and chart legend.` with a safe status and Retry-After. No account IDs, billing remedy, provider bodies, keys or tracebacks.
- Frontend never renders arbitrary error details, including failures from an older deployed backend. It surfaces the short message, keeps the legend available, uses shared buttons, bounds its client deadline, disables generation without forecast data and prevents duplicate loading clicks.
- Responsive verification found the desktop popover extended below the viewport. Fixed viewport positioning and responsive height/scroll limits preserve the mobile navigation/safe-area offset and keep the full panel inside both viewports.

## Verification and release status

The final dotenvx backend run passes **151 tests**: 28 new weather cases plus the existing auditor, batch and hybrid suites. Weather regressions cover safe HTTP failures, caching/concurrency, rotation, malformed/truncated/oversized/thinking output, invalid forecasts, public endpoint response/header, structured retry metadata and daily reset. TypeScript and scoped component/test ESLint pass. Responsive browser checks cover safe public errors, mocked Gemini success and absent forecast on desktop/mobile. Browser fixture responses are explicit mocks, not live generation acceptance. The final Playwright run passes **all six cases** (three per viewport). Earlier cold-build/navigation failures and a real desktop overflow failure were diagnosed before the final run; tests now wait for DOM content rather than all page resources, and the panel overflow is repaired. Verified screenshots remain in ignored frontend/test-results. No new dependency, SQLAlchemy model, migration, database writes or public endpoint.

No additional real weather generation request followed the news 429. The local change removes the public diagnostic leak and selects Gemini, but real generated weather text remains unverified while the project is rate-limited. The developer subsequently authorized publication to roi-branch. Cloud deployment remains pending; the hosted landing page is not yet updated. Preserve production Secret Manager version 2 and the retained backend images. The original news repair release remains gated on actual validated single/eight/negative evidence. Project quota/capacity and schema compatibility are separate unresolved requirements.

## Developer-authorized roi-branch publication

The developer subsequently requested the senior-planner update and push to roi-branch. Preserve the earlier research/live results and existing primary edits; publish all current checkout changes according to AGENTS.md. The package contains the weather repair/tests, prior encrypted backend runtime configuration, all Gemini research/runtime/publication documentation and three existing feed/sidebar/Local Updates presentation edits. Dependency manifests and SQLAlchemy/Alembic definitions are unchanged; there are no new migrations to apply. Sensitive dotenv assignments are encrypted, with private key/receipt/test output files ignored. No extra inference, historical replay, unqualified auditor integration, or cloud deployment is authorized by this Git publication. Final commit/remote verification is recorded in the chat once the push succeeds. [@roicambe](https://github.com/roicambe) (Roi Cambe)
