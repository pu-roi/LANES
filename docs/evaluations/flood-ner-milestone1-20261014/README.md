# Flood NER milestone 1 — local acceptance

> **Last Updated:** October 14, 2026, 4:27 AM (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

Delivered offline source inventory/capture, a source-linked research matrix, a v1 annotation specification/JSON Schema, validation, read-only location inspection and deterministic DocBin export. This is corpus preparation, not a trained NER release. The developer subsequently authorized continuing with gaps; the concrete shared-clock paragraph defect discovered during verification is also repaired locally.

## Sources and coverage

- [coverage.json](coverage.json): 54 distinct URL/text-hash captures, including 50 saved originals and four newly fetched sources. All are research-only with unknown reuse status. Supplied language tags: one English, one Tagalog, one source containing English/Tagalog passages, 51 unknown. These are source metadata, not balanced passage-level training labels.
- [case_matrix.json](case_matrix.json): 20 source-linked research cases, each with a text hash and passage offsets; none missing its captured evidence. Cases are interpretations and evidence pointers, not pilot entity/fact labels.
- [Research](../../research/flood-ner-semantics-20261014.md), [annotation guide](../../guides/flood-ner-annotation-v1.md), [tooling](../../../backend/training/flood_ner/README.md), [JSON Schema](../../../backend/training/flood_ner/annotation/schema.json).
- Full captures and the inventory source JSONL remain in ignored `backend/training/flood_ner/artifacts/`. No raw newly fetched article bodies are committed. Hash pointers remain useful even if a live page changes; another computer must obtain matching captures before using those exact offsets.

## Verification

**301 checks passed in 25.65s** across `test_flood_ner_tooling`, `test_philippine_location_service`, `test_locality_number_service`, `test_news_locality_anchor`, `test_news_heading_context`, `test_news_temporal_scope`, `test_news_september24_replay`, `test_news_source_validation`, and `test_news_processing`.

The suite ran with `--noconftest`, explicit source_rules test settings, empty news-provider credentials and an unreachable test-only PostgreSQL URL. SQL-backed checks used their existing in-memory SQLite fixtures; no shared database access or real publication occurred. This avoids loading encrypted dotenv values as auditor configuration. One existing spaCy/Click deprecation warning remains. The initial unconfigured processing run failed because an encrypted dotenv batch-size value was not valid runtime configuration; the explicit isolated test environment resolved that test setup problem without changing application settings or secrets.

New checks cover source hashes/timestamps, exact offsets, typed references, token alignment, ranges/shared facts/overrides, inferred-value rejection, diverse address identifiers, uncertain geography and cycles, grouped/copy leakage, review/admission failures, explicit constructed-test handling, capture bounds/immutability/corruption, actionable CLI errors, deterministic serialization and entity/relationship round trips. No test imports operational configuration to run the core offline commands. Location inspection reuses existing assets and confirms Sitio Seis matches the parent-scoped Sitio Sais/Sitio 6 OSM candidate in Malabon/Catmon.

## Gap repaired after milestone work

Before repair, two existing temporal regressions assigned an earlier clock to independent subsequent road paragraphs. The narrative-sharing helper checked chronology/source words and distance, but not paragraph continuity. The local fix ends unsupported paragraph inheritance while retaining the existing adjacent city-led narrative continuation, multi-road facts, explicit clocks and list-heading behavior. It also rejects crossing an unrelated intervening paragraph. Existing meanwhile/source-change guards remain.

New regressions cover unrelated paragraph breaks and a valid city-led continuation followed by an independent road paragraph. Extractor identity is now `taglish-rules-v1.8`; durable pipeline identity is `rules-spatial-preview-v21`, preserving old run identities/history rather than relabeling them. The follow-up fix is separate from NER model implementation and has not been deployed.

## Acceptance limits and next work

The research matrix, guide, coverage report and tested tools satisfy milestone 1. Zero pilot passages have been labeled and no model was selected, installed, trained or evaluated. Structural tests cannot prove correct source interpretation, independent gold review or acceptable training reuse. Model/data licenses remain distinct; calamanCy 0.2.0 requires a runtime version not installed here.

Before the pilot, resolve reuse admission, passage language/event/syndication groups, real negative/forecast and shared-exception coverage, high-number/abbreviation cases and independent-review strategy. Cases with unavailable geographic coverage remain unresolved; no coordinate or flood extent is invented. The 20 cases and existing rules regressions are not accuracy claims. No API/UI, schema/migration, dependency upgrade, deployment, operational-data or expiry-setting changes occurred.
