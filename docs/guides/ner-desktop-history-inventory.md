# Desktop NER history inventory

> **Last Updated:** October 17, 2026, 3:50 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

Run this on the **desktop that performed the earlier training**, after pulling `roi-branch`. The next task is history inventory and reconciliation. It does not train, restore files, install packages, open archives, or certify that every earlier collection has been found. Inventory the desktop before downloading/restoring backup material; restoration would change the evidence being checked.

The helper is [history_inventory.py](../../backend/training/flood_ner/history_inventory.py), included in Git. Run it directly from the pulled checkout; a Downloads copy or private helper bundle is unnecessary. Use Python **3.10 or newer**, with no extra packages. The helper is separate from the GPU hardware inventory and training launchers. Do not run archived restore/join scripts for this task.

## Pull the handoff safely

Open PowerShell. The path below is the recorded desktop checkout; replace it if the project moved. These commands stop on local changes or a failed Git operation. Preserve any reported changes and resolve them with Codex before continuing; do not reset, clean, force-pull or overwrite them.

```powershell
Set-Location -LiteralPath "E:\Files\Documents\GitHub\LANES" -ErrorAction Stop
$desktopChanges = git status --porcelain
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect the checkout.' }
if ($desktopChanges) { throw 'Local changes exist. Preserve them and resolve the pull with Codex first.' }
git switch roi-branch
if ($LASTEXITCODE -ne 0) { throw 'Branch switch failed. Stop and keep the error.' }
git pull --ff-only origin roi-branch
if ($LASTEXITCODE -ne 0) { throw 'Fast-forward pull failed. Stop; do not reset or force-pull.' }
```

Read this updated guide and [task plan](../task_plan.md). Earlier restoration/training instructions remain historical and are not the next action.

## Run only the history inventory

From that repository root, check `py -3 --version` and use Python 3.10+. Choose an output directory that does not already exist:

```powershell
py -3 -I -S -B .\backend\training\flood_ner\history_inventory.py --checkout (Get-Location).Path --output .\backend\training\flood_ner\artifacts\desktop-history-inventory-v1
```

The current proposal is **345 training / 57 validation** with **37 conditionally supported independent-test passages**. The user's targets are **345 / 60 / 60**, totaling 465 if all qualify. Missing material is **three additional validation passages and 23 positive test passages (ten English, 13 Taglish)** for the current joint witness. Keep all 345 proposed training passages; never move previously fitted source groups into validation/testing. These are proposed/conditional counts, not an admitted or frozen successor corpus. This desktop task does not select the missing passages.

If you know of article collections or backups **outside that checkout**, include their actual locations with repeated `--extra-root` arguments. For example, append `--extra-root "D:\Research\old-flood-collection"` only if that folder exists. Do not pass the entire user profile or drive. Roots must be distinct and must not contain one another. If another collection is already inside the checkout, it is covered without an extra root, subject to the exclusions below.

The result is two files under `backend/training/flood_ner/artifacts/desktop-history-inventory-v1/`: `inventory.json` and its SHA-256 binding in `manifest.json`. Keep them together and private. A zero exit code means the named readable scope was inventoried; exit code 2 means a report was saved with read/metadata errors that need review. An existing output, invalid root, overlapping roots or unsafe destination is rejected. A second run needs a new output name; earlier reports are preserved.

Hashing many saved files and backups can take several minutes without terminal output. Wait for the final JSON summary and the two report files before treating the run as complete.

The inventory records relative paths, byte sizes, modification times and SHA-256 hashes. It does **not** export file contents. Environments, dependencies/caches, recognized model directories/weights, secret filenames and recognized isolated-test paths are excluded. Links and Windows reparse points are not followed. Exclusion counts and read errors remain visible. Backup archives are hashed as files, never unpacked. Unrecognized private test folders must be explicitly excluded using `--exclude "FULL\PATH\TO\PRIVATE_TEST_FOLDER"`; do not opt them into metadata extraction.

Keep collection files stable while the helper runs. Large unrelated routing tiles can make a whole-checkout scan slow. If present, you may explicitly exclude the checkout's `graphhopper_data` and `valhalla_data` directories with repeated `--exclude` arguments. The exclusions are recorded and are not treated as verified history. Do not exclude a folder that might contain article, annotation or training-history material merely to speed up the scan.

Source metadata extraction is optional and normally unnecessary for the first desktop comparison. Only if a specific historical source-capture JSON/JSONL file has been identified as safe, append `--source-metadata "FULL\PATH\TO\sources.jsonl"`. This projects source IDs, sanitized URLs, recorded dates, hashes and recorded grouping IDs. It never copies article text, titles, entity labels, nested annotations or model results. URL query strings/fragments are removed. Files that mix unrelated structures are not recursively interpreted. The output remains private because paths and source identities can still be sensitive.

## What Git and Google Drive contain

| Location | Available material | Meaning for this desktop task |
|---|---|---|
| Pulled Git checkout | Helper, tests, byte-preservation rules, public aggregate reports and current instructions | Sufficient to run the inventory; no dependency install or private-package download is required. |
| [October 16 v3 Drive backup](https://drive.google.com/drive/folders/1JrrMzZ3FyP0LGU00xWKF54enyyC87ffX) | Historical desktop-to-laptop handoff: 19 parts/manifest/instruction files representing 3,863 logical payload files | Backup reference only. Do not download or restore it before inventorying the desktop. It does not contain the newer October 17 review/selection packages. |
| Laptop's ignored artifacts | Newer source-bound review, design, qualification, history-reconciliation and isolated curator packages | These do not transfer through Git. Public reports do not establish their presence on this desktop; do not reconstruct private records from aggregates. |

The Drive folder metadata was checked through the connected account; this publication does not perform a new remote byte-integrity check or change sharing. Prior archived delivery receipts remain historical. No new private-data upload is required for this task. Captures, annotations, model weights, environments and private curator ledgers stay out of Git. Development may inspect only permitted aggregate curator status/manifests, never fresh-test texts or labels.

## Return the inventory and resume the work

Return the two inventory files through this chat or the existing private handoff when requested, together with the actual checkout path, included extra folders, explicit exclusions and any remaining unknown locations. Do not commit the inventory to Git. The helper does not upload or share the report automatically. No raw article, annotation file, model or environment needs to be returned for the initial comparison.

The laptop coordinator will reconcile the returned metadata/hashes against the recorded October 16 backup and exposure supplement. If required private evidence is absent on the desktop, report that limitation and return the inventory; do not treat it as permission to restore, recollect or invent missing records. Keep unknown history explicit. Isolated test curation remains separate from development work. Further collection also needs the recorded **202/200 URL exposure failure** resolved; no collection allowance is reset by a Git pull.

Paste this into the desktop Codex chat after pulling:

```text
Continue LANES's desktop history inventory only. Read AGENTS.md, DESIGN.md,
docs/task_plan.md and docs/guides/ner-desktop-history-inventory.md first.
Preserve local changes and verify roi-branch. The targets are 345 training,
60 validation and 60 independent test passages; current proposals remain
345/57 with only 37 conditionally supported test passages. Three validation
and 23 positive test passages are still missing; do not select them now.
Run the standard-library history_inventory.py on this actual desktop checkout
into a new ignored output folder. Include only known additional historical
collection folders, preserve the helper's exclusions, and report unspecified
locations as unknown. Do not open isolated fresh-test text/labels, restore
backups, change environments, collect articles, admit/freeze/export data,
run inference or train. Return inventory.json and manifest.json with their
hashes, errors, exclusions and scope explanation for laptop reconciliation.
The Drive v3 folder is an October16 backup; newer private laptop reviews are
not supplied by Git. Do not assume that aggregate reports transfer them or
that the inventory alone proves complete history or test freshness.
```

The laptop smoke run cannot substitute for this desktop action. The returned inventory must still be compared against the recorded backup manifest and exposure supplement. Unspecified folders, excluded material, missing archives and collections that were deleted or never saved can remain evidence gaps. Do not mark external history complete or seal the independent test merely because the helper completed successfully.

After supported history reconciliation, qualify additional validation material and complete isolated test coverage under their separate grouping/use/reference rules. Only after the independent-test boundary passes can actual dataset admission, partition freeze, qualified export and the desktop GPU training handoff be prepared. The 402 qualified development candidates, old holds and known tokenizer failure, original 400-passage experiment, models and results remain preserved. References remain AI-assisted silver; neither human verification nor measured improvement is implied.
