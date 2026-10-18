# Existing-data NER error audit

> **Last Updated:** October 18, 2026, 5:27 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The completed v18 audit uses the existing 345 training / 60 validation records and all three selected checkpoints. It performs CPU inference only. The research holdout stays unopened, and the desktop can remain off. [Results](../evaluations/flood-ner-development-error-audit-20261018/README.md).

## Inputs and entry points

Use `development_error_audit.py` as coordinator and `development_error_worker.py` as the pinned-interpreter worker. The request schema is `lanes-development-error-audit-v1`, scope `existing_development_error_audit_only`, capability `development`. Requests bind the checkpoint archive/embedded-member manifest, qualified development status, base-model contract, desktop comparison results and exact audit/registry/schema/scorer implementation bytes.

The development status must bind exactly the existing eight development-export files and 345/60 membership with 170/175 training and 38/22 validation English/Taglish counts. The worker rejects duplicate IDs, incomplete or null references, source/token mismatches, unsupported partitions and split groups. It imports the existing public registry; no archived helper is executed. It loads selected saved weights and the exact frozen tokenizer using private resource relocation, with no initialization, optimizer or GPU trainer. An absent/unsupported runtime or input is a blocker, not an automatic installation/fallback.

Qualified CPU runtime: existing Python 3.11/spaCy 3.7.5 research environment, including existing Torch. The general backend environment lacks Torch and is not the inference interpreter. No dependencies are installed by this task.

For an explicitly needed later replay, use a new output path; the completed run02 destination must remain unchanged. From the actual checkout:

```powershell
$NerAuditCheckout = (Get-Location).Path
$NerAuditPython = (Resolve-Path .\backend\training\flood_ner\artifacts\preflight-use-20261015\research-env\Scripts\python.exe).Path
& .\backend\.venv\Scripts\python.exe -B .\backend\training\flood_ner\development_error_audit.py --checkout $NerAuditCheckout --request .\backend\training\flood_ner\artifacts\development-error-audit-coordination-20261018-v18\request-v2.json --python $NerAuditPython --output .\backend\training\flood_ner\artifacts\development-error-audit-20261018-v18-run03
if ($LASTEXITCODE -ne 0) { throw "Audit failed; preserve output/logs and inspect the reported blocker." }
```

These private inputs are ignored by Git. An unchanged hash-bound request is required; a Git pull alone is insufficient. Runtime, scoring, model and corpus files are checked before/after execution. Outputs use exclusive creation and an active audit lock; do not delete an interrupted lock without inspecting the process and preserving evidence.

## Outputs and interpretation

Private output contains one prediction/error entry per record per seed, actual metrics, desktop comparisons, checkpoint hashes, request and worker outcome/logs. The separate review package contains 60 validation dispositions, 54 focused training reviews, 27 source-context bindings and nine draft correction records containing 12 proposed boundary changes. Proposed references pass mechanical checks but remain AI-assisted silver and are not admitted or rescored.

Metrics use exact record/start/end/type agreement. Diagnostics link overlapping mismatches without counting them as correct. Report supported-label macro F1 and all per-label/language support counts; unsupported-label F1 is null. Train-set fit is separate from unseen-text performance. An allowlisted aggregate schema excludes individual texts, URLs and record IDs from coordinator status.

This task ends with proposals. No collection, added passages, corpus changes, new exports, holdout access, training, upload or publication is authorized by replaying an audit. The next task chooses a correction revision and a bounded experiment using the same data. Current dataset/model/export manifests must not be patched in place.
