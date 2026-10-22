# Completed NER groundwork and 100-news collection: review

> **Last Updated:** October 14, 2026, 12:40 PM (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Completed-work audit and offline-tooling corrections. Pilot preparation/labeling has not started.

The developer requested a double-check before proceeding. Re-read the architecture, roadmap, research/annotation contract, source registers and preparation/export code; reran the original focused suite; reproduced frozen source bodies; checked live publisher evidence on a stratified sample; and exercised adversarial inputs beyond the earlier tests. The first rerun passed **338 tests in 25.47s**. The adversarial review found real validation gaps despite that passing baseline.

## Revalidated deliverables

| Deliverable | Measured result |
|---|---|
| Historical news register | 100 accepted articles, 100 distinct canonical article keys; unchanged register/coverage/outcome bytes after stricter verification. |
| Original source bodies | 98 reproduced from saved HTML/rendered snapshots using their actual extraction recipes. The 12 older archive bodies use the existing PublisherBody script and its recorded title/publication wrapper. Two captured-original fixtures retain missing original HTML and retrieval times. |
| Source identities/publication evidence | All 100 source IDs, publisher identities, publication-day evidence, text/raw hashes where available, timestamps and body evidence pointers pass the corrected verifier. |
| First milestone research matrix | All 20 case source IDs/hashes/offset ranges still match their frozen sources. Interpretation remains AI-assisted research, not independent gold review. |
| Supporting references | All 36 text hashes and supplied raw hashes pass: 30 Pasig bulletins, one QC directory and five Wikipedia revisions. Zero contribute to the 100-news target. |
| Annotation schema/export | Saved JSON Schema matches the current Pydantic contract. Exact spans, tokenizer alignment, shared facts/overrides, parent uncertainty/cycles, admission checks and deterministic DocBin/relationship round trips pass. |
| PSGC/OSM/number baseline | Existing regressions pass. A fresh read-only Sitio Seis probe yields comparison key sitio 6 and OSM node 11155381066, Sitio Sais, Malabon/Catmon; no PSGC sitio code or flood geometry is invented. |
| Boundaries | No new package/model, SQL schema/migration, production setting, operational record, zone or deployment change. Existing authorized temporal v1.8/v21 edits are preserved. |

[audit.json](audit.json) records per-source reproduction/check results, case-pointer checks and adversarial outcomes. [live_checks.json](live_checks.json) records the 22-page stratified check, retrieval times, raw snapshot hashes/paths and the publication metadata conflict. Raw audit snapshots remain ignored under backend/training/flood_ner/artifacts/review-20261014/.

## Findings corrected during review

1. **Canonical identity could be changed to another story on the same publisher.** The previous validator only checked agreement between the supplied key/canonical URL and publisher. It now binds that identity to the captured source's article identity. Percent-escape hex case is normalized so RMN's equivalent upper/lower escape forms remain valid; ordinary URL path case and encoded slashes remain distinct.
2. **Retrieval/publication provenance could be altered in the register.** Captured/publication timestamps and reuse status now must match the source record. Missing retrieval times remain null. Publication evidence must point to the same raw capture, or to its own frozen legacy text with a header supporting the publication day.
3. **Malformed review inputs could crash with TypeError/AttributeError.** Manifest/container/evidence/reviewer types now produce actionable errors. No partial verified output is written. Discovered URLs must be an explicit JSON string array.
4. **Universal-newline file reads could change valid source text.** Frozen body hashing and repeated browser import now decode bytes directly, preserving CRLF as well as LF. Browser reuse also rejects altered saved metadata.
5. **Export leakage and unresolved groups were insufficiently guarded.** URL aliases/AMP paths/tracking variants and GMA route/slug variants now share split identity. Explicit provisional:, review-needed: and unresolved: groups cannot pass export, even with a constructed-test override. These checks cannot discover unidentified syndication or unrecorded event relationships; semantic grouping still needs review.
6. **Repeated Wikipedia capture could overwrite metadata, and revision filenames were not language-scoped.** Repeated revisions preserve the original metadata/retrieval time and verify frozen content. New revision files include the wiki language; existing revision-only captures remain readable and untouched. Corrupt or conflicting files fail explicitly.
7. **Documentation implied a commit had occurred.** Corrected the collection report to describe local saved metadata. No commit or push was requested or performed.

Corrections are confined to offline collection/validation/export code and focused tests. They do not select a model, add pilot labels or change operational parsing.

## Live publisher double-check

Checked the earliest/latest selected GMA article in each year plus every selected ABS-CBN, RMN, Tribune and Philstar article: **22 pages**, all returning HTTP 200 and the expected publisher. Twenty-one supplied matching structured publication dates. The Philstar AMP page supplies a 1970 epoch datePublished/dateModified in JSON-LD, while the article's own header time element supplies **2026-09-09T17:03:00+08:00**, agreeing with the saved fixture and visible [publisher article header](https://www.philstar.com/nation/2026/09/09/2555106/list-flooded-metro-manila-areas-september-9). Related-story clocks were excluded by restricting the evidence to the main article header before its body. All 22 sampled publication days are therefore corroborated, with the Philstar structured-date conflict retained rather than silently rewritten.

The two old fixture publication instants also match the current publisher evidence: GMA's explicit +08:00 JSON-LD instant and Philstar's explicit +08:00 article-header instant. This corroboration does not recover the original retrieval timestamps or original HTML versions. Their frozen register's earlier uncorroborated-instant notes remain historical; this later audit supplies the independent publisher-page corroboration.

This live sample does not claim all 100 pages were fetched again. The complete 100-record evidence audit uses their frozen versions. Publisher content can change; audit snapshots do not replace the original source version or establish physical flood truth. The Philstar structured-date conflict remains a publisher-format issue requiring explicit evidence review for future capture admission; this audit does not add a generic automatic date override.

## Research and plan review

Rechecked the primary [TLUnified-NER paper](https://arxiv.org/abs/2311.07161), [calamanCy 0.2.0 medium model card](https://huggingface.co/ljvmiranda921/tl_calamancy_md) and [dataset card](https://huggingface.co/datasets/ljvmiranda921/tlunified-ner). Recorded compatibility remains accurate: the model card requires spaCy >=3.8.3 and declares MIT; the dataset card separately declares GPL-3.0. The model's LOC/ORG/PER labels do not supply LANES road/barangay/depth/time relations. No model or dataset was installed, and spaCy remains 3.7.5.

Research and collection milestones remain delivered. Preparation for training remains open: unknown source reuse, provisional event/syndication grouping, passage language review, independent label review, GMA dominance (88/100), only three article-level Taglish tags, and missing written-number/high-number/abbreviation/Roman/suffix/compound-address/shared-exception/negative slices. The 100 articles and 20 research cases are not a labeled or admitted training corpus. No gap was closed merely by counting tests.

## Final verification

**362 checks passed in 26.00s** after corrections, across collection/tooling, existing PSGC/number/locality anchors, headings, temporal scope, September 24 replay, source validation and durable processing. New cases exercise forged identities/provenance, malformed inputs, evidence-file borrowing, CRLF preservation, metadata immutability, equivalent URL aliases, unresolved group refusal and Wikipedia recapture/language separation. Existing deterministic export tests continue to pass.

Verification used --noconftest, explicit isolated source_rules settings, empty provider credentials, an unreachable test-only PostgreSQL URL and existing in-memory fixtures. The existing spaCy/Click deprecation warning remains. Real register verification, schema comparison, unchanged metadata bytes, ignored-artifact checks and documentation-link/whitespace checks passed. No shared database was accessed.

The completed deliverables are available for the next preparation gate after reviewing the documented admission and coverage gaps. See the [roadmap](../../plans/lanes-ner-training-plan.md), [first milestone acceptance](../flood-ner-milestone1-20261014/README.md), [100-news collection](../flood-news-corpus-100-20261014/README.md) and [tooling instructions](../../../backend/training/flood_ner/README.md).
