# Separate Pasig light-vehicle-passability duration experiment

> **Date:** October 8, 2026 (Asia/Manila)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Conditional experimental fit and authenticated backend preview verified locally. No prospective/location-specific accuracy or operational expiry/routing adoption.

The developer clarified that a flooded-to-passable transition is useful for forecasting even without an exact depth or fully dry road. This experiment uses those observations for their actual target, **reported light-vehicle passability**, without relabeling them as observed subsidence or filling missing dry times with model estimates.

The existing lognormal AFT mathematical kernel now accepts a separate passability target. It fits nine conditional road projections, weighted equally over two shared outcome summaries. The training cohort is **Dela Paz, Manggahan, Pinagbuhatan, Rosario, San Miguel, San Nicolas and Ugong**. The eight October 25 collective road projections share one recovery summary; the September 3 Infant Jesus/Manggahan projection has the other. These are not nine independent measured recoveries or seven separately trained locality models.

## Data and time interpretation

Inputs remain the independently reviewed October 7 overlay and content-addressed captures. The new derived [conditional candidates](conditional_passability_candidates.csv) select earlier nonpassable snapshots only within the same source episode, barangay and conservative road key. Road directions, sections, extensions and ambiguous names are not guessed. Review/admission flags and source/capture identity remain visible. The derivation explicitly assumes uninterrupted nonpassability between snapshots; chronology alone does not verify no temporary recovery/reflooding.

For Ugong's Eagles Street corner E. Rodriguez Avenue:

- First recorded nonpassable: October 24, 2024, 9:15 PM PHT.
- Last supported nonpassable: October 25, 1:00 AM.
- Reported collective passability upper bound: October 25, 2:30 AM.
- Conditional elapsed bracket from the first snapshot: `(225,315]` minutes.
- Conditional remaining bracket after the last snapshot: `(0,90]` minutes. It is not an exact 90-minute flood duration or a measured dry time.

The direct September 3 Manggahan source reports light-vehicle passability while water is still present. This demonstrates why passability and dry/subsided labels are distinct. Vehicle wording supplies no unique water depth; LANES's current depth policy permits light vehicles at green/low and blocks yellow/medium and above, but the inverse inference from access wording to centimetres/color is not valid.

## Fit and limits

The pooled model's unconditional median is approximately **280.71 minutes** from first recorded nonpassability; p10/p90 are approximately **112.34/701.42 minutes**. These are model-distribution outputs, not calibrated confidence or an operational clearance time. Predictions conditioned on a supported elapsed nonpassable age use the conditional survival distribution.

One leave-one-summary-out fit is unidentifiable (one remaining contribution cannot identify both parameters). The other fold fits with mean interval NLL about 3.268. Two summary groups and uncertain historical source availability cannot establish geographic transfer or prospective accuracy. The model learns no depth/rainfall/locality effects. Production admission and deployment eligibility remain false.

`prediction_barangays` exposes 30 canonical Pasig identities for **explicitly enabled pooled experimental transfer**; `supported_barangays` retains the actual seven training identities. Unknown/non-Pasig locations, missing model, absent research/continuity assumptions, future issuance and unsupported age abstain. A location outside the cohort needs allow_pooled_pasig_transfer and returns pooled_geographic_transfer=true. The original subsidence model retains its four actual cohort identities and parameters, while its preview now supports the same explicit research-transfer policy. Neither means 30 independently learned locations.

## Runtime/API and reproduction

- [Artifact](passability_aft.json); matching runtime file: backend/runtime_data/flood-duration/passability_aft.json.
- [Experiment report](experiment_report.json) includes source input hashes, actual fit, grouped sensitivity, geographic policy and no observed-label imputation.
- Staff Reports read capability: GET `/api/v1/admin/news/passability-model`, POST `/api/v1/admin/news/passability-preview`.
- Preview requires timezone-aware reference/issuance clocks, explicit research and continuous-nonpassability assumptions; returns estimated_reported_passability_at, not estimated_reported_subsidence_at.
- No public estimate, route permission/color change or automatic expiry/clearance write. Subsidence remains the main existing Overview output; its official registration simulation is separate from physical observation evidence.

From backend:

```powershell
python -m scripts.train_pasig_passability
```

The builder verifies captured/export hashes and does not fetch sources, access the database, rewrite existing evidence or overwrite the original subsidence artifact. New derived candidate rows explicitly mark experimental_fit_included=true, production_training_admitted=false and subsidence_label_admitted=false. Keep predicted missing outcomes in simulation outputs, not ground-truth training labels.

**Verification:** 127 focused native/model/API checks pass, including source-bound Ugong bounds, target separation, unchanged original artifact, finite fits, held-out nonidentifiability, bad/missing artifacts, permission/no-store/error contracts, canonical geography and explicit transfer. TypeScript/scoped lint and 34 responsive workflows pass for existing Overview transfer/simulation behavior. Live authenticated desktop/mobile GET confirms Ugong's training identity and 30 transfer identities. [Full interface/backend acceptance](../case-linked-ml-review-assistant-20261008.md#october-8-pooled-research-transfer-transport-target-and-automatic-registration-simulation).

No package/SQL model/migration/deployment/commit/push is introduced. Source-group calibration, prospective matched outcomes, additional independent storms and operational forecast-to-Unconfirmed/public retention remain open.
