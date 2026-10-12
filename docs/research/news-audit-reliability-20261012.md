# News audit reliability and placement repair research

> **Last Updated:** October 12, 2026, 9:38 PM PHT
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Research and recommended implementation scope. Application repairs and new live inference benchmarks are not implemented by this investigation.

## Finding and evidence boundary

Retain the local extraction and independent evidence audit architecture. Improve the audit's observability, request size and repeatability, then repair geographic coverage separately. Increasing the timeout alone cannot establish reliable auditing or create missing placement assets.

The inspected state is `roi-branch`, commit `f4103aa`. The prior batch implementation already reduced separate per-claim requests, added quota-aware retries and changed the request deadline from 20 to 60 seconds. It did not eliminate the real-provider failures. The [ordered replay evaluation](../evaluations/news-retry-20261012.md) records twenty requests, 131 dispatched claim attempts including retries, four verified claims and zero zones/history. Its final account check was 20 used / 50 limit / 30 remaining; this is a saved replay reading, not a guarantee of current allowance. No HTTP 429 occurred in that retry.

Saved checkpoint diagnostics contain 113 distinct timed-out claim attempts, each carrying HTTP 200. Multiple claims share a request, so 113 is **not** the number of HTTP requests. HTTP 200 establishes that response headers arrived; it does not establish that a complete usable audit arrived. Current records omit timeout subtype, response progress, elapsed phase timings and actual model/provider. They cannot prove whether a particular failure was upstream queueing, generation, body delivery or the application's overall deadline. The local deadline triggers cancellation; responsibility for the underlying delay remains partly unmeasured.

September 24's five locations correctly fail admission because their original observations are too old at publication. That is a valid negative result. The September 9 N.S. Amoranto/Banawe **Santo Domingo** claims retain 19 inches at 08:55 and 10 inches at 16:30, but failed audits precede expiry. No initial eligible zone exists, so zone-update acceptance remains unproven. Preserve those facts and distinguish the Sienna intersections.

## What the implementation currently does

| Area | Confirmed behavior | Implication |
| --- | --- | --- |
| Request deadline | `news_claim_auditor.py:285` wraps the HTTP operation and subsequent processing in `asyncio.timeout(60)`; transport timeouts share the same value. | HTTP transport and overall-deadline exceptions collapse into `auditor_timeout`. Synchronous parsing/validation is not independently timed. |
| Response delivery | `_request` at line 337 never sends `stream: true`. HTTPX's `client.stream` reads HTTP body bytes; it does not enable model token streaming. | Do not interpret the current path as an SSE token stream. |
| Client lifecycle | The ordinary evaluation path supplies no shared client; an audit constructs and closes its own `AsyncClient`. | Connection reuse between batches is available as a low-risk improvement, but is not a proven cause of the 60-second failures. |
| Model selection | Configuration uses `openrouter/free`; `_content` retains content and generation ID, not chosen model or usage. | Equivalent requests can use different models, while saved results lack that attribution. |
| Output contract | Each candidate returns identity, canonical strings and five independently evidenced fact assessments. Hash, source span and locality/depth checks remain strict. | Copying long hashes and redundant strings costs output and can fail identity checks. Valid JSON alone never establishes a correct claim. |
| Queue ownership | `news_evaluation.py` uses five maximum attempts and a 120-second lease, renewed at dispatch. | A five-minute timeout would outlive ownership unless the lease lifecycle also changed. |
| Placement assets | Current qualified news catalog contains twenty polygons, all in Pasig; builder explicitly checks the thirty-barangay Pasig reference. | Malabon/QC coverage requires reviewed assets and a builder/provisioning change, not a timeout adjustment. |

Key implementation paths: `backend/app/services/news_claim_auditor.py`, `news_evaluation_service.py`, `news_audit_quota_service.py`, `barangay_boundary_service.py`, `news_locality_anchor_service.py`; `backend/app/crud/news_evaluation.py`; `backend/scripts/build_news_barangay_catalog.py` and `provision_news_barangay_catalog.py`.

## Local request measurements

A read-only helper reconstructed three saved batches from the isolated September 9 database. It did not dispatch an LLM request or alter database rows. The ignored helper and metrics are `data/news-replay/measure-audit-payload-20261012.py` and `audit-payload-measurements-20261012.json`.

| Saved extraction run | Claims | Article UTF-8 bytes | User JSON bytes | Evidence-options bytes | Candidate-section bytes | Preparation ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 8 | 1,999 | 19,860 | 6,939 | 10,444 | 4.63 |
| 131 | 3 | 1,696 | 9,165 | 3,314 | 3,719 | 0.99 |
| 190 | 8 | 2,710 | 25,069 | 9,437 | 12,500 | 2.86 |

The response schema adds another 4,309 bytes, plus the system prompt and request envelope. These are byte measurements, not tokenizer counts. The article is already supplied once, but evidence options repeat quotes and candidate objects repeat sentences and approximately thirty fields, including derived/null locality/depth values. Preparation took milliseconds; this does not measure provider execution or prove payload size caused any timeout.

## Internet findings and applicability

Technical recommendations below use official documentation and repository-owner implementation reports. Community experiences are useful leads, not evidence that LANES has the same defect.

| Source inspected | Finding | Application to LANES |
| --- | --- | --- |
| [HTTPX timeout documentation](https://www.python-httpx.org/advanced/timeouts/) | Connect, read, write and pool bounds are distinct; read timeout measures waiting for a chunk. | Record exception subtype and separate transport bounds from total audit duration. |
| [HTTPX async documentation](https://www.python-httpx.org/async/) | Repeated client creation in a hot loop loses connection-pooling benefits. | Scope one client to an evaluation cycle and close it once. |
| [OpenRouter free router](https://openrouter.ai/docs/guides/routing/routers/free-router) | Random selection among compatible free models; variable availability and peak latency. | Benchmark named free models; retain the free-only constraint. |
| [OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs) | Endpoint support and strict enforcement vary; structured output can also stream. | Keep `require_parameters: true`, strict schema and application evidence validation. Check actual endpoint support before model selection. |
| [OpenRouter latency guide](https://openrouter.ai/docs/guides/best-practices/latency-and-performance) and [provider routing](https://openrouter.ai/docs/guides/routing/provider-selection) | Queue/prefill and generation both contribute; routing preferences reorder providers. | Try latency/throughput preferences only as measured optimizations, not guaranteed deadlines. |
| [OpenRouter streaming](https://openrouter.ai/docs/api_reference/streaming) | `stream: true` enables SSE; comments and midstream errors need correct handling; `X-Generation-Id` is documented. | Capture the generation header separately from `x-request-id`. If streaming is added, fully assemble and validate the final result before accepting any claim. |
| [Generation metadata API](https://openrouter.ai/docs/api/api-reference/generations/get-generation) | Generation records expose model, provider, timing and token accounting. | Correlate selected diagnostic investigations by generation ID; avoid an extra metadata GET per claim. |
| [ZeroClaw issue #10436](https://github.com/zeroclaw-labs/zeroclaw/issues/10436) and [merged repair #10442](https://github.com/zeroclaw-labs/zeroclaw/pull/10442) | Their native SSE path cut off active responses at a total deadline; the repair separates streaming read bounds and reuses a client. | Relevant timeout-design lesson, but a different Rust/SSE implementation. LANES currently uses nonstreaming completion and requires a lease-compatible hard bound. Do not copy their unbounded total lifetime or 300-second idle value. |
| [LangChain issue #39812](https://github.com/langchain-ai/langchain/issues/39812) | Reported seconds-to-milliseconds mismatch in its OpenRouter integration. | Not this bug: LANES uses HTTPX/asyncio seconds directly. Do not multiply the timeout by 1,000. |
| [Reddit OpenRouter timeout discussion](https://www.reddit.com/r/openrouter/comments/1we52tb/openrouter_80_of_my_requests_timeout_or_fail/) | Firsthand reports of frequent failures, with differing experiences and routing suggestions. | Supports investigating actual provider/model attribution; cannot identify our failing provider or justify blanket replacement. |
| [DEV structured-output experience](https://dev.to/lovanaut55/openrouter-structured-output-broke-before-translation-quality-did-3-layers-of-defense-for-1cdb/) | Translation application reports JSON failures, adjusted timeout and model retries. | Separate syntax/transport failures. Do not adopt permissive parsing, semantic response repair or multiplied model/retry loops for flood approval. |
| [Stack Overflow Semantic Kernel integration](https://stackoverflow.com/questions/79436777/semantic-kernel-with-openrouter) | Reported 404/405 and feature/model compatibility problems, with an anecdotal model-switch answer. | Different stage from our HTTP-200 timeout. No verified LANES fix was established; direct page retrieval was intermittent and search-index content supplied the readable example. |

The public OpenRouter model registry was read without credentials or inference. Six zero-priced `:free` models advertised `response_format` or `structured_outputs`: Apodex mini, Dots note preview, Liquid LFM, two Gemma 4 variants and Nemotron 3 Super. The saved list is `data/news-replay/public-free-audit-models-20261012.json`. This aggregate metadata is a shortlist, not proof of strict-schema compatibility, factual accuracy or response speed. No model is selected by this report. If testing reasoning controls, use documented support; hiding reasoning output does not disable its computation. [Reasoning controls](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens).

## Ordered repair proposal

### 1. Add useful diagnostics and reuse the HTTP client

Use monotonic time for preparation, headers, body progress/completion, parsing, evidence validation and persistence. Save bounded phase/outcome fields, timeout exception subtype, bytes received, candidate count, configured model and actual model when known. Preserve generation ID from headers even if the body later stalls; keep gateway request ID separate. Capture finish reason and safe usage on completed responses. Do not save credentials, arbitrary raw provider errors or unrestricted response bodies.

Use existing evaluation JSON and extend its diagnostic allowlist/DTO consistently; no SQL schema change is necessary. Keep authentication and bounded diagnostic sizes. Pass one scoped client through quota/audit operations where appropriate; avoid database transactions while awaiting provider IO. Update worker progress after each batch so a long audit cycle is visible.

Instrument the current 60-second baseline first. Configure connect/read/write/pool bounds separately. If measured useful completions need more time, test a total bound no greater than 90 seconds initially, leaving at least thirty seconds within the existing lease for validation/persistence. This is a proposed experiment, not a proven threshold. Never raise the deadline past ownership without explicit lease recovery tests and a separate design.

### 2. Compact the request while preserving evidence

Retain the complete bounded article once. Whitelist fields required to audit the candidate; remove redundant conversions/null metadata. Represent evidence with canonical source offsets and deduplicated references. Preserve parent headings, original clocks/depth qualifiers, neighbouring claims, conflicting facts and exact source hashes. Avoid a quote-only prompt that hides contradictions.

Compare compact batches of four and eight on the same saved source versions. Four may improve completion time but spends more requests; twenty-six eligible claims require seven groups at four versus four groups at eight before retries. Choose based on verified throughput and accuracy per daily request budget, not only single-request speed. Retain sequential dispatch initially.

A later compact response can use short candidate IDs and fact verdict/evidence indexes while the server binds each result to its immutable canonical hash. This requires a versioned audit contract and cross-candidate rejection tests. It must never silently correct a mismatched model hash, fill a missing result or accept another road's evidence. Preserve prior terminal evaluations.

### 3. Benchmark specific free models and control retries

Check live allowance before a small provider experiment, with a first-pass ceiling of twelve actual POSTs. Compare unchanged and compact payloads using the same named model and article before comparing another model. Count split batches and retries against that ceiling. Measure successful fully validated claim results, request duration, selected provider, output truncation and tokens where available. A small experiment screens candidates; it does not demonstrate production reliability.

Select a named free primary and only a separately tested free backup if results justify them. Keep strict parameter requirements and evidence gates. Consider supported reasoning limits and latency/throughput routing preferences. Recheck availability at deployment. Use one shared attempt budget across primary/backup, retain account cooldown and avoid parallel hedged requests or a retry loop per model. Repeated availability failures should defer remaining work under a bounded cycle cooldown rather than burn the daily allowance. Recheck observation freshness before every retry and publication.

Token streaming is optional after these measurements. If introduced, use `stream: true`, a bounded SSE parser, proper comment/multiline/error handling and separate idle/overall bounds. Track meaningful content separately from keepalive bytes. Approve only complete, normally finished JSON that passes every identity/evidence check; truncated streams remain unavailable/review. Streaming can reveal progress but cannot guarantee faster inference.

### 4. Extend reviewed placement coverage

The confirmed verified claims needing assets are San Agustin and Tañong in Malabon, and Tatalon in Quezon City. Santo Domingo is also needed for the paired test if auditing succeeds. Generalize the Pasig-specific builder by reviewed parent-city/PSGC identity, or provision a reviewed external catalog with the existing archive/hash/license/containment checks. Preserve the old catalog and create a new immutable asset version.

[PSA PSGC](https://psa.gov.ph/classification/psgc/summary) supplies canonical administrative identity. A [community boundary repository](https://github.com/bendlikeabamboo/barangay-boundaries-repository) is a useful acquisition lead: it reports PSA/NAMRIA-derived polygons, checksum manifests and a 2023 source snapshot. Its example conversion uses 0.005-degree simplification; inspect original geometry and local accuracy before using it near roads. Its MIT statement covers code; review underlying data provenance/use terms separately. No particular required polygon was downloaded, qualified or adopted here. Existing [OSM source attribution](https://www.openstreetmap.org/copyright) also belongs in the asset review.

Barangay coverage is necessary for these outcomes, not sufficient for plotting. Retain NOAH, bounded affected-road, grade/ambiguity and activation gates. Marcos Highway Underloop additionally needs an actual uniquely grounded local structure/road extent. Do not drop the underloop qualifier, use the whole highway or substitute a generic flood buffer.

### 5. Diagnose the preview separately and repeat acceptance

The latest preview has blank pages and mobile JavaScript syntax failures despite working APIs; MapTiler also returns HTTP 403 with fallback. Capture failed script URL/build ID, status/content type, byte count and hash to investigate build/runtime delivery. Verify a clean isolated preview build on desktop and mobile. These observations do not yet prove a stale-cache cause. Preserve port 3000, the old local snapshot and cloud data.

After offline/native checks and the bounded provider comparison, run September 24–25 first and September 9 second in new isolated databases. Keep article processing on replay time and quotas/deadlines on real time. Record actual per-stage acceptance through authenticated history and public-zone APIs, not just extracted cards. Keep reconstructed RSS membership and early indexed GMA markup limitations explicit.

## Completion gates

- Preserve source hashes, independent road claims and heading context; reject wrong IDs, wrong parent locality, altered qualifiers, cross-claim evidence, duplicates and incomplete responses.
- Demonstrate connect/read/overall failure diagnostics, cancellation cleanup, response byte bounds and lease ownership with controlled transport fixtures. Completed audits must not repeat on unchanged input.
- Demonstrate real-provider, fully validated results on representative captured articles within allowance. Compare four/eight batches by actual POST count and correctly verified claims; report unresolved failures rather than invent a success target from a tiny sample.
- Keep HTTP 429, Retry-After, cache/cooldown and expiry behavior correct. Quota exhaustion remains a capacity constraint, even after reliability improvements.
- Qualify required geographic assets and obtain at least one actual eligible zone before claiming positive plotting/history/depth-update acceptance. Record whether the later 10-inch report updates, creates a separate record or is rejected.
- Verify News Intelligence, map and authenticated History on desktop/mobile with the dedicated historical read clock. No forced approvals, manual flood rows, changed evidence policy or cloud deployment.

## Work performed by this research

Read implementation and existing replay evidence, measured saved request construction, inspected actual catalog coverage, queried public model metadata and reviewed official/community sources. Saved this report and synchronized the documentation index/task/progress/issue notes. No backend/frontend product change, SQL schema change, dependency installation, new provider audit, source modification or acceptance claim was made. Previous replay artifacts remain preserved. Repair implementation and real benchmark/replay acceptance are pending.
