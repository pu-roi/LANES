# Flood NER editorial review and research-paper alignment

> **Last Updated:** October 14, 2026, 2:31 PM (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** AI-assisted editorial preparation completed; research-team manual annotation, source admission and split freezing remain pending.

The developer authorized the next preparation step and supplied [LANES_Original](https://docs.google.com/document/d/1FCtFhJ-cFm-m_gxdgGAf61WLJbY8_98iReSIyZ68_LA/edit). Read its methodology through an authenticated, read-only browser DOCX export; the shared document was not edited. The methodology specifies **400 total manually annotated English/Taglish samples: 280 training, 60 validation, 60 testing**. Location-entity NER and rule-based severity evaluation are separate. In this document, Chapter II is Methodology, Chapter III is Results and Discussion, and Chapter IV is Conclusion and Recommendation. This evidence resolves the earlier training-only versus total-dataset question and supersedes the provisional 400-training-plus-holdout interpretation.

[paper_reference.json](paper_reference.json) records the inspected paragraph hashes, export hash, source URL and requirement interpretation. The original export stays under ignored artifacts; no Google revision ID is claimed. Public-data collection and planned institutional ethics review are described, but the inspected sections do not supply a publisher training-use grant or an already completed institutional assessment. This is a record of missing evidence, not a legal determination or a requirement to contact a publisher automatically.

## Delivered review

Read all 100 complete frozen article bodies, rather than only their earlier 1,800-character draft windows. Recorded per-source selection/exclusion offsets, hashes, reasons, passage-language decisions, review identity and source-context warnings. Original captures, the 100-article register and earlier queues remain intact. The separate offline review-passages command validates these decisions against inventoried source identities before creating ignored context blocks; it accesses no operational database or publisher write interface.

| Measure | Result |
|---|---:|
| Complete article bodies inspected / source-accounting validation | 100 / 100 |
| AI-assisted editorial review records | 100 |
| Source-exact contiguous context blocks | 113 |
| English / Taglish / Tagalog / unknown blocks | 45 / 33 / 34 / 1 |
| Blocks compatible with the paper's language scope | 78 |
| Excluded interface / metadata / caption / related-story ranges | 24 / 22 / 4 / 10 |
| Blocks requiring sibling/source context before standalone sample admission | 22 across 9 articles |
| Sources shortlisted for a research-team manual pilot | 12 |
| Completed entity annotations / training-admitted samples / assigned splits | 0 / 0 / 0 |

These are editorial context-block counts, not independent training-sample counts or an accuracy benchmark. A related-story/ad interruption can create several blocks from one article. Such fragments retain sibling IDs, complete source text/hash and a cross-block hold; they must not be padded into the 400-sample dataset. Neither English/Taglish compatibility nor an AI editorial review constitutes research-team manual annotation.

## Findings and corrections

- Restored the reporting context beyond all 43 earlier truncated windows. Two previously omitted numbered-locality sources now expose Purok 12 in Villa Luna, and Sitio 6 plus Purok 1–2/Purok 6 in the long August 17 list. [Audit pointers](audit.json) preserve exact source/hash offsets. Complete long sections still need contextual selection before final annotation/model use.
- Excluded advertising, sharing controls, metadata, footer prompts, duplicate lead photo captions and ten related-story ranges. GMA July 10/August 8 lists contained August 29/30 widget headlines; these are not evidence of the lists' own event. Interrupted city/list scope remains explicit instead of joining text or borrowing headings silently.
- Retained credited embedded reporting and substantive bilingual quotes. Removed lead captions remain captured evidence; inline graduation and Manila road-list captions have explicit origin notes. Future facts must distinguish caption/post support from narrative support and repeated observations.
- All five RMN bodies are Tagalog, despite the frozen article register's English tags. The reviewed passage layer records the correction; the historical register's article-level counts remain a checkpoint and must not be reused as final dataset-language counts. English articles with substantive Filipino quotations become Taglish at passage level. Philippine names and ordinary borrowed technical terms alone do not change a Tagalog passage to Taglish.
- One Davao article includes regional-language quotations not represented by the v1 language vocabulary; retain unknown and an unsupported-language hold. Do not force it into the paper's English/Taglish totals.
- The corn-height phrase hanggang tuhod describes plant height, not water depth. Retain its measurement-role warning. Also recorded an inconsistent nine-versus-ten barangay list and Wednesday/Thursday chronology without correcting the source or inventing an observation date.
- [Event findings](event_findings.json) record source-backed causal storm names missing from or incompletely represented by earlier provisional groups. July 22 early/later MMDA updates, AFP attribution, embedded-post duplicates and shared storm episodes still require article/event/syndication review. No group or train/dev/test membership was frozen.
- Eight earlier keyword cues came from excluded widgets/captions/metadata. [Cue dispositions](cue_dispositions.json) explain those exclusions rather than treating them as reviewed facts or silently losing them.

## Manual annotation handoff

[manual_pilot_shortlist.json](manual_pilot_shortlist.json) identifies twelve sources covering English/Taglish, shared headings/clocks, local overrides, depth versus gauges/rainfall, vehicle access, recession, numbered localities and parent distinctions. It is a selection proposal with all admission holds retained, not twelve labeled examples. Full context is in ignored backend/training/flood_ner/artifacts/editorial-20261014/reviewed-context-v3/context_blocks.jsonl.

1. Research-team annotators inspect the unchanged complete source and confirm passage language/bounds. Use sibling context for interrupted passages; choose a final contiguous sample with enough attribution and headings. Never concatenate disjoint source slices or inherit an omitted observation time.
2. Resolve the recorded training-use basis and article/event/syndication groups. Keep unknown provenance and unsupported language explicit; the two legacy original-capture gaps remain.
3. Manually annotate location entities using the [annotation guide](../../guides/flood-ner-annotation-v1.md), preserving raw spelling and parent uncertainty. Depth/time/status/access evidence is a separate contextual/reference layer; the paper's primary NER model must use location labels rather than severity classes. A qualified location-only export/training profile remains to be implemented before training; existing eight-label rich exports must not be mistaken for that profile.
4. Review the pilot and validate source-exact offsets/token alignment and semantics. AI-suggested labels remain silver unless the required independent review is established. Record actual human annotators/reviewers; this editorial packet is not that evidence.
5. Expand selection/collection for measured coverage, then freeze **400 accepted samples with 280/60/60 group-preserving partitions**. If current group/sample choices prevent exact counts, revise selection or gather independent sources; never split a related event merely to hit percentages. Do not tune against the 60-test holdout.

Report methodology in Chapter II, actual dataset/evaluation evidence in Chapter III, and conclusions grounded in those results in Chapter IV. The supplied document also retains a 60–100 baseline-testing proposal and constructed 50-input rule results; those are different datasets/results and need reconciliation before claiming completion of the new 400-sample trained-model evaluation.

## Verification and remaining work

The final focused suite passed **396 checks in 27.45s**, including 18 editorial checks; [audit.json](audit.json) records verification. New checks cover complete source accounting, corrupted identity/hash/bounds, overlapping/lost ranges, LF/CRLF preservation, deterministic output, overwrite/path guards, source binding, regional/Tagalog scope, explicit AI-versus-human status, auditable excluded cues and refusal to treat context blocks as annotations. The real CLI reproduces all five packet files byte-for-byte from the saved decisions, and all 100 reviewed article/file/publication pointers remain valid.

No model was selected, installed, trained or deployed. No runtime parser, API/UI, SQL schema, dependency manifest, operational records or shared Google document changed. The [roadmap](../../plans/lanes-ner-training-plan.md) and [task plan](../../task_plan.md) track remaining reuse/manual annotation, grouping, source coverage, location-only export, 400-sample completion and model qualification work.
