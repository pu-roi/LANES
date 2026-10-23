# Gemini source-evidence validation investigation

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). October 23, 2026, Asia/Manila.

**Status: investigation and offline reproduction complete; the proposed repair is not implemented or deployed.** No production source code, cloud configuration, application database or budget ledger was changed. There were zero Gemini requests, zero NER inferences and zero seeding writes. External browsing was documentation/community research, not article retrieval for the pilot.

## Full GMA follow-up — correction saved, historical mapping unresolved

[Hosted GMA result](../evaluations/three-article-cloud-pilot-20261022/gma-population.md) supersedes the earlier single-batch scope: 12 new generations plus exact cache adoption yield run 380, five visible timed observations and explicit remaining row outcomes. The corrected-group detail HTTP 422 is patched. Five historical evaluations are unresolved at the shared-versus-individual depth requirement; no geometry/event is fabricated. Ledger stopped at 36 attempts/US$0.7314696 effective commitment. Source research and original failures below remain unchanged.

## Cloud follow-up — restricted real batch accepted

[One-batch execution and verification](../evaluations/three-article-cloud-pilot-20261022/scoped-cloud-gate.md) now establishes actual Gemini acceptance for n12–n15: two supported roads with complete time/depth evidence and two unsupported context headings. New offline testing also identified the headline rubric falsely labelled ROAD and narrowed scoped ownership accordingly without changing the approved request. 231 tests, seven worker contracts and two offline live-response replays pass. No database output or full-article acceptance follows; the stopped ledger retains all history. The research and original failure evidence below retain their original scope.

## Implementation follow-up

The local opt-in repair is now implemented; see [qualification and boundaries](../evaluations/three-article-cloud-pilot-20261022/scoped-evidence-repair.md). It supplies exact target passage bindings and conservative layout hints, requires the model to select its own complete citations, keeps strict canonical acceptance, and records bad semantic rows as unresolved under a distinct V2 identity. No old response is repaired or silently accepted. Thinking-token and failure-summary defects are fixed locally. The original research below describes the pre-repair v11 checkpoint; it remains the last verified hosted behavior. No new paid/cloud/seed action occurred.

## What actually failed

The full original GMA article and NER proposals reached Gemini. Its HTTP-200 response had valid JSON, the correct four target IDs and legal passage numbers. The failure is relational: selected passages do not support the appropriate target/field. The existing schema permits any of the 59 passage IDs in every evidence field; syntactic validation cannot express all of the source-ownership and heading relationships checked later.

The source is a hierarchical list: an article date and explicit flooded-list introduction, a city/clock heading, successive depth headings, barangay headings, then street/intersection list items. Repeated Brgy. Sienna headings belong to different depth blocks. Matching the barangay name alone cannot establish which block or roads a claim covers.

The frozen rejected bundle is SHA-256 `715c98cc084bbe1e9b9e8070aaffbc1da65161f034448ac9cb0a2bf55a83bd88`. The new audit runs the deployed **v11 Linux image**, real pinned reference assets and deterministic reconstruction from immutable NER 375, with Docker `--network=none` and socket connections explicitly blocked. It neither modifies the response nor supplies replacement citations.

| Target | Original first rejection | Additional independently verified problem |
|---|---|---|
| `n12`, first Brgy. Sienna heading | Missing status evidence | Its cited city/time, barangay and road lines omit affirmative flood/depth support. The model also treats a heading as an independently sectioned incident. |
| `n13`, Don Jose St. | Missing place evidence | Place references 12/14 omit its exact street occurrence in passage 15; status references likewise omit affirmative flood/depth support. |
| `n14`, Palali St. | Missing place evidence | Place references 12/14 omit its exact street occurrence in passage 16; status references likewise omit affirmative flood/depth support. |
| `n15`, second Brgy. Sienna heading | Fact/target mismatch | The returned road section names a child road while the selected target is its parent barangay heading. The current source-ownership rule rejects that association. |
| All four | Hidden by earlier exceptions | `date_text` is present in the article's date-bearing passages 0/8, but every `time_evidence` is only passage 12, a clock heading without that date. The actual `resolve_time` independently raises `native_resolution_date_evidence_missing` for every row. |

These are not invalid passage numbers and are not transport/billing failures. Fixing only the first error would expose further errors on another run. A whole-article stop currently prevents all partial corrected observations from reaching News Intelligence or historical qualification.

The validator's refusal to publish unsupported/cross-target facts is appropriate. The integration also contributes to the problem: it asks Gemini to repeat six independent evidence lists per target, does not pre-bind the target's already-known source occurrence, explicitly mentions context-only CITY targets but does not distinguish context-only barangay headings, and lacks an explicit contract for inherited list context. A list heading can legitimately support its children, but this needs a bounded, checked relationship. A generic search result or a nearby paragraph cannot substitute for it.

## Another confirmed backend defect

`news_gemini_receipts.validate_batch` accepts provider thinking-token metadata and can return `thinking_tokens`. `resolution.apply_resolution` permits only `request_id`, `actual_model`, `input_tokens` and `output_tokens` in transport records. A network-disabled, software-only test with 51 synthetic unsupported rows passes without the extra field and fails with `native_resolution_transport_invalid` after adding **`thinking_tokens: 0`**. The fixture asserts no flood facts and is not a replacement for the real response.

This metadata mismatch did **not** cause run 379, which stopped earlier on source semantics. It is a reproducible future blocker and should be repaired before another full paid article run. The failure-path aggregate token counters also remain incomplete; durable accounting receipts already preserve paid usage before semantic validation, and should govern truthful failure reporting.

## Internet findings and their relevance

1. **Structured JSON does not ensure correct facts.** Google's current [structured-output documentation](https://ai.google.dev/gemini-api/docs/structured-output#best-practices) requires application validation and handling of schema-compliant semantic errors. It recommends field descriptions and specific types. This supports retaining strong source checks while improving the input/output contract.
2. **Examples should demonstrate the actual source format.** Google's [prompt design guidance](https://ai.google.dev/gemini-api/docs/prompting-strategies#zero-shot-vs-few-shot-prompts) recommends varied examples and consistent formatting. The current prompt contains a one-line passage-ID example, but lacks examples of nested city/time/depth/barangay/road lists, repeated locality headings and date/clock passages split across lines. Examples for the repair should be synthetic, clearly separated from the live article, and never supply article facts or training labels.
3. **Citation misalignment also appears in grounded systems.** An August 2025 [Google Developer Forum report](https://discuss.google.dev/t/vertex-ai-gemini-w-google-grounding-inaccurate-segment-citations/251345) describes source links attached to the wrong repeated table entries. The discussion suggests more specific fact-level evidence entries. This is a useful analogue, not proof that LANES has the same provider bug.
4. **Evidence identity must survive context expansion.** A [Reddit parent/child citation discussion](https://www.reddit.com/r/LangChain/comments/1t3or38/improving_citation_accuracy_and_reducing/) reports citations referring to a different evidence object than the context shown to the model. Its stable-span-ID suggestion fits our own code finding: article context, source occurrence, inherited heading and selected passage need explicit relationships. The post concerns a different model/stack and is not an implementation specification.
5. **Old schema workarounds are model/adapter specific.** An April 2025 [Stack Overflow report](https://stackoverflow.com/questions/79588648/gemini-ai-structured-output-with-references-via-openai-sdk/79588649) concerns Gemini 2.0 schema references through OpenRouter/OpenAI-compatible parsing. LANES now uses direct Gemini REST and already has compact schema qualification. Removing references, changing SDKs or disabling validation is not an evidenced fix for the present semantic failure.
6. **Search plus structured output is not categorically unsupported.** A June 2026 [Google cookbook issue](https://github.com/google-gemini/cookbook/issues/1274) documented missing grounding metadata for `gemini-3.5-flash`; a collaborator reported the issue fixed on **October 5, 2026**, and closed it. Current Google structured-output docs describe tool combinations. Older March/April 2025 [forum advice](https://discuss.ai.google.dev/t/rest-api-grounding-and-json-responses-not-compatible/73101) recommending two paid passes is not a current requirement for our model. LANES's exact Flash-Lite request would still need a bounded compatibility test and metadata checks before claiming Search is active.

## Search, Maps and OSM

The user's suggestion to enable Search/Maps is technically feasible, but is a separate capability from fixing the retained article citations:

- [Google Search grounding](https://ai.google.dev/gemini-api/docs/google-search/) can supply external, URL-cited sources. Those are different evidence objects from the original article's numbered passages. Verify actual search invocation/returned grounding metadata, bind publisher/URL/capture/date, and keep source namespaces separate. An external claim must not be presented as a quote from the frozen GMA article. Search should not be used to manufacture missing measurements or fill arbitrary dates.
- [Google Maps grounding](https://ai.google.dev/gemini-api/docs/maps-grounding) supports the selected model and supplies place information. It does not establish the historical flood state described by a particular article. The API describes a textual place-search tool, not an authoritative flooded-footprint generator. Continue using authenticated OSM/NOAH services for the approved geometric qualification.
- The Maps documentation requires associated source names/links and attribution when presenting grounded results. That needs assessment against the existing **no UI changes** boundary; do not assume that publicly displaying grounded results requires no presentation work. No legal conclusion about internal-only use is made here.
- [Current pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite) treats search/map queries separately from token usage, with shared free allowances followed by per-query charges. A prompt can trigger multiple queries. Available shared quota was not inspected. The current pilot budget explicitly rejects tools and nonzero tool-prompt tokens, so enabling a tool without extending bounded accounting would violate the reviewed cap contract.

**Recommendation:** repair the article-evidence handoff first. Supply scoped OSM candidates for genuine place ambiguity where useful; treat Search/Maps as a separately versioned, measured enrichment path rather than a global bypass of source validation. Nothing was enabled during this investigation.

## Concrete repair design to implement next

1. **Construct source evidence units before generation.** Preserve the entire original article and existing quote ordering. Pre-bind each NER target to its exact source passage using its immutable start/end offsets. Describe city, clock, explicit date, depth and barangay headings with independently checked scope links. Keep repeated same-name occurrences distinct. Reuse supported native graph relations where they can be verified from the text; do not trust the old graph or a nearest-heading heuristic as proof. Uncertain links stay unresolved.
2. **Make the model select bounded, target-specific evidence.** Supply field-role candidates or qualified evidence-bundle IDs; use meaningful descriptions rather than the same generic description for all six evidence fields. Keep unsupported/ambiguous outcomes. The backend computes source offsets and canonical evidence projections from validated relationships. This is a **new contract**, not silently adding guessed references to the old failed response. Full article updates/clearances remain visible to Gemini.
3. **Handle context headings explicitly.** A barangay-only heading followed by roads under an explicit flood-list structure can supply locality context without becoming an extra road-section incident. Preserve genuine city/barangay-only reported flooding, independent times and unresolved specific mentions. Do not indiscriminately mark all administrative areas unsupported.
4. **Validate inherited facts against scope.** A date passage plus a city-clock heading can jointly support time; a depth heading can support its bounded descendant road list with shared precision retained. Reject heading leakage into the next depth/city/update, unrelated roads, conflicting dates, forecasts, negation and clearance/onset swaps. Do not weaken ownership to a whole-article keyword match or assume that nearby text belongs to a target.
5. **Collect all semantic diagnostics before another call.** Report each target and field, occurrence coverage, relevant scope, expected evidence role and error—not just the first thrown exception. Keep the original response and diagnostics immutable. Correct optional thinking-token transport handling and failure usage reporting at the same time.
6. **Isolate row-level uncertainty under an explicit policy.** Recommend saving independently valid observations while recording bad/ambiguous rows as unresolved, using existing JSON metadata/read projections. Structural errors, mismatched inputs/targets, storage failures, provider errors and unknown billing still stop the invocation. This changes today's whole-article rejection policy and therefore needs explicit inclusion in the next implementation/acceptance plan. It is not implemented by this research. A database transaction can still save the complete article outcome atomically, including unresolved rows, without publishing bad geometry.
7. **Qualify offline before any cloud dispatch.** Preserve 375/376/378/379, all historical receipts and the stopped US$1 ledger. Add the regressions below; rebuild/re-freeze matching release identities and authorities after code/prompt changes. Count exact new payloads and reserve the complete reviewed schedule. Adopt old responses only where the original and new contracts are demonstrably compatible; never rewrite their pins or silently resend consumed/uncertain attempts. The ledger's remaining allowance and fixed attempt bound both need review.

### Required regression cases

| Case | Required behavior |
|---|---|
| Original failed response, unchanged | Same strict rejection and complete diagnostics; no guessed references |
| Valid road occurrence with separate city/barangay/date/clock headings | Qualified scope links accepted, with exact source offsets |
| Same barangay repeated under different depth headings | No depth/status/time transferred between blocks |
| Barangay context heading versus genuine barangay-only flooding | Heading supplies context; genuine independently supported observation remains eligible |
| Multiple roads and explicit intersections | Correct road/section ownership; no duplicate broad incident |
| Date in article title/body and clock in city heading | Both cited/linked; missing date citation does not silently pass |
| Missing date, date-only, contemporaneous publication fallback | Preserve unknown precision/approved estimate basis; invent no observation clock |
| Later clearance, forecast, negation, conflicting update | Correct scope and historical closure; no active presentation from cleared evidence |
| One bad row alongside good rows under the proposed policy | Bad row remains unresolved; valid rows survive without false whole-article verification |
| Missing/duplicate/unexpected targets or tampered evidence | Whole response rejected before publication |
| Optional `thinking_tokens` including zero | Transport and billing contracts agree; usage not lost on semantic failure |
| Search enabled but no invocation/grounding metadata | Do not claim externally grounded verification |
| Web citation versus original article passage | Distinct source identity; no substitution or mixed index namespaces |
| Count/storage/usage failure, interrupted dispatch, repeat execution | Existing cap/stop/reuse safeguards preserved; no automatic paid retry |

## Evidence and current limits

Private ignored scripts/results: `data/gma-evidence-research-20261023/`. `audit_contract.py` and `run_audit.py` reproduce all four independent missing-date failures and the thinking-token counterexample using the deployed image. Source bundle hash remains unchanged; test fixtures contain no accepted replacement observations. Local application files still match the pinned deployed v11 release when inspected.

No claim is made that new prompting has passed a real Gemini request: no new prompt has been sent. No external tool was enabled and no new flood data was accepted. Offline checks prove the defects and candidate test requirements, not future model accuracy. The implementation goal is fewer evidence mistakes, complete diagnostics and contained unresolved outcomes; no LLM can be guaranteed never to return an invalid answer.
