# Flood NER successor dataset design

> **Last Updated:** October 17, 2026, 2:16 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Design complete; training readiness remains open.** Retain all **402 provisionally qualifying candidates** and propose **345 training / 57 development-validation** records. Keep every historically fitted article and its conservative related component on the training side, including fitted examples now excluded or held. No actual corpus admission or partition freeze occurs.

The user explicitly chose using eligible saved examples over fixed counts/exact language balance, and keeping old training material in training. This version prospectively supersedes the additional **240 / 192–48 / 15-per-theme-language-cell** requirements for the successor only. The [historical acquisition specification](../flood-ner-additional-dataset-20261016/README.md), [saved-source feasibility findings](../flood-ner-successor-proposal-20261017/README.md), historical validator and original 400-record experiment remain unchanged. The old quota failure remains a historical result, not a requirement claimed achieved.

## Membership and allocation

| Pool | Considered | Propose include | Exclude | Hold |
| --- | --- | --- | --- | --- |
| Original training | 280 | 214 | 35 | 31 |
| Additional reviewed drafts | 244 | 168 | 29 | 47 |
| Saved-source windows | 41 | 20 | 0 | 21 |
| Total | 565 | 402 | 64 | 99 |

No previous reference correction, source-use status, article/passage text or disposition changes. The private design ledger binds each considered ID to source/passage hashes, correction lineage, its prior review and its conservative grouping evidence. The 64 exclusions and 99 holds remain outside the proposed usable pool. Unsupported references remain null and are never counted as empty-location examples. Existing language and six-class conventions remain in force.

| Proposal | Records | English | Taglish | Positive | Empty-location | Guard components |
| --- | --- | --- | --- | --- | --- | --- |
| Proposed training | 345 | 170 | 175 | 242 | 103 | 38 |
| Proposed validation | 57 | 37 | 20 | 30 | 27 | 20 |
| Combined | 402 | 207 | 195 | 272 | 130 | 58 |

The combined candidates come from **149 source articles**: 126 proposed training sources and 23 proposed validation sources. Proposed training comprises 214 reviewed original-training records, 121 additional drafts and ten saved-source windows. Proposed validation comprises 47 additional drafts and ten saved-source windows. Original training records never become validation examples.

Twenty percent of 402 rounds to 80 validation records. All available unanchored eligible components together contain only **57**, so including all of them is the nearest possible count under the preserved constraints: **85.82% training / 14.18% validation**. This ceiling describes this candidate pool and grouping overlay, not every possible segmentation of the saved articles. No event is fragmented or theme relabeled to force the ratio. Actual records retain unset split/admission fields; proposed allocation is separate metadata.

## Historical exposure and unresolved relationships

Bind the recorded training input through launch requests, configuration hashes, preparation/export manifests and the 400-row text-free export provenance. Verify **eight recorded attempts / seven completed runs**: original seeds 0/1, the failed original seed-2 attempt, recovered original seed 2, A seeds 0/1/2 and B seed 0. The six selected original/A runs additionally match the final historical freeze. All eight configurations point to the same frozen **280-record train.spacy**. Hash it without deserializing train/dev/test DocBins; no model is loaded. This establishes configured-input exposure, not reconstruction of individual minibatch visitation.

All 280 historical training IDs anchor grouping, including the **35 now excluded and 31 held**. Anchoring only the 214 reusable records would incorrectly leave one extra candidate available to validation, raising its ceiling to 58. The actual-history rule retains that candidate on the training side. Source, article/event/syndication metadata and exact source/passage hashes also participate in matching. No proposed member matches historical validation/test identity or a recorded nontraining component. These metadata checks do not certify all semantic event independence.

Preserve all **536 inherited dependency edges / 140 closure components**, with 58 components containing provisional members. Every recorded edge is contained within a component; no proposed training/validation component crosses. Existing confirmed relationships and conservative guards stay distinct from claims of a single physical flood. Original source identities and raw spellings remain unchanged.

The private relationship register retains **259 unresolved relationship entries** affecting candidate-containing components, including the previously unresolved within-pool incident identity. These are relationship/admission holds, not 259 additional held passages or newly discovered incidents. Joint allocation contains these relationships but does not resolve their identity. Existing inherited grouping alone is not newly labeled a defect. Admission still needs supported group qualification, which may retain a justified conservative closure without asserting one physical event. Standalone components are not declared independent merely because no edge was found.

## Class, language and flood-role coverage

Counts below are entity spans, not accuracy measurements.

| Label | Train English | Train Taglish | Validation English | Validation Taglish |
| --- | --- | --- | --- | --- |
| ROAD | 155 | 46 | 14 | 0 |
| LANDMARK | 38 | 20 | 5 | 0 |
| LOCAL_AREA | 6 | 13 | 9 | 3 |
| BARANGAY | 34 | 51 | 10 | 7 |
| CITY | 186 | 122 | 8 | 12 |
| PROVINCE | 106 | 63 | 2 | 8 |

**Validation has no Taglish ROAD or LANDMARK spans.** The overall validation ROAD/LANDMARK counts come entirely from English. Taglish LOCAL_AREA support is only three spans in two passages across two conservative components. Training English LOCAL_AREA has six spans across three components. Validation English PROVINCE has two spans across two components. These small slices cannot establish robust generalization. Both languages have genuine empty-location examples: training 38 English / 65 Taglish; validation 17 English / ten Taglish.

| Passage role | Train | Validation | Combined |
| --- | --- | --- | --- |
| observed_flooding | 161 | 27 | 188 |
| warning_forecast | 48 | 4 | 52 |
| recovery | 81 | 16 | 97 |
| prevention_project | 55 | 10 | 65 |

Observed flooding is the largest individual role, but is not a majority of the combined pool. Useful warnings, recovery and prevention remain eligible under the user's scope. These strata describe location-mention training material; presence of an entity does not assert active flooding, passability or a current routing hazard. This design makes no unsupported flood-report-only claim.

| Theme | Train English | Train Taglish | Validation English | Validation Taglish |
| --- | --- | --- | --- | --- |
| compound-crossing-roads | 11 | 2 | 7 | 2 |
| facilities-institutions | 10 | 12 | 7 | 3 |
| geographic-type-ambiguity | 13 | 13 | 7 | 3 |
| historical-not-theme-coded | 108 | 106 | 0 | 0 |
| locality-designators | 3 | 8 | 5 | 3 |
| misleading-names-time-common-words | 10 | 17 | 7 | 4 |
| project-asset-names | 8 | 10 | 2 | 4 |
| shared-identifiers | 2 | 3 | 2 | 1 |
| short-codes | 5 | 4 | 0 | 0 |

The 214 reused original-training examples were not annotated under the additional-theme design and remain explicitly unclassified for those themes. No backfilled theme labels or old-example substitution is used to claim quota completion. There are **zero short-code-theme validation examples in either language**; numeric shared-locality/ellipsis support also remains limited as described by the preceding source review. Full JSON coverage additionally distinguishes passages, spans and conservative component support for each label/language. Guard components are reported as grouping units, never certified independent-event counts.

## Evaluation boundary and remaining gates

The separate fresh test remains **incomplete and unsealed, zero admitted records**. Read only its existing safe aggregate and verification metadata. Its unchanged design is **60 passages, 30 English / 30 Taglish, exactly three genuine negatives per language**. Safe status reports 56 prospective candidates, only 22 Taglish, 41 complete silver references, 15 unresolved references, 14 history-held sources and two source-extent holds. None becomes successor development material.

No fresh text, title, URL, reference label or individual case was opened, and no curator was contacted or spawned. An authorized isolated curator must apply the previous development-exclusion supplement, reconcile actual exposure/event/source-use relationships and complete the existing design before sealing. This task exposes no new source or passage.

Before a training handoff: resolve proposed-member source-use/reference and group qualification; complete the independent final-test boundary; then perform actual admission, grouped freeze, qualified export and desktop configuration/handoff checks as separate tasks. The empty validation slices limit claims and must remain visible; they are not silently filled or declared measured. Saved-only infeasibility must be reported instead of reducing the fresh-test requirements.

## Verification and reproducibility

Shared schema, source-exact Unicode offsets, labels and non-overlap checks cover **565 unchanged proposed records**, with **zero unexpected failures**. Revalidate the prior real tokenizer signatures against their request/worker hashes, all unchanged passage/source hashes, the frozen tokenizer and vocabulary. All **918 proposed-member spans** still align. The one known unaligned draft remains held. This is a provenance-bound alignment recheck, not a claim of a fresh tokenizer execution or any model inference.

**14 adversarial tests pass**, covering fitted-record leakage, the excluded/held-source anchor, group fragmentation, historical nontraining reuse, overlap-triggered holds, incomplete references miscounted as negatives, promotion of the known tokenizer failure, altered correction/use provenance, false admission/freeze, changed historical configuration hashes and invalid Unicode/type/overlap/source text. Aggregate coverage is recomputed from the private ledger, and the proposed allocation is reproduced deterministically.

Verify **1,461 protected files unchanged**, including the predecessor's 1,207 files, its complete private/public proposal packages, original/additional inputs, historical scores and available model/configuration assets. Only the two permitted fresh-curator metadata files are read from that package. A historical wheel is absent from its recorded GPU-model location, but an existing preflight copy matches the recorded SHA-256 exactly; record that equivalent for future handoff mapping without moving or downloading it. Missing paths are not described as unchanged files.

The ignored private `successor-design-20261017-v1` package contains the full membership design, exposure bindings, group proposal, relationship holds, coverage, contract, readiness, checks and reproducible helpers. See [summary](summary.json), [coverage](coverage.json), [design contract](design-contract.json), [readiness](readiness.json), [evaluation boundary](evaluation-boundary.json), [verification](verification.json) and [publication checks](publication-checks.json).

This remains **AI-assisted source-reading silver**, not human gold, measured accuracy or evidence of model improvement. No collection, actual admission, partition freeze, training-format export, inference, training, dependency/API/database change, upload, commit or push occurs.
