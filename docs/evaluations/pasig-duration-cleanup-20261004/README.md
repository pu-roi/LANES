# Pasig flood-duration data cleanup, 2021–2026

> **Last Updated:** October 05, 2026, 12:58 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Pasig-only working dataset; no duration examples admitted for model training.


**Latest working version:** See the [October 5 follow-up](../pasig-duration-followup-20261005/README.md) for 819 combined wet observations and purpose-specific proxy admission. This dated bundle remains preserved; its counts and original review verdicts are not overwritten.

## Scope and preservation

This bundle prepares the currently gathered Pasig evidence for the automatic-expiry study. It covers January 1, 2021 through the collection cutoff, October 4, 2026; 2026 is partial. Every exported row is scoped to Pasig City. The NCR-wide source bundle remains unchanged because it supports Metro Manila news collection and automatic plotting.

The exports are separated by what each record can actually tell us. They are not combined into a single table that could make a planning estimate or location-history row look like a measured flood outcome. Original source captures are preserved in their source bundles; exported rows retain source IDs, URLs, evidence text, timestamps and review flags. The 12 NDRRMC evidence strings have leading layout whitespace trimmed in the CSV export; their wording is unchanged, and the original PDF/text capture retains the source layout.

## Export inventory

| File | Rows | Meaning | Duration-model use now |
|---|---:|---|---|
| `flood_observations.csv` | 467 | Source-linked reports that observed flooding. | Possible inputs after incident grouping; not duration labels by themselves. |
| `clearance_observations.csv` | 3 | Pasig summaries reporting that flooding subsided. | Candidate outcome evidence; linkage to individual roads remains an inference. |
| `candidate_duration_intervals.csv` | 37 | Road/location bounds formed by matching wet reports to the three clearance summaries. | Candidate intervals only; all remain unadmitted because roads share summary outcomes and continuity is assumed. |
| `historical_incidents.csv` | 12 | Pasig rows in the 2021 NDRRMC report. | Historical event/status context; occurrence time is not an exact road-clearance time. |
| `drrmo_location_context.csv` | 679 | Cleaned Pasig DRRMO rows with source-year headings 2021–2025. | Location/depth context only; these rows have no event observation or clearance time. |
| `local_duration_references.csv` | 8 | General Pasig area-level duration descriptions from the DRRM plan. | Context/prior only; not dated incident outcomes. |
| `quality_summary.csv` | 15 checks | Reproducible counts for duplicates, clocks, review status, interval dependence and year coverage. | Audit summary; not model data. |
| `dataset_manifest.json` | — | Scope and row-count summary. | Reproducibility metadata. |

## Checks and cleaning decisions

- The source Pasig observation subset contained 482 rows, all already marked `city=Pasig`; the export filters for Pasig again. No other NCR city rows are included here.
- There were **zero duplicate observation IDs and zero exact duplicate observation rows** in that 482-row source subset. Repeated updates and reports are retained because they can form a flood timeline; they are not counted as independent floods.
- The 482 rows separate into 467 wet observations, three clearance summaries and 12 historical-document records. The 37 candidate intervals are a second, derived view of some wet reports and summary outcomes; do not add them to the observation count.
- Wet-observation counts by year: 2021: 8; 2022: 3; 2023: 0; 2024: 80; 2025: 129; 2026: 247. The 2023 gap is still a data-collection gap, not evidence that no flooding occurred.
- Four of the 467 direct flood observations lack a supported observation clock. The 12 NDRRMC records store occurrence/status information in different fields; their status clock is not an exact clearance time.
- The 37 candidate intervals come from three shared 2026 summary episodes (8, 1 and 28 locations). A shared summary does not create 37 independent clearance outcomes. Every candidate retains its source IDs and limitations.
- Of the 467 direct flood observations, 395 remain at `candidate` review status and 72 are source-reviewed candidates; neither group is a validated duration outcome. Four lack a supported observation clock. The register also retains 16 alternate-unit disagreements and three potential cross-source duplicate flags for review rather than silently dropping or resolving them.
- Exact duplicate full rows were also absent from the 679-row DRRMO context export. Repeated locations are retained because repeated year/place/depth context is not enough to identify duplicate incidents.
- The DRRMO CSV's `source_year` is the year-heading of an annual source section, not the date of a flood observation. Its 2021–2025 rows provide place/depth context only. The source contains no 2026 rows; the 47 records from 2020 are outside this requested study window and remain untouched in the original file.
- Missing values remain blank; no onset, exact clearance time, storm identity, dry condition or absent-year zero was invented. Original review flags and evidence text remain attached, with the NDRRMC whitespace normalization noted above.
- **Training-admitted duration examples: zero.** The current work is a cleaned, source-linked evidence bundle and candidate-label register, not a model-ready training set.

## Recommended next data step

The first source/timeline review is now delivered in the [October 5 qualification bundle](../pasig-duration-qualification-20261005/README.md). Use its derived corrections, candidate timelines and purpose-specific verdicts alongside these preserved original exports. Three summaries are usable reported-subsidence evidence; 37 physical-section outcomes remain uncertain and no model labels are admitted. The original CSVs in this folder remain unchanged.

Review the three shared clearance episodes and the 2021 NDRRMC entries against their original captures, qualify location aliases and clock meaning, then search for more Pasig-specific 2023 reports and dated DRRMO/MMDA follow-up or reopening records. Only after event-level wet-to-clear evidence is reviewed should a training table be assembled. Keep one row per supported incident/section outcome, linked to its multiple observation rows and source records.

## Independent verification

Two read-only reviews independently checked this export. The row audit confirmed that the 467 wet, three clearance-summary and 12 historical rows partition the original 482 Pasig rows with no missing/extra IDs; all event rows are Pasig, year counts and review flags match, and the 679 DRRMO rows exactly match the 2021–2025 subset in both cleaned source CSV copies. The interval audit confirmed all 37 wet/clearance/support IDs and calculated bounds against the captured sources and rules. The 37 candidates form only three shared summary outcomes and correctly remain unadmitted. Neither review found a row-count or interval correction. The CSV-export whitespace normalization for NDRRMC evidence is disclosed above; the original PDF/text captures remain available.

## Source locations

- [Original Pasig source captures](../flood-duration-pilot-20261004/sources/) and [their source register](../flood-duration-pilot-20261004/sources.md)
- [Additional Metro Manila and NDRRMC source captures](../metro-manila-flood-duration-20261004/sources/) and [their source register](../metro-manila-flood-duration-20261004/sources.md)
- [Expanded NCR register and Pasig subset](../metro-manila-flood-duration-20261004/README.md)
- [Original Pasig duration pilot and candidate bounds](../flood-duration-pilot-20261004/README.md)
- [Pasig DRRMO clean source CSV](../../../data/flooded_areas_pasig_clean.csv)
- [Pasig area-level duration-reference claims](../metro-manila-flood-duration-20261004/pasig_duration_reference_claims.csv)
- [Lifecycle and model investigation plan](../../plans/flood-evidence-lifecycle-and-duration-plan.md)
