# Qualified location training-format export verified

> **Last Updated:** October 16, 2026, 4:49 PM (Asia/Manila) by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The export gate is complete.** The new opt-in offline command exports the admitted location cohort with the exact calamanCy tokenizer that passed corpus qualification. Both the primary export and a separate replay pass; their three DocBins, tokenizer bytes and provenance metadata are byte-identical. No NER prediction evaluation or training occurred.

## Tooling and boundaries

export-qualified-corpus --python RESEARCH_PYTHON --qualification PASSING_QUALIFICATION_DIRECTORY --output NEW_IGNORED_DIRECTORY reuses the repaired CLI environment and isolated Python 3.11.17/spaCy 3.7.5 research environment. The legacy export command, its defaults and exporter source are unchanged.

Before writing training data, the command validates the qualification package and its implementations, frozen evaluation contract, current admission package/ledger and selected evidence, model/vocabulary, candidate bytes, corpus/context memberships, accepted silver annotation profile and split/group policy. It reconstructs the saved qualification comparison rather than trusting a passed flag alone. Research-only or stale/mismatched inputs and existing/unignored destinations are refused.

The worker loads the pinned vocabulary (including its vectors) and qualified tokenizer only, constructs six-class location DocBins, verifies strict spans, then reloads every serialized document and checks original text, tokens, entity offsets/labels and record IDs. Post-run input checks precede the successful manifest. Failures retain diagnostics without creating a success manifest. No NER/tok2vec component weights or model pipeline are loaded, and no legacy tokenizer fallback is used.

## Actual artifacts

- Primary ignored checkpoint: backend/training/flood_ner/artifacts/qualified-export-20261016-v1.
- Replay: backend/training/flood_ner/artifacts/qualified-export-20261016-replay-v1.
- Private execution inventory, test output and verification: backend/training/flood_ner/artifacts/qualified-export-execution-20261016-v1.
- Bound qualification: backend/training/flood_ner/artifacts/desktop-relocation-20261016-162313/qualification.

Each export contains train.spacy, dev.spacy, test.spacy, unchanged candidate tokenizer.bin, metadata-only provenance.json, a hash-bound manifest and private request/worker diagnostics. Tokenizer serialization excludes vocabulary: reuse the bound model/vocabulary rather than reconstructing language defaults. The 40 contextual pairs remain bound references; they are not additional training documents.

| Check | Actual result per export |
|---|---|
| Unique location samples / articles | 400 / 138 |
| Training / validation / testing | 280 / 60 / 60 |
| English / Taglish | 200 / 200 |
| Location spans / negative passages | 1,465 / 48 |
| Contextual pairs referenced / added as samples | 40 / 0 |
| Model predictions / training | None / none |

Reloaded span counts: CITY **478**, PROVINCE **274**, ROAD **346**, LANDMARK **102**, LOCAL_AREA **88**, BARANGAY **177**. These describe the preserved AI silver annotations, not model accuracy.

| Deterministic file | Bytes | SHA-256 |
|---|---:|---|
| train.spacy | 99,320 | b7db4a8741b8dc2630918fd060a3423d83ca5da2b984f90167a3ef047d334ee7 |
| dev.spacy | 33,375 | e186a302113a1cc2fc1a4ed823ee57d76fb88cc791ca446db9f625e3642b34a8 |
| test.spacy | 27,531 | 173646e84358bf4770e5c852981b405edd89902b262116c6751a5540b29e6ead |
| tokenizer.bin | 38,317 | 3f666f61346b7196d931ab9781a3d83f41d688e24b298e8e494b3d92c384a588 |
| provenance.json | 446,427 | c5a4ad509ab460ffa4d84d4349e98247d9aa7bc18ee35139f2695da8f6c8eacf |

Request output paths differ between checkpoints, so diagnostic/package manifest bytes are not claimed identical. The five files above are identical.

## Verification and preservation

**12 focused standard-library unittest methods pass**, including policy/admission refusals, missing/changed qualification members, changed evaluation protocol, moved/duplicate memberships, invalid offsets/labels, Unicode and negative-record serialization, deterministic replay, overwrite refusal and legacy CLI/export behavior. Tests need no private corpus or new dependency. The historical 880-passed/one-skipped suite was not rerun or added to the current count.

Independent disk reload checks all **six DocBins / 800 document reads** against canonical annotations and the saved qualification's token signatures. All texts, IDs, partitions, tokens and strict entity offsets/labels match; every frozen sample appears once per checkpoint. [Disk checks](disk-reload-verification.json).

All **10,500 prior artifact files** remain SHA-256 identical, including admission, original annotations, contextual pairs, partitions, source-use flags and earlier qualification/failure records. All **23 model files** verify. All **22,759 research-environment files** retain size/modification time with no extra non-bytecode files detected. Environment comparison uses file metadata; model/checkpoint preservation uses hashes. Auxiliary downloaded caches/Python/tool runtimes were excluded and not targeted. CLI package versions, requirements, legacy exporter source and .env are unchanged.

The worker's non-fatal CuPy CUDA_PATH warning remains in private logs. Serialization explicitly uses CPU; no CUDA setting change or new GPU qualification is claimed.

The output/replay hold 800 DocBin passage representations and 800 request passage-text fields for the same 400 samples, not 800 admitted examples. No full source-body field is copied into requests or provenance metadata. Ten selected passages equal their entire original source body, producing forty whole-body passage representations across the two requests and two DocBin sets; this is not new collection or broader authorization. Full passage/token artifacts remain ignored and private.

Historical evidence limitations remain explicit: the three-reference laptop classification and unreconciled decision predecessor are not rewritten. Two historical references match on this desktop; the IPOPHL reference still differs. Negative fixtures and copied-manifest aliases retain their separate classifications. No independent human/gold review, new source-use conclusion or publisher permission is inferred.

[Verification](verification.json) binds current inputs, code, output hashes, replay and preservation checks. [Export manifest](export-manifest.json) contains metadata only. [Report hashes](metadata_hash_manifest.json) bind this metadata package.

## Exact next task

Prepare the baseline/training experiment configurations against this export and the frozen evaluation contract. Freeze the existing rules extractor's six-class/character-offset mapping before comparisons; preserve the separate pretrained coarse LOC comparison, development-only model selection, recorded seeds and held-out test policy. Training/evaluation execution remains subsequent work. Six paper-excerpt/dataset-distribution outcomes and six production/model-distribution outcomes retain their existing pending/deferred status.

No production API, database schema, dependency version, Windows policy, model weights or GPU environment changed. No model predictions, training, deployment, external correspondence, commit or push occurred.
