# NER dataset qualification: first completed pass

> **Last Updated:** October 14, 2026, 7:22 PM (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Qualification diagnostics and metadata research delivered; the training-readiness gate remains open.

Used the frozen [400-sample corpus](../flood-ner-corpus-400-20261014/README.md), preserving all source bodies, labels, partitions, the v2 tokenizer and the dedicated 418-file backup bundle. The new offline qualify-cohort command verifies frozen file hashes, saved-tokenizer alignment, all 132 selected capture/publication bindings and immutable source metadata, then reports support and source/model holds without granting admission.

## Measured support and research limits

| Partition | Samples | Source articles | Conservative reporting groups |
|---|---:|---:|---:|
| Train | 280 | 93 | 11 |
| Validation | 60 | 16 | 6 |
| Test | 60 | 23 | 10 |

The equal 200/200 language totals mask a strong publisher/language association. GMA supplies 187 of 200 English passages and RMN supplies 194 of 200 Taglish passages. Assigning each publisher its majority corpus language would match 394/400 recorded language tags (98.5%); **this is a descriptive association, not NER accuracy or an evaluated classifier**. Publisher identities do not replace language adjudication.

Taglish ROAD support is only **17 training / 2 validation / 3 test spans**. Other small holdout slices include English LOCAL_AREA (1 validation / 4 test) and Taglish PROVINCE (3 test). The report flags nine holdout slices with at most five spans; this flag is descriptive, not a new acceptance threshold. The largest article supplies 22 samples; the largest conservative reporting component supplies 112. There are 27 split-dependency components, not 27 verified independent flood incidents. Complete grouping and reference qualification remain pending.

## Tokenizer and serialization safeguards

Broader constructed probes found that frozen v2 cannot align `Purok 1 to 2—baha` at the end of the identifier. The opt-in **lanes.xx.address-v3** candidate adds numeric en/em-dash boundaries while preserving original characters and ordinary 006-A address codes. Fourteen address-boundary probes cover typographic dashes/quotes, apostrophes, nonbreaking whitespace, compound block/lot/phase components, Roman identifiers, leading zeros and suffixes. All 400 actual records also align under the candidate. **The default, frozen dataset and existing exports still use v2; v3 is not promoted or a trained model.**

JSONL serialization now escapes U+0085/U+2028/U+2029 in the representation and reads physical LF-delimited records. Decoding restores the identical source text and offsets. Three regressions cover these separators, including legacy JSONL with literal separators. The frozen corpus contains none of these characters, so its bytes and prior replay remain unchanged. Constructed examples contribute zero samples to the corpus.

## calamanCy metadata qualification

Captured meta.json, config.cfg and README.md at four immutable publisher revisions; no weights were downloaded or packages installed.

| Candidate | Declared spaCy requirement | spaCy 3.7.5 assessment |
|---|---|---|
| Medium / transformer 0.2.0 | >=3.8.3 | Version conflict |
| Medium / transformer 0.1.0 | >=3.5.0,<4.0.0 | Declared version range passes; actual loading still untested |

All four expose LOC/ORG/PER and declare MIT model licensing. They do not natively expose the six LANES place classes. The older models require spacy-transformers >=1.2.5,<1.3.0, which is absent from this environment and is not a declared backend dependency. Metadata compatibility does not establish English/Taglish accuracy, tokenizer alignment, CPU memory/latency, dependency installation success or a selected model. The model-license record does not license this separately gathered news corpus. [Pinned medium 0.1.0 metadata](https://huggingface.co/ljvmiranda921/tl_calamancy_md/blob/51a40433059d8a2c25b98a48eca854f8789a491a/meta.json), [current medium card](https://huggingface.co/ljvmiranda921/tl_calamancy_md), [current transformer card](https://huggingface.co/ljvmiranda921/tl_calamancy_trf).

The source-use inventory binds the current three publishers to five previously captured official policy snapshots and verifies every hash. It records evidence and unresolved assessments, not a legal conclusion or a new permission. All 400 sources remain research-only; **training admission/export-ready count stays zero**. No source is promoted by model metadata, software tests or the user's delegation of AI annotation.

## Verification and files

**455 tests passed, one existing spaCy/Click warning, 49.97 seconds**, retaining the 425-test baseline and adding 30 qualification/tokenizer/serialization checks. Two command executions produce byte-identical reports and candidate tokenizer bytes. Frozen source/partition/tokenizer and backup hashes pass. No operational SQL, API/runtime parser, dependency, model training, Google-document edit, deployment, commit or push changed.

- [qualification.json](qualification.json): measured per-language/label/partition support, confounds and holds.
- [model_register.json](model_register.json): pinned metadata/license/dependency checks and actual qualification limits.
- [source_use_inventory.json](source_use_inventory.json): current publisher counts and captured policy evidence.
- [evaluation_contract_draft.json](evaluation_contract_draft.json): proposed exact-span/coarse-span scoring and untouched test use; not a trained result or a closed evaluation gate.
- [audit.json](audit.json): verification counts and preservation evidence.

The next substantive work is correcting or expanding underrepresented source/label coverage in a separate revision, reviewing incident/language/label and contextual references, resolving source-use assessment and qualifying actual model loading/tokenization/resources. The 400-example checkpoint stays frozen. Model installation, evaluation and training follow those qualifications; the ten-calendar-year collection expansion remains a proposal. [Roadmap](../../plans/lanes-ner-training-plan.md), [tooling](../../../backend/training/flood_ner/README.md).
