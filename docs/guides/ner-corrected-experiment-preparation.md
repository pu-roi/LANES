# Corrected-data experiment preparation and future handoff

> **Last Updated:** October 18, 2026, 11:41 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current NER handoff: the regularization experiment is verified on private Drive; matching code and instructions accompany this roi-branch publication.** The 345 training / 60 validation exports are unchanged. One L2 = 0.05 candidate has seed 0/1/2 configs and a fixed maximum-three-run protocol. All four uploaded files match authenticated readback; parent, destination and files are owner-only. Desktop receipt and GPU verification remain pending. No training, inference or holdout access occurred during delivery. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next on the desktop:** preserve local changes, pull roi-branch with --ff-only, authenticate and extract the delivered archive into an absent destination, then run read-only GPU/schema verification and STOP. Actual training is a separate explicit task after verification; the completed research holdout stays outside tuning.

[Delivery report](../evaluations/flood-ner-regularization-delivery-20261018/README.md) · [Desktop instructions](ner-regularization-experiment.md) · [Private Drive handoff](https://drive.google.com/drive/folders/1vKssoZurLa6WjuJPftXRbJ7GcoefimKq)

**Earlier dated checkpoints below are historical.**

**Current NER status: v19 diagnosis and the one-time frozen research evaluation are complete on the laptop.** Dataset 345/60/60 and validation-selected control/seed 0 stay unchanged. V19 seed 0 training/validation/holdout F1: **98.09% / 71.60% / 73.63%**. Historical v16 seed 0 holdout 74.74%; rules 53.49%. Holdout three-seed means: control 70.34%, v16 75.13%. These results do not establish an overall v19 improvement or authorize choosing a model using the holdout.

**Next:** a separate development plan from the existing training/validation error review; no new articles or automatic retraining. Gate 3 research measurement is complete, while operational qualification, integration and release remain open. The holdout has now been evaluated and must not be tuned against or evaluated again under this protocol. AI-assisted silver, incomplete history/accounting and no certified-fresh claim remain. No collection, new training, reference/partition change, integration, upload, commit or push occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

[Diagnosis/evaluation report](../evaluations/flood-ner-v19-diagnosis-evaluation-20261018/README.md) · [Laptop evaluation guide](ner-corrected-holdout-laptop.md)

**Historical checkpoints follow.** Their “current/next” wording describes earlier dated tasks and is superseded by the status above.

**Current handoff: corrected v19 packages are verified on Drive; matching public code and instructions accompany this roi-branch publication.** Dataset remains 345 training / 60 validation / 60 separate research holdout. Three twelve-file packages and the fixed future protocol are delivered; all uploaded bytes match authenticated readback and five owner-only permission checks pass. No training, inference or holdout access occurred. [Delivery report](../evaluations/flood-ner-corrected-experiment-delivery-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next: desktop receipt and read-only GPU verification for all three packages, then STOP.** Preserve local work, pull roi-branch with --ff-only and receive the new private ZIP from [Drive](https://drive.google.com/drive/folders/1LDO770D82NXHZRiYNZrHe5oyLo7-vJU7). Actual desktop receipt/GPU checks remain pending. A Git pull does not deliver ignored data; do not rerun preparation or historical v16 training commands. Actual training is a separate explicit task. [Exact commands and copyable desktop prompt](../guides/ner-corrected-experiment-desktop.md).

The existing dataset remains **345 training / 60 validation / 60 separate research holdout**. A new private development revision applies only the 12 reviewed training boundaries across nine records. Validation text/annotations, tokenizer and membership/group metadata are unchanged. The unresolved validation landmark boundary keeps its original scored reference. See the [qualification report](../evaluations/flood-ner-corrected-experiment-preparation-20261018/README.md).

## Local files and read-only verification

Completed private output:
`backend/training/flood_ner/artifacts/corrected-experiment-prepared-20261018-v19-run02/`

Its `development/` directory contains the corrected export, complete development records and original partition metadata. `correction-adoption-ledger.json` records original/revised annotation hashes, exact source evidence and review history. `development-revision-manifest.json` links the unchanged original admission/partition lineage to this development-only annotation derivative. `cpu-qualification.json` records actual serialization/schema checks. `experiment-protocol.json` freezes the later study without authorizing training.

Each `packages/control/`, `packages/higher_dropout/` and `packages/lower_learning_rate/` directory contains exactly twelve trainer files. Keep instructions, protocol and transfer receipts outside these directories. Source captures, complete annotation packages, holdout records, environments and model weights do not belong in trainer delivery.

On this laptop, this verifies the completed package without writing or running a worker:

```powershell
Set-Location "D:\Documents\Github\LANES\backend"
& .\.venv\Scripts\python.exe -B -m training.flood_ner.successor_experiment_preparation --checkout .. --grant .\training\flood_ner\artifacts\corrected-experiment-coordination-20261018-v19\preparation-grant-v2.json --output .\training\flood_ner\artifacts\corrected-experiment-prepared-20261018-v19-run02
```

Require `state: verified_read_only`, three packages, `training_authorized: false`, `training_started: false` and `gpu_verified: false`. The pinned CPU worker used the existing research Python 3.11.17/spaCy 3.7.5 environment to serialize/tokenize and resolve schemas; it did not initialize a pipeline, load prediction weights or train.

The explicit `--prepare` entry point is for a **new** hash-bound grant and absent destination only. Existing grants/claims/outputs are evidence, not reusable destinations. The first attempt failed a zero-update representation check and is preserved; use the completed `run02` result. No archived or private helper code is imported.

## Fixed later desktop study

| Run stage | Required sequence |
|---|---|
| Screening | Control seed 0; higher dropout seed 0; lower learning rate seed 0 |
| Confirmation | Control seeds 1 and 2; then the screening winner seeds 1 and 2 if it differs from control |

The configuration values are control 0.1/0.001, higher dropout 0.2/0.001, lower learning rate 0.1/0.0005 (dropout/learning rate). No other recipe settings change. Screening compares full-precision strict validation micro F1; within 1e-12 of the global maximum, prefer control, then higher dropout, then lower learning rate. The pure `schedule` function validates outcome prefixes and proposes the next run but never dispatches one.

Five runs suffice when control wins; seven is the maximum otherwise. Retain a variant only when its seed-0 F1 and three-seed mean both strictly exceed the new corrected-data control. Otherwise retain control. Historical v16 runs are contextual comparisons, not substitutes. Report all screened outcomes and supported class/language regressions; do not run a runner-up automatically. Stop on any failure and preserve logs; no retry, concurrent runs, output reuse or automatic budget expansion.

## Next task and limitations

Private delivery is verified; desktop receipt and GPU verification remain pending. The laptop-only verification command above is not a desktop prerequisite. Follow the [desktop receipt guide](ner-corrected-experiment-desktop.md). Earlier preparation-only status below is historical. A separately authorized task must publish matching public code, transfer private trainer/protocol materials, verify archive checksums and exact twelve-file package membership, and recheck the actual qualified desktop runtime/model/GPU. Pulling Git does not deliver ignored datasets. No automatic installation or CPU training fallback is authorized.

Training requires a later explicit action after delivery and GPU verification. These local packages and the pure schedule do not authorize any training. The old v16 run destinations are occupied and must never be reused. Do not evaluate the research holdout for configuration selection.

References remain AI-assisted silver. Incomplete source history/accounting, zero Taglish ROAD validation support and scarce Taglish LANDMARK coverage remain limitations. No new score or 80% performance claim follows from preparation.
