# Corrected v19 desktop experiment and separate laptop evaluation

> **Last Updated:** October 19, 2026, 12:03 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 19 follow-up:** The report below preserves the October 18 desktop completion checkpoint. The [subsequent laptop diagnosis/evaluation](../flood-ner-v19-diagnosis-evaluation-20261018/README.md) completed the one-time research evaluation and supersedes the original pending statements. Checkout synchronization to `4875cef` preserves the original desktop helpers privately and adopts the qualified laptop evaluator; no holdout is accessed or re-evaluated on desktop.

**Desktop experiment completed: five successful training runs; corrected control retained, seed 0 primary. Research-holdout evaluation remains pending on the laptop.** No holdout references were accessed on desktop. No deployment, commit or push.

The checkout remains `roi-branch` at `882049cb3a709099ef3547a98dad57905f90f84a` with new helpers/reports uncommitted. Frozen trainer, registry, configurations, package manifests, 345/60/60 membership and historical results remain preserved. [Machine-readable evidence](verification.json).

## Actual desktop verification and training

The original v19 archive is 469,492 bytes, SHA-256 `a2c7234a4b9846c845a405b9ed5ebeb3f75745c2b2015f0970ac71f953a4d2da`. Existing extraction verifies as exactly 40 matching files and three exact twelve-file packages; no re-extraction or overwrite. Every fresh actual launcher check reports `verified_read_only`, schema/GPU true and training started false before execution.

The existing Python 3.11.17, spaCy 3.7.5, Torch 2.11.0+cu128, CuPy 13.6.0 and RTX 3060 Ti were reused. All 23 pretrained files match revision `51a40433059d8a2c25b98a48eca854f8789a491a`; nothing was installed or replaced.

| Configuration | Seed | Precision | Recall | Validation F1 | Selected step | Stopping reason |
|---|---:|---:|---:|---:|---:|---|
| control | 0 | 75.3247% | 68.2353% | 71.6049% | 945 | configured maximum 1000 steps reached |
| higher_dropout | 0 | 56.4706% | 56.4706% | 56.4706% | 420 | early stopping after 175 optimizer steps without development improvement |
| lower_learning_rate | 0 | 65.0602% | 63.5294% | 64.2857% | 875 | configured maximum 1000 steps reached |
| control | 1 | 73.7500% | 69.4118% | 71.5152% | 595 | early stopping after 175 optimizer steps without development improvement |
| control | 2 | 66.6667% | 65.8824% | 66.2722% | 665 | early stopping after 175 optimizer steps without development improvement |

All run directories are under `backend/training/flood_ner/artifacts/corrected-v19-experiment-20261018-v1/runs/<configuration>-seed-<seed>/`. Selected checkpoints are `selected-checkpoint/model`, with `selection.json` alongside. Every run exited zero, its selected six-label checkpoint loaded on CPU and independently reproduced its development F1. Individual predictions/logs stay ignored.

Control wins screening; higher-dropout/lower-rate seeds 1/2 were correctly not run. The full-precision pure scheduler retains control. Seed 0 stays primary; no best-seed selection or ensemble. Control mean F1 **69.7974%**, sample standard deviation **3.0533 percentage points**. Historical v16 mean **66.5104%**, sample standard deviation **1.0323 points**. These are validation comparisons, not holdout improvement claims.

## Class differences and limits

Primary seed-0 development comparison on the same frozen 85 reference spans:

| Label | Support | v16 F1 | v19 F1 | Difference (percentage points) |
|---|---:|---:|---:|---:|
| BARANGAY | 19 | 62.86% | 74.29% | +11.43 |
| CITY | 23 | 73.08% | 85.11% | +12.03 |
| LANDMARK | 7 | 30.77% | 58.82% | +28.05 |
| LOCAL_AREA | 12 | 80.00% | 58.82% | -21.18 |
| PROVINCE | 10 | 90.00% | 85.71% | -4.29 |
| ROAD | 14 | 50.00% | 48.00% | -2.00 |

Overall primary development F1 increases by 4.94 percentage points; LOCAL_AREA, PROVINCE and ROAD regress. These mixed class results do not override the frozen selection rule. Trainer DocBins have IDs only, so per-language metrics require the authenticated laptop development metadata; they were not guessed from text or IDs.

References are limited-provenance AI-assisted silver, with incomplete history/accounting and no certified freshness or human gold. Validation Taglish ROAD support is zero, Taglish LANDMARK support one. Holdout LOCAL_AREA support is zero, so that holdout class remains unmeasured. No 80% guarantee or deployment decision follows.

## Evidence, defect correction and preservation

The final focused suite passes **201 tests** (195 combined checks plus six development-language companion checks), with no failures/errors/skips, using the existing isolated interpreter, `--noconftest` and a new private temporary directory. Constructed tests cover schedule/ties/retention, invalid checkpoints, failure stops, occupied destinations and concurrency, casing/schema/import-order regressions, binding/roster/membership tampering, Unicode/raw-text inference, repeat attempts, bootstrap pairing, unsupported support and CPU DLL behavior. All three historical v16 selected checkpoints also load portably and reproduce their recorded development scores.

The initial new controller compared full-precision selection metadata to spaCy's ten-decimal serialized meta.json using exact equality and stopped after control seed 0, although training itself exited successfully. Its error record remains preserved. A bounded rounding regression and independent checkpoint load/scoring established the bookkeeping defect. A hash-bound validated prefix carried forward that same completed first run; no training retry, alternate recipe or destination reuse occurred. selection.json remains authoritative for full-precision ranking and earliest-step ties.

All **242 protected historical/package/model/backup files**, including `.env`, verify unchanged after training. The training lock is absent following normal launcher cleanup. Existing source-byte backups remain private. Public API, dependency and database state are unchanged.

## Frozen laptop handoff

[Owner-only selected-model transfer folder](https://drive.google.com/drive/folders/1XYPTFZ9Ooi2D6_e1jtZT-jdzl06ZEYs4). All 22 uploaded transport/instruction/development-companion files pass complete SHA-256 byte readback and owner-only permission checks; the folder is owner-only too. Laptop receipt/execution is not yet established.

The archive contains 132 files and six selected checkpoints: corrected control seeds 0/1/2 and historical v16 seeds 0/1/2, plus exact package/tokenizer, frozen selection, evaluator, source comparison files, rules bindings and instructions. It includes no research-holdout data. The large direct upload timed out before a Drive file was created; split transport preserves the identical archive. Local reconstruction verifies.

- Complete ZIP: `LANES-NER-corrected-v19-laptop-evaluation-20261018-v1.zip`, **418,467,210 bytes**.
- ZIP SHA-256: `a6675c403216146bbf42da8790df66112a2926ebd63dedbf641c7c1cf6649345`.
- Inner manifest SHA-256: `b3dd00e73d59aa11fdcdbf4a1c97c7e58abd7b30540521f2215e9c7435887367`.
- Thirteen numbered binary parts; transport manifest SHA-256: `959a2404fb22fa2ea3bd86b82da59be1e9dc25a4f28a30f508b922d0b3a14879`.

[Separate laptop operator guide](../../guides/ner-corrected-holdout-laptop.md). Review the source, verify/reassemble all parts and exclusively extract into a new directory. Add only the five new helper/test files to absent checkout paths; verify existing implementation bytes without overwriting them. Do not reinstall resources.

The locked evaluation roster is these six models plus unchanged rules. On laptop, validate the original qualified 60-passage holdout and corrected development lineage, seal all identities and create one durable exclusive inference attempt. Report strict precision/recall/F1 overall and by label/language, support, negatives, three-seed variability and paired connected-group intervals (10,000 draws, seed 0). Keep predictions/references private; return an authenticated aggregate receipt. Holdout scores cannot change the model selection or trigger tuning.

**Remaining blocker:** actual holdout and development-language evaluation require the laptop and its existing backend dependencies. The desktop research interpreter has no SQLAlchemy/backend environment; the evaluator's constructed rules preflight rejects missing dependencies before any holdout prediction or attempt claim. No rules/holdout end-to-end desktop pass is claimed. Until the laptop returns a verified receipt, holdout metrics remain pending.

Delivery includes the reviewed extractor and an updated laptop guide as separate companions. The standard-library extractor was exercised against the actual ZIP into an absent artifact destination: all 132 members verify, with no inference or holdout included.

Reassembly helper SHA-256: `6802f5627d529baa79844c2c7f0a158df63d0aed5aa2c70833a87e679cb8698e`. [Verified updated laptop guide](https://drive.google.com/file/d/1ROwpwtAgcnqig6vBuxZvxfyn69zKXdOw/view?usp=drivesdk). Companion hashes and all provider file IDs are recorded in verification.json.

The separate development-only companion delivers saved predictions from all five desktop runs and a tested scorer. Join these to the authenticated corrected development records on laptop to obtain every screening/confirmation language breakdown without additional inference or transferring rejected-model weights. Follow DEVELOPMENT-LANGUAGE-INSTRUCTIONS.md in the same private folder and return its aggregate result with the holdout receipt. This companion does not change the frozen holdout roster or selection.
