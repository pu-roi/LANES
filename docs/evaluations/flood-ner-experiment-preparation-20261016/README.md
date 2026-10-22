# LANES baseline/training preparation — October 16, 2026

> **Last Updated:** October 16, 2026, 5:18 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

Preparation passes. The next task is the first primary seed 0 training run under the frozen recipe. This checkpoint performs no optimizer updates or model corpus prediction evaluation.

The private checkpoint is backend/training/flood_ner/artifacts/experiment-preparation-20261016-v2. It binds the passing qualified export and tokenizer, scoped admission, evaluation contract, pinned model, rules implementation/assets, registry callbacks and three generated configurations. [Verification](verification.json), [manifest](experiment-manifest.json), [GPU initialization](initialization.json) and [rules mapping](rules-baseline.json) contain metadata only.

## Verified readiness

- The admitted inputs remain 400 samples / 138 articles / 40 contextual pairs / 1,465 spans / 48 negatives, with 200 English / 200 Taglish and 280/60/60 partitions. All admission/qualification/export bindings revalidate; no contextual pairs become training samples.
- All seeds 0/1/2 initialize with the six location labels and exact candidate tokenizer bytes. Each has 46 GPU parameter arrays and two CPU upper-classifier arrays, consistent with the pinned architecture. Python 3.11.17, spaCy 3.7.5 and the RTX 3060 Ti are reused.
- The NER encoder is copied from the unchanged pinned model into a fresh six-class head; all three report the same transferred-encoder hash. No initialized or trained weights are saved. No model predictions, optimizer updates or application database connections occur.
- Twenty-one focused standard-library unittest methods pass: nine preparation tests and twelve export regressions. These cover direct label/offset mapping, unsupported/Unicode cases, duplicates/overlaps, source/assets hashes, seed/budget/test exclusion, label registration, intentional CPU classifier/device rejection and checkpoint ties/overwrite refusal. The historical complete suite is not rerun.
- All 10,531 pre-existing artifact hashes and 23 pinned model files verify. The 22,759 non-bytecode research-environment files retain size/mtime with no additions; this is metadata preservation, not complete environment content hashing. All 109 CLI package versions, requirements and .env are unchanged.

## Frozen experiment choices

| Setting | Value |
|---|---|
| Primary / robustness seeds | 0 / 1, 2 |
| Pipeline | NER only; fresh six-class head with pinned pretrained NER encoder/static vocabulary |
| Batch / dropout / Adam learning rate | 8 / 0.1 / 0.001 |
| Epoch / step settings | max_epochs 30; max_steps 1000 |
| Development evaluation / patience | eval_frequency 35; patience 175 |
| Selection | Strict six-class entity micro F1 on development; earlier step wins ties |
| Authoritative model | Future seed-directory/selected-checkpoint/model |

This is one initial untuned recipe, not a performance claim. The training configs include train.spacy and dev.spacy only. The initializer reads training examples, loads configuration references for development, and never reads test.spacy. Preservation hashing of the held-out file is not prediction evaluation.

The built-in spaCy model-best overwrites equal development scores. The registered selector preserves the earlier-step contract in a separate selected checkpoint. Its behavior is tested on constructed scores; no actual training checkpoint exists yet. The future academic-training-20261016-v1 directory remains absent. The later trainer must load experiment_registry.py and retain the qualified Windows DLL/runtime setup.

## Baselines and limitations

The rules baseline freezes the existing sentence splitter/place-mention component and direct emitted-type mapping: street → ROAD, landmark → LANDMARK, barangay → BARANGAY, city → CITY, province → PROVINCE. LOCAL_AREA is unavailable; numbered locality emissions remain their legacy LANDMARK type. No reference-driven repairs or relabeling are permitted. Original zero-based/end-exclusive Unicode offsets are checked against raw names; invalid/unknown emissions are diagnostics, identical spans deduplicate, overlaps/conflicting types remain. Four constructed passages produce six valid mentions and zero diagnostics with database connections blocked. No corpus baseline scoring occurs.

The original pretrained model remains an unchanged, separately scored native coarse LOC baseline. It cannot be presented as a six-class model. Later comparisons must use matched frozen partitions and development-only choices; final test predictions wait until experimental choices freeze.

The references remain same-AI silver labels, not independently verified gold accuracy. Independent language/label review, broader address cases and the historical acquisition/source-use limitations remain explicit. The formal detailed desktop predecessor remains unreconciled; two historical audit references now match current desktop bytes, while the historical IPOPHL reference hash differs. Eleven invalid-test references and ten copied-manifest aliases retain their separate historical classifications. Six paper-excerpt/dataset-distribution outcomes and six production/model-distribution outcomes stay pending for those uses; preparation supplies no new permission.

## Preserved failure and scope

Preparation v1 is retained with its logs: the helper incorrectly required every parameter on GPU and stopped after seed 0 initialization. Installed spaCy source confirms its upper classifier is intentionally CPU. The corrected helper checks devices by component; a separate v2 passes all seeds without package or architecture changes.

No new articles/passages, DocBins, annotations, source-use decisions, corpus evaluation, optimizer updates, training, deployment, external correspondence, commit or push occur. Metadata/config files and process-local CUDA caches stay inside new ignored checkpoints; no initialized weights are saved. Existing desktop edits are preserved. [Task plan](../../task_plan.md).
