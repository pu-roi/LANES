# V42 junction, clock and article-context repair — bounded acceptance passed

> **Last Updated:** October 19, 2026, 11:33 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

Implemented a separately versioned context successor and promoted it to the default-disabled local backend after acceptance. It keeps co-described numeric/verbal depths with a complete junction, recognizes dotted clocks, carries supported list observation/access context with caution qualifiers, excludes unsupported dateline targets and abstains on incomplete specific locations. Original v19/v40/v41 implementations, predictions, model and references remain unchanged. [Metrics](metrics.json) · [Independent verification](verification.json) · [Approved design](../../plans/ner-context-repair-v42.md) · [Guide](../../guides/ner-backend-preview.md).

## Frozen execution and controls

One isolated Linux attempt processes **371 raw inputs / 1,419 graph outputs**: 24 saved contexts with five cached views, 238 old fixtures in those views, 36 temporal cases, 36 v41 regressions, 36 new scenarios and one reviewed article using 53 saved mentions. The new scenarios cover six families across English, Tagalog and Taglish with supported/counterexample contrasts. Additional unit checks cover clock punctuation, ranges/qualifiers, replacement/report clocks, conflicting measurements, administrative aliases and unmeasured junction rows.

**1,158 pre-freeze tests pass.** Every new scenario and all 310 preserved context/temporal expectations pass in the isolated worker's prescribed views. Code, scoring, source-bound expectations and raw workload were frozen before candidate processing. Freeze SHA-256: `0173994e0e6851ec3896f47138d45387d3dae2d732072b9a940374d8b9b58009`. No retry or post-result extractor tuning occurred.

Actual Docker inspection verifies the qualified image, no networking, two CPUs, 4 GiB memory/swap, read-only root/code/input, PID/capability restrictions and exact mounts. Only the selected raw inputs/cached mentions enter the worker; no model assets, reference/expected-answer files, complete corpus directories or credentials are mounted. Neural/database modules are blocked. The worker exits successfully and is stopped with PID zero.

## Extraction outcomes

The reviewed article's **five complete junction rows now retain their two depth descriptions on the same joint target**. Three complete single-target rows remain supported. All **52 original depth substrings** and all **59 earlier facts** retain source spans, values, roles and qualifiers; unsupported relations are corrected or removed without deleting source evidence. The list clock is captured as observation time, never onset. Vehicle headings and caution remain source-backed, and dateline relations no longer assert an unsupported city flood observation.

**Eighteen of 26 measured rows remain unresolved because their saved location mentions are absent, incomplete or mistyped.** Fourteen are incomplete junctions; four are other specific subjects. A separate unmeasured junction also lacks a complete target set. These are documented recognition limitations, not recovered observations. The original 53 mentions and their provenance remain unchanged; no additions, resizing, retagging or lookup is used.

The successor retains 141 facts, with 101 unassigned. The higher unassigned count includes new list evidence for unresolved rows and removal of unsafe prior assignments. It is not a success count. Each measured row and every previous fact has an individual private disposition.

Across all 120 saved contextual view comparisons, resolved-link and expression sets remain unchanged. The combined view retains **104 TP / zero FP / one FN** on the same 23 exposed silver training references; original/transport/shared-locality/explicit-road views remain 98/0/7, 102/0/3, 100/0/5 and 98/0/7. There are zero new strict incorrect links, supported-link losses, span regressions or qualifier losses. These retained development counts are not a new accuracy measurement. Three reference holds remain held.

## Backend promotion and preservation

After independent saved-output verification, the worker, host validator, projection validator and provenance check use `lanes-context-association-v42`. **1,195 post-promotion software tests pass**, including 36 worker context-boundary cases and rejection of stale v41 provenance. Semantic test expectations are retained; predecessor consumer/test sources were snapshotted before wiring changes.

One cached response-contract check preserves the article URL, input/body hashes, original/effective mentions, proposals and public response shape. It reuses the saved candidate graph and predictions. No neural model or location proposals are rerun, and no fresh live database/API worker inference is claimed after promotion. The preview remains disabled in ordinary local configuration.

All **55 frozen v41 source/test hashes** and **208 protected evidence hashes** match. Historical metadata preservation is 1,538 unchanged entries plus the previously declared application-config change; all 82 excluded metadata entries match. Sets overlap; metadata checks do not open validation/holdout contents. Private preparation, outputs, source evidence, 26 row/59 fact dispositions and promotion receipts remain in the ignored v42 artifact directories.

The task adds no dependency, schema/migration, database write, new article, geographic lookup, frontend, map behavior, upload, commit or push. Learned DEPTH/TIME, real pure-Tagalog measurement, the separate non-flood access omission and recognition-dependent rows remain unfinished. The next task is a separately scoped recognition-gap assessment; no retraining or hidden name fallback is automatic. [@roicambe](https://github.com/roicambe) (Roi Cambe)
