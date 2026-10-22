# Successor training publication and private Drive backup

> **Last Updated:** October 18, 2026 by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The user authorized publication to `roi-branch` and an updated private Drive backup.** This publication includes the combined v16 Windows launcher, 75-test verification, the preserved failed first attempt, completed three-seed results and synchronized operator/project records. The repository contains code and aggregate evidence; private training exports, selected models, environments and credentials remain outside Git.

## Verified Drive update

The new owner-only [v17 trained-successor folder](https://drive.google.com/drive/folders/1ZFFNL9Vu-dg5xLyWsSR2wd99_qsGTE_J) contains exactly **11 files**: the combined twelve-file trainer ZIP, checkpoint-backup manifest, seven numbered checkpoint ZIP parts, SHA256SUMS and START-HERE instructions. Every uploaded file was fetched through authenticated access and its full byte count/SHA-256 verified against the local original. Folder and all eleven children have only the existing owner's permission; no sharing settings or old folders were changed.

The checkpoint archive is **208,875,788 bytes**, split into six 32 MiB parts and a final 7,549,196-byte part. Download all parts and follow START-HERE to verify, concatenate and extract into new staging/absent destinations. It contains each seed's selected model and selection metadata, configs, requests/outcomes, training/launcher logs and verification receipts. Redundant `spacy/model-best` and `spacy/model-last` directories remain locally and are excluded from this backup. No environment, base pretrained model, credential or holdout content is uploaded. The trainer ZIP contains the already-authorized train/dev exports.

The saved configs retain original absolute paths; another computer needs separate relocation and the matching qualified runtime/base model before loading. Restoration does not authorize retraining or held-out evaluation. Completed output directories must never be overwritten or reused. Original v15/v16 packages and previous Drive backups remain preserved. [Aggregate backup verification](verification.json).

## Publication checks and results

The current launcher and both affected test sources match the exact hashes bound to the passing **75-test** execution; test-result bytes also match. Newly used `os` is standard-library code; Torch is already declared in the isolated GPU qualification requirements and lock. No production dependency, SQLAlchemy model, Alembic migration, API or frontend change is present, so database migration execution is not applicable.

Security review keeps the tracked machine-local `backend/.env` modification out of this commit and preserves its bytes. Offline datasets/checkpoints and all ignored research artifacts remain excluded. Git stages the authorized public changes, verifies the staged snapshot for unintended secrets/private artifacts, creates a Conventional Commit and pushes normally to `roi-branch`; no force push is authorized. This record precedes the commit/push; its execution receipt is retained privately after completion.

All three selected checkpoints are loadable with six labels. Seed 0 remains primary: development F1 **66.67% / 65.41% / 67.46%** for seeds 0/1/2, mean **66.51%**, sample SD **1.03 percentage points**. All 12,387 protected predecessor files, original packages and `.env` verify unchanged after training. No additional training, holdout evaluation, deployment or claim of 80% F1 is part of publication. [Training evidence](../flood-ner-successor-v16-desktop-training-20261018/README.md).
