# Stronger 400-sample NER continuation

> **Last Updated:** October 15, 2026, 2:18 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The annotation-preparation milestone is complete: **400 reviewed AI silver location samples from 139 articles**, with **40 reviewed contextual pairs from training**. All unchanged hard quotas pass. The original dataset, backup and prior checkpoints remain preserved. Training admission and export are **zero**, pending source reuse assessment; no model was trained.

| Partition | English | Taglish | Total |
|---|---:|---:|---:|
| Training | 140 | 140 | 280 |
| Validation | 30 | 30 | 60 |
| Testing | 30 | 30 | 60 |

| Publisher | English | Taglish | Total |
|---|---:|---:|---:|
| ABS-CBN News | 58 | 100 | 158 |
| GMA News | 95 | 65 | 160 |
| Philstar | 47 | 35 | 82 |

The cohort contains 1,494 place spans and 82 connected reporting groups: 48 training, 19 validation and 15 testing groups. The largest article supplies eight samples; the largest reporting group supplies 53. Each location class meets its per-language span/passage/article minimum in every partition, including the stricter ROAD quotas. All ten retained pilots are in training. Forty-five passages contain no supported place entities; negative contexts still receive every supported location label. [Coverage and exact checks](coverage.json), [years and group limits](corpus_coverage.json), [frozen partitions](partition_manifest.json).

All 156 pending captures were read: 83 GMA, 71 RMN and two Philstar. All 36 failed URLs were retried; HTTP retries failed, so eligible public rendered bodies were saved as new immutable versions. Recoverable older-window/extraction exclusions were reassessed. The source register now contains 342 research sources, with 200 cumulative additional admissions and all 300 original candidate URL slots used. Recoveries stayed inside that ledger. Non-English/Taglish, foreign, incomplete, ambiguous, conflicting-date and duplicate material was excluded or held. Nineteen reviewed candidates were deferred at the article-admission limit. Earlier outcomes remain intact. [Review decisions](source_review_register.json), [source register](source_register.json), [budget](collection_budget.json), [status](status.json).

The corrected input revision contains 1,340 accepted location records; duplicate/overlap rejection leaves 1,331 eligible passages. During contextual review, two named drainage outfalls were corrected from ROAD to LANDMARK, and a municipality-list mention from BARANGAY to CITY with its spelling/identity unresolved. The first successful selection no longer met ROAD span support after that correction; assembly was rerun and all quotas passed. No source characters or prior annotations were changed. [Label corrections](label_revision.json), [exclusions](exclusion_register.json).

The contextual pilot comprises 20 English and 20 Taglish training records from 14 and 19 articles respectively. Shared observations, local exceptions, collective ranges, temporal transitions and negative/unknown times all meet the four-example minimum with both languages. Collective sets preserve different reported depths; temporal overrides preserve earlier observations. Schedules, rainfall clocks, money and project-phase counts do not become flood depths or observation instants. Unnamed targets and absent clocks remain unresolved. These 40 pairs are part of the same 400 passages. [Context coverage](context_coverage.json), [fact/relationship metadata](context_register.json), [category evidence pointers](context_category_reviews.json).

spaCy remains 3.7.5. The saved `lanes.xx.address-v3` tokenizer is bound by its bytes and SHA-256; the legacy v2 and 2022–2026 defaults remain unchanged. Explicit 300-second selection limits allowed the existing optimizer to complete. Resource-limit termination is recorded as unresolved rather than proven infeasibility. The final corrected cohort and the original 400 both replay byte-for-byte. **525 tests pass**, retaining the 508 baseline and adding 17 regression cases. [Verification](audit.json), [old/new comparison](comparison.json).

[400 source/sample CSV links](sample-links.csv) and [342 article links](article-links.csv) are metadata-only. The dedicated ignored local folder is `backend/training/flood_ner/artifacts/stronger-400-continuation-20261015/`; its `selected` article column identifies the 139 used sources. It includes frozen annotations, 40 contextual pairs, all reviewed source captures and a verified hash manifest. This folder requires an external backup separately from Git. [Bundle record](bundle_register.json).

The labels and passage-language judgments remain AI-created silver references, reviewed by the same agent. English borrowings are counted under the disclosed operational Taglish convention; this is not independent language adjudication. Conservative reporting components are leakage guards, not verified physical incidents. Meeting quotas does not establish model accuracy, broad geographical representativeness or coverage of every number/address form. [Paper-method notes](methods-notes.md), [case matrix and remaining gaps](case_matrix.json).

The next stage is source-use/training-admission and model/tokenizer/resource qualification, followed by authorized baseline evaluation and training. This continuation performed no production ingestion, map publication, database change, model installation/training, deployment, shared-document edit or Git publication.
