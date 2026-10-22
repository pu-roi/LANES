# NER annotation corrections and refreshed study package

> **Last Updated:** October 15, 2026, 11:38 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The two verified annotation findings are corrected in a new cohort revision. Three location records and one paired contextual record changed. The same **400 passages from 139 articles**, source text, record IDs, source identities, reporting groups and **280/60/60 partitions** are preserved. Location labels remain same-agent AI silver references.

| Correction | Result |
|---|---|
| Missing province mention | Add Ilocos Sur at passage offsets 218–228; retain the later mention |
| Compound-location convention | EDSA is ROAD and Balintawak is LOCAL_AREA in all three EDSA-Balintawak passages |
| Location spans | 1,494 → 1,497: one additional PROVINCE and two additional LOCAL_AREA spans |
| Contextual v3 | One of 40 pairs updated; existing road target IDs and override links preserved |
| Context scope | Three existing facts gain a road-segment qualifier; no new locality-wide flood assertion |
| Membership and partitions | Unchanged: 200 English/200 Taglish; 140/140 train and 30/30 each holdout |
| Selection and hard quotas | No selection rerun; every existing hard quota passes; ten retained pilots unchanged |
| Study-use decisions | All fifteen remain unresolved; nine prior AI assessments and six deferred scopes unchanged |
| Training admission / DocBin export / model training | 0 / 0 / none |

The specific compound convention follows the preserved pilot. It does not authorize splitting every hyphenated name or identifiers such as 31-A. Geographic identities remain unresolved; these changes do not resolve PSGC or OSM features. The corrected validation label was reviewed before model training or tuning; validation/test membership did not change.

## Files and reproducibility

The current dataset is under `backend/training/flood_ner/artifacts/annotation-correction-20261015-v1/cohort-v2/`; current rich pairs are in the sibling `contextual-v3/`. The previous cohort and contextual v2 remain intact. The correction register binds complete prior-record and passage hashes, before/after entities, actual AI reviewer identity, review date, rationale and revisions. Applying it to changed inputs is rejected.

The current organized folder is `backend/training/flood_ner/artifacts/400-sample-study-package-corrected-20261015-v1/START-HERE.md`. Its 606-file manifest and separate replay agree byte-for-byte. It retains all 400 locations and 40 contextual v3 pairs privately, ten training-only appendix examples and held passage/ZIP candidates. The appendix still covers all six classes and three publishers with five English/five Taglish examples. The candidate still has 391 passage texts plus nine metadata-only entries; contextual candidates have 38 texts plus two metadata-only entries. Full article text and generated datasets remain ignored by Git.

The versioned study-use packet and review packet bind the corrected manifests and retain hash-linked predecessors. Publisher policies, source register, original twelve decision forms and fifteen scoped outcomes are unchanged. Annotation correction does not grant a dataset license, training admission or distribution readiness.

## Verification

**638 focused regression tests pass**, including all NER tests, PSGC, locality numbers, locality anchors, headings and three article-road suites. This is the latest 613-test focused selection plus 25 new correction/versioning checks. The historical 666-test broader result uses a different selection and is preserved as historical evidence; it is not represented as this run's count. One existing spaCy/Click deprecation warning remains.

Saved-data checks cover source binding, exact Unicode offsets, frozen-tokenizer alignment, duplicate hashes, same-article overlaps, reporting groups, every hard quota, contextual references/overrides, preserved pilots, package/ZIP identities and refusal to export all 400 research-only records. Cohort and package replays are byte-identical. No live model, GPU, production pipeline or database execution is performed.

[Correction register](correction_register.json), [coverage](coverage.json), [selection register](selection_register.json), [revision manifest](partition_manifest.json), [context coverage](context_coverage.json), [bundle register](bundle_register.json), [verification](audit.json), [comparison](comparison.json) and [paper-method notes](methods-notes.md).

Full artifacts are additional local copies, not an external backup or public release. No article collection, source-use clearance, runtime integration, dependency installation, schema change, deployment or Git publication is included. The four feed review issues remain deferred in the task plan.
