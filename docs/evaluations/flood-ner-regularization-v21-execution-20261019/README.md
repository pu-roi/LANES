# Regularization v21 desktop execution

> **Last Updated:** October 19, 2026, 01:39 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Private archival backup:** [Nine owner-only, fully byte-verified files](https://drive.google.com/drive/folders/14A4kgWRH0LNay8My9vCutIQp_ro-ezTl) preserve the completed run and frozen decision. Original packages and retained control are unchanged. [Publication checks](../flood-ner-regularization-publication-20261019/README.md). No retraining or additional holdout evaluation is authorized by this backup.

**Completed: one successful seed-0 run; screening failed and corrected v19 control remains retained, seed 0 primary.** Candidate overall validation F1 is **69.7143%**, versus control **71.6049%**. ROAD and LOCAL_AREA improve, but the required overall improvement fails. Seeds 1/2 were not dispatched. [Machine-readable results](verification.json) · [Execution plan](../../plans/ner-regularization-v21-execution-20261019.md). No holdout evaluation, data/annotation change, deployment, commit or push occurred.

## Readiness and implementation

The original 20-file v21 experiment and twelve-file trainer package remain unchanged. Fresh actual verification returned `verified_read_only`, `configuration_schema_verified: true`, `gpu_verified: true`, `training_started: false`. Existing Python 3.11.17, spaCy 3.7.5, Torch 2.11.0+cu128, CuPy 13.6.0 and RTX 3060 Ti compute capability 8.6 are reused; all 23 pinned model files match. Nothing was installed.

New internal controller and CPU development worker reuse the frozen scheduler, launcher, raw-text inference and exact-span scorer. The controller records an exclusive permanent experiment claim, dispatches each seed at most once, rejects occupied/concurrent destinations, and stops on failure. The worker joins exact record/text identities to authenticated development language metadata and scores training/validation separately. References never enter inference. Package-bound implementations, manifests, expected hashes, configs and tokenizer are unchanged.

**291 tests passed, 0 failed, 3 warnings in 47.14 seconds**, using the existing isolated interpreter, `--noconftest`, no shared pytest cache and a new private pytest directory. This includes new bounded execution/scoring regressions, constructed CPU checkpoint loading, existing regularization transfer/protocol tests, successor preparation, Windows runtime, successor experiment and corrected checkpoint bookkeeping checks. Warnings concern test-process CUDA-path discovery, Click deprecation and constructed duplicate ZIP membership; actual fresh GPU preflight stderr is empty.

The checkout is `roi-branch` at `4875cef4f03ecc4fdc2b3b0ff9d7e7bc43f36bad`. A new owner-only preflight directory preserves local work, implementation copies/patches, private hashes, exact test/runtime commands and logs. **8,047 protected files** verified before dispatch. Execution authorization is recorded separately and binds 81 source/runtime files plus preservation and actual preflight receipts; frozen preparation manifests remain unchanged.

## Frozen comparison

| Corrected v19 comparator | Overall F1 | ROAD F1 | LOCAL_AREA F1 |
|---|---:|---:|---:|
| Seed 0 | 71.60493827% | 48.00000000% | 58.82352941% |
| Three-seed mean | 69.79742638% | 50.29951691% | 63.99380805% |

Seed 0 must strictly improve overall validation F1 and not reduce either protected-label F1, using full precision and epsilon 1e-12. Only a passing screen permits seeds 1 then 2. Retention requires three-seed mean overall improvement and no regression in either protected-label mean. Overall ties retain control; protected-label ties pass. Seed 0 remains primary; no best-seed selection or ensemble.

Keep batch size 8, dropout 0.1, learning rate 0.001, maximum 30 epochs/1,000 steps, evaluation every 35 steps and patience 175. Only the predefined L2 0.01 to 0.05 change applies. The six-class head is fresh with the pinned pretrained encoder; models do not resume from v19. Fixed membership remains 345 training / 60 validation, with the separate research holdout excluded.

## Actual seed-0 outcome and retention

The launcher, training subprocess and execution controller each exited successfully. The selected checkpoint loads on CPU with exactly six labels and the unchanged tokenizer; independent strict development scoring reproduces selected F1. **Selected step: 945. Last recorded optimizer step: 1000. Stopping reason: configured maximum 1,000 steps reached.** Raw logs and resolved config remain private; development F1 and earliest-step tie selection are unchanged.

| Seed-0 development metric | Corrected v19 control | L2 = 0.05 candidate | Difference (percentage points) |
|---|---:|---:|---:|
| Precision | 75.3247% | 67.7778% | -7.5479 |
| Recall | 68.2353% | 71.7647% | +3.5294 |
| Overall F1 | 71.6049% | 69.7143% | -1.8907 |
| ROAD F1 | 48.0000% | 53.3333% | +5.3333 |
| LOCAL_AREA F1 | 58.8235% | 73.6842% | +14.8607 |

Candidate counts are 61 TP / 29 FP / 24 FN, against control's 58 TP / 19 FP / 27 FN, over the same 85 reference entities in 60 passages. Recall rises, but the extra false positives reduce precision and overall F1. The frozen screen fails its overall criterion; both protected-label criteria pass. The controller stopped normally after this decision, leaving seeds 1/2 absent. This is a failed performance screen, not a training/runtime failure.

Corrected control's three-seed overall mean remains **69.7974%**, sample SD **3.0533 percentage points**. Candidate three-seed means and sample deviations are **unmeasured**, because confirmation runs were not authorized by screening. Do not compare the single candidate score to the control mean as a replacement gate. The retained checkpoint is the original corrected control seed-0 checkpoint; its exact files/tokenizer/configuration identities are frozen in the private `frozen-primary.json` and public metadata receipt.

## Development support and regressions

| Label | Reference support | Candidate precision | Candidate recall | Candidate F1 | Control F1 | F1 difference (points) |
|---|---:|---:|---:|---:|---:|---:|
| BARANGAY | 19 | 68.7500% | 57.8947% | 62.8571% | 74.2857% | -11.4286 |
| CITY | 23 | 74.1935% | 100.0000% | 85.1852% | 85.1064% | +0.0788 |
| LANDMARK | 7 | 40.0000% | 57.1429% | 47.0588% | 58.8235% | -11.7647 |
| LOCAL_AREA | 12 | 100.0000% | 58.3333% | 73.6842% | 58.8235% | +14.8607 |
| PROVINCE | 10 | 80.0000% | 80.0000% | 80.0000% | 85.7143% | -5.7143 |
| ROAD | 14 | 50.0000% | 57.1429% | 53.3333% | 48.0000% | +5.3333 |

| Language | Passages | Reference entities | Candidate precision | Candidate recall | Candidate F1 | Control F1 |
|---|---:|---:|---:|---:|---:|---:|
| English | 38 | 50 | 66.6667% | 68.0000% | 67.3267% | 69.4737% |
| Taglish | 22 | 35 | 69.2308% | 77.1429% | 72.9730% | 74.6269% |

Negative-passage false positives: **2/27 candidate versus 0/27 control**, with candidate English 1/17 and Taglish 1/10. Full label/language cross-tables, counts and supported-label summaries are in the metadata receipt. Taglish ROAD has zero reference support and remains unmeasured. No inference-driven label changes or annotation corrections occurred.

Candidate fitted-training F1 is **98.8124%**, versus validation **69.7143%**, a **29.0981-point** gap. Training scores are diagnostic and do not select the model. These measurements do not establish better generalization.

## Execution locations and final preservation

New private experiment: `backend/training/flood_ner/artifacts/regularization-v21-experiment-20261019-v1`.

Actual run: `runs/stronger-weight-decay-seed-0`. Seeds 1/2 were not created. Logs, predictions, weights and resolved configs stay private. The successful CPU loading/scoring receipt and checkpoint hashes are preserved. Checkpoints use development F1 and earliest-step ties.

Preflight and process evidence: `backend/training/flood_ner/artifacts/regularization-v21-execution-preflight-20261019-v1`. All **8,047 protected files** pass the final preservation check, including `.env`, original packages, all 23 pinned model files, historical runs and source backups. The permanent experiment claim remains; both active locks were released through normal cleanup. No retry or manual active-lock removal occurred. The original archive, frozen v21 manifest/config/data/tokenizer files and existing local work remain preserved. Only new execution helpers/tests and synchronized documentation were added or changed.

These are reused-validation, limited-provenance AI-assisted silver research results with history/support limitations. Better performance is possible, not guaranteed. No new holdout comparison or 80% acceptance threshold is introduced.
