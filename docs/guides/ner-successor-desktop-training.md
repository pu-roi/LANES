# Successor NER desktop handoff

> **Last Updated:** October 18, 2026 by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The laptop prepared **345 training / 60 validation / 60 research-holdout passages** under the approved documented-limitations standard. Membership is locked and the separate exports are qualified. No training has run. [Preparation evidence](../evaluations/flood-ner-successor-preparation-20261018/README.md).

The private trainer ZIP is delivered to the owner-only [successor Drive folder](https://drive.google.com/drive/folders/1WuhvnWfKybY8lbKKO55aToTUQ_PY6RqJ). Its complete downloaded bytes match the laptop archive. The current code and public reports accompany this handoff on `roi-branch`. **Desktop receipt and GPU verification remain pending; no training has run.** A Git pull alone does not transfer ignored datasets, environments, models or training results.

## Pull the code and receive the private package

Open PowerShell in the actual desktop LANES checkout. Preserve local changes: if the first check reports any, stop and review them before continuing. Do not reset, stash, overwrite or restore archives automatically.

```powershell
$NerChanges = @(git status --porcelain)
if ($LASTEXITCODE -ne 0) { throw "Not a usable Git checkout." }
if ($NerChanges.Count -gt 0) { throw "Local changes exist. Preserve and review them before pulling." }
git switch roi-branch
if ($LASTEXITCODE -ne 0) { throw "Branch switch failed; stop." }
git pull --ff-only origin roi-branch
if ($LASTEXITCODE -ne 0) { throw "Fast-forward pull failed; stop without resetting." }
```

Using `roicambe02@gmail.com`, download [the private ZIP](https://drive.google.com/file/d/1xaa9a6WV2L8t78O9XoR0NRmZqDJemYYm/view?usp=drivesdk), `SHA256SUMS.txt` and `START-HERE.md` from the new Drive folder. The ZIP is **153,734 bytes**, containing exactly the twelve trainer files beneath one package directory. Its SHA-256 is:

```text
7fb4f16f4726f9dc104c5236a5151543a7831cf64987e356dfe165b060ce334a
```

Extract through a new staging directory, verify the manifest and every payload file, then move the package to its absent destination. The atomic directory move refuses an existing destination; no `-Force` is used. Keep the small empty staging directory as transfer evidence.

```powershell
$NerZip = (Resolve-Path -LiteralPath (Read-Host "Full path to the downloaded successor ZIP")).Path
if ((Get-Item -LiteralPath $NerZip).Length -ne 153734) { throw "ZIP size mismatch." }
if ((Get-FileHash -LiteralPath $NerZip -Algorithm SHA256).Hash.ToLowerInvariant() -ne "7fb4f16f4726f9dc104c5236a5151543a7831cf64987e356dfe165b060ce334a") { throw "ZIP checksum mismatch." }
$NerArtifacts = Join-Path (Get-Location).Path "backend\training\flood_ner\artifacts"
$NerPackageName = "successor-desktop-handoff-20261018-v15-run02"
$NerDestination = Join-Path $NerArtifacts $NerPackageName
if (Test-Path -LiteralPath $NerDestination) { throw "Destination already exists. Verify it separately; do not overwrite it." }
if (-not (Test-Path -LiteralPath $NerArtifacts)) { New-Item -ItemType Directory -Path $NerArtifacts -ErrorAction Stop | Out-Null }
$NerStaging = Join-Path $NerArtifacts ("successor-delivery-staging-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $NerStaging -ErrorAction Stop | Out-Null
Expand-Archive -LiteralPath $NerZip -DestinationPath $NerStaging -ErrorAction Stop
$NerStagedPackage = Join-Path $NerStaging $NerPackageName
$NerManifestPath = Join-Path $NerStagedPackage "handoff-manifest.json"
if ((Get-FileHash -LiteralPath $NerManifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne "ec3abd74e2201f116a90a90a3dc203877c3f511284b11374d7beb381c1faa11a") { throw "Package manifest mismatch." }
$NerManifest = Get-Content -LiteralPath $NerManifestPath -Raw | ConvertFrom-Json
if (@(Get-ChildItem -LiteralPath $NerStagedPackage -Force).Count -ne 12) { throw "Unexpected package contents." }
foreach ($NerEntry in $NerManifest.files.PSObject.Properties) {
    $NerFile = Join-Path $NerStagedPackage $NerEntry.Name
    if ((Get-FileHash -LiteralPath $NerFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $NerEntry.Value) { throw "Payload file checksum mismatch." }
}
[System.IO.Directory]::Move($NerStagedPackage, $NerDestination)
```

This is delivery of **345 training / 60 validation** records to the trainer. The separately prepared **60 research-holdout** records remain on the laptop. Once code and payload are present, continue with read-only GPU verification below. [Delivery verification](../evaluations/flood-ner-successor-delivery-20261018/README.md).

## What must reach the desktop

Use the current successor code and its unchanged registry from `roi-branch`. Preserve desktop local changes; never reset or overwrite a checkout. Do not run the older fixed-400 exporters or launchers for this successor.

Privately copy the **complete** `backend/training/flood_ner/artifacts/successor-desktop-handoff-20261018-v15-run02/` directory. It contains eleven files plus `handoff-manifest.json`: train/dev DocBins, tokenizer, three portable seed configs, qualification, model contract, evaluation contract and GPU qualification metadata. Its manifest SHA-256 is:

```text
ec3abd74e2201f116a90a90a3dc203877c3f511284b11374d7beb381c1faa11a
```

Keep that directory exact: no extra files, renamed configs or research-holdout data. The isolated holdout export remains separate on the laptop and is not an input to the trainer. The pinned model and qualified GPU environment are separate existing prerequisites; do not install or replace them automatically.

The [October 16 Drive folder](https://drive.google.com/drive/folders/1JrrMzZ3FyP0LGU00xWKF54enyyC87ffX) is a **historical handoff**, not delivery of this successor package. Its files must not be used as evidence that the new private payload exists on the desktop.

## Read-only verification

Open PowerShell in the actual desktop LANES checkout. Confirm its branch and inspect changes:

```powershell
git branch --show-current
git status --short
```

Set explicit paths. The examples below refer to the recorded desktop GPU environment and the complete saved model directory. Change them to the actual existing qualified paths if needed; a missing path means stop and report it.

```powershell
$NerCheckout = (Get-Location).Path
$NerPython = (Resolve-Path .\backend\training\flood_ner\artifacts\gpu-qualification-20261015\research-env\Scripts\python.exe).Path
$NerModel = (Resolve-Path .\backend\training\flood_ner\artifacts\preflight-use-20261015\model).Path
$NerPackage = (Resolve-Path .\backend\training\flood_ner\artifacts\successor-desktop-handoff-20261018-v15-run02).Path
Get-FileHash (Join-Path $NerPackage handoff-manifest.json) -Algorithm SHA256

& $NerPython -I -B .\backend\training\flood_ner\successor_training.py --checkout $NerCheckout --preparation $NerPackage --python $NerPython --model-dir $NerModel --verify-gpu
```

This verifies package, code, model and config hashes, Python 3.11/spaCy 3.7.5, and the currently available GPU against recorded qualification. It writes no training run. Successful output must say `verified_read_only`, `gpu_verified: true`, and `training_started: false`. Without `--verify-gpu`, the default only verifies files/runtime and reports `gpu_verified: false`; that is insufficient to start training.

The complete model has 23 pinned files, including its wheel. The laptop's older GPU model copy lacked the wheel; the complete existing preflight model was used instead, without changing any model bytes. A different GPU/runtime requires separate qualification; there is no automatic CPU fallback. RAM does not replace GPU compute.

## Later explicit training action

Only after delivery and successful desktop verification, start a seed explicitly. **These commands were not run by preparation.** Keep each output directory new. The examples use direct children of the existing artifacts directory.

```powershell
& $NerPython -I -B .\backend\training\flood_ner\successor_training.py --checkout $NerCheckout --preparation $NerPackage --python $NerPython --model-dir $NerModel --start-training --seed 0 --output .\backend\training\flood_ner\artifacts\successor-training-seed-0-v1
```

After seed 0 finishes, run seeds 1 and 2 sequentially by changing both `--seed` and the new output name. The launcher rejects concurrent runs and existing destinations. A failed run retains logs/output; do not delete an active lock or reuse a failed destination automatically. Inspect the recorded process state before any interrupted-run recovery.

The unchanged recipe uses a fresh six-label NER head, the pinned pretrained encoder/vocabulary and frozen tokenizer, batch size 8, dropout 0.1, Adam learning rate 0.001, up to 1,000 steps/30 epochs, and development checks every 35 steps. The selected checkpoint uses development entity F1 with the earliest step breaking ties. Configs have no holdout corpus.

## Interpretation and evaluation

These are **AI-assisted silver** references for a research comparison against available recorded history. Original search/transport records and some historical scope remain incomplete. Neither admission nor the 60-passage count establishes certified freshness, human gold or measured improvement.

Validation has no Taglish ROAD spans and only one Taglish LANDMARK span; the holdout has no LOCAL_AREA spans. Unsupported class performance remains unmeasured. Holdout theme metadata is incomplete. The exact evaluation contract accompanies the private payload. Later isolated evaluation must compare baseline and successor on the same locked holdout; older scores from other texts do not establish improvement.

Copyable desktop-chat prompt:

> Read the current task plan, this guide and the successor preparation report. Verify that the latest code and exact private successor trainer payload are actually present; a Git pull is insufficient. Preserve local changes, historical data/models/results and all ignored files. Use explicit checkout, interpreter, model and package paths. Run only the read-only successor launcher with GPU verification, report its outcome and missing prerequisites, and do not open holdout references. Do not collect, reinstall models/environments, restore archives, push, run old fixed-400 helpers or start training during verification. Training is a later explicit action after delivery and successful GPU verification.
