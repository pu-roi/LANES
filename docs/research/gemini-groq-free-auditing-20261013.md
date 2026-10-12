# Gemini and Groq free flood-audit investigation

> **Last Updated:** October 13, 2026, 4:56 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Bounded research completed; Groq viable in captured tests, Gemini quota-blocked. No active-provider or cloud change.

## What the official documentation establishes

[Google rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) apply per project, not per key, and daily quotas reset at midnight Pacific. On October 13 this is 3 PM Manila. More keys in the same project do not add allowance. Earlier read-only project inspection measured Gemini 3.8 Flash at 5 RPM / 20 RPD; these are project limits, not invented remaining counters. Schema errors and quota exhaustion need separate repairs.

[Google's generation reference](https://ai.google.dev/api/generate-content) now describes `generationConfig.responseFormat.text` with `mimeType: APPLICATION_JSON` and `schema`. The legacy JSON-schema interface documents support for references, definitions, nullable alternatives and closed objects. A blanket conversion to OpenAPI 3.0 is not justified. A new inline-schema/current-format experiment returned 429 before compatibility could be assessed; no successful Gemini schema profile is established.

[Groq overview](https://console.groq.com/docs/overview) and [API reference](https://console.groq.com/docs/api-reference) describe hosted LLM inference using an OpenAI-compatible chat endpoint. Groq serves its available models directly; it does not expose OpenRouter's catalog. The supplied credential's read-only model listing succeeded and included GPT-OSS 120B/20B and Qwen 3.8 27B.

[Structured outputs](https://console.groq.com/docs/structured-outputs) supports strict JSON-schema output on those models, including required fields and `additionalProperties: false`. Syntax/shape guarantees do not establish factual accuracy or publication eligibility. LANES still performs all existing candidate-ID, strict type, size, evidence-index, exact-span, place-parent, observation-time and publication checks.

[Groq limits](https://console.groq.com/docs/rate-limits) lists free defaults of 30 RPM, 1,000 RPD, 8,000 TPM and 200,000 TPD for these tested models, and explicitly warns that accounts may also have separate input/output token limits. Actual response headers confirmed 1,000 request/day and 8,000 combined token/minute limits. A later account rejection identified **1,000 output tokens/minute**. The remaining-request header describes daily allowance, not requests remaining this minute. GET model discovery consumed no generation POST.

## Reproducible bounded experiment

The developer explicitly requested new Gemini trial/error and Groq alternative evaluation after the previous saved cooldown elapsed. Preserve the stopped ledger and identity before continuing. All new providers share the original **12-POST ceiling**, counting failed, successful and reserved/interrupted attempts. The original three requests remain counted; do not reset the campaign. No SDK retry, database read/write, publication or historical activation occurs in this experiment. Deadline remains 60 seconds; responses remain bounded to 65,536 bytes.

Use the unchanged original five frozen qualification cases described in [the initial evaluation](../evaluations/news-gemini-qualification-20261013.md). Article/claim hashes and offsets validate before dispatch. Groq receives the original strict canonical Pydantic schema, with no normalization or acceptance relaxation. Experimental request settings use `max_completion_tokens`, explicit model-supported reasoning effort, hidden reasoning and no tools.

Groq responses replay offline through LANES's unchanged OpenAI-envelope decoder and full evidence validator using a mock transport. Receipts explicitly label actual dispatch provider `groq` separately from decoder configuration `openrouter`; this is **transport compatibility research**, not an implemented Groq provider in the application.

GPT-OSS 120B returned correct structured shape for both Santo Domingo source versions, but left their status unconfirmed, so both remained review. Qwen's first eight-claim response rewrote short raw place labels into full intersection names; seven results failed strict identity validation. Its corrected experimental instruction says to preserve requested labels only after independently confirming their body-supported identity, and to leave unsupported identities unconfirmed. This does not repair returned data or change backend validation. With that clarification Qwen returned eight independently verified results.

The morning Santo Domingo source says half knee-deep (19 inches), while the saved extraction has canonical knee. Keep this discrepancy and the exact original claim/source. A verified source claim does not prove that this inconsistent gauge has passed zone/depth-update acceptance. The separate afternoon source reports 10 inches at 16:30.

## Current blockers and integration direction

Gemini's new `QuotaFailure` explicitly identifies `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, model `gemini-3.8-flash`, quota value 20. Google dispatches stopped immediately. It also supplied `RetryInfo`; use the longer of that delay and the documented daily-reset boundary. A successful schema test still must run after reset. No model switching to bypass the exhausted account.

An eight-claim Qwen response uses about 2,000 output tokens. The account subsequently rejected an expected output of 1,993 against its 1,000 OTPM limit. A high headline request/day allowance therefore does not make this workload unrestricted. Smaller batches/output caps and deliberate pacing are necessary; never truncate and accept partial results. A smaller output-capped request is a distinct explicit experiment after cooldown, not a hidden automatic retry.

Before operational integration, implement Groq as an explicit third provider with its own secret, private account identity, native diagnostics and rate state. Do not disguise it as OpenRouter or call OpenRouter's quota endpoint for it. Requalify a repeatable smaller-batch policy, negative/ambiguous evidence and public weather output, preserve all strict gates, and deploy consistent API/worker configuration only after acceptance. Keep model preview status visible: [Groq's model catalog](https://console.groq.com/docs/models) distinguishes production GPT-OSS from preview Qwen.

Final count is **12/12**: the original three calls, one additional Gemini call and eight Groq calls. Explicit identity instructions passed the eight original morning claims and the separate afternoon single. A 768-token output cap produced a complete afternoon audit and conservative review of the negative/forecast fixture. The original ambiguous-title case and standalone morning single were not retested with the successful Qwen configuration before the ceiling; smaller recurring batches and weather also remain unqualified. **215 offline checks pass**. [Full measured results](../evaluations/gemini-groq-live-trials-20261013.md).

Private payloads, bounded envelopes and the experimental harness remain in ignored `data/provider-qualification/`; the persistent original ledger remains in the retained detached repair checkout. Plaintext credentials are absent from repository source, documentation and receipts. The supplied Groq credential stayed in ephemeral process memory and was cleared after testing. No new dependency, migration, endpoint, runtime provider or cloud secret is added by this research.
