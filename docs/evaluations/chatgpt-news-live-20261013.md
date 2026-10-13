# ChatGPT plan authorization and first news requests

> **State:** Real account authorization and structured eight-claim inference proved; automatic-news qualification remains blocked.
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

The user completed the local sign-in on port 1457. Sanitized runtime status confirms connected=true, plan_permission_verified=true and current access token. Credentials remain Windows DPAPI protected outside Git. No Google/ngrok changes, LANES staff account mapping, DB mutation, provider configuration change or deployment was required for this separate SIWC inference route. The MCP review gateway remains disabled and its actual ChatGPT tool connection is still unverified.

Account-specific GET /v1/models returned HTTP 200 and listed gpt-6.1-sol first, followed by gpt-6-astra, gpt-6-sol, gpt-6-luna and three gpt-5.6 models. The initial conservative 500,000-byte catalog bound aborted a read; the actual catalog is 621,381 bytes and was retrieved under an 8 MiB bound. This is model discovery, not an inference POST.

## Live request ledger

One shared **five-POST maximum** is retained in ignored `data/mcp-research/chatgpt-news-qualification.json`. Three requests were dispatched; two remain unused. Each attempt was reserved before dispatch. No new Gemini/Groq requests or alteration of their exhausted twelve-request ledger occurred.

| Attempt | Original case | Measured outcome |
| --- | --- | --- |
| 1 | Santo Domingo 19-inch / 08:55 single | HTTP 200 and completed stream; local parser rejected message shape. Its text/items were not retained, so no validated audit is claimed. |
| 2 | Separate Santo Domingo 10-inch / 16:30 single | HTTP 200 and completed stream; retained terminal response shows output=[] and nonzero generated-token usage. No validated single result is claimed. |
| 3 | Eight repeated roads and parent headings | HTTP 200, completed stream, gpt-6.1-sol; all eight candidate IDs parsed and strict evidence validation ran. Seven results are review/observation_time_not_confirmed; Santo Domingo is invalid/audit_depth_disagreement. |

Third response: 5,518 input tokens, 1,482 output tokens, 412,351 streamed bytes. Metadata is provider-observed, not a model-written identity claim. The model selected source evidence for places/depths but returned time.confirmed=false, observed_at=null and no time evidence for all eight. The source has a Quezon City 08:55 heading and September 9 date context; independent model confirmation of the combined date/time/timezone remains unresolved. Do not change the prompt or acceptance rule merely to obtain a verified label.

Santo Domingo's original captured body says **Half knee-deep (19 inches)**, while its saved candidate canonical gauge is **knee**. ChatGPT returned **half-knee** with the original 19-inch measurement. The backend rejected the disagreement as designed. This discrepancy was already recorded in the MCP plan. Do not change saved claims/hashes or rewrite history to turn this result into a pass; qualification's inherited all-verified expectations need a source-grounded review.

The semantic failure stopped further dispatches. The combined sign-in/qualification/MCP regression run passed **129 checks**; a subsequent budget concurrency guard was verified by the 23-check focused suite. Ambiguous-title and forecast/negation live cases remain untested in this experiment. No positive case has passed full qualification and no rollout is permitted.

## Transport implementation and checks

Added `app/services/chatgpt_plan_qualification.py` and `scripts/qualify_chatgpt_news.py`: fixed public Responses endpoint, store=false, stream=true, original compact strict JSON schema, no unsupported temperature/output-token parameters, no automatic retries and the existing 60-second overall deadline. Every result uses unchanged candidate/hash/index/source-span/classification checks; duplicate/unknown/missing IDs fail the entire result set. No provider runtime path or publication policy was replaced.

First parser assumed one complete final message in response.completed.output. Offline research established separate commentary/final phases. The second retained envelope then proved the actual stream uses a thin output=[] completion response. Final parser collects response.output_item.done, excludes reasoning/commentary from final text and still requires response.completed. Deltas alone never qualify. Bounded raw SSE capture now enables offline investigation without another request. Captures contain response data only, no Authorization header or OAuth credentials, and remain ignored local artifacts.

Initial 19 offline qualification checks passed after adding concise pytest IDs to avoid Windows oversized auto-generated test IDs. Phase/capture/budget regressions increased this to 22, then streamed-item tests to **23 passing**. Matching/missing terminal events, quota errors after headers/completion, oversized responses, refusal, bad claims and no-reset budgeting are covered. Existing sign-in suite separately passed 42 tests; both desktop/mobile local-page checks separately passed four cases. Target Linux/PostGIS shared-upgrade acceptance remains pending.

The final runner holds an exclusive local ledger lock through the experiment, rejecting concurrent resume/dispatch. A narrow explicit transport-repair resume preserved the same ledger, account identity/model, failed attempts and five-call ceiling; it skipped earlier singles rather than retry them. It cannot resume account/quota/semantic failures, and cannot mark qualification complete when an earlier attempt failed. After the third semantic failure, the ledger is blocked with three used requests.

## Next gates

Review source-grounded expected outcomes and observation-time context, retain strict validation and original records, and qualify the remaining live cases only under a reviewed experiment. Implement renewable credential handling and a separately identified worker provider only after qualification. Public Cloud Run eligibility, durable secret storage and production rollout remain unverified. The successful sign-in does not establish an authenticated MCP tool call or unlimited Plus usage.

Sources: [SIWC inference contract](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference), [preview limits](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations), [streamed output-item events](https://developers.openai.com/api/reference/resources/responses/streaming-events), [assistant phases](https://developers.openai.com/api/docs/guides/reasoning).
