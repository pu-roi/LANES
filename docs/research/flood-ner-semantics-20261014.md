# Flood NER milestone 1: location and fact semantics

> **Last Updated:** October 14, 2026 (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Source-backed research and v1 tooling specification, with coverage gaps explicitly retained.

## Evidence and method

Inventoried 50 distinct preserved original-text captures, then fetched four additional public HTML sources offline. Source bytes, frozen text and metadata live under ignored training artifacts; tracked [coverage metadata](../evaluations/flood-ner-milestone1-20261014/coverage.json) records hashes, clocks, identities, reuse status and capture methods. All 54 remain research-only. Existing fixture expected claims are not entity-span labels. The inventory's 51 unknown language tags need review; the three supplied language categories cover research examples, not balanced training support.

The [20-case matrix](../evaluations/flood-ner-milestone1-20261014/case_matrix.json) points to exact source-hash/character ranges. Interpretations are research proposals, not independently reviewed gold annotations. The four new captures were manually inspected for relevant body context; extraction retains source headings/captions and can include publisher interface text, so passage selection/review remains necessary. Group identifiers for new captures are provisional research identifiers; they must be reviewed across related articles before training admission.

## Location and number findings

The [Quezon City government directory](https://quezoncity.gov.ph/departments/social-services-development-department/) contains named and numbered sitios/puroks, larger purok identifiers, abbreviated blocks, lot/phase/area/unit components, Roman numerals, letter suffixes and compact address notation. These establish real address syntax, not current flood observations. Different components retain their own types and parents; identical numbers across subdivisions or barangays do not identify one place.

Existing `locality_number_service` covers units, teens, decades and composed cardinal forms across English, native Filipino and Spanish/borrowed spellings, including hundreds and larger forms. Existing independent regressions exercise extensive vocabulary/compositions. It recognizes full Sitio/Purok/Block/Zone/Phase and Barangay/Brgy designators; it currently lacks Blk/Prk/Bgy/Lot/Area/Unit prefixes and Roman numerals. Leading-zero and suffix treatment must be evaluated as identity policy, not assumed universally correct. The milestone adds no runtime aliases.

| Coverage dimension | Research outcome / remaining gap |
|---|---|
| Digits, units and teens | Existing vocabulary and regressions support many variants; real-source support is not available for every form. |
| Compounds, hundreds and larger numbers | Existing composed parsing is reusable; no complete field-spelling or large-address corpus is established. |
| Abbreviations | Real block abbreviation evidence exists; additional prefix aliases require case-specific source review. |
| Roman/ordinal/letter forms | Real address cases exist; keep full identifiers and distinguish numbered streets from local areas. |
| Native and borrowed names | Numerals embedded in names retain the named administrative identity; global replacement is incorrect. |
| Joined/mixed/leading-zero forms | Structural tests cover some cases; real examples and normalization decisions remain incomplete. |
| Regional variation | This is English/Tagalog/Taglish groundwork; other regional-language coverage is not established. |

PSGC is already loaded for nationwide administrative identities; the OSM placement catalog currently covers 17 NCR city relations and contains 1,374 locality points. Existing Sitio Sais/Sitio 6 matching in Malabon is a verified example, not the whole requirement. Proper place parent context remains mandatory; the code's low-confidence first-result hierarchy fallback is a candidate, not established identity. OSM provides bounded road candidates and explicit local aliases; absence from that snapshot does not invalidate a recognized source name. Recognition, administrative identity and bounded placement require separate evaluation.

## Flood-fact findings

[GMA's August 10 report](https://www.gmanetwork.com/news/topstories/nation/997943/thousands-evacuate-as-habagat-rains-cause-flooding-in-ncr-other-regions/story/) supplies a named sitio with barangay context, locality-specific water recession, city transitions, river-level measurements and barangay names containing borrowed numerals. The river gauge cannot become a road-water depth; report and evacuation clocks do not establish onset. Preserve source wording and distinguish supported local facts from nearby context.

[GMA's Tagalog August 8 report](https://www.gmanetwork.com/news/balitambayan/balita/997853/iba-t-ibang-bahagi-ng-bansa-binaha-dahil-sa-ulan-na-dulot-ng-habagat/story/) combines verbal depths, current observations, habitual-flood context and a warning issuance time. Broad area depths do not locate a specific road segment. A warning's time is a report/publication fact rather than flood onset. Missing clocks and imprecise observation areas stay unresolved; the report also demonstrates that local language and source switches need contextual interpretation.

[Daily Tribune's August 30 report](https://tribune.net.ph/2026/08/30/extreme-rain-warning-renews-fears-across-pampanga-floods-rise-again) reports two terminals under a shared depth/chronology, a multi-town collective range, recession followed by renewed rising, and English/Tagalog quotation. Preserve one shared evidence occurrence with explicit targets; do not invent separate readings. Recession is not lasting clearance. Collective ranges remain collective; quoted source attribution and event-relative chronology need separate relations. The mixed-language research tag applies to this source's passages, not a claimed whole-corpus Taglish classifier.

Existing saved list evidence and heading tests cover shared clocks with per-road depths and local overrides. Verification initially exposed two paragraph-boundary failures: narrative clock propagation reached a later independently worded road paragraph. After the developer authorized gap fixes, a local follow-up repair bounded that inheritance while preserving adjacent city-led continuations and the existing source/chronology guards. The [evaluation](../evaluations/flood-ner-milestone1-20261014/README.md) records before/after evidence. Neither old rule output nor repaired rule output becomes a training target automatically.

## Model qualification and decisions

The [TLUnified-NER paper](https://arxiv.org/html/2311.07161v1) provides a Tagalog NER methodology and reusable coarse entity data. It does not establish LANES flood-fact/relationship accuracy. The examined [calamanCy medium 0.2.0 model card](https://huggingface.co/ljvmiranda921/tl_calamancy_md) lists spaCy >=3.8.3, MIT licensing and PER/ORG/LOC entity labels. The [dataset card](https://huggingface.co/datasets/ljvmiranda921/tlunified-ner) separately declares GPL-3.0. Keep model and data licensing distinct. No model/data package was installed or selected; English/Taglish adaptation, fine-grained labels, CPU memory/latency and artifact provenance remain qualification work.

For milestone 1, retain spaCy 3.7.5 and the [v1 annotation specification](../guides/flood-ner-annotation-v1.md). Use a frozen multilingual tokenizer with one terminal-period boundary for alphanumeric address identifiers, saving its bytes/hash. Entities identify spans; separate facts/relations preserve meaning. Reuse existing number/PSGC/OSM services for read-only comparison. Export only admitted, fully reviewed source-exact records with frozen grouped splits. DocBin is spaCy's corpus serialization format, not a model or relation learner. [spaCy documentation](https://spacy.io/api/docbin).

Remaining gaps include real negative/forecast examples across all languages, source-supported shared depth with distinct per-place clocks and explicit exceptions in Tagalog/Taglish, onset versus physical clearance distinctions, real high-number/mixed-prefix coverage, independent review and reuse assessments. Constructed regression examples test these structural cases but are explicitly separate from captured evidence. These gaps do not prevent using the tooling; they prevent claiming a qualified training corpus or production NER.
