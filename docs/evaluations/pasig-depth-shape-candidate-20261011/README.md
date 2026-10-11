# Conditional depth-shape experiment — October 11, 2026

**Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe). **Result:** no demonstrated accuracy improvement; no runtime artifact replaced.

The existing interval-censored, regularized cross-location AFT fitter now accepts an optional `nondecreasing` depth-shape assumption. It constrains the shared coefficient to be nonnegative while fitting the historical likelihood. This applies to the log-duration centre with other inputs fixed. It does not force arbitrary shallow-flood timers or make predictive upper quantiles monotonic: coefficient/location uncertainty still affects their spread. Unsupported curvature causes abstention. The deployed fitter's default remains unconstrained; this experiment does not retrain production automatically.

The evaluator verifies retained source/input checksums, shares each outcome summary's total weight across its projections, and purges overlapping summaries/episodes for held-out summary, location and forward-time folds. It compares lognormal/exponential pooled baselines, four location-prior sensitivities and the constrained candidate. Captured historical predictor availability and independent storms remain unverified. All outputs remain conditional research, with zero production-training admission.

| Full-cohort property | Result |
| --- | --- |
| Eligible projections / shared outcome summaries | 36 / 3 |
| Unconstrained standardized depth coefficient | 0.0159360643 |
| Nondecreasing candidate coefficient | 0.0159360182 |
| Constrained gutter-to-knee central duration ratio | 1.01496191 |
| Depth constraint active | No |
| All model/fold attempts supported / unsupported | 29 / 41 |
| Constrained candidate supported / unsupported folds | 3 / 7 |
| Constrained forward-time folds supported | 0 / 3 |

The positive original coefficient already satisfies this shape assumption. Constraining it leaves the central shallow/deep difference almost unchanged at about 1.5%. The candidate can score only two summary folds and one location fold; other folds lack enough groups or require unsupported depth extrapolation. There is no defensible basis to claim improved field accuracy, shorten shallow-zone deadlines, or select it for production. Synthetic mathematical tests demonstrate transfer/shape behavior and reject unsupported curvature; they do not supply field evidence.

See [evaluation.json](evaluation.json) for per-fold likelihoods, failure reasons, source/kernel/evaluator checksums and explicit deployment blockers. [qualification.csv](qualification.csv) preserves conditional eligibility; [conditional_candidates.csv](conditional_candidates.csv) preserves the fitted rows. Candidate JSON files are offline results, separate from `backend/runtime_data/flood-duration`.

Reproduce from `backend/` with `venv/Scripts/python.exe -m scripts.evaluate_cross_location_duration --output <new-empty-directory>`. Recorded evaluations cannot be overwritten. Use reviewed, timed observations from the same road section and episode for the next dataset; staff approvals, test reports and automatic expiry are not observed-clearance labels. [Research and next steps](../../research/pasig-flood-recession-depth-and-availability-20261011.md).
