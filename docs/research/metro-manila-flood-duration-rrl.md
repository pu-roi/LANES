# Metro Manila flood duration and automatic recession: literature review

> **Last Updated:** October 04, 2026, 6:52 PM (Asia/Manila)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Literature review and recent-data follow-up documented. Survival investigation and a two-hour Unconfirmed fallback for insufficiently supported locations accepted. No trained duration model or runtime change.

## 1. Answer and recommended direction

There are viable ways to automate the lifecycle and develop local recession estimates. The absence of a duration column in the existing Pasig CSV does not make the problem unsolvable. This review found a separate official Pasig document with duration estimates, local river-duration studies, historical duration maps, time-dependent hydraulic models, and public clearance advisories.

**Recommended research direction:** combine current evidence, qualified local duration information, rainfall/river/lake context, and a validated time-to-clearance estimator. Use **Active / Unconfirmed / Cleared** for observational status and a separate **estimated recession window** for predictions. Stale observational support becomes Unconfirmed; a matched credible clearance update can establish Cleared automatically. Predictions may assist an evaluated adaptive evidence policy, but cannot establish observed clearance.

The developer revised the policy: **two hours after the latest eligible supported flood observation, locations without enough validated duration support become Unconfirmed**. Survival analysis remains an accepted research family. A final adaptive model, adaptive bounds and map-retention thresholds are pending. Expiry cannot imply physical clearance or road safety. See the [implementation study plan](../plans/flood-evidence-lifecycle-and-duration-plan.md) and the recent-data follow-up below.

The recommendations below are **LANES interpretations of the literature**, not claims that the cited studies validated this application.

## 2. Important new Pasig finding

**Pasig City, Disaster Risk Reduction and Management Plan 2023–2028**, Table 19, *Hazard Characterization, by Barangay, Pasig City, 2021*, explicitly includes a **Duration** column. Its method describes consultations with barangay representatives and stakeholders. Selected unambiguous rows:

| Affected locality named in the table | Reported duration |
| --- | --- |
| Santolan: riverside and western areas | 3–5 days |
| Manggahan: Teacher’s Village, Metroville and Trinidad homes | 1–2 days |
| Ugong: Puroks 1, 2 and 4, riverside and Valle Verde | Under one hour |
| Bagong Ilog: Puroks 2–5 | 3–7 days |
| Pineda: Mabanta Compound, Purok 4 | One hour |

[Official city FOI release](https://www.foi.gov.ph/agencies/usap/pasig-city-drrm-plans/) · [Released DRRM plan](https://drive.google.com/file/d/1fi43-iCC1n9ruUgBRcu_2zl4wGQ0vkSZ/view).

These are **consultation-based locality summaries**, not timestamped incident records or timers to copy into LANES. Preserve their spatial scope, year and uncertainty. Verification used the original city-released PDF’s readable extraction through Drive; its repeated page-number field is malformed, so cite Table 19 rather than an inferred page. Ambiguous multiline rows were excluded.

This complements, rather than changes, the [726-row CSV/workbook audit](flood-expiry-and-duration-research.md#2-local-pasig-data-audit): that dataset still has no onset/clearance/duration fields. The developer retains it primarily for automatic plotting; the duration study does not depend on it. Optional historical location/depth features may be evaluated for measured benefit. Do not attach one consultation range to every CSV row and count them as independent training incidents.

## 3. Local literature and available duration evidence

### A. Statistical river duration

**de Lara-Tuprio, E. P., Bautista, E. P., Marcelo, R. M., Bataller, R. T., Esteban, D. A. B., & Yutuc, Y. P. B. (2018).** *Marikina Flood Hazard Models Using Historical Data of Water Level*. Philippine Journal of Science, 147(3), 373–382. [Publisher](https://philjournalsci.dost.gov.ph/marikina-flood-hazard-models-using-historical-data-of-water-level/) · [Ateneo full text](https://research.ateneo.edu/ws/portalfiles/portal/39983793/Marikina%20flood%20hazard%20models%20using%20historical%20data%20of%20water%20level.pdf).

Hourly MMDA-EFCOS Sto. Niño levels from 2002–2012 support duration distributions above gauge thresholds, with comparison against 2013–2016. Tables 2–5 include durations of 1–92 hours above 15 m and 2–56 hours above 18 m. Dagum, Burr and Fatigue Life distributions and Monte Carlo quantiles demonstrate a local probabilistic approach. Missing hourly readings required repairs/imputation.

**Contribution:** request original and recent EFCOS histories; reproduce threshold-duration distributions as river-context benchmarks. Gauge stage is not street-water depth or road clearance. A citywide street timer cannot be inferred from these distributions. Full text verified; no raw downloadable CSV located.

### B. Historical observed-event duration map

**JICA / DPWH / CTI Engineering International / Nippon Koei (2010).** *The Preparatory Study for Sector Loan on Disaster Risk Management: Needs Assessment Study on Flood Disasters Caused by Typhoons No.16 (Ondoy) and No.17 (Pepeng).* [Official full report](https://openjicareport.jica.go.jp/pdf/11999422_01.pdf).

Printed p.9 attributes depth/duration maps to NAMRIA survey data and the team’s field survey. Figure 2.2.4, p.14 / PDF page 35, maps six duration bands, spanning under a day to over a month. The summary describes core-metropolis drainage taking 1–3 days and West Manggahan residential inundation lasting 1–3 weeks during Ondoy.

**Contribution:** request underlying survey/GIS data for historical spatial intervals. The map is an exceptional 2009 event under older infrastructure conditions; digitized figure colors would be approximate and cannot establish current typical duration. Original machine-readable survey/GIS was not linked. Full text and map located.

### C. Historical drainage infrastructure effects

**JICA (2001).** *Metro Manila Flood Control Project (II)*, ex-post evaluation, September 2000 field survey. [Official report](https://www.jica.go.jp/Resource/english/our_work/evaluation/oda_loan/post/2001/pdf/e_project_55_all.pdf).

Table 2, p.4, gives DPWH-sourced maximum duration per flood: Vitas and Balut decreased from 10 hours in 1995 to 5 hours in 1998–2000; San Andres decreased from 6 to 2 hours. These are catchment/year maxima, not complete incident histories.

**Contribution:** drainage works and pumping performance can change duration. Record infrastructure era and available pump status when acquiring modern labels. A two-hour historical maximum in one catchment cannot justify a universal expiry. Full table text verified; original operational rows not located.

### D. Regional simulated duration map

**JICA / NEDA / ALMEC (2014).** *Roadmap for Transport Infrastructure Development for Metro Manila and Its Surrounding Areas*, Technical Report No.1: Environment and Hazard Risk Reduction Analysis. [Official report](https://openjicareport.jica.go.jp/pdf/12149621.pdf).

Figure 3.5.4, p.3-12 / PDF page 62, reproduces World Bank 2012 **simulated** Ondoy duration, with classes from 0–6 hours through 2–3 months.

**Contribution:** regional hydraulic duration modeling already exists. Seek original time-series/raster outputs from DPWH/World Bank rather than treating this figure as observed clearance. Scenario, resolution and infrastructure age remain material limitations. Full text verified; machine-readable duration layer not found.

### E. Recent Marikina recession modeling

**Serrano, J. S., Herrera, E. C., & Naito, K. (2024).** *Hydraulic Analysis of the Marikina River Floodplain During Typhoon Vamco using Numerical Modelling*. Proceedings of IAHS, 386, 121–126. [Full article / DOI](https://doi.org/10.5194/piahs-386-121-2024).

Coupled HEC-HMS/HEC-RAS models include rainfall, terrain, channel conditions and river/lake boundaries. Section 3.1 reports maximum simulated inundation after 16 hours of continuous rain, followed by another 19 hours for inundated area to decrease by half. This is **area recession**, not clearance of every road. A 40 m hydraulic grid comes from 1 m LiDAR. Another storm is needed for independent validation.

**Contribution:** request processed model outputs, explicitly available on request, to investigate depth trajectories and physical predictors. Raw inputs require agency acquisition. This is model evidence, not observed training labels. Full article verified.

### F. Laguna Lake / backwater duration

**Herrera, E. C., & Naito, K. (2024).** *Hydrodynamic Investigation of Laguna Lake, Philippines for Water Security and Flood Risk Management of Metro Manila*. Proceedings of IAHS, 386, 95–100. [Full article / DOI](https://doi.org/10.5194/piahs-386-95-2024).

Delft3D scenarios quantify shoreland/lake recovery under detention conditions. Table 1 includes a Pasig-associated recession of approximately 219 days, referenced to a normal lake level of 10.5 m on LLDA datum. **This is not a typical Pasig street duration.** The study incorporates rainfall, inflow, evaporation, wind and tidal/lake interactions.

**Contribution:** separate lake/backwater incidents from local rain ponding. The publisher offers Table 1 XLSX and processed model data on request; XLSX retrieval was unsuccessful in this review. Full article verified.

**Ardales Jr., G. Y., Espaldon, M. V. O., Lasco, R. D., Quimbo, M. A. T., & Zamora, O. B. (2015).** *Trends in Rainfall and the Causes of Flood Events in the Municipalities of Los Baños and Bay, Laguna, Philippines*. Journal of Nature Studies, 14(2), 40–53. [Publisher full text](https://www.journalofnaturestudies.org/files/JNS14-2/14%282%29%2040-53%20Ardales-fullpaper.pdf).

Table 2 reports 60–108 days above a 12.5 m lake threshold across five historical examples; the method references daily LLDA records. This neighboring-region comparison supports acquiring lake histories, but concerns a level threshold rather than pavement clearance. Full text verified; raw data not found.

### G. Street observations, surveys and terrain

**Abad, R. P., Fillone, A., & Schwanen, T. (2017).** *Analysis of Inter-City Travel Behavior in Metro Manila during Flooding*. TSSP proceedings, pp.159–168. [UP NCTS full text](https://ncts.upd.edu.ph/tssp/wp-content/uploads/2017/07/TSSP2017-16-Abad-Fillone-and-Schwanen.pdf).

A March 2015 pilot collected 159 validated questionnaires about recent flood location, height and duration. Table 2, p.163, reports 83.0% under an hour, 16.4% at 1–3 hours and 0.6% at 3–5 hours.

**Contribution:** structured retrospective surveys can recover duration categories where automatic observations are absent. These are recollections in a small transport sample; multiple responses can concern the same event. Do not turn percentages into fabricated independent incidents. Full text verified; underlying responses not located.

**Lagmay, A. M., et al. (2017).** *Street floods in Metro Manila and possible solutions*. Journal of Environmental Sciences, 59, 39–47. [Publisher](https://doi.org/10.1016/j.jes.2017.03.004).

The accessible publisher preview describes MMDA flood-prone streets, NOAH maps, photographs and LiDAR road/creek profiles. Low terrain, creek intersections and drainage impediments explain street flooding.

**Contribution:** investigate terrain/drainage features beyond city or barangay name. Full text was access restricted; no duration dataset was verified from the preview. NOAH return periods remain rainfall scenarios, not duration labels.

**Abon, C. C., David, C. P. C., & Pellejera, N. E. B. (2011).** *Reconstructing the Tropical Storm Ketsana flood event in Marikina River, Philippines*. Hydrology and Earth System Sciences, 15, 1283–1289. [Publisher full text](https://doi.org/10.5194/hess-15-1283-2011).

Resident interviews helped reconstruct peak timing and height when gauge information was inadequate, allowing comparison with hydrologic/hydraulic models.

**Contribution:** prompt structured interviews can supplement archival reconstruction. Peak observations alone are not drainage duration; collect explicit last-flooded and first-cleared evidence. Publisher material verified; direct PDF retrieval was intermittent.

**Mamuyac, L. K. D., Delos Reyes, J. R. D., Lumanglas, L. S. L., Rebotiaco, E. L. C., & Fillone, A. M. (2024).** *Characterizing Traffic Behavior on Flooded Roads of Metro Manila*. TSSP. [UP NCTS full text](https://ncts.upd.edu.ph/tssp/wp-content/uploads/2024/12/TSSP2024-03-Revised-Paper.pdf).

Fifteen 30-minute MMDA CCTV clips support traffic/depth analysis. The paper expressly leaves filling/draining rates outside its analysis, because longer sequences were unavailable.

**Contribution:** request contiguous footage with timestamps and section identity to derive clearance brackets. It is an acquisition route, not an existing duration dataset. Full text verified.

## 4. Public observations and realistic acquisition routes

| Source | Concrete acquisition target | What cannot be inferred |
| --- | --- | --- |
| Pasig DRRMO / barangays | Original consultation basis plus recent section-specific positive, clearance, depth/passability and storm records | The published consultation ranges do not reveal how many incidents supported each range. |
| MMDA / EFCOS | Hourly stage history, traffic flood/clear advisories, continuous CCTV, pump/gate operational histories | A flood-prone street list is not an incident history. |
| NAMRIA / DPWH / JICA | Underlying 2009 survey/GIS, contemporary terrain, drainage and infrastructure metadata | A published map image is not a precise current-road observation. |
| UP model authors / UPRI | Processed temporal outputs and calibration evidence, with reuse permission | A susceptibility polygon is not a dynamic depth trajectory. |
| PAGASA / LLDA | Dated rainfall, forecasts as issued, river/lake history, station datum and quality flags | Rain ending or a falling river does not prove street drainage. |
| LANES and permitted public advisories | Repeated supported flood/clear observations, preserving source and observation time | Article publication time or missing posts cannot establish clearance. |

**Concrete public clearance example:** PNA’s August 22, 2025 report attributes cleared-road observations to MMDA, including EDSA Shaw Tunnel northbound at 09:00 and Ortigas La Salle Gate 6 westbound at 10:45. [Official report](https://www.pna.gov.ph/articles/1257131). Pairing with earlier matched flood observations can supply labels. This article alone has no onset for those sections; “passable” must be separated from absence of water.

**Access warning:** MMDA’s [2023 successful FOI request for daily/hourly flood levels](https://www.foi.gov.ph/requests/request-for-dataset-of-dailyhourly-flood-levels-of-flood-prone-areas-in-metro-manila/) provided a PDF called *Flood Prone Areas Analysis*, not a verified hourly CSV. Its attachment could not be retrieved. A successful FOI status is insufficient evidence of temporal fields.

**Current partnership lead:** a [January 2026 official PIA announcement](https://pia.gov.ph/news/mmda-up-resilience-institute-strengthen-deal-on-metro-manila-traffic-flood-control/) describes MMDA/UPRI flooded-area data sharing. Public API/archive access, licensing and duration fields were not established.

No agency or paper author has been contacted. Requests listed here are prepared acquisition recommendations; sending them requires the user’s authorization.

## 5. Methods literature and relevance to LANES

| Primary study | Verified contribution | LANES interpretation and limit |
| --- | --- | --- |
| Kumar, A., Saharia, M., & Kirstetter, P. (2024). *Mapping a Novel Metric for Flash Flood Recovery Using Interpretable Machine Learning*. Journal of Hydrometeorology, 25(12), 1863–1875. [Publisher](https://doi.org/10.1175/JHM-D-23-0196.1), [author preprint](https://eartharxiv.org/repository/view/6758/) | Learns a US watershed recovery metric from recession and physical/climatic characteristics. Publisher indexed text and preprint abstract verified; publisher fetch was restricted. | Supports physics-informed probabilistic recession research. Watershed recovery is a different target from dry road; US accuracy does not establish NCR transfer. |
| Rättich, M., Martinis, S., & Wieland, M. (2020). *Automatic Flood Duration Estimation Based on Multi-Sensor Satellite Data*. Remote Sensing, 12(4), 643. [DLR author repository](https://elib.dlr.de/134179/), [DOI](https://doi.org/10.3390/rs12040643) | Combines repeated satellite inundation masks to estimate duration and uncertainty in Mozambique/India. Institutional abstract verified; full PDF retrieval failed. | Wet/dry observation sequences can recover historical brackets without an original duration column. Satellite gaps and urban detection limit short street episodes. |
| Tarpanelli, A., Mondini, A. C., & Camici, S. (2022). *Effectiveness of Sentinel-1 and Sentinel-2 for Flood Detection Assessment in Europe*. NHESS, 22, 2473–2489. [Full article](https://doi.org/10.5194/nhess-22-2473-2022) | Evaluates missed events caused by revisit and cloud limitations. Full article verified. | Satellite non-detection cannot establish dry conditions. Reconstruct intervals with observation uncertainty; do not promise hourly NCR clearance. |
| Magro, R. B., Pedrollo, O. C., & Rafaeli Neto, S. L. (2025). *Urban Flood Forecasting with Multi-Output Neural Networks: A Physically-Based and Data-Driven Approach*. RBRH, 30. [Full article](https://doi.org/10.1590/2318-0331.302520240089) | Brazilian HEC-HMS/HEC-RAS simulations supply depth trajectories for ANN forecasting where observed depth series are scarce. Full article verified. | A calibrated hydraulic model plus ML surrogate is a feasible research route. Simulator-derived labels need separate provenance and field validation; static NOAH polygons alone cannot supply the simulator. |
| Turnbull, B. W. (1976). *The Empirical Distribution Function with Arbitrarily Grouped, Censored and Truncated Data*. JRSS B, 38(3), 290–295. [Original publisher](https://doi.org/10.1111/j.2517-6161.1976.tb01597.x) | Foundation for interval-censored duration distributions. Publisher summary verified. | Use last-positive/first-clear bounds instead of invented exact times. Censoring assumptions and reporting bias require investigation. |
| Cox, D. R. (1972). *Regression Models and Life-Tables*. JRSS B, 34(2), 187–202. [Original publisher](https://doi.org/10.1111/j.2517-6161.1972.tb00899.x) | Foundation for covariate-dependent censored time-to-event analysis. Publisher summary verified. | Survival analysis is appropriate to investigate; standard right-censored Cox fitting does not automatically support interval labels. Check assumptions and actual fitter support. |

## 6. Ways to solve the problem

| Approach | Data requirement | Appropriate output | Main limitation |
| --- | --- | --- | --- |
| Evidence lifecycle and matched clearance updates | Qualified flood/clear reports and observation times | Automatic Unconfirmed or observed Cleared | No current update leaves physical condition uncertain. |
| Local duration ranges / empirical distributions | Qualified consultation summaries and reconstructed episodes | Broad local expectations and review priorities | Sparse/old summaries cannot provide calibrated current-road probabilities. |
| Survival / time-to-clearance models | Incident follow-up with exact/interval/censored outcomes plus available predictors | Persistence probability and estimated clearance interval | Model assumptions, reporting bias and sample support need evaluation. |
| Completed-duration quantile regression | Reliable completed durations and predictor histories | Predicted lower/median/upper duration estimates | Excluding unresolved events can bias training; not every reported clear time is exact. |
| Calibrated hydraulic forecast or ML surrogate | Suitable terrain/drainage, rainfall, boundaries and local calibration data | Simulated depth trajectory and threshold-crossing estimate | More acquisition and modeling work; scenario output needs real-event validation. |
| Repeated CCTV/satellite/community observations | Permitted timestamped wet/dry/depth observations | Clearance brackets and model updates | Coverage, revisit, visibility and evidence quality vary. |

**Preferred sequence:** implement the accepted evidence contract after pending storage/policy decisions; assemble an offline duration register; pilot empirical and survival estimates in supported Pasig areas; compare quantile methods; investigate hydraulic outputs as additional evidence. Extend to other NCR cities only after separate geographic validation. More complex ML should follow measurable benefit.

For other cities, collect local records and classify drainage/rain ponding, river overflow, tidal flooding and lake/backwater effects. Share statistical information across similar settings only through an explicitly evaluated pooled/hierarchical approach. Pasig consultation summaries cannot silently become labels for all NCR.

### How the survival study works

The LANES team can conduct this study and explain the results. The user does not need to independently master survival mathematics before progress can begin.

1. **Define the outcome.** Estimate remaining time from a supported flooded observation to supported clearance. Full physical duration requires actual onset evidence. Define road-water clearance and vehicle passability separately.
2. **Reconstruct chronologies.** For example, a road reported flooded at 08:00 and 10:00, then clear at 11:00, has clearance in `(10:00, 11:00]`, subject to incident continuity. This is an illustrative example, not a source observation.
3. **Preserve missingness.** Without clearance, retain only supported follow-up. Searching until noon cannot prove the flood persisted until noon. A single initial observation with no follow-up supplies little duration information.
4. **Keep evidence classes separate.** Observed incident bounds, retrospective survey ranges, consultation priors, river threshold episodes and simulated trajectories need distinct provenance. Never synthesize hundreds of training incidents from one summary range.
5. **Compare candidates.** Pooled empirical/Turnbull estimates first; interval-capable accelerated failure time models next. Quantile/log-duration regression applies to suitable completed outcomes. Cox/survival forests are comparators only when label format, support and assumptions fit.
6. **Evaluate future storms and new places.** Put observations from the same storm/incident in the same partition; hold out later storms and geographic areas. Check calibration and interval coverage, then replay premature retirement and stale active hours. Investigate reporting-dependent censoring rather than assuming random follow-up.
7. **Run shadow estimates.** Record forecasts without changing routing, compare them with subsequent supported updates, and then choose model/policy from measured errors. A model may abstain for unsupported conditions.

“Survival” here means an episode has not yet cleared. A survival curve describes estimated persistence over time; it is not a live observation of the road. No model-probability threshold or adaptive horizon is selected by this review; the developer's separate conditional two-hour evidence fallback is accepted.

### Tools and documentation outputs

Use existing **pandas/NumPy** for cleaning, timelines and numerical work; **scikit-learn** for completed-duration baselines and quantile comparisons. Evaluate **lifelines** for interval-aware survival candidates and **scikit-survival** for supported right-censored comparators. Select specific compatible fitters and versions in isolation. [Official lifelines guide](https://lifelines.readthedocs.io/en/latest/Survival%20analysis%20with%20lifelines.html), [official scikit-survival evaluation guide](https://scikit-survival.readthedocs.io/en/stable/user_guide/evaluating-survival-models.html).

ARIMA is a possible river/time-series component where monitored sequences exist, not a duration learner for the current location/depth CSV. Monte Carlo/random sampling propagates assumed or fitted uncertainty; it does not discover drainage from missing labels.

Required outputs are label coverage/censoring charts; local duration distributions; persistence curves with uncertainty; prediction-interval coverage; calibration plots; held-out baseline/model error comparisons; city/road error maps; and rainfall/observation/estimate incident timelines. Export figures and underlying aggregates for capstone documentation. No trained-model graphs can be claimed yet. Package additions must synchronize requirements and tech-stack records.

## 7. Search scope, access and exclusions

Research used parallel local-literature, data-source and methods investigations on October 4, 2026, followed by source reconciliation and original Pasig-plan verification. Selection prioritized NCR/Pasig duration or recession evidence and transferable methods with explicit targets. Agency studies and consultation documents are distinguished from journal/conference papers. This is a focused review, not an exhaustive systematic review.

| Requested search venue | Result and access limitation |
| --- | --- |
| Google Scholar | Scholar-oriented/indexed literature discovery led to publisher and institutional records; no complete authenticated Scholar export was performed. |
| Philippine E-Journals | Indexed searches found drainage/governance studies; checked abstracts did not expose road-clearance training rows. |
| Tuklas, UP Diliman | Catalog surfaced the Marikina duration paper and planning works. Evidence was checked against available original publications. |
| Bahandian | Current host is [repository.cpu.edu.ph](https://repository.cpu.edu.ph/); some works have access restrictions and one drainage item failed retrieval. No NCR clearance dataset verified. |
| National Library / Philippine eLibrary | [National Library](https://web.nlp.gov.ph/) catalogs led to historical theses; selected records explicitly lacked digital copies. They remain access leads. |
| ERIC | Native query retrieval failed; indexed education/disaster material did not supply relevant NCR duration labels. |
| DOAJ | Some open studies were found through indexed discovery; direct native search was unreliable. No complete directory search is claimed. |
| BASE | Homepage returned access denial/Anubis protection. A complete native search was unavailable. |

Example searches: `"Metro Manila" "flood duration"`, `"Pasig" "duration" "flood"`, `"Marikina" "recession"`, and domain-scoped searches for each requested repository. No contemporary public road onset-to-clearance CSV was verified. This is an access/search result, not proof that agencies lack records.

Excluded from duration labels: NOAH rainfall return periods; design rainfall duration; economic cleanup/rebuilding periods; DROMIC terminal-report dates; administrative LANES event endings; broad MGB susceptibility ranges; and places named Pasig outside Pasig City. Scanned KAMANAVA 2000 duration numbers surfaced in indexed official text, but lacked a successful page-image check and were not promoted into the verified numerical findings. Third-party Pasig LCCAP mirrors were discovery leads; the official DRRM plan independently established the duration column.

## 8. Research contribution and remaining gap

The literature can contribute real local duration information, mechanism-specific features, older observed-event intervals, dynamic simulation leads and methods for incomplete histories. Public clearance updates offer a practical path to new labels without LANES-owned sensors.

The remaining gap is a **recent, geographically matched and quality-reviewed incident register** sufficient to evaluate current-road estimates. First acquire/reconstruct that register; then compare methods and document results. The final model, provider integrations, adaptive bounds/map retention and storage implementation remain open. The accepted direction and revised conditional fallback are recorded in [decisions](../decisions.md#22-separate-observed-flood-status-evidence-expiry-and-predicted-clearance).

## 9. Recent data and revised plan: October 4 follow-up

### Actual 2026 observations found

Recent official Pasig HTML reports provide temporal evidence suitable for an **extraction/labeling pilot**. The pages were retrieved directly with read-only HTTP requests and their title, dates, observation clocks, locations, depths and clearance wording inspected. Some browser-tool fetches timed out; direct HTTP retrieval succeeded. These are extractable public observations, not an already reviewed training CSV.

| Candidate episode | Supported wet observation | Later clearance update | Candidate interval and limitation |
| --- | --- | --- | --- |
| Maybunga, August 10–11, 2026 | At 00:30 August 10, Blocks 1–8, Alley 8, Westbank Road Floodway were reported flooded. The next day's page preserves a 05:30 August 11 flooded snapshot at the same locations. | At 09:50 August 11, the city reports that recorded Maybunga floods subsided and no flooded areas remained reported. | Clearance after 05:30 and by 09:50: up to 4 hours 20 minutes after the last positive snapshot. This summary is matched to its reported locations; it is not a per-road instrument measurement or exact onset-to-clearance duration. |
| Dela Paz, August 29–30, 2026 | Kabutihan Street and two Katipiran locations have 22:30 August 29 and 05:00 August 30 flooded observations. | At 11:00 August 30, the city reports that recorded flooding subsided according to barangay reports. | Clearance after 05:00 and by 11:00: up to six hours after the latest positive snapshot. Summary scope needs explicit mapping and label review. |

Primary sources: [August 10, 00:30](https://pasigcity.gov.ph/news-and-releases/southwest-monsoon-habagat-flood-update-as-of-1230-am-of-august-10-2026-588), [August 11, 09:50 / preceding 05:30](https://pasigcity.gov.ph/news-and-releases/enhanced-southwest-monsoon-habagat-flood-update-as-of-950-am-of-august-11-2026-502), [August 29, 22:30](https://pasigcity.gov.ph/news-and-releases/southwest-monsoon-habagat-flood-update-as-of-1030-pm-of-august-29-2026-757), [August 30, 11:00 / preceding 05:00](https://pasigcity.gov.ph/news-and-releases/southwest-monsoon-habagat-flood-update-as-of-1100-am-of-august-30-2026-965).

Onset is unknown, so neither bracket is full physical flood duration. Nearby roads and repeated snapshots share an episode; they must not be counted as independent storms or split across training and evaluation. Broad summary clearance remains lower-resolution evidence than an explicit section observation. Review continuity, source revisions and passability separately before admitting labels.

### Contemporary acquisition leads

- [MMDA: historical flood reports 2022–2025](https://www.foi.gov.ph/agencies/mmda/historical-flood-reports-in-metro-manila-2022-to-2025/), requested June 2026: the final response says FCSMO-EFCOS emailed information on July 9, 2026. No public attachment or schema was verified. This is a strong acquisition lead, not data currently held by LANES.
- [MMDA: historical flood logs 2024–2025](https://www.foi.gov.ph/agencies/mmda/smartcommuteph-historical-flood-logs-and-flood-prone-areas-data-requst/), requested August 2026: explicitly seeks onset, location, depth and clearance times. Its visible status is Accepted; no released training file was verified. The generic page workflow also displays a success heading, which must not override the actual request status and response.
- [MMDA: hourly Marikina-basin rainfall](https://www.foi.gov.ph/agencies/mmda/data-request-hourly-rainfall-data-of-marikina-river-basin/), May 2026 request: asks for histories through 2026 and later streamflow records. The final response says requested information was emailed. Coverage, fields and completeness require obtaining the actual files.

Prioritize actual **2024–2026 observations**, with older records used for mechanism/history and separately evaluated supplemental learning. A paper's publication date is not the date of its underlying events: the 2024 Vamco paper analyzes 2020 flooding; the 2023–2028 Pasig plan's consultation table refers to 2021. Updated drainage and pumping can invalidate older local averages.

### Is the data enough?

**Enough to specify the lifecycle and begin a recent Pasig labeling pilot; insufficient to claim a validated adaptive duration model.** The research has not established a reviewed event count, independent storm diversity, recent predictor histories, city coverage or an untouched evaluation set. No minimum row count is selected. Hundreds of correlated road snapshots from two episodes would not establish multi-storm accuracy.

Next deliverable: an offline register and quality/coverage report listing source identity, supported place and clocks, first/last wet observations, clearance brackets, continuity, mechanism, storm group, source revision and review status. Add compatible rainfall/river/lake inputs available at prediction time. Count independent episodes and usable outcomes, then assess whether a pilot model can be fitted and evaluated honestly.

### ML candidates and scale

Survival analysis is a time-to-event framework that can use statistical or ML estimators. **XGBoost's survival AFT** objective supports interval and right-censored outcome ranges with a nonlinear tree ensemble. This is a concrete ML candidate for incomplete flood histories. Its ranged-label interface uses the training/DMatrix API. It is not installed or chosen for LANES. [Official documentation](https://xgboost.readthedocs.io/en/stable/tutorials/aft_survival_analysis.html).

For suitable completed durations, **scikit-learn quantile gradient boosting** can estimate conditional duration quantiles; check interval coverage and completed-case selection bias. **Random survival forests** are optional nonlinear comparators for compatible right-censored records. Their standard target format does not automatically accept interval outcomes. [Quantile example](https://scikit-learn.org/1.5/auto_examples/ensemble/plot_gradient_boosting_quantile.html), [survival forest guide](https://scikit-survival.readthedocs.io/en/stable/user_guide/random-survival-forest.html).

A shared model can combine terrain, drainage/basin, rain, depth and location/context features. A small set of mechanism-specific models may be justified by evaluation. Separate training for every barangay is unnecessary; flood conditions also differ among roads within one barangay. New geography requires validation or abstention. Computational scale is manageable as a design proposal; trustworthy outcome coverage remains the main unproven requirement.

### Updated product sequence

1. Retain the current CSV primarily for plotting/location context. Preserve the three-part update/register/estimate direction as the current plan, subject to subsequent developer feedback.
2. Use the developer-approved **two-hour observation-based fallback to Unconfirmed** where duration support is insufficient. A research mention alone is not model qualification; this can include Pasig before local validation. Fresh accepted flooding refreshes support; credible matched clearance can act earlier. Expiry supplies no clearance label.
3. Build/review the recent incident register, acquire permitted contemporary records and graph coverage before choosing the final model.
4. Compare simple empirical and interval-capable AFT baselines against nonlinear boosted survival/quantile candidates; evaluate future storms and geographic holdouts. Require model-result graphs and shadow predictions.
5. Allow adaptive horizons only for validated compatible settings. Keep the fallback for insufficient support or failed/missing estimates, and select finite retention/routing semantics separately.
6. Plan a future public-map observation action for Unconfirmed areas. Commuters can report continuing flooding or subsidence; backend evidence/trust/identity checks decide refresh, clearance or review. The interaction and its acceptance rules are not yet implemented.

## 10. Recent-study supplementation without waiting for external requests

**October 4 developer direction:** prioritize online studies and accessible data because agency/author requests may not arrive before next week's defense. Relevant evidence can contribute through measured input features, qualified background ranges, model methods or released datasets. Preserve each source's role and limits; a paper's finding does not establish an unobserved clearance time in a different incident. There is no trained LANES duration model yet to improve. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

| Newly checked source | Verified availability and contribution | Admission limits |
| --- | --- | --- |
| Cruz et al., **2026**, [Influence of typhoon and monsoon-enhanced rainfall patterns on riverine flooding in Balanga City, Philippines](https://doi.org/10.3389/frwa.2026.1775842) | Published April 2, 2026. Six modeled storms include 2024 and 2025. Supports investigating rainfall sequencing and antecedent wetness as predictors of persistence. Article and public tables were inspected. | Balanga riverine simulations, not NCR street-clearance observations. Calibration is indirect; antecedent wetness was qualitatively inferred. The generic data-availability statement does not verify a downloadable hourly/raw dataset. Do not copy results into Pasig incident labels. |
| Cao et al., **2025**, U-RNN / [UrbanFlood24 author dataset page](https://holmescao.github.io/datasets/urbanflood24), [official Figshare release](https://figshare.com/articles/dataset/28082549), [author repository](https://github.com/holmescao/U-RNN) | Simulated urban depth series at one-minute intervals for 56 rainfall scenarios, with terrain/drainage/imperviousness context. Dataset released December 30, 2024. Figshare API metadata retrieved: CC BY 4.0, `urbanflood24.zip`, **19,619,322,176 bytes** (approximately 19.6 GB), download URL `https://ndownloader.figshare.com/files/51407804`, supplied MD5 `91f394ad0388d457358a9b38645c88fe`, DOI `10.6084/m9.figshare.28082549.v1`. | Archive not downloaded or contents inspected. Shenzhen simulations can support algorithm development, not demonstrated Pasig accuracy. Check simulation endpoint, depth threshold and whether recession is observed or truncated before deriving targets. Prefer a bounded subset/lightweight author-supported path if feasible; full download and deep sequence training are not assumed deadline-compatible. |
| Google **Groundsource, 2026**, [official introduction](https://www.research.google/blog/introducing-groundsource-turning-news-reports-into-data-with-gemini/), [dataset release](https://zenodo.org/records/18647054) | Public news-derived flood archive and downloadable Parquet identified; official methodology supports deriving structured evidence from public articles. | No file/subset acquired in this check. Philippine/NCR presence, temporal granularity, date semantics and suitability for clearance-duration targets still need inspection. Extraction errors and duplicate reporting require review; do not assume event date ranges are observed road-clearance durations. |

**Use of other relevant sources:** measured rainfall/river/terrain/drainage inputs can enrich a matching incident; reported aggregate duration ranges may inform separately labelled priors; published simulation series can support a separate surrogate-model experiment. Each needs compatible geography, mechanism, units, timing and provenance. Unrelated impact or vulnerability variables remain RRL context unless they demonstrate predictive value. Known unknown clearance labels stay unknown/censored. Neither copied averages nor generated durations become observed ground truth.

**Next concrete data task:** use accessible Pasig flood/clear reports to build a bounded source-linked pilot, while inspectable public supplementary datasets are assessed in parallel with that collection. Join only defensible features, count independent storms/outcomes, and decide whether statistical or ML fitting is supported. Preserve an evaluation set of actual local observations and required graphs. Requests for MMDA/EFCOS records remain optional leads; these are government-record routes, not an NGO prerequisite. Source metadata inspection, full acquisition, admission and fitting remain separate reported milestones.

**First collection outcome:** the [public-report pilot](../evaluations/flood-duration-pilot-20261004/README.md) is now expanded to 18 official sources, 398 observations and 37 candidate location bounds across three shared clearance episodes. These remain candidate summary linkages with unknown onset; no trained model or accuracy claim follows from these counts. This changes the source status from examples merely inspected to reproducible captures for a bounded batch, while preserving the need for more independent outcomes and local evaluation. UrbanFlood24 public metadata is saved; its simulation archive is not downloaded.


## 11. Actual older-year acquisition and regional evidence snapshot

See the [expanded register](../evaluations/metro-manila-flood-duration-20261004/README.md), [captured citations](../evaluations/metro-manila-flood-duration-20261004/sources.md) and [search/access log](../evaluations/metro-manila-flood-duration-20261004/collection-search-log.md). The register now holds 753 evidence records across 16 NCR LGUs, including separate document-derived historical incidents. Pasig 2021/2022 evidence was actually acquired; 2023 remains a capture gap. The source selection is incomplete and repeated observations share storms. Neither a literature reference nor this row count supplies accurate duration labels; fitting/admission gates remain unchanged.
