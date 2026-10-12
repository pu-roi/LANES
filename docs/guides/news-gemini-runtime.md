# Gemini news auditor runtime

> **Last Updated:** October 13, 2026, 4:56 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Latest bounded research:** Current Google failure is confirmed daily Flash quota exhaustion (20/day); do not keep retrying before reset. The shared ledger reached 12/12 including user-authorized Groq alternatives. Groq passed captured samples but remains research-only: no provider selection/secret/worker/cloud change, recurring batch and remaining acceptance pending. [Official docs and measured results](../research/gemini-groq-free-auditing-20261013.md).

## Current integrated source and retained runtime

Gemini news-auditor repair `df16a02` is integrated into roi-branch alongside weather repair `680118b`. Canonical evidence validation/publication gates remain strict. Both Gemini schema and weather settings are retained in `.env.example`; encrypted runtime configuration and existing feed edits are preserved. Live qualification remains blocked at shared 3/12 POSTs; no deployment or additional inference. The original private worktree/request ledger is retained; merging the source does not reset its shared count or authorize a new probe.

`LANES_NEWS_GEMINI_SCHEMA_PROFILE` defaults to `normalized`; `compact` and `inline` are explicit qualification profiles. Adapter revision is `gemini-json-schema-v1`. Profile/revision enter news policy and model circuit identity, while credential identity owns Gemini account cooldowns. Normal workers never switch models/profiles automatically. Strict backend validation, evidence indexes/occurrence/parent checks, response bounds and publication gates remain unchanged.

Offline readiness from backend: `dotenvx run -f .env -- python -m scripts.check_news_auditor`. The default makes no HTTP or DB call; `--probe` is explicit historical synthetic inference. Read-only qualification uses `python -m scripts.qualify_news_gemini --fixtures <frozen-json> --ledger <persistent-json>` under dotenvx; a stopped ledger cannot be silently resumed/reset. Follow the retained [release gate](../plans/news-gemini-audit-repair.md) and [initial qualification](../evaluations/news-gemini-qualification-20261013.md), with latest 3/12 follow-up above the older two-request report. [Merge acceptance](../evaluations/gemini-repair-integration-20261013.md).

All separate/unmerged branch descriptions below are earlier records; the current source is combined, and the cloud remains unchanged.

## Latest user-requested recheck and weather scope

The isolated auditor repair was pushed to `codex/gemini-audit-repair` (`df16a02`) according to its approved feature-worktree plan; it is not merged into roi-branch or deployed. The fresh explicit news recheck after cooldown returns HTTP 429, so shared qualification count is 3/12 and live auditing remains unqualified. Latest scheduled extraction completed 11 articles but zero audit calls. Direct issuing-project free quotas for Flash are 5/minute, 20/day, 250,000 input tokens/minute; remaining use is unknown. Daily reset is midnight Pacific (15:00 Manila on October 13).

Weather insight generation was a separate hardcoded OpenRouter endpoint. Its Gemini/safe-error/cache/cooldown repair now resides locally on roi-branch with your existing edits preserved. No real weather probe follows the 429, no billing change, no integration of the unqualified auditor branch or cloud deployment. The developer authorized Git publication of the primary roi-branch changes. [Actual checks and official Google guidance](../evaluations/gemini-weather-followup-20261013.md). Earlier configuration/research entries below are history.
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Current configuration

The developer authorized replacing the active OpenRouter auditor with Gemini locally and in Google Cloud. The replacement credential is installed and basic generation works. LANES structured-audit qualification is blocked by HTTP 400, not billing.

| Setting | Current value |
| --- | --- |
| `LANES_NEWS_AUDITOR_PROVIDER` | `gemini` |
| `LANES_NEWS_AUDITOR_MODEL` | `gemini-3.8-flash` |
| `LANES_NEWS_AUDITOR_CONFIG_REVISION` | `gemini-free-20261013` |
| `LANES_NEWS_AUDITOR_BATCH_SIZE` | `8` |
| Cloud credential | `GEMINI_API_KEY` references Secret Manager `lanes-gemini-api-key`, version `2` |

The normal local launcher uses `dotenvx run -f .env` from `backend/`; the Gemini key and default settings are encrypted in the tracked dotenvx file. Never commit decrypted values or `.env.keys`. Existing ignored Linux/replay credential handoffs now select Gemini. The running port-8004 historical preview was recreated with the same image, bind mount, database and September 9 final read clock; its new receipt is `gemini-free-20261013-sep9-current-code-preview-clock.json`. The original preview container is retained stopped as `lanes-reliability-preview-sep9-v20-before-gemini-20261013`. Restart attempts initially omitted the Python entrypoint and then hit the existing immutable-clock safeguard; both were corrected before health verification.

Cloud Run `lanes-api` and `lanes-news-discovery` in project `lanes-project-508809`, region `asia-east1`, have the same provider/model/revision and secret binding. API revision `lanes-api-gemini-key-20261012-185034` receives 100% serving traffic. The date in that generated revision name is UTC. Initial service-template updates left traffic pinned to an older OpenRouter revision; direct revision inspection caught this, and a new explicitly named revision was verified before traffic promotion. Root `cloudbuild.yaml` preserves runtime settings on subsequent image deployments; local dotenv files are excluded from container/build inputs.

This is a runtime configuration change, not a source-image release. The initial configuration inspection observed image `bed589028eccced74713ea9910e53b0bfe943d2a` with v5. The later read-only October 13 investigation confirms API/worker digest `2ea46a7a6fe6657c5d5ef0116e398f36af6136ca7fb60713dcab9076d5c9f2e6`, deployed commit `2cf147b4b6f322130f225ae0ecf29d081ee1c46f`, whose v11 audit/schema/evaluation code matches local checkout `4444778`. Those image changes were not performed by the credential/research task. Existing OpenRouter transport code and historical evidence remain available for compatibility, but the active selection does not fall back to OpenRouter. No migration, new dependency, provider-generated flood approval or historical replay was performed.

## Replacement key verification — October 13, 2026, 2:56 AM

The developer supplied a replacement key associated with project number `32816280739` and confirmed deleting the original issuing key in AI Studio. The local encrypted Gemini value, both existing ignored credential handoffs, running historical preview, Cloud Run API serving revision and news worker use the replacement. Secret Manager version 2 is enabled; version 1 containing the old key is destroyed after verification of both runtime bindings. The deployment project remains `lanes-project-508809`; its hosting billing was not changed.

New-key authentication and a minimal `gemini-3.8-flash` generation return HTTP 200 with normal STOP completion. This resolves the old key's prepaid-credit error; it does not independently establish the new project's billing tier. Both cloud API and historical preview health return HTTP 200. The preserved stopped pre-Gemini preview container contains no Gemini credential, and the replaced Gemini container was removed rather than retaining the old credential.

A real current-code LANES single-candidate audit returns HTTP 400, `INVALID_ARGUMENT`, with the generic message "Request contains an invalid argument." A separate bounded diagnostic reproduction confirms that result. No successful structured evidence result, eight-claim audit or source publication is claimed. Diagnose the actual Gemini request/schema compatibility before treating flood auditing as operational; no further provider call or historical replay was performed after that diagnostic result. Existing source checks, dependencies and migrations remain unchanged. The earlier 123 deterministic checks remain valid for unchanged source, but do not replace live acceptance. No Git push.

## Structured-request investigation

[Internet evidence, controlled comparisons and proposed repair](../research/gemini-news-audit-invalid-argument-20261013.md) isolate rejection to the full response-schema path. The same request with a minimal response schema succeeds; array-bound isolation hits provider-demand 503 and remains inconclusive. Four research POSTs made no DB/publication writes. No backend fix or live flood-audit acceptance is claimed.

## Original-key verification and billing blocker (historical)

- Gemini model listing returned HTTP 200, confirming authentication and listing `gemini-3.8-flash`.
- One real LANES single-candidate audit returned HTTP 402, `RESOURCE_EXHAUSTED`; a separate minimal generation request confirmed the same billing response. The provider stated: "Your prepayment credits are depleted." No eight-claim live probe followed the failed first audit, and no claim result was persisted.
- The local and preview configurations load Gemini successfully with no configuration error. Cloud serving-revision inspection confirms Gemini and the secret reference. Cloud API and local preview health return HTTP 200.
- The existing auditor, batch and hybrid suites passed 123 tests using the required dotenvx launcher. An initial invocation without dotenvx failed while parsing the encrypted batch setting; the corrected launcher passed without source/test changes. These deterministic tests do not establish real model accuracy or live batching success.
- Santo Domingo automatic activation and the 19-inch to 10-inch scenario remain unverified. Switching providers does not satisfy those acceptance criteria.

The original key was blocked by depleted prepaid credits before replacement. Its issuing key has since been deleted by the developer. Google documents HTTP 402 when an account's prepaid balance is depleted; Gemini credits are separate from other Cloud service credits. [Gemini billing](https://ai.google.dev/gemini-api/docs/billing#prepay), [Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash).

After resolving the current structured-request rejection, perform a bounded real single/eight-claim qualification using the actual LANES schema and evidence checks. Then decide the separately scoped historical replay and matching source-image release. Do not reset terminal evaluations or weaken evidence gates to obtain a successful result. No Git push is part of this configuration task.
