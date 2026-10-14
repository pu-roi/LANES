# 400-sample AI-reviewed flood NER research corpus

> **Last Updated:** October 14, 2026, 7:00 PM (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Annotation assembly completed locally; all samples remain research-only. Model training, training admission and independent accuracy qualification remain pending.

**Find the final dataset:** The dedicated local folder `backend/training/flood_ner/artifacts/400-sample-dataset-20261014/` groups the 400 selected passages, corrected context, all 132 source article captures, frozen tokenizer/schema/partitions, reports and file/path manifests. Start with its README.md; open 400-sample-links.csv for one row per sample or 132-article-links.csv for the article list. Verified 418 bundled files and both CSV totals. Original research files remain intact. The folder is ignored by Git; copy the entire folder for a private external backup. No external backup or publication was performed. [Folder record](bundle_register.json).

The developer authorized expansion of the [twelve-passage pilot](../flood-ner-ai-pilot-20261014/README.md). Source reading produced 551 additional location annotation records; with ten retained pilot records, the reviewed pool contains 561 records from 142 articles. Deterministic grouped selection produces **400 distinct, complete, same-AI-reviewed silver records from 132 articles**, with 1,374 location spans. Two unresolved original pilot records stay excluded and unchanged. Clear, separately reviewed passages from the same articles may still be selected.

| Research partition | English | Taglish | Total |
|---|---:|---:|---:|
| Training | 140 | 140 | 280 |
| Validation | 30 | 30 | 60 |
| Testing | 30 | 30 | 60 |
| Total | 200 | 200 | 400 |

All ten retained pilots belong to training. These are frozen research partition assignments, not proof of training admission or an executed training run. Accepted annotations: **400**. Training-admitted samples: **0**. DocBin-exported samples: **0**. Independently verified gold records: **0**.

## Sources, method and limitations

- Sample publishers: **GMA 193, RMN 194, ABS-CBN 13**. No publisher exceeds 200. The selected source articles are GMA 36, RMN 92 and ABS-CBN 4. The full reviewed source pool adds 97 distinct articles outside the original 100; 88 of those additions appear in the final selection. The original 100-register bytes and earlier source/annotation revisions remain intact.
- Samples by publication year: **2022: 50; 2023: 44; 2024: 74; 2025: 110; 2026: 122**, through October 14. Publication/capture evidence is separate from flood-observation time. Missing observation calendars and geographic identities were not invented.
- English/Taglish are **AI-assigned passage categories**, independent of historical article language tags. The operational Taglish definition includes Filipino clauses containing untranslated English common/technical lexical material; proper names alone are insufficient. Borrowing versus code switching and language judgments are not independently adjudicated. Do not present these counts as linguist-verified language ground truth.
- Publisher and language are strongly linked: English is GMA 187/ABS-CBN 13; Taglish is RMN 194/GMA 6. This limits language comparisons and publisher generalization. Equal language totals do not establish representativeness.
- ROAD 468, LANDMARK 103, LOCAL_AREA 50, BARANGAY 165, CITY 426 and PROVINCE 162 are source-exact spans. Seventy-two records contain no entities **within this six-label Philippine-place profile**. They may contain regional/country/water-body mentions or active flood reporting; empty entity lists do not mean no flooding.
- Complete annotation refers to the declared location profile. Regional aggregates, country names, island/water-body references and institution-only geographic adjectives are excluded. Generic local-government jurisdiction references and source datelines can contain location mentions without establishing flooding. Unknown PSGC/OSM identities remain unknown; supported parent mentions are separate from resolved identity.
- Paragraphs and list entries retain original offsets. Reviewed bounds remove widgets/captions and join cut observations into complete entries. Repeated text, overlapping passages, paired context views and entity counts cannot increase the sample count.

## Grouping, context and tooling

The **27 connected reporting components** conservatively combine same-publication-month reporting and named-storm co-mentions across months, plus article/body/syndication dependencies. They are split-dependency groups, not assertions of one physical flood event per component. Group evidence, reviewers and revisions remain separate from immutable capture metadata. This overgrouping reduces independence assumptions; uncertain unnamed cross-window reporting and exact incident identity still warrant further review before scientific model qualification.

The offline build-cohort command validates capture/publication evidence, source-bound annotations and explicit group reviews, rejects malformed spans and leakage, pins retained pilots to training, and enforces exact language/split/publisher constraints. Existing SciPy 1.14.1/NumPy dependencies supply deterministic constrained selection. No new dependency or operational database access is introduced.

AnnotationRecord now stores passage_language separately from source language. The frozen corpus uses **lanes.xx.address-v2**, retaining spaCy 3.7.5 and adding dateline/list-delimiter boundaries without changing text or internal address hyphens. Schema/tokenizer bytes, hashes, selected identities and artifact hashes are frozen. Earlier tokenizer-v1 evidence remains historical.

All 400 passages have separate raw context views with source-exact **unreviewed cue candidates** for measurements, time, status and access. They do not supply accepted scalar depths, polarity, observation dates, shared-fact relationships or severity labels. Earlier twelve rich drafts are preserved; completing contextual/severity references remains separate work.

## Verification and files

**424 automated tests passed in 30.58 seconds**, retaining the prior 400-test baseline and adding 24 collection/cohort/tokenizer/provenance checks. Raw capture hashes and publication pointers pass for all 142 reviewed sources. All 400 annotations validate. A second CLI build is byte-identical. Actual corpus DocBin export is rejected without output because reuse/admission remains unresolved. These checks establish software/source consistency, not model accuracy or independent label agreement.

- [selection_register.json](selection_register.json): 400 sample identities, offsets, quality, languages and partitions.
- [source_register.json](source_register.json): 132 represented articles with original capture/publication evidence.
- [entity_spans.json](entity_spans.json): source-exact names/types and parent references; no full bodies.
- [partition_manifest.json](partition_manifest.json), [group_reviews.json](group_reviews.json): frozen artifact identities and grouping evidence.
- [case_matrix.json](case_matrix.json), [collection_outcomes.json](collection_outcomes.json): selected source-linked cases, remaining gaps and acquisition outcomes.
- [coverage.json](coverage.json), [exclusion_register.json](exclusion_register.json), [audit.json](audit.json): measured coverage, dispositions and verification.
- [context_register.json](context_register.json): contextual evidence pointers; candidate interpretation remains unreviewed.
- [methods-notes.md](methods-notes.md): accurate paper-preparation wording and pending research claims.

Full captures, source-reading decisions, 561 input records, frozen 400-record JSONL, tokenizer/schema snapshots and contextual text stay under ignored backend/training/flood_ner/artifacts/cohort400-20261014/. The metadata report does not redistribute full news bodies. [Commands](../../../backend/training/flood_ner/README.md), [roadmap](../../plans/lanes-ner-training-plan.md).

PNA/Philstar failed fetches, ABS-CBN site shells, short publisher summaries and supporting Wikipedia material do not contribute samples. Missing real-source address forms, broader taxonomy, independent language/label review and source-use assessment remain explicit. No model installation/training, runtime integration, schema migration, Google document edit, publication or deployment occurred.

## Follow-up completed-work review

The [follow-up review](followup_review.json) rechecks all 142 reviewed capture/publication bindings and 400 annotations, frozen artifact hashes, exact quotas, pilot placement, saved-tokenizer round trips and research-only export refusal. A fresh CLI assembly is byte-identical to cohort-v2. Source-context spot checks supplement these technical checks; they do not establish independent human label verification.

Found and fixed one auxiliary format defect: context-v1/context_evidence.jsonl contained concatenated pretty-printed JSON objects. The new context-v2/context_evidence.jsonl contains exactly 400 independently parseable JSONL lines. Every context object, source character, offset and candidate cue is unchanged; the earlier file remains preserved. The reusable context writer refuses overwriting earlier artifacts and has a multiline/Unicode/byte-determinism regression. The frozen location dataset and original 100-article register are unchanged.

Final isolated verification: **425 passed, one existing spaCy/Click deprecation warning, 27.46 seconds**. The first run inherited an encrypted local auditor batch-size value (405 passed/19 failed); setting all auditor test options explicitly yields 424 passes before the fix and 425 afterward. No runtime configuration was modified.

The ten-calendar-year window (2017–October 14, 2026) remains proposed; collection still filters 2022–2026. Broad future tokenizer/model compatibility tests, independent label/language review, publisher/language confounding, exact incident grouping, missing address forms, contextual/severity annotation and source-use qualification remain open. Dataset preparation can proceed to qualification; model training remains pending.
