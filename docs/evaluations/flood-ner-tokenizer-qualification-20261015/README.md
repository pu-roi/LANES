# Constructed calamanCy tokenizer qualification

> **Last Updated:** October 15, 2026, 9:11 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

Candidate **lanes.tl.calamancy-address-v1** passes the constructed qualification: **48 cases, 24 English/24 Taglish**, zero strict reference-alignment errors and all **56 token-boundary controls** passing. Original model files, datasets, contextual v2 and prior results remain unchanged. **625 tests pass**, retaining the 586-test baseline.

| Tokenizer | Reference-alignment errors across 48 constructed cases |
|---|---:|
| Native calamanCy | 22 |
| Separate candidate | 0 |
| Unchanged lanes.xx.address-v3 | 14 |

The original 24 native predictions reproduce exactly, including their two previously observed gaps. The expanded cases add twenty native alignment failures. The candidate preserves native exceptions and token matching, and extends the serialized infix/prefix/suffix regexes for composite en/em-dash-plus-hyphen separators, leading list hyphens and trailing dateline hyphens. Internal identifiers such as 31-A remain intact. Every original source character and Unicode offset is retained.

Tokenization changes in **13 cases** and coarse NER predictions change in **12 cases**. Native predicts 61 LOC/2 ORG/0 PER; the candidate predicts 68 LOC/1 ORG/1 PER. These counts and differences do not establish accuracy or improvement. Both model runs still predict only LOC/ORG/PER; the six expected location classes describe constructed references, not a newly trained model.

[Qualification](qualification.json), [case register](case_register.json), [comparison and controls](comparison.json), [prediction metadata](prediction_metadata.json), [tokenizer/vocabulary binding](tokenizer_manifest.json), [resources](resource_measurements.json), [replay](replay.json), [status](status.json), [audit](audit.json).

Native and candidate inference use separate Windows CPython 3.11.17/spaCy 3.7.5 CPU subprocesses, batch size one, two CPU threads, one warm-up pass and ten measured passes: **480 measured calls per mode**. Loading time excludes module imports and candidate adaptation/serialization. Measurements apply to these short constructed inputs on the current host. They are not GPU or news-service performance guarantees. Saved tokenizer bytes exclude vocabulary and are bound to the pinned model's vocabulary-file hashes. Reloaded tokenization matches before inference; repeated predictions are identical.

A fresh replay produces byte-identical native/candidate tokenizer files, tokenizer manifest, comparison and corpus-v3 token output. Native/candidate prediction payloads match after excluding inherently variable resource values. All **23 original model files** and **26,584 prior artifact files** verify unchanged, including dataset, partition, contextual-v2 and preflight checkpoints. Main Python 3.12 and installed packages are unchanged. Full constructed predictions and tokenizer bytes are in the ignored final-v5 folder; replay-v6 and prior runs remain preserved.

The dataset tokenizer's 14 failures are on the expanded constructed probes. They do not invalidate its previously validated frozen 400-source annotation alignment. The candidate is a separate research artifact; existing v2 defaults and frozen v3 bytes are preserved. Alignment against the news cohort remains unqualified and must follow source-use admission.

The new offline qualify-model-tokenizer command requires a verified pinned model, isolated interpreter, explicit constructed provenance, preserved original cases, and a new ignored output directory. It independently recomputes reference alignment and controls from validated token offsets; false flags, omitted source characters, malformed outputs and failed processes cannot become successful qualification.

The **400 silver location samples and 40 contextual v2 pairs remain prepared**. All twelve source/use review outcomes are unresolved. News inference, corpus evaluation, training admission, export and training remain zero. GPU setup, production integration, database changes, deployment and Git publication were excluded. This milestone completes constructed boundary qualification; it does not qualify six-class accuracy or every possible future tokenization case.

Future training and inference must use consistent tokenization. Modifying a pretrained tokenizer can change predictions. [Official spaCy guidance](https://spacy.io/usage/linguistic-features#tokenization).

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).
