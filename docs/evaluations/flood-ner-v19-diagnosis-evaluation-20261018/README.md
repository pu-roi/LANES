# Corrected v19 diagnosis and frozen research comparison

> **Last Updated:** October 18, 2026, 9:59 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

Completed locally on the laptop using unchanged **345 training / 60 validation / 60 research-holdout passages**. V19 control remains the validation-selected family and seed 0 remains primary. The one-time holdout comparison completed once; it does not select a replacement model. No collection, annotation/partition change, retraining, application integration, deployment, upload, commit or push occurred.

## Development diagnosis

All 405 development records were scored by each of the three selected control checkpoints: **1,215 predictions**. Python 3.11.17/spaCy 3.7.5 CPU inference reproduces every desktop precision, recall and F1 within 1e-8. References contain 840 training and 85 validation spans.

| Seed | Train P | Train R | Train F1 | Validation P | Validation R | Validation F1 | F1 gap (points) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | 98.44% | 97.74% | 98.09% | 75.32% | 68.24% | 71.60% | 26.48 |
| 1 | 94.26% | 93.81% | 94.03% | 73.75% | 69.41% | 71.52% | 22.52 |
| 2 | 92.89% | 93.33% | 93.11% | 66.67% | 65.88% | 66.27% | 26.84 |

Seed 0's 26.48-point gap is consistent with memorization and differences between fitted and validation examples. It is v19's own measurement; the earlier 99.40% training score belonged to v16. Training is not continued to drive validation toward 100%.

| Seed-0 label | Train spans | Train F1 | Validation spans | Validation F1 |
|---|---:|---:|---:|---:|
| BARANGAY | 85 | 100.00% | 19 | 74.29% |
| CITY | 308 | 99.35% | 23 | 85.11% |
| LANDMARK | 58 | 91.23% | 7 | 58.82% |
| LOCAL_AREA | 19 | 97.30% | 12 | 58.82% |
| PROVINCE | 169 | 99.12% | 10 | 85.71% |
| ROAD | 201 | 96.50% | 14 | 48.00% |

Seed-0 validation language F1 is 69.47% English and 74.63% Taglish. The 60 validation passages form only **20 connected groups**. Taglish validation has zero ROAD support and one LANDMARK span. Unsupported slices remain unmeasured; the JSON tables retain their false positives. Full strict TP/FP/FN, precision/recall/F1, supported-label macro, language and language/label tables are in [development metrics](development-metrics.json) and [gaps](development-gaps.json).

All 60 validation references were reviewed without edits; 22 passages have an error in at least one seed. The focused review read 14 complete saved articles and 28 relevant training passages, including all 16 positive LOCAL_AREA training passages. Road name boundaries, directions, compound roads and list/shared-designator context account for demonstrated errors. Source context supports keeping the frozen references instead of following model predictions. One school/gymnasium proper-name-boundary question remains unresolved and is still scored against the unchanged reference.

LOCAL_AREA has only 19 training spans versus 12 validation spans. Seed 0 misses seven validation LOCAL_AREA spans. This is a coverage/context limitation, not proof that a particular new recipe will fix it. Existing street-list training examples include boundary cues, so low ROAD F1 does not establish that all road examples are absent or incorrectly annotated. The [review summary](development-review-summary.json) records development-only proposals.

The authenticated desktop archive supplies selected/last-step summaries, not raw learning curves or stdout. Seed 0 selected step 945 and reached the 1,000-step limit; seeds 1/2 selected 595/665 and report stopping at 770/840. These summaries do not establish the shape of learning curves. No logs were recreated by training.

## Qualified evaluation boundary

The received archive is 418,467,210 bytes with SHA-256 `a6675c403216146bbf42da8790df66112a2926ebd63dedbf641c7c1cf6649345`. All 132 entries (131 payload files plus manifest) authenticated. Received originals remain private and unchanged; only reviewed new helpers were installed in absent checkout paths.

Twelve proven transport differences are qualified separately: **ten Python AST equivalences and two parsed-CSV row equivalences**. Exact original/actual hashes remain in private versioned receipts; application/data bytes were not overwritten and general hash checks were not weakened. Initial preflight rejected Python 3.11/3.12 AST metadata differences before model/holdout access. A separately preserved v2 receipt uses runtime-neutral syntax encoding that omits only empty3.12 type-parameter metadata, retains all literals/statements and still requires exact newline-only byte differences. All twelve actual proofs were then checked in both runtimes.

Neural inference uses the existing Python 3.11.17/spaCy 3.7.5 environment and frozen tokenizer/resources. Rules use the existing Python 3.12.14 backend environment in a separate worker receiving **raw text and opaque IDs only**. Network, subprocess and database operations are blocked inside that worker; inert import-time engine declarations do not create drivers/connections. Frozen bindings include package initializers, transitive application sources and unchanged assets.

The isolated curator received only scoped model/tokenizer files and source-only development/history exclusion metadata. Development references/predictions, coordinator history and historical score reports were excluded. Individual holdout texts, IDs, labels and predictions remain private. No development scoring occurs in the holdout process.

## One frozen holdout comparison

The locked holdout contains 60 passages/96 location spans, 30 English and 30 Taglish; each language has 27 positive and 3 genuine negative passages. Thirty connected groups, article caps, source-exact references, original Unicode spans, tokenizer alignment, alternatives, duplicate/overlap and cross-partition metadata checks passed before inference.

| System | Precision | Recall | Strict micro F1 | Negative passages with FP |
|---|---:|---:|---:|---:|
| control-seed-0 | 77.91% | 69.79% | 73.63% | 0/6 |
| control-seed-1 | 65.98% | 66.67% | 66.32% | 2/6 |
| control-seed-2 | 69.31% | 72.92% | 71.07% | 2/6 |
| v16-seed-0 | 75.53% | 73.96% | 74.74% | 1/6 |
| v16-seed-1 | 78.41% | 71.88% | 75.00% | 0/6 |
| v16-seed-2 | 75.26% | 76.04% | 75.65% | 1/6 |
| rules | 60.53% | 47.92% | 53.49% | 0/6 |

Control three-seed mean is **70.34%**, sample SD **3.71 points**. V16 mean is **75.13%**, sample SD **0.47 points**. V19 seed 0 language F1 is 74.47% English/72.73% Taglish. All systems are evaluated on the identical references. Control is retained from validation; these results do not change it.

Paired connected-group percentile bootstrap, **10,000 draws, seed 0**, reports F1 differences in percentage points:

| Comparison | Lower95% | Upper95% | Defined draws |
|---|---:|---:|---:|
| control-seed-0 minus rules | 2.29 | 35.99 | 10000 |
| control-seed-0 minus v16-seed-0 | -8.04 | 5.79 | 10000 |
| control mean minus v16 mean | -9.60 | -0.54 | 10000 |

The seed-0 control/v16 interval includes zero. The three-seed mean difference favors v16 on this fixed silver holdout; this uncertainty is conditional on the recorded checkpoints and groups, not an assessment of all possible training seeds or deployments. V19 does not establish an overall holdout improvement over v16. Full class/language support, negative errors, means, sample deviations and uncertainty are in the [allowlisted aggregate](holdout-aggregate.json).

Holdout LOCAL_AREA has **zero reference spans**, so it is unmeasured even where systems emit false positives. V19 primary LANDMARK F1 is 20% on seven spans; this is reported as a limitation, not a new tuning signal. No individual holdout errors were disclosed to development.

Exactly one persistent attempt claim binds the **original handoff, holdout qualification and protocol**, independently of freeze/output paths. The first failed qualification created no claim; after qualification passed, the sole evaluation succeeded. Its claim persists and a new destination or freeze cannot authorize a second comparison.

## Verification, limits and next gate

Fresh final checks: **269 tests and four subtests** pass in the backend environment; **61 tests** pass in the neural environment. The latter are a runtime recheck, not additional unique tests. One existing spaCy/Click deprecation warning is recorded. These replace no historical counts (including the earlier367-test preparation evidence).

The143-file current snapshot and154 earlier protected-input bindings reconcile unchanged (overlap is not counted as unique files); the isolated evaluator also rechecked all frozen holdout/resource/scoped/source bytes after inference. Both initial development setup failures and the pre-attempt AST qualification failure remain preserved privately. [Verification hashes](verification.json).

References remain **AI-assisted silver**, with incomplete external source history and acquisition accounting. The research holdout is evaluated and its aggregate results are now exposed; it is not certified-fresh or human-gold, and cannot serve as an untouched tuning set again. The rules comparison measures location mentions, not full flood-fact/activation or road-placement correctness.

This completes the requested diagnosis and frozen research evaluation within **Gate 3**, not Gate 4 application integration or production acceptance. Next is a separately scoped development decision using the existing-data diagnosis: source-bound boundary adjudication and constructed checks of road/list/locality context before any bounded experiment. No new articles are required by that proposal and no further experiment is authorized here. Clean Linux/resource/latency qualification and integration/release gates remain open. Near100% F1 is not an acceptance requirement.
