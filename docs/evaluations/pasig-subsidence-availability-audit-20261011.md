# Pasig subsidence availability and depth audit — October 11, 2026

> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe).
> **Audit start:** October 11, 2026, 1:00:49 PM, Asia/Manila; targeted follow-up and production reads followed.
> **Status:** Historical pre-fix investigation snapshot. Availability/locality/lifecycle fixes subsequently deployed; accuracy remains unqualified. See [v3 post-release acceptance](pasig-subsidence-v3-acceptance-20261011.md).

## Live evidence

The following counts and API revision describe the original 1:00–1:07 PM investigation window, before the authorized fixes. They are preserved as RCA evidence; use the linked v3 acceptance for current runtime status.

The configured backend database was read under `SET TRANSACTION READ ONLY`; the targeted provenance check additionally used repeatable-read isolation. Forty-three zone records were inspected, including 22 active Pasig zones. The broad read used read-committed isolation and is an observation window rather than an atomic whole-system snapshot. The sanitized [active-zone table](pasig-subsidence-active-zones-20261011.csv) preserves observed IDs, depths, locality, saved method/deadline and blockers without reporter identity or source text.

Saved active policy counts: **seven pooled ML**, **eight cross-location ML**, **seven null fixed fallbacks**. No active zone had a qualified explicit wet-observation reference in this audit. Fifteen had approved submission or official-registration proxy forecasts; #36 additionally has a currently computable proxy but no saved forecast.

Protected production `GET /api/v1/admin/zones/{id}/expiry-policy` returned HTTP 200 and matched the database for #34/#36/#37/#47/#49/#54. The current API serves 100% traffic from revision `lanes-api-build-86a78939-ca6d-4bce-9d18-db533a8e1c23`, superseding the October 10 revision in historical release notes. Scheduled cloud expiry executions `lanes-zone-expiry-8j8hc` and `lanes-zone-expiry-qz25b` completed successfully around 1:00–1:01 PM PHT. A running worker does not guarantee a deadline when model qualification abstains.

## Availability RCA

| Zone | Source evidence and observed result |
| --- | --- |
| #36 | Official creation audit #300 at 10:40:27.570 AM PHT; saved policy `applied_at` 10:40:26.318 AM, before that source clock. At the later read, the unchanged registration simulation is valid and `choose_deadline` returns `ml_pooled`. `_source_signature` still equals the cached signature, so `apply_zone_policy` would return the saved null result before recalculating. This confirms a time-dependent negative-cache defect. Concurrent worker selection during creation is consistent with these clocks; this audit did not reproduce that interleaving with a controlled concurrency test. |
| #47 | Approved report #26; original submission audit #328 lacks `observed_at`. Follow-up #360 reports **subsided** at 12:08 PM PHT and has no review. Resolver correctly returns `needs_review`. |
| #49 | Report #29 says Rosario; the saved polygon resolves to Manggahan. It also has subsided follow-ups #355/#382. Resolver returns `needs_review`; no locality override was performed. |
| #50 | Report #30 says Rosario; saved polygon resolves to Manggahan. Resolver returns `needs_review`. |
| #54 | Legacy report #6 created September 26. Only approval audit #373 exists in its report audit history; no `CITIZEN_OBSERVATION` record or qualifying observed clock. |
| #55 | Legacy report #2 created September 22 PHT. Only approval audit #375 exists; no original observation audit. |
| #56 | Legacy report #3 created September 22 PHT. Only approval audit #377 exists; no original observation audit. Later zone edit #388 changes the depth snapshot to knee and spans Maybunga/Rosario. An edit cannot backfill a historical wet clock. |

These are not all missing-history failures. The #36 cache bug needs code repair; source/review gaps require real evidence or a deliberately separate evidence-retention policy. All seven have no retained fixed deadline, making their operational expiry unscheduled.

## Depth calculations and data sufficiency

Artifacts were loaded unchanged into the existing numerical functions. The [sensitivity table](pasig-subsidence-depth-sensitivity-20261011.csv) varies depth at zero elapsed time for Ugong, Maybunga and Santolan. No fit or runtime artifact was modified.

Pooled formula: `log(T_minutes)=6.964058396239009+0.4606544869441319*Z`, with standard-normal `Z`. It has no depth, rainfall or local-effect feature. At issuance equal to reference, `q50=exp(6.964058...)/60=17.632 hours` and `q90=31.819 hours`.

Cross-location location parameter: `mu=6.928022598674013+0.01593606426122616*(depth_cm-54.340246913580216)/29.981134725777245+local_effect`. For a location outside the four fitted locations, the central local effect is zero and prior uncertainty is added. Quantiles use the fitted residual variance plus coefficient variance and, for unseen locations, local prior variance.

| Counterfactual, Ugong, zero elapsed | Median | p90 |
| --- | --- | --- |
| Gutter proxy, 20.32 cm | 16.703 h | 38.684 h |
| Half-knee proxy, 25.40 cm | 16.748 h | 38.042 h |
| Knee proxy, 48.26 cm | 16.953 h | 36.701 h |
| Tires proxy, 66.04 cm | 17.114 h | 37.483 h |

The median gutter-to-knee ratio is `exp(0.015936064...*(48.26-20.32)/29.9811347...)=1.014961`. p90 need not increase with depth because this approximation's uncertainty also changes with depth. This is not a universal physical recession relationship. Operational expiry uses p90, not the median.

Actual shallow #37 has a depth-aware saved median of about 16.70 h; pooled #34/#38 have medians 17.63 h. Deep neck #40 also has the pooled 17.63 h median because 140 cm is outside cross-location training support. Their true clearance times are not established by these records, so an accuracy error in hours cannot yet be measured.

The historical 37-row candidate register shares three collective outcome groups: eight rows with intervals 1,740–2,000 minutes; one row with 930–1,050 minutes; and 28 rows sharing another summary with several intervals (including 510–870 minutes). The depth model retains 36 rows. This explains the long historical duration pattern and poor identification of independent depth effects. Each summary is group-weighted, not counted as many independent labels. Artifact lineage retains zero production-training admission, no verified independent storm count and no prospective calibration.

## Source paths inspected

- `backend/app/services/pasig_ml_expiry_service.py`: cache identity/early return, p90 policy, 48-hour bound, null fallback and saved forecast DTO.
- `backend/app/services/zone_prediction_service.py` and `backend/app/crud/zone_prediction.py`: geometry/location resolution, observation/submission/registration gates, edit rejection and immutable clocks.
- `backend/app/services/cross_location_prediction_service.py`: frozen depth provenance, single-locality gate and 5–91.44 cm support.
- `backend/app/services/cross_location_duration_model.py` and `flood_duration_model.py`: standardized depth/local effects, censoring, conditioning and uncertainty calculation.
- `backend/runtime_data/flood-duration/{conditional_aft,cross_location_aft,cross_location_evaluation}.json`: coefficients, lineage, three shared summaries and incomplete evaluation.
- `docs/evaluations/pasig-duration-model-20261007/conditional_training_candidates.csv`: interval and shared-summary audit.
- `frontend/src/features/flood-followups/{CaseReviewSuggestion,ZoneExpiryPolicy}.tsx`: separate saved operational forecast, pooled simulation and comparison presentation. Browser behavior was not tested in this investigation.

## Proposed acceptance gates

1. Reproduce the #36 race with a controlled future-source clock, then prove a later worker retries without moving original issuance or granting unrelated evidence.
2. Ensure review/geometry/legacy blockers remain explicit and preserve qualified clearance handling; verify any new unavailable-fallback policy independently from prediction.
3. Align the primary UI estimate with the operationally chosen model on desktop/mobile while retaining evidence/proxy warnings.
4. Train improved candidates only from reviewed, episode-matched wet/clearance bounds; exclude expiry, staff approval and simulated test outcomes from dry labels.
5. Require grouped, temporal and unseen-location evaluation; report interval coverage, availability, censoring, calibration and shallow/deep behavior against current artifacts.

[Research, sources and recommended model sequence](../research/pasig-flood-recession-depth-and-availability-20261011.md).

No application, model, schema, dependency, production configuration or record mutation was performed. Read-only diagnostics and calculations are not an automated regression-suite pass or predictive validation. The documentation and sanitized diagnostic tables are the deliverables of this task.
