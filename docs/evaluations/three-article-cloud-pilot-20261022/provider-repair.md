# Gemini request repair and cloud acceptance

October 22, 2026, 10:20 PM Asia/Manila. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Result

The corrected manual worker passes a real Gemini request and canonical backend acceptance. Matching API revision **`lanes-api-gemini-fix-20261022-v5` serves 100% of backend traffic for navlanes.live**. Protected canary and serving API reads pass. No article processing, neural inference or database writes were performed by these checks; the three-article pilot remains unstarted. News automation remains paused, expiry OFF, historical seed disabled, and the spending ledger stopped pending the next inspected stage.

## Cause and controlled comparison

The original request's 400 is reproducible with its exact payload. Improved error capture confirms Google returns only `Request contains an invalid argument.` / `INVALID_ARGUMENT`, without field violations or explanatory details. The diagnostic handler previously discarded these fields; that defect is repaired, but the new response still does not expose Google's internal compiler explanation.

The next comparison changes **only array cardinality limits in `responseJsonSchema`**, using the existing explicit `compact` profile. It keeps the key, model, fictional full article, proposed targets, instructions, token cap and other generation parameters unchanged. A transport assertion verifies the complete outgoing request against that one-variable projection before forwarding. The original payload SHA is `1480440e53c18e43ef29bac667a79eb45ffbe667bbc1b0d3c33630bd2c4fe5cc`; the comparison SHA is `5af070462ce9462801d4530c478e69ea8d11f20462762dbe069212825be1fe3e`.

Google accepts the comparison with HTTP 200. This isolates the rejected schema's array constraints as the request compatibility problem, consistent with Google's documented [nested-array schema complexity limitation](https://ai.google.dev/gemini-api/docs/structured-output#limitations). It does not identify a particular internal compiler threshold. The 8,192-token cap, funded LANES key and model are retained.

That accepted response then fails the local exact-target check. The prior wire schema allowed arbitrary target strings and output cardinality; instructions alone had not produced the required set. The raw unsuccessful response was not retained, so its exact missing/unexpected/duplicate composition is unknown. The repair constrains target IDs to the current batch, constrains only the outer response count to that batch's size, and explicitly retains unsupported context-only city rows. Nested evidence-array bounds remain absent from the compact wire schema. Strict local Pydantic limits, exact target-set/duplicate checks, source-quote validation and independent saved-result recomputation remain enforced. New target-mismatch diagnostics retain bounded counts, without model-generated facts.

## Preserved request outcomes

| Execution | Purpose | Outcome |
|---|---|---|
| `lanes-news-verified-bjlbv` | Earlier original funded request | HTTP 400; retained original failed reservation |
| `lanes-news-verified-nwdv4` | Authorized identical-payload diagnostic | HTTP 400; sanitized generic message retained; no automatic retry |
| `lanes-news-verified-2tdss` | Schema-only comparison | HTTP 200; local `native_resolution_target_mismatch`; no database writes |
| `lanes-news-verified-65rcn` | Repaired adapter and backend acceptance | HTTP 200; one accepted observation at the quoted October 20 10 AM Manila time; saved result recomputed successfully |

These are individually controlled stages, not an automatic retry sequence. No model/account fallback occurred. The last request reports **1,612 input and 429 output tokens**. All four reservations remain in the same concurrency-protected US$1 ledger: **US$0.1225868 conservatively reserved**, not a confirmed provider charge. The total actual bill is unconfirmed. There are no in-flight attempts, and the ledger is stopped with `provider_accepted_article_pilot_not_started`.

## Implementation and verification

- `news_ner_durable/gemini_resolution.py`: explicit per-batch target/count schema and context-row instruction; bounded target-error counts; delegated safe provider diagnostics.
- `news_provider_diagnostics.py`: bounded response reading, redacted message, allowlisted provider status/reasons and field violations. Credentials, unrestricted metadata and headers are excluded.
- `scripts/diagnose_news_gemini_request.py`: immutable, separately authorized single-payload diagnostic with reserve-before-dispatch, zero retries and stopped budget afterward; no SQL or inference.
- **50 focused tests pass**, including full article/evidence handling, unsupported facts, compact oversized-response rejection, no redirects/retries, credential redaction and durable spending controls. No dependency, migration, schema or UI change.
- Linux amd64 image passes seven network-disabled contracts and exact reader descriptor checks. Cloud `lanes-news-verified-vfpsn` passes read-only preflight and the same seven contracts. Cloud real acceptance uses the actual adapter, source validation, read projection and saved-result recomputation, with a fictional authored-mention fixture. It does **not** establish trained-NER accuracy or real-article spatial eligibility.
- Protected canary and promoted serving API reads pass: news lists/counts/pagination, collections, history, analytics/export, spatial/report/moderation empty states, existing account access and unauthorized-admin rejection. No frontend artifact was changed. Populated desktop/mobile article/map verification remains a pilot gate.
- All database table fingerprints, constraints, triggers and sequences match the release baseline. Preserve eight accounts, 37 community posts, 174 articles and 224 versions; extraction runs/events/reports/zones remain zero. Both expiry flags are OFF, news flags/scheduler remain paused, and old seed stays disabled.

## Release and recovery

- Image: `asia-east1-docker.pkg.dev/lanes-project-508809/lanes/lanes-news-verified@sha256:593482627b8c72ae2cc43a523ec052346d26082d85d736aaea3b8dd83062e3f1`.
- Release SHA: `eef8c6c2c4b83c7b09fcbde15dc414cce1b4ccd48ade5a866da9b450e8102c11`; reader SHA: `a948b6bb533d3f6dbda679381cd2c72ece28e06a338983c602616bbbdb38fc95`.
- Raw pipeline: `ner-v1:41ecf61ec4bd78e73098e68b3cc7911439ad7d5bf6e3205f500c63affffe1aaa`; resolved: `ner-v1:42a35fb27edbf3e0800eccb5de34f1ee0f9ed4efa25dadb899ccac053ee394bd`.
- Resolver profile `compact`, configuration revision `native-gemini-compact-cloud-v2`, model `gemini-3.5-flash-lite`. Original trained bundle and inference worker identity remain unchanged; application manifests were frozen anew rather than rewriting earlier evidence.
- Manual job `lanes-news-verified`: 1 CPU, 3 GiB, 600 seconds, zero retries, default read-only preflight. General provider execution remains disabled. API, discovery and manual worker retain LANES secret version 2; personal version 3 remains unused. Existing API resources are unchanged.
- Private immutable inputs/control receipts and stage failures are retained in ignored `data/gemini-diagnostic-20261022/`, `data/gemini-schema-comparison-20261022/` and `data/gemini-repair-20261022/`. Earlier manifests and failed reservations remain available.

Recovery restores serving revision `lanes-api-gemini-20261022-v4` and the retained previous manual-job specification, disables further manual execution, and retains all database/spending evidence. Do not reset the database or ledger. Before the three-article pilot, explicitly inspect/resume its stopped budget, freeze authorities against this release, register missing captures and create fresh NER runs. No earlier application authority can authorize this new release.
