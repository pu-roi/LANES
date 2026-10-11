# Cross-location flood prediction implementation

> **Started:** October 08, 2026 (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Implemented locally as a separate automatic research comparison; field accuracy, prospective evidence and primary model promotion remain open. [Results](../evaluations/cross-location-duration-20261008/README.md).

The developer authorizes implementing the [cross-location research](../research/cross-location-flood-prediction.md). Build a reproducible offline qualification/comparison pipeline and an automatic private comparison in existing Active Zone calculation details. Keep the selected baseline while prospective admission and independent accuracy remain unestablished.

The October 9 [Decision 26](../decisions.md#26-cross-location-learning-as-a-source-bound-research-comparison) records this method and its source/uncertainty/selection boundaries. At the October 8 research checkpoint, the developer authorized `roi-branch` publication without deployment or primary model promotion. Subsequent October 10 authorization delivered a separate operational expiry policy to the local app/shared cloud workers under [Decision 27](../decisions.md#27-experimental-pasig-ml-deadlines-as-an-operational-expiry-policy). Research API flags and scientific qualification remain unchanged; eligible shared Pasig inference retains explicit unavailable/fallback gates. See [current acceptance](../evaluations/pasig-ml-automatic-expiry-20261010.md).

## Model contract

- Implement a separate fixed-prior penalized lognormal AFT candidate using existing SciPy/NumPy. Share one standardized depth coefficient and shrink canonical barangay intercepts toward zero. Compare a pooled-depth candidate and location prior scales 0.15, 0.35 and 0.70; these are declared sensitivity settings, not empirically learned drainage similarities.
- Preserve interval/right/left/exact outcome likelihoods. Each shared summary has total likelihood weight one, recomputed in every fold. Scale depth using only training data with those weights. Repeated projections do not create additional outcome support.
- Estimate local curvature for a conditional Laplace approximation of coefficient uncertainty. Add the location prior variance for unseen locations. Combine this with fitted residual log variance for an explicitly approximate predictive lognormal distribution. Residual-scale/hyperparameter uncertainty, selection bias and real storm dependence are not fully modelled; intervals are not calibrated confidence guarantees.
- Do not constrain a positive depth effect or fit weather/drainage effects without qualified evidence. Do not add inference libraries, synthetic endpoints or SQL schema changes.

## Evidence and evaluation

Read hash-bound existing reviewed inputs. Export rejected versus conditional historical candidates with source clocks, scope/continuity/availability blockers and canonical locality. Historical production admission remains zero. Preserve all input/runtime hashes.

Hold out summary/episode dependencies together. For unseen-location testing, remove target-location rows and purge any remaining rows sharing their summaries or reporting episodes. Forward evaluation trains only on earlier outcome groups. Record unsupported folds explicitly rather than using priors to manufacture evidence support. Compare lognormal and exponential intercept baselines and both candidate types on identical held records. Save per-fold NLL, prior sensitivity, support, failed folds and selection blockers. Sparse-local-history simulation and prospective calibration remain open until sufficient independent groups exist.

## Automatic comparison contract

Use a separate authenticated Reports+Zones GET endpoint. It first calls the existing automatic zone eligibility service, then reads the exact immutable source audit chosen for the wet reference or approved registration/submission simulation. A frozen numeric-centimetre snapshot with matching source clocks and locality can produce candidate quantiles. A frozen canonical gauge conversion can exercise a separately labelled proxy-depth simulation; it is never called a numeric measurement or training label. Current depth, later environment fetches and news without a supported frozen snapshot must abstain explicitly.

Retain unknown observation time for proxy simulations and label them. Multi-barangay footprints abstain for local effects because the supplied depth does not establish an appropriate whole-footprint input. A stale, inactive or needs-review case cannot receive a candidate. Missing/invalid artifacts expose a reason; never break or replace the baseline. An error in the database must propagate through normal API error handling.

Return support counts, trained locations, source/reference identity, fitted depth/local contributions, approximate uncertainty basis, candidate checksum, actual validation blockers and separate comparison quantiles. `selected_for_primary=false` and `changes_status_expiry_or_routing=false` are fixed for this research contract. Render the result lazily in existing details, with visible loading/error/retry/abstention states on both desktop and mobile.

## Acceptance

- Mathematical tests: shrinkage, shared-depth effects, duplicate-weight invariance, unseen-location uncertainty, censoring and conditional survival calculations, invalid input/artifact rejection.
- Evidence/evaluator tests: exclusions, checksum rejection, canonical identities, no summary/episode leakage, failed/unsupported folds and zero automatic promotion.
- Private API tests: capabilities, source/clock/scope qualification, research simulation labels, stable refresh and untouched operational fields.
- Responsive browser tests: candidate versus baseline separation, no manual inputs, proxy/abstention/error/retry states and readable layouts.
- Preserve pre-existing changes and runtime baselines; document actual results and remaining prospective/deployment gates. No SQLAlchemy/schema/migration changes or push/deployment are part of this implementation.
