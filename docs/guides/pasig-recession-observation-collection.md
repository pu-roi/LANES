# Collecting evidence for Pasig flood recession predictions

**Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe). **Purpose:** create defensible, reviewed road-section outcomes for depth-aware model evaluation. These instructions do not promote existing test reports into training data.

The current model has only three shared historical outcome summaries. More test records exercise the application but do not establish real clearance times. Collect observations only where staff/citizens can safely observe; do not enter floodwater to measure it.

For the October 11 investigation, the developer confirmed the groupmate's entries were tests through the public manual-report panel. Keep those records as workflow evidence. A submitted depth and predicted expiry cannot supply an observed recession duration. [Engineering fixes and test-record outcomes](../evaluations/pasig-subsidence-v3-acceptance-20261011.md).

1. Record the exact road section and actual observation time when water is present. Use the same drawn/snapped section throughout the episode. The location label follows reviewed administrative geometry; it is not sufficient on its own to match episodes.
2. Record the selected depth gauge and its basis. A canonical gauge is a proxy, not a ruler measurement. Where a numeric depth is already safely available, record it in the same-report follow-up's centimetre field with its actual observation time. Record whether water is rising, stable or falling in the supporting description; unknown answers remain unknown.
3. Submit subsequent observations through the original report's follow-up or the zone's current-condition update. Record the time observed, not the upload time. Keep the road section/extent explicit. Do not treat a dry point as clearance of the whole avoidance polygon.
4. Have a different authorized staff member review the source and same-location correspondence. Accepted source claims remain claims; they do not automatically clear a zone or become admitted model labels. Pending/dismissed claims, geometry/event changes and incomplete clocks require qualification.
5. Retain the last reviewed wet observation and the first subsequent reviewed clearance claim for the same scope and episode. Their times bracket the reported transition only under explicit continuity and same-scope assumptions, with no intervening contradictory/recurrent episode. Relative to a qualified first recorded wet reference, the duration lies between `last_wet − first_wet` and `first_cleared − first_wet`; this reference is not necessarily the true flood onset. Without a later clearance endpoint, retain right censoring after the last supported wet time. Do not replace missing endpoints with the worker's expiry time.
6. Freeze predictors available at the chosen forecast issuance. Keep observation, recording and review clocks separate. Rainfall/elevation fetched today cannot be imputed as historically available predictors. Identify episodes and storms where evidence supports them; otherwise retain unknown storm identity.

Use staff-only source exports: `GET /api/v1/admin/zones/{id}/model-evidence` for current-condition updates and the existing follow-up export for owner observations/reviews. Both retain qualification blockers and `training_admitted=false`. Export before any research fit; explicitly verify scope, clocks, independent review, event identity and source feature availability. These exports do not by themselves admit production training labels.

Evaluate by held-out episode/summary, location and forward time. Keep rows sharing an outcome together and prevent future evidence entering historical predictors. Compare pooled survival and depth-aware candidates, including shallow/deep strata, interval likelihood, calibration, coverage and abstention rate. Do not choose a model solely because its displayed times look shorter. Dataset sufficiency depends on independent outcome diversity and calibration results, not an arbitrary number of duplicated reports.

Existing records #47/#49 have pending subsided claims; staff must review them rather than the agent accepting them automatically. Legacy #54–#56 lack their original timed wet audits, so a new current observation cannot repair their historical onset. Such records can exercise retention/review behavior but cannot supply an invented historical duration.

[Research](../research/pasig-flood-recession-depth-and-availability-20261011.md) · [Depth candidate result](../evaluations/pasig-depth-shape-candidate-20261011/README.md).

## Offline pairing and qualification

The implemented `scripts.build_recession_dataset` is an offline research step, not an automatic training or clearance job. Export **all** review states from `GET /api/v1/admin/flood-follow-ups/export?review_state=all&limit=100`, starting without `before_id`. Follow each returned `next_before_id` with `before_id` until it is null. Keep private source text outside Git, for example under ignored `backend/data/`. Wrap the complete pages as:

```json
{
  "schema_version": 1,
  "selection": {"review_state": "all", "first_before_id": null},
  "pages": ["replace this string with each complete JSON response body"]
}
```

The selection header declares acquisition provenance; the tool cannot prove that a manually supplied file originated from the API. It validates pagination/chronology and records input hashes. Authorized source review remains in the existing application. Keep the source export intact rather than editing its claims to pass qualification.

A separate JSON array contains explicit episode reviews. The following IDs are placeholders, not existing qualified records:

```json
[
  {
    "episode_id": "replace-with-reviewed-episode-identity",
    "reference_id": 1000,
    "endpoint_id": 1001,
    "reviewer_id": 1,
    "reviewed_at": "2026-10-11T06:00:00Z",
    "sample_kind": "unclassified",
    "same_section_verified": false,
    "continuity_verified": false,
    "storm_group": null
  }
]
```

Set `sample_kind=field_verified` only after checking genuine observations. Both extent/continuity flags require review of the **same complete report section**, not merely a point inside it. The episode reviewer must differ from all observation authors. Unknown storms remain null. File-based declarations are auditable research claims, not authorized production label writes. Test records must remain `test`; source approval alone does not establish the truth of a measured flood duration.

The reference must be a timed accepted wet observation with frozen numeric depth and one resolved locality. Choose the first reported clearance in the reviewed window, or its latest supported wet endpoint for right censoring. The builder rejects pending/intervening signals, changed geometry/event, contradictory wet/dry clocks, unsupported inputs and hidden later observations. Retrospective source review may qualify evidence for hindcasting, but cannot create a historical issued forecast; the submission-time anchor is labelled simulated. Actual prospective validation requires saved forecasts and later real outcomes.

From `backend/`, run:

```powershell
venv/Scripts/python.exe -m scripts.build_recession_dataset --export data/recession-source-export.json --reviews data/recession-episode-reviews.json --output ../docs/evaluations/pasig-recession-outcomes-YYYYMMDD
```

Omitting `--reviews` produces a collection-gap audit and no automatically paired candidates. Outputs contain numerical/source identities, qualification blockers and byte/code hashes; private source text/media/URLs are omitted. Use a new output directory each time. Every result remains `production_training_admitted=false`. This target starts at the first selected recorded wet observation, with unknown true onset; keep its target version distinct from prior summary-derived cohorts before fitting/evaluation.

[October 11 actual export: three pending follow-ups, no eligible outcomes](../evaluations/pasig-recession-collection-readiness-20261011/README.md).
