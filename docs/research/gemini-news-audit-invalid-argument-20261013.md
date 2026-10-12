# Gemini news audit HTTP 400 investigation

> **Last Updated:** October 13, 2026, 3:49 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Research complete; repair implemented/tested locally, qualification blocked by HTTP 429; no repair deployment.

## Finding

Controlled requests strongly isolate the current failure to the response-schema path. With the same new key, `gemini-3.8-flash`, article/candidate document, system instructions and generation settings, the full LANES schema returns HTTP 400 `INVALID_ARGUMENT`, while a tiny replacement schema returns HTTP 200 with STOP completion. That control proves structured JSON generation works; it is deliberately not a flood audit and cannot approve a claim.

The exact incompatible constraint remains unproved. Tests intended to isolate schema details encountered HTTP 503 high-demand responses and were stopped. Do not claim that a particular keyword, array bound, or candidate count is the confirmed culprit.

No backend source, database schema, evidence policy, deployed runtime, provider selection or saved flood record was changed during this investigation. Existing concurrent frontend edits were preserved. Probe helpers/results are ignored local artifacts, and credentials are never included in this report.

## Internet evidence and its limits

| Primary source | Finding | Relevance |
| --- | --- | --- |
| [Google AI Developers Forum: large response-schema rejection](https://discuss.ai.google.dev/t/unexpected-invalidargument-error-for-large-response-schema/37272) | The author reproduces generic 400 failures by changing schema property counts/name lengths; another participant reports continued failures in January 2026. | Firsthand evidence that others experience schema-dependent rejection. Older models and `response_schema` APIs; their numeric thresholds are not LANES limits. |
| [Gemini structured-output documentation](https://ai.google.dev/gemini-api/docs/structured-output) | Supported JSON Schema is a subset; large/deep schemas can be rejected. Application validation remains necessary. | Direct authority for a provider-specific projection plus unchanged backend validation. |
| [Google structured-output considerations](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output?hl=en) | Google identifies long array limits, enums, names and optional properties as possible complexity contributors to 400 errors. | Useful experiment design. This is the enterprise/Vertex-family API, not proof of Developer API thresholds. |
| [Google's API schema definition](https://github.com/googleapis/googleapis/blob/master/google/ai/generativelanguage/v1beta/generative_service.proto) | The JSON Schema path documents `$defs`, `$ref`, `anyOf`, bounds, required fields and additional properties; its supported list omits `pattern` and `exclusiveMaximum`. | Do not blindly remove references or null alternatives based on older SDK advice. Unsupported keywords are investigation candidates, not demonstrated causes. |
| [Google SDK tuple-schema issue #69](https://github.com/googleapis/python-genai/issues/69) | Reports 400 for `prefixItems` in a typed response-schema path. | Different API/shape. LANES has variable-length tuples emitted as `items`; this issue does not diagnose LANES. |
| [September 2026 system-instruction report](https://discuss.ai.google.dev/t/400-request-contains-an-invalid-argument-when-systeminstruction-exceeds-85-90k-tokens-3-7-3-8-flash-3-1-pro/183049) | The author isolates failures to very large system instructions on recent models. | LANES's instruction is 3,814 bytes, far smaller than that reported workload. The successful same-instruction schema control also argues against this being our cause. |

The generic [Gemini CLI issue #14731](https://github.com/google-gemini/gemini-cli/issues/14731) confirms the error appears elsewhere, but lacks a matching schema reproduction. LANES uses raw HTTPX rather than that CLI or a Google SDK; updating a CLI/SDK is not an established fix for this failure.

## LANES request and verification

`backend/app/services/news_claim_auditor.py:495` sends `CompactBatchSelection.model_json_schema()` directly as `generationConfig.responseJsonSchema`, with JSON MIME type, temperature 0 and an 8,192-token output ceiling. Its strict schema is 4,295 bytes. The controlled complete request is 9,278 bytes. Credentials, endpoint, prompt and generation settings remain fixed across schema controls.

The schema contains seven reusable definitions, nested arrays, required fact objects, nullable alternatives and enums. Results are capped at eight, evidence arrays at twelve and depth qualifiers at twelve. `AuditEvidenceReference.option_index` emits `minimum: 0` and `exclusiveMaximum: 256`; candidate IDs emit a regular-expression `pattern`. These strict local requirements must continue to be enforced even if the wire schema changes.

Four actual POSTs were made in this investigation:

| Order | Comparison | HTTP | Time | Meaning |
| --- | --- | --- | --- | --- |
| 1 | Original LANES schema | 400 | 20.80 s | Reproduces invalid request before any audit result |
| 2 | Same request with 112-byte boolean schema | 503 | 0.95 s | Availability failure; not a schema verdict |
| 3 | Same minimal-schema control, separate bounded follow-up | 200/STOP | 19.16 s | JSON schema transport works with the same key/model/request envelope |
| 4 | Original schema with array bounds removed | 503 | 2.09 s | Cannot determine whether this modification fixes rejection |

Each experiment run stopped on a provider availability error. Supported-keyword and exact-single-result variants were prepared but not dispatched. The six-request ceiling was not exhausted; no more requests were made because the independent schema tests were inconclusive under provider demand.

Ignored receipts: `data/news-reliability/gemini-schema-investigation.json` and `gemini-schema-investigation-followup.json`. The successful control returns an `ok` field, not verified evidence. No synthetic approval, batch success or historical activation is recorded.

Cloud reads confirm API revision `lanes-api-gemini-key-20261012-185034` serves 100% traffic. API and news worker resolve to image digest `sha256:2ea46a7a6fe6657c5d5ef0116e398f36af6136ca7fb60713dcab9076d5c9f2e6`, tag/commit `2cf147b4b6f322130f225ae0ecf29d081ee1c46f`. The auditor, audit schema and evaluation service in that deployed commit match the local source, including v11 compact source locators. This supersedes the earlier v5 image observation in the runtime record. No image was deployed by this investigation.

## Proposed repair and acceptance order

1. **Build a Gemini-specific schema projection.** Clone the existing schema; retain all required facts, types, enums, candidate IDs and supported source-reference structure. Remove unsupported wire regex keywords and translate the integer exclusive upper bound to inclusive `maximum: 255`. Separately test whether reducing/removing provider-side array bounds resolves decoder complexity. Keep the original strict Pydantic models, eight-candidate limit, twelve-span limit, bounded responses, exact candidate-set matching, source-offset validation and all publication gates. Do not mutate the canonical schema or accept coerced/repaired results. Keyword cleanup alone is not yet a proven fix.
2. **Complete field isolation under a shared request budget.** Compare one schema alteration at a time against the original request after provider availability recovers. Keep evidence/document/settings fixed and stop on 429/503. If a smaller faithful schema still fails, flatten the Gemini wire representation with deterministic server-side expansion and a versioned contract. Do not fall back to unvalidated free-form answers or per-claim request multiplication.
3. **Repair Gemini operational checks.** Diagnostics currently read OpenRouter's `model`, `usage` and `choices.finish_reason`; map Gemini's `modelVersion`, `usageMetadata` and `candidates.finishReason` into the existing bounded fields. The readiness command currently refuses any provider other than `openrouter/free`; make offline checking work for Gemini, with live probes explicitly opted into. Use the selected provider's credential in private account/circuit identity: the current helper always uses the OpenRouter key, so Gemini key rotation cannot distinguish accounts correctly. Keep real-clock cooldowns and prevent repeated identical permanent 400 requests from consuming a whole cycle.
4. **Qualify before full replay or release.** Add meaningful transport/normalization regressions and adversarial response cases: missing/duplicate IDs, extra results, wrong types, invalid indexes, another claim's evidence, unexpected fields, truncated/thinking-only responses and oversized output. Then run bounded real single/eight-claim audits on captured positives and negatives using the actual production request composition. Every accepted result must pass existing evidence validation. Release matching validated API/worker code only after that acceptance. Historical Santo Domingo activation/depth-update replay is a later, separate check.

The prior 123 mocked transport/batch/hybrid checks establish local failure handling and evidence gates, not provider acceptance of the exact schema. No migration or new dependency is expected for the proposed adapter/diagnostics work. The current request-format repair, model accuracy and full replay remain pending.

## Implemented repair and bounded qualification

The approved repair is implemented in an isolated branch from the deployed commit. Normalized still returns HTTP 400; compact returns HTTP 429, so qualification stops after 2/12 requests. Neither profile is qualified; inline and Flash-Lite backup remain untested. This narrows the result: pattern/exclusive bounds alone are insufficient to remove the 400, but the exact remaining conflict is still unknown. 243 targeted/234 native/two responsive checks pass. [Qualification receipts and release decision](../evaluations/news-gemini-qualification-20261013.md).
