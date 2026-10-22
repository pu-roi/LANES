# V7 workflow repair and isolated saved-evidence reassessment

> **Last Updated:** October 17, 2026, 10:44 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

All ten workflow defects have replacement implementations and constructed regression coverage. The development proposal remains **345 training / 60 validation**. **V7's claim that 60 test passages were sealed and training was unlocked is superseded.** Its files, including its unauthorized binary export, are retained as historical evidence and must not be used as successor training/evaluation inputs.

The last audited baseline was 49 conditional test passages. Applying the repaired evidence gates retains **22**, with **27 baseline members now held**: ten lack supported historical comparison, ten lack supported reviewed grouping, and seven have both limitations. These holds preserve the material; they do not delete data or prove contamination. All eleven new v7 windows remain held after candidate-specific disclosures affected their five source groups. Prior exposure quarantines remain in force.

| Current joint conditional proposal | Positive | Genuine negative | Total | Missing positives | Missing negatives |
| --- | ---: | ---: | ---: | ---: | ---: |
| English | 12 | 2 | 14 | 15 | 1 |
| Taglish | 7 | 1 | 8 | 20 | 2 |
| Combined | 19 | 3 | 22 | 35 | 3 |

The target remains **60 passages: 30 per language, each with 27 positives and three genuine negatives**, at most three passages per article. Counts describe one compatible saved proposal, not all potential passages on the internet. Global collection accounting and history remain unresolved, so even these 22 are conditional. No measured model improvement or human gold verification is claimed; references remain **AI-assisted silver**.

## Repairs and regression mapping

Replacement helpers live in [research_capture.py](../../../backend/training/flood_ner/research_capture.py) and [research_review.py](../../../backend/training/flood_ner/research_review.py). They never import or execute preserved private-package helpers. Frozen historical capture helpers, exporters, schema and tokenizer rules remain unchanged.

| Finding | Replacement and regression evidence |
| --- | --- |
| 1. Fabricated readiness and fixed guard/span totals | Status derives from executed selection, actual validated records and executed guards; arithmetic, quotas, evidence bindings and blockers reconcile. Fabricated selections, post-selection mutation, absent guards and incorrect quotas are rejected. |
| 2. Missing acquisition preflight | The grant binds the exact preflight payload, implementation/tests, original receipts, predecessor journal/replay and accounting scope. Alternate proofs and stale baselines are rejected. Unknown exposure or interruption blocks dispatch. The review-only authorization cannot create a live session. |
| 3. Unfiltered concatenated selection | All six evidence gates precede joint selection. Historical/exposure groups, duplicates, overlapping windows, alternatives, different source versions and article caps are checked; baseline reductions are recorded. |
| 4. Missing references treated as negatives | Only an explicitly complete reviewed empty reference qualifies. Missing/null entities, the shared schema's empty-list default, incomplete references and contradictory flags are rejected. |
| 5. Direct training-format serialization | The replacement export entry point always rejects review-only scope and creates no output. Successor admission, freezing and model-tokenizer-qualified export remain separate. |
| 6. Candidate identity leakage | Both coordinator files have strict allowlists and hash/total reconciliation. Candidate IDs, URLs, titles, text, labels and arbitrary fields are rejected. Existing disclosures remain quarantined. |
| 7. First-occurrence-only annotation | Explicit spans are required for each applicable occurrence. Unreviewed repeated literals are rejected; ambiguous typing stays held. A non-entity omission needs exact spans, a reviewed reason and bound evidence. |
| 8. Unguarded parsing and unfinished accounting | Body reads and parsing share the guarded outcome path. Every attempted GET retains headers, partial bytes, a failure outcome and unresolved reservation. Parsing/accounting failure halts the session. |
| 9. Malformed identities and response types | Headers are persisted before body processing. Malformed identities, wrong content types, redirects and header/body alias overruns halt processing while preserving evidence. TLS is verified; redirects and automatic retries are disabled. |
| 10. Receipt overwrite and competing writers | Exclusive receipt creation, an authorization-bound claim location, a non-reopenable authorization, thread exclusion and a hash-chained append-only journal reject overwrite, reuse, tampering and interrupted writes. |

Constructed tests: [capture regressions](../../../backend/tests/test_flood_ner_research_capture.py), [review regressions](../../../backend/tests/test_flood_ner_research_review.py). No private test content appears in fixtures. Mocked transports are the only HTTP transports exercised in this task.

## Isolated evidence review

A dedicated curator ran without inherited coordinator conversation, development annotations, model predictions or historical scores. It received scoped conventions, source-use guidance, source-only history and hash-bound exclusions/disclosure snapshots. The coordinator received only the allowlisted [aggregate status](curator-aggregate-status.json) and [verification manifest](curator-verification-manifest.json).

The curator reviewed five complete v7 captures and eleven proposed windows. Supported annotation changes are separate from the originals. Across the saved proposal pool, **139 complete references / 182 entity spans** pass shared location-only schema, source-exact Unicode offsets, non-overlap and frozen `lanes.xx.address-v2` checks; **62 unknown references remain held and unscored**. Six inherited negative flags were corrected separately to agree with complete reviewed empty references. Four repeated literal occurrences in non-location contexts receive separately evidenced omission decisions, without global type propagation.

All 60 v7 membership claims are accounted for: 22 retained conditionally, 27 prior members held and eleven new windows held. Mechanical correctness of a reference does not clear source-use, publication, language, historical exposure or grouping gates. Eighteen freshly executed private guards pass; no guard count or entity count is copied from v7.

Private repair/reassessment outputs are in ignored versioned v8 packages. Their ledgers contain dispositions, corrections, source and evidence bindings, full rejection reasons, baseline reductions, input/output hashes and replay instructions. They are not included in Git or the public report. The known development tokenizer failure remains outside usable membership; no tokenizer or original annotation was changed.

## Accounting and missing evidence

No network operations occurred. The recorded v5 claim of 649 identities plus four uncertain slots / 84 publisher attempts and v7's later claims remain historical assertions, not certified remaining allowance. Existing overruns and uncertainty are not reset or refunded. Missing original receipts and unquantified response exposure keep acquisition blocked despite unused numerical allowance.

Required recovery evidence is specific:

- Byte-original request arguments and complete unfiltered request/result receipts for all eleven v5 search calls, including tool-call IDs, timestamps and request/result bindings.
- Isolated reconciliation of all response identities, aliases, ambiguous tokens and truncation against reservations and the saved journal. Recreated summaries or rerun searches cannot replace original receipts.
- Independent outbound transport/publisher evidence for the inherited 84-attempt history, including failed requests, redirects, interruptions and retry settings.
- Resolution of unquantified omitted-response exposure. Its count remains unknown, separate from the four preserved uncertain slots.
- Source-specific historical comparison and conservative reviewed component evidence for held members. Different dates or a storm-name blacklist cannot establish independence.
- Supported source-use/admission decisions and the remaining joint language/polarity coverage. Exposure quarantines cannot be cleared merely by relabeling or rewriting passages.

Earlier scoped desktop coverage and the user's knowledge statement remain distinct from verified exhaustive history. Unavailable historical receipt/helper payloads are not newly declared recovered. No curator text is opened in the coordinator to fill these gaps.

## Verification and next gate

Fresh final checks: **292 passed / one existing Windows symlink test skipped**, including **61 new repair regressions**, plus 110 passing subtests. The final focused run also records 61 passing tests and 62 passing subtests in a separate machine receipt. The only warning is the existing spaCy/Click deprecation warning. Eighteen private rejection guards pass separately. **All 7,067 protected files retain their original bytes**, including v7 artifacts, earlier reviews, historical data/models/scores, tokenizer and frozen helper code; no file is missing or changed. These are fresh results, separate from every historical test count.

See [verification.json](verification.json) for reproduction commands, protected-file preservation and implementation/test hashes; [metadata_hash_manifest.json](metadata_hash_manifest.json) binds the report artifacts. The isolated curator also verifies 214 predecessor files unchanged.

This task completes the repairs and saved-evidence reassessment with **readiness blocked**. Next recover and reconcile the specified evidence, resolve supported holds and plan any remaining independent-test work under a separate authorization. Only after the independent-test requirements pass may another task prepare admission, grouped partition freezing, isolated test sealing, qualified exports and the desktop GPU handoff. Actual training follows that preparation. Historical fixed-400 launchers/exporters must not be reused unchanged.

No public API, dependency or database schema changed. No collection, budget increase, admission, freeze, sealing, training-format export, inference, training, upload, commit or push occurred. **The desktop can remain off.**
