# Pasig follow-up acquisition, parser repair and reported-subsidence register

> **Last Updated:** October 05, 2026, 3:20 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Targeted acquisition, source review, collector v3 repair and merged evidence/proxy exports delivered. No fitted model or runtime expiry change.

The earlier collection-before-cleaning work was already completed. This is an additional bounded pass authorized by the developer, followed by target definition and parser repair. It does not restart an unlimited acquisition loop. The original source captures, base CSVs and October 5 qualification version remain preserved.

## Main files

**Pre-push reproducibility checkpoint:** SHA-bound dated CSV/JSON files, collector/builders and the adopted target plan require byte-preserving Git attributes. The audit found Windows newline normalization would alter 17 hashed files; `.gitattributes` now preserves their original bytes, and staged blob hashes must match the 30 manifest input/output/builder checks before commit. This is byte preservation, not a new data derivation: 819 wet observations, 37 conditional proxies and zero training admission remain unchanged. [BUG-102](../../others/bug-log.md#bug-102-git-newline-normalization-breaks-sha-bound-research-replay). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

| File | Rows | Purpose |
| --- | ---: | --- |
| [pasig_wet_observations.csv](pasig_wet_observations.csv) | 819 | One place/time/source wet claim per row: 467 preserved original observations plus 352 newly captured observations. Use this as the combined wet-evidence table. |
| [proxy_label_register.csv](proxy_label_register.csv) | 37 | Conditional reported-subsidence projections sharing three outcomes, with reference clocks, bounds, scope conditions and provenance. All `training_admitted=false`. |
| [wet_followup_pairs.csv](wet_followup_pairs.csv) | 3 | July 24, 2025 same-named River Side streets reported wet again five hours later at lower depths. No inferred clearance or admitted censoring. |
| [dataset_manifest.json](dataset_manifest.json) | — | Input/output hashes, builder/collector revision, 35 source identities and 70 checked capture artifacts. |
| [additional-reports/sources.md](additional-reports/sources.md) | 8 sources | Publisher URLs, retrieval dates, text/HTML captures, checksums and observation IDs. |
| [additional-reports/observations.csv](additional-reports/observations.csv) | 352 | Collector v3 extraction from the new captures, before merged-layer metadata. |
| [parser-v3-replay/observations.csv](parser-v3-replay/observations.csv) | 398 | Offline reparse of the original 18 captures: 395 wet claims plus three summaries. These are alternate derivations of existing evidence, not additional records. |

Clearance observations (3), historical entries (12), DRRMO context (679) and locality duration references (8) remain in the [original separated working bundle](../pasig-duration-cleanup-20261004/README.md). Combining the wet table with the first two evidence categories gives **834 evidence records**. The DRRMO and consultation rows have different meanings and are not appended as wet claims or outcome labels.

## Collection and coverage

Eight additional official Pasig reports were captured with bounded ordinary HTTP requests, access-policy checks and immutable HTML/text checksums. All concern the existing July 21–25, 2025 reporting episode.

| Source | Parsed wet observations | Supported observation frames |
| --- | ---: | --- |
| PASIG-20250722-0345 | 38 | July 22, 03:45 |
| PASIG-20250722-0600 | 40 | July 22, 06:00 |
| PASIG-20250722-0900 | 87 | July 22, 08:00 and 09:00 |
| PASIG-20250722-1100 | 57 | July 22, 11:00 |
| PASIG-20250722-1500 | 109 | July 22, 14:00 and 15:00 |
| PASIG-20250722-2100 | 13 | July 22, 21:00 |
| PASIG-20250724-0600 | 5 | July 24, 06:00 |
| PASIG-20250724-1100 | 3 | July 24, 11:00 |

The current wet-observation year counts are **2021: 8; 2022: 3; 2023: uncollected; 2024: 80; 2025: 481; 2026: 247**. The three 2026 summaries are separate. The acquisition cutoff is October 5, 2026; 2026 is partial. These counts describe selected acquired reports, not annual flood frequency or independent storms. More repeated updates help track changes, but do not themselves establish additional subsidence outcomes.

## Targeted search outcomes

Two read-only search agents investigated older-year gaps and more recent follow-ups. Captured pages are cited individually in the source register above; inspected but unacquired leads are recorded here.

- Official [archive page 134](https://pasigcity.gov.ph/news-and-releases?page=134), [135](https://pasigcity.gov.ph/news-and-releases?page=135) and [136](https://pasigcity.gov.ph/news-and-releases?page=136) were accessible and inspected around July–September 2023. This pass did not recover a new qualified timed wet/subsidence pair there. Archive pagination can change; this is a search result at acquisition time.
- The [Manila Bulletin August 31, 2023 lead](https://mb.com.ph/2023/8/31/classes-work-suspended-in-ncr-provinces-due-to-heavy-rains-floods) remained blocked for full capture (HTTP 403). Search-visible Mega Market wording lacked a usable Pasig clock. A 13:00 reference concerned Pasay and cannot become a Pasig clearance time. DENR clipping access also remained blocked. No observation or label was added from these snippets.
- A November 8, 2024 official item describes quick subsidence generally without a qualified location/time pair; no duration label was added.
- A 2025 NDRRMC “Pasig” lead referred to Candaba, Pampanga; a separate Ortigas news lead had unresolved city assignment. Neither was admitted as new Pasig evidence.
- Eight accessible July 2025 official updates added 352 verified wet observations, including three supported depth-recession pairs. They added **zero** explicit clearance summaries. The existing three summary outcomes remain the complete acquired outcome set for this version.

No finding above proves that other records do not exist. The 2023 gap remains explicit. Further acquisition is an optional evidence improvement; it is not a prerequisite for finishing the evidence-based expiry lifecycle.

## Prediction target and proxy admission

The adopted [target contract](../../plans/pasig-reported-subsidence-target.md) estimates elapsed time from a supported wet reference until scope-matched **reported subsidence**. It is not an onset-to-end duration when onset is unknown. Physical dry conditions and vehicle passability require separate evidence.

The 37 projections are admitted for conditional collective-scope proxy analysis:

- Maybunga August 11: eight locations, `(0, 260]` minutes.
- Dela Paz August 18: one location, `(0, 120)` minutes; before 14:00, not the article's 23:00 response clock.
- August 30 retained list: 28 locations, `(0, 360]` minutes.

They share **three** summary observations; meteorological storm independence and measured physical sections are not established. The proxy register explicitly records these assumptions and keeps `training_admitted=false`. Its retrospectively selected last-wet references and unknown pre-outcome source availability prevent treating it as a validated prospective training/replay table. A later model builder must choose references without seeing future outcomes and use predictors actually available at issuance.

The three July 24 street pairs show lower reported depths at 11:00 than at 06:00. Tawi-Tawi and Callos disappearing from the later list is not clearance. Two wet observations alone also cannot exclude intervening subsidence/re-flooding, so the five-hour gap is not automatically an admitted right-censored duration.

## Collector v3 repairs and preservation

`backend/scripts/collect_flood_duration_pilot.py` now handles repeated-unit ranges, numeric-adjacent units, singular `foot`, explicit whole-centimeter rounding uncertainty, supported plain barangay headings, `4.Rosario`/`29..`/spaced numbering and canonical barangay qualifiers. An already emitted pending row cannot be reused for an unsupported following water-depth line. Raw measurement text remains preserved; genuine unit disagreements retain blank canonical numeric depths.

The original 398 observation identities/evidence/clocks and 37 candidate bounds are retained in a separate replay. A. Policarpio gains the supported San Joaquin heading and 5.08–7.62 cm range; 14 Greenpark observations retain 20 cm with rounding uncertainty; three genuine conflicting conversions remain blank. The replay has 33 extraction/review exceptions, including rounding flags and existing unsupported bullets/conflicts. It does not overwrite the old 32-exception v2 snapshot.

In the merged CSV, original raw fields and all v1 reviewed features remain unchanged. `parser_v3_*` columns show alternate derived values for the original official rows. New official rows carry v3 extraction and source qualification. Original non-pilot publisher rows keep their existing qualification; they were not reprocessed by this official-page parser. Canonical reviewed numeric features are `qualified_depth_cm_low/high`, with `depth_qualification` restrictions; raw columns can contain older disputed conversions and must not be used blindly as model features.

Independent read-only agents checked the new 352 rows against every captured location/depth/clock, the original replay, and the merged register. All 352 new IDs are unique; all 16 new capture hashes match. The merged builder verifies original raw-field preservation, all source versions/evidence, 35 source identities/70 artifact hashes and unchanged input bytes. No automated tests were added/run; no dependency, schema, live processing, trained model, deployment, commit or push is introduced.

## Rebuild offline

Run from the repository root with Python. These commands use cached captures; no new acquisition occurs. `--skip-figures` needs only the standard library.

```powershell
python backend/scripts/collect_flood_duration_pilot.py --seeds docs/evaluations/flood-duration-pilot-20261004/seeds.json --source-bundle docs/evaluations/flood-duration-pilot-20261004 --output docs/evaluations/pasig-duration-followup-20261005/parser-v3-replay --review-rules docs/evaluations/flood-duration-pilot-20261004/review_rules.json --skip-figures
python backend/scripts/collect_flood_duration_pilot.py --seeds docs/evaluations/pasig-duration-followup-20261005/additional-reports/seeds.json --output docs/evaluations/pasig-duration-followup-20261005/additional-reports --skip-figures
python backend/scripts/build_pasig_duration_followup.py
```

## Next implementation work

Complete the backend evidence/status lifecycle using the accepted freshness fallback, matched qualified updates and supported clearance. Resolve the pending storage/API and Unconfirmed routing/retention decisions in the publication plan; application schema changes still require approval. Keep optional prediction work separate: establish prospective references, predictor availability and enough independent outcomes before fitting empirical or interval-aware AFT models. Do not hold routine expiry implementation open while repeatedly searching for a minimum row count.
