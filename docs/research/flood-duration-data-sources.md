# Flood duration dataset: source register

> **Last Updated:** October 04, 2026, 6:52 PM (Asia/Manila)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Expanded current register: 753 evidence records (739 report observations and 14 separate historical incidents), 36 captured source files across the two bundles, 16 NCR LGUs. Older Pasig acquisition remains incomplete; no training admission/model.

## Purpose and collection scope

This is the human-readable citation and provenance register for data collected for the LANES flood-duration study. Keep it updated throughout collection so the capstone documentation can identify the original source of each observation and derived incident record.

Target **2021–2026**, beginning January 1, 2021 and ending at the recorded collection cutoff (initially October 4, 2026, Asia/Manila). This spans six calendar years; 2026 is partial/year to date. Include qualifying 2026 sources in the register and reserve previously unused later storm groups for evaluation when feasible. Sources verified so far do not establish complete coverage of all target years. The [literature review](metro-manila-flood-duration-rrl.md) holds studies/methods and additional acquisition leads; the [study plan](../plans/flood-evidence-lifecycle-and-duration-plan.md) defines dataset construction and model gates.

## Current acquisition: older Pasig years and NCR expansion

The [expanded register](../evaluations/metro-manila-flood-duration-20261004/README.md) is the current data/figure snapshot. Its [sources.md](../evaluations/metro-manila-flood-duration-20261004/sources.md) supplies 17 newly captured publisher articles and one NDRRMC PDF, alongside links to the original 18 official Pasig captures. The [search/access log](../evaluations/metro-manila-flood-duration-20261004/collection-search-log.md) documents older archive pagination, blocked files, inspected government reports and exclusion reasons.

Pasig now has **2021: eight report observations plus 12 historical incident records; 2022: three report observations; 2023: a capture gap; 2024: 80; 2025: 129; 2026: 250**. Two 2021 city assignments and two 2022 road assignments retain context/geographic alias qualifications. The Julia Vargas 2022 report has a date inferred from the contemporary storm section but no clock. Counts measure evidence acquired, not independent floods or training labels. The supplied depth/location CSV remains for plotting/context, not duration targets.

The NDRRMC 2021 table occurrence date/time is kept separately from latest Subsided status and report issue time. No exact clearance is fabricated. Five additional Manila remaining-time candidates across two dates remain unadmitted; eight conflicting chronological pairs are retained as exceptions. Complete archives, matched outcomes across independent storms and compatible predictors remain pending.

## Required record for every collected source

Each collected report receives a stable source ID and Markdown entry containing:

- Publishing organization/author, original title, canonical URL and supported publication date.
- Actual observation date/time(s), separately from publication/fetch time, with timezone and uncertainty.
- Named geographic scope and available fields, such as water depth, flooding, clearance and passability.
- Access/retrieval time, capture/version ID, content checksum and relative local snapshot path once captured.
- Collection and dataset-admission status: fetched, failed, duplicate/version, excluded, awaiting review or admitted, with reason.
- Observation/incident IDs derived from the source, including matched clearance source IDs and any interpretation limits.
- Reuse/license or published access-policy findings; leave unverified terms explicit.

The collector must update this register alongside its machine-readable manifest. Every admitted observation and derived duration bracket must reference the corresponding source ID and captured version. A report containing several observation clocks has one source entry with multiple observation records. Preserve revisions and original URLs; never substitute a search-result page for the publisher URL. Failed/excluded sources remain documented in the collection log/register without becoming training evidence.

## Earlier research: acquisition status and priority

Reading a paper, inspecting a published table or identifying a download/request link is not acquisition of its underlying dataset. The sources below remain recorded; they have not been silently removed from the plan. Raw data are not assumed to be available merely because a paper used them.

| Source ID and earlier source | What was actually inspected or available | Underlying data still missing | Role and priority |
| --- | --- | --- | --- |
| RRL-MARIKINA-2018 — [Marikina Flood Hazard Models Using Historical Data of Water Level](https://philjournalsci.dost.gov.ph/marikina-flood-hazard-models-using-historical-data-of-water-level/), [institutional full text](https://research.ateneo.edu/ws/portalfiles/portal/39983793/Marikina%20flood%20hazard%20models%20using%20historical%20data%20of%20water%20level.pdf) | Full paper and published river-threshold duration tables reviewed. | Original MMDA-EFCOS hourly records and recent compatible histories have not been obtained. Published tables have not been extracted into a versioned dataset. | Retain for RRL, river-context methods and optional benchmark reconstruction. Prefer recent records for current prediction; older paper data need not block the first Pasig collection. |
| RRL-JICA-2010 — [Ondoy/Pepeng Needs Assessment Study](https://openjicareport.jica.go.jp/pdf/11999422_01.pdf) | Report and historical surveyed duration-map evidence reviewed. | Original NAMRIA/DPWH field-survey records and machine-readable GIS duration layers have not been obtained. | Retain as historical observed-event context. Supplemental reconstruction only; not the primary 2021–2026 training source. |
| RRL-JICA-2014 — [Metro Manila transport roadmap, environment/hazard technical report](https://openjicareport.jica.go.jp/pdf/12149621.pdf) | Report's reproduced simulated-duration map reviewed. | Original World Bank/DPWH scenario rasters/time series and model inputs have not been obtained. | Retain as simulated regional context; separate from observed labels. Optional acquisition if useful for comparison. |
| RRL-VAMCO-2024 — [Serrano, Herrera and Naito: Marikina floodplain hydraulic analysis](https://doi.org/10.5194/piahs-386-121-2024) | Full 2024 article reviewed; it analyzes the 2020 Vamco/Ulysses event. | Processed model outputs, available upon author request, have not been obtained. Raw agency inputs also remain unacquired. | Retain for RRL and a possible hydraulic comparison/features pathway. Author outreach requires user authorization and has not occurred. |
| RRL-LAKE-2024 — [Herrera and Naito: Laguna Lake hydrodynamic investigation](https://doi.org/10.5194/piahs-386-95-2024) | Published shoreland/lake scenarios reviewed. | Processed model data not obtained; publisher-table XLSX retrieval failed during research. | Retain for lake/backwater mechanisms. Scenario recovery cannot be assigned as a current street-clearance timer. |
| PASIG-DRRM-2023 — [Pasig City DRRM Plan 2023–2028](https://drive.google.com/file/d/1fi43-iCC1n9ruUgBRcu_2zl4wGQ0vkSZ/view), [official release](https://www.foi.gov.ph/agencies/usap/pasig-city-drrm-plans/) | Original released PDF's readable text and Table 19 consultation ranges inspected. Raw local PDF download failed. | Incident-level basis, consultation sample counts and timestamped flood/clearance logs not obtained. | Retain as locality context; no synthetic event labels from aggregate ranges. Recent official updates below are the primary pilot acquisition route. |
| NOAH-CONTEXT — [UP DREAM hazard maps](https://dream.upd.edu.ph/products/flood-hazard-maps/), [NOAH Studio](https://noah.up.edu.ph/noah-studio) | Static local-asset findings are documented in the existing [placement audit](../plans/lipad-noah-flood-placement.md). Public product descriptions were reviewed. | Supported dynamic API/archive access and temporal simulation outputs have not been verified/acquired. | Existing susceptibility assets can provide context. Dynamic products remain conditional; neither is a clearance-label source by default. |
| WEATHER-CONTEXT — [PAGASA basin system](https://pasig-marikina-tullahanffws.pagasa.dost.gov.ph/about/aboutus.do), [Open-Meteo historical forecast documentation](https://open-meteo.com/en/docs/historical-forecast-api) | Monitoring/API documentation reviewed. | A matched historical weather/river/lake feature export for the duration register has not been collected. | Supporting acquisition after incident identity/time audit. Preserve as-of availability and distinguish observed, forecast and reanalysis inputs. |
| GOOGLE-FORECAST — [Flood Forecasting API](https://developers.google.com/flood-forecasting) | Provider documentation and broad capability/coverage descriptions reviewed. | LANES access, actual NCR footprints and usable historical/live exports not established. No authenticated forecasting calls made. | Optional provider trial; do not block initial official-road-report collection or treat forecasts as observed clearance. |
| GOOGLE-HISTORY — [Flood resources](https://sites.research.google/gr/floodforecasting/resources/), [Groundsource dataset record](https://zenodo.org/records/18647054) | Dataset descriptions and Groundsource landing metadata inspected. | Groundsource file not downloaded; NCR subset, temporal/clearance schema and reuse terms remain unverified. GRRR/inundation exports not acquired. | Optional global context/discovery. Assess usable fields before adding any records to the training register. |
| OTHER-CONTEXT — [NASA IMERG](https://gpm.nasa.gov/data/imerg), [Open-Meteo Flood API](https://open-meteo.com/en/docs/flood-api), [Copernicus flood monitoring](https://emergency.copernicus.eu/news/gfm-now-includes-data-from-sentinel-1c/) | Official product documentation reviewed in the [initial research](flood-expiry-and-duration-research.md). | No matched export was collected for this duration study. | Optional rainfall/river/satellite context if local availability and validation justify it; never infer clearance from non-detection. |
| EXISTING-PASIG-CSV — local [cleaned historical CSV](../../data/flooded_areas_pasig_clean.csv) | Existing repository file audited; location/depth records available. | It contains no onset/clearance/duration targets. | Retained primarily for plotting. Optional context only if measured useful; not a required duration dataset. |

**Collection order:** recent dated LGU/MMDA flood and explicit clearance observations first; matched weather/hydrologic context next; historical or simulated raw outputs if they add measurable value. Literature sources remain in the [RRL bibliography](metro-manila-flood-duration-rrl.md), including additional surveys and methods papers. Those papers do not all require acquisition of their original datasets to proceed with the pilot.

**Current readiness:** the [first public-report pilot](../evaluations/flood-duration-pilot-20261004/README.md) now contains saved captures and candidate temporal registers. There is no completed 2021–2026 archive or training-admitted duration dataset yet. Recent 2026 summary links supply 37 candidate bounds, but they share only three clearance episodes; correlated rows cannot establish multi-storm model accuracy.

## First collected pilot: actual files and complete citations

The [pilot source register](../evaluations/flood-duration-pilot-20261004/sources.md) documents **every one of the 18 collected reports**, including original titles/URLs, capture times, hashes, version paths and observation IDs. The [machine-readable manifest](../evaluations/flood-duration-pilot-20261004/source_manifest.json) and [observation register](../evaluations/flood-duration-pilot-20261004/observations.csv) retain provenance. The expanded pilot has 395 wet observations and three clearance summaries, covering selected 2024–2026 reports. Its [37 location-bound candidates](../evaluations/flood-duration-pilot-20261004/candidate_incidents.csv) remain not training-admitted; onset is unknown and clearance scope is inferred from reported summaries.

In addition to the seven original report examples below, the batch includes July 21, 2025 reports at 19:00, 22:00 and 23:45; August 18, 2026 reports at 00:30, 04:30 and noon; and the August 18 late-evening response report with an explicit **before 14:00** clearance statement. All original links are in the complete pilot source register. The [exception list](../evaluations/flood-duration-pilot-20261004/exceptions.csv) preserves one same-place/time conflict as two rows. Reuse terms remain unverified. The bounded collector has not scanned archive pagination or collected 2021–2023.

### Second bounded collection batch: October 4, 2026

Four newly saved official sources add **122 candidate observations**: [September 2, 2024](https://pasigcity.gov.ph/news-and-releases/flood-update-september-2-2024-929) (31), [July 23, 2025, 09:00](https://pasigcity.gov.ph/news-and-releases/flood-update-as-of-0900am-july-23-2025-580) (14), [July 25, 2025, 23:30](https://pasigcity.gov.ph/news-and-releases/flood-update-as-of-1130pm-july-25-2025-533) (20), and [August 29, 2026, 20:30](https://pasigcity.gov.ph/news-and-releases/southwest-monsoon-habagat-flood-update-as-of-830-pm-of-august-29-2026-903) (57). Capture paths, hashes and row identities are in the complete pilot source register. Totals: 18 sources, 398 observations, six candidate continuity groups and 14 barangays. The 37 candidate bounds still share three clearance episodes; these pages provide no additional explicit matched clearance endpoint.

The v2 rebuild records 32 exceptions: 16 alternate-unit disagreements, 14 bullets needing attribution review and two same-clock depth-conflict rows. The unit check conservatively flags differences over 0.25 cm, including possible rounding; it does not decide which source value is true. Canonical numeric depth stays blank for flagged rows. The September page has additional later road lists without repeated explicit flood attribution; these remain saved text/review exceptions rather than automatically completed labels.

**Earlier-year discovery:** Bounded indexed searches for official Pasig flood updates in 2021, 2022 and 2023 did not locate usable dated incident reports in this pass. This is not an exhaustive archive scan or evidence of no flooding. A [GMA July 25, 2021 report](https://www.gmanetwork.com/news/topstories/metro/796691/list-flooded-areas-in-metro-manila-on-sunday-july-25-2021/story/) is an unacquired alternate-publisher lead; the present capture/parser supports only official Pasig article pages. The official [September 25, 2022 Karding safety advisory](https://pasigcity.gov.ph/news-and-releases/kasalukuyang-nakataas-ang-tropical-cyclone-wind-signal-twcs-no-3-sa-metro-manila-kaugnay-ng-super-typhoon-kardingph) supplies preparedness information rather than matched wet/clear duration labels and was not added to the incident register. Archive pagination remains pending; one browser fetch of the archive index timed out. Keep 2021–2023 uncollected in coverage.

[UrbanFlood24 metadata](../evaluations/flood-duration-pilot-20261004/urbanflood24_metadata.json) is also now saved with a checksum in the pilot report. The 19.6 GB simulation archive itself remains unacquired. Literature/metadata files and empirical flood observations remain distinct.

## Initial verified report sources

### Recent research and downloadable supplemental data checked October 4

| Source ID | Original source and actual access status | Intended contribution and limitations |
| --- | --- | --- |
| RRL-BALANGA-2026 | [Cruz et al., 2026](https://doi.org/10.3389/frwa.2026.1775842); online article, public tables and availability statement inspected October 4, 2026. No raw time-series export or dedicated supplementary file acquired. | Rainfall pattern/antecedent-wetness and river-recession context. Six modeled storms, including 2024–2025, in Balanga; indirect calibration and qualitatively inferred wetness. Does not supply NCR road-clearance labels. |
| SIM-URBANFLOOD24 | [Author dataset page](https://holmescao.github.io/datasets/urbanflood24), [official Figshare dataset](https://figshare.com/articles/dataset/28082549), [Figshare metadata API](https://api.figshare.com/v2/articles/28082549). Metadata directly retrieved October 4; DOI `10.6084/m9.figshare.28082549.v1`; December 30, 2024; CC BY 4.0; `urbanflood24.zip`, 19,619,322,176 bytes; [direct archive](https://ndownloader.figshare.com/files/51407804); supplied MD5 `91f394ad0388d457358a9b38645c88fe`. | Public simulated depth series and geographic inputs, associated with the 2025 U-RNN study. Archive contents not downloaded/inspected/admitted. Potential method-development dataset; cannot establish Pasig/NCR accuracy. Evaluate a bounded subset, recession endpoint and cross-location transfer before use. |
| GOOGLE-HISTORY — follow-up | [Official Groundsource introduction, March 12, 2026](https://www.research.google/blog/introducing-groundsource-turning-news-reports-into-data-with-gemini/); [existing dataset release](https://zenodo.org/records/18647054). Methodology and download metadata reviewed again October 4. No archive file or NCR subset acquired. | Public news-derived event-discovery candidate. Timing semantics and local duration-label usefulness remain unverified. Do not equate extracted event dates with confirmed street clearance. |

The [recent RRL follow-up](metro-manila-flood-duration-rrl.md#10-recent-study-supplementation-without-waiting-for-external-requests) distinguishes input features, background priors, simulation records and actual outcome labels. These entries are metadata/literature checks, not completed dataset acquisition. No external request is required before proceeding with accessible official-report collection.

### Official report examples

**Publisher for all entries below:** City Government of Pasig. **Access date:** October 4, 2026 (Asia/Manila). Dates below are displayed report dates; embedded observation clocks must be retained individually. Source IDs identify this register, not independent flood events.

| Source ID | Report date | Original title / canonical source | Research inspection and possible use |
| --- | --- | --- | --- |
| PASIG-20240725-0400 | 2024-07-25 | [FLOOD UPDATE — As of 04:00AM July 25, 2024](https://pasigcity.gov.ph/news-and-releases/flood-update-as-of-0400am-july-25-2024-601) | Publisher text available through indexed retrieval. Contains several dated snapshots and road flood/passability information. No exact clearance inferred from a missing road. |
| PASIG-20240725-1700 | 2024-07-25 | [FLOOD UPDATE — As of 5:00PM July 25, 2024](https://pasigcity.gov.ph/news-and-releases/flood-update-as-of-500pm-july-25-2024-968) | Publisher text inspected. Preserves multiple observation clocks; continued flooding and bridge closure need separate meanings. Candidate follow-up within the same weather episode. |
| PASIG-20250723-1700 | 2025-07-23 | [FLOOD UPDATE (as of 05:00PM — July 23, 2025)](https://pasigcity.gov.ph/news-and-releases/flood-update-as-of-0500pm-july-23-2025-749) | Publisher text inspected. Named localities and depth values are potential positive observations; does not independently establish clearance. |
| PASIG-20260810-0030 | 2026-08-10 | [Southwest Monsoon (Habagat) — Flood Update as of 12:30 am of August 10, 2026](https://pasigcity.gov.ph/news-and-releases/southwest-monsoon-habagat-flood-update-as-of-1230-am-of-august-10-2026-588) | Official HTML directly retrieved during research. Positive Maybunga observations; onset unknown. Candidate linkage to the following source. |
| PASIG-20260811-0950 | 2026-08-11 | [Enhanced Southwest Monsoon (Habagat) — Flood Update as of 9:50 am of August 11, 2026](https://pasigcity.gov.ph/news-and-releases/enhanced-southwest-monsoon-habagat-flood-update-as-of-950-am-of-august-11-2026-502) | Official HTML directly retrieved. Earlier 05:30 flooded snapshot plus 09:50 reported subsidence summary. Candidate clearance bracket, subject to matched scope/continuity review. |
| PASIG-20260829-2230 | 2026-08-29 | [Southwest Monsoon (Habagat) — Flood Update as of 10:30 pm of August 29, 2026](https://pasigcity.gov.ph/news-and-releases/southwest-monsoon-habagat-flood-update-as-of-1030-pm-of-august-29-2026-757) | Official HTML directly retrieved. Positive Dela Paz observations; candidate linkage to the next source. |
| PASIG-20260830-1100 | 2026-08-30 | [Southwest Monsoon (Habagat) — Flood Update as of 11:00 am of August 30, 2026](https://pasigcity.gov.ph/news-and-releases/southwest-monsoon-habagat-flood-update-as-of-1100-am-of-august-30-2026-965) | Official HTML directly retrieved. Earlier 05:00 flooded snapshot plus 11:00 reported subsidence summary. Clearance is based on barangay reports, not individual instrument timestamps. |

These entries originally recorded research access only. They have now been captured in the first bounded pilot, with persistent raw files/checksums and derived observation IDs in the linked complete source register. Training admission and reuse-term review remain pending. Multiple nearby locations or clocks in one episode remain grouped.

## Acquisition leads: records not yet obtained

| Lead ID | Organization and source | Status and limitation |
| --- | --- | --- |
| MMDA-2026-HISTORY | MMDA, [Historical flood reports in Metro Manila (2022 to 2025)](https://www.foi.gov.ph/agencies/mmda/historical-flood-reports-in-metro-manila-2022-to-2025/) | Final response states information was emailed to the requester. LANES has not obtained or inspected the file/schema. |
| MMDA-2026-LOGS | MMDA, [SmartCommutePH: Historical Flood Logs and Flood Prone Areas Data Requst](https://www.foi.gov.ph/agencies/mmda/smartcommuteph-historical-flood-logs-and-flood-prone-areas-data-requst/) | Visible request status Accepted; requests 2024–2025 onset and clearance fields. No released training file verified. |
| MMDA-2026-RAIN | MMDA, [DATA REQUEST: Hourly Rainfall Data of Marikina River Basin](https://www.foi.gov.ph/agencies/mmda/data-request-hourly-rainfall-data-of-marikina-river-basin/) | Response states information was emailed. Actual coverage, values and permitted reuse require obtaining the files. |

Acquisition leads are not dataset observations. No agency/author message has been sent. Consult the literature review for separate consultation, survey and simulation evidence; preserve those evidence classes if acquired.

## Citation format for research documentation

Use the recorded publisher, publication date and original page title, followed by the canonical link. For example:

City Government of Pasig. (2025, July 23). *FLOOD UPDATE (as of 05:00PM — July 23, 2025).* [Original report](https://pasigcity.gov.ph/news-and-releases/flood-update-as-of-0500pm-july-23-2025-749). Accessed October 4, 2026.

Keep access/capture dates because these update pages can change. Add new sources when collected; do not assign the initial access date to future retrievals. The final evaluation report must identify the source-register/manifest version used and link exported graphs to that dataset version.
