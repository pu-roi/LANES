# Pasig and Metro Manila flood-evidence collection

> **Last Updated:** October 04, 2026, 10:24 PM (Asia/Manila)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Expanded evidence snapshot delivered; graph exports removed during cleanup. Historical collection remains incomplete. No training admission, fitted model or duration-accuracy result.

## Current result

The developer requested actual 2021–2023 collection and expansion beyond Pasig. This bundle combines the original 398-row Pasig pilot with newly captured NCR reporting. All retained records have source/version links. Counts measure collected evidence, **not flood frequency, independent incidents, or trained examples**.

| Measure | Current snapshot |
| --- | --- |
| New captured publisher articles | 17 articles: 15 GMA, one RMN and one OneNews; 341 extracted observations |
| New captured government document | NDRRMC Fabian/Habagat SitRep 10, public AHA Centre copy; 123 pages |
| Historical document records extracted | 14 page-47 rows: 12 Pasig and two Pateros |
| Original Pasig reports reused | 18 official captures; 398 observations |
| Combined evidence records | 753: **739 report observations + 14 historical incident records** |
| Pasig evidence records | 482: 470 report observations + 12 historical incident records |
| NCR geographic coverage | Evidence from 16 of 17 LGUs; San Juan remains unrepresented |
| Date-only report observations | 25; no hourly duration target inferred |
| New explicit road clearance-pair candidates | 5 Manila pairs across two dates, with unknown onset |
| New chronology exceptions | 8 unresolved earlier-clear/later-wet comparisons; retained, flagged, not duration labels |
| Training-admitted incidents / fitted models | 0 / 0 |

### Pasig data cleanup

The 482-row Pasig subset contains 467 reported-flood observations, 12 separate historical-document records and three clearance-summary observations. They come from 27 source identities. A row-level audit found **zero exact duplicate rows**, so no source observations were deleted. Sixteen observations have no supported hour/minute clock; they remain in the register with their date-only or missing-time status rather than being assigned invented times.

Rows can describe different roads or updates during the same flood period. The date-based storm groups are review aids, not confirmed independent storms. The pilot's 37 road-level clearance bounds are linked to only three shared clearance summaries and remain candidates, not training examples. The current duration-training dataset therefore remains empty. Keep uncertain, conflicting and incomplete records in the evidence register with flags so they can be reviewed without losing their sources.

Generated coverage and clearance graph files were removed from both evaluation bundles because the underlying CSV/JSON registers and plot scripts are retained. The figures can be regenerated when needed. Original source captures, manifests, exceptions and the NDRRMC page image remain in place.

### Pasig coverage and the uneven years

| Year | Report observations | Separate historical incident records | Interpretation |
| --- | ---: | ---: | --- |
| 2021 | 8 | 12 | Two GMA reports, RMN and a government table; includes provisional road aliases and correlated Fabian/Habagat reporting, not 20 independent storms |
| 2022 | 3 | 0 | C5/Ortigas, C5/Eagle and Julia Vargas; first two retain geography corroboration/alias review; Julia Vargas has an inferred date and no clock |
| 2023 | No captured Pasig row | 0 | A Pasig Mega Market article was identified but the full publisher body is blocked; no row fabricated from a search snippet |
| 2024 | 80 | 0 | Selected city updates and a regional report |
| 2025 | 129 | 0 | Selected detailed city updates |
| 2026 | 250 | 0 | Selected detailed city/regional updates, partial through October 4 |

The original 5/2/gap graph described a small collected sample. Recent reports contain long street lists and repeated snapshots, whereas the older-year search initially recovered only a few reports. This is a **collection imbalance**; it does not demonstrate a rise in flood frequency or better duration-model accuracy. The follow-up search added three date-only 2021 publisher observations, 12 separate historical incident records, and a 2022 Julia Vargas observation. The graph now distinguishes report observations from historical incidents.

The current Pasig archive was inspected via ordinary public pagination: pages 127–149 contain 2023 entries; September–December 2022 appears around pages 149–156; pages 157–180 are empty. This inspection found no listed 2021 or January–August 2022 entries, while old third-party reports remain accessible. Do not claim that all older records were deleted. The 2023 flood-safety page and 2022 storm-preparation/evacuation pages inspected do not establish road flooding or clearance.

## Sources and access gaps

Use [sources.md](sources.md) for the captured article/document citations, URLs, retrieval times, hashes, local evidence and observation IDs. It links the original 18 Pasig citations. [Collection search log](collection-search-log.md) records inspected archives, unsuitable reports and inaccessible leads. The project-wide [source register](../../research/flood-duration-data-sources.md) retains studies, datasets and acquisition leads.

- [Manila Bulletin: August 31, 2023](https://mb.com.ph/2023/8/31/classes-work-suspended-in-ncr-provinces-due-to-heavy-rains-floods): indexed Pasig Mega Market flood/subsided lead; actual body HTTP 403. No exact clock verified. The surrounding 13:00 clearance belongs to Pasay, never Pasig.
- [FOI Bagong Ilog request](https://www.foi.gov.ph/requests/flood-data-in-barangay-bagong-ilog/), [2022 workbook attachment](https://www.foi.gov.ph/documents/203508/Flooded_Areas_Bagong_Ilog_2022.xlsx): attachment returned temporary maintenance; workbook/schema/count/temporal fields not acquired.
- [2021 NDRRMC report](https://adinet.ahacentre.org/assets/uploads/supported_doc/20210802-SITUATION_REPORT_TCFABIAN-SWMonsoon-Aug1.pdf): saved original PDF and layout text; page 47 rendered and visually inspected. Its **Date/Time of Occurrence** and **Status** columns are different facts. Preserve reported occurrence separately; the report issue time is only an as-of bound for status, never an exact physical clearance timestamp.
- [`pasig_duration_reference_claims.csv`](pasig_duration_reference_claims.csv): eight locality-level duration/depth descriptions transcribed from Pasig's adopted 2023–2028 DRRM plan. They are context-only community/planning summaries, not dated flood observations or model labels.

`access_leads.json` records inaccessible leads separately from successful captures. The publisher manifest's zero failures describes its selected capture seeds only; it does not imply every research lead was obtainable. Public access does not establish a redistribution license. Captures are retained for research provenance; reuse terms remain unverified.

## Candidate bounds and quality review

`pairing_rules.json` explicitly matches five Manila road identities and qualified source clocks. Remaining-time bounds are `(0, 20]`, `(0, 85]`, `(0, 25]`, `(0, 70]` and `(0, 34]` minutes. These are **candidate report-based intervals after the last wet report**, conditional on correct clock interpretation and incident continuity. They are not total flood duration, exact clearance measurements, or predictions. The 2025 city-wide list has chronology conflicts elsewhere, so even positive pairs retain source-clock/continuity qualification requirements.

Eight nonpositive wet/clear comparisons remain in `exceptions.csv`; flags are attached to the affected observations. A contradiction can reflect stale list entries, reflooding or unresolved section scope; it does not establish that one source is false. None becomes a negative duration. Historical depth/passability beside `SUBSIDED` remains source text; canonical current depth is blank.

An independent LANES review identified and corrected depth/passability copied into road identities, recovered explicit four-foot depths, and added the actual 20:30 source-clock line to all 56 August 17 Pasig observations. All reviewed text lines, HTML date evidence and capture hashes are checked by the offline builder. Approximate body-depth words remain qualitative. Ambiguous city/road aliases retain flags; date-only claims stay date-only.

The date-based `storm_group` is a conservative grouping aid, **not a verified independent-storm ID**. Consecutive dates can belong to one storm and need further reconciliation before any evaluation split. Base Pasig 37 summary-linked bounds across three clearance episodes remain separately available in the [original pilot](../flood-duration-pilot-20261004/README.md); they are not upgraded to observed road-level outcomes here.

## Files and reproducible coverage summaries

- `observations.csv/json`: combined evidence register, including explicitly labelled historical incident records.
- `pasig_observations.csv/json`: Pasig subset with the same record-type distinction.
- `historical_incidents.csv/json`: separate document-derived occurrence/status records.
- `source_manifest.json`, `document_manifest.json`, `sources/`: versioned original evidence and normalized text.
- `review_rules.json`, `document_review_rules.json`, `pairing_rules.json`: reproducible source interpretation and explicit candidate matching.
- `candidate_clearance_bounds.csv/json`, `exceptions.csv`, `coverage.json`: candidates, conflicts and current coverage.
- `coverage.json` retains the coverage counts and missingness summaries.
- Generated graph exports were removed to keep the evidence bundle focused. `backend/scripts/plot_flood_report_archive.py` can regenerate them from the saved register when needed.

These coverage summaries describe collected records, not independent floods or model results. Model-result graphs remain a separate future deliverable if fitting/evaluation is justified. The data builder completed an offline rebuild. No automated tests, database writes or application lifecycle changes were performed.

## Reproduce from the saved evidence

From the repository root, using the existing backend environment:

```powershell
backend/venv/Scripts/python.exe backend/scripts/collect_flood_report_archive.py --seeds docs/evaluations/metro-manila-flood-duration-20261004/seeds.json --output docs/evaluations/metro-manila-flood-duration-20261004 --rules docs/evaluations/metro-manila-flood-duration-20261004/review_rules.json --base docs/evaluations/flood-duration-pilot-20261004 --pairs docs/evaluations/metro-manila-flood-duration-20261004/pairing_rules.json
backend/venv/Scripts/python.exe backend/scripts/plot_flood_report_archive.py docs/evaluations/metro-manila-flood-duration-20261004
```

The offline build requires both source bundles. It verifies saved document/article hashes and reviewed evidence without fetching or touching application settings. Optional `--collect` obtains approved publisher seeds with bounded retries/cache/access-policy checks; reviewed source versions must be requalified after a new capture. PDF extraction was performed with the bundled research runtime; saved document rules rebuild with the collector's standard library only. NumPy and Matplotlib are already recorded backend dependencies.

## What remains before duration-model training

Continue older-year and NCR coverage collection, resolve duplicate/alias/clock/continuity issues, recover outcomes from more independent storms, and collect compatible rainfall/hydrologic predictor histories. Decide which records support an interval-censored target and which are only context. More years and street snapshots are helpful evidence, but they do not supply missing physical clearance truth. Compare survival methods, simple baselines and quantile approaches only after training/evaluation admission; no accurate expiry claim is currently supported.
