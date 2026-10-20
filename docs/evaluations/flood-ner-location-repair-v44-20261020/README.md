# V44 source-supported location repair feasibility

> **Last Updated:** October 20, 2026, 12:22 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The single study completed; no method qualifies for a later implementation proposal.** The combined method corrects eight article location occurrences and restores 40 facts across eight measured rows. Acceptance remains blocked by three preserved fixture conflicts and a defect in the frozen new-case scorer. No backend promotion occurred.

[Frozen metrics](metrics.json) · [Independent verification](verification.json) · [Scorer diagnostic](scoring-diagnostic.json) · [Approved plan](../../plans/ner-location-repair-v44.md) · [Evidence guide](../../guides/ner-location-repair-v44.md).

## What was implemented and executed

V44 is a separate offline prototype for source-delimited missing junction names, boundary replacements and junction-context road type corrections. It preserves the original neural/control mentions and returns effective mentions, source evidence, action, original ID, rule identity/provenance and abstentions. Clear junction grammar can support a complete road name without a suffix. Ambiguous abbreviated/numbered names, compatible but uncertain landmark/local-area senses and conflicting boundaries remain unchanged. There is no geographic lookup, article-specific name list, name expansion or hidden fallback.

One frozen Linux attempt processes **788 raw inputs**: 345 saved training prediction records, 24 contextual inputs, one article, 36 preserved location cases, 346 preserved context/temporal cases and 36 new fictional cases. The four candidate methods operate on saved v40 combined controls; predecessor location proposals are never regenerated. Original and combined context controls are checked against saved v42 outputs. **560 pre-freeze software checks pass**, bound to the final frozen code; this authoring result did not catch the serialized scoring defect described below.

The worker uses the qualified CPU image, two CPUs, 4 GiB RAM/swap, no network and read-only code/raw inputs. References, expectations, models and credentials are outside its mounts. Independent saved-output verification checks 1,628 candidate context graphs, 58 proposal records across methods, exact offsets, provenance, control preservation, mounts and the stopped worker state. There was no inference, database access or second attempt.

## Bounded results

| Method | Corrected article occurrences | Restored measured rows | Restored facts | Preserved v42 cases |
|---|---:|---:|---:|---:|
| Missing junction names | 5 | 5 | 25 | 35/36 |
| Boundary replacements | 3 | 3 | 15 | 35/36 |
| Junction type corrections | 0 | 0 | 0 | 35/36 |
| Combined | 8 | 8 | 40 | 33/36 |

The combined result leaves **11 rows unresolved**: ten measured rows and the unmeasured junction. Twelve missing occurrences and one incompatible type remain. All 34 target occurrences, 19 previously unresolved rows and 93 affected facts have individual private dispositions; 40 facts are restored and 53 remain unassigned. No depth is invented for the unmeasured junction. All eight previously complete article rows, existing facts, depth/time expression spans, source qualifiers and dateline exclusions are retained. Meaning/type review flags remain recorded.

Across the unchanged 345 training references, every candidate retains the saved combined control's **823 TP / 12 FP / 17 FN** with zero introduced false positives, zero lost correct locations and zero new correct locations. Original saved neural counts are 821 TP / 13 FP / 19 FN. Existing errors are not claimed as fixed. Each candidate retains **104 TP / 0 FP / 1 FN** on the same 23 eligible contextual references, with no introduced incorrect links, supported losses, expression regressions or qualifier losses. Six historical recoveries remain retained; the seventh, separate non-flood access omission remains unresolved. All three reference holds remain held.

Every method preserves all 36 old location cases, 238 old contextual cases, 36 temporal cases and 36 v41 regressions. These are exposed training/source diagnostics and constructed checks, not independent accuracy measurements or real pure-Tagalog performance.

## Why acceptance is blocked

**Serialized scoring defect.** The new-case scorer compares JSON-loaded expected spans (lists) with actual span tuples. Authoring tests use in-memory tuple expectations, so they missed the round-trip defect. The frozen scorer records 26/36, 24/36, 24/36 and 2/36 passes respectively. These numbers are unreliable as measures of extraction correctness. A separate saved-output diagnostic normalizes only representation and finds all 36 original expected cases match for each method. It changes no expectations, frozen code, official score or worker output. The frozen scoring gate remains blocked; no passing replacement score is substituted.

**Preserved fixture conflicts.** Three existing v42 incomplete-target cases expect untouched input mentions and unassigned depth. Applying a corresponding location proposal changes those mentions and resolves depth, conflicting with their unchanged expectations. Each individual family fails one such case; the combination fails all three. These are reported compatibility failures, not waived as recoveries. Their interpretation must be settled before another acceptance design. The article and eligible contextual source checks introduce no incorrect resolved links, but that does not override failed fixture requirements.

**No real type-correction evidence.** The type family makes no supported correction on the real workload. Its fictional success alone cannot satisfy the required real-correction condition. Conservative parsing also leaves junctions whose source subjects include locality context unresolved; no broader-name fallback was added after seeing results.

## Recommended next task and preservation

Separately qualify a scoring successor using JSON round-trip tests and explicit original-control versus repaired-effective-view fixture contracts. Preserve every old fixture and expectation unchanged; any additional repaired-view expectations must be independently specified before a future study. Do not automatically rerun v44, broaden its parser or promote it. Remaining recognition coverage can then receive its own frozen scope.

All 208 protected hashes, 55 frozen v41 files, v40/v42 implementation bindings and promoted application hashes match. Historical metadata matches 1,538 entries, with the earlier declared preview-config change accounted separately; all 82 excluded metadata entries match (sets overlap). Validation/holdout contents were not opened. Original references, predictions and model assets remain unchanged.

No new article, publisher fetch, retraining, application wiring, database write, frontend, history storage, plotting, upload, commit or push occurred. The preview stays disabled by default. Observation/report/publication clocks remain separate from onset; subsided evidence remains available. Learned DEPTH/TIME recognition and real pure-Tagalog measurement remain unfinished.
