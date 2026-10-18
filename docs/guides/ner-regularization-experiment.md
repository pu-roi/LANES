# Regularization experiment: verified desktop delivery

> **Last Updated:** October 18, 2026, 11:41 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current NER handoff: the regularization experiment is verified on private Drive; matching code and instructions accompany this roi-branch publication.** The 345 training / 60 validation exports are unchanged. One L2 = 0.05 candidate has seed 0/1/2 configs and a fixed maximum-three-run protocol. All four uploaded files match authenticated readback; parent, destination and files are owner-only. Desktop receipt and GPU verification remain pending. No training, inference or holdout access occurred during delivery. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next on the desktop:** preserve local changes, pull roi-branch with --ff-only, authenticate and extract the delivered archive into an absent destination, then run read-only GPU/schema verification and STOP. Actual training is a separate explicit task after verification; the completed research holdout stays outside tuning.

[Delivery evidence](../evaluations/flood-ner-regularization-delivery-20261018/README.md) · [Preparation](../evaluations/flood-ner-regularization-preparation-20261018/README.md)


Prepared data: **345 training / 60 validation**. No holdout files are included.
One fixed candidate uses L2 = 0.05 with all other training settings unchanged.
Maximum later runs: seed 0, then conditional seeds 1/2. This handoff authorizes no training.

Drive folder: https://drive.google.com/drive/folders/1vKssoZurLa6WjuJPftXRbJ7GcoefimKq

Download the ZIP, SHA256SUMS.txt, transfer-manifest.json and START-HERE.md.
ZIP: regularization-desktop-20261018-v21.zip
Size: 216866 bytes
SHA-256: 2336dbafdb93832323c702c61d142ad68b9bfce2371c84fbb27c50117183884f
Transfer manifest SHA-256: 5f9c5c58b34356826ba6427ee0c60820f8cb92e59e0eb7ee9452e0ac10f7784e
Experiment manifest SHA-256: 35050682217749d945a3c5fecbe5d3771212b1df1276f9f5f95bad4c7d6a0e78

The archive contains exactly 20 files: twelve in package/, three control templates,
the frozen protocol, baseline metrics, development slice metadata, CPU qualification
and experiment manifest. Instructions and transfer receipts stay outside it.
No model weights or environment are transferred. Reuse existing qualified resources.

## Desktop steps

Open PowerShell in the actual LANES checkout. Preserve local changes and stop on conflicts.
Do not reset, restore backups, install dependencies or overwrite files.

~~~powershell
git status --short
if (git status --porcelain) { throw 'Preserve local changes; reconcile before switching/pulling.' }
git switch roi-branch
if ($LASTEXITCODE -ne 0) { throw 'Stop; branch switch failed.' }
git pull --ff-only origin roi-branch
if ($LASTEXITCODE -ne 0) { throw 'Stop; pull failed. Do not reset or force.' }
$RegularizationRoot = (Get-Location).Path
$RegularizationPython = (Resolve-Path -LiteralPath (Read-Host 'Existing qualified GPU python.exe')).Path
$RegularizationModel = (Resolve-Path -LiteralPath (Read-Host 'Existing pinned model directory')).Path
$RegularizationZip = (Resolve-Path -LiteralPath (Read-Host 'Downloaded regularization ZIP')).Path
$RegularizationTransfer = (Resolve-Path -LiteralPath (Read-Host 'Downloaded transfer-manifest.json')).Path
$RegularizationExperiment = Join-Path $RegularizationRoot 'backend\training\flood_ner\artifacts\regularization-desktop-20261018-v21'
& $RegularizationPython -I -S -B .\backend\training\flood_ner\regularization_delivery.py extract --checkout $RegularizationRoot --archive $RegularizationZip --manifest $RegularizationTransfer --manifest-sha256 5f9c5c58b34356826ba6427ee0c60820f8cb92e59e0eb7ee9452e0ac10f7784e --destination $RegularizationExperiment
if ($LASTEXITCODE -ne 0) { throw 'Stop; preserve the extraction blocker/partial destination.' }
& $RegularizationPython -I -B .\backend\training\flood_ner\regularization_experiment.py verify --checkout $RegularizationRoot --experiment $RegularizationExperiment --experiment-sha256 35050682217749d945a3c5fecbe5d3771212b1df1276f9f5f95bad4c7d6a0e78 --python $RegularizationPython --model-dir $RegularizationModel --verify-gpu
if ($LASTEXITCODE -ne 0) { throw 'Stop; preserve the GPU/schema verification blocker.' }
~~~

The standard-library transfer helper validates full archive/manifest checksums,
all member bytes, regular safe paths, exact membership and matching checkout
implementation/test bytes before creating the destination. It executes no archive code.
Extraction is exclusive. Interrupted or existing destinations are preserved, never reused.

Require verified_read_only, configuration_schema_verified true, gpu_verified true and
training_started false. STOP after verification. If extraction is already complete,
verify the experiment read-only instead; partial or conflicting destinations need review.

## Copyable desktop-chat prompt

Verify the newly delivered LANES regularization experiment only. Read DESIGN.md,
docs/task_plan.md and docs/guides/ner-regularization-experiment.md. Preserve local
changes; use roi-branch and pull --ff-only when safe. Download all four files from
the Drive folder above. Authenticate the exact ZIP and transfer manifest checksums.
Use the published regularization_delivery.py helper, not code from the archive;
extract only into the absent artifact destination. Verify twenty experiment files
and twelve package files. Locate the actual existing qualified Python 3.11/spaCy
3.7.5 GPU environment and pinned model. Run regularization_experiment.py verify
with the exact experiment hash and --verify-gpu. Require verified_read_only,
configuration_schema_verified true, gpu_verified true, training_started false.
Return the actual desktop receipt and verification output, then STOP.
Do not install, overwrite, fall back to CPU training, retry automatically, train,
or access/re-evaluate the completed research holdout. Missing resources, conflicting
source bytes or incompatible runtime/GPU must be reported as specific blockers.

## Later experiment (not authorized here)

The existing authenticated v19 corrected control is the baseline. Candidate seed 0
must improve strict validation micro F1 and not reduce ROAD or LOCAL_AREA F1.
Only then run seeds 1/2 sequentially. Retain the candidate only if the three-seed
overall mean improves and both protected-label means do not regress. Tolerance 1e-12;
overall ties fail improvement, protected-label ties pass non-regression.
At most three new runs, no control retraining, extra configuration or automatic retry.
Use fresh six-class head and pinned encoder initialization, never resume checkpoints.
Preserve raw logs, step curves, resolved configs, checkpoint-selection evidence,
all-label/language metrics, unsupported slices, negatives and train/validation gaps.
The completed research holdout is excluded from selection and any further comparison.
References remain AI-assisted silver with incomplete history/accounting limitations.
