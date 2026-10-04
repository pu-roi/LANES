# Automatic flood expiry and duration estimation research

> **Last Updated:** October 04, 2026, 5:00 PM (Asia/Manila)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Research and local data audit documented. Unconfirmed, survival investigation and a two-hour fallback for insufficient duration support accepted. Final adaptive model, retention/routing policy, provider access and implementation remain open.

## 1. Recommendation and meaning

Adopt a finite evidence lifecycle with **Active, Unconfirmed and Cleared** as distinct public meanings. Investigate a separate duration estimator that supplies location-specific prediction intervals and helps prioritize refresh/review. Keep estimated subsidence distinct from observed clearance. The developer revised the policy to accept a **two-hour observation-based fallback to Unconfirmed where duration support is insufficient**. It is not a measured flood duration or an implemented news-publication default.

Automatic expiry can retire stale active evidence without claiming the water disappeared. Automatic confirmed clearance requires a newer credible observation tied to the same affected section and incident. An ML estimate can support an explicitly labelled likelihood or estimated window; it cannot create a confirmed clearance observation. Removing an indefinite hard routing exclusion also does not establish road safety.

The developer accepted **time-to-clearance / survival analysis** for investigation. Quantile regression is a useful comparator when reliable completed durations exist. Neither can currently be trained for LANES from the supplied Pasig CSV because clearance labels are absent. Begin with evidence lifecycle and data collection, then compare models offline before selecting one. No package, schema or deployment change is selected.

**RRL follow-up:** the separate official Pasig DRRM Plan 2023–2028 contains a Duration column in Table 19, based on community consultations. Local river-duration studies, historical survey maps and hydraulic recession models provide additional evidence and acquisition routes. See the [Metro Manila flood-duration literature review](metro-manila-flood-duration-rrl.md) for verified findings, provenance, access limits and the team’s study workflow. This does not change the CSV audit below or establish current-road clearance.

## 2. Local Pasig data audit

Read the actual files on October 4, rather than assuming a duration column exists:

| File | Finding |
| --- | --- |
| `data/flooded_areas_pasig_clean.csv` | 726 records, 15 columns; annual source year, record number, raw/canonical barangay, PSGC, locality review fields, street/landmark and estimated water-depth parsing. No duration, onset, observation or clearance timestamp. |
| `backend/runtime_data/flooded_areas_pasig_clean.csv` | SHA-256 matches the root cleaned CSV: `E3FD9C5A1FC966EA017DE89F061EB8E80A199A026C93F58FCAB5D96379623E13`. |
| `data/Flooded_Areas_Pasig_City_2020_2025_EDITED_ver2.csv` | 745 physical CSV records including annual headings and headers; maximum five columns. Headers are No., Barangay, Street, Landmark, Water Level (Estimated). No duration/time field was dropped during cleaning. |
| `data/Flooded_Areas_Pasig_City_2020_2025_EDITED.xlsx` | `Flooded Areas`: 745 rows × 5 columns. Six annual header blocks have the same five fields. `PDF Source Text`: 19 rows × 2 columns. Entire-workbook search found no duration/onset/clearance labels. |

Cleaned record counts by source year: 2020: 47; 2021: 86; 2022: 142; 2023: 122; 2024: 103; 2025: 226. These are **source rows**, not identified independent incidents. Repeated locations across years cannot supply incident duration, true recurrence frequency or storm identity.

The developer retains this dataset primarily for automatic plotting/location context. It is not required for duration estimation and supplies no duration targets. Optional matched historical location/depth features may be evaluated for measured benefit. Request a separate incident log from Pasig DRRMO containing dated observations and clearance/reopening evidence. That request is future work; no agency was contacted. [Recent-data follow-up](metro-manila-flood-duration-rrl.md#9-recent-data-and-revised-plan-october-4-follow-up) now includes actual August 2026 Pasig candidate chronologies.

LANES already has a different duration concept: `FloodEvent.verified_at`, `ended_at` and history `official_duration_minutes`. Source inspection shows this measures verification until the final operational zone ended. `deactivate_zone_and_end_event_if_final` can end an event when zones cease to be live. Therefore these values need reason/provenance auditing before use as physical clearance labels. Training on timer-driven operational endings would teach the model the old application policy. No live database completeness or label-quality audit was performed.

## 3. UP NOAH and UP DREAM / LiPAD

### Static hazard maps

UP DREAM describes inundation scenarios for 5-, 10-, 25-, 50- and 100-year rainfall return periods, using Marikina–Pasig as a prototype basin. A return period describes a rainfall scenario's recurrence, not how many hours water stays on a street. The available scenario maps are susceptibility context. [UP DREAM flood hazard maps](https://dream.upd.edu.ph/products/flood-hazard-maps/).

The LANES Metro Manila archive inspection already found only `Var` hazard classification in its shapefiles, with 5-, 25- and 100-year scenarios. Those local assets contain neither incident time series nor per-road duration labels. See [existing file-level evidence](../plans/lipad-noah-flood-placement.md#file-level-verification-september-28-2026). Lack of mapped overlap is not evidence of a dry road.

Possible duration-model inputs are scenario-specific overlap, terrain/elevation, slope and basin context. Whether they improve duration estimation must be measured against held-out labelled incidents. Do not convert hazard class to an invented number of hours.

### Dynamic forecasts and other products

UP's College of Science documents an **Impact-Based Flood Forecasting System** combining rainfall forecasts with hazard information; NOAH Studio is therefore worth exploring beyond static maps. Its existence does not establish that LANES can obtain timestamped road-level clearance data or a supported API. [UP announcement](https://science.upd.edu.ph/up-scientists-develop-advanced-impact-based-flood-forecasting-system/), [UP public-service description](https://publicservice.up.edu.ph/5-apps-tools-developed-in-up-everyone-should-know-about-and-use-this-rainy-season/).

NOAH Studio returned a JavaScript application shell to the research reader. This research did not verify a public machine-readable contract, historical forecast archive, update SLA, licensing for automated ingestion, or duration output. A future capability check must establish those details with documentation or UP before integration. [NOAH Studio](https://noah.up.edu.ph/noah-studio).

UP's April 14, 2025 announcement describes 24-hour neighborhood forecasts based on accumulated rainfall forecasts and 100-year hazard maps, with barangay-level population exposure. These are useful forecast features, not a stated drainage-time output. The documented crowdsourcing integration is also a lead for future clearance-label acquisition, subject to access and provenance checks.

LiPAD distributes Phil-LiDAR/DREAM products, including hazard maps and elevation products subject to the product's access process. Its current page says hazard maps remain available without registration, while other data requests use forms during portal maintenance. The UP DREAM Pampanga report documents hydrologic discharge computation and FLO-2D hazard/depth modeling. Time-varying hydrographs or simulation depth sequences could support a physics-based duration study **if supplied**; this research did not establish a public road-duration training dataset or downloadable temporal outputs for Metro Manila. [LiPAD](https://lipad.dream.upd.edu.ph/), [UP DREAM modeling report](https://dream.upd.edu.ph/assets/Publications/UP-DREAM-River-Reports/FMC/DREAM-Flood-Forecasting-and-Flood-Hazard-Mapping-for-Pampanga-River-Basin.pdf).

Conclusion: current NOAH layers can support spatial features throughout covered Metro Manila locations. They cannot replace missing clearance labels. Simulation-derived durations, if obtained, must be labelled simulated and validated separately against field observations.

## 4. Google: verified API and datasets

### Flood Forecasting API

Google documents a Flood Forecasting API offered at no charge, with API data under CC BY 4.0. Access still requires waitlist approval, a Google Cloud project, API enablement and a key. Existing Google credentials alone do not establish access. Cloud storage, processing and other services have their own costs. No access request or authenticated call was made. [API access documentation](https://developers.google.com/flood-forecasting).

The official coverage list includes the Philippines. This establishes country coverage, not a gauge, usable inundation footprint or urban forecast for every Metro Manila street. Verify actual Pasig/Marikina/Tullahan and other city coverage after access. [Official coverage](https://support.google.com/flood-hub/answer/16508958).

The REST service documents gauge search, gauge forecasts, flood status, serialized polygons, significant events and **flash-flood search**. A flood-status geographic search currently selects by gauge location, not necessarily by intersection with an affected road; a basin/gauge outside a city can still matter. Capture forecast issue and valid times, units, quality flags, covered basin and provenance before joining predictions to incidents. [REST reference](https://developers.google.com/flood-forecasting/rest), [RPC semantics](https://developers.google.com/flood-forecasting/rpc/google.research.floodforecasting.v1).

Google's current research page describes up to seven-day riverine forecasts and up to 24-hour urban flash-flood forecasts, updated daily. River discharge recession can be contextual evidence of decreasing river hazard. Its translation into a local road's drainage time remains a separate modelling problem. [Google research overview](https://sites.research.google/gr/floodforecasting/).

**Do not overlook the newer urban product.** Google documents a separate flash-flood model with approximately 20 km × 20 km cells and 24-hour occurrence predictions. Its coverage is limited by available flood history; inspect the Flash Flood coverage layer for the actual NCR footprint. Such coarse occurrence forecasts are neither road-depth observations nor a road-drainage countdown. A negative forecast or missing event cannot confirm street clearance. [Flash-flood model and limitations](https://support.google.com/flood-hub/answer/16811681), [flashFloods.search method](https://developers.google.com/flood-forecasting/rest/v1/flashFloods/search).

### Historical datasets

| Dataset | Potential use | Duration limitation |
| --- | --- | --- |
| Google Runoff Reanalysis & Reforecast (GRRR) | Global river-discharge estimates, 1980–2023; candidate river-event and recession context. | River discharge requires spatial alignment and is not measured street clearance. |
| Inundation History | Historical wetness frequency, 1999–2020, described at 128 m pixels. | Wetness frequency does not establish a current flood or hourly clearance. |
| Groundsource | Open global news-derived flood-event dataset, roughly 2.6 million records; potential historical-event/source discovery and methodology reference. | News-derived occurrence and timing are imperfect labels; verified NCR coverage and street-level clearance fields remain unassessed. |

GRRR and Inundation History are documented in [Google's resources](https://sites.research.google/gr/floodforecasting/resources/). Groundsource was announced on March 12, 2026; Google's extraction workflow distinguishes observed floods from forecasts and anchors temporal references to source context. This closely relates to LANES's news pipeline, but does not remove the need to verify each clearance label. [Groundsource methodology](https://research.google/blog/introducing-groundsource-turning-news-reports-into-data-with-gemini/).

The official dataset record offers `groundsource_2026.parquet` at about 667 MB. The landing metadata does not expose a field-level clearance contract or populated licence detail in the reader. Before downloading/training, inspect the paper, schema, reuse terms, Philippine subset, duplicates, temporal resolution and source traceability. The dataset itself was not downloaded. [Author-published dataset](https://zenodo.org/records/18647054).

## 5. Data options for other Metro Manila cities

| Source | What to use | What must be checked |
| --- | --- | --- |
| City DRRM offices and MMDA incident/reopening records | Section-specific active updates, pump/drainage operations, depth/access, clearance brackets. Highest-priority label acquisition. | Availability, timestamp meaning, incident identity, permission and reporting delay; no common public city-duration API was verified. |
| PAGASA Pasig–Marikina–Tullahan forecasting system | Existing public-network rainfall/water-level context and flood bulletins; LANES does not need to install its own gauges to use permitted external observations. | Public monitoring is documented; historical export/API access, station-to-catchment mapping and acceptable reuse still need verification. River-stage decline alone does not establish local street drainage. |
| Open-Meteo weather / forecast archives | Rainfall history, forecast accumulation and weather covariates using an API family already referenced in LANES requirements. | Historical forecasts available at decision time for fair backtesting; reanalysis is a different product. Check terms, local accuracy and usage limits. |
| NASA GPM IMERG | Satellite rainfall features: half-hourly 0.1° fields. | Early product latency is around four hours; it is coarse and delayed for short street floods. Research Final data must not be treated as information available live. |
| GloFAS / Open-Meteo Flood API | Catchment-scale modelled discharge and ensemble context. | Open-Meteo documents roughly 5 km, daily river discharge and warns nearest-river selection can be wrong. This cannot establish sub-hour street clearance. |
| Copernicus Global Flood Monitoring | Satellite flood-extent observations for retrospective spatial checks. | Revisit/processing gaps and urban detection limitations make hourly road clearance uncertain. Missing detection is not a dry observation. |

Primary sources: [PAGASA system description](https://pasig-marikina-tullahanffws.pagasa.dost.gov.ph/about/aboutus.do), [PAGASA monitoring principles](https://bagong.pagasa.dost.gov.ph/learning-tools/floods), [Open-Meteo historical forecasts](https://open-meteo.com/en/docs/historical-forecast-api), [NASA IMERG](https://gpm.nasa.gov/data/imerg), [IMERG resolution documentation](https://gpm.nasa.gov/resources/documents/imerg-v07-technical-documentation), [Open-Meteo Flood API](https://open-meteo.com/en/docs/flood-api), [GloFAS FAQ](https://confluence.ecmwf.int/spaces/CEMS/pages/315563119/6%2BFAQ%2Bin%2BGloFAS), [Copernicus GFM](https://emergency.copernicus.eu/news/gfm-now-includes-data-from-sentinel-1c/).

Recommended acquisition order: dated LGU/MMDA road incident and reopening records; permitted PAGASA series; weather as-of archives; existing NOAH features; Google coverage/access trial; satellite/global records for additional context. Broader weather coverage does not provide broader clearance labels. A Pasig-trained model must abstain outside its validated geography until separate city/storm holdouts support transfer.

## 6. Model comparison

| Approach | Suitability for LANES | Recommendation |
| --- | --- | --- |
| Evidence freshness rules plus supported clearance updates | Works before duration labels exist. Finite policy windows are administrative choices, not physical forecasts. | Implement lifecycle once its policy/contracts are settled; compare later duration-assisted policies against this baseline. |
| Historical median/quantile or pooled survival curve | Transparent baseline once real incident histories exist. Sparse roads need pooling and visible sample counts. | First statistical comparator; never manufacture location precision from one or two examples. |
| Linear / regularized log-duration regression | Simple comparator for reliably completed durations; ordinary regression mishandles unresolved durations and may give invalid raw-time predictions. | Benchmark only on an appropriately defined target; no default selection. |
| Quantile gradient boosting | Estimates conditional median and upper/lower duration quantiles with nonlinear features. Standard fitting does not handle censoring automatically. | Strong comparator for reliable completed-duration labels; explicitly test selection bias and interval calibration. |
| Survival models: Kaplan–Meier baseline, Weibull accelerated failure time, regularized Cox, random survival forest | Represents time to documented clearance and unresolved histories. Cox requires checking its proportional-hazards assumption; nonlinear forests need more data. | Preferred research family when clearance follow-up is incomplete. Match right/interval censoring to model support. |
| Discrete-time clearance hazard / landmark models | Can update using rainfall and latest observations, with an interval-aware likelihood. | Consider if time-varying covariates and clearance brackets dominate. Avoid relabelling interval outcomes as exact. |
| ARIMA / SARIMAX | Models a timestamped sequence, such as a river-stage series. Annual location/depth rows are not such a sequence. | Optional hydrologic-feature forecasting benchmark if an appropriate series exists, not the first road-duration model. |
| Random sampling / Monte Carlo | Sampling estimates uncertainty or simulates from an existing model; it does not learn clearance by itself. | Use storm-level bootstrap for uncertainty; do not randomly choose expiry as a prediction. |
| Hydrologic / hydraulic simulations or deep neural models | Potentially capture physical recession, but need terrain, drainage, boundary conditions, calibration and much larger temporal data. | Defer until those inputs and a measured advantage justify the work. |

Supporting method documentation: [survival analysis and censoring](https://scikit-survival.readthedocs.io/en/stable/user_guide/00-introduction.html), [lifelines censoring support](https://lifelines.readthedocs.io/en/latest/index.html), [interval-censored fitting](https://lifelines.readthedocs.io/en/stable/fitters/univariate/KaplanMeierFitter.html), [scikit-learn 1.5 quantile intervals](https://scikit-learn.org/1.5/auto_examples/ensemble/plot_gradient_boosting_quantile.html), [ARIMA/SARIMAX interface](https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html).

### Label contract is more important than algorithm choice

Define the target before fitting: physical drainage time, time until a documented clearance report, and time until a vehicle becomes passable are different outcomes. Prefer section-specific time to supported clearance, preserving observation brackets and reporting delay. Water receded and road safe/passable are also distinct facts.

For example, a road is observed flooded at 8 AM, still flooded at 10 AM, and first observed clear at 11 AM. Clearance lies in `(10 AM, 11 AM]`; it is not automatically exactly 11 AM. If monitoring stops after the positive 10 AM observation, duration is right-censored at that observation. Silence until noon does not prove flooding persisted until noon. An incident with only its first observation offers little follow-up information.

Store supported onset separately from first report. If onset is unknown, model remaining time from an observation/landmark and label the target accordingly. Do not pretend publication or fetch time is onset. Typical news coverage misses mild incidents and successful drainage, and reporting frequency varies by city; this creates informative missingness that ordinary survival assumptions must be audited.

For a static survival model, `S(t | x)` estimates persistence beyond time `t`; conditional persistence after an observed flooded age `a` is `S(a+h | x) / S(a | x)`, within the supported horizon. Time-varying weather requires a validated landmark/dynamic formulation rather than blindly using this ratio. Prediction quantiles beyond available follow-up must remain unavailable rather than extrapolated as precise times.

## 7. Tools and evaluation

Already declared in `backend/requirements.txt`: **scikit-learn==1.5.0**, **NumPy**, **pandas** and **openmeteo-requests**. These are useful existing tools, not evidence that a duration estimator exists. pandas handles table preparation, NumPy handles arrays, and scikit-learn supplies preprocessing/regression/comparison tools.

Potential additions after model selection: lifelines for supported survival analyses, or a compatible scikit-survival release for survival forests and evaluation; Matplotlib for reproducible exported graphs, optionally Plotly for interactive staff exploration. No packages were installed or requirements changed. Current scikit-survival documentation requires a much newer scikit-learn than LANES's 1.5.0 pin; investigate compatible releases in an isolated research environment before changing the application stack. [Installation requirements](https://scikit-survival.readthedocs.io/en/stable/install.html).

Split by storm/incident group and time, with a final later-storm holdout and separate city/road holdouts. All sections and syndicated versions of one incident must stay in the same split. Fit preprocessing only on training data. Backtest using only information available at prediction time, including forecast issue times and product latency. Report sensitivity to interval bounds, reporting delays and missingness.

Measure duration MAE/median absolute error on properly observed completed targets; quantile loss and empirical interval coverage for regression; censor-aware Brier score, calibration and discrimination for supported survival targets. C-index alone cannot show that probabilities or deadlines are reliable. IPCW metrics rely on censoring assumptions and a valid follow-up horizon; interval-censored outcomes need appropriate evaluation rather than applying right-censoring metrics blindly. [Survival evaluation](https://scikit-survival.readthedocs.io/en/stable/user_guide/evaluating-survival-models.html).

Replay the policy too: premature removal while fresh evidence still confirms flooding, stale active hours after supported clearance, Unconfirmed hours, unnecessary detour cost, city-level errors and abstention coverage. Set acceptance criteria before examining the final test set. No arbitrary accuracy percentage, clearance-probability threshold, sample minimum or adaptive duration is adopted by this research. The conditional two-hour evidence fallback is a subsequent developer policy decision.

**Required model visualizations:** data/label coverage by city and storm; duration distributions with censored/interval counts; observed/predicted plots and error distributions; persistence/clearance curves with uncertainty; reliability plots; predicted-interval coverage and width; baseline/model comparisons; geographically separated error maps; feature effects; incident timelines with rainfall, observations, forecasts and actual policy transitions. Publish real held-out metrics with split IDs, dataset/model checksums, seed, units, sample counts and limitations. Synthetic demonstrations must be labelled synthetic and cannot count as measured model results.

## 8. Implementation direction and unresolved gates

Use a backend-owned maintenance job to expire evidence and a separate optional prediction service. New observations can refresh qualified evidence; model recalculation, re-fetching an old story and weather forecasts alone cannot refresh a claimed active flood. Forecasts may change estimates and review priority while observational status becomes Unconfirmed.

A future adaptive evidence deadline can use a calibrated location/context-specific horizon from the latest supported observation, with finite policy bounds and a pinned model/input snapshot. Compare this against simple windows using premature removal and stale-active time. This is a proposed application of duration estimates to expiry, not an adopted equation or automatic clearance rule. It cannot be calibrated from the current annual Pasig records.

Bound active-evidence and Unconfirmed-map retention independently. Older Unconfirmed records should leave the default current map under an explicit retention policy and remain accessible as history. No ongoing unconfirmed road should retain an indefinite hard closure solely because its historical hazard is high. Evaluate an uncertainty warning/route-cost policy before selecting routing behaviour; route availability must not be labelled verified safe.

Pending work: assemble/review recent labels; verify provider/API and city coverage; define model target/censoring; implement the accepted conditional two-hour fallback after storage/API gates; settle adaptive bounds and map-retention/routing policies; benchmark and graph; choose a model only if it improves the measured baseline; run in shadow mode; settle exact storage/API contracts and schema approval; verify desktop/mobile and server/routing consistency before release. See the [implementation study plan](../plans/flood-evidence-lifecycle-and-duration-plan.md). Literature and recent-data discovery are documented; corpus-quality audit, training and live validation remain future work.
