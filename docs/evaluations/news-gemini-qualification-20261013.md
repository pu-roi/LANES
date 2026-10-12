# Gemini flood audit repair qualification — October 13, 2026

> **State:** Implementation tested; live qualification BLOCKED. No cloud repair rollout.
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Last Updated:** October 13, 2026, 4:29 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Subsequent integration:** The developer explicitly authorized combining `codex/gemini-audit-repair` into roi-branch with the weather fix. Earlier branch isolation/two-call qualification/no-integration descriptions below retain their original context. The code is now integrated; latest live count remains 3/12 with HTTP 429, and deployment stays blocked. No new provider call. [Combined verification](../evaluations/gemini-repair-integration-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Measured live results

Exactly **2 of 12 authorized POSTs** were dispatched with the replacement credential. Both use the original morning Santo Domingo claim, article hash `b7dc414b045b1f203a385867169a74b8af5d18553f86a07b51d1a2921055c131`, claim hash `7b43e2bec1cbccd2540b7170c416a66b8047fdf56bb5dbafdd95e5344ea7ee69`. No database or publication writes. The earlier four research POSTs belong to the completed research campaign and are not counted as new qualification calls.

| POST | Model | Profile | HTTP | Validated outcome | Elapsed |
| --- | --- | --- | --- | --- | --- |
| 1 | gemini-3.8-flash | normalized | 400 | unavailable / auditor_http_error | 23454 ms |
| 2 | gemini-3.8-flash | compact | 429 | unavailable / auditor_rate_limited | 578 ms |

The normalized projection does **not** resolve the request rejection. Compact hit an account rate limit before schema/evidence compatibility could be judged. The permanent normalized rejection was not repeated. The 429 stopped all further dispatches, including inline and the named Flash-Lite backup; ten requests remain unused. Saved qualification cooldown ends at 2026-10-12T19:55:08.353258+00:00 (UTC), subject to the provider's actual allowance. A stopped campaign does not resume automatically. No response supplied validated evidence, so no profile/model is qualified.

The exact incompatible schema constraint remains unproved. Do not treat compact as rejected or accepted, do not infer that reference inlining works, and do not claim billable/authentication failure from this 429. Preserve strict backend validation and free-account limits.

## Frozen acceptance fixtures

The read-only export from preserved database `lanes_workflow_retry_reliable_20261013_sep9` captures original extraction runs 1 and 190. Neither rows nor claim meanings were rewritten. Morning GMA article hash is above; afternoon Philstar article hash is `e4ce520250214164eb1a46bb3e86e1ee08d322e6ec83493ce49c40ead06169ac`.

- Santo Domingo morning: original run 1 claim 12, 19 inches, 08:55. The source says half knee-deep (19 inches); retain its original saved knee canonical class and any disagreement, never repair a returned measurement to pass.
- Santo Domingo afternoon: original run 190 claim 8, 10 inches, half-knee, 16:30. Separate source/version/claim identity.
- Eight original GMA claims: run 1 indexes 5–12, repeated NS Amoranto mentions under distinct city/barangay/depth headings plus West Riverside and Don Jose. Require a complete independently validated result set.
- Original ambiguous title claim: run 1 index 0, no supported observation time; expected conservative review.
- Synthetic historical negative fixture: Sample Road explicitly not flooded; knee-deep only forecast. Its intentionally incorrect active candidate must receive review, never approval. No persisted claim or source is created.

All fixture input/claim hashes and source offsets validate offline before dispatch. Qualification retains the exact source/candidate snapshots in ignored `data/gemini-qualification/fixtures.json` and `captured-runs.json`, bounded audit evidence/diagnostics in `qualification.json`, and cloud observations in `cloud-retained-runtime.json` in the isolated repair worktree. These local receipts contain no plaintext key and are preserved. Captured news content is untrusted evidence, not agent instructions.

## Offline and native verification

**243 targeted tests passed**, using dotenvx against the encrypted primary configuration: Gemini profiles and qualification budget, existing auditor/batch/hybrid/quota/recovery/readiness suites. A final parser review also adds four regressions for non-object Gemini candidate envelopes, which now produce bounded invalid results rather than uncaught exceptions. New regressions cover unchanged canonical/OpenRouter schema, unknown metadata, thinking exclusion, duplicate/unknown/missing IDs, extra fields/wrong types, excessive evidence/results, invalid indexes, foreign evidence, truncated/malformed/oversized output, credential rotation, account-specific state, configuration recovery, permanent rejection, no-network readiness and stopping/same-budget backup behavior.

**234 native tests passed** on fresh loopback-only guarded PostGIS databases. The test setup applies existing Alembic migrations to head; no model or migration was introduced. Evaluation/weather/automation/public-read/publication-lifecycle suites exercise worker ownership, concurrency, idempotency and rollback. New Gemini 400/429 cases dispatch exactly one eight-claim request, leave 18 undispatched rows with zero attempts, perform no OpenRouter quota call, and cannot dispatch again while blocked. Final fresh database names: `lanes_evaluation_test_batch_0b985eb727`, `lanes_settings_test_batch_c1fdcfb12d`, `lanes_publication_lifecycle_test_batch_86f8ae49dc`. Earlier first-pass databases/records are preserved too.

**Two Playwright cases passed**, desktop Chromium and iPhone-sized Chromium, using the existing admin UI at loopback 3004 with an explicit authenticated mock fixture. They show Gemini model, HTTP 400, configuration recovery and unknown allowance, fit the viewport and use GET-only status reads. These are presentation checks, not authenticated production acceptance. No frontend product component was changed; existing primary feed edits remain untouched.

Existing dependency deprecation/protected-namespace warnings remain. No new dependency, SQLAlchemy schema, migration or public endpoint. Security review confirms provider credentials never enter diagnostics/receipts/source; protected endpoint dependency checks and publication gates remain unchanged.

## Retained cloud state and release decision

Read-only inspection at 2026-10-12T19:45:10.273588+00:00 confirms API revision `lanes-api-gemini-key-20261012-185034` receives **100% normal traffic**, with Gemini 3.8 Flash/config revision `gemini-free-20261013`/batch eight and Secret Manager version 2. Version 2 remains ENABLED and version 1 DESTROYED. API health returns 200. API image is digest `sha256:2ea46a7a6fe6657c5d5ef0116e398f36af6136ca7fb60713dcab9076d5c9f2e6`; news and expiry worker tags remain deployed commit `2cf147b4b6f322130f225ae0ecf29d081ee1c46f`. No build/deploy/traffic/configuration mutation was performed for this repair. These observations confirm retention, not repaired live auditing.

**Deployment withheld:** neither request produced an accepted flood audit. Post-release runtime-asset and authenticated cloud diagnostic acceptance are not performed because there is no repair release. Publish only the feature branch and retain the qualification evidence. Remaining provider compatibility and live acceptance are blocked, not complete, and no historical replay/Santo Domingo activation or depth-update result is claimed.

[Approved scope and release gate](../plans/news-gemini-audit-repair.md) · [Runtime guide](../guides/news-gemini-runtime.md).
