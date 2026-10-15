# Laptop research artifacts restored to the RTX desktop

> **Last Updated:** October 15, 2026, 5:10 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

Restored **946 missing files**, skipped **17 existing identical files**, and found **zero conflicting hashes**. All 963 planned files verify after restoration. The checkout is `E:/Files/Documents/GitHub/LANES` on `roi-branch`. The 30 pre-existing uncommitted files (including backend/.env) and 71 existing GPU checkpoint files matched their pre-restore fingerprints. This report and three status documents were added/updated afterward without replacing earlier desktop work. [Structured results](summary.json).

## Verified archives

Windows' actual Downloads folder is `E:/Files/Downloads`. The three archives initially appeared in an expanded Drive download directory. After that directory disappeared, the same byte-identical inner archives were recovered from the remaining `400-sample-study-corrected-20261015-v1-20261015T082932Z-1-001.zip` wrapper. Every inner archive matched the user-provided hash before restoration. Copies and detailed receipts remain in ignored `backend/training/flood_ner/artifacts/desktop-restore-20261015-v1/`.

| Archive | Verified SHA-256 |
|---|---|
| LANES-400-sample-private-study-corrected-20261015-v1.zip | `39d71d1f660a12887c4007246530253be0895ced32649b0f2e5c75bcbdc7a910` |
| academic-use-decision-proposals-v1.zip | `ef57e597a885b5441f2531c54ab7e2fea6e89b32e7a46e2b67ae1cc52ec0fc38` |
| evidence-support-v1.zip | `cab3b693eac8949a376bc08b1c713139d4c0ffe057d0f2da0ea9b27c88df7f25` |

Checked ZIP CRCs and paths, both study/proposal manifests, all support-index entries and the study relocation index. Restored the organized study package at `artifacts/400-sample-study-package-corrected-20261015-v1/`, then restored original raw-capture and review paths through the relocation index. Reconstructed the canonical `artifacts/annotation-correction-20261015-v1/cohort-v2/` and `contextual-v3/` directories from exact manifest-bound bytes. The proposal is at `artifacts/academic-decision-proposal-20261015-v1/`; support paths were rooted at the repository root. The byte-identical original study ZIP was also restored at its proposal-bound storage path. One additional historical storage manifest in the outer download exactly matched a hash already bound by the verified evidence. No extra backend directory was created.

## Validation

| Check | Result |
|---|---|
| Unique location records / articles | 400 / 139 |
| Location entity spans | 1,497 |
| Contextual-v3 pairs | 40, with 20 English / 20 Taglish |
| Location languages | 200 English / 200 Taglish |
| Partitions | 280 train / 60 validation (`dev`) / 60 test |
| Frozen annotations, spans and group checks | Passed |
| Existing frozen corpus tokenizer | lanes.xx.address-v3; bytes/hash unchanged |
| Context pairing and category checks | Passed |
| Article capture/publication evidence | Passed for all 139 articles |
| Current review evidence and proposal validation | Passed; all nine required proposal bindings resolve |
| Existing recommendations / actual decisions | 70 recommend / 69 held; zero actual decisions |
| Admission / export | All 400 remain research_only / unknown reuse; zero admission/export |
| Existing GPU environment | Same Python 3.11.17, spaCy 3.7.5 and all 73 package versions |

Reused the existing desktop research interpreter for the repository's annotation, contextual, capture, review and proposal validators. Used a blank pipeline with the frozen corpus tokenizer to check saved annotation alignment; no pretrained news inference, export, training or deployment ran. The minimal Windows research environment lacks IANA timezone data, so verification used the already-bundled tzdata through a process-local search path; no package or GPU environment file was changed. The private validation report records the exact timezone data hash.

Every newly restored private file is ignored by Git. Existing source-use records, decisions, annotations, partitions and tokenizer/model checkpoints were preserved byte for byte. No Git reset, pull, commit, push, database or deployment operation occurred.

## Historical audit-reference limits

The current validators and all required current bindings pass. Three older audit files referenced by historical bookkeeping are absent from the supplied archives, the outer download metadata and the existing checkout:

- `backend/training/flood_ner/artifacts/adviser-guidance-20261015-v1/manifest.json` — expected SHA-256 `d9c8cc984afffefdb13fb16b801a5257a4e227e0f8873a925026ea1865219b6f`.
- `backend/training/flood_ner/artifacts/academic-use-review-20261015-v1/academic_review.json` — expected SHA-256 `d4f4406295563d0da7acd8ae562dd3ebf136e56082a6c83866ffc6a9ccce603d`.
- `backend/training/flood_ner/artifacts/academic-use-review-20261015-v1/manifest.json` — expected SHA-256 `5b8e3a752d248a1f14ce3857290272957db6ea75c735c9724ab6b07624985f09`.

These files were not fabricated and their references were not rewritten. They are separate from the nine required proposal bindings and the policy/capture evidence verified above. Recover their exact bytes from the laptop if complete historical audit replay is later needed. The laptop Python environment and additional historical model/tokenizer runs were not in these backups; the existing qualified desktop environment and model remain the active checkpoint.

## Exact next task from task_plan.md

Finalize the case-specific supported research-use basis and explicit project decision using existing evidence, considering statutory-exception and contractual/origin questions separately. Publisher replies are optional evidence, not a universal prerequisite. Apply supported admission separately, then qualify news-cohort tokenization, export and train using the frozen partitions. Desktop inventory and constructed GPU environment qualification are complete; preserve the isolated environment and measured recipe; no news-model processing while admission is unresolved. Deployed inference/defense demonstration scope must also be assessed separately from the existing private-use review. Keep the 400-sample requirements and release checks; the 157 recommended passages are not a replacement cohort. [@roicambe](https://github.com/roicambe) (Roi Cambe)

Restoration and validation do not adopt an AI recommendation, resolve a source-use hold or grant training admission. Source-use/project decisions and separate admission remain next; the 157 recommended passages do not replace the required 400-sample cohort.
