# Saved-pool feasibility for a separate 400-sample revision

Completed October 16, 2026. Project attribution: [@roicambe](https://github.com/roicambe) (Roi Cambe). All original data and decisions remain unchanged.

**No qualifying replacement selection was found.** All four tested scenarios are mathematically infeasible while retaining the 332 unaffected samples and their splits, all 60 test records and ten training pilots. HiGHS returned status 2 for each scenario, and independent reruns matched. This is a conclusion about the tested, hash-bound candidate universe—not every possible future sentence window, newly annotated passage or authorized rebalancing.

| Scenario | Total available records including 332 fixed | Result |
|---|---:|---|
| Existing publishers, unused saved passages | 811 | Proven infeasible |
| Existing publishers plus 43 location-positive paragraph proposals | 854 | Proven infeasible |
| Additional RMN publisher, unused saved passages | 1,225 | Proven infeasible |
| Existing publishers plus 106 positive/negative paragraph proposals | 917 | Proven infeasible |

The 1,340 saved annotations from 342 articles and their source/publication evidence passed structural and hash checks. Of 902 unused passages from non-held sources, nine overlap or nearly copy a fixed sample, leaving 893. These are candidates, not admitted training data. The 106 shortening proposals are full source paragraphs within held selections, with exact text/offsets retained; projected language, location spans and negative labels are explicitly unreviewed. No prospective labels were accepted.

## Limiting constraints

GMA already contributes its maximum 160 fixed samples, so none of its unused candidates can enter without changing a fixed record. RMN has 414 unused Taglish candidates and zero reviewed English candidates, failing the required 25-per-language publisher minimum. Without shortening, ABS-CBN and Philstar offer at most 49 unused candidates for 68 slots. Philstar also has only 16 fixed Taglish samples; the location-positive shortening scenario raises its relaxed total to only 20, below 25.

Even the broader positive/negative paragraph scenario has these necessary support deficits after accounting for publisher saturation, article saturation and frozen group assignments. The figures are relaxed upper bounds; further constraints can only reduce them.

| Partition / language | Support | Available upper bound | Required |
|---|---|---:|---:|
| Training / Taglish | ROAD spans | 54 | 60 |
| Training / Taglish | ROAD-positive passages | 26 | 30 |
| Validation / English | LANDMARK spans | 6 | 10 |
| Validation / English | LOCAL_AREA spans | 7 | 10 |
| Validation / English | ROAD-positive passages | 9 | 10 |
| Validation / English | ROAD-bearing articles | 4 | 5 |

## Recommendation

Do not assemble a nominal 400 by relaxing quotas or counting unreviewed language/labels as established. The next narrow task is to identify and review additional suitable windows in already saved captures that supply the exact deficits above, then assess the proposed selected extents for source use. This is not new URL collection and does not expand the exhausted 300-candidate/200-article budget. If that cannot supply the gaps, seek separate authorization for limited train/validation rebalancing beyond the 68 held slots, keeping the test partition, pilots and hard quotas. This analysis does not establish the minimum additional changes or authorize that revision.

Five contextual pairs would be affected by future replacement: two English and three Taglish. The other 35 retain all five category minima and both-language representation. A later revision must add five newly reviewed training-only pairs to restore 20 per language and recheck category/article support. No contextual record changed here.

Current status remains 400 location records / 40 contextual-v3 pairs, 200 English / 200 Taglish and 280/60/60 partitions. Project-basis coverage remains 125 articles / 332 passages adopted and 14 articles / 68 passages held. Source admission and successful exports remain zero. The unavailable detailed desktop predecessor remains unreconciled.

Verified 2,621 earlier files unchanged and all 23 model files by hashes without loading. No model inference/training, new collection, admission, API/schema/dependency change, messages, uploads, deployment or Git publication. A focused run passes **99 tests** (13 new constructed analysis guardrails plus existing cohort/revision/qualification tests), with one deprecation warning in 6.50 seconds. This is separate from solver results, annotation quality and any historical full-suite baseline.

The private ignored folder is `backend/training/flood_ner/artifacts/revision-feasibility-20261016-v1/`; open its START-HERE.md. Earlier stage manifests and scenario results are preserved; final-manifest.json binds the completed analysis. See [quota evidence](quota-blockers.json), [scenario/replay results](scenarios.json), [candidate register](candidate-register.csv), [exclusions](exclusion-register.csv), [source-use gaps](source-use-gaps.csv), [context impact](context-impact.json), [verification](verification.json) and [method notes](paper-method-notes.md). Public reports contain metadata only.
