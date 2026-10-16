# Desktop CLI repaired and corpus tokenizer qualified

> **Last Updated:** October 16, 2026, 4:27 PM (Asia/Manila) by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The desktop tokenizer gate passes.** The backend CLI was restored to the existing repository pins, and one separately recorded qualification attempt completed successfully. The selected candidate has zero alignment errors over the admitted **400 samples / 138 articles / 40 contextual pairs / 1,465 location spans**, all **56 constructed controls** pass, and serialization/reload is verified. The evaluation contract is now frozen with the qualified tokenizer binding. No training-format export, NER prediction evaluation, training or deployment occurred.

## CLI repair and smoke checks

Only two of the existing backend CLI environment's 109 installed packages changed:

| Package | Before | After, matching backend/requirements.txt |
|---|---|---|
| NumPy | 2.5.1 | 1.26.4 |
| SciPy | 1.18.0 | 1.14.1 |

Read-only resolution proposed only these replacements. Windows CPython 3.12 binary wheels were downloaded from PyPI, hashed and checked against PyPI distribution metadata, then installed offline with required hashes and dependency installation disabled. [Wheel identities](wheel-manifest.json) and private installation logs preserve the exact provenance. spaCy **3.7.5**, Thinc **8.2.4**, all other installed packages and the repository requirements file remain unchanged.

Verification passed: `pip check`; NumPy/SciPy/Thinc/spaCy imports; a constructed Unicode passage preserving text, offsets and tokenizer serialization/reload; a one-variable constructed SciPy MILP smoke check; and offline `training.flood_ner --help` startup. No test framework was installed. The historical **880 passed / one skipped** regression result was not rerun or claimed as current.

## Actual corpus qualification

Fresh ignored relocation: `backend/training/flood_ner/artifacts/desktop-relocation-20261016-162313`. Its generated `QUALIFY.ps1` ran once with exit code **0**, using the existing backend CLI and unchanged Python 3.11.17 research interpreter. The isolated worker explicitly used CPU, loaded vocabulary/tokenizers only, and ran no NER pipeline or model predictions. Candidate SHA-256 remains `3f666f61346b7196d931ab9781a3d83f41d688e24b298e8e494b3d92c384a588`.

| Tokenizer | Corpus location alignment errors | Contextual location alignment errors | Constructed alignment errors | Failed constructed controls, of 56 |
|---|---:|---:|---:|---:|
| Selected candidate | 0 | 0 | 0 | 0 |
| Frozen corpus-v3 | 0 | 0 | 14 | 6 |
| Original model native | 1 | 0 | 22 | 14 |

All three tokenizer outputs reload reproducibly. The native corpus gap and its three TIME boundary diagnostics remain in the [comparison](comparison.json); they were not patched. The selected candidate also has zero contextual boundary diagnostics. These measurements establish token boundary compatibility with the saved references, not NER accuracy or independent annotation correctness.

The worker emitted a non-fatal CuPy warning that CUDA_PATH could not be detected. This CPU tokenizer run passed without changing CUDA configuration or repeating GPU qualification; it makes no new GPU workload claim.

[Qualification result](qualification.json), [frozen evaluation contract](evaluation-contract.json) and [verification](verification.json) are metadata only. Full request text, token outputs, serialization files, worker logs, wheel files and package inventories remain under ignored artifacts. The previous failed desktop relocation and restoration checkpoints are preserved unchanged. The original prepared manifests remain historical preparation records; the separate qualification package records the actual pass.

## Acceptance and preservation

Counts reconcile to **400 unique samples from 138 articles**, **40 linked contextual pairs**, **1,465 spans**, **200 English / 200 Taglish**, and **280 training / 60 validation / 60 testing**. The framework-backed qualifier validates the frozen corpus/context, admission bindings, ledger memberships, evidence, controls and tokenizer outputs; post-run hashes revalidate its inputs.

All **10,458 pre-existing artifact files** match their before-state SHA-256 hashes. All **23 model files** match the pinned inventory. The **22,759 research-environment files** retain their sizes/modification times, with no additional non-bytecode files detected. Environment comparison is file metadata; model and checkpoint checks use hashes. Auxiliary download caches and downloaded Python/tool runtimes were excluded from preservation traversal and were not targeted by the repair. Original source text, annotations, contextual pairs, partitions, decision forms, source-use flags and `.env` remain unchanged.

Historical evidence limitations remain explicit: the laptop's three-reference classification is preserved; the checklist manifest and delegation record match on this desktop, while the historical IPOPHL reference still has different bytes. No formal predecessor reconciliation, new source-use conclusion, publisher permission or independent gold-label claim is made. Eleven negative fixtures and ten copied-manifest aliases retain their separate historical classification.

## Next task

Prepare a separately versioned training-format export using the qualified candidate and frozen 280/60/60 partitions. Then follow the frozen baseline/training protocol as a separate task, preserving development-only selection and the held-out test policy. The native baseline remains unchanged. Six paper-excerpt/dataset-distribution outcomes and six production/model-distribution outcomes retain their existing pending/deferred status.

No application source, API, schema, repository dependency pin, Windows policy, model weight or GPU environment changed. No export, training, model prediction evaluation, deployment, external correspondence, commit or push occurred. [Report hashes](metadata_hash_manifest.json) bind this metadata package.
