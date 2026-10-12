# Repair and qualify Gemini flood auditing

> **State:** Implementation verified locally; live qualification blocked, rollout withheld.
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Last Updated:** October 13, 2026, 3:49 AM

## Scope and architecture

Isolated branch `codex/gemini-audit-repair` starts at deployed commit `2cf147b4b6f322130f225ae0ecf29d081ee1c46f`. Preserve primary frontend edits, encrypted configuration, frozen articles, original extracted claims and historical databases. No new HTTP endpoints, dependencies, database models or migrations.

Gemini alone receives an immutable wire-schema projection. Profiles are explicit: normalized removes `pattern` and maps integer `exclusiveMaximum: 256` to `maximum: 255`; compact also removes array length constraints; inline also expands acyclic local references and removes titles/descriptions. Preserve required fields, enums, nullability, object closure and references in the first two profiles. Default `LANES_NEWS_GEMINI_SCHEMA_PROFILE=normalized`; include profile and `gemini-json-schema-v1` in audit policy/circuit identity. Normal workers never switch profiles or models automatically.

Canonical strict Pydantic models, identity/occurrence/parent evidence checks, index/array/response-size limits and publication gates remain unchanged. Diagnostics parse Gemini modelVersion/usageMetadata/responseId/finishReason; explicit thinking parts do not enter final JSON. Missing metadata remains unknown. Gemini credential owns its private account identity; separate existing settings rows preserve OpenRouter cooldowns. Gemini has no fabricated quota counters and never calls OpenRouter quota HTTP. Permanent request errors block the specific model/configuration for 60 minutes; transient retry/worker ownership behavior remains intact.

## Acceptance checklist

- [x] Three adapter profiles, canonical immutability and OpenRouter compatibility.
- [x] Metadata/thinking parsing, credential rotation, configuration cooldown recovery and provider diagnostics.
- [x] Offline readiness; explicit synthetic historical live probe only, no DB/publication imports.
- [x] Adversarial ID/type/evidence/array/index/truncation/size regressions.
- [x] 239 targeted dotenvx tests, 234 fresh guarded local PostGIS checks including migration-to-head/ownership/idempotency, two desktop/mobile diagnostic cases.
- [x] Frozen original Santo Domingo 19-inch 08:55 and 10-inch 16:30 claims plus repeated-name eight-claim batch; separate ambiguous and synthetic negative cases. Shared persistent 12-POST ledger, reserve before dispatch, 60-second deadlines, no automatic HTTP retries.
- [x] Execute permitted live qualification and stop on account errors. Normalized returns 400; compact returns 429. Stop after two POSTs, with ten unused; inline and backup remain untested.
- [ ] Qualify correct validated single claims, all eight batch claims and conservative negative/ambiguous results. Blocked by account rate limit; HTTP 200 alone would not pass.
- [ ] Deploy only a qualified model/profile through existing Cloud Build, match API/news/expiry images, verify actual 100% revision/assets/health/authenticated diagnostics. Withheld because qualification did not pass.

## Live-request rules and release gate

One shared 12-POST ceiling includes both named models, every profile and every dispatched attempt, including transport failures. Gemini 3.8 Flash first; only model-specific unavailability permits Gemini 3.5 Flash-Lite within that budget. Stop on authentication, billing or 429; never switch models to evade account limits. On 400, move to the next explicit qualification profile without repeating that rejected configuration. A terminal ledger cannot be reset by rerunning the command. Do not continue the stopped qualification automatically when cooldown expires; any additional campaign needs an explicit budget and retained previous receipts.

Cloud Billing is disabled for issuing project 32816280739. Retain replacement Secret Manager version 2; never revert to version 1. A successful release must select matching local/cloud model/profile/configuration revision before traffic promotion and inspect the actual serving revision, not only a mutable template. Existing Cloud Build prepares the API with no traffic, updates both workers and promotes its exact named revision. This campaign did not qualify any selection, so cloud/local runtime selection and source deployment remain unchanged.

Full historical replay and Santo Domingo automatic zone/depth-update acceptance are separate follow-up work. This repair does not claim them.

[Results](../evaluations/news-gemini-qualification-20261013.md) · [Research](../research/gemini-news-audit-invalid-argument-20261013.md) · [Runtime guide](../guides/news-gemini-runtime.md).
