# Gemini and Groq captured-evidence trials

> **Last Updated:** October 13, 2026, 4:56 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Research trials; active provider and cloud release unchanged.

The developer authorized Gemini trial/error and Groq alternative research. Frozen inputs, original source identities, source offsets and strict backend acceptance remain unchanged. See [official documentation and integration direction](../research/gemini-groq-free-auditing-20261013.md). No live capture, database/publication write, billing change, key rotation or automatic fallback.

## Shared dispatch history

The previous three requests remain counted. New Google/Groq experiments share the original 12 ceiling. Only model discovery GET is outside that count. Each HTTP failure consumes one attempt; no SDK retries. The prior stopped ledger was backed up before explicitly authorized continuation after its saved deadline.

| POST | Provider/model | Case/configuration | HTTP | Strict result |
| --- | --- | --- | --- | --- |
| 1–3 | Gemini 3.8 Flash | Earlier normalized/compact morning single | 400 / 429 / 429 | No validated evidence; preserved earlier results |
| 4 | Gemini 3.8 Flash | Inline schema, current `responseFormat.text` interface | 429 | Daily free requests exhausted; compatibility unknown |
| 5 | Groq GPT-OSS 120B | Morning Santo Domingo, original canonical schema | 200 | Review: status not confirmed |
| 6 | Groq GPT-OSS 120B | Afternoon Santo Domingo, original canonical schema | 200 | Review: status not confirmed |
| 7 | Groq GPT-OSS 120B | Eight original claims | 429 | Combined 8,000 TPM exceeded; honor short cooldown |
| 8 | Groq Qwen 3.8 27B | Eight original claims, unchanged instructions | 200 | One verified; seven invalid exact-place identities |
| 9 | Groq Qwen 3.8 27B | Eight original claims, explicit identity instruction | 200 | **Eight verified**, 5,149 prompt + 1,993 completion tokens, ~4.8 s |
| 10 | Groq Qwen 3.8 27B | Afternoon single, output cap 4,096 | 429 | Account OTPM 1,000; expected output 1,993 too large |
| 11 | Groq Qwen 3.8 27B | Afternoon single, same identity instruction, output cap 768 | 200 | **Verified**, 3,361 prompt + 269 completion tokens, ~1.0 s |
| 12 | Groq Qwen 3.8 27B | Negation/forecast-only synthetic case, same instruction/cap 768 | 200 | **Review**, conflicting evidence; 1,153 prompt + 192 completion tokens, ~0.7 s |

POST 4 explicitly reports quota ID `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, model `gemini-3.8-flash`, quota value 20 and RetryInfo 11,624 seconds. Stop Google requests. The documented daily boundary is 3 PM Manila; use the later of the reset and RetryInfo. Do not interpret this as a new schema rejection, invalid key or billing failure.

Groq's account advertised 1,000 RPD / 8,000 TPM response headers. POST 10 also proves a separate 1,000 OTPM cap, consistent with its official account-specific limits documentation. Eight-claim success is therefore an accuracy sample, not a reliable throughput policy. Smaller batches and explicit output limits require qualification. No model was switched to evade a pending cooldown; distinct Groq model experiments followed the prior token cooldown.

## Identity and evidence contract

The only successful experimental prompt addition preserves requested `raw_place_name`, `canonical_city` and `canonical_barangay` **after** independently verifying them against body evidence; `road_segment_raw` does not replace the raw label. Unsupported identities must remain unconfirmed. No returned field is coerced or corrected. Pydantic schema, parent/occurrence/span validators, candidate hashes, ID cardinality, time checks and publication gates remain unchanged.

The eight-case result separates five NS Amoranto observations in Sienna (37/26 inches), West Riverside in Damayan, Don Jose in Sienna, and NS Amoranto in Santo Domingo (19 inches). The afternoon single uses its separate article's Santo Domingo 10-inch/16:30 observation. Do not combine their source versions or times. Source morning wording is half knee-deep (19 inches), while saved extraction is canonical knee; retain that discrepancy and do not claim zone/depth-update acceptance.

Groq envelopes were evaluated through the unchanged OpenAI-compatible decoder using an HTTPX mock, followed by full LANES validation. Receipts label actual provider Groq separately from decoder provider OpenRouter. This does not install Groq as an active application provider.

## Reproducibility and completion limits

Private request payloads, bounded provider envelopes and a no-DB experimental Python/Node harness are retained in ignored `data/provider-qualification/`; original frozen fixtures, hashes and the persistent ledger remain in the detached retained repair checkout. No credential is stored in those files; the Groq key remained in ephemeral memory. Each new ledger entry stores actual provider, model, profile, input/claim hashes, result and safe rate headers.

All **12/12** reserved attempts dispatched. Google remains blocked; Groq is a viable research candidate, with three successful case sets under the clarified contract (eight positives, separate afternoon positive, conservative negative). Original ambiguous-title and standalone morning cases were not retested with that configuration, and no repeatable smaller-batch throughput/weather acceptance was performed. Requests with cap 768 completed rather than truncating; the schema/validator did not accept partial outputs. Stop all further live requests at the shared ceiling.

**215 offline tests passed**, using dotenvx: auditor, batch, Gemini adapter/qualification, weather insights and hybrid extraction. Existing multipart/Pydantic namespace warnings remain. These tests and mock-envelope replay verify existing validation; they do not implement Groq runtime integration. Both article hashes and all original fixture claim hashes/offsets were checked before dispatch. Receipt hashes and final ledger state are preserved privately.

No production source, local active provider configuration, Secret Manager secret, Cloud Run revision or worker job was changed. The working branch remains roi-branch. No new dependency, migration, endpoint or historical replay. A successful research sample does not satisfy the original Gemini qualification gate. Before switching, implement explicit Groq provider identity/credentials/diagnostics, qualify a repeatable quota-compatible batch policy and the remaining ambiguous/standalone cases, and qualify weather separately.

## Documentation publication audit

The developer requested senior-planner synchronization and publication to roi-branch, followed by computer shutdown. The documentation package preserves complete test/budget history, explicitly keeps operational integration blocked, and updates the index, progress/tasks, runtime guide, feature/system/stack status and bug investigation. Decisions and database definitions were reviewed and need no change: no architecture pivot or database/dependency modification occurred. Existing 215 passing checks remain applicable because production source is unchanged. Relative links, whitespace and plaintext credential exclusions are verified before commit; the remote Git state is the authority for completed publication. [@roicambe](https://github.com/roicambe) (Roi Cambe)
