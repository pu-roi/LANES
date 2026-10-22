# Offline flood-context association outcome

> **Last Updated:** October 19, 2026, 5:07 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Decision

The bounded implementation/comparison task is complete. **The method is not qualified for a read-only LANES connection.** One frozen attempt completed; **36/40 fictional cases passed**. Relative to the frozen AI-assisted silver references it gained **34 correct associations**, retained all **six baseline-correct associations**, and introduced **20 new reference-disagreeing resolved associations across 11 passages**. Both required zero-new-error and all-fictional-case gates fail. No retuning or second extraction followed the result.

These 20 strict disagreements are not 20 independently established false physical claims. Review separates genuine scope/time errors, incomplete target groups, inherited recognition limitations and reference representation/completeness questions. The fixed scoring and failed decision remain unchanged; references were not rewritten to match predictions.

## Scope and frozen execution

All **26 training counterparts** are accounted for: 24 eligible (11 English / 13 Taglish), two held and unscored. They span **13 connected training groups**; overlapping language group counts must not be added. The workload adds the existing **40 fictional cases**, without adding corpus members. Fixture location mentions are explicit inputs and do not measure neural recognition. The candidate used original authenticated v19 seed-0 training predictions, preserving all six types and exact mention boundaries, including LOCAL_AREA.

The unchanged rules worker processed the 24 real passages; the candidate processed those 24 and 40 fictional cases. Both ran in the qualified Linux image, separately, with **two CPUs, 4 GiB, networking disabled, read-only code/raw inputs and no mounted models, references, saved predictions beyond input mentions, credentials, validation or holdout**. Publication metadata was supported but never used as flood onset. References and expected answers remained in the coordinator scoring package. Neither neural inference nor optimizer/training initialization occurred.

Recorded stopped-container states show PID 0, exit 0 and no OOM for both workers. Observed cold readiness was **5.344 s rules / 3.438 s candidate**; wall times were **6.797 / 4.750 s**. The single-use claim is preserved and the completed active lease is cleared. Worker completion establishes execution, not acceptance.

## Recognition and associations

Strict source-exact spans and exact occurrence/type/scope associations are separate measures. These are **training-only, small-subset silver diagnostics**, not unbiased validation performance or complete-system accuracy. The rules figures measure only its unambiguously source-locatable returned evidence; they are not a retrospective score for every capability of the production extractor. Eight context-only baseline items remain separately unscored, with zero ambiguous/missing evidence gaps. Broad strings are not narrowed or relocated using the references.

| Measure | Support | Rules TP / FP / FN | Rules F1 | Prototype TP / FP / FN | Prototype F1 |
|---|---:|---:|---:|---:|---:|
| locations | 109 | 49 / 16 / 60 | 56.32% | 105 / 3 / 4 | 96.77% |
| DEPTH | 35 | 13 / 3 / 22 | 50.98% | 34 / 0 / 1 | 98.55% |
| TIME | 22 | 0 / 1 / 22 | 0.00% | 21 / 2 / 1 | 93.33% |
| links | 86 | 6 / 47 / 80 | 8.63% | 40 / 30 / 46 | 51.28% |
| links_depth | 41 | 4 / 14 / 37 | 13.56% | 25 / 2 / 16 | 73.53% |
| links_time | 7 | 0 / 1 / 7 | 0.00% | 3 / 3 / 4 | 46.15% |
| links_status | 17 | 2 / 32 / 15 | 7.84% | 4 / 24 / 13 | 17.78% |
| links_access | 21 | 0 / 0 / 21 | 0.00% | 8 / 1 / 13 | 53.33% |


| Measure | Support | Rules TP / FP / FN | Rules F1 | Prototype TP / FP / FN | Prototype F1 |
|---|---:|---:|---:|---:|---:|
| ROAD | 46 | 17 / 9 / 29 | 47.22% | 45 / 1 / 1 | 97.83% |
| LANDMARK | 10 | 0 / 0 / 10 | 0.00% | 9 / 1 / 1 | 90.00% |
| LOCAL_AREA | 4 | 0 / 0 / 4 | 0.00% | 3 / 0 / 1 | 85.71% |
| BARANGAY | 13 | 11 / 0 / 2 | 91.67% | 13 / 0 / 0 | 100.00% |
| CITY | 27 | 12 / 5 / 15 | 54.55% | 26 / 0 / 1 | 98.11% |
| PROVINCE | 9 | 9 / 2 / 0 | 90.00% | 9 / 1 / 0 | 94.74% |


The candidate has 40 correct, 30 false-positive and 46 missed strict associations against 86 resolved reference groups. Ten incorrect groups persist from the baseline representation and 37 baseline false-positive groups disappear; strict gained/lost accounting remains independent of diagnostic pairings. Collective groups are scored intact, not expanded into convenient per-road matches. Exact phrases preserve qualifiers/ranges; point/maximum/collective and temporal-role mismatches fail strict links. Free-text explanatory qualifier notes are not a separately validated semantic metric.

Candidate outputs contain **49 unassigned facts**. References retain **21 unassigned facts and two unresolved relations**; neither becomes a negative or resolved positive. There are no complete contextual-negative real references and no supported real onset/clearance-time references in this subset. No general score is claimed for those slices. [All language, label and supported-phenomenon counts](metrics.json) include support and unmeasured slices.

## Failed behaviors and source-bound findings

- **Second-clause clocks and updates:** a Taglish contrast misses the second road's observation clock. Two historical-update cases miss the new current status/time when the flood predicate is omitted in the second clause.
- **Collective range:** the words and exact range span are recognized, but the named collective link is left unassigned without an extra shared cue.
- **Overassertion and scope:** observed real failures include using an evacuation/proneness clause as active flooding, flattening collective depth into a point, attaching a rise duration as an observation clock, resolving a fragmented road list to only part of its group, and treating nearby facilities as flooded.
- **Recognition/reference limitations:** saved neural mentions include missed/mistyped shared identifiers; this adapter neither repairs them nor uses a hidden rules fallback. Some local status assertions are source-supported but absent from, or grouped differently by, the frozen references. The private ledger records those as concerns, without applying a correction or changing this outcome.

The fictional families passing all four cases were row measurements, shared depth, scope boundaries, forecasts, negation, observation/onset and recession/clearance. Separate-depth/shared-time and range families each pass 3/4; historical updates pass 2/4. Acceptance checks all explicitly specified fact kinds, exact spans/roles/targets/groups and prohibited numerical/absolute-time inventions. Extra unspecified kinds are reported unmeasured; passing a facet is not full-field accuracy.

## Verification and preservation

**277 fresh affected tests passed, including 61 new constructed checks**, with one upstream Click deprecation warning. Coverage includes offsets/repeats, shared versus local facts, ranges, status/time roles, missing references, strict gates, stale bindings, privacy guards, occupied outputs, concurrency and guarded execution. A broader inherited-suite attempt reached its 60-second command deadline and is preserved as incomplete, not passing. The earlier 753-test v33 result is historical and not added to the fresh count.

Saved-output scoring was reproduced into a new destination with **all seven analysis files byte-identical**, without running an extractor again. Preservation verifies **1,383 protected hashes**, all **33 v33 manifest entries**, **135 v32 metadata entries**, and **55 holdout / 27 earlier-validation metadata-only entries**. Frozen inputs, tokenizer bindings, models, datasets, scores, code and tests are unchanged. [Verification and reproducible hashes](verification.json).

## Next gate

Propose a separate bounded repair for clause/time updates, named collective scope, abbreviation-aware list boundaries and nearby-facility abstention. Separately adjudicate the recorded reference completeness/qualifier/grouping questions against source evidence; do not silently change the frozen v33 package or tune references to outputs. Freeze any successor method and criteria before another authorized comparison. No automatic retry or live connection is authorized by this failed attempt.

The original learned DEPTH/TIME objective remains unfinished. The interim location-model plus context-rule demonstration is a temporary priority, not a completed trained contextual model. Keep **345 training / 60 validation / 60 research-holdout** unchanged and the completed holdout closed. No collection, applied annotations, exports, neural inference, training, integration, upload, commit or push occurred. Public APIs, dependencies, configuration and database schemas remain unchanged. October 25 readiness remains unestablished.

[Operator guide](../../guides/ner-context-association.md) · [Current tasks](../../task_plan.md#current-ner-scope-and-defense-checkpoint) · [Historical frozen acceptance specification](../../plans/ner-interim-context-acceptance.md).
