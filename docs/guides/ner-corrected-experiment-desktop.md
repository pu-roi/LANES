# Corrected NER experiment: desktop receipt and GPU verification

> **Last Updated:** October 18, 2026, 11:41 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current NER handoff: the regularization experiment is verified on private Drive; matching code and instructions accompany this roi-branch publication.** The 345 training / 60 validation exports are unchanged. One L2 = 0.05 candidate has seed 0/1/2 configs and a fixed maximum-three-run protocol. All four uploaded files match authenticated readback; parent, destination and files are owner-only. Desktop receipt and GPU verification remain pending. No training, inference or holdout access occurred during delivery. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next on the desktop:** preserve local changes, pull roi-branch with --ff-only, authenticate and extract the delivered archive into an absent destination, then run read-only GPU/schema verification and STOP. Actual training is a separate explicit task after verification; the completed research holdout stays outside tuning.

[Delivery report](../evaluations/flood-ner-regularization-delivery-20261018/README.md) · [Desktop instructions](ner-regularization-experiment.md) · [Private Drive handoff](https://drive.google.com/drive/folders/1vKssoZurLa6WjuJPftXRbJ7GcoefimKq)

**Earlier dated checkpoints below are historical.**

**Current NER task completed: one stronger-weight-decay experiment is prepared and CPU-qualified.** The existing 345 training/60 validation records, annotations, tokenizer and grouping remain unchanged. One twelve-file package supplies seed 0/1/2 configs with only `L2: 0.01 -> 0.05` changed. Fresh 341 tests/four subtests pass; 72 new checks also pass in the pinned runtime. No inference, training or research-holdout content access occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next:** separately publish matching code and privately deliver the experiment bundle; then perform actual desktop read-only GPU verification. Training follows as a separate explicit task: seed 0 screening, conditional 1/2, maximum three runs, with overall improvement and ROAD/LOCAL_AREA protection required. The completed holdout stays outside tuning. Delivery/GPU verification remain pending; the desktop can remain off.

[Preparation report](../evaluations/flood-ner-regularization-preparation-20261018/README.md) · [Operator guide](ner-regularization-experiment.md)

**Prior checkpoints follow; their dated “current/next” wording is historical.**

**Current NER status: v19 diagnosis and the one-time frozen research evaluation are complete on the laptop.** Dataset 345/60/60 and validation-selected control/seed 0 stay unchanged. V19 seed 0 training/validation/holdout F1: **98.09% / 71.60% / 73.63%**. Historical v16 seed 0 holdout 74.74%; rules 53.49%. Holdout three-seed means: control 70.34%, v16 75.13%. These results do not establish an overall v19 improvement or authorize choosing a model using the holdout.

**Next:** a separate development plan from the existing training/validation error review; no new articles or automatic retraining. Gate 3 research measurement is complete, while operational qualification, integration and release remain open. The holdout has now been evaluated and must not be tuned against or evaluated again under this protocol. AI-assisted silver, incomplete history/accounting and no certified-fresh claim remain. No collection, new training, reference/partition change, integration, upload, commit or push occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

[Diagnosis/evaluation report](../evaluations/flood-ner-v19-diagnosis-evaluation-20261018/README.md) · [Laptop evaluation guide](ner-corrected-holdout-laptop.md)

**Historical checkpoints follow.** Their “current/next” wording describes earlier dated tasks and is superseded by the status above.

**Stop after read-only verification. Do not train during this task.** The corrected revision uses 345 training / 60 validation passages. The separate 60-passage research holdout remains on the laptop and is absent from this delivery. Three packages preserve the approved control/dropout/learning-rate configurations and frozen five/seven-run future protocol. [Preparation evidence](../evaluations/flood-ner-corrected-experiment-preparation-20261018/README.md).

## 1. Pull matching code safely

Open PowerShell in the actual desktop LANES checkout. Preserve all local work. A nonempty status requires review before any pull; do not reset, stash, overwrite or restore archives automatically.

```powershell
$NerChanges = @(git status --porcelain)
if ($LASTEXITCODE -ne 0) { throw "Not a usable Git checkout." }
if ($NerChanges.Count -gt 0) { throw "Local changes exist; preserve and review before pulling." }
git switch roi-branch
if ($LASTEXITCODE -ne 0) { throw "Branch switch failed." }
git pull --ff-only origin roi-branch
if ($LASTEXITCODE -ne 0) { throw "Pull failed; stop without resetting." }
$NerRoot = (Get-Location).Path
```

A Git pull alone does not deliver ignored training files.

## 2. Download the verified private transfer

Use the existing personal account to download these three files from the owner-only [v19 Drive folder](https://drive.google.com/drive/folders/1LDO770D82NXHZRiYNZrHe5oyLo7-vJU7): [ZIP](https://drive.google.com/file/d/12spTf1iMc05z2HbEp1xuDhhquJ0HF_UN/view?usp=drivesdk), `SHA256SUMS.txt` and `START-HERE.md`. Earlier handoffs are historical and unchanged.

Archive: `LANES-NER-corrected-experiment-20261018-v19.zip`

Complete size: **469,492 bytes**

SHA-256:

```text
a2c7234a4b9846c845a405b9ed5ebeb3f75745c2b2015f0970ac71f953a4d2da
```

The archive contains exactly **40 files** under `corrected-experiment-desktop-20261018-v19/`: three twelve-file trainer directories plus the protocol, aggregate CPU qualification, instructions and transfer manifest. Source captures, correction/annotation ledgers, holdout files, credentials, environments and model weights are excluded.

Locate the actual existing qualified **Python 3.11 / spaCy 3.7.5 GPU interpreter** and **tl_calamancy_md 0.1.0** model revision `51a40433059d8a2c25b98a48eca854f8789a491a`. The model directory must contain the 23 files bound by each model contract. Do not install or replace resources to obtain a pass.

## 3. Verify and extract into an absent destination

Set these variables using the actual desktop paths. The ZIP can stay in Downloads; extraction goes into a new ignored artifact directory. Keep all scripts and receipts outside the twelve-file trainer directories.

```powershell
$NerPython = (Resolve-Path -LiteralPath (Read-Host "Existing qualified GPU python.exe")).Path
$NerModel = (Resolve-Path -LiteralPath (Read-Host "Existing pinned model directory")).Path
$NerZip = (Resolve-Path -LiteralPath (Read-Host "Downloaded v19 ZIP path")).Path
$NerDestination = Join-Path $NerRoot "backend\training\flood_ner\artifacts\corrected-experiment-desktop-20261018-v19"
if (Test-Path -LiteralPath $NerDestination) { throw "Destination exists; preserve it and verify separately." }
$NerExtractCode = @'
import hashlib, json, stat, sys, zipfile
from pathlib import Path, PurePosixPath
NAME = "corrected-experiment-desktop-20261018-v19"
EXPECTED_SHA = "a2c7234a4b9846c845a405b9ed5ebeb3f75745c2b2015f0970ac71f953a4d2da"
MANIFEST_SHA = "071c97fd761d3d5e21bdf5de0d43b01f1f915f96a82c8351e0cba14e5b1cf98b"
VARIANTS = ("control", "higher_dropout", "lower_learning_rate")
FILES = {"train.spacy", "dev.spacy", "tokenizer.bin", "model-contract.json",
 "qualification.json", "evaluation-contract.json", "gpu-qualification.json",
 "gpu-runtime.json", "train-seed-0.cfg", "train-seed-1.cfg", "train-seed-2.cfg", "handoff-manifest.json"}
def require(ok, message):
 if not ok: raise ValueError(message)
def sha(data): return hashlib.sha256(data).hexdigest()
archive, output = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).absolute()
root = Path.cwd().resolve()
require(archive.stat().st_size == 469492 and sha(archive.read_bytes()) == EXPECTED_SHA, "ZIP checksum/size mismatch")
allowed = (root / "backend/training/flood_ner/artifacts").resolve()
require(output.name == NAME and output.resolve().parent == allowed and not output.exists(), "Absent checkout artifact destination required")
expected = {"packages/" + v + "/" + n for v in VARIANTS for n in FILES}
expected |= {"experiment-protocol.json", "cpu-qualification.json", "START-HERE.md", "transfer-manifest.json"}
data = {}
with zipfile.ZipFile(archive) as z:
 infos = z.infolist()
 require(len(infos) == 40 and len({i.filename for i in infos}) == 40, "Unexpected/duplicate ZIP members")
 for info in infos:
  n, path = info.filename, PurePosixPath(info.filename)
  require(not path.is_absolute() and path.parts[0] == NAME and n == path.as_posix()
   and ".." not in path.parts and ":" not in n and chr(92) not in n
   and not info.is_dir() and stat.S_ISREG(info.external_attr >> 16), "Unsafe ZIP entry")
  relative = "/".join(path.parts[1:])
  require(relative in expected and info.file_size <= 2000000, "Unexpected ZIP member/size")
  data[relative] = z.read(info)
require(set(data) == expected and sha(data["transfer-manifest.json"]) == MANIFEST_SHA, "Transfer manifest mismatch")
manifest = json.loads(data["transfer-manifest.json"])
require(set(manifest["files"]) == expected - {"transfer-manifest.json"}
 and manifest["training_authorized"] is False and manifest["holdout_included"] is False, "Unsafe transfer scope")
for name, binding in manifest["files"].items():
 require(len(data[name]) == binding["bytes"] and sha(data[name]) == binding["sha256"], "Transfer member hash mismatch")
for binding in manifest["implementation"]:
 relative = PurePosixPath(binding["path"])
 require(not relative.is_absolute() and ".." not in relative.parts and ":" not in str(relative)
  and chr(92) not in str(relative), "Unsafe implementation binding")
 source = root.joinpath(*relative.parts).resolve()
 require(source.is_relative_to(root) and source.is_file()
  and sha(source.read_bytes()) == binding["sha256"], "Pull matching implementation before extraction")
for variant in VARIANTS:
 prefix = "packages/" + variant + "/"
 package = json.loads(data[prefix + "handoff-manifest.json"])
 require(set(package["files"]) == FILES - {"handoff-manifest.json"} and package["variant"] == variant
  and package["training_authorized"] is False and package["training_started"] is False, "Trainer capability mismatch")
 require(sha(data[prefix + "handoff-manifest.json"]) == manifest["trainer_manifests"][variant], "Trainer manifest mismatch")
 for name, digest in package["files"].items():
  require(sha(data[prefix + name]) == digest, "Trainer payload mismatch")
 for name, digest in manifest["shared_exports"].items():
  require(sha(data[prefix + name]) == digest, "Packages do not share qualified data")
 require(package["experiment_protocol_sha256"] == sha(data["experiment-protocol.json"]), "Protocol binding mismatch")
output.mkdir()
for name, payload in data.items():
 target = output.joinpath(*PurePosixPath(name).parts)
 target.parent.mkdir(parents=True, exist_ok=True)
 with target.open("xb") as stream: stream.write(payload)
print(json.dumps({"state": "extracted_verified", "files": len(data), "packages": 3, "training_started": False}))
'@
& $NerPython -I -S -B -c $NerExtractCode $NerZip $NerDestination
if ($LASTEXITCODE -ne 0) { throw "Extraction failed; preserve evidence and stop." }
```

The published standard-library snippet verifies the archive checksum, exact member set, safe regular-file paths, transfer/member hashes, source helper bindings, every trainer manifest, shared export hashes and protocol binding **before creating the destination**. It executes no archived code. Writes use exclusive creation. On interruption, preserve partial output and do not reuse the directory. The laptop exercised the same snippet and ten successful/rejection controls; the authenticated archive matches every qualified source file.

If the correct destination already exists from a completed receipt, have the desktop agent verify its existing membership and all transfer/trainer hashes without extraction or overwrite. A partial destination or any conflicting byte is a blocker; no automatic repair.

## 4. Verify each package on the desktop GPU

From the checkout root, after successful receipt, run:

```powershell
$NerResults = @()
foreach ($NerVariant in @("control", "higher_dropout", "lower_learning_rate")) {
    $NerPackage = Join-Path $NerDestination ("packages\" + $NerVariant)
    $NerJson = & $NerPython -I -B .\backend\training\flood_ner\successor_training.py --checkout $NerRoot --preparation $NerPackage --python $NerPython --model-dir $NerModel --verify-gpu
    if ($LASTEXITCODE -ne 0) { throw "Verification failed for $NerVariant; stop and preserve output." }
    $NerResult = ($NerJson -join [Environment]::NewLine) | ConvertFrom-Json
    if ($NerResult.state -ne "verified_read_only" -or $NerResult.configuration_schema_verified -ne $true -or $NerResult.gpu_verified -ne $true -or $NerResult.training_started -ne $false) {
        throw "Unexpected verification status for $NerVariant."
    }
    $NerResults += [pscustomobject]@{ variant = $NerVariant; result = $NerResult }
}
$NerResults | ConvertTo-Json -Depth 10
```

Require all three results. The launcher checks exact package files/hashes, current code, pinned model bytes, actual runtime/GPU and all three configuration schemas. It resolves local resource paths without modifying the frozen package. A different GPU/runtime, missing model/interpreter or source mismatch stops verification. No automatic installation or CPU fallback.

**Stop here.** Return the actual checkout/commit, package location, archive/member checks and all three read-only results. Keep any new receipt/log outside the trainer directories. The laptop's `successor_experiment_preparation` verification command requires private audit inputs intentionally absent here; it is not a desktop prerequisite. Frozen preparation flags remain unchanged; later delivery/GPU events belong in separate receipts.

## Copyable desktop-chat prompt

```text
Continue LANES with the corrected v19 experiment handoff. This task is RECEIPT AND READ-ONLY GPU VERIFICATION ONLY. Do not train or run inference.

Read AGENTS.md, DESIGN.md, docs/task_plan.md and docs/guides/ner-corrected-experiment-desktop.md. Inspect the actual checkout and preserve local work. Safely switch to roi-branch and pull --ff-only only when local changes permit. Never reset, overwrite, restore old archives or reuse completed run destinations.

Download the v19 ZIP/checksum/instructions from the Drive folder linked in the guide. The ZIP must be 469492 bytes with SHA-256 a2c7234a4b9846c845a405b9ed5ebeb3f75745c2b2015f0970ac71f953a4d2da. Use the published verification/extraction snippet, not executable code from an archive. Extract only into the absent checkout artifact destination. If an earlier complete extraction exists, verify it read-only instead; report partial/conflicting files rather than overwriting.

Verify all 40 transfer members and the three exact twelve-file packages: control, higher_dropout, lower_learning_rate. Confirm shared corrected train/dev/tokenizer bytes and the frozen protocol; preserve package manifests. Locate the existing qualified Python 3.11/spaCy 3.7.5 GPU interpreter and exact 23-file pinned model using actual desktop paths. Do not install or replace anything.

Run successor_training.py --verify-gpu for each package with explicit checkout/preparation/python/model-dir. Require verified_read_only, configuration_schema_verified=true, gpu_verified=true, training_started=false. Stop on the first error and report its specific blocker. No automatic retries, CPU fallback, --start-training, seed execution, holdout access or inference.

Do not run the laptop preparation verifier: its private audit dependencies were deliberately not delivered. Return actual checkout/commit/interpreter/model/package paths, receipt checks and the three GPU verification JSON results. STOP after verification. Actual five/seven-run training is a separate explicit task.
```

References remain AI-assisted silver with documented incomplete history/accounting. The unresolved validation landmark question, zero Taglish ROAD validation support and one Taglish LANDMARK span remain limitations. Delivery does not establish model improvement, human gold or certified-fresh evaluation.
