# Cross-location duration implementation and conditional evaluation

> **Last Updated:** October 09, 2026, 12:07 AM (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Implemented locally as an automatic private research comparison. Primary baseline selection, prospective qualification and deployment remain separate.

## Delivered behaviour

The [implementation plan](../../plans/cross-location-flood-prediction.md) follows the [research](../../research/cross-location-flood-prediction.md). A separate fixed-prior penalized lognormal AFT model shares one standardized depth effect and restrains canonical-barangay intercepts. Unseen locations receive the shared relationship plus local prior variance. This is exchangeability-based pooling, not a learned drainage network or physical-neighbour connection.

The evaluator verifies the seven existing comparison input hashes and retained source captures, exports qualification reasons, and compares pooled-depth/partial-pooling candidates at local prior scales 0, 0.15, 0.35 and 0.70. Each summary contributes total likelihood weight one, recomputed per fold; preprocessing uses training data only. The 0.35 comparison prior is predeclared, not optimized on these holdouts.

GET `/api/v1/admin/zones/{zone_id}/cross-location-prediction` uses existing zone eligibility, then reads the exact selected audit by ID, action, table and target. It requires Reports+Zones read capability and no-store. Missing/corrupt models and unsupported evidence expose reasons; database failures use normal private API error handling.

**Use locally:** Spatial Operations → Active Zones → Info → Overview → View calculation details → **Depth and location comparison · research only**. The shared component loads lazily and refreshes while open, without new input forms or save controls. The primary estimate remains visible separately.

Frozen numeric depth must match the chosen wet clock, source geometry and locality. Frozen gauge conversions produce labelled proxy-depth simulations, not numeric measurements. Registration/submission simulations preserve unknown actual observation time and fixed issuance. Current depth/weather cannot backfill old inputs. Missing features, clock/scope conflicts, unsupported depth, multi-barangay footprints, unsupported news snapshots and inactive/stale/review-pending cases abstain.

## Actual comparison results

The export has 36 conditional historical records and one rejected uncertain depth row; production admission remains zero. The 36 records share three summaries. Location holdouts purge shared summaries and reporting episodes; forward folds train only on earlier endpoints. Unsupported folds are retained explicitly.

Current reproducible outputs are under [final/](final/evaluation.json). Root CSV/JSON files are an earlier checkpoint, superseded by the final conditional coefficient-curvature calculation. The final version inverts the coefficient Hessian block while holding fitted residual scale fixed; the earlier checkpoint used the leading block of the full inverse.

| Held summary | Intercept lognormal NLL | Intercept exponential NLL | Partial pooling, prior 0.35 NLL |
| --- | ---: | ---: | ---: |
| Dela Paz | 2.493 | 3.134 | 3.270 |
| August 30 collective summary | 3.332 | 1.819 | Unsupported: held depths exceed fitted support |
| Maybunga | 6.503 | 3.449 | 3.660 |

Lower interval NLL is better; it is not minute error or an accuracy percentage. Of 60 model-fold combinations across summary/location/forward tests, 34 are unsupported, including baseline folds with insufficient remaining training groups. Partial pooling improves Maybunga against lognormal, worsens Dela Paz and cannot cover the collective summary. No overall or prospective improvement is established. Sparse-history testing remains open; zero-history transfer tests do not establish performance with a few local independent episodes.

The final standardized depth coefficient is approximately 0.01594, a small effect under these priors and confounded evidence. Training localities are Dela Paz, Maybunga, Santa Lucia and Santolan. No weather/terrain/drainage effects or selected future-depth trajectory model are added.

## Uncertainty and selection

The approximate predictive lognormal combines residual variance, conditional Laplace coefficient variance and unseen-location prior variance. Residual/prior-scale uncertainty, source selection and real storm dependence are not fully modelled. These p10–p90 intervals are not calibrated safety/confidence guarantees.

`selected_for_primary=false`, `deployment_eligible=false` and `changes_status_expiry_or_routing=false` are enforced. Editing a selection flag cannot turn this comparison contract into a primary forecast. No generated prediction becomes observed clearance or a training label.

Final candidate SHA-256: `b33c7583096c3aa96beb3a7db87b9305a5a331de4c6b6a02d5dff3838599e8c2`. Its separate candidate/evaluation/manifest bundle is checked by the existing asset verifier. Baseline identities remain:

- Subsidence: `eef51e6c0f5ba03efbba44272f64a71ceccef0c0574e9b575d3d084b0c9f0bc6`.
- Passability: `391eaa894717722963d38b6fd34276ef737a33e3224351433b794aa88ddf958c`.

## Verification and remaining gates

- **131 backend/model/API checks pass:** independent survival calculations, shrinkage/depth transfer, duplicate-summary weighting, censoring, artifact validation, source/clock/geometry qualification, real automatic adapter logic with transient records, proxies, capabilities and visible SQL failures. These do not prove field accuracy.
- **24 distinct desktop/mobile cases pass across runs:** eight new comparison/abstention/error/proxy cases and sixteen existing forecast/context/calculation/proxy regressions. Authentication/API responses are fixtures, not live release checks. Final new-case rerun passes all eight with content/footer reachability assertions and screenshots under ignored `frontend/test-results/cross-location-final/`.
- TypeScript, scoped ESLint and runtime asset validation pass. The asset verifier reports prediction locality 30, separate news locality 20 and cross-location model identity.
- Security review confirms capability checks, source ID/action/table/target binding, no client-controlled artifact/provider paths and visible failure states. No CORS/auth policy or dependency additions.
- SQLAlchemy models, Alembic definitions and dependency manifests are unchanged. The existing native zone suite reports **20 skipped** because no disposable test database is configured. Docker remains closed/unavailable after BUG-129, so migrations/image checks are not rerun; earlier migration acceptance is historical.
- No push/deployment or automatic retraining. Independent matched prospective outcomes, issued predictor histories, calibration, physical PWA and matching API/frontend release remain open. Decisions are not rewritten to claim model promotion; BUG-128 remains open for local accuracy.

## October 9 planner and pre-push checkpoint

At the developer's request, reconcile the eight core records and adopt [Decision 26](../../decisions.md#26-cross-location-learning-as-a-source-bound-research-comparison) for the separate cross-location research method and its source/uncertainty/selection boundaries. Preserve the recorded October 8 test results and primary baselines; do not convert publication into deployment or accuracy acceptance. [@roicambe](https://github.com/roicambe) (Roi Cambe)

Fresh pre-push inspection confirms `roi-branch` matches its remote before the new commit. Declared packages cover changed external imports; SQLAlchemy/Alembic definitions and dependency manifests have no changes. The fresh analytical asset check returns `assets_ok`; final evaluator/kernel/input/baseline hashes and documentation links/anchors match. Existing native/migration/image limitations remain documented. User-authorized staging, commit and push include the prior calculation/proxy changes and the cross-location implementation; this checkpoint does not rerun the recorded browser/model suites or deploy.

Staged research exports retain their original CRLF bytes with the repository's existing `cr-at-eol` whitespace policy. This fixes Git whitespace diagnostics without changing artifact/evaluation hashes. Sensitive-path and credential-pattern scans examine staged content before commit; no application source changes are introduced by this documentation pass.

## Reproduction commands

From `backend`, choose a **new or empty output directory**:

```powershell
.\venv\Scripts\python.exe -m scripts.evaluate_cross_location_duration --output ../docs/evaluations/cross-location-duration-new-run
.\venv\Scripts\python.exe -m pytest tests/test_cross_location_duration.py tests/test_cross_location_prediction.py tests/test_flood_duration_model.py tests/test_flood_duration_api.py tests/test_zone_submission_simulation.py tests/test_pasig_feature_evaluation.py -q
.\venv\Scripts\python.exe -m scripts.verify_news_runtime_assets
```

The evaluator does not install outputs automatically. Provisioning requires an intentional candidate/evaluation pair and regenerated manifest. It does not authorize baseline promotion or release. Git attributes preserve hashed evaluator/kernel/export bytes across Windows/Linux checkouts.
