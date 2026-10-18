# Regularization v21 publication and private backup

> **Last Updated:** October 19, 2026, 01:39 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The completed screening results, internal execution/scoring tools and verified private backup accompany this roi-branch publication.** The user requested the repository/Drive updates. Corrected v19 control remains retained, seed 0 primary: candidate overall validation F1 69.7143% versus control 71.6049%; ROAD/LOCAL_AREA improve, but the overall gate fails, so seeds 1/2 were not run. [Execution results](../flood-ner-regularization-v21-execution-20261019/README.md) · [Publication evidence](verification.json).

## Verified Drive backup

The new [owner-only screening-results folder](https://drive.google.com/drive/folders/14A4kgWRH0LNay8My9vCutIQp_ro-ezTl) contains **nine files**: five numbered ZIP parts, backup manifest, transport manifest, SHA256SUMS and START-HERE. Parent, new folder and all nine children pass **eleven owner-only permission checks**. Every uploaded file was fetched through authenticated access; complete byte count/SHA-256 matches the local original. Exact nine-file membership verifies. Original handoff and earlier backups remain unchanged; no sharing settings changed.

Reconstructed archive: **70,309,880 bytes**, SHA-256 `82f90757e3902fd2e3bf53ae68d96784d2cb55192a70dd48ca23d8910ed23a42`. Exactly **146 members** pass byte/hash verification. The first four parts are 16 MiB and the final part contains the remaining bytes. Backup-manifest SHA-256: `9f11c0dbfede6e520d53c99949d7182b60088125bbb6ad9182ee9098cd6ac7f6`.

Contents include the candidate selected checkpoint and selection metadata, resolved configs, requests/outcomes, raw logs, private train/dev predictions/metrics/gaps, frozen control-retention decision, exact original input transfer, source/test snapshots and preflight/regression evidence. Redundant model-best/model-last weights remain on desktop. Existing retained control weights remain in the [earlier v19 backup](https://drive.google.com/drive/folders/1XYPTFZ9Ooi2D6_e1jtZT-jdzl06ZEYs4).

No `.env`, credential, environment, pinned base pretrained weights or research-holdout content is uploaded. Follow START-HERE: authenticate parts, concatenate exclusively into an absent archive path, verify the reconstructed archive and exact safe membership, then extract only into a new destination. Do not automatically execute archived code, overwrite existing packages or reuse completed run destinations. Configs retain desktop paths and need separate reviewed relocation before use elsewhere. This archival publication authorizes no retraining, tuning, holdout evaluation or deployment.

## Repository publication checks

The new execution helpers/tests and aggregate reports are public; weights, private data/predictions/logs and all ignored artifacts stay outside Git. The existing tracked `.env` modification is preserved and excluded. One older untracked test, `test_flood_ner_corrected_holdout.py`, targets the evaluator API superseded by the qualified laptop implementation; its original bytes remain locally and privately backed up, and it is not published. The qualified evaluator tests already in the branch remain unchanged.

All 291 execution regression tests remain bound to unchanged source bytes. Six saved-development-language tests pass freshly, and the checkout regression passes **20 source/test comparisons** under core.autocrlf true/false in temporary repositories. Two newly published test paths receive `-text` rules so their frozen hashes survive Windows checkouts. The regression's old evaluation-contract expectation now reflects the already-published literal-byte rule; four execution/test paths are added to coverage. Original attribute/test bytes are privately preserved. No frozen training helper, manifest, recipe, tokenizer, reference or model is modified.

A staged-checkout review also inspected 81 source/test files: 54 reproduce desktop bytes exactly; 27 pre-existing files differ only in CRLF/LF and have identical Python ASTs. None of those 27 is a v21 package-bound implementation/test or a new execution/test source. Their original desktop bytes remain in the authenticated private source snapshot; no broad source normalization or manifest rebinding is performed.

New imports use the standard library and already-declared isolated spaCy/Torch resources. No dependency, SQLAlchemy model, Alembic migration, public API or frontend change is introduced; database migration execution is not applicable. Staged public blobs and exact manifest-bound implementations are checked before a normal Conventional Commit/push to roi-branch. No force push is authorized. The resulting Git receipt is retained privately; this report is part of that publication commit.

The earlier training preservation check verified all 8,047 protected files. Publication intentionally updates Git attributes and the checkout regression, with their originals backed up; package/model/run/backup and `.env` preservation is checked again. Limited-provenance AI-assisted silver research limitations remain. No further training, inference or holdout evaluation occurs during publication.
