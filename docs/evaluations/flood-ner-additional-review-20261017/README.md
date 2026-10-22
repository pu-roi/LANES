# Additional flood NER dataset review and hold reconciliation

> **Last Updated:** October 17, 2026, 12:58 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The additional-dataset review is complete; the next training dataset is not ready.** The review covered all **244 draft passages and 49 complete saved article bodies**, account for all **65 prior new-dataset holds**, and revisit all **33 original training holds**. New-draft recommendations: **166 keep, 2 correct, 29 exclude from the successor core, 47 hold**. Original-hold recommendations: **2 supported corrections and 31 retained holds**. These are separate, future-only AI silver judgments. Original data, all 244 drafts, prior review packages, models, scores, source-use decisions and partitions remain unchanged.

This follows the [original 280-passage training review](../flood-ner-original-training-review-20261017/README.md), the [additional acquisition checkpoint](../flood-ner-additional-dataset-20261016/README.md), the existing [annotation guide](../../guides/flood-ner-annotation-v1.md) and prospective [reference-scope addendum](../../guides/flood-ner-reference-scope-addendum-v1.md). Preserve the [completed experiment](../flood-ner-heldout-test-20261016/README.md). No fresh held-out private texts/labels, model predictions or external sources are opened for this review.

## Source reading and relevance

Read **82,820 characters in 49 full saved bodies** and all **59,436 characters in the 244 draft windows**, checking their **359 existing location spans**. Every draft has exactly one review entry with article and passage relevance separately, exact source/passage hashes, Unicode offsets and evidence, original labels/language, proposed changes if supported, recommendation and rationale. Source capture metadata/body/raw HTML and saved source-use/policy hashes verify. Origin-aware credits and existing mixed-origin holds remain attached. Reading captured article text does not prove that every element of its live webpage was captured; no live collection occurs.

| Dominant role | Full saved articles | Selected draft passages |
|---|---:|---:|
| Observed flooding | 35 | 93 |
| Recovery, relief and aftermath | 10 | 70 |
| Warning/forecast and related weather | 1 | 24 |
| Prevention/projects/explanation | 3 | 28 |
| Adjacent hazards/weather impacts | 0 | 25 |
| Unrelated selected fragments | 0 | 4 |
| **Total** | **49** | **244** |

**The selected articles concern flooding or deliberately related coverage; some selected windows still fail the flood-focused core criterion.** Four fragments concern promotional endings or TNVS franchise queues. Twenty-five concern landslide clearance, falling rocks/trees, waves, power disruption or other impacts without a useful selected flood link. Excluding these is a prospective sampling recommendation, not proof that their location annotations are wrong. No source is rejected solely for age, and a flood-focused headline does not approve every paragraph.

The user chose to retain useful warnings, recovery and prevention coverage. Locations remain entities even in forecasts, denials and history. A negative reference means **no named in-scope six-class location**, not absence of flooding. Regions, island groups, countries, water bodies and agency-only geographic substrings stay outside this profile. Opinion, insurance assertions, engineering explanations and causal allegations retain their attributed role; this review does not independently verify them or offer legal/medical/engineering advice.

## All holds accounted for

| Prior hold set | Resolved under existing rules / supported correction | Excluded from core with reference questions unresolved | Retained hold | Total |
|---|---:|---:|---:|---:|
| Additional drafts | 8 | 12 | 45 | 65 |
| Original training | 2 | 0 | 31 | 33 |

The new-draft review also flags **2 formerly candidate passages** for unsupported bare-town types, producing **47 current held drafts**. The 65 earlier records contained **67 reason entries** because some had more than one hold. Every reason is separately accounted for; resolving language or one physical-asset referent does not clear a separate place-type or source-use question.

- **Eight additional holds resolved:** four shared-designator cases and four operational-language cases. Two town-list passages need exact first-span boundary corrections; two other shared-designator references were already correct. Common lexical material such as a productive English verb or noun inside Filipino syntax supports the existing operational language rule; proper names or source attribution alone do not.
- **Two original holds resolved through proposals:** classify an almost entirely English passage with isolated `yung` as English, and remove LANDMARK from a foundation acting as a care organization. Its separate physical building reference does not turn the organizational occurrence into a landmark. Original annotations remain frozen.
- **Remaining type/scope questions:** bare settlements, district/locality roles, generic town suffixes, physical facility versus organizational references, and interchange taxonomy remain unresolved where the existing conventions or saved evidence do not settle them. No new taxonomy or map identity is invented. A proposal changes the reference only in the separate review package.
- **Source-use holds:** all **six affected passages from two mixed-origin sources** remain held. Existing source-use dispositions and their limitations are preserved, with six unique saved policy-artifact hashes checked. This is verification of existing evidence and decisions, not a new legal conclusion, correspondence requirement or admission.
- **Tokenizer hold:** the known LOCAL_AREA span remains semantically supported but fails the unchanged frozen tokenizer's strict boundary check. Preserve it as a hold; do not shorten a correct source span or rewrite punctuation/text to pass alignment.

There are **five separate draft proposal records**: two new-draft boundary corrections, one partial language correction on a still-held new draft, and the two original-hold corrections. The partial proposal reclassifies one previously Taglish passage as Tagalog, while its separate type hold remains. Prior partial proposals on original holds are retained in their original review package; they are not silently applied or replaced. All new proposals are research-only, incomplete/draft, unsplit and unadmitted.

Held and excluded references have `expected_entities=null`, `allow_definitive_scoring=false` and `is_negative=false`. Candidate review entries also disable definitive benchmark scoring. These are **Codex source-reading silver references**, not independent human gold or empirically measured improvements.

## Candidate coverage and event relationships

After this review, **168 new passages qualify for further consideration: 84 English / 84 operational Taglish**, consisting of **70 positive and 98 empty-location passages**. Their **164 spans** are CITY 57, PROVINCE 44, BARANGAY 27, ROAD 24, LANDMARK 12 and **LOCAL_AREA 0**. These are reviewed candidates, not admitted training data. All 49 represented sources are still GMA; publisher concentration remains.

The proposed 240-passage theme/language design cannot be filled: capping current candidates at fifteen per existing theme/language cell gives a capacity of **154**. Many candidates are empty-location examples; a theme title alone does not supply positive rare-class coverage. No negative ratio is asserted to be universally correct. Existing original/new holds and the already captured pending-source pool must inform the following membership/coverage decision; automatically appending all drafts would not solve the LOCAL_AREA gap.

The review reconciles all **75 previously flagged original-source/new-event-component links across 16 components**. Distinguish explicit related reporting/storm aftermath from date-only weather candidates, inherited conservative groups and broad components spanning different storms. Confirmation means a supported relationship between reports, **not identical physical flooding, duplicate evidence or independent authentication**. Original and additional component memberships remain unchanged; joint grouping must be resolved before a new split.

Named Carina/Habagat, Ulysses, Egay, Maring and Tisoy source evidence supports related reporting in the directly compared sources. The November component combines Tino/Cebu and Uwan/Cagayan: only the Tino subcomponent relationship is confirmed, and the storms must retain different identities. July–September monsoon/project stories remain a broad group needing subreview. Dates alone cannot establish one event, including the January and May candidates.

Two within-new relationships receive explicit decisions. NLEX Wednesday/Thursday reports are related flood-traffic updates with changing lane conditions and raw exit-name spelling differences. Two Angeles accounts of a 25-year-old manhole/drain death differ in road/location and victim details; **do not merge them without further evidence**. Identical age or similar headlines do not establish incident identity.

Exact/normalized passage equality and canonical article keys find no within-new or cross-pool duplicates. Near-match screening finds none above the recorded thresholds: five-word passage shingles with twelve shared and at least 0.35 containment; twelve-word source shingles with twelve shared and at least 0.25 containment. These are screening results, not a proof of event independence. Full original/new grouping ledgers remain necessary; no article, event or syndication group is split to satisfy counts.

## Verification and next task

Fresh shared schema/record checks cover **282 records: 244 drafts, 33 original held records and 5 proposals**. There are **zero unexpected failures**. The **one known unaligned draft span remains explicitly failing and held**. All **29 proposal spans** and **187 original-held spans** strictly align. The existing Python 3.11/spaCy 3.7.5 CPU environment loads static vocabulary and the frozen tokenizer only; serialization remains byte-identical. No trained neural pipeline components, predictions or optimizer updates are loaded/run. This is not a model-accuracy evaluation or CPU-training benchmark.

Guard scenarios reject a missing/duplicated review ID and an invalid changed entity offset. Preserve **1,174 snapshotted files**, verify all **52 original admission hashes**, all **565 additional-development manifest hashes**, and **66 files across six selected models** plus frozen configurations. Counts overlap and are not additive. The prior original-training review package remains byte-identical. Original scores/reference labels and the fresh-test isolation boundary remain intact. See [aggregate summary](summary.json), [verification](verification.json) and [publication checks](publication-checks.json).

**Next task:** decide successor membership using the two completed reviews, explicitly address positive LOCAL_AREA and theme coverage, reconcile remaining group/hold constraints, and complete a separate independent sealed test before export. Unresolved references may remain excluded; review completion does not promise every hold is resolvable from saved evidence. The next corpus size is not determined by these counts. Preparing its separate desktop GPU export/configuration follows that decision. Training remains desktop-only; the laptop handles preparation.

No new collection, data replacement, admission, partition freeze, export, training, model inference, deployment, commit or push occurs. Public APIs, dependencies, ORM and migrations are unchanged. Private source text, evidence, reference labels and proposed records remain in the ignored `backend/training/flood_ner/artifacts/additional-review-20261017-v1/`; public deliverables contain aggregates only. Assembly scripts reproduce the authored decisions and validation, not independent semantic adjudication.
