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

## Government data acquisition specification — October 11 continuation

The developer confirmed there are no additional government flood-history files yet. Request existing, anonymized event-level records from Pasig DRRMO or MMDA for Pasig roads, including both shallow/short and deep/long episodes and observations with unknown outcomes. Historical records from comparable surrounding cities can support a later transfer experiment only after target, measurement and hydrologic context are reviewed. City proximity alone does not justify combining labels. This specification is a prepared request, not a request already submitted or an acquired dataset.

Suggested request text:

> We are conducting academic research for LANES on flood-water recession and route-condition evidence in Pasig City. May we obtain existing anonymized flood-monitoring records, preferably CSV/XLSX with the original field descriptions, for available Pasig road-section episodes? We need actual observation dates/times and timezones, road-section identities/extent or coordinates, measured water depths and units/method, successive wet observations, and the first observed subsidence/clearance condition with its definition and timestamp. Please retain incomplete episodes, sampling gaps and unknown values, rather than replacing them with estimated durations. If available, include storm/event identifiers, rainfall, river/backwater, tide and pumping/drainage operating context with their observation times. Please provide source/collection methods, revisions and permitted research use. Personal names, contact details and household identifiers are not required. If only aggregate duration summaries exist, please distinguish them from individually observed events and explain how duration and clearance were defined.

| Requested field group | Why it is needed |
| --- | --- |
| Source record/event ID, storm ID if known | Deduplicate shared outcomes and separate episodes/time/storms for validation. |
| City/barangay, road name and section endpoints/extent | Match observations to the same physical section; resolve identity through the existing reviewed geometry/PSGC catalog. Names alone do not certify a polygon. |
| Observation timestamp with timezone; recorded/revised timestamp | Distinguish water-state time from upload/review time and identify which predictors were available at issuance. |
| Depth value/unit, measured-versus-gauge basis, method and location within the section | Prevent canonical gauge proxies from being treated as ruler measurements or point readings as whole-section depths. |
| All successive wet and subsidence/clearance observations, plus sampling gaps | Establish interval/right censoring and detect recurrence; missing next-day listings do not imply clearance. |
| Clearance definition/threshold and spatial scope | A passable road, reduced water, and a dry section are different outcomes. Keep the reported definition rather than silently substituting zero depth. |
| Rainfall/inflow, river/tide/backwater, pump/drainage context if recorded, each with its timestamp | Investigate mechanisms beyond depth without inventing historical environmental inputs. Unknown values remain unknown. |
| Collection method, source document, correction history, coverage and research-use terms | Establish lineage, representativeness and reproducible qualification. |

Public acquisition leads checked October 11:

- [Pasig flood-history request, USAP-882318571725](https://www.foi.gov.ph/agencies/usap/flood-history-in-pasig-city/): the retrieved detail says PENDING and exposes no dataset; generic progress/search badges conflict. Do not treat it as a successful data delivery.
- [Metro Manila flood reports, MMDA-418642086637](https://www.foi.gov.ph/agencies/mmda/history-of-flood-reports-in-metro-manila-20152024/): the agency response says records were delivered by email to that requester. No downloadable training file was established from the public page. This does not authorize accessing somebody else's email.
- [Marikina hourly flood levels, MMDA-520123386008](https://www.foi.gov.ph/requests/historical-data-on-hourly-optional-flood-levels-of-flood-prone-areas-in-marikina-city/): the response refers the requester to Marikina DRRM rather than exposing a dataset. River gauges and road-water depths need separate target review.
- [MMDA-046843049063](https://www.foi.gov.ph/requests/request-for-dataset-of-dailyhourly-flood-levels-of-flood-prone-areas-in-metro-manila/): an indexed request lead, but direct retrieval returned 503; its delivered contents remain unverified.

Retain raw delivered files privately and unchanged with their hashes and provenance. Review their actual fields before designing an importer: an external government table is not the existing LANES follow-up export and must not be fabricated into authenticated staff observations. The offline builder above remains specific to LANES source exports. Any government-data adapter must preserve its distinct source/review contract, target and censoring, and cannot automatically admit labels or refit production. Once qualified, evaluate comparative depth/context/location effects on independent held-out episodes and forward time before promoting a model.
