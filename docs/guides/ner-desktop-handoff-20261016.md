# Continue the NER work on the existing desktop checkout

Updated: October 16, 2026, 12:39 PM (Asia/Manila). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Private Drive delivery verified:** The unchanged v2 ZIP is available in the [desktop handoff folder](https://drive.google.com/drive/folders/1gnGV2wP0gNHx2LNa64fwc-U4AIQxRdkT) under your LANES_NER folder. Personal account roicambe02@gmail.com and owner-only permissions were verified. The uploaded ZIP was read back and matches the local SHA-256 and all 28,476,420 bytes. No sharing permissions were changed. Git alone does not carry private evidence.

## 1. Get the two parts

Code and metadata come from `roi-branch`; implementation commit `ac1ae53df246fdee376909d20b9ffd52f7b5f264` is pushed and verified. Pull the latest branch to include the publication receipt too. Private data come from `LANES-NER-desktop-handoff-20261016-v2.zip`, accompanied by its `.sha256`, `file-manifest.json` and `START-HERE.md` in the same local handoff folder. Preserve the previous ZIPs.

On the desktop, open the **existing LANES checkout**, inspect `git status --short` and preserve any local work before pulling. Do not discard or overwrite local edits. With a clean checkout on `roi-branch`, run `git pull --ff-only origin roi-branch`. If it refuses, retain the error and reconcile the branches before continuing.

Download [the verified ZIP](https://drive.google.com/file/d/1bir775mAWUtHPBDbsTsLavsX8mChYtsp/view?usp=drivesdk) to an actual folder you can locate. No `incoming` folder is required. In PowerShell opened inside the existing checkout:

```powershell
$lanesRoot = (git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Open the existing LANES checkout first.' }
$handoffZip = (Resolve-Path -LiteralPath (Read-Host 'Paste the downloaded ZIP full path')).Path
$handoffSha = 'afe11aa15398d9b88e7ef268c75f7d51c79107206a60f29ac4313264f4dba65f'
if ((Get-FileHash -LiteralPath $handoffZip -Algorithm SHA256).Hash.ToLowerInvariant() -ne $handoffSha) { throw 'ZIP checksum mismatch; stop.' }
$researchCandidates = @(Get-ChildItem -Path (Join-Path $lanesRoot 'backend/training/flood_ner/artifacts/gpu-qualification*/research-env/Scripts/python.exe') -File)
if ($researchCandidates.Count -ne 1) { throw 'Locate the existing Python 3.11 GPU interpreter; do not create or reinstall an environment.' }
$researchPython = $researchCandidates[0].FullName
$handoffHelper = Join-Path $lanesRoot 'backend/training/flood_ner/desktop_handoff.py'
```

These variables use discovered paths. They do not assume that the laptop's `D:` or historical desktop `E:` location is current. If there are several research environments, choose the previously qualified one using its saved environment manifest and pass its exact path. Missing prerequisites are a stop, not a request to reinstall GPU dependencies.

## 2. Verify before restoring

```powershell
& $researchPython -B $handoffHelper --repo $lanesRoot --archive $handoffZip --sha256 $handoffSha --research-python $researchPython
if ($LASTEXITCODE -ne 0) { throw 'Verification failed; preserve the error. Nothing was restored.' }
```

The standard-library helper checks the whole ZIP, declared payload, frozen counts, local conflicts, tracked checkout dependencies and existing interpreter/package metadata. It verifies all 23 model files against the laptop inventory. The metadata probe does not import spaCy or torch. It searches the existing backend environment for the offline CLI dependencies, then considers the existing research environment. Supply `--runner-python` or `--model-dir` only when their actual existing paths have been verified.

Existing conflicting evidence stops restoration before writing. Identical files are skipped; no existing bytes are overwritten. The archive includes the original research-only checkpoints and the separate admitted derivative; their statuses remain distinct.

## 3. Restore and prepare relocation

Only after verification passes:

```powershell
$relocationOut = Join-Path $lanesRoot ('backend/training/flood_ner/artifacts/desktop-relocation-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
& $researchPython -B $handoffHelper --repo $lanesRoot --archive $handoffZip --sha256 $handoffSha --research-python $researchPython --restore --output $relocationOut
if ($LASTEXITCODE -ne 0) { throw 'Restoration/preparation failed; preserve the error and do not run qualification.' }
Get-Content -LiteralPath (Join-Path $relocationOut 'relocation.json')
Get-Content -LiteralPath (Join-Path $relocationOut 'QUALIFY.ps1')
```

The output contains separately versioned model/tokenizer relocation manifests, unchanged candidate tokenizer bytes, verified environment paths and the exact qualification command. Original manifests are preserved. A path rebinding establishes identical model/vocabulary bytes; it is **not a qualification pass**.

## 4. Separate desktop qualification

After checking the successful restore result and generated command, run the script in the same desktop session:

```powershell
& (Join-Path $relocationOut 'QUALIFY.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Corpus qualification failed; keep its logs. Do not export or train.' }
```

The command uses the discovered CLI interpreter and existing isolated Python 3.11/spaCy 3.7.5 research environment. It reads tokenizers/vocabulary without running NER predictions. Its output is a new `qualification` folder beneath the relocation directory. Require a successful result, zero candidate alignment errors across 1,465 location spans, passing constructed controls and reproducible tokenizer reload. Record failures without changing Windows policy, tokenizer rules or GPU dependencies automatically.

No desktop command has been executed by the laptop agent. Training-format export follows only a successful qualification. The model and dataset are unchanged, and this handoff does not train or deploy anything.

## Evidence and limitations

ZIP: **28,476,420 bytes**, 1,757 payload files; **145,167,696** uncompressed payload bytes. SHA-256:

```text
afe11aa15398d9b88e7ef268c75f7d51c79107206a60f29ac4313264f4dba65f
```

The laptop's temporary restore revalidated all 400 admitted samples, 40 contextual pairs and all 407 selected source-evidence files for 138 articles. Language counts are 200/200 and partitions 280/60/60. Forty contexts remain paired records within the 400, not extra samples. All 23 recorded desktop/laptop model-file identities match; model weights, Python environments and credentials are excluded.

Three historical evidence references remain missing or hash-divergent and the detailed desktop decision predecessor remains unreconciled. Eleven negative-fixture references and ten copied-manifest aliases are separately explained in the report. Current qualification inputs validate offline; this is not a claim that every historical evidence file has been reconstructed.

Software verification: **880 passed, one skipped**; the earlier 840/one result is historical. [Metadata report](../evaluations/flood-ner-desktop-handoff-20261016/README.md).
