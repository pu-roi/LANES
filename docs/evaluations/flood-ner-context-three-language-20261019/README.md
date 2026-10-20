# V36 association review and three-language checks

> **Last Updated:** October 19, 2026, 7:15 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The bounded task is complete; connection acceptance is blocked.** One frozen Linux successor processed all 24 unchanged training inputs and 160 fictional cases. All fictional checks pass. On 23 revised real references, eight incorrect and 31 missed associations remain. No extractor or reference was tuned after inspecting this run.

## Reference review and error accounting

An isolated source-only reviewer read all 23 passages and their 19 distinct complete captured articles, without predictions, extractor output, scores or coordinator history. It retained 14 proposals and corrected nine; the three earlier holds remain unchanged. Separate schema, Unicode, source-use and frozen-tokenizer qualification passes for the 23 references and all 160 fixtures. Repeated contextual literals are accounted for. These are private AI-assisted silver proposals; admitted corpus labels remain unchanged.

Every one of the earlier **13 incorrect / 43 missed** associations has a source-bound disposition. Strict FP/FN counts remain separate from diagnostic pairings. The 56 dispositions classify 48 code defects, three reference concerns and five errors involving missing exact neural targets. All seven previously introduced errors are included in the inventory.

| Outcome of the original 56 errors | Count |
|---|---:|
| Original incorrect key no longer predicted | 5 |
| Original missed key recovered | 19 |
| Original incorrect key still predicted | 7 |
| Original missed key still absent | 22 |
| Independently source-revised reference key; not a method gain | 3 |
| Total | 56 |

Every previously correct association is mapped: 47 retained and one source-corrected. No difficult record disappeared from the 23-reference scoreable subset. The same 24 raw inputs were executed, including the previously held counterpart; all three holds remain outside eligible reference scoring.

## Scores with reference versions kept separate

The v35 reference version has 91 supported associations; the independently revised v36 version has 101. Reference changes do not establish model improvement. The following table compares methods **within each fixed reference version**.

| Reference version / method | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| V35 references / saved original rules | 9 | 43 | 82 | 17.31% | 9.89% | 12.59% |
| V35 references / saved v34 | 46 | 22 | 45 | 67.65% | 50.55% | 57.86% |
| V35 references / saved v35 | 48 | 13 | 43 | 78.69% | 52.75% | 63.16% |
| V35 references / v36 successor | 66 | 12 | 25 | 84.62% | 72.53% | 78.11% |
| V36 references / saved original rules | 9 | 43 | 92 | 17.31% | 8.91% | 11.76% |
| V36 references / saved v34 | 46 | 22 | 55 | 67.65% | 45.54% | 54.44% |
| V36 references / saved v35 | 48 | 13 | 53 | 78.69% | 47.52% | 59.26% |
| V36 references / v36 successor | 70 | 8 | 31 | 89.74% | 69.31% | 78.21% |

On revised references the successor preserves all nine original-rules-correct and all 48 v35-correct links, gaining 61 and 22 respectively. Against saved v35 it removes six incorrect links and introduces one incorrect link. It therefore fails the required **zero total incorrect resolved associations**, despite retaining supported correct links and demonstrating targeted corrections. There are no incorrect resolved TIME or access links in this subset; that does not mean those recognizers are perfect.

| V36 reference slice / successor | Support | TP | FP | FN | F1 |
|---|---:|---:|---:|---:|---:|
| Supplied neural locations | 105 | 101 | 3 | 4 | 96.65% |
| DEPTH expression spans | 39 | 36 | 2 | 3 | 93.51% |
| TIME expression spans | 24 | 21 | 5 | 3 | 84.00% |
| Depth associations | 40 | 29 | 2 | 11 | 81.69% |
| Time associations | 8 | 6 | 0 | 2 | 85.71% |
| Status associations | 33 | 19 | 6 | 14 | 65.52% |
| Access associations | 20 | 16 | 0 | 4 | 88.89% |

Location results use unchanged saved model predictions. This task performs no neural inference, training or new model selection. The expression and association results describe the rule prototype on this exposed training subset, not held-out accuracy.

TIME span F1 declines from saved v35's 89.36% to 84.00%, with false-positive expressions increasing from two to five. Improved time associations do not erase that recognition regression.

## Remaining evidence and language limits

Every remaining error has exact source evidence and a diagnostic cause in the private ledger. The eight incorrect links comprise two depth and six status links. The 31 missed links comprise 11 depth, two time, 14 status and four access links. Seven missed links require exact location occurrences/types absent from supplied neural mentions. The remaining 24 misses and all eight incorrect links are extraction/association defects. Across the 39 strict errors, diagnostics identify 13 fact-value/role/measurement semantics issues, 19 target-occurrence/group-scope issues and seven missing neural targets. Diagnostic categories do not reduce strict counts.

The three held counterparts remain unresolved. On eligible references, two intentionally unresolved relations and 27 explicitly unassigned facts stay visible; they are not negatives. The successor has 48 unassigned facts and no resolved numerical depths or absolute timestamps. Qualifier-preservation checks find zero failures.

| Language | Eligible real passages | Real association support | Real association F1 | Fictional checks |
|---|---:|---:|---:|---:|
| English | 11 | 61 | 75.73% | 64/64 pass |
| Taglish | 12 | 40 | 81.58% | 64/64 pass |
| Tagalog | 0 | 0 | **Unmeasured** | 32/32 pass |

The original 64 fictional cases are unchanged. The new 96 cases cover 16 families × three languages × supported/counterexample. New cases score all four fact kinds and both expression types exhaustively; original cases retain their frozen facet-specific criteria. Expected spans, roles, qualifiers and prohibited inferences were authored before successor extraction. Language judgments are AI-assisted, not human/native-speaker verification; lexical-borrowing uncertainty remains explicit. Proper names alone do not establish Taglish. Passing Tagalog software cases does not measure the neural model's Tagalog accuracy or establish three-language system readiness.

There are **13 connected groups across 19 source articles**, with component sizes 7, 5 and eleven singletons. These exposed training diagnostics are concentrated and contain no genuine complete contextual-negative real subset. The first post-run grouping report incorrectly counted three dictionary field names; a preserved metadata-only correction independently recomputes group identities and transitive components. Two constructed grouping assertions pass separately from the regression suite. No worker, score or reference changed for that correction.

## Execution, verification and boundaries

The authorized worker ran once in the previously qualified image, with two CPUs, 4 GiB RAM, no networking, read-only raw inputs/code and no model weights, expected answers, references or credentials. All 184 identities/text hashes join exactly. Model mentions retain their six labels and original boundaries; original text and Unicode offsets are unchanged. The container stopped with PID 0, exit 0 and no OOM. Controller-observed cold readiness was 2.015 seconds; wall time 4.640 seconds; slowest input 0.00412 seconds. This run does not supply a new peak-RSS measurement.

**561 fresh affected regression tests pass, including 295 new v36 checks**, with one existing upstream spaCy/Click deprecation warning. The suites cover strict accounting, missing references, reference/expected-answer leakage, exact repeated Unicode spans, exhaustive new fixtures, qualifier/role behavior, occupied destinations, single-use claims, competing writers, timeout preservation and blocked neural/network/database access. Historical test totals remain separate.

Hash verification preserves 1,383 baseline files and 147 additional v35 files. Preservation of 55 holdout entries and 27 validation entries uses metadata only; their contents stayed closed. Prior review, repair, execution and failure evidence is preserved. Private manifests and reproducible bindings are recorded in [verification](verification.json); [metrics](metrics.json) contain aggregate values only.

Guidance came from [TimeML's distinction between temporal expressions and event relationships](https://timeml.github.io/timeMLdocs/annguide12wp.pdf), [spaCy's model/rule combination guidance](https://spacy.io/usage/rule-based-matching/#combining-models-and-rules), and [Batayan's separate Tagalog/Taglish evaluation categories](https://aclanthology.org/2025.acl-long.1509/). These inform the study; they replace neither LANES's schema nor source-specific evidence.

**Next gate:** separately scope repairs for the eight wrong resolved links and remaining code omissions, and decide how to address required missing neural targets and the three contextual holds without hidden fallback or relabeling. No further repair experiment or connection follows automatically from this result. Keep learned DEPTH/TIME recognition unfinished on the roadmap. October 25 demonstration readiness is unestablished.

Preserve **345 training / 60 validation / 60 research-holdout passages**, AI-assisted silver status and incomplete-history limitations. No collection, corpus edits, partition changes, exports, neural inference, training, live integration, API/dependency/database changes, upload, commit or push occurred. The desktop can remain off. [Operator guide](../../guides/ner-context-association-v36.md).
