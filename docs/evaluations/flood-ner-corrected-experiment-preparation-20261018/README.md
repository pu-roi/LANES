# Corrected-data experiment preparation — October 18, 2026

Prepared a separate revision of **345 training / 60 validation** records. Exactly **12 supported boundary extensions across nine training records** were adopted from the completed [development audit](../flood-ner-development-error-audit-20261018/README.md). Text, source captures, record/entity identities, types, languages, membership and fitted-source/group bindings are preserved. Training retains 840 entity spans; validation retains 85. Labels remain AI-assisted silver, not human verified.

All 60 validation references, `dev.spacy`, frozen tokenizer bytes and partition/source-join metadata remain byte-identical. The unresolved validation landmark-boundary question remains documented with its original reference. Training languages remain 170 English / 175 Taglish; validation 38 / 22. Validation still has no Taglish ROAD support and only one Taglish LANDMARK span.

Three exact twelve-file trainer packages share the corrected training export and unchanged validation export. Each includes portable seed 0/1/2 configs:

| Configuration | Dropout | Learning rate |
|---|---:|---:|
| Corrected-data control | 0.1 | 0.001 |
| Higher dropout | 0.2 | 0.001 |
| Lower learning rate | 0.1 | 0.0005 |

The pinned model/vocabulary/tokenizer, fresh six-class head and restored encoder recipe, batch size 8, L2 settings, 1,000-step/30-epoch ceilings, patience 175, evaluation frequency 35 and earliest-checkpoint tie-break are unchanged. Actual Python 3.11.17 / spaCy 3.7.5 registry/schema qualification passes for all nine configs without initializing a training pipeline, loading pretrained weights, predictions or optimizer updates. Serialization and exact identity/text/span reload checks pass for all 405 records. The existing frozen trainer, serializer and registry helpers remain unchanged.

## Future protocol — specified, not executed

Screen control, higher dropout and lower learning rate sequentially on seed 0. Use full-precision strict validation micro F1; values within 1e-12 of the maximum tie, preferring control, then higher dropout, then lower learning rate. Confirm control on seeds 1/2 and, if different, the screening winner on seeds 1/2: five runs if control wins, otherwise seven. Historical v16 models cannot replace the corrected-data controls.

Retain a variant only when its seed-0 F1 and three-seed mean both strictly exceed the corrected-data control; otherwise retain control. Report all screened outcomes, supported per-label/language metrics and regressions. Do not try a runner-up automatically. Any failure stops the sequence; preserve logs/output without retry, concurrent runs, destination reuse or budget expansion. This is research selection, not production acceptance or a promised 80% F1.

## Verification and preservation

Fresh checks: **367 passing tests / 35 passing subtests across nine suites**, including **83 new tests**. The pinned runtime runs 158 tests; the existing general environment runs the other 209. A combined attempt could not collect a SciPy-dependent historical suite across these incompatible runtimes; separate compatible runs pass without dependency changes. Both final runs retain the existing Click deprecation warning. These are fresh results, separate from earlier audit/training counts.

The first preparation attempt stopped on an overly strict numeric-zero assertion: spaCy uses an empty per-parameter optimizer-update mapping. Its partial output, source snapshot and consumed grant are preserved. A regression covers empty versus nonempty update mappings; a new hash-bound grant and absent destination produced the completed second package. No training attempt occurred.

All 154 explicitly snapshotted predecessor files match their original SHA-256 and sizes. The 23-file base model passes existing contract verification. Holdout contents remain unopened and unhashed; metadata for 55 files under holdout artifact directories is unchanged. This metadata check is distinguished from a new content-hash inspection. Existing recorded holdout hashes are not rewritten. Default verification produces no file or timestamp changes in the completed package.

[Machine verification and hashes](verification.json) · [Operator instructions](../../guides/ner-corrected-experiment-preparation.md).

## Delivery status

**LAPTOP QUALIFIED; NOT DELIVERED; DESKTOP GPU NOT VERIFIED FOR THIS REVISION.** No collection, added passages, holdout access, inference, training, upload, commit or push occurred. The 60-passage research holdout stays separate and unchanged. Incomplete collection/history evidence remains explicitly accepted only under the documented-limitations silver research comparison; preparation does not certify freshness.

Next task: separately publish the matching code and deliver the private trainer/protocol materials, then verify their actual presence and the qualified GPU on the desktop. Explicit desktop execution follows that preparation. A Git pull alone cannot transfer ignored packages. The desktop can remain off now.
