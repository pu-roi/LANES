# Pasig subsidence model implementation

> **Last Updated:** October 08, 2026, 02:10 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Subsidence and separate passability research fits, explicit pooled transfer and automatic official registration simulation verified locally. Forecast-to-Unconfirmed/public retention, accuracy qualification and release remain open.

## October 8 continuation

**Placement correction:** The developer subsequently removed Flood condition follow-ups and ML review assistant from Moderation Center, including per-report ML controls. The two staff queue components are unmounted and replacement UI placement is unfinished; native API acceptance and owner follow-ups remain. Existing Active Zone Overview now uses automatic geometry/evidence selection and read-only prediction; its manual test/save inputs have been withdrawn. Historical staff queue verification below does not establish acceptance of its location.

Local database/authenticated API and desktop/mobile follow-up acceptance is now complete, and the experimental case-linked staff review assistant is implemented. See [current acceptance](../evaluations/case-linked-ml-review-assistant-20261008.md). The historical checkpoint below preserves what was known on October 7. Physical PWA/deployment, the monitored pilot and qualified prospective model evaluation remain open. No automatic clearance, schema/dependency change or training admission is introduced. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## What is implemented

The [October 7 experiment](../evaluations/pasig-duration-model-20261007/README.md) adds a fitted interval-aware model, a reproducible training script, source-derived experimental rows, summary-group sensitivity and prediction quantiles/probabilities. Original October 5 data and its admission decisions remain unchanged. No automatic self-training or production expiry decision is introduced.

| Layer | Implementation |
| --- | --- |
| Statistical kernel | `backend/app/services/flood_duration_model.py`: exact, left-, interval- and right-censored lognormal AFT likelihood; numerical identifiability checks; numeric feature standardization/missing indicators; strict JSON artifacts; conditional prediction. |
| Experimental training | `backend/scripts/train_pasig_duration.py`: immutable input/capture checks, earliest recorded wet references, conditional bounds, group-balanced fitting, sensitivity and figures. |
| Model artifact | `backend/runtime_data/flood-duration/conditional_aft.json`: fitted intercept-only research model, input lineage, numerical diagnostics and explicit limitations. |
| Preview service | `backend/app/services/flood_subsidence_prediction_service.py`: bounded artifact loading, scope/assumption checks, finite predictions; no database writes. |
| API | Staff report-read permission required for `GET /api/v1/admin/news/duration-model` and `POST /api/v1/admin/news/duration-preview`. No commuter/public prediction endpoint. |

The generic preview accepts staff-supplied hypothetical inputs. It does not certify report evidence, match a live incident, resolve a road section or establish historical publication availability. It is a research inspection interface and is not connected to settings, zone expiry, public-map rendering or routing.

## Two distinct targets and datasets

The original [reported-subsidence target](pasig-reported-subsidence-target.md) describes remaining time after its supported wet reference. Its existing 37 last-wet intervals have zero lower bounds and only three shared outcomes. They are retained as descriptive evidence; using those bounds alone does not identify a positive duration distribution.

The new experimental target is:

`remaining_time_from_first_recorded_wet_to_reported_subsidence_continuity_assumed_v1`

It estimates elapsed time from the first **recorded** wet observation in a selected reporting timeline. This is not physical flood onset. The cohort is selected from locations with acquired subsidence summaries. Reference selection is deterministic within that cohort; it does not establish a prospective population or an unbiased sample.

The positive lower bounds assume that flooding continued between snapshots with **no intervening recovery and recurrence**. Collective subsidence scope remains conditional. These assumptions have not been verified. Keep `experimental_fit_included=true` separate from `production_training_admitted=false`. Never overwrite original proxy admission fields to make fitting appear justified.

Current experimental intervals, in minutes:

| Shared summary | Projections | Conditional interval |
| --- | ---: | --- |
| Maybunga August 11 | 8 | `(1740,2000]` |
| Dela Paz August 18 | 1 | `(930,1050)` |
| August 30 list; first wet at 20:30 | 22 | `(510,870]` |
| August 30 list; first wet at 22:30 | 4 | `(390,750]` |
| August 30 list; no earlier wet record | 2 | `(0,360]` |

Historical availability and issuance fields remain unknown. The two upper-only rows first occur inside the subsidence article and cannot become pre-outcome predictors. The GMA earlier reference has publication/modification metadata, but the acquired version has no archival proof of historical availability. Any later approximation needs a separate declared analysis.

## Model choice and interpretation

The first implementation is a **lognormal accelerated-failure-time baseline with an intercept and scale**. It fits the probability of each observed interval, without converting uncertain bounds to exact midpoints. The formula is `log(T) = intercept + sigma * Z`, where `Z` is standard normal. AFT can later use qualified features, but this experiment supplies **no depth, location, rainfall or historical-recurrence coefficients**. [Lognormal AFT documentation](https://lifelines.readthedocs.io/en/latest/fitters/regression/LogNormalAFTFitter.html).

The objective is a **group-balanced composite interval likelihood**. Projections sharing a subsidence summary receive weights that sum to one for that summary. This limits repeated-summary influence but does not make dependent locations independent or prove that three summaries represent three independent storms.

The kernel rejects all-upper-only and all-right-censored evidence sets, deficient feature designs, failed numerical convergence, boundary-scale fits and nearly singular likelihood curvature. These checks detect some unsupported fits; passing them is not a data-sufficiency or accuracy guarantee. All five optimizer starts converged; the best finite fit was retained. Numerical log-scale bounds are optimizer safeguards; boundary solutions are rejected rather than converted into estimates.

Outputs include p10/p50/p90 **model-distribution quantiles** and model-derived horizon probabilities. They are not validated confidence intervals, calibrated probabilities, safe-road times or confirmed clearance. The kernel uses stable log-CDF/log-survival computations. [SciPy log-CDF documentation](https://docs.scipy.org/doc/scipy-1.14.1/reference/generated/scipy.special.log_ndtr.html).

Leaving out each shared summary measures sensitivity under the same assumptions. It is not untouched prospective accuracy validation. No exact physical clearance time exists for calculating an honest minute-level MAE on these intervals. Do not score against an invented midpoint, use random row splits or claim 37 independent validation events.

Nonlinear XGBoost AFT remains a later comparator if diverse, qualified independent outcomes and useful predictors support it. Its native training interface supports ranged labels. Adding trees now cannot establish missing outcome information. [Official XGBoost AFT guidance](https://xgboost.readthedocs.io/en/stable/tutorials/aft_survival_analysis.html).

## Research preview contract

Requests require timezone-aware `reference_at` and `prediction_as_of_at`, `reference_policy=first_recorded_wet_in_episode`, Pasig geography, a represented barangay and explicit acknowledgement of research limitations. Positive elapsed age also requires `assume_continuous_wet=true`; that is an assumption supplied by staff, not a verified observation.

The preview is limited to the current represented Maybunga, Dela Paz, Santolan and Sta. Lucia samples. This is a study-scope check, not geographic validation. Missing artifacts, unsupported geography, unacknowledged assumptions, future issuance clocks and reference age beyond the experimental bound support cause abstention. Invalid/unreadable artifacts return a visible HTTP 503. Authentication and role checks run before endpoint work; responses are not cached.

For an explicitly assumed still-wet elapsed age `a`, the research calculation conditions on `T > a` and returns remaining duration quantiles. It does not subtract age from an unconditional median or silently clamp a past prediction to zero. Changing that conditioning requires current evidence and target review before any operational use.

`LANES_FLOOD_DURATION_MODEL_PATH` optionally selects a server-owned JSON artifact; `LANES_FLOOD_DURATION_MODEL_SHA256` optionally pins its checksum. The default uses the packaged research artifact. The loader limits size and validates schema, finite parameters and research lineage; it never unpickles model files or downloads a model.

## October 8 coverage correction

The [canonical coverage audit](../evaluations/pasig-barangay-coverage-20261008/README.md) separates overall collection from duration training: 29 annual barangays plus 20 main wet barangays cover all 30 in union; main and October 7 overlay wet claims cover 21. Ugong has eight annual rows and ten named wet snapshots across the registers, plus one transport-passability projection, but no retained matched subsidence-duration row. Four barangays are the existing duration-cohort scope, not all collected geography. A pooled citywide baseline is possible in design; qualify outcomes/censoring/dependencies and evaluate transfer before expanding its experimental prediction scope. Preserve the historical model/input bytes and do not use another year's road observations as a current zone reference.

## October 8 model path update

Current status now separates four subsidence training-cohort identities from 30 explicitly allowed pooled research-transfer identities. Zone prediction is automatic; an unchanged recent official registration may supply a separately labeled simulation proxy when observed time is missing. Evidence-based outputs and simulations hold their original issuance anchor across refresh, preventing a continually postponed countdown. The original subsidence parameters/data remain preserved; no missing observed outcomes are imputed by the model.

A separate [passability-duration AFT experiment](../evaluations/pasig-passability-model-20261008/README.md) uses nine conditional projections/seven barangays/two shared summaries, including Ugong. Staff API exposes passability-model and passability-preview alongside the original subsidence endpoints; vehicle facts remain independent of exact depth and dry status. One held-out group is unidentifiable, so broader independent evaluation/prospective qualification remain open. [Full acceptance](../evaluations/case-linked-ml-review-assistant-20261008.md#october-8-pooled-research-transfer-transport-target-and-automatic-registration-simulation).

The requested operational continuation is forecast-triggered Unconfirmed with retained public visibility/updates, not model-triggered Cleared. Model-to-expiry/public retained-zone delivery is not implemented by the research endpoints and stays open in task_plan.

## Complete prediction locality and feature-candidate result

The [two-limit continuation](../evaluations/pasig-location-feature-models-20261008/README.md) completes source-consistent prediction locality for all 30 barangays, separate from unchanged news OSM geometry. Current feature context and future immutable input snapshots are implemented without user fields or backfill. Depth AFT and depth/locality trajectory candidates are evaluated under full-summary/episode holdouts and are not selected; the active research models remain pooled. Independent matched outcomes/feature availability are still required for useful street-specific effects. Do not confuse implemented feature extraction with demonstrated feature-model accuracy.

## Remaining gates for automatic prediction

**October 7 follow-up acquisition:** A separate [independently reviewed overlay](../evaluations/pasig-clearance-followup-20261007/README.md) adds five captures, one explicit October 10, 2025 road-subsidence outcome without a prior wet clock, and two shared vehicle-passability outcomes. It adds zero subsidence-duration training pairs. Keep these transport observations and unknown clocks out of the current model. A [structured owner/staff follow-up workflow](flood-followup-evidence-plan.md) is now implemented locally using existing append-only storage, with original availability/observation/submission/review provenance and JSON export. Runtime/browser acceptance and deployment remain pending; staff acceptance is not automatic training admission.

1. Collect/qualify observation references and explicit follow-ups with actual source availability/issuance clocks, outcome-independent sampling and verified same-episode correspondence. Preserve missing outcomes and separately qualified right-censoring; silence is not a survival observation.
2. Establish independent storm/dependency groups and enough diversity for fitting and held-out evaluation. No fixed record count is an accuracy guarantee.
3. Evaluate feature baselines using only pre-issuance depth, age, supported depth changes, geography and source metadata. DRRMO annual rows remain optional matched context, never clearance labels. Manual-report submission/approval clocks and operational event end times cannot stand in for physical flood observation/clearance.
4. Evaluate interval-compatible calibration, uncertainty, source/reporting bias, location transfer and operational errors on independent outcomes. Compare the simple baseline with feature-based AFT before selecting a more complex model.
5. The local automatic zone adapter now selects qualified immutable citizen/current linked news evidence and resolves geometry. Run prospective shadow evaluation and adopt explicit adaptive-expiry/abstention policy before operational expiry. Reaching a forecast time does not establish observed Cleared status.

The accepted evidence lifecycle remains operationally separate: fresh qualified evidence supports Active; matched clearance supports Cleared; stale evidence becomes Unconfirmed. This work adds no SQLAlchemy models, migrations, live settings changes, public estimates or deployed automatic forecast. The original implementation slice recorded the training experiment, manual service preview and source/numerical/text review without automated/API/auth/browser checks. The subsequent [validation continuation](../evaluations/pasig-subsidence-validation-20261007/README.md) passes 62 duration numerical/API checks plus 27 existing regressions, reproduces the original fit and compares summary-held-out lognormal and exponential baselines. Exponential achieves lower mean interval NLL (2.801 versus 4.123); neither is operationally qualified. Browser/deployment and prospective case-bound acceptance remain pending.
