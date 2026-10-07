# Pasig subsidence model implementation

> **Last Updated:** October 07, 2026, 09:34 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Conditional experimental AFT baseline fitted; authenticated research preview implemented locally. Operational prediction remains unqualified.

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

## Remaining gates for automatic prediction

**October 7 follow-up acquisition:** A separate [independently reviewed overlay](../evaluations/pasig-clearance-followup-20261007/README.md) adds five captures, one explicit October 10, 2025 road-subsidence outcome without a prior wet clock, and two shared vehicle-passability outcomes. It adds zero subsidence-duration training pairs. Keep these transport observations and unknown clocks out of the current model. A [structured owner/staff follow-up workflow](flood-followup-evidence-plan.md) is now implemented locally using existing append-only storage, with original availability/observation/submission/review provenance and JSON export. Runtime/browser acceptance and deployment remain pending; staff acceptance is not automatic training admission.

1. Collect/qualify observation references and explicit follow-ups with actual source availability/issuance clocks, outcome-independent sampling and verified same-episode correspondence. Preserve missing outcomes and separately qualified right-censoring; silence is not a survival observation.
2. Establish independent storm/dependency groups and enough diversity for fitting and held-out evaluation. No fixed record count is an accuracy guarantee.
3. Evaluate feature baselines using only pre-issuance depth, age, supported depth changes, geography and source metadata. DRRMO annual rows remain optional matched context, never clearance labels. Manual-report submission/approval clocks and operational event end times cannot stand in for physical flood observation/clearance.
4. Evaluate interval-compatible calibration, uncertainty, source/reporting bias, location transfer and operational errors on independent outcomes. Compare the simple baseline with feature-based AFT before selecting a more complex model.
5. Build a case-bound server adapter using qualified immutable evidence, run prospective shadow evaluation and adopt explicit adaptive-expiry/abstention policy before enabling automatic estimates. Reaching a forecast time does not establish observed Cleared status.

The accepted evidence lifecycle remains operationally separate: fresh qualified evidence supports Active; matched clearance supports Cleared; stale evidence becomes Unconfirmed. This work adds no SQLAlchemy models, migrations, live settings changes, public estimates or deployed automatic forecast. The original implementation slice recorded the training experiment, manual service preview and source/numerical/text review without automated/API/auth/browser checks. The subsequent [validation continuation](../evaluations/pasig-subsidence-validation-20261007/README.md) passes 62 duration numerical/API checks plus 27 existing regressions, reproduces the original fit and compares summary-held-out lognormal and exponential baselines. Exponential achieves lower mean interval NLL (2.801 versus 4.123); neither is operationally qualified. Browser/deployment and prospective case-bound acceptance remain pending.
