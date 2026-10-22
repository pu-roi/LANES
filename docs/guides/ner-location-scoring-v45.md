# V45 scoring-only evidence guide

> **Last Updated:** October 20, 2026, 12:40 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

V45 reassesses saved v44 results without extraction or inference. [Outcome](../evaluations/flood-ner-location-scoring-v45-20261020/README.md) · [Metrics](../evaluations/flood-ner-location-scoring-v45-20261020/metrics.json) · [Verification](../evaluations/flood-ner-location-scoring-v45-20261020/verification.json) · [Plan](../plans/ner-location-scoring-v45.md).

## Contracts and interpretation

`location_scoring_v45.py` validates span representations, immutable neural/control mentions and three source-authored repaired-view expectations. `location_reassessment_v45.py` scores the saved workload; `location_reanalysis_v45.py` freezes/binds evidence and installs execution guards. These modules live under `backend/training/flood_ner/`. The independent verifier is `backend/scripts/verify_location_v45.py`.

The scorer does not repair locations. It reads already saved original/control/effective views. Representation normalization never changes offsets, labels or expected meaning. Original fixture expectations stay valid for their declared control views; enabled repair families have additional expectations for full road names and collective source measurements. Disabled families retain the original expectation. Original neural predictions must remain exactly equal as JSON objects, independently of effective-view changes.

All 418 applicable candidate checks and three conditional paired checks pass per method. Control checks consist of 382 preserved fixture expectations and 36 new original-view integrity checks. Missing-junction, boundary-replacement and combined views qualify for a later proposal; type correction lacks a real source-supported correction and remains unqualified. V45 supersedes scoring interpretation only. Never overwrite v44's frozen code, metrics, failed expectations or blocked report.

## Private evidence and authentication

Ignored directories under `backend/training/flood_ner/artifacts/`:

- `location-scoring-authoring-20261020-v45`: the 176-test scoring-only receipt bound to final code.
- `location-scoring-prepared-20261020-v45`: three source-authored repaired expectations, workload, acceptance, preservation and frozen bindings to historical evidence.
- `location-scoring-analysis-20261020-v45`: control/candidate checks, per-target and per-fact dispositions, execution guard receipt and independent verification. Individual source text and evidence stay private.

Freeze SHA-256: `beace0fd7d5cf84e39cec71f23e4abfe8e8e2020f4bb1020294160725b915a9b`. All 788 saved inputs, 34 article target occurrences, 19 affected rows, 93 facts and seven historical misses are reconciled per method. The article findings remain eight corrected occurrences / 40 restored facts / 11 unresolved rows for the combined view.

Use `location_reanalysis_v45`'s `check` action to authenticate frozen files without scoring or extraction. The independent verifier reads saved analysis and writes only fresh receipts; use fresh receipt destinations and retain previous evidence. Do not call the v44 worker or regenerate location proposals. The scoring claim permits no automatic repeat, and execution guards reject recognition/extraction calls, neural/database imports, process starts and networking.

## Application boundary

No public API, output contract, schema, frontend, database or backend wiring changed. The backend remains v42 and the preview flag stays disabled. Qualifying views require a separately scoped implementation proposal. Type-family uncertainty, existing strict recognition errors, three holds, non-flood access and language/training limits remain documented. This exposed saved-evidence reassessment establishes no unseen-article accuracy.
