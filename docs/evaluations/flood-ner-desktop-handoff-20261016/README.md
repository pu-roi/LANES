# Laptop-to-desktop NER handoff — October 16, 2026

Updated: October 16, 2026, 12:28 PM (Asia/Manila). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Laptop handoff prepared and restoration verified:** The private v2 ZIP contains **400 admitted locations / 40 contexts**, 138 selected articles and all **407 original capture-evidence files**. Its **1,757 payload files** restore with identical hashes; a second restore skips every identical file. All 400/40 qualification inputs and selected publication evidence revalidate offline. **880 software tests passed; one skipped** (40 new handoff tests). The 23 recorded desktop/laptop model identities match; weights and environments are excluded. Three historical evidence gaps remain unreconciled; eleven invalid-test references and ten copied-manifest path aliases are separately classified. Drive delivery remains pending because this chat still sees the school account and cannot access the owner-only personal folder. Desktop restoration and tokenizer qualification have not run.

The private archive is `backend/training/flood_ner/artifacts/desktop-handoff-20261016-v2/LANES-NER-desktop-handoff-20261016-v2.zip`. Its size is **28,476,420 bytes** and SHA-256 is **afe11aa15398d9b88e7ef268c75f7d51c79107206a60f29ac4313264f4dba65f**. Full text and the archive remain ignored by Git. The new helper, tests, documentation and metadata are the Git deliverables. [Desktop steps](../../guides/ner-desktop-handoff-20261016.md).

| Outcome | Measured result |
|---|---|
| Laptop package and temporary restoration | Pass; 1,757 files, zero restored capture errors |
| Admission and frozen identity | 400 locations / 40 pairs, 200/200 languages, 280/60/60 splits preserved |
| Existing model identity | 23 matching path/size/SHA entries; no weights included |
| Software tests | 880 passed / one skipped in 94.16 seconds; 40 new handoff tests |
| Drive delivery | Pending: current connector is the school account; restricted personal-folder read returns 404 |
| Desktop restoration | Not run |
| Corpus-tokenizer qualification | Not run on desktop; laptop import remains blocked by error 4551 |
| Export / training | Zero / zero |

## Restoration and safety evidence

The standard-library helper rejects traversal, duplicate/colliding ZIP entries, symlinks, undeclared files, checksum failures, excluded environments/weights and conflicting destination bytes. Verification is the default. Tests cover exact Unicode source offsets, incorrect counts, identical-file skipping, missing prerequisites and relocation binding. The metadata probe does not import spaCy or torch. No dependency or database/schema change was introduced.

The first local v1 archive is preserved as an intermediate checkpoint. Its qualification inputs validated, but source-manifest `capture_path`, `raw_path`, `text_path` and publication-evidence references were not all followed. The v2 builder explicitly includes all 407 selected capture-evidence paths and re-runs `verify_capture_files` both before packaging and after restoration, with zero errors. No prior artifact was overwritten.

## Historical reference limitations

The raw closure scanner reports 24 diagnostics: **three genuine historical evidence gaps**, eleven deliberate invalid-test fixture references and ten copied-manifest relative aliases. [Classification](reference-classification.json). The three gaps are the unavailable original decision-checklist manifest, unavailable detailed delegation record and a divergent older IPOPHL evidence-file hash. They are not reconstructed. The preserved source-use index continues to distinguish 69 explicit, 68 desktop-reported and one prior local adoption.

Current offline qualification bindings validate after restoration. This does not independently verify the missing desktop predecessor or grant publisher permission, broader reuse or a dataset license. The private owner-only academic scope and all twelve nonacademic outcomes are unchanged.

## Delivery and next gate

Git publication is authorized and recorded by a separate publication receipt after push. The existing personal research folder was not modified because the current connector cannot verify owner-only access. The user's reported reconnection is preserved as context, not treated as authenticated access. No substitute-account upload or sharing change occurred.

Once private delivery is verified, continue on the existing desktop checkout using the guide. Discover its actual environment/model locations, verify the ZIP without writing, restore missing evidence, create new relocation manifests and then run the separate tokenizer-only qualification. Training-format export stays behind that qualification gate.

[Artifact checks](verification.json) · [Restoration](restoration-verification.json) · [Software evidence](software-verification.json)
