# Successor v16 desktop integration and training retry

> **Last Updated:** October 18, 2026, 4:39 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Integration, 75 focused tests and combined desktop verification pass. All three successor seeds complete and their selected checkpoints verify; seed 0 remains primary.** The user authorized a new seed-0 attempt followed by seeds 1/2 only after each preceding run succeeds; no automatic retries after failure. Seed 0 remains primary. The fixed data remains 345 training / 60 validation / 60 separate research-holdout passages; holdout contents are outside this task.

## Integration and private package

Preserved the dirty checkout as private exact-file backups, base bytes and an overlapping-change patch. Temporarily reversed only backed-up overlapping changes, fast-forwarded `roi-branch` from `adffbb8` to `da71912`, merged the launcher and reconciled documentation. No stash, reset, commit or push. The existing `.env` and untracked work are preserved. The [first failed v15 run](../flood-ner-successor-desktop-training-20261018/README.md) and [v16 config-casing correction](../flood-ner-successor-config-correction-20261018/README.md) remain separate historical records.

The v16 ZIP verifies at 153,999 bytes / SHA-256 `b581ed97a7e54e3d6db7f9b3504ff94d8a48bb341437f7e84ed31bf39b2b41c7`. The original twelve-file package manifest is `40fda6b9df92ea1d51d99d167b1830fa38da64308203168d5ca5457a05a2738f`. It is preserved unchanged. The separately versioned `successor-desktop-handoff-20261018-v16-configfix-windows-runtime-v1` derivative changes only the launcher implementation binding; all eleven payload files are byte-identical to v16. Its manifest is `18aacb9ad1c285392adfaa4b995edca4d05baec81fdb3ae9ba1bbbf0d753b986`. Private receipts bind the exact patch, test sources/results, original and derived manifests.

## Runtime and verification

Retain v16's case-preserving `L2`, `L2_is_weight_decay` and `nO` handling and actual spaCy registry-schema validation. Shared interpreter-local Windows DLL setup now precedes Torch/spaCy imports in the GPU probe, new schema-validation subprocess and actual training process. DLL handles remain alive throughout each operation. Bounded failure/timeout diagnostics preserve the no-CPU-fallback behavior. No dependencies, public APIs, CLI, schema or hyperparameters changed.

**75 focused tests pass**, including argument casing and generated seeds, runtime setup/import ordering and handle lifetime in all three paths, non-Windows behavior, missing libraries, partial setup cleanup, bounded timeout/error diagnostics, schema failure before output creation, hash-bound package rejection, holdout exclusion and concurrent destination controls. Tests use the existing isolated interpreter, `--noconftest` and a new private `--basetemp`. The existing CuPy environment warning during test imports and Click deprecation warning are separate from actual desktop runtime qualification.

Actual combined launcher qualification passes: `verified_read_only`, `gpu_verified=true`, `configuration_schema_verified=true`, `training_started=false`. All 23 model hashes, eleven payload hashes and recorded runtime/device versions match: Python 3.11.17, spaCy 3.7.5, Torch 2.11.0+cu128, CuPy 13.6.0 and RTX 3060 Ti compute capability 8.6. Verification creates no training destination. The complete pinned model is under `gpu-qualification-20261015/model`, rather than the absent preflight example. Before dispatch, all 12,387 protected historical artifact files (4,870,838,279 bytes) and `.env` verify unchanged, including the failed v15 run and original packages.

## Training outcome and limits

All three successor seeds complete and their selected checkpoints verify; seed 0 remains primary.

| Seed | Development F1 | Precision | Recall | Selected step | Final step | Stopping reason |
|---|---:|---:|---:|---:|---:|---|
| 0 (primary) | 66.67% | 67.47% | 65.88% | 910 | 1000 | configured maximum 1000 steps reached |
| 1 | 65.41% | 70.27% | 61.18% | 560 | 735 | early stopping after 175 optimizer steps without development improvement |
| 2 | 67.46% | 67.86% | 67.06% | 980 | 1000 | configured maximum 1000 steps reached |

Three-seed mean development F1: **66.51%**; sample standard deviation: **1.03 percentage points**. These development figures do not establish held-out improvement.

Every completed run exits 0 and its selected model reloads with exactly the six location labels and matching finite development F1/precision/recall, selection step and earliest-step tie-break metadata. Reload verification reads no documents and makes no predictions. Stopping reasons derive from recorded final/selected steps and the unchanged 175-step patience/1000-step limit. Selected checkpoint files are hashed privately. New output directories and per-seed launch logs remain under ignored artifacts.

All 12,387 protected predecessor files, including the failed v15 run, original packages and `.env`, verify unchanged after execution. All eleven derivative payload files and 23 model files also verify unchanged. [Machine-readable verification](verification.json).

The limited-provenance AI-assisted silver scope remains unchanged. Holdout contents/evaluation, deployment, commits and pushes remain outside this task. Validation lacks Taglish ROAD support; the separate holdout lacks LOCAL_AREA support. No broader accuracy or production-readiness claim follows from development results.
