# Funded Gemini request — investigation without generation requests

October 22, 2026, 9:51 PM Asia/Manila. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

Later follow-up: [controlled schema comparison, repair and real cloud acceptance](provider-repair.md). This document preserves the earlier read-only investigation and its evidence limits; no original request/manifests were rewritten.

## Conclusion and limits

**The exact upstream cause is not established.** Google rejected execution `lanes-news-verified-bjlbv` with HTTP 400 / `INVALID_ARGUMENT`. This investigation made **zero additional generation requests**, changed no integration code/cloud settings and did not resume or reset the stopped spending ledger.

The ordinary model output limit is not exceeded, the original key belongs to the funded billing account, and the basic endpoint/header/JSON configuration agrees with the official reference. Structured-schema complexity remains a concrete compatibility hypothesis, not a confirmed diagnosis. Do not change generation parameters or switch models on the assumption that it is proven.

## Exact offline reconstruction

Reconstructed the request using the exact staged image, synthetic credentials and `httpx.MockTransport`, inside a container with networking disabled. No inference model or database was used. Canonical payload/context identity equals the recorded spending-reservation ID:

`2b4d0ec61922f3f597c8fff09583ef7089641e9f4bf6bc1787b18ee431ad9380`.

| Property | Failed request |
|---|---:|
| Article body | 88 characters, fictional software fixture |
| Requested observation targets | 2 |
| Full HTTP JSON body | 8,766 UTF-8 bytes |
| System instruction | 2,043 characters |
| Schema serialized with ordinary JSON formatting | 2,748 bytes |
| Fields per observation | 21 |
| Maximum response items in schema | 8 |
| Nested evidence arrays per observation | 6, each with `maxItems: 12` |
| `maxOutputTokens` | 8,192 |
| `temperature` | 0 |
| MIME type | `application/json` |

The request uses the documented `v1beta/models/gemini-3.5-flash-lite:generateContent` endpoint, JSON content type, `x-goog-api-key` header and `generationConfig.responseJsonSchema`. It does not combine `responseSchema` with `responseJsonSchema`, use tools, reference external files, send all three articles, or request multiple model response candidates. The two observation targets are data inside one response, not `candidateCount`.

The [official model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite) lists a 1,048,576-token input limit, a 65,536-token output limit and structured-output support. The configured 8,192-token cap is below that output limit. Actual input token count was not measured with a provider request; the reconstructed input is only 8.8 KB including framing/schema.

## Key and billing checks

Read-only Secret Manager/API Keys metadata inspection, with credential strings kept in memory and excluded from output, confirms:

- The worker-selected secret remains version 2, the original LANES credential, with authorization-key format and no whitespace corruption.
- Its key resource exists, is not deleted, and is restricted to `generativelanguage.googleapis.com` without method, browser, IP or application-origin restrictions.
- Its owner is `gen-lang-client-0723504039`, distinct from hosting project `lanes-project-508809`. That distinction is valid: a Gemini key can belong to a different funded project from the hosting service.
- The key-owning project has billing enabled and is linked to the same billing account displayed in the LANES AI Studio dashboard. The dashboard displays a US$5.00 credit balance. It warns that usage figures can be delayed, so this is not a final billing reconciliation.
- Metadata checks do not establish successful model authentication, rule out all service-account/provider security checks, or prove an actual provider charge.

Google documents [key lookup](https://docs.cloud.google.com/api-keys/docs/reference/rest/v2/keys/lookupKey), [key metadata](https://docs.cloud.google.com/api-keys/docs/reference/rest/v2/projects.locations.keys/get) and [standard versus authorization keys](https://ai.google.dev/gemini-api/docs/api-key). No key was created, edited, activated, deleted or printed.

## Hypotheses assessed against official documentation

| Possible cause | Assessment |
|---|---|
| Excessive configured output-token limit | The request cap is within this model's documented limit; no evidence supports reducing it as the cause-specific fix. |
| Too many articles / excessive ordinary prompt size | The failure used an 88-character fictional article and two targets. Real seeding never started. |
| Rate quota or depleted credits | The observed status is 400 / `INVALID_ARGUMENT`; Google's documented usual statuses are 429 for rate limits and 402 for depleted prepaid balance. Current funded-account linkage is confirmed, but status alone is not a complete diagnosis. |
| Wrong basic endpoint, missing JSON content type, unsupported model feature | Offline request inspection agrees with the documented endpoint, header and advertised structured-output support. |
| JSON-schema complexity | Plausible. Google's guide specifically warns that nested array bounds and branching can make a supported schema fail with 400. The normalized profile sends an outer bound of eight results and six inner arrays bounded at twelve, alongside nullable branches/enums. No published deterministic complexity threshold or retained provider explanation proves that this particular schema exceeded it. |
| Deleted/unrestricted/origin-blocked key, wrong funded project | Metadata checks do not show these conditions. Broader authentication/security causes remain unconfirmed. |

References: [Generate Content error codes and error body](https://ai.google.dev/gemini-api/docs/generate-content/api-errors), [structured-output limitations](https://ai.google.dev/gemini-api/docs/structured-output#limitations), [Generate Content request reference](https://ai.google.dev/api/generate-content), [troubleshooting and no client-error retries](https://ai.google.dev/gemini-api/docs/troubleshooting).

## Confirmed diagnostic defect

`provider_error_diagnostic` in `backend/app/services/news_ner_durable/gemini_resolution.py` reads the error response but persists only HTTP status, an allowlisted provider status and a few keyword-derived categories. It discards `error.message`, `error.details`, `ErrorInfo.reason` and field violations. The actual receipt contains only `provider_request_failed` / `INVALID_ARGUMENT`.

Consequently, a malformed schema, another invalid parameter or an authentication-specific reason can become indistinguishable in retained evidence. The earlier passing contracts used simulated provider responses; they verify local behavior and cannot prove Google's acceptance of the schema. A Cloud Logging read scoped to the failed request's time found no upstream Generative Language audit entries in the hosting project; this does not prove that AI Studio project logs are absent.

Google's [logging guide](https://ai.google.dev/gemini-api/docs/logs-datasets) says Generate Content request storage is opt-in. If an existing AI Studio record contains the original rejection, recover its sanitized message/details before another call. Otherwise the precise historical rejection cannot be recovered from our saved receipt.

## Next gate, before any repair or paid retry

Preserve the current image, failed request identity, key selection and stopped budget. First obtain a bounded, sanitized Google rejection explanation: existing provider logs if available; otherwise a separately controlled diagnostic invocation after improving error capture. Retain HTTP/gRPC status, allowlisted reason/field paths and a redacted message; never credentials, authorization headers or unrestricted provider payloads.

Only a confirmed reason should choose the implementation change. For example, if Google confirms schema-state complexity, simplify the provider-facing schema while keeping strict Pydantic/evidence checks locally; if it reports a key/service-account issue, repair only that configuration. No retry loop, model sweep, output-limit guessing, account switch or article seeding is justified by the current evidence.
