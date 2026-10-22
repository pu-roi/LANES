# Existing depth, time and association gap review

> **Last Updated:** October 19, 2026, 3:30 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Outcome

All **405 development records** are accounted for, with one final inventory entry each. Current location references authenticate against the frozen tokenizer, source text, Unicode offsets, membership and language metadata. No dataset, reference, model or production extractor was changed. The **60-passage completed research holdout remained closed**.

The original goal of **learned locations, DEPTH and TIME plus correct per-location relationships remains unfinished**. The retained v19 head still learns six location classes. This audit ran the existing contextual rules once; it did not train or run a neural model.

The immediate obstacle to a depth/time training experiment is incomplete contextual supervision and evaluation, not the absence of a context-rich schema. Existing articles can support annotation work without collecting more articles, but this review does not establish sufficient coverage for every required phenomenon or promise completion before October 25.

## Authenticated reference inventory

| Current partition/language | Records | Matching contextual pilot | Supported for limited diagnostics | Context holds | No matching contextual reference |
|---|---:|---:|---:|---:|---:|
| Training, English | 170 | 12 | 10 | 2 | 158 |
| Training, Taglish | 175 | 14 | 11 | 3 | 161 |
| Validation, English | 38 | 0 | 0 | 0 | 38 |
| Validation, Taglish | 22 | 0 | 0 | 0 | 22 |
| **Total** | **405** | **26** | **21** | **5** | **379** |

The active contextual pilot has 40 records: 26 exact matches and 14 outside current development membership. ID, unchanged passage, source identity/hash, capture version, source window, language and partition were checked. The earlier 40-record pilot is superseded, not another 40 examples. A separate editorial package contains **113 text-only context blocks and zero annotated passages**; those blocks are not contextual ground truth or new admitted samples. This is an inventory of the identified, authenticated packages, not a claim that every possible file on every computer has been exhausted.

All 26 matching pilot records were checked against complete selected passages, saved fact/relation entries and adjacent captured-source context; full source hashes were validated. This was AI-assisted silver review, not human gold verification or a manual reread of every complete source article.

Of the five held contextual references, two have location-boundary revisions that no longer match current location references. The other three have missing time/depth coverage or an unsupported relationship override between different spatial scopes. Original annotations remain intact; concerns are separate proposals. The other 21 remain usable only under their existing pilot reference scope, not as proof of exhaustive association ground truth.

The 26 matched pilots contain 41 DEPTH and 25 TIME spans. After the five holds, the supported subset contains **30 DEPTH / 18 TIME spans**: English 17/4, Taglish 13/14. There are **no authenticated contextual validation references and no complete contextual-negative references**. Missing annotations, empty rule results and unmatched drafts are never negatives.

### Phenomenon coverage in the 21 supported pilots

Counts below are records containing the phenomenon, not occurrence totals. Categories overlap.

| Phenomenon | English | Taglish |
|---|---:|---:|
| Depth linked to multiple targets | 5 | 5 |
| Separate depth facts under a multi-target time | 1 | 0 |
| Collective depth scope | 5 | 3 |
| Maximum/upper-bound depth scope | 1 | 3 |
| Range depth scope | 0 | 1 |
| Observation-time role | 1 | 4 |
| Report-time role | 1 | 4 |
| Unspecified time role | 1 | 4 |
| Subsided status | 1 | 0 |
| Receding status | 0 | 1 |
| Rising status | 0 | 1 |

Multi-target and collective annotations do **not** establish one identical numeric depth everywhere. Six records have a collective summary with no uniform scalar. No supported pilot relation is explicitly labeled `shared` for depth/time; existing `collective` links require interpretation under their recorded conventions, not silent relabeling. Supported onset, clearance, historical-update, negation and forecast-status references are absent from this subset. A weather-forecast passage exists, but its saved status reference is `unknown`, so it cannot establish forecast accuracy. Coverage remains unmeasured where labels are missing.

## One guarded rules execution

All **405 exact passages** had existing, exact-extent private academic use evidence for this diagnostic. An initial 191 holds caused by stale capture-level `not verified` wording were reconciled against existing passage-bound qualification receipts; no publisher policy or permitted extent was expanded. Original history/accounting and source-retention limitations remain.

One Linux CPU worker received only opaque IDs, original text/hash and supported publication metadata. It received no references, partition labels, saved predictions, neural model, credentials or holdout material. The existing offline network/database guard and an additional neural-import guard were active. The immutable qualified image ran with two CPUs, 4 GiB RAM, networking disabled and read-only code/input mounts. The stopped worker exited 0 without OOM; all 405 ID/hash joins and all returned place/sentence offsets verify exactly. Leading whitespace removed internally by the existing rules was offset-translated once against the original input; source text was not rewritten.

| Raw diagnostic output | Count |
|---|---:|
| Location-bearing rule claims | 567 |
| Claims with depth / time / resolved time | 108 / 27 / 9 |
| Forecast-flagged claims | 9 |
| Negated / historical-flagged claims | 0 / 0 |
| Passages without rule claims | 153 |
| Returned place/sentence offset failures | 0 |

These counts are **outputs, not accuracy, recall, article totals or genuine negatives**. Parent-place/context claims remain distinguishable by their existing uncertainty flags. Rules language/partition coverage is stored in the private coverage tables.

Only the 21 supported contextual pilots received partial exact-evidence comparisons. DEPTH: 30 reference spans, 16 uniquely located candidates, 13 exact intersections, 17 reference-only and three candidate-only. TIME: 18 reference spans, one located candidate, zero exact intersections, 18 reference-only and one candidate-only. The one time candidate includes an introductory phrase excluded by the pilot's narrower clock boundary; zero exact intersections does not mean the clock was completely missed. Raw claim fields are not a complete entity or relationship output, so **no DEPTH/TIME precision, recall, F1 or association accuracy is claimed**.

## Source-bound findings

| Category | Finding and bounded implication |
|---|---|
| Demonstrated passage-extraction gap | Several road/list rows contain explicit measurements but return locations without their row-local depths. Missing article headings do not explain these measurements being present but unattached. Sentence/list scope and place detection must be tested separately. |
| Demonstrated qualifier loss | An explicit above-gutter phrase becomes the unqualified gutter gauge; approximate body-part phrasing can lose its approximation in the returned depth field. Preserve raw qualifiers before using any numerical gauge downstream. |
| Demonstrated recognition gap | Explicit Taglish observation-date and digit-based `alas-` expressions are not recognized by current patterns. Report dates, rainfall duration and flood observations need different roles; recognizing a date alone does not justify resolving an onset or clearance instant. |
| Demonstrated coverage limit | A spelled-out measurement range and unusual physical comparisons are not fully represented. Numeric values outside exact configured gauges deliberately retain raw text with a null canonical depth; that abstention is not itself a conversion bug. |
| Reference work | Five contextual pilots need review; 379 current records have no matching contextual reference. None of validation has complete contextual references. Model/rules disagreement cannot fill these labels. |
| Missing passage context | Some selected list windows omit the source heading/clock, and some pronouns require preceding text. Their missing interpretation is a passage-context limitation, not a demonstrated full-article rule failure. No full-article extraction replay was performed. |
| Unresolved semantics | Different indoor/outdoor depths, intersections, collective lists and updated observations require explicit target/scope rules. Receding/subsided is not proven dry/cleared. Observation is not automatically onset. |
| Existing safeguard | Some parent-city depth outputs are already marked context-only. They must not be counted as independent affected-road facts or described as unguarded association failures. |

Individual source identities, offsets, annotations, claims and evidence bindings remain in the ignored private package. Production extraction code is unchanged.

## Prioritized next-task proposal

1. **Freeze the contextual annotation and association specification on existing texts.** Resolve DEPTH qualifier/range boundaries, time-expression roles, shared versus separate targets, updates, uncertainty and genuine negatives. Reconcile the five pilot concerns in a separate proposal. Preserve current location references and partitions.
2. **Complete source-bound contextual references on the existing development records.** Inventory missing labels as annotation work, not new corpus membership. Prepare complete validation references before using them to claim contextual accuracy; keep validation out of rule authoring and the completed holdout closed. Audit whether the unchanged texts actually cover onset, clearance, forecasts and negation; report shortfalls without manufacturing examples.
3. **Propose bounded offline association/rule repairs.** Start with row-local measurement attachment, qualifier preservation and explicit time patterns. Test different depths under a shared time and scope boundaries with fictional acceptance cases and existing training evidence. Do not connect live processing or alter durable modes from this audit.
4. **Then decide the neural experiment.** Learned DEPTH/TIME requires a separately qualified reference/profile revision, exports, training and evaluation. Relationship correctness needs separate assessment; adding entity labels alone does not solve it. Current v19 location training is preserved.

For the **October 25 defense**, a carefully tested interim location-model + depth/time-rule demonstration may be narrower and faster than another roughly three-day training cycle, but it remains a scheduling recommendation requiring a separate decision. It does not fulfill the original learned DEPTH/TIME requirement or guarantee readiness. A complete new annotation/training/evaluation cycle before the defense cannot be promised. No collection is needed to begin the proposed annotation task; data adequacy for every phenomenon remains open.

## Verification and preservation

**659 fresh tests pass**, including **48 new audit tests**, with one upstream Click deprecation warning. The actual command receipt and pre-execution implementation/test/workload bindings are private. Tests cover exact spans/repeated mentions, incomplete references, roles/scopes/ranges, source-use bindings, stale inputs, privacy, network/database/neural guards, read-only verification and existing extraction regressions. Software checks do not establish extraction accuracy.

The final package preserves the initial inventory/source-use decisions, their supported reconciliation, frozen grant, raw execution, 405-entry final inventory, 26 contextual source reviews, 21 partial comparisons, coverage tables and reproducible input/output hashes. **1,383 protected file hashes**, **55 stat-only holdout entries** and **27 stat-only earlier-validation-study entries** verify unchanged. The stat-only checks read no holdout text or labels. [Aggregate verification](verification.json) binds the private manifests and actual receipts.

No new article collection, passage addition, annotation application, partition change, export, neural inference, training, holdout access, live integration, upload, commit or push occurred. Public APIs, dependencies and database schemas remain unchanged. [Current task plan](../../task_plan.md#current-ner-scope-and-defense-checkpoint) · [Operator guide](../../guides/ner-context-gap-audit.md).
