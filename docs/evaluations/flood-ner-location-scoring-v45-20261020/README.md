# V45 saved-output scoring qualification

> **Last Updated:** October 20, 2026, 12:40 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Scoring qualification passes for the missing-junction, boundary-replacement and combined views.** Junction type correction remains unqualified because the saved real workload demonstrates no correction from that family. These are eligibility findings for a later proposal; no application promotion occurred.

[Metrics](metrics.json) · [Independent verification](verification.json) · [Plan](../../plans/ner-location-scoring-v45.md) · [Guide](../../guides/ner-location-scoring-v45.md) · [Unchanged historical v44 outcome](../flood-ner-location-repair-v44-20261020/README.md).

## What changed

The separate v45 scorer validates and normalizes equivalent JSON-list/tuple spans, rejecting malformed offsets/types, wrong labels, duplicates, overlapping spans and stale evidence. **176 scoring-only tests pass**, including all 36 new cases × four methods before/after JSON serialization, original/effective preservation, semantic loss checks and execution guards. No extraction was needed for these tests.

The three previous fixture conflicts now have two explicit contracts. Their original inputs must still retain their original incomplete mentions and unassigned depths. Separate source-authored repaired-view expectations require two complete ROAD spans and both exact measurements attached collectively. Each new expectation applies only to its enabled family or the combined method; other methods retain the original expectation. Neural predictions remain unchanged in both views. The new expectations were authored from fictional source sentences and the user-approved contract, not copied from candidate outputs.

The new code, expectations, workload, acceptance and evidence bindings were frozen before reassessment. All v44 code, raw scores, outputs, predictions and its blocked historical report remain unchanged. **This report supersedes the scoring interpretation only.** The evidence was already exposed; this is neither a new extraction experiment nor independent accuracy measurement.

## Saved-evidence results

All **788 saved inputs** are reassessed: 345 training records, 24 contexts, one article and 418 fictional cases. Each method passes **418/418 applicable candidate checks** and **3/3 conditional original/repaired checks**. All 788 original-neural/control preservation checks pass for each method. Control checks comprise 382 preserved fixture expectations in their declared views plus 36 new original-view integrity checks; all 418 pass. The combination uses all three repaired expectations; each individual family uses one and retains the two disabled-family originals.

| Saved method | Later-proposal qualification | Corrected article occurrences | Restored rows / facts |
|---|---|---:|---:|
| Missing junction names | Pass | 5 | 5 / 25 |
| Boundary replacements | Pass | 3 | 3 / 15 |
| Junction type corrections | Blocked: no real correction | 0 | 0 / 0 |
| Combined | Pass | 8 | 8 / 40 |

These are the same saved v44 article gains; no new correction was executed. **Eleven rows remain unresolved** in the combined view: ten measured rows and the unmeasured junction. Its 40 restored and 53 still-unassigned facts reconcile all 93 affected facts. All 34 target occurrences, 19 affected rows, eight previously complete rows and seven historical misses have private dispositions. Six earlier historical recoveries remain retained; the separate non-flood access omission remains unresolved. No depth is invented for the unmeasured junction.

All methods retain training recognition counts of **823 TP / 12 FP / 17 FN** on unchanged references, with zero newly introduced false positives or lost correct locations. No training location gain is claimed. The same 23 eligible contextual references remain **104 TP / 0 FP / 1 FN**, with zero new incorrect associations or supported losses. Source checks find no span, qualifier, temporal-role or protected-fact losses. Existing recognition errors, meaning/type uncertainties and all three held references remain open.

## Independent verification and preservation

Independent verification recomputes training and association counts, checks the 36 serialized new-case expectations, verifies enabled and disabled repaired-view behavior, and reconciles article/fact/historical counts. It also revalidates saved v44 source offsets, proposal provenance and original execution isolation. All frozen v45 input/code hashes and historical public/private v44 bindings match.

All 208 protected evidence hashes and 55 frozen v41 files remain unchanged, alongside v40/v42 and promoted application bindings. Historical metadata matches 1,538 entries with the earlier declared preview-config change separately accounted; all 82 excluded metadata entries match. These sets overlap. Validation/holdout contents were not opened.

Runtime guards prohibit recognition/extraction calls, neural/database imports, worker/process launches and network actions. Receipts confirm **zero extraction calls, no inference and no worker rerun**. There were no new articles, rules/model/reference changes, database access, API/frontend/plotting changes, uploads, commits or pushes. The backend stays on v42 and the preview stays disabled by default.

## Next recommendation

Separately scope a backend-preview proposal using the qualified saved views and explicit neural/rule provenance. Keep the type family's lack of real correction evidence visible; the combination's qualification does not establish that family's standalone readiness. Do not assume an untested combination qualifies or activate a repair automatically.

Retain the 11 unresolved rows, non-flood access omission, three reference holds, unfinished learned DEPTH/TIME recognition and unmeasured real pure-Tagalog performance. Observation/report/publication time never implies onset. Subsided status/time remain extraction evidence; database history and plotting remain subsequent work.
