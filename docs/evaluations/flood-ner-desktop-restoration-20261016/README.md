# Desktop corpus restored; tokenizer qualification blocked

> **Last Updated:** October 16, 2026, 4:11 PM (Asia/Manila) by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The existing desktop checkout fast-forwarded from `b84c464` to `4736cea` on `roi-branch`. The private v2 handoff was downloaded through authenticated Drive access and verified against **28,476,420 bytes** and SHA-256 `afe11aa15398d9b88e7ef268c75f7d51c79107206a60f29ac4313264f4dba65f`. Verification preceded restoration: **697 missing files restored, 1,060 identical files skipped, zero conflicts**. A post-restore check verifies all **1,757 payload files** against the archive. Existing files were not overwritten.

## Restored inputs and preservation

| Check | Actual result |
|---|---|
| Admitted location records / articles | 400 unique records / 138 articles |
| Contextual pairs | 40, linked within the 400 records |
| Location spans / negative passages | 1,465 / 48 |
| English / Taglish | 200 / 200 |
| Training / validation / testing | 280 / 60 / 60 |
| Current admission package, ledger and selected article references | Hash bindings and 400 unique ledger memberships verified |
| Research-only versus admitted v5 derivative | Differences limited to the three recorded source admission/reuse fields |
| Existing research artifacts | All 9,744 before-state file hashes unchanged |
| Pinned model | All 23 files verified against the laptop inventory and existing desktop manifest |
| Research environment | 22,759 file sizes/modification times unchanged; no additional files detected, excluding Python bytecode caches |
| Local `.env` | Before/after SHA-256 identical; contents never included in this report |

The environment comparison is file metadata, not a hash of every installed package. Download caches and auxiliary downloaded Python/tool runtimes were excluded from preservation traversal; no task command changed them. All preserved model files and research checkpoint files were hashed. Original annotations, partitions, historical forms and source-use flags remain unchanged. The separate admitted derivative retains its existing statuses.

The new ignored relocation checkpoint is `backend/training/flood_ner/artifacts/desktop-relocation-20261016-160823`. It binds the existing Python 3.11.17 research environment, the existing backend CLI environment and pinned model. Candidate tokenizer bytes remain SHA-256 `3f666f61346b7196d931ab9781a3d83f41d688e24b298e8e494b3d92c384a588`. Relocation is preparation only.

## Single qualification attempt

The generated `QUALIFY.ps1` was run once. It exited **1** during the outer backend CLI's spaCy import, before corpus validation or the isolated tokenizer worker started:

```text
ValueError: numpy.dtype size changed, may indicate binary incompatibility.
Expected 96 from C header, got 88 from PyObject
```

The traceback reaches `thinc.backends.numpy_ops` in `backend/venv`. Installed CLI metadata reports NumPy **2.5.1**, Thinc **8.2.4**, spaCy **3.7.5** and SciPy **1.18.0**. This establishes an observed runtime ABI incompatibility; the package installation history and a compatible repair have not been investigated in this task. Metadata-only preflight did not test extension imports. This failure is distinct from the laptop's historical Windows Application Control 4551 failure.

No worker, tokenization, alignment comparison, constructed-control check, tokenizer reload result or `qualification` output directory was produced. Standard-library hash/record/pairing/membership checks passed; framework-backed corpus validation did not execute. No qualification pass is claimed. No retry, dependency repair, security-policy change, tokenizer-rule change or GPU setup was performed. The historical **880 passed / one skipped** software result was not rerun.

Full invocation output, stderr, return code, before-state inventory and verification are retained privately under `backend/training/flood_ner/artifacts/desktop-execution-20261016-run-01`. [Metadata verification](verification.json) binds the inputs and execution/relocation output hashes; [report hashes](metadata_hash_manifest.json) bind this report.

## Historical evidence limitations

Preserve the laptop's three-reference historical classification and unreconciled desktop decision lineage. On this desktop, the recorded checklist manifest and delegation record exist and match their expected hashes; the IPOPHL evidence reference still differs. These observations are recorded individually in the verification, without rewriting historical records or claiming formal predecessor reconciliation. The eleven negative fixtures and ten copied-manifest aliases remain separately classified in the [handoff report](../flood-ner-desktop-handoff-20261016/reference-classification.json).

## Next task

Resolve the existing backend CLI's NumPy/Thinc compatibility in a separate task, preserving the qualified GPU research environment. Record any approved repair and a separate qualification attempt. The desktop gate remains open; training-format export follows only a successful qualification. This task performs no export, training, model predictions, deployment, source-use reassessment, API/schema/dependency change, external correspondence, commit or push.
