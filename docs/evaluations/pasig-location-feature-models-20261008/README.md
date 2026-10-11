# Complete Pasig prediction locality and feature-model evaluation

> **Date:** October 08, 2026, 02:06 PM (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Automatic prediction location coverage completed locally for 30 barangays. Feature capture/inspection and model comparisons implemented; the feature candidates are not selected because they do not improve held-group results. Learned street-specific duration accuracy remains open.

The developer asks to remove two limits: the missing ten automatic-locality boundaries and the shared duration pattern. This delivery completes the location catalog and implements/evaluates the feature pipeline. It does not claim the second accuracy problem is solved or replace the working baseline with a worse candidate.

## Complete source-consistent location catalog

The OCHA/HDX [Philippines COD-AB source dataset](https://data.humdata.org/dataset/cod-ab-phl) attributes NAMRIA/PSA and supplies a CC BY-IGO licence. Its public [CKAN metadata](https://data.humdata.org/api/3/action/package_show?id=cod-ab-phl) and downloadable shapefile are captured; token-required GeoRisk/Esri services and generalized third-party conversions were not used. Dataset notes and row valid_on dates do not certify a new cadastral survey. Use this as analytical humanitarian locality geometry, not legal boundaries or observed flooded extent.

The source has all 30 Pasig barangay records and one source-consistent Pasig city polygon. Exact current/legacy PSGC identities and parents match; San Nicolas (Pob.) is an explicit code-bound name crosswalk. All source shapes are valid, have disjoint interiors and exactly partition the parent city. No shape is clipped, simplified, repaired, buffered, synthesized or inferred from a nearest pin.

`fetch_pasig_cod_boundaries.py` reads ZIP ranges, validates full DBF/SHX member CRCs, decompresses original shape streams through the selected records, and archives every selected binary shape with SHA-256. National ZIP SHA/full shape-member CRC is not claimed for partial streams. Original compressed prefixes total approximately 206 MiB and remain under ignored data/pasig-local-model-20261008. The extracted parent/barangay GeoJSON and metadata have recorded hashes. Runtime source subset is only about 211 KiB; catalog/city/manifest remain small. Source snapshot field uses the row valid_on 2025-02-13, not a field-survey date.

Installed separate catalog: backend/runtime_data/flood-location. Catalog SHA-256: `65d88755d7e0f25d4f1648406cfa16ed76244bae6d4849098ed233b22a1b9724`; source subset SHA-256: `a2c20c736a71590f00f2580504ec9518028eb2f9b64721f39ff966c7c1eeb767`. The provider verifies checksums, 30 unique canonical identities, valid same-source parent containment, complete partition and no interior overlap. Source/licence attribution is retained. Existing OSM/NOAH news placement remains on its separate 20-record community catalog and has unchanged operational footprint gates.

`zone_prediction_service.resolve_location` uses the complete prediction catalog. New street names need not appear in training data: geometry selects locality. Outside-city, invalid and multi-barangay/ambiguous footprints still return explicit states. Native tests exercise a valid new-street zone in each of all 30 source polygons, plus outside/crossing/checksum cases. Complete names do not remove border uncertainty or establish flood footprint correctness.

## Feature pipeline and source limits

`flood_feature_service` extracts source coordinates, geometry digest, boundary revision, canonical locality and a labeled gauge-depth proxy. New CITIZEN_OBSERVATION, CREATE_OFFICIAL_ZONE and UPDATE_ZONE audits freeze these versioned inputs without adding SQL columns or user fields. Actual observed time remains null when absent. Normal writes take available cached environment and never wait on optional external providers; an absent cache is explicitly not_captured. No older audit is backfilled.

Authenticated Reports and Zones readers can GET `/api/v1/admin/zones/{zone_id}/prediction-features`. It returns fresh source-labeled input context, using fixed bounded Open-Meteo HTTPS endpoints, short time budgets, no redirects/credentials, size limits and a bounded hourly cache. Errors and absent values remain visible; no zero/guessed capacity is substituted. The existing Overview calculation details load this lazily with visible loading/retry/source failures and no new input/page/tab/bubble or Moderation content.

[Open-Meteo elevation](https://open-meteo.com/en/docs/elevation-api) supplies Copernicus GLO-90 modelled surface elevation (90 m), not measured street/drain invert height. Rainfall is ECMWF IFS 0.25-degree coarse-grid background; store requested versus grid coordinates, actual capture time and prior-hour interval. Future hours are excluded. Current weather values cannot be backdated as historically available predictors. [Historical weather](https://open-meteo.com/en/docs/historical-weather-api) and [archived forecasts](https://open-meteo.com/en/docs/historical-forecast-api) have different availability semantics. Drainage/pump capacity remains unknown; weather/terrain context is not yet used by the active baseline because its effects are not fitted/qualified. Open-Meteo/Copernicus attribution is displayed in details.

## Actual model comparisons

The [feature comparison report](feature_comparison.json), [depth-feature AFT artifact](depth_feature_aft.json) and [251 depth-change pairs](depth_trajectory_pairs.csv) are new versioned analysis outputs. Original observations, 37 duration projections and both runtime baseline artifacts are preserved byte-for-byte.

A depth-feature lognormal AFT fit uses 36 qualified first-depth rows, excluding one uncertain unit conversion. It learns depth coefficient approximately -0.0301 on standardized depth, a small effect. Whole-summary holdout results:

| Held summary | Intercept NLL | Depth-feature NLL |
| --- | ---: | ---: |
| Dela Paz | 2.493 | 2.503 |
| August 30 collective summary | 3.332 | Unidentifiable |
| Maybunga | 6.503 | 13.767 |

Lower NLL is better; the candidate is worse on completed folds and unidentifiable on the remaining one. This does not support promotion to active prediction or a claim of learned drainage/rainfall effects.

A separate Ridge depth-change candidate uses current depth, elapsed hours and canonical barangay. It uses adjacent exact numeric snapshots within candidate timeline/episode and a maximum six-hour interval; conflicting clocks break adjacency. It predicts the next reported depth, not a future observed dry label. The 251 pairs span only three reporting episodes: **224 unchanged, 14 rising and 13 falling**. Whole-episode holdouts:

| Held episode | Pairs | Depth/location model MAE (cm) | Depth-stays-unchanged MAE (cm) |
| --- | ---: | ---: | ---: |
| July 2025 | 185 | 22.561 | 4.586 |
| August 17–18, 2026 | 35 | 4.601 | 0.000 |
| August 29–30, 2026 | 31 | 17.960 | 11.227 |

The location/depth candidate is worse in every held episode. No model-estimated dry labels or depth-to-zero extrapolations are used as observed truth. The active subsidence/passability baselines remain selected. Source/reporting episodes are proxy groups, not independently verified storms or prospective accuracy.

The mathematical kernel already supports features and censoring; [XGBoost AFT](https://xgboost.readthedocs.io/en/stable/tutorials/aft_survival_analysis.html) is a future nonlinear candidate, not a new dependency adopted here. More complex algorithms cannot establish street-specific capacity from absent observations. Independent timed wet/subsided outcomes, matched street/extent, quality depth changes and source-available environmental/drainage measurements remain necessary.

## Developer-selected future LANES evidence collection

The developer chooses future LANES reports and reviews as the next evidence source. Public zone updates now freeze prediction_features and model_evidence with actual/null observation clock, recorded-at clock, event/version, gauge-or-missing depth and explicit claimed-point/proposed-road/official-context geometry basis. No floodwater remains a spot/road source claim; it does not manufacture zero depth, a whole-zone dry endpoint or a training label. Submission records are stamped after media/road validation; weather captured after that clock cannot be backdated into a snapshot.

Owner still-flooded/subsided follow-ups freeze their actual supplied numeric centimetres and explicit observation clock, never an old report gauge. The existing private owner/staff/export contracts retain those snapshots; legacy records have null features instead of a backfill.

Independent public reviews record the reviewed zone version and remain model-unadmitted. Staff with Reports and Zones read capability can GET `/api/v1/admin/zones/{zone_id}/model-evidence?limit=50&before_id=...`; bounded keyset export separates pending/reviewed/dismissed sources, missing clocks, geometry scope, episode/source features and qualification blockers. It omits usernames, free text, media URLs and request UUIDs. Commuter/missing-capability access is denied; no-store and operational read-only behavior are tested. No new frontend input or automatic retraining is introduced. Export blockers also identify non-condition detail updates and absent/unresolved source locality features. More independent matching timed outcomes are still needed before the feature models can be selected. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Verification and live state

A comprehensive run passes **256 backend/model checks** across complete locality, input snapshots, feature evaluation, zone prediction, old news boundaries, settings, community editor/update/growth and original subsidence/passability/case contracts. The final comprehensive run includes numeric precision, causal cache clocks and future public/owner source-export coverage. The earlier ten-case targeted run is a historical intermediate check. Existing Alembic head d7e4b9a21c60 applies in disposed local PostGIS databases; no schema/package change. All **38 desktop/mobile workflow cases**, TypeScript/scoped lint and the runtime asset verifier pass. The verifier now reports separate news-qualified 20 versus prediction-locality 30 counts.

Real authenticated desktop/mobile Zone #17 calls return Ugong through the new catalog and HTTP 200 from prediction/context endpoints. Actual current context includes modelled elevation about 14 m and a coarse rainfall grid near 14.5 latitude/121 longitude; values change with actual retrieval hour and do not change the anchored forecast. No API responses are mocked in those flows; source labels/unknown observation/no manual fields and both layouts are inspected. Screenshots remain ignored under frontend/test-results/real-location-features-desktop.png and real-location-features-mobile.png. The short-lived JWT stayed in process/browser memory and was not saved.

Read-only shared-DB inspection finds zero CITIZEN_OBSERVATION, FLOOD_FOLLOWUP_OBSERVATION/REVIEW and ZONE_PUBLIC_OBSERVATION/REVIEW records at this checkpoint. There are no additional live timed outcomes to rescue the failed candidates. Future snapshot hooks are implemented, but no new real observations are fabricated or collected by this task.

No application/cloud evidence or model-label rewrite, public routing/status/expiry write, agency message, deployment, commit or push. Local API restarted to load the new modules. Physical PWA, independent feature-model accuracy and forecast-to-Unconfirmed/public retention remain open.

## Senior-planner documentation audit

**October 08, 2026, 03:07 PM PHT.** [@roicambe](https://github.com/roicambe) (Roi Cambe) audits the eight authoritative records on `roi-branch`, using current service/router/audit-action sources, dependency manifests and SHA-256 identities. This pass changes documentation only; the recorded 256 backend/38 responsive acceptance and two actual Zone #17 flows above are not new test runs.

| Core record | Audit disposition |
| --- | --- |
| [Tech stack](../../tech-stack.md) | Register selected subsidence/passability AFT models, unselected depth/location candidates, existing declared dependencies, COD locality assets and bounded environmental providers. Correct historical plotting wording that implied no later fitted model. |
| [Task plan](../../task_plan.md) | Point current acceptance to the final verification; mark future source capture/export and this documentation audit delivered, while retaining accuracy/expiry/public-retention/release gates. |
| [Progress](../../progress.md) | Add the documentation reconciliation above earlier milestones; preserve implementation and verification history. |
| [Feature reference](../../feature-reference.md) | Extend the existing Spatial Operations module with future reports/reviews/export; add no new flagship feature or UI workflow. |
| [Decisions](../../decisions.md) | Reviewed and retained unchanged in this pass: Decision 24 already records pooled new-street transfer, distinct complete locality, feature qualification and the developer-selected future LANES evidence source. |
| [System documentation](../../others/system-documentation.md) | Record existing Overview/component placement, three full private API paths, capability/privacy/cache behavior and automatic source-selection flow. |
| [Database design](../../others/database-design-plan.md) | Map existing audit actions to versioned feature/review JSON; preserve actual/null clocks, geometry scope, legacy missing values and explicit non-admission. No new relational schema. |
| [Bug log](../../others/bug-log.md) | Keep BUG-128 In Progress for learned model improvement while recording resolved locality and delivered future collection/export. |

The master index is synchronized, including four older timeout-follow-up anchors whose target heading now includes an earlier-diagnosis suffix. Current subsidence artifact SHA remains `eef51e6c0f5ba03efbba44272f64a71ceccef0c0574e9b575d3d084b0c9f0bc6`; passability remains `391eaa894717722963d38b6fd34276ef737a33e3224351433b794aa88ddf958c`; complete prediction catalog remains `65d88755d7e0f25d4f1648406cfa16ed76244bae6d4849098ed233b22a1b9724`. Dependency manifests, SQLAlchemy models and Alembic definitions have no changes in this continuation. Existing head application is recorded above; no migration/build/provider request or deployment is performed by the documentation pass.

The next implementation remains the server-owned forecast-to-Unconfirmed/public-retention/update workflow. More real independent matched outcomes are needed to select a better street-specific model; snapshot collection is implemented but prospective evidence and accuracy are not complete. Links and unchanged application-file hashes are checked at the documentation checkpoint.

## Pre-push verification — October 8

The developer requests publication to `roi-branch`. The branch is verified; dependency manifests and SQLAlchemy/Alembic definitions remain unchanged. A fresh disposable-PostGIS run of `test_operational_settings_postgres.py` passes **24 checks**, with the shared fixture applying `alembic upgrade head`; the generated databases are removed afterward. This is a migration/settings pre-push check, separate from the earlier comprehensive 256-check acceptance.

The runtime asset verifier returns `assets_ok`, prediction barangays 30 and separate news-qualified barangays 20, with the recorded catalog SHA unchanged. Changed-file Python imports use declared packages or existing local script/test modules. Credential-pattern and sensitive-filename scans find no matches. New checksum-preserved asset/evaluation/script attributes use the existing CRLF-aware whitespace policy, so staged checks preserve recorded bytes across Windows/Linux checkouts. Previously recorded desktop/mobile verification remains applicable because application source is unchanged since that acceptance. No live migration, deployment, automated retraining or operational forecast expiry is performed. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Reproduce

From backend:

```powershell
python -m scripts.fetch_pasig_cod_boundaries
python -m scripts.build_pasig_location_catalog
python -m scripts.evaluate_pasig_feature_models
python -m scripts.verify_news_runtime_assets
```

Source extraction downloads bounded portions of public assets and caches original records under ignored data. Catalog build validates that source and writes the working version; restart processes and verify the revision after any intentional asset change. Model evaluation never overwrites runtime baselines. Do not concatenate transport outcomes, depth changes and physical subsidence into one target or treat counts as independent storms.
