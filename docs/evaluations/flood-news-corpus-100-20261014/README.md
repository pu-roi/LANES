# Historical Philippine flood-news collection: 100 reviewed articles

> **Recorded:** October 14, 2026, 11:48 AM (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Offline research collection completed locally on roi-branch. Source-body review is AI-assisted research review, not independent gold annotation or training admission.

**Later completed-work review:** [Audit and corrections](../flood-ner-review-20261014/README.md) reproduces 98 source bodies, verifies all 100 records/20 research cases/36 supporting references, corroborates 22 live publication days, records the Philstar AMP structured-date conflict and passes 362 checks after offline validation/export fixes. The original register remains unchanged and research-only.

The frozen [news register](news_register.json) contains **100 distinct Philippine flood-news articles** published within January 1, 2022–October 14, 2026. Seventeen previously eligible articles are retained and 83 qualifying articles added. All counted records have a captured body, checked publisher/publication-day evidence, a reviewer decision, immutable text identity and hashed body offsets. The observed publication range is March 12, 2022–September 9, 2026; the collection does not claim every month in the requested window is represented.

The original [54-capture milestone](../flood-ner-milestone1-20261014/README.md) remains a historical checkpoint. It included news and supporting sources, not 54 qualifying historical news articles. This expansion does not overwrite its evidence or count official bulletins, directories, Wikipedia, snippets, failed captures or repeated stories toward 100.

## Coverage

| Publication year | News articles | English | Tagalog | Taglish |
|---|---:|---:|---:|---:|
| 2022 | 22 | 10 | 12 | 0 |
| 2023 | 21 | 10 | 10 | 1 |
| 2024 | 23 | 20 | 3 | 0 |
| 2025 | 18 | 11 | 6 | 1 |
| 2026 | 16 | 13 | 2 | 1 |
| Total | 100 | 64 | 33 | 3 |

| Publisher | Articles |
|---|---:|
| GMA News, including Balitambayan | 88 |
| ABS-CBN News | 5 |
| RMN Networks | 5 |
| Daily Tribune | 1 |
| Philstar | 1 |

ABS-CBN contributes one rendered-body capture in each of the five years. Its static HTML often returns a site shell without the article. Forty-one such captures are explicitly excluded; five complete public browser bodies and their publication headers were preserved separately. GMA NewsArticle JSON-LD article bodies often contain HTML; the offline extractor now decodes that body instead of selecting surrounding navigation. This is confined to preparation tooling, not runtime ingestion.

Reports span Metro Manila/Camanava, Bulacan, Pampanga, Pangasinan, Isabela/Cagayan, Bicol/Quezon, Iloilo/Western Visayas, Cebu, Zamboanga, Misamis and Davao. Examples include Purok 9 in Barangay Poblacion and Puroks 5–8 in Barangay Magading, Nabunturan, in the January 2024 Davao report; Barangay 19-B in Davao City; and November 2024 recession in Purok 12, Barangay Villa Luna, Cauayan, Isabela. Raw names remain untouched and no geographic identity is resolved by this collection. These references do not expand the bundled NCR OSM road coverage.

The [machine-readable coverage report](coverage.json) includes year/publisher/language totals and cross-tabulations. Article-level research cues include road locations (72), depth wording (56), clocks (52), access/status wording (38), recession/clearance wording (38), named-locality wording (76), numbered localities (8), and impact counts (61). These overlapping cue counts are search aids, **not entity labels or verified fact relationships**. A clock cue may be a publication header, a subsiding reference may be retrospective, and a knee-height phrase may describe crops rather than water. The Isabela corn report explicitly records that last ambiguity. Source offsets and span hashes make each cue inspectable.

Language tags describe the reviewed article narrative and mixed quotation structure. They are metadata decisions, not passage-level gold language annotations. Predominantly English reports can include Filipino or regional quotations; preserve those passages and review their language before annotation.

## Register and outcomes

- [news_register.json](news_register.json): exactly 100 accepted research articles; URLs/canonical keys, publisher, publication value/basis/evidence pointers, capture time/version/hash, original-text/raw-file paths, language, review notes, evidence offsets/hashes and provisional groups.
- [collection_outcomes.json](collection_outcomes.json): 249 capture/review outcomes: 100 accepted, 111 excluded, 14 failed and 24 reserves without completed body review. Multiple capture versions can share one article identity. The translated July 2024 NCR calamity report is linked to its English counterpart and excluded. Exclusion reasons distinguish foreign reports, static shells, policy/forecast/ancillary selections, unknown/out-of-range dates and supporting material.
- [supporting_references.json](supporting_references.json): 36 separate references—30 preserved Pasig bulletins, one Quezon City address directory and five Wikipedia revisions. Their contribution to the news target is zero.
- Raw captures, rendered DOM snapshots, full source JSONL and review decisions remain in ignored `backend/training/flood_ner/artifacts/collection100/` and `artifacts/captures/`. Metadata registers are saved locally for repository review; no commit or push has been performed. Newly collected full article bodies remain ignored. On another computer, obtain matching frozen captures before reusing offsets. A changed live page is not a replacement for a recorded version.

`lanes-flood-news-collection-v1` versions the register/report. Publication-day filtering uses Asia/Manila when the publisher supplies a timezone-qualified instant. Date-only and unzoned evidence retain their original value without an invented timezone. Publication, retrieval, flood observation and Wikipedia revision times remain separate. Two preserved captured-original fixtures have no original raw HTML or retrieval timestamp; their printed publisher body headers corroborate the publication day, and their original declared timestamps remain explicitly uncorroborated as instants. Missing provenance is not filled with today's retrieval time.

Article keys link revisions; exact/near-identical body comparisons and manual translated-repeat review prevent count padding. Event groups use conservative provisional storm/year or rain/month buckets; syndication remains unresolved except the identified translated repeat. These groups identify candidates for later review, **not qualified train/dev/test splits**. Unknown identities and relationships remain unknown.

## Wikipedia references

Captured English revisions cover Typhoon Noru, Typhoon Doksuri, Typhoon Gaemi, Tropical Storm Trami (the requested 2024 typhoon title redirects), and Metro Manila. The MediaWiki revisions API supplies revision ID, timestamp and unchanged main-slot wikitext. Records include permanent/history links, contributor attribution, retrieved site rights metadata and a content hash. All five content hashes were checked against the frozen local wikitext.

The retrieved site license is Creative Commons Attribution-Share Alike 4.0. Attribution/history and applicable license links are retained; page-specific or third-party exceptions still require checking before reuse. See Wikimedia's [content reuse guidance](https://www.mediawiki.org/wiki/Wikimedia_APIs/Content_reuse). These pages support context, place-name research and original-news discovery only. No Wikipedia geography was promoted to a resolved identity; any future identity use must be checked against PSGC/OSM. Revision time does not date flooding, and these pages stay outside the primary training corpus.

## Verification

**338 focused checks passed in 53.18s**, including publication-window/timezone boundaries, domain-bounded publisher identity, URL/AMP canonicalization, GMA story identities, duplicate/version/copy rejection, static-shell failure, HTML-body decoding, metadata precedence, immutable rendered captures, malformed reviews/spans, publication/hash/file evidence, and Wikipedia revision/license separation. Existing number/PSGC/locality-anchor regressions remain passing, alongside preparation/export, heading, temporal, replay, source-validation and processing checks.

Tests used `--noconftest`, explicit source_rules test settings, empty provider credentials, an unreachable test-only PostgreSQL URL and existing in-memory fixtures. No operational database was contacted or historical flood records/zones published. The existing spaCy/Click deprecation warning remains. spaCy stays 3.7.5 and no dependencies or schemas changed.

The real manifest passed `verify-news`, checking all 100 source identities, frozen text/raw hashes where available, publisher publication evidence and exact body-offset hashes. Exported register/coverage/outcome bytes were also compared against the frozen documentation copies. Instructions are in the [offline tooling guide](../../../backend/training/flood_ner/README.md).

## Remaining preparation

GMA dominance and the three Taglish articles limit balanced evaluation. Early-2022 and late-2026/month coverage, region/publisher diversity, real forecast/negative contrasts, shared facts/local exceptions, written number families, larger identifiers, abbreviations, Roman numerals, leading zeros, suffixes and compound block/lot/phase/unit addresses remain explicitly incomplete. The separate directory supports syntax research but cannot fill a news-coverage gap. Existing research cases remain useful; collection cues do not replace the source-linked annotation matrix.

Before the pilot, assess reuse rights, review passage selection/language and event/syndication boundaries, then annotate and independently review appropriate slices. All 100 source captures retain unknown reuse and research-only admission. Zero pilot entity/fact labels or training-admitted sources were created; no model was selected, installed or trained. Runtime integration, provider removal, operational data changes and deployment remain subsequent stages in the [roadmap](../../plans/lanes-ner-training-plan.md).
