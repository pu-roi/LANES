# Flood NER successor dataset proposal from saved articles

> **Last Updated:** October 17, 2026, 1:55 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The saved-article proposal is complete; training readiness remains open.** Read all **91 remaining saved development bodies / 219,454 characters**, reconcile the original-training and additional-draft reviews, and account for **565 considered records**. Recommend **402 provisional inclusions, 64 exclusions and 99 holds**. These are research proposals, not an admitted replacement for the original 400-record experiment.

The user selected **saved articles only**. No discovery, live fetch, new capture, admission, partition freeze, training-format export, model prediction, training, correspondence, commit or push occurs. The laptop handles review/preparation; training remains a later desktop GPU task. Public APIs, dependencies, database schemas and migrations are unchanged.

This builds on the [original training review](../flood-ner-original-training-review-20261017/README.md), [additional review and hold reconciliation](../flood-ner-additional-review-20261017/README.md), [acquisition checkpoint](../flood-ner-additional-dataset-20261016/README.md), existing [annotation guide](../../guides/flood-ner-annotation-v1.md) and [scope addendum](../../guides/flood-ner-reference-scope-addendum-v1.md).

## Proposed membership and correction precedence

| Pool considered | Considered | Propose include | Exclude | Hold |
|---|---:|---:|---:|---:|
| Previously reviewed original training | 280 | 214 | 35 | 31 |
| Previously reviewed additional drafts | 244 | 168 | 29 | 47 |
| New windows from saved development sources | 41 | 20 | 0 | 21 |
| **Total** | **565** | **402** | **64** | **99** |

Each considered record has exactly one disposition, full source/passage identity, hashes, exact evidence offsets, rationale, correction lineage, language, reference status and grouping guard. Original review proposals take precedence over historical annotations, followed by the latest supported hold corrections. Prior partial corrections remain partial: they do not clear separate missing-reference questions. The original training contribution grows from 212 eligible review candidates to 214 after the two supported hold corrections. Its 35 exclusions comprise 27 topic exclusions and eight passages reviewed as Tagalog rather than English/Taglish.

Only the **280 historical training records** are candidates for original reuse. The historical 60 validation and 60 test memberships are excluded by ID and article/passage metadata; no contextual pair or constructed fixture becomes an extra sample. Exact checks find no proposed overlap with those nontraining identities. That metadata result does not certify every possible historical event relationship.

All proposal records are **draft, incomplete, research-only and unsplit**. Every membership disables definitive benchmark scoring. Held/excluded references are `null`, never empty-location negatives; partial known spans remain diagnostic only. Case-specific future source-use adoption and corpus admission are still separate gates. Previously adopted decisions are preserved rather than extended to unrelated sources or new uses.

## What the 91 saved sources add

The 91-body inventory reconciles exactly with the acquisition checkpoint's pending-source screen. Article roles are **46 observed flooding, 19 recovery, 21 prevention/project/explanation and five warning/forecast**. All concern flooding or deliberately eligible supporting coverage; selected-window relevance still requires its own judgment. No source is rejected solely because it is old.

Full-body reading yields **41 proposed windows**, of which **20 are provisionally eligible and 21 held**. Sixteen sources supply those 20 eligible windows. The source-level outcomes are 16 selected, 39 held opportunities, 26 not selected and ten with main reporting outside the English/Taglish scope. Nonselection does not mean an article is unrelated or has no entities. The review targets missing phenomena instead of generating a passage from every paragraph.

The 20 new candidates are **15 English / five operational Taglish**, all positive location examples. They provide **47 spans**, including **14 LOCAL_AREA**: ten in English and four in Taglish. Explicit named/numbered sitios and puroks, including one supported English shortened numeric coordination, add coverage. The Taglish shared-identifier cell still has **no LOCAL_AREA spans**; administrative shared-name lists cannot substitute for numeric locality ellipsis.

Some promising reports use Cebuano or Hiligaynon with borrowed English. They are not silently reclassified as Filipino Taglish. Eligibility is checked per selected passage; these source-level main-language flags do not prohibit a separately reviewed English quotation/table window. Numbered barangays remain BARANGAY; household counts, engineering chainages, project numbers, monetary amounts, times and legal article/decree numbers are not locality or road-code entities. Unclear residential compounds, ramps, bare settlements and proposed-asset/title references remain held under existing conventions. No new taxonomy rule or geographic identity is invented, and raw spelling is preserved.

Captured bodies can contain embedded posts, translations, navigation or later related-story headings. Full captured text was read, but only contiguous main-story windows were proposed. Duplicate adjacent translations, traffic analogies in an explanatory interview and unrelated hazard fragments were not used to fill flood-core quotas. This does not certify that every element of a live webpage was captured.

## Source origin and use remain explicit

All 91 sources receive a separate source-use proposal with capture/raw hashes, attribution, whole-copy and selected-window amounts, policy bindings where applicable, purpose and limitations. Routes are **44 GNO selected-text proposal routes, 27 RMN basis holds, 16 mixed-origin/working-copy holds and four regional-path scope holds**. These are mutually exclusive summary routes; a source may have additional recorded reasons.

Six newly checked raw cover captions exposed independent credits absent from some extracted bodies, including official, company and user contributions. Those six source proposals retain working-copy holds. Official origin alone is not treated as proof of a public-domain or computational-use basis. No image/video bytes become training examples. The saved GNO policy is not automatically extended to RMN, a regional-TV path or third-party text/media.

The 20 provisional windows have a **proposed** selected-publisher-text private research basis using the saved GNO evidence and existing delegated rationale. Computational applicability remains an explicit project inference, not publisher AI permission, independent legal adjudication or actual admission. Full working-copy extent remains separately recorded. No previous source-use decision changes, and no publisher message is sent. These limitations do not imply that correspondence is always required to establish a supported basis.

## Coverage and grouping feasibility

| Provisional pool | English | Taglish | Empty-location passages | LOCAL_AREA spans |
|---|---:|---:|---:|---:|
| Reused original training | 108 | 106 | 32 | 17 |
| Reviewed additional drafts | 84 | 84 | 98 | 0 |
| Newly proposed saved-source windows | 15 | 5 | 0 | 14 |
| **Combined candidates** | **207** | **195** | **130** | **31** |

The 402 provisional candidates contain **918 spans**: CITY 328, ROAD 215, PROVINCE 179, BARANGAY 102, LANDMARK 63 and LOCAL_AREA 31. The combined pool has 272 positive and 130 empty-location passages. These counts describe reviewed silver candidates, not a selected training corpus or measured model improvement. The additional candidates remain concentrated in GMA sources.

The **additional** development pool contains **188 candidates: 99 English / 89 Taglish**, with 90 positives and 98 empty-location examples. The 240-passage design still requires 15 in each existing theme/language cell:

| Theme | English candidates | Taglish candidates |
|---|---:|---:|
| Compound/crossing roads | 18 | 4 |
| Short road codes | 5 | 4 |
| Locality designators | 8 | 11 |
| Shared identifiers | 4 | 4 |
| Facilities/institutions | 17 | 15 |
| Project/asset names | 10 | 14 |
| Geographic type ambiguity | 20 | 16 |
| Misleading names/time/common words | 17 | 21 |

Capping each cell at 15 gives an upper bound of **169 slots**, up from 154 before this proposal. **At least 71 cell-specific slots remain missing**, and both locality-designator language cells lack their required genuine negative. Excess cases in other cells cannot fill these gaps. This is the bound for the **current proposed candidate pool**, not an exhaustive mathematical maximum over every possible segmentation of the 91 articles. Do not relabel themes, substitute old training examples for the additional quota or manufacture easy negatives.

Necessary cardinality conditions already fail, so a grouped **192 training / 48 validation** allocation with **96/96 training and 24/24 validation languages** is infeasible from this proposal. No allocation or partition freeze is attempted. The full coverage table also records positive and negative support, preventing a nominal theme total from hiding missing rare phenomena.

Reconcile all **75 inherited cross-pool relationships**, add **nine source-reading report-series assessments**, and retain **126 conservative cross-pool shared-storm-reference guards**. Explicit related reporting, changing forecasts, project-investigation series and uncertain monsoon sequences have different recorded roles. Shared storm names within publication year may be historical references; they do not certify one physical flood. Different storms, roads, project sites and observation times retain their own identities. Legacy null source timestamps remain null; preserved publication-date metadata supports comparisons where available.

The conservative overlay contains **140 components, 58 with provisional candidates**. No exact metadata link to historical nontraining source components is observed; incomplete history and unresolved semantic relationships remain limitations. Existing groups/partitions are unchanged, and standalone proposal nodes do not certify event independence.

There are no exact/normalized passage duplicates, article aliases or exact/threshold-near source-body pairs in the reviewed comparison. Two near-passage matches are the already reviewed original MMDA formula/list pairs. Retain their different status/time/list context under a shared guard; neither is a newly proposed window. Five-word passage screening uses at least twelve shared shingles and 0.35 containment; twelve-word body screening uses twelve shared and 0.25 containment. Threshold screening is not proof of independence. Historical nontraining material was compared through metadata only, without opening its texts/labels for new near-match decisions.

## Independent evaluation boundary and verification

Read only the existing curator's safe aggregate and verification metadata. It remains **incomplete and unsealed: zero admitted test records**, 56 prospective candidates, 41 complete silver references, 15 unresolved references, 14 history-held sources and two third-party extent-held sources. Only 22 candidate passages are Taglish. Its existing **60 records / 30 English + 30 Taglish / exactly three negatives per language** design is not satisfied. No curator was appointed/contacted and no fresh held-out text, title, URL or label was opened.

A separate metadata exclusion supplement records all newly read development sources, new passage hashes and grouping bindings. An authorized isolated curator must incorporate these exposures and resolve actual history/event/source-use questions before sealing a test. The supplement is not a seal or a claim of independent gold.

Fresh shared schema/source-exact Unicode/non-overlap checks cover all **565 proposal records**, with **zero unexpected validation failures**. The **one known draft tokenizer failure remains held**. All **111 spans across 41 new windows**, and all **918 provisional-member spans**, strictly align with the frozen tokenizer. The existing Python 3.11/spaCy 3.7.5 CPU environment loads static vocabulary/tokenizer only; no neural pipeline, model prediction or optimizer update runs.

Seven guard scenarios reject duplicate/missing IDs, historical nontraining membership, nonexact Unicode spans, unsupported labels, overlapping entities, rewritten source windows and held references miscounted as negatives. Verify **1,207 protected prior files**, both safe curator metadata files, all **52 original admission hashes**, all **565 additional manifest hashes** and **66 files across six selected models** plus frozen configurations. Counts overlap. Prior datasets, scores, tokenizer, reviews and source-use decisions remain byte-identical.

See [aggregate summary](summary.json), [coverage feasibility](coverage-feasibility.json), [verification](verification.json), [evaluation boundary](evaluation-boundary.json) and [publication checks](publication-checks.json). Source text, exact references, source-use proposals, group evidence and scripts remain in the ignored `backend/training/flood_ner/artifacts/successor-proposal-20261017-v1/` package. This is **AI-assisted source-reading silver**, not human verification, an accuracy result or proof that retraining will improve the model.

**Readiness decision:** do not admit, freeze partitions, export or retrain this proposal. A following decision must address the recorded coverage and source-use/reference/group constraints under the saved-only limit and complete the independent evaluation boundary. Do not silently relax the design or reopen collection. A separate desktop handoff follows only after those gates have supported dispositions.
