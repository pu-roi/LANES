# Flood NER additional-dataset acquisition and readiness

> **Last Updated:** October 16, 2026, 10:28 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Readiness is incomplete.** This is a measured acquisition/review checkpoint in the existing Gate 3 task, not a new experiment or admission. Codex preserves the original 400-sample experiment and prepares a separate draft pool. No new records are admitted, no 192/48 partition is frozen and no export or training is performed.

## Development acquisition and topic correction

Development discovery closes at **365 distinct canonical candidate article URLs (363 article keys), 428 exposed links, 182 capture attempts and 159 successful full captures**. The 400-URL/200-capture bounds are not exhausted; failed attempts count conservatively toward the capture budget. Ninety-eight unrelated search results, 90 historically exposed articles and four foreign-story results remain exposure exclusions. Broad initial weather/locality searches returned unrelated material; these were not annotated or admitted. New capture screening requires an explicit flooding term and Philippine scope. Parent discovery is sealed before isolated test curation and the helper now refuses reopening it.

All 49 articles represented in the draft concern Philippine flooding, impacts/recovery or flood-control reporting. Of the other captured sources, **91 await complete topic/origin/reference review and 19 are excluded or held** (15 outside/unverified publication dates, three foreign stories and one incomplete/short capture). No quota-infeasibility claim is made for every unreviewed source. A negative passage means no named six-class location reference; it may still describe flooding, rescue, school disruption or recovery. Negatives do not justify importing unrelated news.

**244 draft passages / 49 articles** contain **123 English, 121 operational Taglish, 359 location spans and 107 negatives**. Source-exact Unicode windows, hashes, offsets and duplicate checks pass. After source-reading review, **179 remain candidates (96 English / 83 Taglish; 159 spans; 101 negatives)** and **65 are explicitly held** for occurrence-level type/boundary/language/source-use or tokenizer questions. Held references have expected_entities=null, allow_definitive_scoring=false and is_negative=false in the review register; unchanged draft annotations are retained as history.

These 179 candidates are not admitted records or independent gold. Coverage capped at 15 per theme/language has an upper bound of **156**, below the required 240, even before group partition solving. All 49 draft source articles are GMA reports: publisher concentration, the high negative proportion and event concentration limit coverage. Compatibility with older references, publisher balance and the final combined corpus size are undecided. Shared administrative-type lists do not establish numeric LOCAL_AREA ellipsis coverage, and negative controls do not replace positive rare-phenomenon examples.

| Theme | English candidates / 15 | Taglish candidates / 15 |
|---|---:|---:|
| compound-crossing-roads | 21 | 6 |
| facilities-institutions | 14 | 14 |
| geographic-type-ambiguity | 23 | 15 |
| locality-designators | 5 | 9 |
| misleading-names-time-common-words | 18 | 21 |
| project-asset-names | 10 | 13 |
| shared-identifiers | 2 | 2 |
| short-codes | 3 | 3 |

## Source use, grouping and history

Codex records case-specific project decisions under researcher delegation: **47 selected-text private academic bases adopted; two mixed-origin working-copy questions remain held**. Each entry binds article/sample identities, selected and whole-copy amounts, dated policy/raw capture hashes, factual/quoted nature, market uncertainty, credits and limitations. Corpus admission remains zero. The saved [GNO user policy](https://www.gmanetwork.com/news/user-policy/) educational/noncommercial download language supports an explicitly identified project inference for owner-only research; it is not publisher authorization for AI training. The publisher's [internal AI-production policy](https://www.gmanetwork.com/news/artificial-intelligence-policy/) is not researcher approval. Third-party image/user content, raw working-copy scope, publication/model distribution and other-use outcomes retain separate limits.

Forty-nine source group reviews conservatively join known event/aftermath relationships, including cross-month reports, rather than declaring stories independent by date or hash. Final compatibility with older development groups and 192/48 grouped language quotas remains unresolved. No group is split to meet quotas.

Local restored/public inventories and seven ZIP payloads reconcile **609 historical URLs / 725 key strings and aliases**, with no source-inventory or archive structured-parse errors. The missing detailed desktop project-use decision predecessor is a source-use audit gap; it is not automatically an unknown article universe. Unavailable external laptop history is not certified. Any actual unresolved exposure/event relationship blocks fresh-test admission. The three historical audit-reference gaps remain separate: two restored references match recorded hashes without formal reconciliation, and the IPOPHL historical reference remains hash-divergent. Eleven invalid-fixture references and ten copied-manifest aliases retain their prior classifications; six paper/dataset and six production/model-distribution outcomes remain separately deferred. See the unchanged [qualification-review limitations](../flood-ner-model-qualification-20261016/README.md).

Policy raw HTML hashes verify exactly. Saved policy text uses Windows CRLF while its original logical-text digest used LF; both exact byte and normalized text digests are recorded without rewriting evidence.

## Tokenizer and isolated held-out curation

The unchanged Python 3.11 research environment loads vocabulary and tokenizer only, with no pipeline components or model weights. Across 244 drafts / 359 spans there is **one strict alignment failure**, preserved by record/entity ID and offsets. Candidate tokenizer bytes serialize identically and are unchanged. The affected passage remains held; no tokenizer rule, source wording or dependency is changed.

One fresh curator runs with fork_turns=none, receiving conventions, source-use guidance and exclusion metadata without model outputs or this conversation. Parent reads only the curator's aggregate-status.json and verification-manifest.json. The curator's aggregate result and hashes are preserved in [verification.json](verification.json). Standalone test-package status is recorded below; overall dataset readiness remains incomplete because development gates fail. Missing or unresolved curator fields are not inferred as passing.

```json
{
  "status": "incomplete-unsealed",
  "ready": false,
  "sealed": false,
  "records": 0,
  "articles": 0,
  "languages": {
    "english": 0,
    "taglish": 0
  },
  "negatives_by_language": {
    "english": 0,
    "taglish": 0
  },
  "candidate_article_urls": 185,
  "capture_attempts": 32,
  "successful_captures": 27,
  "failed_captures": 5,
  "source_use_admitted_records": 0,
  "alignment_errors": 0,
  "historical_independence_status": "Not certified. Candidate-specific actual undated/continuing-event/project relationships remain held. Available article keys are disjoint; unavailable external/laptop history is not reconciled.",
  "blockers": [
    "Exact 60 definitive passages / 30 English + 30 Taglish / 3 genuine negatives per language quotas not met. Only 56 prospective candidates; 22 operational Taglish; 41 complete silver references across all languages before history/source-use admission.",
    "15 full references unresolved; no type guessed for bare ambiguous administrative names, uncertain proposal/project assets or weak language mixing.",
    "14 captured article histories held for actual undated or potentially continuing source/event/project relationships; complete unavailable external/laptop exposure reconciliation not available.",
    "2 sources retain specific independently credited photo/user-content extent/basis holds in full working context.",
    "No independently admitted held-out membership or final test seal. All candidates remain private holds; none count as definitive negatives or training data."
  ]
}
```

Initial child network failures are retained. Where required, parent executes the curator's fixed bounded transport helpers without inspecting article text/labels; that transport provenance is recorded separately from curation.

## Verification and preservation

**20 standard-library tests pass**, covering input hashes, Unicode offsets, invalid labels, unresolved references, duplicate/moved memberships, group leakage, theme/language/negative/partition quotas, admission and overwrite refusal. The earlier 15-test verification is retained, followed by five additional quota/membership cases. Readiness failures are evidence, not passing gates.

Preservation verifies **11,712 prior artifact hashes, 22,759 research-environment file stats, 109 CLI package versions, 2,888 prior repository files outside the four synchronized documents, and backend/.env**. Original counts remain **400 samples / 138 articles / 1,465 spans, 200/200 languages and 280/60/60 partitions**; all original contextual/evaluation/tokenizer/model records are unchanged by their prior file hashes. No API/schema/dependency/runtime/model-selection change occurs.

An earlier unbounded capture command was rejected by automatic approval review before execution because its batch/budget safety was unclear. The capture helper was changed to enforce at most ten attempts per batch and cumulative caps before networking; bounded captures then succeeded. Original failures and retry attempts remain logged.

## Remaining work in the same Gate 3 task

1. Resolve the 65 reference/language/source-use/alignment holds using source evidence; unsupported interpretations remain unscored. A tokenizer failure does not authorize changing the frozen tokenizer.
2. Review the remaining 91 captured sources for the measured rare-theme/language and genuine positive-example gaps first. Further discovery needs a separately recorded continuation respecting isolated test exposure exclusions and remaining round budgets. Do not relabel themes or use unrelated articles to meet counts.
3. Complete source-use admission and reviewed grouped **192/48**, **96/96 training** and **24/24 validation** membership assembly; seal the new **60-test / 30+30 / exactly three negatives per language** package only if the isolated curator's provenance/eligibility/independence gates pass.
4. Decide combined corpus compatibility/size and bounded recipes from actual readiness evidence before export/training. CPU/Linux, failure-handling and performance qualification remain open before Gate 4.

The source-reading annotations and decisions are Codex AI silver under delegation, with no invented human reviewer or publisher permission. Independent accuracy claims require independent reference review. No export, training, model prediction evaluation, correspondence, deployment, commit or push occurs.
