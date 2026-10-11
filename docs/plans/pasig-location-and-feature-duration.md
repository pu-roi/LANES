# Pasig automatic location and feature-based flood modelling

> **Started:** October 08, 2026, 01:25 PM (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Location coverage completed; feature input capture/evaluation implemented, candidates unselected on worse/failed holdouts. Independent street-specific model improvement remains open. No deployment, SQL schema or public-map change.

The developer asks to complete automatic location coverage across all 30 Pasig barangays and investigate useful location/condition effects beyond the shared intercept-only duration pattern. Retain existing Overview, no manual prediction inputs, source clocks and experimental qualifiers. Do not invent dry labels, measured drainage capacity or street coordinates.

## Location implementation

Acquire the source-backed OCHA/HDX Philippines COD-AB Pasig subset, retaining publisher/licence, original source records, CRC/transfer/capture hashes and exact PSGC parent/code/name crosswalks. Validate 30 complete unsimplified polygons against the source-consistent Pasig city polygon. Use a distinct flood-location catalog for prediction location resolution so the existing OSM/NOAH news activation/catalog gates are preserved. Do not silently clip/repair polygons or make the older OSM parent geometry certify a different source. Border/multi-barangay ambiguity and outside-city geometry remain explicit.

## Model investigation

1. Compare feature-aware lognormal AFT candidates against the current grouped subsidence baseline using first recorded depth and other genuinely available qualified features. Leave whole shared outcome summaries out; no random row split, synthetic dry labels or hidden precision from vehicle wording.
2. Evaluate a separate depth-trajectory model from adjacent exact numeric snapshots in matching candidate location/episode timelines. Predict depth change rather than labelling a future observed dry event. Preserve repeated/static/rising evidence; prior investigation identifies 251 pairs but only 13 falling transitions across three reporting episodes. Evaluate held-out episode performance before runtime selection; a trend-to-zero simulation would require separately disclosed extrapolation/continuity assumptions.
3. Build explicit context/provenance for location, depth, terrain and modelled rainfall. Open-Meteo historical reanalysis/90 m DEM can supply environmental context but cannot represent measured street drainage, guarantee street-scale rain, or establish historical pre-issuance availability. OSM mapped drains/river distances are map context, not hydraulic capacity. Missing features remain unknown.
4. Promote only evidence-supported experimental outputs, with clear feature-cohort/transfer status and a fallback if required inputs are unavailable. Poor held-group performance or unidentifiability must be recorded rather than bypassed to make every location appear learned.

## Verification and completion boundaries

Native tests should cover every barangay, a street absent from training data, outside-city and crossing boundaries, checksum/identity/invalid geometry, and unchanged operational state. Model checks should cover source/group/clock/feature leakage, held-out groups, finite outputs, missing/unsupported inputs, actual feature sensitivity and preservation of original observed labels. Compare useful baselines and report numerical versus prospective accuracy separately. If UI display contracts change, check both desktop/mobile and preserve the bubble/status and Moderation scope.

Source research: [HDX source dataset](https://data.humdata.org/dataset/cod-ab-phl), [NAMRIA Geoportal](https://geoportal.gov.ph/), [XGBoost AFT censoring/feature support](https://xgboost.readthedocs.io/en/stable/tutorials/aft_survival_analysis.html), [Open-Meteo historical weather](https://open-meteo.com/en/docs/historical-weather-api), [archived forecasts](https://open-meteo.com/en/docs/historical-forecast-api). XGBoost is a candidate architecture, not a new dependency/adopted algorithm. Use the existing SciPy/scikit-learn stack where sufficient.

This work does not implement the separate forecast-to-Unconfirmed/public retention/routing task or grant operational model adoption. Update task plan/progress/evaluations with what actually passes and any evidence constraints.

## Delivery checkpoint

**October 9 cross-location modelling record:** [Decision 26](../decisions.md#26-cross-location-learning-as-a-source-bound-research-comparison) and the [implemented comparison](../evaluations/cross-location-duration-20261008/README.md) extend this investigation with fixed-prior shared-depth/location AFT, purged holdouts and automatic source-bound research details. Primary model replacement remains open because three summaries and mixed/unsupported holdouts do not establish reliable improvement. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Approved-citizen/multiple-barangay continuation:** Full footprints verified inside the Pasig parent can use the shared baseline while retaining every detected name; outside-city extents still abstain. Untimed, unchanged, staff-approved citizen cases can supply a separately labeled submission/approval-audit simulation without fabricating onset time. Actual observed evidence remains preferred; version, geometry, event, chronology and later-evidence guards apply. Real Zone #18 verifies this adapter path; it does not improve learned street-specific accuracy or implement operational expiry. Per-zone evidence clocks are separate from the future location/depth/weather parameter-learning gate. [Acceptance](../evaluations/zone18-submission-simulation-20261008.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

[Actual source/implementation/evaluation](../evaluations/pasig-location-feature-models-20261008/README.md) records complete 30-barangay COD coverage, immutable input snapshots, cached-or-missing write context, bounded current provider inspection, depth AFT and trajectory Ridge comparisons, 256 comprehensive backend checks, 38 responsive workflows and live Zone #17 calls. The shared baselines remain active because the tested feature candidates are worse/unidentifiable; obtain more independent matched wet/subsided episodes and available feature histories before claiming the second limit solved.

## Selected acquisition path

The developer selects future LANES reports and independent admin reviews. Collection hooks now preserve source features in citizen records, official create/edit audits, public condition updates and owner follow-ups. A bounded private model-evidence export separates unknown clocks, spot/road scope, independent reviews and qualification blockers. Existing follow-up export includes frozen numeric-depth inputs. This collection path is implemented without new user fields, automatic label admission, historical backfill or self-training. Independent real episodes still need to accumulate before the feature candidates can improve on the active baselines.
