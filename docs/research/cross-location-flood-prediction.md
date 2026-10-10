# Cross-location learning for flood depth and subsidence prediction

> **Last Updated:** October 08, 2026, 11:43 PM (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Research documented; offline qualification/comparison and automatic private research integration are implemented locally. Primary model selection and operational acceptance remain pending. [Results](../evaluations/cross-location-duration-20261008/README.md).

**October 10 operational continuation:** The developer authorized a separate experimental policy that consumes eligible estimates and saves expiry deadlines. Research views remain read-only; field accuracy and scientific qualification remain open. [Decision 27](../decisions.md#27-experimental-pasig-ml-deadlines-as-an-operational-expiry-policy), [local acceptance](../evaluations/pasig-ml-automatic-expiry-20261010.md).

## 1. Research question and recommendation

The implemented local comparison and its selection boundaries are now recorded in [Decision 26](../decisions.md#26-cross-location-learning-as-a-source-bound-research-comparison), dated October 9. The literature review below remains the October 8 research record; model promotion is still an evaluation gate.

Can LANES use information from locations with substantial historical flood evidence to improve predictions at a location with limited history?

**Yes.** Established approaches include hydrological regionalization, hierarchical partial pooling, transfer learning and prediction ensembles. Their usefulness depends on the quality of the source evidence, similarity between locations and validation on previously unseen locations and events. Additional predictions derived from the same observations do not constitute additional independent evidence.

**Recommended direction:** investigate a depth-aware AFT duration model with hierarchical partial pooling of location effects. Begin with a small regularized pooled-depth benchmark, then compare a minimal hierarchical extension when the independent evidence supports it. Keep future reported depth, reported subsidence and vehicle passability as distinct targets.

This is a recommendation for LANES based on the literature and local audit, not a published demonstration that this particular model improves Pasig street-level accuracy. The present three shared subsidence summaries cannot establish that improvement. Numerical convergence or a proper posterior under priors does not establish predictive reliability.

The deliverable records the research and a proposed sequence for follow-up work. No application code, runtime artifact, dataset, database schema, dependency, operational status, routing policy or deployment is changed by this document.

## 2. What connecting locations means

### 2.1 Sharing historical knowledge

Location 1 has little history. Locations 2 and 3 have more qualified observations. A model learns shared relationships between depth, available conditions and the duration outcome from all eligible locations, then applies those relationships to Location 1's own inputs. Location 1's observations can gradually support a local adjustment.

The source and target locations need not be physically connected to share statistical knowledge, but their relevant flood behaviour must be sufficiently comparable. A nearby location can be a poor donor if its drainage, elevation or flood mechanism differs.

### 2.2 Using current observations elsewhere

Current measurements at Locations 2 and 3 can also become inputs for Location 1 when their relationship is supported, such as shared drainage or upstream influence. This requires aligned observation and availability clocks, a supported spatial connection and potentially a learned time lag.

Historical sharing and real-time neighbour inputs are separate capabilities. LANES can investigate historical sharing first; it should not assume that a nearby report is a measurement of the target zone.

### 2.3 Sharing prediction outputs

Several models can produce forecasts for **Location 1 under Location 1's conditions**, and an ensemble can combine them. Directly averaging Location 2's and Location 3's actual clearance timestamps mixes different events, reference times and conditions.

If future ensembles are used, align target, reference policy, issuance time and forecast horizon. Combine predictive distributions where possible, retain model disagreement and validate the combination. A weighted average of medians is not generally the median of a mixture distribution. Never admit model-generated outcomes as observed training truth.

## 3. Current LANES model and prediction logic

This review concerns the local working checkout on `roi-branch`, including existing uncommitted work. It is not a fresh deployed-service or live-database audit.

| Component | Inspected behaviour | Implication |
| --- | --- | --- |
| [Duration kernel](../../backend/app/services/flood_duration_model.py) | Lognormal accelerated failure time model; numeric features, missing indicators and exact/left/right/interval-censored likelihood contributions | Reusable duration mathematics, but no hierarchical fitting or posterior uncertainty implementation |
| [Selected subsidence artifact](../../backend/runtime_data/flood-duration/conditional_aft.json) | Empty feature list, one intercept, fitted lognormal scale; shadow-only and deployment-ineligible lineage | No depth, rainfall, drainage or learned location effect |
| [Subsidence preview service](../../backend/app/services/flood_subsidence_prediction_service.py) | Rejects feature-bearing artifacts; passes empty prediction features; permits explicitly labelled pooled Pasig transfer | Selecting a feature model requires a deliberate loader and input-contract change |
| [Automatic zone adapter](../../backend/app/services/zone_prediction_service.py) | Resolves geometry/locality and qualifies linked episode evidence; freezes issuance to evidence availability; supports separately labelled registration/submission simulations | A useful integration point after offline model evaluation; simulations remain distinct from observed clocks |
| [Feature capture service](../../backend/app/services/flood_feature_service.py) | Freezes depth basis, source clocks, coordinates, geometry digest, locality and optional environmental context | Available inputs must be qualified before they are used for fitting or prediction |
| [Public model-evidence export](../../backend/app/services/zone_update_service.py) | Independent review provenance, explicit admission blockers and `training_admitted=False` | A collection foundation, not an automatically qualified training dataset |
| [Passability service](../../backend/app/services/flood_passability_prediction_service.py) | Separate intercept-only research AFT target | Transport recovery must remain distinct from subsidence/dry conditions |

The subsidence target is remaining time from the first recorded wet reference to **reported subsidence**, with uninterrupted-episode assumptions. The first recorded wet time is not necessarily physical flood onset. Reported subsidence does not establish measured zero depth or safe passage.

LANES already performs a basic form of cross-location transfer: one shared duration distribution can be applied to other recognized Pasig barangays with warnings. It does not yet learn how their conditions differ. With equal reference and issuance inputs, the duration pattern is identical across locations and depths.

The selected artifact has log-duration centre approximately 6.964058 and scale 0.460654. Current p10/p50/p90 outputs describe variation under these fitted parameters; they do not fully quantify parameter uncertainty or uncertainty about transfer to an unfamiliar location.

## 4. Dataset audit and the depth/outcome gap

| Dataset or experiment | Recorded count | Interpretation |
| --- | ---: | --- |
| [Working wet observations](../evaluations/pasig-duration-followup-20261005/pasig_wet_observations.csv) | 819 | Wet snapshots with differing timing, depth and geographic qualifications; not 819 completed duration episodes |
| [Conditional subsidence candidates](../evaluations/pasig-duration-model-20261007/conditional_training_candidates.csv) | 37 | Four training barangays, three shared subsidence summaries |
| Depth-feature AFT subset | 36 | One depth row excluded; same limited shared-outcome structure |
| [Depth-change pairs](../evaluations/pasig-location-feature-models-20261008/depth_trajectory_pairs.csv) | 251 | Three reporting episodes: 224 unchanged, 14 rising, 13 falling |
| [Passability artifact](../../backend/runtime_data/flood-duration/passability_aft.json) | 9 | Seven training barangays, two shared passability outcomes |

The inspected subsidence candidates are all marked production-training-unadmitted, continuity-unverified and historical-prospective-availability-unverified. Reporting episode labels do not certify independently verified storms. Group balancing reduces domination by repeated projections, but does not create independent local endpoints.

### 4.1 Why different depths on a date are insufficient

The 37 duration projections have this structure:

| Shared outcome | Projections | Localities | Starting-depth evidence |
| --- | ---: | --- | --- |
| Maybunga August 10–11, 2026 summary | 8 | Maybunga | All starting depths 38.1 cm |
| Dela Paz August 17–18, 2026 summary | 1 | Dela Paz | Starting depth 91.44 cm |
| August 29–30, 2026 collective summary | 28 | Dela Paz 5, Santolan 11, Sta. Lucia 12 | Different starting depths, including one excluded/uncertain row |

Most usable depth variation is attached to one collective summary. That summary does not reveal the separate time at which each street or extent subsided. Depth, location, event and reporting behaviour can be confounded. This explains why seeing different recorded depths does not automatically yield an identifiable depth-duration relationship.

### 4.2 Existing candidate results

The [feature comparison](../evaluations/pasig-location-feature-models-20261008/feature_comparison.json) records these whole-summary AFT comparisons. Lower interval negative log likelihood is better; it is not an error in minutes or a calibrated accuracy percentage.

| Held summary | Intercept AFT NLL | Depth-feature AFT NLL |
| --- | ---: | ---: |
| Dela Paz | 2.493 | 2.503 |
| August 30 collective summary | 3.332 | Unidentifiable |
| Maybunga | 6.503 | 13.767 |

The full depth fit has a small negative standardized coefficient, approximately -0.0301. It does not establish that deeper floods physically subside faster; the failed/worse holdouts and evidence structure do not support that interpretation.

The separate Ridge next-depth experiment uses current depth, elapsed hours and canonical barangay:

| Held reporting episode | Depth/location Ridge MAE | Unchanged-depth baseline MAE |
| --- | ---: | ---: |
| July 2025 | 22.561 cm | 4.586 cm |
| August 17–18, 2026 | 4.601 cm | 0.000 cm |
| August 29–30, 2026 | 17.960 cm | 11.227 cm |

The candidate is worse in every recorded fold. Persistence is a necessary comparator, not a claim that water physically remains unchanged. Neither feature candidate is selected.

The research audit read the datasets/scripts/artifacts and verified all seven input checksums listed in the feature comparison against current files. These results reproduce recorded evidence identities; model fitting and application tests were not rerun during this research. The later acquisition overlay records 30 additional wet claims but zero new matched subsidence-duration pairs. See the [working manifest](../evaluations/pasig-duration-followup-20261005/dataset_manifest.json), [feature evaluation notes](../evaluations/pasig-location-feature-models-20261008/README.md) and [follow-up manifest](../evaluations/pasig-clearance-followup-20261007/dataset_manifest.json).

## 5. Methods and evidence

### 5.1 Similarity-based regionalization

Regionalization transfers information from observed locations to poorly observed ones. Donor locations can be selected using relevant characteristics rather than distance alone. Chang and Rubin investigate hydrologic similarity and information transfer for ungauged groundwater-recharge estimation [S1]. Kratzert and colleagues demonstrate regional learning from meteorological series and static catchment characteristics across 531 basins [S2].

**LANES application:** compare transferable patterns using qualified depth, flood mechanism and available location attributes. Drainage/pump information could help if genuinely obtained. Existing locality names or administrative boundaries do not establish drainage similarity.

**Limit:** donor selection can cause harmful transfer if source and target behaviour differ. Watershed recharge or runoff results do not directly validate road-level subsidence prediction. Few qualified donor endpoints limit this method even if many wet snapshots exist.

### 5.2 Hierarchical partial pooling — recommended model direction

Partial pooling estimates a shared population relationship and restrained group differences. Sparse groups borrow more information from the population, while evidence-rich groups can support stronger local distinctions. Stan's examples document this statistical principle [S3]; its guide also warns about estimating hierarchy with few groups [S4]. Zhou and Hanson describe spatial survival modelling, including AFT and interval censoring [S5].

A minimal proposed duration model is:

```text
log(T_i) = alpha + beta_depth * depth_i + gamma * qualified_conditions_i
           + u_location[i] + epsilon_i
u_location ~ Normal(0, tau_location^2)
epsilon ~ Normal(0, sigma^2)
```

`T` is duration to a consistently defined reported outcome from a consistently defined wet reference. The depth coefficient is initially shared. Optional conditions enter only if available, qualified and supported. Location effects shrink toward a shared mean; broader condition-based groups could later be considered if defensible. Storm dependence must also be addressed, rather than treating every projection as independent. An event effect could be examined when enough independent events exist; an unseen event's effect must be integrated over, not estimated using its later outcome.

For a location with no outcomes, integrate uncertainty in its unobserved location effect. Setting that effect to zero and reporting a narrow interval would conceal transfer uncertainty. For a location with a few observations, shrink its local estimate while retaining uncertainty. Population averages also require sensitivity checks when the available locations are unrepresentative.

**Limit:** three shared summaries cannot reliably establish many local intercepts, group variances and different depth slopes. Priors can stabilize a fit but cannot supply missing observations. Bayesian posterior and prior-sensitivity checks, or appropriately regularized frequentist comparisons, would be required; no implementation dependency has been selected.

### 5.3 Ensembles and stacking

Stacking uses other models' outputs as predictors for a combining model [S6]. It could eventually combine distinct regional, pooled and local models evaluated for the target location.

**Limit:** weights require honest held-out evidence. Out-of-fold training predictions must respect event/source dependence and clocks. Correlated models can share the same errors. Repeated outputs from the current single pooled model add no information. Standard point-regression stacking is not directly a solution for censored duration targets without adapting its objective and evaluation.

### 5.4 Transfer learning

A source model can be trained on a large relevant dataset and adapted to limited target data. Oruche and colleagues investigate LSTM parameter transfer between a richer US streamflow dataset and a smaller Kenyan dataset [S7].

**Limit:** discharge, simulated inundation, measured depth and reported subsidence are different targets. Source-target differences and unsuitable adaptation can degrade predictions. LANES currently lacks a qualified large source dataset for its exact local duration target, so adopting a pretrained river model alone would not solve the problem.

### 5.5 Spatial models and graph neural networks

Spatial statistical models can represent residual spatial relationships; graph models can represent connections and evolving states. SWE–GNN uses hydraulic variables, terrain and shallow-water-inspired propagation, trained using numerical flood simulations [S8].

**Limit:** geometric neighbourhood is not necessarily hydraulic connectivity. Barriers, elevation differences, drains and pumps matter. Irregular public reports and a handful of outcomes are not equivalent to the simulated hydraulic time series in that study. Detailed terrain, hydraulic connectivity and qualified real/simulated calibration data are needed before this becomes a practical LANES option.

## 6. Keep targets and evidence semantics separate

| Task | Inputs and outcome | Required evidence |
| --- | --- | --- |
| Depth-aware subsidence duration | Qualified depth/conditions at the prediction reference; later reported subsidence | Matched extent/episode, supported clocks and duration bounds |
| Future reported depth | Recent depth observations and aligned conditions; depth at a specified future horizon | Repeated matched numeric or appropriately modelled range observations |
| Vehicle passability recovery | Nonpassability reference and later vehicle-specific recovery | Explicit transport outcome for the matching scope |

A predicted depth of zero is not an observed dry outcome. A spot-level no-floodwater report does not establish whole-zone clearance. A registration or submission time is not physical onset. Reports lacking timestamps or qualified scope must retain those limitations rather than receiving fabricated labels.

Deeper water may be associated with longer recession under comparable conditions, but depth alone is not a sufficient physical model. The current evidence does not justify imposing a universal depth-duration rule or converting an observed short decline into a guaranteed time to zero.

## 7. Feasible integration path

### Stage A — evidence qualification and a reproducible dataset

1. Export existing versioned source snapshots and independent reviews. Preserve raw records and source identities.
2. Form location/extent/episode timelines with actual observation and availability clocks. Retain qualitative depth and numeric uncertainty instead of treating gauge proxies as precise measurements.
3. Match endpoints to the same scope and episode. Retain interval bounds; qualified ongoing observations can contribute right-censoring. A missing later report alone does not establish continued flooding or a clearance endpoint.
4. Identify duplicate sources, shared outcomes, reporting episodes and storm groups. Shared summaries need explicit dependence treatment; weighting alone is not proof of independence.
5. Include eligible episodes without a reported final outcome where observation support permits, to investigate the current outcome-selected cohort bias. Examine reporting-related censoring rather than assuming it is uninformative.
6. Record predictor availability at issuance. Later weather, later reports and hindsight-based donor selection must not leak into historical predictions.

### Stage B — simple offline benchmarks and partial pooling

1. Preserve the selected runtime artifacts and original exports.
2. Compare intercept-only lognormal and exponential duration baselines on the same eligible data.
3. Investigate a regularized shared-depth AFT benchmark with a small feature set. Document regularization and check sensitivity; finite fitting does not qualify release.
4. Compare a minimal location hierarchy if the evidence supports it. Avoid a separate depth slope per street initially.
5. Evaluate depth trajectories separately against persistence at defined horizons, including rising/falling/static cases.
6. Save dataset hashes, group assignments, scalers, fitting configuration, uncertainty method, metrics, failed fits and source limitations under `docs/evaluations/`.

### Stage C — demonstrate transfer and uncertainty

Evaluate previously unseen locations, locations with artificially limited training history, unseen events and later prospective episodes. Remove all held-location evidence from training for a zero-history experiment; shared summaries spanning train/test locations must not leak endpoints across the split. Evaluate a distinct same-event real-time scenario only using neighbour data available at issuance.

Use grouped and chronological splitting rather than random snapshot splits [S9]. Fit preprocessing, donor selection and tuning inside the training folds. With the present few groups, holdouts remain sensitivity analysis, not independent final acceptance.

For duration, examine censored likelihood scores, calibrated horizon probabilities and predictive uncertainty coverage using suitable censoring-aware methods. Minute error is appropriate only where endpoint precision supports it. For depth, examine horizon-specific MAE and coverage, separating numeric measurements from proxy/range reports. Report per-location and per-event outcomes and abstention coverage, not only one aggregate score.

No universal row-count threshold is established here. Promotion requires an improvement that survives honest held-out evaluation, acceptable calibration, supported geography/conditions and stability to plausible assumptions. Unsupported locations or depths should fall back to a labelled research baseline or abstain.

### Stage D — automatic backend integration after selection

1. Version the model artifact and feature/reference contract. The current loader deliberately rejects feature-bearing artifacts; replacing a JSON file alone is insufficient.
2. Pass qualified frozen inputs from the automatic zone adapter into the selected model. A new current depth observation requires a defined reference/update policy; do not insert it retrospectively as first-observation depth.
3. Preserve stable issuance anchors across display refresh. Recompute only under deliberate qualified-new-evidence rules, including continuity and re-flooding checks.
4. Update calculation details to explain depth and location contributions and distinguish predictive spread from transfer/parameter uncertainty.
5. Return model/source version, evidence support, transfer basis, missing inputs, uncertainty and abstention reasons through backend-owned contracts. Keep existing authentication and Reports/Zones permission checks.
6. Verify both desktop and mobile presentations if UI work follows. Maintain the existing automatic flow and do not require extra prediction input forms merely to exercise the model.
7. Treat forecast-to-Unconfirmed/public retention as the separate existing lifecycle work. A forecast must not manufacture Cleared or training truth. Model outputs from other places cannot establish the target zone's observed flood status or affected geometry.

Existing [feature/locality work](../plans/pasig-location-and-feature-duration.md), [follow-up evidence plan](../plans/flood-followup-evidence-plan.md) and [current task plan](../task_plan.md) are the starting points for a subsequent implementation blueprint. This research does not mark any of those implementation or release gates complete.

## 8. Environmental and implementation limits

- The current feature provider supplies modelled Copernicus GLO-90 elevation and coarse ECMWF IFS 0.25-degree rainfall context through Open-Meteo. Neither is a street drainage measurement. Source/grid coordinates, capture time and data basis remain explicit.
- Hydraulic drainage and pump capacity are currently unknown. An OSM drain line or administrative boundary cannot establish capacity or flow connectivity.
- Historical reanalysis and archived forecasts have different availability semantics. A hindsight reconstruction is not proof that a predictor was available when a forecast would have been issued. Future rainfall may be used only as an appropriately issued forecast, not later observed rainfall.
- Missing depth or unavailable environment remains missing. Qualification and fallback policy must be explicit; automatic zero substitution is unsuitable.
- SciPy, NumPy and scikit-learn are already declared. Hierarchical inference libraries, if selected later, must be recorded in dependencies and deployment checks. No new package is adopted by the research.
- Existing JSON snapshots and exports allow an initial offline investigation without relational schema changes. Any later SQLAlchemy/Alembic modification requires the developer's confirmation and migration verification under repository rules.
- This direction improves use of available evidence. It does not remove the need for independent, matching local outcomes or guarantee safe passage.

## 9. Follow-up deliverables

- [x] Literature research and local model/dataset review documented.
- [x] Create the implementation blueprint for qualified cross-location experiments and acceptance criteria.
- [x] Build reproducible historical qualification separating rejected/conditional records; production admission remains zero.
- [x] Compare pooled-depth and minimal partial-pooling candidates; incomplete/mixed holdouts do not qualify replacement.
- [x] Integrate an automatic private research comparison with source clocks, uncertainty and responsive proxy/abstention/error states.
- [ ] Complete location/event/temporal transfer evaluation and uncertainty checks.
- [ ] Integrate a selected supported candidate with automatic prediction and calculation details.
- [ ] Complete responsive verification, monitored prospective validation and matching release acceptance.

The developer intends to proceed with this research direction. Model choice remains an evaluation result, and a candidate's research availability must be distinguished from an accepted operational prediction model.

## 10. Sources and scope of support

Sources were consulted during the October 8, 2026 research. Descriptions below are paraphrases. Hydrology papers support related methods; statistical documentation supports the modelling mechanics. The proposed LANES design is an inference from those sources and the repository audit.

1. **[S1] Chang, C.-F., and Rubin, Y. (2019).** [Regionalization with hierarchical hydrologic similarity and ex situ data in the context of groundwater recharge estimation at ungauged watersheds](https://hess.copernicus.org/articles/23/2417/2019/). *Hydrology and Earth System Sciences*, 23, article starting at p. 2417. DOI: 10.5194/hess-23-2417-2019. Supports similarity-conditioned information transfer and its uncertainty. Its outcome is groundwater recharge, not Pasig road subsidence.
2. **[S2] Kratzert, F., et al. (2019).** [Towards learning universal, regional, and local hydrological behaviors via machine learning applied to large-sample datasets](https://hess.copernicus.org/articles/23/5089/2019/index.html). *Hydrology and Earth System Sciences*, 23, 5089–5110. DOI: 10.5194/hess-23-5089-2019. Demonstrates shared learning across 531 basins using weather series and catchment attributes; it uses large-sample rainfall-runoff evidence.
3. **[S3] Carpenter, B., Gabry, J., and Goodrich, B. (2017).** [Hierarchical Partial Pooling for Repeated Binary Trials](https://mc-stan.org/learn-stan/case-studies/pool-binary-trials-rstanarm.html). Official Stan case study. Explains complete/no/partial pooling and held-out predictive checks; the example is binary trials, not a flood model.
4. **[S4] Stan User's Guide.** [Multilevel regression and poststratification](https://mc-stan.org/docs/2_24/stan-users-guide/multilevel-regression-and-poststratification.html) and [Truncated or Censored Data](https://mc-stan.org/docs/stan-users-guide/truncation-censoring.html). Official documentation; the multilevel link is a versioned older guide. Supports hierarchical stabilization, few-group limitations and likelihood treatment of censoring.
5. **[S5] Zhou, H., and Hanson, T.** [A unified framework for fitting Bayesian semiparametric models to arbitrarily censored survival data, including spatially-referenced data](https://arxiv.org/abs/1701.06976). Author-posted research manuscript, revised July 2017. Supports spatial AFT modelling with interval and other censoring types; it does not benchmark floods.
6. **[S6] Scikit-learn documentation.** [StackingRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.StackingRegressor.html). Supports learning from multiple model outputs and warns about overfitting when combining predictions made on their training data. Current online documentation is conceptual guidance; LANES' declared package version must be checked for any later implementation.
7. **[S7] Oruche, R., Egede, L., Baker, T., and O'Donncha, F. (2021).** [Transfer learning to improve streamflow forecasts in data sparse regions](https://arxiv.org/abs/2112.03088). Author-posted research manuscript. Investigates LSTM parameter transfer and static descriptors for streamflow across a richer US and smaller Kenyan dataset; this is not a reported-clearance model.
8. **[S8] Bentivoglio, R., et al. (2023).** [Rapid spatio-temporal flood modelling via hydraulics-based graph neural networks](https://hess.copernicus.org/articles/27/4227/2023/). *Hydrology and Earth System Sciences*, 27, article starting at p. 4227. DOI: 10.5194/hess-27-4227-2023. Uses numerical dike-breach simulations and hydraulic/terrain inputs; it supports a possible future graph direction, not expected LANES accuracy from current reports.
9. **[S9] Scikit-learn documentation.** [Cross-validation: evaluating estimator performance](https://scikit-learn.org/stable/modules/cross_validation.html). Supports group separation for dependent samples and chronological evaluation for time series. LANES still needs domain-specific storm/shared-source/availability grouping.

Related provider references: [Open-Meteo elevation API](https://open-meteo.com/en/docs/elevation-api), [historical weather API](https://open-meteo.com/en/docs/historical-weather-api) and [historical forecast API](https://open-meteo.com/en/docs/historical-forecast-api). Provider semantics and current LANES input limitations are already recorded in the [feature pipeline evaluation](../evaluations/pasig-location-feature-models-20261008/README.md).
