# LANES Gate 3 model-qualification review — October 16, 2026

> **Last Updated:** October 16, 2026, 8:37 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The authorized review is complete: **60 passages from 22 articles, 120 original/A seed 0 assessments and all 391 recorded FP/FN events** are individually accounted for. Codex read every saved passage, including 3 negatives and no-error cases, and checked saved source context/notes for 13 passages (12 with additional surrounding text; one already equals its complete captured source). This is an **AI review under researcher delegation**, not independent gold adjudication.

**Benchmark execution and this review are complete; operational model qualification remains open.** Original seed 0 stays primary at **63.12 strict test F1** and Recipe A seed 0 stays exploratory at **67.72**. No labels, offsets, scores or model choices change. No inference, training or fresh test suite runs in this review.

## Error review

| Mechanical pattern | Original seed 0 | A seed 0 | Combined FP/FN events |
|---|---:|---:|---:|
| wrong class | 94 | 78 | 172 |
| boundary mismatch | 47 | 40 | 87 |
| boundary and class mismatch | 24 | 29 | 53 |
| missed reference | 27 | 22 | 49 |
| extra prediction | 16 | 14 | 30 |

Original contributes **96 FP / 112 FN (208 events)**; A contributes **85 FP / 98 FN (183 events)**. A single wrong-class or boundary mistake can contribute both FP and FN; these are **391 scoring events, not 391 independent mentions or incidents**. All overlapping opposite spans are retained, with no forced one-to-one pairing.

| Reference/predicted class of event | Original FP / FN | A FP / FN |
|---|---:|---:|
| BARANGAY | 9 / 12 | 16 / 6 |
| CITY | 26 / 10 | 19 / 11 |
| LANDMARK | 2 / 20 | 11 / 13 |
| LOCAL_AREA | 5 / 16 | 3 / 15 |
| PROVINCE | 7 / 17 | 7 / 20 |
| ROAD | 47 / 37 | 29 / 33 |

The contextual reading identifies recurrent compound-road fragmentation, adjacent crossing-road merges, absorbed direction/position words, short-code omissions, explicit sitio/barangay confusion, landmark names classified as roads, and place predictions on speaker/byline names, time/common-word fragments or generic structures. These are descriptive findings for the frozen models, not post-test tuning changes.

English accounts for **277 combined events** and Taglish **114**. Their entity support differs (**178 versus 112 reference spans**) and the English material includes dense road/administrative lists; the gap cannot be attributed to language alone. Primary English/Taglish F1 stays **58.89 / 69.68**; A seed 0 stays **60.23 / 79.11**. Full slices for all eight frozen systems remain in [the original test report](../flood-ner-heldout-test-20261016/README.md) and [review summary](review-summary.json).

Original has **18** error-free passages under the frozen references; A has **23**. The reviewed negatives contain 2 English / 1 Taglish passages: original seed 0 has a false-positive prediction in **1/3**, A seed 0 **0/3**. Across robustness seeds A is not uniformly better: A seeds 1/2 have false positives in **2/3** each, original seeds 1/2 in **1/3 and 0/3**. These tiny denominators are not field false-activation estimates, and NER mention prediction is not complete flood-claim evaluation.

Original/A family mean test F1 remains **68.46 / 70.24**, sample SD **4.85 / 2.20 percentage points**. Rules stay **58.97 six-class F1**, with LOCAL_AREA unavailable; native LOC stays **67.02 on the separate coarse task**. No higher-scoring seed is promoted, no significance claim is made and coarse scores are not interchangeable with six-class scores.

## Reference questions remain separate

| AI review question category | Passage count |
|---|---:|
| possible reference type ambiguity | 7 |
| possible reference scope ambiguity | 3 |
| possible reference completeness gap | 1 |
| possible reference boundary ambiguity | 1 |
| unresolved geographic identity | 1 |
| annotation convention needs documentation | 1 |

Fourteen passages carry review questions, including institution-versus-physical-facility use, bare locality/administrative identity, an unlabelled geographic name inside an administrative list, designator boundaries, project-title/asset scope, source spelling and shared elliptical identifiers. Existing captured context was used; no new material was fetched and no geographic identity was invented.

**57 event assessments** retain unresolved reference interpretation; the other **334** have context-supported model disagreements under the current profile. This does **not** establish 57 erroneous labels or excuse those predictions: one question may affect multiple paired events, and all **391** remain in the official scores. These are same-agent AI judgments, not independent truth. No corrected or counterfactual F1 is produced. Detailed rationale, IDs, offsets and hash-bound source references remain in the ignored passage/event/question ledgers.

## Qualification dispositions

| Claim/use | Disposition | Remaining evidence |
|---|---|
| Frozen private academic research benchmark execution | supported_scoped | Report AI silver provenance and historical acquisition/use limitations. |
| Descriptive original/A six-class comparison | supported_scoped | No test-driven seed promotion, significance or field-accuracy claim. |
| Complete/geographically verified place labels | pending | Resolve a versioned reference-scope specification and any proposed revisions separately; preserve this benchmark. |
| Independently verified accuracy | unsupported_by_current_evidence | Independent reference review for independent-accuracy claims; not a prerequisite for this authorized AI review. |
| Six-class operational model qualification | pending_not_qualified | Freeze explicit qualification criteria prospectively; retain unsupported slices and fresh untouched holdout if tuning occurs. |
| Contextual flood-fact associations and severity | pending | Separate association/severity reference specification and held-out evaluation. |
| PSGC/OSM identity and road placement | pending | Qualified parent/identity resolution and isolated article-grounded placement checks. |
| Selected trained-model CPU and clean Linux compatibility | pending | Bounded offline selected-model loading, tokenizer parity and constructed inference in target CPU/Linux runtime. |
| CPU latency, memory and long-article behavior | pending | Declared cold/warm workload, token-length limits, p50/p95, peak RSS and visible long-article failures. |
| Operational missing/corrupt-model handling | pending | Isolated failure injection, version traceability and fail-closed publication; no silent regex success labeled NER. |
| Publication safety and autonomous lifecycle | pending | Separate negative/ambiguous/stale-source, duplicate/retry/rollback, geometry and lifecycle checks on isolated records. |
| Distribution, production use and deployment | not_established_deferred | Use-specific decisions before those uses; source-use status is unchanged by this review. |

The roadmap's proposed per-label precision/recall, association, safety and performance targets remain **proposals**. This review neither adopts nor weakens them retrospectively. Low measured slices and absent runtime/contextual evidence prevent a production-readiness claim without fabricating a new pass/fail threshold. Private research admission remains the saved delegated project disposition, not publisher permission or a dataset license.

## Remaining qualification work before Gate 4

1. **Prepare the bounded remaining Gate 3 qualification specification:** Hash-bound reference-question addendum and constructed regression matrix for compound/split roads, short codes, explicit/shared locality cues, named institutions/assets, bylines, time/common-word/generic-structure negatives. Do not alter or rescore the exposed benchmark.
2. **Plan and run a separately authorized offline compatibility/failure/performance qualification:** Fixed original-primary/A-exploratory checkpoint roles; CPU and target Linux offline load/tokenizer parity, constructed probes, corrupt/missing-model behavior, resource and long-text measurements. No runtime installation or dependency change is performed here.
3. **Resolve evaluation scope and qualification criteria prospectively:** Clear supported/unsupported label and language slices; independent review if independent-accuracy claims are pursued; fresh untouched grouped holdout for future tuning, no test-driven seed choice.
4. **Gate 4 isolated integration only after required model-qualification evidence:** Versioned model-loading/neutral fact-helper boundary, contextual association and source/identity/placement checks, visible failures and shadow comparisons without public writes; separate Gate 5 system safety and deployment authorization.

**Immediate next task:** prepare the bounded remaining Gate 3 qualification specification: a reference-scope addendum, constructed regression matrix and prospective CPU/Linux/failure/performance qualification plan. This supplies a concrete specification for the next execution; it does not rerun or tune on the exposed test set. Gate 4 runtime integration has not started and requires its own model-qualification evidence. Independent reference review is required for independently verified accuracy claims, not for conducting this authorized AI review.

## Verification and preservation

Artifact validation passes for exactly **60 unique passages / 22 articles / 120 model assessments / 391 unique events**, including every error-free and negative passage. **42 model/class/language count slices** reconcile with unchanged saved FP/FN metrics; all overlap links, 14 question references and 10 input bindings verify. The sealed six-model test experiment is revalidated without inference.

All **11,676 prior artifact files**, **23 pinned model files**, **22,759 research-environment file stats**, **109 CLI package versions**, requirements and .env remain unchanged. Research-environment preservation checks size/mtime with bytecode excluded, not complete environment content hashing. Original/recovered/failed runs, corpus/context/source-use flags and frozen partitions remain preserved. The earlier 59 software tests and 240 test-metric checks remain historical execution evidence; they are not fresh tests in this review.

No new article or passage-body copies are generated. Review ledgers bind to the existing admitted JSONL and saved request via IDs, hashes and source ranges; source bodies are not copied into provenance. Public reports contain metadata and aggregate findings only, with no passage quotations.

Historical evidence limitations remain unchanged: two restored references match their recorded hashes without formal reconciliation, the IPOPHL historical reference remains hash-divergent, and the detailed desktop predecessor remains unreconciled. Eleven invalid-fixture references and ten copied-manifest aliases remain separately classified. Six paper/dataset and six production/model-distribution outcomes remain separate deferred uses.

[Verification](verification.json), [qualification matrix](qualification-matrix.json), [reference-question counts](reference-question-counts.json), [private output hashes](private-output-hashes.json). Private checkpoint: backend/training/flood_ner/artifacts/model-qualification-review-20261016-v1, with passage-review.jsonl, event-register.jsonl and reference-questions.json. Inputs and this review retain explicit AI provenance.

No public API, schema, CLI, dependency, model-selection, source-use, deployment, correspondence, commit or push changes occur. No inference, training, annotation modification or test rerun occurs. [Task plan](../../task_plan.md); [training roadmap](../../plans/lanes-ner-training-plan.md).
