# Pasig flood recession: depth, missing estimates and suitable models

> **Investigated:** October 11, 2026, approximately 1:01–1:05 PM, Asia/Manila.
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe).
> **Scope:** Read-only connected database and production API investigation, current source/artifact inspection, numerical sensitivity calculations and internet research. Recommendations below are not implemented or deployed by this investigation.

## Finding

The expiry workers are connected, but coverage and scientific prediction quality remain incomplete. Of 22 active Pasig zones in the inspected records, 15 have saved ML deadlines (seven pooled and eight cross-location); seven have no deadline. The missing records have distinct source, review and cache causes. Borrowing other locations' histories addresses missing local outcomes; it cannot supply a missing observation clock or resolve conflicting incident evidence.

The user's depth concern is supported by the implementation. The pooled fallback ignores depth entirely. The cross-location model uses depth, but its learned effect is almost flat, and uncertainty can make shallow-depth upper deadlines longer than deeper-depth deadlines. These are reproducible properties, not evidence that the actual floods necessarily cleared earlier. The inspected records do not establish their true recession times.

See the [database and numerical audit](../evaluations/pasig-subsidence-availability-audit-20261011.md) for individual zones, provenance, formulas, limitations and proposed fixes.

## Why estimates are unavailable

| Zones | Verified cause | Suitable response |
| --- | --- | --- |
| #36 | Current source qualifies for the pooled registration simulation, but an earlier null policy is reused because the source signature still matches. Its saved evaluation clock predates the registration audit by about 1.25 seconds. | Repair transient negative-cache handling and clock-sensitive qualification. Reconstruct the original forecast; never start a new timer from refresh. |
| #47 | Report #26 has an unreviewed **subsided** follow-up, audit #360. | Review that claim and its location/episode. Accept real clearance through the existing workflow if supported; do not manufacture a new wet forecast. |
| #49–#50 | Reports #29/#30 say Rosario, while their zone polygons resolve to Manggahan. #49 also has subsided follow-ups. | Reconcile the source locality and affected geometry through a recorded correction. Do not silently relabel historical evidence. |
| #54–#56 | Legacy reports #6/#2/#3 have approval audits but no original `CITIZEN_OBSERVATION` audit or qualified observation clock. #56 was also edited. | Request/review a current, same-location observation. A new approval or geometry edit is not a flood onset. |

All seven saved fallbacks have `fixed_deadline=null`. Consequently, ML abstention also leaves these records without any automatic evidence expiry. This is an operational lifecycle gap requiring an explicit fallback policy, independent of whether a scientific recession estimate exists. Such a policy must mark evidence **Unconfirmed**, not confirm that the road is dry.

The UI has separate saved operational forecasts, pooled research simulations and depth-comparison output. The research API can return `state=unavailable` while also returning a usable, explicitly labeled registration/submission simulation. The UI suppresses its generic unavailable label when that simulation exists. A missing environmental context value is also different from a missing model prediction. A future unified summary should identify the chosen estimate, its source and the precise blocker without showing apparently contradictory primary forecasts.

## What the current model actually learns

`conditional_aft.json` has `feature_names=[]` and one coefficient. Its lineage explicitly says `intercept_only_no_depth_location_rainfall_effects_learned`. At zero elapsed time, its median is **17.63 hours** and p90 is **31.82 hours**, for every eligible depth/location.

`cross_location_aft.json` learns a standardized depth term and fixed-prior location effects. Its depth coefficient is **0.015936**, depth mean **54.340 cm**, and depth scale **29.981 cm**. For an unseen location, changing depth from gutter proxy **20.32 cm** to knee proxy **48.26 cm** increases the median only **1.50%**, from **16.70 to 16.95 hours**. The corresponding p90 falls from **38.68 to 36.70 hours**, because coefficient uncertainty varies with depth. This tail reversal follows the implemented distribution; it is not a learned drainage mechanism.

The Green/low severity flag is not a separately learned duration input in either model. Several canonical severity levels are already derived from depth; adding both without a deliberate model design could double-count the same information. The UI's gutter level is a canonical 8-inch proxy, not a measured ankle-depth observation; ankle is not currently a selectable canonical gauge.

The depth model's fitted support is **5–91.44 cm**. Canonical waist **93.98 cm**, chest **114.30 cm** and neck **140 cm** exceed it and can fall back to the depth-independent pooled model. Multi-barangay polygons also fall back because one locality/depth cannot describe the whole footprint under the current comparison contract. Seven of the 15 saved active forecasts used the pooled model for these reasons.

The pooled fit has 37 projections and the cross-location fit 36 depth-qualified projections. Both share only **three reported-subsidence summaries**. They are not 36 or 37 independent observed clearance events. Existing group weighting correctly limits each summary's contribution, but cannot create additional evidence. The selected cohort contains long historical intervals and assumes continuity; it does not identify a short-duration, shallow street-flood population well. No prospective calibration is established.

Operational expiry chooses p90, while the displayed central estimate is p50. A 16–18 hour median may therefore produce a 32–39 hour expiry deadline. The 48-hour ceiling is an operational policy bound, not a fitted maximum or verified reliability level.

## What physical and published research supports

Flood recession depends on the balance of inflow and outflow, with storage and drainage changing over time. EPA SWMM models rainfall-runoff, storage, drainage, pumps, surface ponding and backwater/reverse flow. Therefore, depth is useful but does not imply a universal hours-per-depth formula. Under otherwise similar conditions, less stored water can clear sooner; continuing inflow or constrained drainage can keep shallow water present. This interpretation follows the mechanisms documented by [EPA SWMM](https://www.epa.gov/water-research/storm-water-management-model-swmm) and its [hydraulics reference manual](https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P100S9AS.TXT).

A published urban study predicts water-depth time series from rainfall inputs using LSTM and transfer learning, with hydrodynamic simulation supplying training examples. It demonstrates a trajectory approach and transfer feasibility, not a pretrained Pasig expiry estimator. Its inputs and validation are substantially richer than three reported outcomes. [Zhou et al., HESS, 2023](https://hess.copernicus.org/articles/27/1791/2023/).

Global sharing also has empirical support: the Nature study on ungauged watersheds trains a shared probabilistic streamflow model. Its target is river discharge/extreme riverine flooding, not time until a particular urban road becomes dry. It supports the general idea of sharing information, but its accuracy cannot be transferred to LANES without a new local target and validation. [Nearing et al., Nature, 2024](https://www.nature.com/articles/s41586-024-07145-1).

## Approaches assessed for LANES

| Approach | Fit for LANES now | Data and limitations |
| --- | --- | --- |
| Hierarchical, interval-aware survival/AFT model | **Recommended next scientific candidate.** Share depth/context effects across locations and shrink poorly observed local effects toward a shared distribution. | Needs credible wet-to-clearance bounds and clustered event identities. The current three summaries cannot establish strong depth effects or local accuracy. |
| Depth- and context-stratified empirical survival baseline | Useful transparent comparator, with pooling when strata are sparse. | Too few independent outcomes currently to estimate stable curves per gauge. It still needs reviewed clearance observations. |
| Gradient-boosted survival/AFT | Later nonlinear comparator once sufficient independent episodes exist. | Handles interval/right/left censoring, but complexity is unjustified on three summaries. New package/release changes would need normal dependency verification. |
| Local depth-trajectory recession model | Promising when repeated, timed measurements exist for the same affected section. | Requires observed falling/rising depth and rainfall/context. A single depth snapshot cannot identify the recession rate. |
| SWMM or coupled 1D/2D simulation, then an ML surrogate | Longer-term option for selected instrumented areas. | Requires drainage network, topography, boundary conditions, forcing and calibration. Existing NOAH susceptibility and coarse environmental context do not supply these. |
| Pretrained basin LSTM/foundation model | Potential external hydrologic context; unsuitable as a direct expiry replacement. | Different spatial scale and target. Needs forcing histories and adaptation; no validated Pasig street-clearance checkpoint was established in this search. |
| Fixed depth/severity timers | Can be an explicitly named evidence-retention/review policy. | They are not a learned recession model and should not be presented as calibrated predictions or used as clearance labels. |

The existing SciPy AFT kernel can support the recommended investigation without an immediate framework replacement. A parsimonious candidate could model `log(T)=intercept+f(depth)+rainfall/context terms+location effect+noise`. Any proposed nondecreasing depth effect applies to a central prediction with other conditions held fixed, and is a declared structural assumption to test, not evidence learned from three outcomes. Location transfer should be justified by hydraulic similarity or validated shared effects, rather than geographic distance alone.

[XGBoost's AFT documentation](https://xgboost.readthedocs.io/en/stable/tutorials/aft_survival_analysis.html) confirms support for interval-censored outcomes and provides a later implementation option. AFT is a time-to-event modeling family; its suitability here does not depend on the medical examples used in that documentation.

## GitHub, Hugging Face and open forum findings

The [NeuralHydrology repository](https://github.com/neuralhydrology/neuralhydrology) is a maintained hydrologic training framework, not a street-clearance dataset or ready-made Pasig model. Google's [pretrained-model README](https://github.com/google-research/flood-forecasting/blob/main/pretrained-models/Pretrained-Models-README.md) describes basin-model weights and explicitly warns that the released full-period training prevents valid temporal holdout evaluation on that same history. Any adoption needs strict geography/time leakage controls.

The inspected Hugging Face [Global-Flood-LSTM model card](https://huggingface.co/OneScience-Group/Global-Flood-LSTM) describes a reproduction with synthetic-data workflow checks. It explicitly does not provide a confirmed original checkpoint link and does not claim those workflow results reproduce the paper's performance. It supplies no validated Pasig street-recession model. A descriptive model card is insufficient evidence for deployment.

The [OpenSWMM discussion on flooding statistics and graphs](https://www.openswmm.org/Topic/4410/flooding-discrepancies-between-graphs-and-attribute-table) highlights ponding, output sampling and numerical effects when interpreting flood duration. These are practitioner diagnostics, not controlled validation. The [NeuralHydrology maintainer discussion](https://github.com/neuralhydrology/neuralhydrology/discussions/210) distinguishes historical inputs from forecast forcing and describes streamflow outputs. It reinforces that a prediction target and input availability must be explicit. No forum statement was used as proof of a universal depth-to-duration relation.

## Proposed integration sequence

1. **Availability and lifecycle:** Repair the #36 negative-cache defect with a race regression; expose precise timing/locality/review reasons; reconcile #49–#50 and review existing subsided follow-ups. Preserve source evidence and original issuance times. Define what happens to active evidence when no ML estimate and no fallback deadline exist.
2. **One understandable forecast contract:** Display the operationally selected method, central estimate, uncertainty interval and expiry deadline together. Clearly name pooled estimates as depth-independent. Keep any secondary research comparison labeled separately. A successful calculation is not proof of current flooding.
3. **Collect defensible outcomes:** Use existing source/review audit storage and event timelines where adequate. Record actual observation time, depth/gauge basis, affected section, last verified wet and first verified cleared evidence, reviewer and availability time. Retain incomplete episodes as censored records. Staff approval, worker expiry and test simulations are not dry labels. Freeze features available at issuance; an environmental request today cannot populate a historical training feature.
4. **Fit and compare:** Start with a pooled baseline and regularized hierarchical AFT candidate with depth and a small justified feature set. Train/evaluate separately by episode/summary, storm where verified, location and time. Add a conditional depth-shape candidate; report the assumption and uncertainty. Avoid raw random row splits across shared summaries.
5. **Validate before promotion:** Measure availability/reason counts, censored likelihood, calibration/interval coverage, median error on credible bounds, shallow/deep performance and false early-expiry behavior. Compare with the current baseline on the same supported cases and report abstentions. Predefine acceptable errors with the developer; there is no defensible universal minimum event count or 100% accuracy promise.
6. **Release proven changes:** Test API/worker agreement and desktop/mobile UI; keep expiry-to-Unconfirmed separate from clearance. Refit/version only after evidence supports it. A model failure must yield an explicit fallback/review state; refreshes must not restart clocks or resurrect inactive zones.

The immediate recommendation is to fix availability and evidence handling first, while developing a **depth-aware hierarchical survival model with genuine reviewed outcomes**. Replacing the current coefficient with an arbitrary shallow-flood duration would hide the data problem rather than demonstrate better prediction.

## Research limits

**Implementation follow-up:** The read-only investigation described below preceded the authorized repair. [Expiry v3 acceptance](../evaluations/pasig-subsidence-v3-acceptance-20261011.md) records negative-cache retry, geometry-derived locality, distinct activation-based retention and the saved-forecast UI. Matching local/shared API and workers are deployed; new frontend is local only. The [offline depth-shape experiment](../evaluations/pasig-depth-shape-candidate-20261011/README.md) leaves the shallow/deep relationship almost unchanged and was not promoted. The developer confirmed the manual reports were application tests; real reviewed wet/clearance evidence remains required under the [collection guide](../guides/pasig-recession-observation-collection.md). These repairs do not demonstrate predictive accuracy.

The live inspection was observational; no deadline, moderation decision, schema, runtime model, cloud configuration or flood record was changed. No new model was trained or downloaded. Numerical sweeps demonstrate the deployed artifacts' behavior, not predictive accuracy. The reviewed external models use different targets/locations and have not been benchmarked on LANES. Ground truth and source-quality limitations remain the main constraints.
