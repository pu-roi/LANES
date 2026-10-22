# Successor config casing correction

> **Updated:** October 18, 2026 by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The v15 trainer configs were invalid for spaCy's actual registry schemas.** The desktop reported seed0 failed before optimizer updates and stopped seeds1/2. Desktop failure logs were not supplied, but the original config's optimizer schema error was reproduced locally without training. The earlier preparation/delivery checks established byte equality and syntax, but did not establish usable argument casing; those config-readiness claims are superseded by this correction. Earlier frozen reports and packages remain unchanged.

## Repair and evidence

The private v15 builder used RawConfigParser's default option normalization and compared recipes after lowercasing both sides. That changed `L2` to `l2`, `L2_is_weight_decay` to `l2_is_weight_decay`, and architecture `nO` to `no`. The successor-only public generator now uses case-sensitive parsing/writing, and its fast verifier rejects these aliases. Historical fixed-400 helpers and the preserved v15 private builder are unchanged.

The launcher now additionally resolves all three complete rendered configs through spaCy 3.7.5's registry and ConfigSchema in the selected Python3.11 interpreter, before a training destination or lock is created. This constructs uninitialized model graphs and an unused optimizer; it does not create a Language pipeline, load pretrained weights, read examples, invoke training callbacks, predict, or perform updates. The config-schema subprocess verifies zero optimizer updates and no checkpoint writes. Validation errors surface to the caller.

Actual pinned qualification passed for seeds0/1/2 on Python3.11.17/spaCy3.7.5. The actual read-only launcher reports `verified_read_only`, `configuration_schema_verified: true`, `gpu_verified: false` and `training_started: false`. Laptop verification does not establish desktop GPU readiness. Constructed regressions cover all three casing errors, each generated seed, rejection before output creation and the isolated validation subprocess. Fresh affected-suite result: **352 passed / 190 passing subtests / one Windows symlink skip**; one existing Click deprecation warning. Historical215/165 and344/190 results remain historical.

The replacement preserves **345 training /60 validation /60 separate research-holdout** records. All eight non-config payload files are byte-identical, including train/dev exports, tokenizer and model/evaluation/GPU contracts. Hyperparameter values, labels and membership did not change. The three configs and manifest/implementation bindings are versioned separately. The original twelve-file payload is hash-checked unchanged. Holdout content was not accessed.

## Corrected delivery and desktop action

The owner-only [v16 folder](https://drive.google.com/drive/folders/15sxU7utCM9Nf429BXWUQlXgtEoC1nTQH) contains a [corrected trainer ZIP](https://drive.google.com/file/d/1TWFzEQVE6EFlxeOVrYf7YR0d1SaPhcjK/view?usp=drivesdk), checksum and START-HERE instructions. The ZIP has exactly12files, **153,999 bytes**, and its complete Drive download matches SHA-256:

```text
b581ed97a7e54e3d6db7f9b3504ff94d8a48bb341437f7e84ed31bf39b2b41c7
```

New trainer manifest SHA-256: `40fda6b9df92ea1d51d99d167b1830fa38da64308203168d5ca5457a05a2738f`. The v15 Drive folder, packages and frozen manifests remain preserved. Research-holdout content, model weights, environments and credentials are excluded from this transfer. [Machine-readable verification](verification.json).

Follow the [desktop correction guide](../../guides/ner-successor-desktop-training.md): preserve failed seed0 logs/output and the old package; pull matching code with `--ff-only` after reviewing local changes; verify the corrected ZIP; extract to an absent v16-configfix destination; run `--verify-gpu` and stop. Require schema verification in addition to GPU verification. Do not hand-edit old manifest-bound configs or rerun old commands. A seed0 retry needs a later explicit action and a new output directory; seeds1/2 remain stopped. Desktop receipt and GPU re-verification of the correction are pending. Publication/readback receipts are private.

No training, inference, collection, environment installation, data replacement or holdout evaluation occurred for this repair. AI-assisted silver, incomplete provenance/accounting and no certified-fresh/human-gold or improvement claims remain in the evaluation contract. Production APIs, dependencies and database schemas are unchanged.
