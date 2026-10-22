# NER plan, data and training consistency review

> **Last Updated:** October 16, 2026, 11:50 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The completed original experiment is intact. The new article pool has not replaced it or been used in another training run.** Original and new records share the same schema and six-class location profile. This review finds and repairs a real checkout-byte problem, distinguishes intentional workflow changes from unfinished work, and records the user's device decision: **laptop for review/validation/preparation; the existing qualified desktop GPU for training**.

This is not a certification that another run is ready. New dataset readiness, a versioned experiment/export and the fresh independent holdout remain incomplete. No new articles, annotation revisions, corpus replacements, predictions, optimizer updates, environment installation or deployment occur in this review.

## Evidence inspected

Read the user-supplied `D:/Downloads/helo (1).txt` as a report of desktop work, not executable instructions. Read **Build flood news NER check** from its final handoff back through all available earlier turns to the original request, including the 100-article expansion, the correction to **400 total annotated passages**, AI annotation delegation, stronger revisions, tokenizer qualification and the final 400/138/40 handoff. The attachment's later desktop claims are checked against restored artifacts and published reports; they are not assumed to be contents of that older chat.

Compare the October 14 roadmap at Git commit `4240a3d8`, the pre-desktop handoff at `4736cea3`, the desktop code/reports at `477c6d4c`, current uncommitted review work and the verified v3 private transfer. Inspect the shared annotation schema, both serialization paths, tokenizer bindings, encoder initialization, recipe variants, selection callback, launcher/device checks and final test freeze. Supporting records: [original roadmap](../../plans/lanes-ner-training-plan.md), [source/relevance audit](../flood-ner-topic-audit-20261016/README.md), [desktop qualification](../flood-ner-desktop-tokenizer-qualification-20261016/README.md), [qualified export](../flood-ner-qualified-export-20261016/README.md), [completed study](../flood-ner-validation-study-20261016-v2/README.md), [test freeze/results](../flood-ner-heldout-test-20261016/README.md).

## What is consistent

| Concern | Completed original experiment | New development pool | Assessment |
|---|---|---|---|
| Record schema | `lanes-flood-ner-v1` | Same | Both validate against the actual shared `AnnotationRecord` model. |
| Location profile | `location-only-v1`; ROAD, LANDMARK, LOCAL_AREA, BARANGAY, CITY, PROVINCE | Same six classes/profile | No new competing label vocabulary. |
| Record state | 400 accepted, privately admitted references | 244 drafts, research-only; splits null | Intentional preparation state, not an interchangeable training input. |
| Frozen original membership | 138 sources, 1,465 spans, 200 English/200 Taglish, 280/60/60 | Separate checkpoint and record IDs | Original hashes/partitions remain unchanged. |
| Context | 40 linked context-rich records within the original 400 | No replacement context benchmark delivered | The original experiment is not 440 independent location samples; six-class NER does not learn all depth/time/status associations. |
| Text and spans | Source-exact strings with non-overlapping Unicode character offsets | Same contract | Character offsets, not UTF-8 byte offsets; no text normalization to force alignment. |
| Training representation | Qualified spaCy DocBins derived from JSONL | No new export | JSONL and `.spacy` are source and training representations of the same intended data, not conflicting formats. |
| Tokenizer | Qualified `lanes.tl.calamancy-address-v1`, SHA-256 `3f666f61346b7196d931ab9781a3d83f41d688e24b298e8e494b3d92c384a588` | Same saved bytes; one draft alignment failure | No silent tokenizer replacement. The new failure remains a hold. |
| Experiment | Original seeds 0/1/2; separately preregistered A/B development trials | No new recipe frozen or trained | Additional collection is preparation for a possible next experiment. |

Fresh validation checks **684 schema objects**: 400 original locations, 40 contextual records and 244 new location drafts. All **52 original admission-manifest hashes** pass. Qualification/export/preparation have identical input bindings, and their **27 payload-file hashes** verify. All **16 pinned source hashes** across tokenizer qualification, export, preparation and the final evaluator/launcher/recipe freeze match after the checkout repair below. All **66 selected-model files**, six frozen configuration bindings and tokenizer identities verify; no training configuration includes `test.spacy`. All **460 original audit inputs** remain unchanged.

## Intentional changes that can look inconsistent

1. **Article count changed across research revisions.** The original target is 400 annotated passages, not 400 articles. Earlier 132- and 139-source versions and the final 138-source handoff are separate preserved revisions. The referenced conversation explicitly reviews their changes; the final trained derivative is the 400/138/40 one.
2. **Collection/helpers evolved.** The initial generic collection/export tooling used a multilingual address tokenizer. The later model-bound export uses the pinned calamanCy vocabulary and qualified tokenizer. Qualification checked the same original source spans before export. Reverting to an earlier generic exporter merely because it is older would undo that qualification boundary.
3. **Model adaptation is specific.** Actual training initializes a fresh six-class NER head and copies the pinned pretrained calamanCy NER encoder/static vocabulary. The saved architecture is `TransitionBasedParser.v2` + `Tok2Vec.v2`/`MaxoutWindowEncoder.v2`; it is not a trained transformer. Original recipe: batch 8, dropout 0.1, learning rate 0.001, patience 175, up to 30 epochs/1,000 steps, development scoring every 35 steps. Recipe A changes patience to 350; B also changes learning rate to 0.0005. These changes were separately registered, not silently applied to the original runs.
4. **Selection remains development-only.** Original seed 0 remains primary, seeds 1/2 are robustness runs, and the selector retains the earlier step on equal development F1. A higher-scoring original test seed is not promoted. The separate coarse LOC baseline is not six-class performance.
5. **Fresh data after error review is a normal next experiment, with a new evaluation boundary.** The original test is exposed, so future tuning cannot reuse it as an untouched test. The 240-development/60-fresh-test target is a proposed improvement design, not an automatic rewrite of the original paper's 400-sample experiment or a decided combined corpus size.

The original research plan already distinguishes six-class location recognition from contextual flood interpretation and PSGC/OSM identity/placement. These latter tasks remain separate qualification/integration work. If the manuscript still describes human-created gold annotations or an already-trained transformer, it must be reconciled with the actual AI silver/encoder-transfer method before those results are presented. This review does not edit the manuscript or invent independent annotation verification.

## Repaired: Windows checkout changed hash-bound source bytes

The laptop has `core.autocrlf=true`. Newly added Python tools were LF in Git but CRLF in the working tree; several older desktop tools were recorded as CRLF in their frozen manifests while the laptop had LF. **The text/logic was identical, but raw-byte SHA-256 differed.** This is a concrete portability defect, not evidence that the original model trained on a different dataset or algorithm.

Added recursive research-Python byte preservation to `.gitattributes`, following the repository's existing frozen-code convention. Four historically CRLF files have explicit `text eol=crlf` overrides: `cli.py`, `corpus_tokenizer_qualification.py`, `corpus_tokenizer_worker.py` and `evaluation/contract.py`. Other research Python files preserve their recorded Git blob bytes. Matching each file's actual frozen style matters; a blanket LF rewrite would break some identities too.

Restored the byte-equivalent source forms and refreshed Git conversion metadata without staging content changes. Kept every frozen manifest/hash, dataset and model unchanged; no relaxed/normalized hashing is introduced in validators. All **16 unique recorded source bindings** now pass: two qualification, two export, four preparation and eight final evaluator/launcher/recipe files. There are no semantic changes to those Python files.

The new `test_flood_ner_repository_bytes.py` creates real temporary Git checkouts with both `core.autocrlf=true` and `false`. Six root/nested source fixtures retain the required LF/CRLF styles in both settings. Newline conversion should not be used as an excuse to regenerate frozen manifests or bypass a failed identity check.

## Unfinished work before another run

- **Corpus decision and annotation compatibility:** Keep the original experiment immutable. Decide whether the next study uses a revised 400-sample corpus or a separately reported expanded corpus, with exact membership/counts before export. Do not append all 244 drafts, silently overwrite six weak original windows or count the 48 fictional fixtures as captured samples. Apply one prospectively frozen convention version; review any old references affected by the addendum before mixing versions.
- **Actual eligibility:** There are 179 candidates/65 unscored holds, zero newly admitted records and no new frozen splits. Candidates contain 101 empty-location passages, 78 positives and zero LOCAL_AREA spans. Resolve the existing reference/language/source-use/alignment questions and improve positive rare-class and publisher/event coverage. These are measured limitations, not automatic proof every negative or older article is bad.
- **Join review/grouping evidence before final assembly:** Draft annotations are preserved history. Their `complete=true` field does not override the separate 65 unresolved-reference entries, whose `expected_entities=null`, `allow_definitive_scoring=false` and `is_negative=false` are authoritative. Raw `validate_rows` checks are structural, not admission. Reviewed groups/duplicate components are in a separate ledger while draft source groups remain provisional. The successor assembler must consume those ledgers, preserve the shared source schema and retain real article/event/syndication separation; it is not yet delivered by the draft helpers.
- **Fresh test:** Safe aggregate metadata still reports 56 prospective records, zero admitted independent test records and no seal. This review does not open private held-out texts/labels to solve development gaps. Complete that curation separately and freeze it before new training.
- **A new export/experiment on the desktop:** Current qualified export and launcher deliberately bind the original 400-record experiment and completed output folders. They are not a generic launcher for a new corpus. Preserve them. Prepare a new versioned export/configuration and output path only after readiness; verify actual desktop-local paths, environment, tokenizer and selected recipe rather than editing historical manifests in place. Do not reuse a completed run directory or rerun the old exclusive test attempt.

These items remain open explicitly. The attachment's statement that no further training occurred after the model-qualification review is consistent with the saved new-dataset state. No corrupted original experiment or completed new corpus was found.

## Laptop and desktop roles

Observed laptop: **Acer TravelMate P215-53G, Intel i5-1135G7 (4 cores/8 threads), 15.78 GiB installed RAM, MX330 with 2,048 MiB VRAM**. Available RAM at the observation was 6.31 GiB and changes with other applications.

CPU-only spaCy training is supported (`--gpu-id -1`), and CPU computation uses system RAM. RAM holds data/parameters; it does not turn a weak GPU into a faster one. Suitability and duration for a particular run need actual resource measurements. [spaCy training CLI](https://spacy.io/api/cli#train).

The existing launcher explicitly requires `spacy.require_gpu(0)`, imports the frozen GPU runtime and refuses CPU fallback. Its recorded configurations contain original desktop paths. That is an implementation choice for the completed experiment, not a fundamental requirement that all spaCy NER training use a GPU. The laptop's existing Python 3.11.17/spaCy 3.7.5 environment successfully imports spaCy and selects CPU in a fresh no-model probe; this does not qualify model loading, training speed or peak memory. The older Windows 4551 failure is preserved as history, not assumed to be today's import result.

**The user then chose desktop-only training.** Continue laptop data/consistency checks and prepare the future private handoff here. Do not install CUDA, replace environments, add a CPU trainer or begin a laptop benchmark for this task. Reuse and verify the existing desktop environment when the new dataset/experiment is ready. The repository CLI environment remains Python 3.12.14; the qualified training interpreter remains a separate Python 3.11 environment.

## Verification and outcome

**80 focused tests pass:** 60 export/preparation/launcher/recipe/test-freeze/real-Git-checkout methods plus 20 existing new-dataset gate methods. They exercise constructed fixtures, not actual corpus training or a new held-out evaluation. The old 880/one and other historical suite totals are not claimed as rerun. Artifact checks and the CPU import probe are reported separately from these tests.

Changes: `.gitattributes`, one checkout regression test, synchronized current-status/guide documentation and a separate ignored audit script/report. Existing source Python semantics, private records, models, tokenizer, `.env`, dependencies, public APIs and database schemas remain unchanged. No collection, export, training, model predictions, deployment, correspondence, commit or push occurs.

Private audit: `backend/training/flood_ner/artifacts/consistency-review-20261016-v1/audit.py`, `summary.json`, `checkout-byte-repair.json`. Public [verification](verification.json) and [compatibility summary](summary.json) contain metadata only. Current instruction: finish the existing data-readiness/compatibility work on the laptop, then prepare a distinct verified desktop training handoff; do not start another run yet.
