# Source-only reference review and offline association repair

> **Last Updated:** October 19, 2026, 6:25 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Outcome

The bounded v35 task is complete; **the method is not qualified for a read-only LANES connection**. All **64 fictional behavior cases pass**. On **23 eligible revised training references**, the candidate gains **39 correct links** relative to the unchanged rules baseline, loses none of its supported correct links, and introduces **seven new strict reference-disagreeing resolved links**. The zero-new-error gate fails. The candidate was frozen and executed once; no post-result repair, reference change or second extraction occurred.

The candidate retains all **46 v34-correct links under the revised references** and gains two more. All **40 associations previously correct under original references** have an explicit retained mapping. No original correct association silently disappears into the new hold. Software checks and improved aggregate F1 do not override the failed safety gate.

## Source-only review before repairs

A reviewer with `fork_turns=none` received only the **24 prior eligible proposals**, full saved source articles, current location references, conventions and scoped use receipts. It received no predictions, extractor outputs, scores, coordinator conversation or identification of disagreement records. All 24 passages and complete saved articles were read before freeze: **nine retained, fourteen corrected, one newly held**. The two earlier holds carry forward unchanged, giving **26 total dispositions / three holds**.

Corrections address source-supported contextual completeness, temporal roles, status/access, measurement qualifiers and grouped versus local facts. Genuine source-listed collective summaries remain; unsupported cross-observation summaries are not manufactured. The new hold concerns temporal completeness that the existing conventions do not resolve. It remains unscored rather than becoming an empty negative. Text, identities, language, all six location annotation objects and train membership remain unchanged. These are separate private **AI-assisted silver proposals**, not applied corpus changes or human-gold verification. Prior development exposure means the overall work is not universally blinded.

The original input manifest mistakenly included its own then-unfinished bytes. Its four actual source-only payloads all matched their original hashes. The original manifest was preserved and an explicit noncircular authentication receipt bound its actual bytes and the four payloads; no substantive input was regenerated. The reviewer disclosed and bound that limitation.

Guarded qualification passed source-exact Unicode/schema/relation checks and exact frozen-tokenizer reconstruction for all 24 revised proposals, including explicit held status. All **64 fictional records** also passed schema/tokenizer checks. The review freeze predates creation of the successor extractor. Models and training pipelines were not loaded.

## Frozen repair and execution

The standalone successor preserves the raw input/output contract and original six-class mention arrays, including LOCAL_AREA. It repairs bounded omitted-predicate observation updates, named collective ranges, abbreviation-aware list segmentation, durations/report-time abstention, susceptibility/evacuation context and nearby-facility scope. No geographic lookup, article-specific names, reference-driven decision, hidden rules fallback or prediction resizing/retagging is used. Numeric depths and absolute instants are not invented.

All **40 original fictional cases** remain unchanged. The **24 added cases** cover six repair families × English/Taglish × supported/counterexample: parallel updates, collective ranges, abbreviated lists, temporal evidence, flood evidence and facility scope. Fixture location mentions are explicit software inputs; they do not measure neural recognition. Cases score every specified fact kind; unspecified extra kinds remain unmeasured, and a facet pass is not complete contextual accuracy.

One Linux CPU worker processed **88 inputs: the same 24 real passages plus 64 fictional cases**. Revised scoring uses 23 eligible records; the newly held raw passage is still accounted for, and original-reference diagnostic scoring separately covers all 24. Saved original-rules and v34 outputs were authenticated and reused without rerunning them.

The qualified image was fixed at `sha256:a51ce2a6b0f19f382ce96bf63c265e060b37112098176c97c66c23e887794680`. Execution used **two CPUs, 4 GiB, networking disabled, read-only code/raw inputs and no mounted references, expected answers, models, credentials, validation or holdout**. Recorded cold readiness was **2.563 s**, wall time **3.922 s**, and maximum per-input extraction **0.0040 s**. The container stopped at PID 0/exit 0 without OOM; the consumed claim remains and the completed active lease is cleared. No worker peak-RSS measurement is claimed by this task.

## Separate recognition and association diagnostics

The revised scoreable subset contains **11 English / 12 Taglish records**, **13 connected groups**, **105 location references, 37 DEPTH spans, 24 TIME spans and 91 resolved association groups**. Language group counts overlap; they cannot be summed as independent events. References also retain **24 unassigned facts and two unresolved relations**. Candidate outputs have **52 unassigned facts** across scoreable records. Held/missing references are never scored as negatives.

| Measure | Support | Rules F1 | V34 F1 | V35 F1 | V35 TP / FP / FN |
|---|---:|---:|---:|---:|---:|
| locations | 105 | 56.29% | 96.65% | 96.65% | 101 / 3 / 4 |
| DEPTH | 37 | 49.06% | 95.77% | 94.44% | 34 / 1 / 3 |
| TIME | 24 | 0.00% | 89.36% | 89.36% | 21 / 2 / 3 |
| links | 91 | 12.59% | 57.86% | 63.16% | 48 / 13 / 43 |
| links_depth | 40 | 13.79% | 74.63% | 76.47% | 26 / 2 / 14 |
| links_time | 8 | 0.00% | 42.86% | 42.86% | 3 / 3 / 5 |
| links_status | 23 | 17.86% | 40.82% | 48.78% | 10 / 8 / 13 |
| links_access | 20 | 0.00% | 55.17% | 62.07% | 9 / 0 / 11 |


| Measure | Support | Rules F1 | V34 F1 | V35 F1 | V35 TP / FP / FN |
|---|---:|---:|---:|---:|---:|
| ROAD | 45 | 47.89% | 97.78% | 97.78% | 44 / 1 / 1 |
| LANDMARK | 9 | 0.00% | 88.89% | 88.89% | 8 / 1 / 1 |
| LOCAL_AREA | 4 | 0.00% | 85.71% | 85.71% | 3 / 0 / 1 |
| BARANGAY | 13 | 91.67% | 100.00% | 100.00% | 13 / 0 / 0 |
| CITY | 25 | 51.28% | 97.96% | 97.96% | 24 / 0 / 1 |
| PROVINCE | 9 | 90.00% | 94.74% | 94.74% | 9 / 1 / 0 |


The seven introduced strict false-positive groups coexist with **six persistent baseline false-positive groups**; 37 earlier false-positive groups disappear. Association precision/recall are **78.69% / 52.75%**, with F1 **63.16%**. English link F1 is **56.47%**, Taglish **71.64%**, with their actual support and all supported-phenomenon slices in [metrics](metrics.json). These are small **training-only silver diagnostics**, not validation, generalization or operational accuracy. Rules figures cover its returned source-locatable claims; they are not a retrospective oracle for every production rule capability.

Depth recognition also shows a regression: one extra unsupported span lowers revised DEPTH F1 from v34's **95.77% to 94.44%**; TIME recognition is unchanged at **89.36%**. Exact qualifier spans/raw values and recognized range/upper-bound/approximation semantics are preserved by mechanical checks, but free-text reference qualifier notes are not a separately validated semantic score. Learned DEPTH/TIME remains unfinished.

**Original-reference comparison, separately retained:** on all original 24 references, the same saved candidate outputs produce **45 TP / 18 FP / 41 FN**, link F1 **60.40%**, compared with v34 **40 / 30 / 46**, F1 **51.28%**. All six original rules-correct links and all 40 original v34-correct links are retained; eight introduced strict disagreements remain. The revised 23-record score uses a different reference version and denominator, so its numerical increase cannot be attributed wholly to code improvement. Every previous-correct mapping and independent source-review change ledger is private and hash-bound.

No complete contextual-negative real references or adequate onset/clearance evaluation coverage is established by this subset. Fictional checks do not fill those empirical gaps. [Full aggregates, slices and support](metrics.json) · [Verification and bindings](verification.json).

## Remaining blocker

The seven introduced links occur across six passages:

- **Three clocks:** a generic as-of rule takes precedence over explicit subsided/recession meaning, producing observation roles where the independently revised references require recession.
- **Two depth semantics:** one body-gauge phrase is treated as maximum where the frozen proposal uses point; another listed-road relation is collective but its depth fact remains point instead of collective. Correct target offsets alone do not satisfy these semantics.
- **Two status links:** source flood wording supports a plausible active assertion, but the frozen complete references either omit that fact or assign status to another occurrence/group. These remain strict errors and residual reference-completeness questions; neither was relabeled after seeing results.

All 24 raw results have completed private review dispositions, including the new hold. Source-exact evidence and reasons separate these issues from inherited missing/mistyped neural mentions. Those recognition limitations are preserved; no fallback fills missing entities.

## Verification, preservation and next proposal

**470 fresh affected tests passed, including 111 new constructed checks**, with one upstream Click deprecation warning. Checks cover source-only revision integrity, stale hashes, incomplete references, exact scoring, qualifiers, unchanged mentions, repeated Unicode occurrences, privacy guards, occupied outputs, competing owners, consumed claims, timeout partial evidence and failed-launch preservation. Inherited monitoring checks cover timeout/crash/OOM states. Pre-freeze constructed testing caught range ambiguity and a Taglish month/depth homograph; fixes preceded the final freeze. Earlier passing counts remain separate historical receipts.

Saved-output analysis was reproduced into a new destination with all **12 analysis files byte-identical**, without another extractor run. Preservation verifies **1,383 protected file hashes**, **231 additional predecessor files**, the independent review freeze and all frozen v35 code/tests/workloads. **55 holdout / 27 earlier validation entries** were checked through filesystem metadata only. Dataset, model, tokenizer, historical results and partition bytes remain unchanged. Public production code, API/configuration, dependencies and database schemas are unchanged.

Next propose one narrowly scoped follow-up for **recession-time precedence and collective depth semantics**, with independent source-only disposition of the residual status/qualifier questions before a successor freeze. Do not rewrite v33/v34/v35, add proper-name exceptions, silently waive seven errors or repeat tuning under this consumed authorization. This task's failed gate is a completed bounded outcome, not an invitation to connect the system.

Preserve **345 training / 60 validation / 60 research-holdout passages**. No new articles, applied corpus corrections, export, neural inference, training, validation/holdout evaluation, integration, upload, commit or push occurred. The original learned DEPTH/TIME goal stays open. Read-only LANES connection requires its own later acceptance; `rules_only` persistence and live source/status/time/depth/geometry/expiry gates remain intact. October 25 readiness is unestablished; the desktop can remain off.

[Operator guide](../../guides/ner-context-association-v35.md) · [Current task plan](../../task_plan.md#current-ner-scope-and-defense-checkpoint) · [Preserved v34 outcome](../flood-ner-context-association-20261019/README.md).
