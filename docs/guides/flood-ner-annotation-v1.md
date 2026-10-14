# Flood NER annotation specification v1

> **Last Updated:** October 14, 2026, 6:17 PM (Asia/Manila)

**Passage language and cohort:** AnnotationRecord.passage_language is separate from source.language and defaults to unknown for older records. Review language from the unchanged passage. The current research operational Taglish category includes Filipino clauses with untranslated English common/technical lexical material; names alone do not establish mixing. Record lexical-borrowing uncertainty and do not claim independent language adjudication. [Actual cohort](../evaluations/flood-ner-corpus-400-20261014/README.md) records publisher/language confounding, source-scoped taxonomy and frozen research partitions; complete location labels do not complete contextual facts.
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Offline contract with a delivered AI pilot and 400-record silver location cohort; no trained model or independent gold verification.

The annotation unit is a contiguous passage from frozen captured text. Include enough surrounding headings, list entries, attribution and chronology to interpret shared facts. Use half-open Python Unicode character offsets (`start` inclusive, `end` exclusive), not byte or JavaScript UTF-16 offsets. Preserve accents, punctuation, whitespace and spelling. Passage offsets refer to the complete source; entity and evidence offsets refer to the passage. Store exact text alongside offsets and SHA-256 values. Never edit captured wording to make a span align.

## Research-paper profile and editorial handoff

The supplied paper describes 400 manually annotated English/Taglish examples split into 280 training, 60 validation and 60 testing samples. The developer later authorized Codex to perform annotation; the [AI pilot](../evaluations/flood-ner-ai-pilot-20261014/README.md) records that actual method as silver AI labels, with paper-method reconciliation pending. Its primary NER task is location recognition; severity mapping is a separate rule-based evaluation. AnnotationRecord.annotation_profile defaults to context-rich-v1 for backward compatibility. location-only-v1 contains the six place labels and no DEPTH/TIME/facts/relations; richer references are separate records. Export requires explicit --profile location-only-v1 and records profile/vocabulary in its manifest. This serializer is tested; model qualification/training remains pending.

The [editorial packet](../evaluations/flood-ner-editorial-20261014/README.md) provides 100 AI-assisted reviews and 113 contiguous context blocks; none is a completed manual annotation. Confirm each final passage's language and complete context. Names/ordinary technical borrowings do not alone make a Filipino passage Taglish; substantive bilingual clauses or quotations do. Regional-language quotations unsupported by v1 remain unknown. Tagalog-only samples stay separate from the paper's English/Taglish dataset unless its scope changes.

Editorial block/source-note offsets are absolute source offsets, whereas annotation entities/facts use passage-relative offsets. An exclusion creates a source gap, never permission to concatenate slices. Use full source/sibling context before selecting an independent sample, and keep every same-article/event/syndicated passage in one split. Inline captions and embedded posts need origin-aware fact review; corn height, rainfall and river gauges must not become road depths. Record the actual AI or human annotator/reviewer; AI work is not manual ground truth or training-use admission. The current location pilot explicitly leaves regional aggregates/water bodies and organization-only geography outside its six-label scope; do not silently force them into CITY/PROVINCE or generalize its completeness claim to all geographic entities.

## Entity boundaries

| Label | Meaning and boundaries |
|---|---|
| ROAD | Named road, including an integral ordinal/number and source abbreviation; annotate crossing roads separately. |
| LANDMARK | Named terminal, bridge, market, building or other landmark; a nearby landmark is not automatically a flooded location. |
| LOCAL_AREA | Full named/numbered sitio, purok, block, phase, zone, area, lot or unit reference, including designator and integral identifier/suffix. |
| BARANGAY | Official or source-named barangay mention including its explicit designator; an integral borrowed numeral in a proper name remains unchanged. |
| CITY | City or municipality mention; source city/municipality designators remain in the span. |
| PROVINCE | Province mention, including an explicit province designator. |
| DEPTH | Whole measurement or verbal gauge, including units, range/comparator and integral approximation qualifier. |
| TIME | Whole temporal expression including role cues such as as-of/by/since, date and clock when contiguous. |

Keep entities non-overlapping for spaCy NER. For a composite address, annotate contiguous non-overlapping components and express their parents separately. Do not merge a block and a lot because they share a number. Avoid redundant nested labels; a street number integral to a named road stays ROAD, while a house/lot qualifier is LOCAL_AREA when its role is supported. A code-switch does not change geographic type. Label entities even in forecasts, denials or historical statements; their flood interpretation belongs in facts/relations. Complete entity annotation covers all v1 labels in the selected passage, including non-flood contexts.

## Numbers and geographic identity

The supported research scope includes native Filipino, English, Spanish and Philippine borrowed spellings; digits, teens, compounds and larger observed identifiers; abbreviated prefixes; Roman/ordinal forms; letter suffixes; leading zeros; and named non-numbered places. Existing number normalization is a comparison aid, not a license to rewrite entities. Record `comparison_key` only when checked; unsupported spellings stay raw with unresolved identity. Numeric equivalence must preserve designator, suffix and geographic parent. Do not treat a number in a proper name, river gauge, clock, date or count as a numbered locality.

`identity.parent_entity_ids` links source-supported parent mentions present in the passage. `identity.state` is unresolved/ambiguous/resolved. A resolved identity requires reviewed reference evidence plus a PSGC or typed OSM ID. PSGC codes belong to administrative entities; a city PSGC code is not the ID of its road, sitio or lot. OSM uses node/way/relation plus integer ID, preserving reference URL. Uncertain identities carry no definitive IDs. The inspector returns candidates, not accepted identity labels; first-result hierarchy fallbacks and confidence scores do not remove ambiguity. Missing local-map coverage remains unresolved.

## Facts, scope and uncertainty

Facts are independent evidence nodes with one kind: depth, time, status or access. Depth/time nodes reference their DEPTH/TIME entities; status/access use exact supporting clause spans. Store source evidence once when multiple targets share it. In v1, depth/time `value` is source entity text or null, never an inferred scalar/date. Units and qualifiers stay in the depth span; ranges, maxima, collective readings and point readings have separate `depth_scope` values. Numeric canonicalization belongs to the later qualified runtime, not this preparation tool.

Time roles are onset, observation, report, publication, recession, clearance or unspecified. A supported observation is not onset. Capture/publication clocks cannot supply an absent observation date. Unknown dates remain null/unresolved; an article's explicit chronology can support a role without a resolved calendar timestamp.

Status values are active, rising, receding, subsided, cleared, forecast, negated, historical, habitual, prevention or unknown. Access values are passable_all, passable_with_caution, passable_unspecified, light_vehicle_closed, impassable_all or unknown. Passable does not mean dry; receding does not mean cleared. Source subsidence wording stays subsided unless explicit clearance evidence supports cleared. River gauges and evacuation counts are not road depths.

Each relation references one fact and explicit place targets, with exact scope evidence containing those targets. Scope is local, shared, collective or unresolved. Use shared only when the source supports the same fact for multiple places; use collective when it reports an area-level range/maximum that cannot establish independent per-place readings. Unresolved scope requires an uncertainty reason. A local exception uses a new fact and relation with `overrides_relation_id`, preserving the original shared evidence and overriding only the supported target subset for the same fact kind. Keep distinct observation times as separate relations rather than collapsing them.

Sharing requires evidence, not proximity: list headings apply within their bounded list; local measurements/clocks override only their entry. New source attribution, city/section changes, unrelated content and chronology can end scope. Meanwhile/samantala is interpreted with those cues, not always shared or always discarded. Captions and repeated related-story links need explicit origin treatment. If context is insufficient, retain unresolved relationships and expand the source passage before accepting complete annotation; never invent missing targets or timestamps.

## Review, admission and export

Review records carry annotation revision, reviewer, completeness and draft/accepted/rejected/unresolved status. Silver annotations require teacher identity when accepted. Same-teacher review remains silver; gold requires independently established review outside this milestone. Constructed test sources must retain constructed quality and cannot enter ordinary export. Mechanical validation verifies structure, not factual truth or independent review.

All current captures are research-only with unknown reuse status. Training admission requires an explicit allowed reuse assessment, complete reviewed labels and frozen article/event/syndication grouping; unclear rights are retained for research inventory rather than silently admitted. Related revisions, syndicated reports, identical text and events stay within one split. Split assignments are explicit rather than passage-random. A source-level language tag is research metadata; review passage language before model evaluation.

Use the [offline tooling instructions](../../backend/training/flood_ner/README.md). The [research case matrix](../evaluations/flood-ner-milestone1-20261014/case_matrix.json) provides source-hash/offset pointers and interpretations, not a ready training dataset. The later pilot must preserve ambiguity, source admission and silver/gold evaluation limits.

The [completed-work review](../evaluations/flood-ner-review-20261014/README.md) adds export guards for equivalent article URL aliases and explicitly provisional:, review-needed: or unresolved: group identifiers. Replace these placeholders only after source-supported group review. Unknown/unrecorded event or syndication relationships still require semantic review; URL normalization alone cannot establish independent split membership. Frozen CRLF/LF text is preserved without changing offsets.
