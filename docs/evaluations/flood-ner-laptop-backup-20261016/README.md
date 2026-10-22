# Verified desktop-to-laptop NER backup

> **Last Updated:** October 16, 2026, 11:20 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The newer private desktop research artifacts are uploaded to the owner-only [desktop-to-laptop-20261016-v3 Drive folder](https://drive.google.com/drive/folders/1JrrMzZ3FyP0LGU00xWKF54enyyC87ffX). All **19 uploaded files** were fetched back through authenticated Drive access and their complete byte lengths and SHA-256 hashes match the local files. The folder and all children have only the owner permission; sharing settings and older backups were preserved. [Verification receipt](verification.json).

The backup represents **3,863 repository-relative files**, deduplicated into **2,357 content objects**. It includes captured source evidence, annotations and admissions, the pinned model/tokenizer, exports, completed original/A/B runs and recovery/failure records, evaluation and review evidence, improvement preparation, and both additional-dataset packages. Isolated held-out content was handled mechanically as bytes/hashes, without opening its text or labels for development review.

The content-addressed ZIP is **700,047,334 bytes** and restores **2,220,662,026 logical bytes**. Its SHA-256 is:

```text
9e217a78613b1f86ce9fa2c051262fe8a53d4d74b5ec35f906758f2823cb0336
```

The transfer uses **11 numbered ZIP parts**, ten of 64 MiB and a final 28,958,694-byte part, plus eight instruction/manifest/checksum files. Whole-file and 400 MiB transport attempts exceeded connector limits before creating remote files; the final 64 MiB parts all succeeded. The final folder contains exactly the 19 intended files.

## Continue on the laptop

1. Preserve the laptop checkout, uncommitted work and `.env`. Update `roi-branch` using a normal fast-forward only when local changes permit. The payload binds implementation commit `477c6d4c2343d0ddc7c00e31e33f83b131774e38`; later documentation commits are compatible.
2. Download **all 19 files** from the new Drive folder into one local folder. Read [START-HERE.md](https://drive.google.com/file/d/1Ihw2nzPjT84pM5ZlGEJ3w-b4A1ilPuiL/view?usp=drivesdk); it contains the commands and a continuation prompt for laptop Codex.
3. Run `JOIN.py` to verify all eleven parts and assemble the ZIP. Use `RESTORE.py` in verification-only mode first, then use its explicit `--restore` option after the checks pass. Both helpers use Python 3.10+ standard libraries. Content-addressed objects must be restored through the helper to retain the original checkpoint paths.
4. Existing identical files are skipped. Conflicts stop restoration before writes. Installed environments and `.env` are excluded; retain the laptop's existing configuration and environments. Preserve frozen absolute-path manifests and prepare any required laptop relocation separately.
5. Resume the same **Gate 3 additional-dataset readiness/admission task**. Read only aggregate status/manifests from the isolated test package; its private text/labels remain outside development inspection.

The development package still has **244 drafts / 179 candidates / 65 holds**, incomplete coverage, and one tokenizer alignment failure. Isolated curation still has **56 prospective records, zero admitted independent test records and no seal**. This backup does not close dataset readiness, admit records, change model roles or authorize another test run. The original 400 samples / 138 articles / 40 contextual pairs and historical evidence gaps remain preserved. See the [readiness report](../flood-ner-additional-dataset-20261016/README.md).

## Verification and limits

Every ZIP object passed content-hash and CRC verification. The actual restore helper's desktop **verification-only** run found 3,863 identical existing files, zero missing files and zero conflicts; it wrote no restored files. Eight constructed restore unit tests and three constructed join checks passed, covering exact bytes/Unicode, identical-file skipping, changed data, conflicts, duplicate memberships, invalid paths and configuration exclusion. A real laptop restoration has not yet run.

The desktop `.env` digest remains unchanged; no source checkpoint, installed environment, dependency, inference, training or deployment was changed. Environment/cache/tool and credential exclusions are recorded in the private manifest (27 excluded entries). The v3 archive supplements older Drive backups and preserves their files. Backup construction logs, readback receipts and source manifests remain in the ignored `desktop-to-laptop-backup-20261016-v3` checkpoint. This public report contains metadata only.
