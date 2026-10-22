# Regularization v21 desktop receipt and GPU verification

> **Last Updated:** October 19, 2026, 12:06 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Completed: authenticated extraction and actual GPU/schema verification. STOP before training.** The launcher reports `verified_read_only`, `configuration_schema_verified: true`, `gpu_verified: true` and `training_started: false`. No inference or research-holdout access occurred. [Machine-readable receipt](verification.json).

## Received package

The four owner-only [Drive handoff files](https://drive.google.com/drive/folders/1vKssoZurLa6WjuJPftXRbJ7GcoefimKq) were downloaded and checked privately. The ZIP is **216,866 bytes**, SHA-256 `2336dbafdb93832323c702c61d142ad68b9bfce2371c84fbb27c50117183884f`; transfer manifest SHA-256 `5f9c5c58b34356826ba6427ee0c60820f8cb92e59e0eb7ee9452e0ac10f7784e`. The published standard-library extractor checked all member hashes, safe paths, exact membership, implementation/test bindings and the trainer manifest before exclusive extraction.

Destination: `backend/training/flood_ner/artifacts/regularization-desktop-20261018-v21`. Actual extraction returned `extracted_verified`, **20 files / 12 trainer files**, training false. The experiment manifest hash is `35050682217749d945a3c5fecbe5d3771212b1df1276f9f5f95bad4c7d6a0e78`. All fourteen source/test bindings and the delivery helper match. The original archive and companions remain preserved.

## Actual desktop verification

The published `regularization_experiment.py verify --verify-gpu` command exited **0** with empty stderr. It verified the sole stronger-weight-decay package and all three seed configurations. This is one candidate with three configs, rather than the earlier v19 three-family handoff. The recipe remains 345 training / 60 validation, batch 8, dropout 0.1, learning rate 0.001, maximum 30 epochs/1,000 steps, evaluation every 35 steps, patience 175; its predefined change is L2 0.01 to 0.05 with weight decay true.

| Required result | Actual |
|---|---|
| state | verified_read_only |
| configuration_schema_verified | true |
| gpu_verified | true |
| training_started | false |

Existing qualified interpreter: `backend/training/flood_ner/artifacts/gpu-qualification-20261015/research-env/Scripts/python.exe`. Existing pinned model: `backend/training/flood_ner/artifacts/gpu-qualification-20261015/model`. All **23 files** match revision `51a40433059d8a2c25b98a48eca854f8789a491a` and remain unchanged.

Runtime: Python **3.11.17**, spaCy **3.7.5**, Torch **2.11.0+cu128**, CuPy **13.6.0**, NVIDIA GeForce **RTX 3060 Ti**, compute capability **8.6**. These match the package's recorded GPU/runtime qualification. No installation or replacement occurred. Ordinary registry resolution qualified seeds 0/1/2 with zero optimizer updates, no pipeline creation or pretrained neural-weight loading, and no corpus reads during schema qualification. File hashing is separate from schema resolution.

## Integration and preservation

`roi-branch` fast-forwarded from `882049cb3a709099ef3547a98dad57905f90f84a` to `4875cef4f03ecc4fdc2b3b0ff9d7e7bc43f36bad`. Nineteen local files were copied byte-for-byte into a new owner-only private backup; local doc patches, initial status and relevant hashes are retained there. Five overlapping docs were reconciled, preserving desktop execution history beneath the newer laptop records. Three untracked collisions were byte-identical to incoming files; the qualified incoming laptop evaluator and guide replace their older desktop versions, which remain backed up.

The first fast-forward refused stat-dirty documentation. Rewriting only the backed-up overlapping docs in this checkout's existing CRLF style and refreshing index stat data allowed the fast-forward. No stash, reset, commit or push occurred, and no Git setting changed.

`collection.py` had only CRLF/LF differences. Its HEAD blob matched the authenticated transfer binding; original bytes were preserved, normalized comparison confirmed no substantive change, and Python `subprocess.check_output` plus `Path.write_bytes` restored the exact Git blob. Frozen logic, manifests, expected hashes and recipes were not changed.

Final preservation checks covered **6,304 entries**: **6,303 unchanged**; the remaining `.gitattributes` update is the expected incoming commit and matches it. Its original bytes are preserved separately. Historical packages, runs, model files, source backups and `.env` are unchanged. All new package files remain unchanged after verification. No training destination, checkpoint or training lock was created.

## Regression evidence and boundary

**248 passed, 0 failed, 3 warnings in 57.87 seconds** across the regularization transfer/experiment, successor preparation, Windows runtime and successor experiment suites. The existing isolated interpreter used `--noconftest`, a new private pytest directory, no bytecode and no shared pytest cache. Constructed tests cover tampering, unsafe paths, existing destinations, scheduler/tie/retention guards, failed-run stopping, casing/schema controls, heldout-file rejection, concurrent locks and all three Windows initialization paths. Warnings concern constructed duplicate ZIP membership, test-process CUDA-path discovery and a Click deprecation; actual launcher stderr is empty.

Raw logs, original local files, Git receipts and preservation hashes remain outside the frozen package in `backend/training/flood_ner/artifacts/regularization-desktop-verification-20261018-v1`. Public evidence contains metadata only. [Operator guide](../../guides/ner-regularization-experiment.md).

Training remains a separate explicit task: seed 0 screening, then conditional seeds 1/2, at most three new runs, validation-only improvement with ROAD/LOCAL_AREA protection. The completed research holdout stays excluded from further tuning/comparison. This receipt adds no accuracy measurement. References remain limited-provenance AI-assisted silver research with incomplete history/accounting; no guaranteed score, human-gold or certified-fresh claim follows.
