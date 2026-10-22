# LANES Gate 3 NER improvement preparation — October 16, 2026

> **Last Updated:** October 16, 2026, 8:57 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Preparation complete; operational model qualification remains open.** Codex, acting under researcher delegation, prepares a prospective [reference-scope addendum](../../guides/flood-ner-reference-scope-addendum-v1.md), a verified constructed matrix, a training/validation coverage inventory and a [fresh evaluation protocol](future-evaluation-protocol.md). This is AI-authored development preparation, not independent adjudication or improved-model evidence.

The original **400 samples / 138 articles / 40 contextual pairs / 1,465 spans**, 200 English/200 Taglish and 280/60/60 partitions remain frozen. Original seed 0 remains primary (**63.12 strict test F1**), Recipe A seed 0 exploratory (**67.72**). No benchmark label, offset, prediction, score or selection changes.

## Delivered specification

- All **14** historical questions appear once in the ignored register, with original IDs/offsets, passage hashes, evidence bindings, future handling and missing-evidence requirements. Thirteen retain unresolved occurrence interpretation/identity/taxonomy/boundary/scope; one documents a shared-identifier convention for future development. No original question is silently relabeled.
- **48** fictional constructed cases: eight themes, **24 English / 24 Taglish**, three per language/theme including one negative. There are **30 positive cases, 16 negatives and 2 unresolved cases**. The 46 definitive references and two unscored ambiguity probes retain exact Unicode offsets, rationale, provenance and hash-bound guide/review evidence. They stay outside corpus admission/export.
- The 340 training/validation records are inventoried without promoting exposed test passages to development examples. Candidate matches below are reproducible proxies, not complete semantic coverage, defect counts or model performance.
- A local exclusion index binds **1,445 structured inputs** and **712 source-metadata variants / 348 source-ID values**, including historical/nonadmitted material. Three unrelated node dependency configuration files are not strict JSON and are separately classified; none is a research-source parse failure. Historical coverage is explicitly incomplete pending reconciliation with missing/other-computer inventories.

## Coverage and additional captured evidence needed

| Theme | Train proxy hits | Validation proxy hits | Existing evidence and limitation | Additional capture requirement |
|---|---:|---:|---|---|
| compound-crossing-roads | 49 | 10 | Training includes a two-road intersection; validation includes code-plus-road and compound/list passages. Having multiple ROAD spans does not establish every crossing/compound convention. | Capture English/Taglish integral compound roads versus two crossing roads, road/locality hyphens, directions, abbreviations and dense lists. Preserve each raw occurrence and source-supported segmentation. |
| short-codes | 7 | 3 | A small uppercase/code-shaped ROAD proxy finds train/dev examples. It includes familiar named-road acronyms; novel code generalization and code-like negative support are unmeasured. | Capture independently sourced road acronyms/codes with explicit road cues and contrasting batch/equipment/report codes. Do not infer ROAD from capitalization alone. |
| locality-designators | 57 | 18 | Both splits contain explicit barangay/locality cues; prefix matches do not prove coverage of every block/lot/phase/zone abbreviation, Roman numeral or suffix. | Capture full block/lot/phase/unit/sitio/purok addresses, leading zeros, letter suffixes, accents and repeated identifiers under different parents. Contrast stages/counts and retain raw spelling. |
| shared-identifiers | 1 | 0 | One training passage contains an explicitly coordinated purok identifier whose second raw span is a bare number. No dev match for this narrow numeric-span proxy; broader ellipsis remains unmeasured. | Capture coordinated short sitio/purok/block identifiers, explicit antecedents and scope breaks, plus numbered non-place lists. Include English and Taglish material; never synthesize absent designators. |
| facilities-institutions | 18 | 5 | Named schools, market and hospitals occur in train/dev physical contexts. Keyword candidates include unrelated wording and do not quantify the institution-only negative contrast. | Capture physical hospital/school/terminal/market mentions versus professional, board or organizational attribution using the same names/acronyms. Ambiguous senses need unresolved review, not guessed labels. |
| project-asset-names | 26 | 11 | Broad keyword hits include generic bridges without landmark entities, flood-project prose, a proposed-school route and an existing dam group. They are candidate contexts, not verified project-title coverage. | Capture independently described physical/proposed named assets, formal project titles and geographic substrings used only as branding. Keep genuinely unresolved title/asset senses outside definitive references. |
| geographic-type-ambiguity | 201 | 40 | Many bare administrative/local-area spans exist; this deliberately broad proxy also matches type-bearing suffixes. Its counts are not counts of annotation defects or actual ambiguity. | Capture explicit source-supported type cues and genuinely bare settlement/island/province contrasts. Require contextual evidence for class, separate reviewed PSGC/OSM evidence for identity, and preserve unresolved spellings. |
| misleading-names-time-common-words | 39 | 6 | There are 39 train and 6 dev zero-entity passages; all dev negatives are Taglish. These support generic/no-place negatives, not necessarily reporter-name/clock adversarial coverage. | Capture real no-location passages and positive/negative contrasts for bylines, people, clocks, counts, weather names and generic structures. Require both languages; never equate no flood with no location. |

The narrow shared-identifier proxy has **one training example and no validation example**. Six validation negatives are all operational Taglish; future acquisition must include English negative contrasts. Counts overlap across themes and cannot be summed as unique coverage. Exact IDs, entity offsets and input hashes remain private; this report contains no article quotations.

## Fresh future evaluation

Require **60 newly acquired passages, 30 per language**, with **3 no-location negatives per language**. Separate article/event/syndication/duplicate groups from all prior material and new development. Freeze conventions before acquisition/label finalization, isolate held-out curation from model development and seal memberships before training. Unknown grouping or incomplete historical screening blocks admission. Document AI silver provenance and pretrained-data overlap limitations.

Strict six-class metrics, class/language supports, negatives, null metrics and separate coarse-LOC comparison are specified. Additional corpus size, recipes and future acceptance decisions remain for dataset-readiness after actual source-backed coverage. Do not adopt the roadmap's proposed thresholds retrospectively.

## Verification and preservation

The preparation validator passes **12 standard-library tests** for case counts/uniqueness, theme/language/negative quotas, six-class labels and unresolved separation, Unicode/ellipsis offsets, malformed-case rejection, all 14 question bindings, train/dev-only coverage, prior-passage/test-sequence copying, source exclusion inventory, future protocol and original corpus totals. These are preparation-integrity checks, not tokenizer alignment or model evaluation.

The sealed test experiment revalidates read-only without another attempt. Final [verification](verification.json) and [preservation](preservation.json) record the prior-artifact hashes, pinned-model files, research-environment metadata, CLI packages, original source files and .env checks. Research environment preservation uses size/mtime, excluding bytecode, rather than full environment content hashes. No earlier model/software evaluation is claimed as rerun.

## Next task and boundaries

**Prepare and admit the additional dataset under this specification**, beginning with historical exclusion reconciliation, case-specific source-use eligibility and captured examples for the recorded gaps. Keep new held-out curation isolated. Record actual coverage before deciding corpus size and bounded recipes.

CPU/Linux compatibility, missing/corrupt-model behavior and latency/memory/long-text evidence remain open Gate 3 work; Gate 4 has not started. Historical acquisition/use-evidence limitations and deferred distribution/production outcomes remain as recorded in the [completed review](../flood-ner-model-qualification-20261016/README.md).

Ignored checkpoint: backend/training/flood_ner/artifacts/improvement-preparation-20261016-v1. It contains the question register, 48-case JSONL, coverage/acquisition inventory, exclusion index, future protocol, reproducible preparation/verification scripts and audit manifests. Public JSON is metadata-only.

No new research, acquisition, annotation revision, inference, export, training, dependency/API/schema changes, deployment, correspondence, commit or push occurs. [Task plan](../../task_plan.md); [training roadmap](../../plans/lanes-ner-training-plan.md).
