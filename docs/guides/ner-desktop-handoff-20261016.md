# Continue the NER work across desktop and laptop

> **Last Updated:** October 17, 2026, 3:55 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current desktop action: pull `roi-branch` safely and follow the [history inventory guide](ner-desktop-history-inventory.md). Inventory existing files before restoring any backup.** The helper and a copyable desktop Codex prompt are now in Git. Current proposals are 345 training / 57 validation plus 37 conditional test passages; targets are 345 / 60 / 60, requiring three additional validation and 23 positive test passages if current eligibility holds. The v3 Drive folder below is the October 16 backup, not the newer laptop review packages. Do not start the old launchers, restore archives, collect articles or open private fresh-test content for this task. Return only the inventory/manifest and scope explanation for laptop reconciliation. [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical handoff, restoration and training checkpoints follow; their commands are not the next desktop action.

**Current Gate 3 status:** Improvement preparation is complete; additional-dataset readiness/admission remains open. Development has 244 drafts (179 candidates / 65 holds); isolated test curation has 56 prospective entries, zero admitted independent test records and no seal. Resolve coverage, reference/language, source-use, historical-overlap and the single development tokenizer-alignment failure before corpus admission/export or further training. Original 400-sample results and model roles remain frozen. [Readiness report](../evaluations/flood-ner-additional-dataset-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical qualification-review checkpoint:

**Gate 3 qualification review complete; operational qualification remains open:** Codex reads all **60 held-out passages / 22 articles**, records **120 original/A seed 0 assessments** and accounts for all **391 FP/FN events**. Fourteen passages retain AI reference/convention questions; no label, offset, score or model choice changes. Original seed 0 remains primary (**63.12 test F1**) and A seed 0 exploratory (**67.72**). All 42 event-count slices and preservation checks pass. Next prepare the remaining Gate 3 qualification specification (reference-scope addendum, constructed regression matrix and bounded CPU/Linux/failure/performance plan) before Gate 4 integration. No inference, training or test rerun occurs in this review. [Review](../evaluations/flood-ner-model-qualification-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical held-out benchmark execution:

**Held-out NER evaluation complete:** The six frozen original/A checkpoints and two baselines complete one evaluation on **60 test passages / 290 spans**, 30 English/30 Taglish. Original seed 0 remains primary at **63.12 six-class F1**; exploratory A seed 0 scores **67.72**. Three-seed means are **68.46 original / 70.24 A**, with sample SD **4.85 / 2.20 percentage points**. Rules score **58.97 six-class F1**; native LOC scores **67.02 on the separate coarse task**. All 59 focused tests, 240 metric reconciliation checks and preservation checks pass. Test results are now exposed; no further tuning or seed selection uses them. Next complete the existing Gate 3 model-qualification/error review before Gate 4 isolated integration. [Held-out report](../evaluations/flood-ner-heldout-test-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical development-only checkpoint:

**Frozen experiment and bounded validation trials complete:** Original seeds 0/1/2 reproduce development F1 **67.15 / 70.59 / 72.29**; seed 2 succeeds in its separate authorized recovery folder. Recipe A wins the seed 0 comparison (**71.81**, versus B **70.70**) and completes robustness seeds 1/2. A family mean is **72.61**, sample SD **0.92 percentage points**; original mean is **70.01**, sample SD **2.62**. Original seed 0 remains primary. All five permitted new runs complete before the renewed cutoff; 43 focused tests pass. Prior artifacts, GPU environment, dependencies and .env verify unchanged. Next freeze the final experiment/checkpoint decision, then perform separate held-out testing under the frozen protocol; test predictions remain untouched. [Completed report](../evaluations/flood-ner-validation-study-20261016-v2/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical primary-training checkpoint:

**Primary seed 0 training complete:** The researcher manually ran the frozen GPU recipe. The selected development checkpoint is step 455, F1 67.15 / precision 68.32 / recall 66.03; early stopping ends at step 630 after 175 steps without improvement. All 103 run files remain unchanged; test predictions remain untouched. Manual check-only launchers for robustness seeds 1/2 pass; 29 focused tests pass. Next run seeds 1/2 and the frozen baseline comparisons, keeping seed 0 primary. [Training result](../evaluations/flood-ner-primary-training-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical preparation checkpoint:

**Baseline/training preparation complete:** Frozen rules type/original-offset mapping and seed 0/1/2 configurations pass initialization on the RTX 3060 Ti using the verified qualified export. Each initializes six location labels, 46 GPU parameter arrays and the two CPU upper-classifier arrays required by the pinned architecture, with the exact candidate tokenizer and copied pretrained NER encoder. No optimizer updates, corpus prediction evaluation or held-out test reading occurred. Twenty-one focused unittest methods pass. All 10,531 prior artifact hashes, 23 model files, 22,759 audited research-environment file stats, CLI package versions and .env are unchanged. The next task is the first primary-seed training run under the frozen development-selection protocol. [Preparation verification](../evaluations/flood-ner-experiment-preparation-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical export result:

**Latest desktop result - export verified:** The separate qualified-export-20261016-v1 checkpoint contains the verified 280/60/60 location DocBins and unchanged qualified tokenizer bytes. A separate replay is byte-identical for DocBins/tokenizer/provenance; independent disk reload checks all records. Preserve the qualification and prior checkpoints. Baseline/training preparation is next; no NER prediction evaluation or training has run. [Export result](../evaluations/flood-ner-qualified-export-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Historical qualification checkpoint:** Only NumPy/SciPy in the existing backend CLI were restored to repository pins. The separate desktop-relocation-20261016-162313/qualification package passes on the admitted 400 samples/40 contexts: zero candidate alignment errors, all 56 constructed controls and tokenizer reload pass. Export is the next separate task; no export/training has run. The GPU environment, corpus, model files and .env remain unchanged. Preserve the earlier failure and preparation records; the qualification package supplies the pass binding. [Passing result](../evaluations/flood-ner-desktop-tokenizer-qualification-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Historical first desktop attempt:** The v2 package is restored and relocation is prepared. The single generated qualification invocation failed during the existing backend CLI spaCy/Thinc import with a NumPy dtype-size mismatch, before the isolated research worker. Do not repeat the restoration or qualification as a repair. Resolve CLI compatibility in a separate task and record a subsequent qualification attempt; export remains gated. No dependencies, Windows policy or GPU setup changed. [Actual desktop result](../evaluations/flood-ner-desktop-restoration-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

The original handoff procedure below is retained for audit and future verified restoration.

**Private Drive delivery verified:** The unchanged v2 ZIP is available in the [desktop handoff folder](https://drive.google.com/drive/folders/1gnGV2wP0gNHx2LNa64fwc-U4AIQxRdkT) under your LANES_NER folder. Personal account roicambe02@gmail.com and owner-only permissions were verified. The uploaded ZIP was read back and matches the local SHA-256 and all 28,476,420 bytes. No sharing permissions were changed. Git alone does not carry private evidence.

## Historical October 16 cross-computer continuation: verified v3 backup

The newer private artifacts are now in the owner-only [desktop-to-laptop-20261016-v3 folder](https://drive.google.com/drive/folders/1JrrMzZ3FyP0LGU00xWKF54enyyC87ffX). **Download all 19 files into one folder** and follow its [START-HERE.md](https://drive.google.com/file/d/1Ihw2nzPjT84pM5ZlGEJ3w-b4A1ilPuiL/view?usp=drivesdk). The 11 parts assemble into a 700,047,334-byte ZIP with SHA-256 `9e217a78613b1f86ce9fa2c051262fe8a53d4d74b5ec35f906758f2823cb0336`. Use `JOIN.py`, then `RESTORE.py` verification-only, then explicit restoration. The helper restores missing original paths and skips identical files; conflicting bytes stop before writes. [Verified backup receipt](../evaluations/flood-ner-laptop-backup-20261016/README.md).

Git carries code and metadata; v3 carries 3,863 private research files, including newer models/results and both additional-dataset packages. Preserve laptop `.env` and installed environments, which are excluded. Keep the isolated held-out private texts and labels outside development inspection. Leave original frozen manifests unchanged and record laptop path relocation separately when needed. Continue the same incomplete Gate 3 dataset-readiness task after restoration; do not rerun the original test or start training automatically. [@roicambe](https://github.com/roicambe) (Roi Cambe)

The following numbered procedure is the **historical laptop-to-desktop v2 handoff**, retained for audit. It predates the newer desktop work and is not the current laptop restoration procedure.

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

Three historical evidence references remain formally unreconciled: two now match their restored bytes, while the IPOPHL reference remains hash-divergent. The detailed desktop decision predecessor remains unreconciled. Eleven negative-fixture references and ten copied-manifest aliases are separately explained in the report. Current qualification inputs validate offline; this is not a claim that every historical evidence file has been reconstructed.

Software verification: **880 passed, one skipped**; the earlier 840/one result is historical. [Metadata report](../evaluations/flood-ner-desktop-handoff-20261016/README.md).
