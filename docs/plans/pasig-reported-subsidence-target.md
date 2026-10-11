# Pasig reported-subsidence prediction target

> **Last Updated:** October 05, 2026, 12:50 AM (Asia/Manila)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Offline target and conditional proxy-label policy defined. Three shared reported-subsidence outcomes support 37 dependent location projections. Physical-section outcomes remain unknown; training and runtime prediction remain pending.

## Scope and intended output

Metro Manila-wide news collection and automatic plotting remain the product scope. Pasig City remains the primary thesis evaluation area and initial duration-prediction study. Finish and evaluate system features before updating the thesis. Chapter 3 technical placeholders are not evidence of implementation or model performance; only the supplied user evaluation/survey is treated as real research evaluation.

The initial research target is:

> From a supported wet observation at a Pasig location, estimate the time until the same reporting episode is explicitly reported to have subsided within a matched source scope.

**Target version:** `remaining_time_from_supported_wet_reference_to_scope_matched_reported_subsidence_v1`.

This is a supervised time-to-event prediction problem when qualified outcomes and available predictors support fitting. Its endpoint is **source-reported subsidence**. The sources do not establish zero water on a measured road section, vehicle-specific passability, exact physical flood onset, or uninterrupted flooding across all snapshots. A future physical-clearance target needs its own evidence and version.

For a supported wet reference time `t_ref`, the historical response variable is `T = reported_subsidence_time - t_ref`. Store evidence-supported bounds for `T`, rather than inventing a single clock or substituting an interval midpoint. An optional total-duration target requires independently supported onset; the current three outcomes have no onset.

## Current evidence and purpose-specific admission

The [October 5 qualification](../evaluations/pasig-duration-qualification-20261005/README.md) reviewed 467 original wet observations, three clearance summaries and 12 historical rows. The subsequent [additional-source register](../evaluations/pasig-duration-followup-20261005/additional-reports/sources.md) adds 352 wet observations from eight official 2025 reports, with no new clearance summaries. Together these represent **819 wet observations plus three clearance summaries plus 12 historical rows = 834 evidence records**. The 2023 direct-report gap remains. Additional snapshots enrich reporting histories; they do not add completed duration outcomes by themselves.

Independent source qualification of all 352 additional observations is complete: captured evidence, supported clocks and 16 HTML/text artifact hashes were audited with no discrepancies. The merged 819-observation register is delivered. Physical section identity, continuity between snapshots and independent storm identity remain unresolved. Neither the combined count nor the new parser's unflagged rows establish model eligibility. Replayed original observations are alternate derived versions and must not be counted again as new evidence.

This policy admits the existing three reviewed summaries for a conditional **reported-subsidence proxy** and their 37 linked location projections for that same purpose. It does not change the October 5 v1 qualification files or retroactively make their physical-section verdicts certain.

| Reporting outcome | Wet reference | Reported subsidence upper bound | Conditional interval, minutes | Location projections |
| --- | --- | --- | --- | ---: |
| Maybunga, August 11, 2026 | 05:30 | By 09:50 | `(0, 260]` | 8 |
| Dela Paz, August 18, 2026 | 12:00 | Before 14:00 | `(0, 120)` | 1 |
| Recorded floods, August 30, 2026 | 05:00 | By 11:00 | `(0, 360]` | 28 |

All clocks above use Asia/Manila. The Dela Paz response article's 23:00 clock is not the subsidence time. Preserve the strict upper bound at 14:00. Each lower bound is zero **exclusive**; no exact elapsed duration is asserted.

The 37 projections share three summary IDs. They are not 37 independent measured subsidence clocks. The three reporting outcomes are also not yet three verified independent meteorological storms. Unknown earlier continuity does not invalidate a conditional bracket from the final supported wet snapshot, but collective scope and reporting uncertainty remain explicit assumptions.

The delivered [proxy_label_register.csv](../evaluations/pasig-duration-followup-20261005/proxy_label_register.csv) implements these policy fields:

| Field | Value or rule |
| --- | --- |
| `proxy_label_status` | `admitted_collective_scope_conditional` |
| `outcome_kind` | `collective_reported_subsidence` |
| `physical_section_label_status` | `not_established` |
| `physical_dry_status` | `not_established` |
| `passability_status` | `not_established` |
| `reference_selection_policy` | `retrospective_last_supported_wet_descriptive_only` |
| `availability_status` | `pre_outcome_availability_not_established` |
| `scope_condition` | Summary must apply to the retained reported location; physical section identity is unverified |
| `training_admitted` | `false` |
| `training_exclusion_reason` | `only_three_shared_outcomes;retrospective_reference;pre_outcome_feature_availability_unknown;section_identity_unverified` |

Proxy-label admission means usable evidence under this declared target. Training admission, fitted-model performance and runtime release are separate gates. None is granted merely by choosing a target name.

## Scope-matching admission rules

A proxy outcome requires a traceable timed affirmative wet claim, an explicit later subsidence statement, supported episode correspondence, consistent chronology and no unresolved contradictory evidence invalidating that correspondence. Preserve source versions and uncertainty instead of correcting a locality by majority vote.

| Scope linkage | Admission rule |
| --- | --- |
| `direct_location` | The subsidence statement identifies the same qualified reported location. |
| `explicit_collective_list` | An affirmative subsidence statement expressly covers the associated list of recorded flooding; retained list entries establish conditional location projections. |
| `explicit_barangay_collective` | The statement names subsided reported flooding in the barangay containing the supported candidate wet location within the same reporting episode. |
| `unresolved_scope` | Broad or vague text lacks supported episode/list/locality correspondence; keep the outcome unadmitted. |

Maybunga and August 30 have same-capture retained wet lists accompanying affirmative collective subsidence. Dela Paz explicitly names reported flooding in that barangay and follows the noon Katipiran C Yap Compound claim. Their reviewed source references and limitations are in [clearance_episode_review.csv](../evaluations/pasig-duration-qualification-20261005/clearance_episode_review.csv).

“No reports,” omission from an updated list, administrative expiry and search silence do not establish subsidence alone. A supported explicit subsidence statement may be accompanied by “no remaining recorded roads,” but absence by itself is not an outcome.

Keep future direct-location outcomes distinguishable from collective proxies. Compare results with and without collective labels when enough outcomes exist; do not hide different evidence strengths in one generic event flag.

## Reference selection and real-time availability

The current 37 brackets use the **last wet observation selected retrospectively** before a known summary. This is appropriate for describing those historical brackets. A training or replay builder must not choose the final wet snapshot using knowledge of future subsidence and then claim performance for arbitrary runtime reports.

For prospective training/evaluation, predefine a reference-selection policy without examining outcomes, such as the first eligible available wet snapshot or fixed prediction landmarks while qualified wet evidence exists. Repeated references from the same location/episode remain dependent. The builder must reproduce the reference-selection and refresh policy actually proposed for runtime use.

Maintain three clocks separately:

- `reference_at`: the supported wet observation clock.
- `reference_evidence_available_at`: when the source carrying that observation became available; publication is a supported historical approximation, while a later fetch proves availability only at fetch time.
- `prediction_as_of_at`: the time at which a prediction could actually be issued using then-available evidence.

Some historical wet lists occur inside later subsidence articles. They support historical wet evidence but do not prove that the list was publicly available at its embedded clock. A location projection can be proxy-admitted yet ineligible for prospective replay because its wet evidence became available only alongside its clearance evidence.

Only predictors available by the recorded prediction issuance time may enter a forecast. Store both feature valid/as-of time and availability time. Rainfall observed after issuance, later clearance text, terminal peak depth, and future-compiled context cannot become historical predictors without explicit version/as-of support. If physical/reference outcome bounds have already passed by issuance, preserve the historical bracket and exclude the row from positive-future-duration replay. Do not silently move the clock to make a positive training target.

This v1 target describes elapsed time from the wet reference. A later target for remaining time **at prediction issuance** must explicitly subtract the issuance/reference age, handle already-past/straddling bounds and carry its own version. The current plan does not pretend those two clocks are identical.

## Outcome bounds and missing follow-up

| Evidence | Label treatment |
| --- | --- |
| Supported precise reported endpoint | Exact reported-time label, preserving the source's actual clock precision. |
| Supported wet/clear bracket | Interval bounds with endpoint inclusivity; do not select the midpoint or upper bound as an exact duration. |
| Supported positive follow-up after an earlier reference | Potential lower bound under reviewed same-episode/no-intervening-end correspondence. |
| No qualified follow-up | Missing outcome; never extend confirmed wet persistence to collection cutoff. |
| Intervening clearance/reopening or unresolved recurrence | Split when supported, otherwise withhold a first-transition label. |
| DRRMO annual location/depth row | Optional context; no elapsed-duration outcome. |
| General locality duration consultation | Optional qualified context/prior; never copy it onto individual events as a label. |

A right-censored lower bound may use the last supported positive follow-up after a predefined earlier reference when target continuity is defensible. Later wet evidence alone cannot rule out an unobserved intervening recovery/re-flood; retain that assumption and withhold unresolved records. A lone wet snapshot has no informative positive elapsed lower bound and is not turned into a multi-hour censored example.

Reporting schedules may depend on severity, recovery and publisher practices. Interval-aware likelihoods handle bounded times, but do not automatically remove reporting-selection or informative-censoring bias. Preserve publisher/reporting-process metadata and audit sensitivity to source, interval width and missing outcomes. The [primarycensored method documentation](https://www.stat.ethz.ch/CRAN/web/packages/primarycensored/vignettes/why-it-works.html) explains its noninformative-censoring assumption; that assumption cannot simply be presumed for flood news.

## Delivered proxy register and future training columns

Keep source observations, summaries, histories and context CSVs separate as evidence inputs. The delivered proxy register has one conditional reference/outcome projection per row, with dependent groups retained. A later flat model CSV is a derived, versioned artifact; it is not a concatenation of incompatible row types.

| Group | Columns |
| --- | --- |
| Target and place | `label_id`, `candidate_id`, `target_version`, `city`, `qualified_barangay`, `location_raw`, `reported_location_id`, `section_id` |
| Dependencies | `candidate_timeline_id`, `reporting_episode_id`, `shared_outcome_group`, `storm_group_id`, `storm_identity_status` |
| Reference | `reference_observation_id`, `reference_at`, `reference_selection_policy`, `reference_clock_precision`, `reference_evidence_available_at`, `prediction_as_of_at`, `availability_status` |
| Outcome | `subsidence_observation_id`, `summary_as_of_at`, `outcome_kind`, `reported_scope`, `scope_linkage_class`, `reported_subsidence_lower_at`, `reported_subsidence_upper_at`, `lower_minutes`, `upper_minutes`, `lower_inclusive`, `upper_inclusive`, `censoring_type` |
| Interpretation | `continuity_before_reference`, `recurrence_after_summary`, `physical_section_label_status`, `physical_dry_status`, `passability_status`, `scope_condition` |
| Eligibility and review | `proxy_label_status`, `training_admitted`, `training_exclusion_reason`, `review_rule_id`, `review_rule_version` |
| Source lineage | `wet_source_id`, `subsidence_source_id`, `wet_capture_path`, `subsidence_capture_path`, `wet_capture_sha256`, `subsidence_capture_sha256`, `wet_source_line_start`, `subsidence_source_line_start`, `wet_source_url`, `subsidence_source_url` |

The current `censoring_type=upper_bound_with_positive_time_support` describes source evidence. Before fitting, map this deliberately to the selected fitter's positive-time/upper-bound representation while preserving original open/closed endpoints. It is not a universal library censoring enum.

**Future extensions, not shipped proxy-register columns:** supported `location_match_status`, source-specific publication/fetch clocks, operational feature-as-of/availability clocks, qualified depth predictors, and matched DRRMO/NOAH/rainfall context. Source manifests already preserve acquisition lineage; historical pre-outcome availability and predictor joins are not established by those manifests alone.

Unknown section geometry, onset, storm identity, clocks and numerical depths stay blank/explicitly unknown. Reported-place identities may support the declared reporting-location proxy; a verified physical road section is not invented to fill a column. DRRMO joins require actual supported locality matching. Source-year headings cannot supply event clocks or incident counts.

These are offline file fields, not approved SQLAlchemy columns or migrations. Building a proxy register under this contract is authorized planning/data work; application schema changes still require the repository's separate approval.

## Method and evaluation gates

1. Publish the three shared descriptive bounds and 37 conditional projections under this target policy. Count shared outcomes and candidate storm groups separately from row count.
2. Source qualification of the additional reports and the merged 819-observation register are complete. Continue prospective reference/availability review, physical section/timeline continuity, dependent storm identity and available predictor checks. Seek evidence that adds independent outcomes or tightens bounds, rather than repeating broad collection solely to inflate wet-row counts.
3. Start with an interval-aware empirical baseline when actual outcome support and identifiability permit it. The present three intervals all start at zero and give upper bounds only; they do not establish an exact median, road-specific duration curve or calibrated subsidence probability.
4. Compare a simple interval-capable parametric accelerated-failure-time model when independently grouped data support fitting and held-out evaluation. Consider nonlinear XGBoost AFT later, only with a measured benefit and compatible predictors.
5. Ordinary quantile regression is a comparator only for appropriately completed outcomes. Do not replace uncertain intervals with midpoint labels. A completed-only subset can be selected by reporting practices and must be audited for that bias.
6. Hold dependent location projections, shared summaries, repeated landmarks and storm/incident records together. Use chronological and geographic holdouts where support permits. Previously inspected sources are development material, not an untouched final evaluation set.
7. Evaluate interval-compatible predictive likelihood/calibration, horizon outcomes identifiable from the evidence, uncertainty width and operational policy errors. Do not score a predicted exact clock against an unknown exact subsidence time. Record support and abstention; produce reproducible model-result graphs only if a model is actually fitted and evaluated.
8. Require prospective shadow evaluation before estimates influence operational expiry or routing. No fitted model, performance claim or automatic retraining is delivered by this document.

[Official XGBoost AFT documentation](https://xgboost.readthedocs.io/en/stable/tutorials/aft_survival_analysis.html) supports exact, right-, left- and interval-censored ranged labels through native `DMatrix` and `xgboost.train`; its sklearn regressor interface does not accept ranged labels. This is a research candidate, not an installed dependency or selected production model.

[Lifelines interval fitting](https://lifelines.readthedocs.io/en/latest/fitters/univariate/KaplanMeierFitter.html) implements Turnbull estimation but is experimental and supports closed intervals. Preserve the original strict endpoints in the evidence contract even if a fitter needs an explicit documented approximation. [R survival outcome documentation](https://www.stat.ethz.ch/R-manual/R-devel/library/survival/html/Surv.html) also distinguishes censoring types and interval-compatible methods. [Scikit-learn grouped cross-validation guidance](https://scikit-learn.org/stable/modules/cross_validation.html) supports keeping related observations together rather than performing random row splits.

## Relationship to automatic expiry

The accepted [evidence lifecycle](flood-evidence-lifecycle-and-duration-plan.md) remains Active/Unconfirmed/Cleared. Recent qualified wet evidence refreshes Active; supported matched clearance can establish Cleared; insufficiently fresh evidence uses the accepted conditional two-hour Unconfirmed fallback. Unconfirmed means the current condition is unknown.

Predicted subsidence is an estimate with as-of time, uncertainty, input freshness and model version. Reaching the predicted time does not establish Cleared, verify a safe road, extend observational freshness, or generate a training label. Exact adaptive-deadline, retention and routing policy remains pending evaluation. Future reports can enlarge a reviewed dataset, but automatic self-training is not adopted.

The [offline follow-up builder](../../backend/scripts/build_pasig_duration_followup.py) now produces the merged wet register, conditional proxy register, wet-follow-up pairs and checksummed dataset manifest. The three wet-follow-up pairs remain unadmitted for right-censoring because uninterrupted episode persistence is not established. This delivery implements an offline evidence export, not application code, database changes, a trained model, a final training export or runtime expiry integration.
