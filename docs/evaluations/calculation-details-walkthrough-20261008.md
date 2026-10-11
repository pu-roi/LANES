# Calculation details walkthrough — October 8

> **Last Updated:** October 08, 2026, 09:23 PM (Asia/Manila)

**Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

The developer requests a friendlier explanation of how the prediction is calculated, including the formula. This refinement stays inside the existing Active Zone Info → Overview → View calculation details disclosure. It adds no prediction inputs, public-bubble content, new tab/page or Moderation Center sections.

The walkthrough explains three steps: select the first qualified observation or explicitly labeled registration proxy, apply the selected duration distribution, and add remaining duration to the stable forecast anchor. Existing source records, coordinates, cohort and checksum remain under Source records and model information; current environmental background retains its visible source/error/retry behavior and explicit exclusion from the selected baseline.

The backend returns optional `lognormal_aft_calculation_v1` metadata from the current kernel result. It supplies full-precision μ/σ, elapsed minutes a, conditional probability and normal score, total/remaining minutes and the same forecast timestamps already displayed above. React only formats numbers/timestamps. Older API responses lacking this metadata remain usable and explicitly say the steps are unavailable.

The displayed formula is `ln(T) = μ + σZ`, where T is total duration in minutes. When elapsed age is positive, the conditional percentile is `p = F(a) + q(1 − F(a))`, with `Z = Φ⁻¹(p)` and `T = exp(μ + σZ)`. Remaining duration is `T − a`; the forecast is the original issuance anchor plus remaining duration. At age zero, F(a) is zero and the median score is zero. Rounded display values are identified; no current-screen time is substituted for the anchor.

The original artifact remains μ=6.964058396239009 and σ=0.4606544869441319. This is an intercept-only lognormal AFT baseline, not a newly fitted depth/rainfall/street model. The 10th/90th percentiles describe the middle 80% of the assumed distribution, not demonstrated 80% forecast accuracy. Unknown physical observation time and registration-proxy meaning remain explicit.

## Verification checkpoint

Twenty model-preview/API checks pass, including zero/60/1100-minute conditional ages, independent normal-CDF quantile checks, exact agreement with forecast outputs and unchanged results when the view is refreshed later. TypeScript and scoped ESLint pass. The responsive matrix records 41 passes and one initial mobile navigation timeout before the prediction panel opened; that exact case passes in a targeted rerun. All 42 distinct workflows therefore pass across runs. The final four formula/visual cases also pass after disclosure-marker and rounded-arithmetic refinements, covering both registration-proxy and six-hour elapsed observation examples on desktop/mobile. Do not add repeated cases to the distinct count.

Model fixtures are generated from the unchanged selected backend artifact, not invented duration constants. They verify presentation with mocked authenticated source responses, not a live Zone #17 forecast or prospective accuracy. Screenshot pairs in ignored `frontend/test-results/calculation-final/` show the calculation steps and result separately; the first tall-element captures were clipped by the dialog and replaced by viewport previews. Final previews are visually checked for both screen sizes.

Native spatial/API assertions could not be rerun because Docker remains unavailable; the pending guard recheck is separate from completed model/API-unit and UI acceptance. No model artifact, mathematical kernel, SQLAlchemy model, dependency manifest or migration definition changes; no operational status/expiry/routing write, commit, push or deployment is performed. A matching API/frontend release is still required for these new calculation details to appear on the cloud site.

## Local Docker interruption

Docker was initially stopped. Starting it for disposable PostGIS verification exposed the user's reported sailor-ingest.sock error, matching [Docker's Windows stale-socket report](https://github.com/docker/desktop-feedback/issues/554). After confirming Desktop/backend processes were stopped and validating absolute targets, only the two runtime socket parent directories were renamed to sibling backup folders and recreated; no VM disk, container volume or source data was deleted. The directories are preserved under LocalAppData as `Docker/run.lanes-backup-20261008-a709e6ea` and `docker-secrets-engine.lanes-backup-20261008-aa73bc28`.

Startup proceeded beyond the socket failure, then exposed a WSL disk-mount timeout. A controlled Desktop force-stop and `wsl --terminate docker-desktop` completed, but the next startup reproduced the same socket error. Docker was force-stopped successfully and left closed; the preserved runtime directories remain available. A Windows restart before another launch is the next user-controlled diagnostic step, not a verified repair. Native disposable-PostGIS checks cannot be rerun on this host at this checkpoint. Factory reset, WSL unregister, VM-disk deletion and broad filesystem cleanup were not performed. [Official troubleshooting](https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/).
