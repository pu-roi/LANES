# Pasig real-outcome collection readiness — October 11, 2026

**Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe). **Status:** offline pairing tool implemented and tested; no new real outcomes, model promotion or deployment.

The shared private `GET /api/v1/admin/flood-follow-ups/export?review_state=all&limit=100` was read with an existing authorized staff session. All pagination was retained. It returned one complete page with **three follow-ups across two reports (#26/#29), all pending review, zero numeric depth measurements**. No source review, record, zone, deadline or training-admission write was made. Private text/URLs/request identifiers remain in ignored local export storage; this evaluation contains sanitized counts/identities and hashes only.

The developer confirmed the groupmate's manual submissions were workflow tests. No episode was declared field-verified. The new offline dataset builder therefore yields **zero conditional research candidates and zero production-training admission**. This is evidence of a data gap, not a reason to turn tests or administrative expiry into observed subsidence labels.

| Collection gate | Current evidence |
| --- | --- |
| Follow-up observations / reports | 3 / 2 |
| Independent accepted source reviews | 0; all three pending |
| Numeric depth sources | 0 |
| Explicit episode/extent/continuity reviews | 0 |
| Source snapshot with missing Pasig episode identity | 1 |
| Conditional research candidates | 0 |
| Actual prospective calibration examples | 0 established by this export |

## Delivered builder

`backend/app/services/recession_dataset_service.py` and `python -m scripts.build_recession_dataset` accept the complete existing staff export and explicit episode-review rules. The builder has no database/network writes, model fit or artifact promotion. It:

- Requires declared all-review-state pagination from the first page through the terminal cursor, so pending or contradictory observations are not silently filtered out.
- Checks accepted independent source reviews, explicit observation/submission/review chronology, report/zone/event/geometry identity and human same-section/continuity declarations. Test/unclassified samples remain blocked.
- Uses only the first selected wet observation's frozen numeric depth and a resolved single-locality feature snapshot. It does not borrow a current depth or newly fetched weather as historical input. This version does not admit environmental predictors or convert multi-locality/gauge-only sources into measured values.
- Derives `(last_wet − reference_wet, first_reported_clearance − reference_wet]` under declared continuity/same-extent assumptions. Without a clearance endpoint, a later verified wet observation supports right censoring; later non-rejected claims prevent selectively hiding a known endpoint. True onset stays unknown.
- Records a **simulated** submission-time hindcast anchor, with actual source-review and outcome-qualification availability separately retained. Retrospective review does not manufacture an actual issued forecast or prospective calibration result.
- Rejects intervening clearance/recurrence, changed scope, incomplete clocks, self review, duplicate episode/reference/endpoint rules and invalid feature provenance. Human field/scope statements are not automatically verified; filesystem rules cannot grant production admission.
- Parses and hashes the same bounded input bytes, emits allowlisted numerical/source identities, and refuses to overwrite a recorded output directory.

**26 tests passed** in `backend/tests/test_recession_dataset.py`, including both censoring cases, privacy, review/test/scope/chronology guards, pagination, contradiction/recurrence, retrospective versus issued-forecast provenance and a file-change-during-build lineage regression. Three existing multipart/Pydantic warnings remain. Tests use synthetic fixtures to exercise the code; their outcomes are not field evidence.

## Recorded outputs and reproduction

[final/dataset.json](final/dataset.json) is the final acceptance output and retains exact export, builder and qualifier hashes. [dataset.json](dataset.json) preserves the initial readiness run; [validated/dataset.json](validated/dataset.json) preserves the intermediate run after separating retrospective hindcast issuance from actual forecasts. All three runs report the same live 3/2/0-candidate shortage. Earlier snapshots are historical, with their own source-code hashes.

The private export was captured before the builder run; no new publisher/AI-provider acquisition was triggered. Rebuild with a newly captured complete export and explicit human rules, writing to a new directory. [Collection guide and file contract](../../guides/pasig-recession-observation-collection.md#offline-pairing-and-qualification).

Interval/right-censored target representation follows the [official AFT documentation](https://xgboost.readthedocs.io/en/stable/tutorials/aft_survival_analysis.html). This design reuses existing Python/Pydantic; it does not add XGBoost or establish suitability/calibration on Pasig floods. Its target version is separate from the existing three-summary historical cohort and cannot silently merge with or replace runtime artifacts.

## Completion audit

### Revalidation — October 11, 2:29 PM PHT

The current authorized all-state export was re-read and run through the unchanged final builder. [recheck/dataset.json](recheck/dataset.json) still reports three pending follow-ups across two reports, zero numeric depths, zero episode reviews and zero candidates. Its private capture is retained separately; captured-byte and current builder/qualifier hashes match. Original readiness outputs remain historical. During this recheck the diagnostic helper reused its old private export filename; that earlier raw capture is no longer retained, although its recorded hash remains in the earlier results. The helper now reserves a unique capture filename per call to preserve subsequent evidence snapshots.

| Requirement | Completion evidence or remaining gap |
| --- | --- |
| Repair operational unavailable/cache/lifecycle failures | v3 acceptance records original-clock recovery, configured Unconfirmed retention, native tests and matching local/shared API/workers. |
| Resolve OSM/PSGC locality correctly | Final-geometry resolution and immutable Manggahan corrections are implemented; all-30 locality and source-identity regressions are recorded. |
| Explain/show the saved selected forecast | Local desktop/mobile fixture and actual workflow acceptance recorded; optional hosted frontend release remains separate. |
| Improve and verify the learned shallow/deep duration response | **Not achieved.** The existing pooled model lacks depth; the tested constrained candidate barely changes the coefficient, and its forward-time folds are unsupported. |
| Obtain independent real outcomes for evaluation/calibration | **Not achieved.** Current test/source claims are pending and lack numeric depth; no field-verified episode reviews or qualified durations are present. |

The last two goal turns delivered engineering/docs and the offline builder while identifying this same real-outcome shortage. The third consecutive audit revalidates it. No source links or actual record IDs have arrived in response to the pending evidence question. Tests, administrative expiry, inferred clocks, model predictions and newly fetched weather cannot establish the missing observed targets. Further fitting or an arbitrary shorter shallow timer would not prove the requested accuracy improvement. Full goal completion remains unproven; scientific validation requires human field/source evidence or another external data change.

The [v3 acceptance](../pasig-subsidence-v3-acceptance-20261011.md) proves operational cache/locality/expiry fixes and local responsive UI behavior. The current export contradicts any claim that LANES already has reviewed real road-section duration data for a new calibration. Scientific improvement remains unproven: the constrained candidate did not improve the depth response, and the new builder has no eligible field examples to fit. Real verified observations or source-linked outcomes remain required; an asynchronous source/record-ID question is pending.

All eight core documents were audited. README/task/progress and the collection plan/guide now link this tool and live result. The existing Spatial Operations/system records identify the offline entry point. No new flagship feature/architectural decision, dependency, SQLAlchemy model, migration, API endpoint or UI flow is added. The shared API/workers continue on v3; the offline tool exists in the local worktree and was not separately deployed. Hosted forecast UI release remains separate.
