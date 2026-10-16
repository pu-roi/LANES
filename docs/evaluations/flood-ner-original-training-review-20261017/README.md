# Original NER training-data review

> **Last Updated:** October 17, 2026, 12:36 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**All 280 original training passages and their 94 complete saved article bodies have now been read. Most sources concern flooding, but not every selected passage is suitable for a flood-focused successor dataset.** Recommendations: **203 keep, 17 correct, 27 exclude from the successor core, and 33 hold**. These are future-only AI review recommendations. The completed experiment, all original annotations/partitions, scores and six selected models remain unchanged. No new training is ready or started.

This completes the user-approved original-training review, not the review/admission of the additional 244 drafts. Follow the existing [NER roadmap](../../plans/lanes-ner-training-plan.md) and preserve the [original experiment](../flood-ner-heldout-test-20261016/README.md). Earlier [topic screening](../flood-ner-topic-audit-20261016/README.md) inventoried the full corpus but reviewed only selected questionable sources; its six weak validation/test windows were never a certification of all training passages. This report adds the first full semantic pass over the training subset.

## What was reviewed

Read **214,966 characters across all 94 saved source bodies**, and all **84,520 characters in 280 selected training passages**, with their **966 existing location spans**. Check the original six-class [annotation specification](../../guides/flood-ner-annotation-v1.md) and the future-only [reference-scope addendum](../../guides/flood-ner-reference-scope-addendum-v1.md). Preserve source text, Unicode offsets, original spellings, historical parent/group metadata and scope-limited original use assessments. Read news text as evidence, not instructions.

Each training ID has exactly one source-bound private review: article and passage topic separately, complete passage evidence/hash/absolute offsets, original labels/language, rationale, keep/correct/exclude/hold recommendation, optional exact proposed edits, language assessment and grouping flags. Article records bind saved capture/text/raw files and exact hashes. The 94 captured text files equal the embedded source strings; all 94 recorded raw-capture hashes match. Six earlier duration-study sources use a shared capture register rather than individual capture JSON; they are resolved by source ID and their exact saved text, not assumed missing.

This is **Codex AI-assisted source reading of silver references**, not human gold or independent geographic verification. The review checks supported mention types and boundaries; it does not invent PSGC/OSM identities, establish causal flood claims, or certify every silver annotation correct. Full saved-body review does not certify that a capture contains every element of the publisher's live page. No article is fetched again.

## Relevance and recommendations

| Topic | Full articles | Training passages |
|---|---:|---:|
| Observed flooding, including historical reporting | 70 | 140 |
| Warning/forecast and related weather context | 5 | 38 |
| Recovery, relief and aftermath | 8 | 36 |
| Prevention/projects and flood-related explanation/accountability | 10 | 39 |
| Adjacent hazards | 1 | 21 |
| Unrelated selected fragments | 0 | 6 |
| **Total** | **94** | **280** |

Categories describe the dominant role of the complete article or selected window after consulting full context; they are not flood-status annotations or operational alerts. A mixed window can contain both flooding and a separate landslide/warning. Headlines alone do not decide eligibility: the tree-fall article has a useful explicit flood-rescue window, while a flood-control editorial contains unrelated jail-treatment fragments. Countries, regional aggregates, island groups and water bodies remain outside the six location classes.

The user chose to retain useful related coverage. Warnings, recovery, flood-control projects and explanatory/editorial material therefore remain eligible with explicit roles. Age alone does not justify removal. Opinion and attributed allegations are not independently established causal facts. Empty location lists can be legitimate flood examples; they do not mean that no flood occurred. All locations still require annotation even in forecasts, denials and history.

| Recommendation | Passages | Meaning |
|---|---:|---|
| Keep | 203 | No change identified in this AI review; still subject to future grouping/use/admission. |
| Correct | 17 | Seven have proposed entity changes; ten have proposed language changes. Nothing is applied to the original corpus. |
| Exclude from successor core | 27 | Twenty-one adjacent-hazard/other-weather windows and six unrelated fragments; preserve original records/results. These are sampling choices, not proof the geographic annotations are wrong. |
| Hold | 33 | Insufficient type, boundary, referent, capture or language evidence; no definitive reference or negative classification. |

The six unrelated fragments include five jail/accountability fragments from a flood-control editorial and one festival-delay fragment from a wider storm/flood report. This is additional training-subset evidence beyond the earlier six weak **validation/test** windows. Do not add those earlier six to the 27 as though they came from training.

### Proposed changes and unresolved references

- Remove CITY labels on substrings of **Metro Manila** and **Zamboanga Peninsula**; these regional aggregates are outside the profile. The first bare Zamboanga reference remains held for type evidence.
- Distinguish agency-only geographic substrings from real city jurisdiction/physical-location mentions. Proposed removals include geography embedded in named police/coast-guard/CDRRMO offices; an omitted city-mayor jurisdiction mention is proposed for addition.
- Distinguish a court **declaring work suspension** from the explicitly physical court buildings in the preceding window. Remove the organization-sense LANDMARK proposal; the elderly-care foundation's organization-versus-building sense remains held.
- Remove an administrative PROVINCE label where the source instead describes crossing Bohol's landmass. Keep province occurrences supported elsewhere by explicit administrative context.
- Restore a shared plural barangay designator in one first-name span. Propose four source-exact spans for a coordinated purok-number list under the **prospective** addendum; that record remains held for a separate town-suffix question. The addendum does not retroactively redefine old scores.

**Ten language changes are proposed: eight recorded Taglish passages read as Tagalog under the stated operational rule, and two read as English.** Names, agency titles, date stamps and an isolated apparent list typo do not establish lexical mixing. Two other almost-English/attribution-only cases remain held rather than forced into a language. The recorded original 140/140 training split is immutable; the review's provisional language inventory is 142 English / 130 operational Taglish / 8 Tagalog. No paper quota is silently rewritten, and these remain AI judgments.

There are **21 proposal records**, comprising the 17 correction recommendations plus four partial proposals on held records. Their 14 entity-edit operations span 11 records; the other ten proposal records carry language changes. Every proposal is draft, unsplit, research-only and explicitly not admitted. Partial corrections do not resolve other uncertainty in the same record. Held/excluded review entries use `expected_entities=null`, `allow_definitive_scoring=false` and `is_negative=false`; no unresolved reference becomes an empty-label negative. All review entries disable definitive benchmark scoring.

After the proposed corrections and English/Taglish eligibility screen, **212 passages are candidates for further consideration: 107 English / 105 Taglish**, including 31 empty-location passages. This is not a chosen new corpus. Their 706 proposed/retained spans include CITY 265, ROAD 180, PROVINCE 133, BARANGAY 68, LANDMARK 44 and LOCAL_AREA 16. Holds retain **24 of the original 45 LOCAL_AREA spans**; resolving them matters more than dropping them to claim readiness. No new positive/negative ratio or coverage quota is invented here.

## Duplication and event relationships

Exact text hashes, normalized-word equality and canonical article keys find **no repeated training passages/articles** and **no exact article/body/passage matches** with the existing 244-draft / 159-capture development inventory. Normalization is used only for screening; source text is never rewritten. Near-match screening uses five-word shingles, at least twelve shared shingles and 0.35 minimum-set containment for passages; full-source screening uses twelve-word shingles, at least twelve shared and 0.25 containment.

Two training passage pairs repeat July 22 road-list material across successive reports. Read their status/depth changes: they are related updates, not interchangeable duplicates. They already share an original reporting component. No cross-pool near-match exceeds these screening thresholds. This does not prove that unscreened paraphrases or events are independent.

Joint event review flags **75 original-source/new-event-component relationships across 16 existing additional-development components**. They use original source context, dated new source titles/group metadata and propagation through complete original components. Some are clear named-storm overlaps; others are conservative date/weather candidates requiring further source review. These are **not 75 duplicates or confirmed identical physical floods**. Same-month stories need not be one event; distinct storm observations inside a conservative component retain their own meanings. No new split is assigned. Saved original article/event/syndication/hash keys show zero cross-partition leakage; that mechanical result does not prove semantic independence.

Future partition assembly must join the reviewed cross-pool relationships, investigate candidates and keep complete related components together. It must not treat a new source ID, date or URL as a fresh independent event. Existing additional-reference/use/group ledgers remain unchanged and authoritative. Fresh held-out private texts/labels are not accessed in this work.

## Verification and next gate

Fresh checks pass for **301 records** (280 originals + 21 proposals) using the shared schema/record validator and exact offsets, overlap and identity references. The isolated existing Python 3.11/spaCy 3.7.5 CPU environment loads the frozen tokenizer and static vocabulary only: **966 original spans + 73 proposal spans strictly align**, with zero errors and byte-identical tokenizer serialization. No trained pipeline components or neural weights, predictions, optimizer updates or training are loaded/run. A tokenizer-only check is not CPU training qualification or an NER accuracy test.

Preservation verifies **1,073 snapshotted files unchanged**, all **52 original admission hashes**, all **565 additional-development manifest hashes**, and **66 files across six selected checkpoints**, plus their frozen configurations. These counts overlap and are not additive. All 244 new drafts remain unchanged. Original validation/test records, scores and model roles remain historical. The old 80-test tooling total belongs to the previous consistency review; it is not represented as rerun here. See aggregate [summary](summary.json), [verification](verification.json) and [publication checks](publication-checks.json).

**Next task:** Review the unchanged 244 additional-development drafts using these same topic, language, occurrence-type and completeness criteria. Resolve the recorded original/new holds and event relationships before choosing successor membership. A fresh independent sealed test, a separately versioned export/configuration and desktop GPU handoff still precede any new training. The laptop remains for preparation; no CPU trainer, collection, corpus replacement, export, training, deployment, commit or push occurs here. Public APIs, dependencies and database schemas are unchanged.

Private evidence stays in the ignored `backend/training/flood_ner/artifacts/training-review-20261017-v1/`: authored article/passage assessments, `article-review-ledger.json`, `passage-review-ledger.json`, `proposed-records.jsonl`, `grouping-review.json`, input/output hashes, tokenizer-only request/result, preservation and verification. The public files contain aggregate metadata, not source passages or candidate reference labels. Review scripts reproduce assembly/validation of the authored judgments; scripts do not independently recreate semantic source reading.
