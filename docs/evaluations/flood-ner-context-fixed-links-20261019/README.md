# V38 fixed-reference context repair

> **Last Updated:** October 19, 2026, 8:36 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The bounded contextual repair passes; a LANES connection remains blocked.** All four wrong links were removed, all eight contextual omissions recovered, and every supported v37/baseline-correct link retained. Seven links still require missing/mistyped neural targets. Three contextual holds and unmeasured real-world Tagalog performance remain.

## Fixed-reference results

All methods use the **same unchanged v37 references**: 23 eligible training passages, 105 strict resolved association keys. Twenty-four raw training inputs ran; the held input remained unscored. Three carried reference holds remain unchanged in the 26-counterpart inventory. This is an exposed, AI-assisted silver training-subset diagnosis, not independent accuracy, human gold, validation evaluation or a claim of production generalization. Thirteen connected groups across 19 saved articles limit independence. Incomplete acquisition/history limitations remain.

| Saved method | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Original rules | 14 | 38 | 91 | 26.92% | 13.33% | 17.83% |
| V37 | 90 | 4 | 15 | 95.74% | 85.71% | 90.45% |
| V38 | 98 | 0 | 7 | 100.00% | 93.33% | 96.55% |

Zero observed wrong links applies only to this reviewed subset. It does not establish error-free performance on unseen articles. No references were relabeled to obtain the result. Earlier v36-reference results retain their separate representation contract.

| V38 association slice | Support | TP / FP / FN | F1 |
|---|---:|---|---:|
| Depth | 40 | 37 / 0 / 3 | 96.10% |
| Time | 8 | 8 / 0 / 0 | 100.00% |
| Status | 39 | 37 / 0 / 2 | 97.37% |
| Access | 18 | 16 / 0 / 2 | 94.12% |
| English (11 passages) | 64 | 59 / 0 / 5 | 95.93% |
| Taglish (12 passages) | 41 | 39 / 0 / 2 | 97.50% |

Recognition remains separate: saved neural locations **101 TP / 3 FP / 4 FN, 96.65% F1**; rules-based DEPTH **36 / 1 / 3, 94.74%**; TIME **22 / 0 / 2, 95.65%**. No new strict DEPTH/TIME span FP/FN or qualifier losses occurred. There were no neural inference or optimizer calls. Learned DEPTH/TIME recognition remains unfinished.

## Changes and acceptance

The separately versioned prototype uses grammatical affected/causal/destination roles, event-anchored repeated occurrences with explicit clock resets, bounded water/rescue continuation, scoped bulletin observation timing, and plural flood predicates. It preserves supplied mention spans/types and abstains on unsupported scope; it does not use source identities, proper-name exceptions, geographic lookup or fallback.

All **19 prior errors** have outcomes: four incorrect removed, eight misses recovered, seven recognition-dependent misses retained. All **90 v37-correct**, **14 original-rules-correct**, and **70 pre-frozen previous-correct mappings** are retained. The previously missed baseline-correct local status is recovered. These retention sets overlap and must not be added together.

All **238 fictional cases pass**: English 90, Tagalog 58, Taglish 90. Original 208 cases are preserved. Thirty new cases cover five families across three languages with supported/counterexamples. Before the final execution freeze, three new fixture oracles were corrected: standalone deep/malalim is unspecified, and an explicit occurrence disambiguates it from the deep substring in waist-deep. Original drafts and correction receipts remain private. No real-result tuning followed.

Fresh affected regressions: **1,158 passing tests, including 298 new v38 checks**. The earlier 860-test receipt remains historical. One inherited spaCy/Click deprecation warning remains. Constructed Tagalog behavior does not measure real-world or neural Tagalog performance.

## Execution and preservation

One frozen Linux attempt processed **24 unchanged real inputs + 238 fixtures** with two CPUs, 4 GiB RAM, network disabled and read-only code/raw input mounts. No references, expected answers, models, credentials, validation or holdout were mounted. The container stopped at PID 0, exit 0, without OOM. Cold readiness was 2.094s, measured execution 5.828s and maximum individual extraction 0.005078s. Peak RSS was not newly measured; the 4-GiB isolation limit was verified, and no renewed memory benchmark claim is made.

Strict-set counts were independently recomputed from saved outputs. **1,383 baseline files and 167 v37-bound files** match preserved hashes. Holdout (55 entries) and validation (27 entries) preservation used metadata only. Keep private predictions, reference evidence, per-record errors and all traces outside Git.

## Remaining decision

Contextual repair passes its bounded gate. Overall readiness remains blocked by **seven missing-neural-target links, three reference holds and unmeasured real-world Tagalog performance**. Their disposition needs a separate scoped task; do not silently retag/add locations or introduce fallback. No automatic integration or training follows. October 25 demonstration readiness remains unestablished.

Preserve **345 training / 60 validation / 60 research-holdout passages** and all historical artifacts. No collection, corpus edits, exports, training, application connection, upload, commit or push occurred. Public APIs, dependencies, configuration and database schemas are unchanged.

[Metrics](metrics.json) · [Verification](verification.json) · [Operator guide](../../guides/ner-context-association-v38.md) · [Fixed representation](../../plans/ner-context-representation-v37.md).
