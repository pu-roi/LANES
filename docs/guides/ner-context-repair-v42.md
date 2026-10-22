# V42 context repair operator and evidence guide

> **Last Updated:** October 20, 2026, 12:05 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The [subsequent recognition assessment](../evaluations/flood-ner-recognition-gaps-20261020/README.md) accounts for all 19 unresolved rows: 17 missing target occurrences, three boundary errors and one incompatible type. It changes no extraction behavior; v42 remains the backend context version.

V42 passed its one frozen comparison and is the local backend's context version. [Outcome](../evaluations/flood-ner-context-repair-v42-20261019/README.md) · [Acceptance design](../plans/ner-context-repair-v42.md) · [Backend setup](ner-backend-preview.md). The ordinary preview flag remains false; there is no frontend, database-history or plotting change.

## Meaning and limits

The model and v40 proposals are unchanged. The context successor preserves complete junctions when numeric/verbal descriptions describe their measurement, recognizes dotted clocks, retains supported list observation/access/caution context and excludes unsupported datelines. It never infers onset from a report, observation or publication clock, never creates an absolute timestamp, and preserves subsided/cleared evidence.

Missing, incomplete or mistyped location mentions remain unchanged and unresolved. In the reviewed article, five complete junction rows and three complete single-target rows pass the declared checks; 18 measured rows still lack supported complete locations. An additional unmeasured junction remains unresolved. A higher unassigned count can reflect removal of unsafe links and additional retained evidence; it is not a recovery count. Three held references, the separate non-flood access omission, unmeasured real pure-Tagalog performance and learned DEPTH/TIME remain open.

The backend identifies the context implementation as `lanes-context-association-v42`. Worker, projection and host validator use this version; stale v41 provenance is rejected. The response contract and `source.canonical_url` are retained. Original v41 files and predecessor consumer/test snapshots remain available.

## Saved artifacts and reproduction

Private paths below are under `backend/training/flood_ner/artifacts/` and ignored by Git:

- `context-repair-authoring-20261019-v42`: predecessor application/test snapshots and their hashes.
- `context-repair-prepared-20261019-v42`: frozen raw request, fixtures, article expectations, source bindings and `analysis-v1` dispositions.
- `context-repair-execution-20261019-v42`: exact Docker receipts, isolated outputs, completed stopped state and output hashes.
- `context-repair-verification-20261019-v42`: independent verification, all-59-fact preservation, cached response-contract check and promotion source hashes.

Freeze SHA-256 is `0173994e0e6851ec3896f47138d45387d3dae2d732072b9a940374d8b9b58009`. The worker processed 371 raw rows/1,419 graphs using cached locations, without neural inference, proposal regeneration or database access. Expected answers/references remain outside worker mounts.

Use the backend Python with `PYTHONPATH=backend` from the repository root. `python -B -m training.flood_ner.context_study_v42 check --package backend/training/flood_ner/artifacts/context-repair-prepared-20261019-v42` authenticates the frozen code/input bindings without running extraction. `backend/scripts/verify_context_v42.py --help` describes independent saved-output verification; provide the recorded SHA and an absent private output directory. Scoring can be repeated over saved outputs in a fresh analysis directory; it does not rerun extraction.

Do not rerun `execute` or reuse an attempt after a failure. The execution claim prevents another attempt under the same freeze. Preserve receipts and separately define any future repair/comparison; no post-result tuning is part of this outcome.

The 1,195 post-promotion checks comprise the preserved preview/v40/v41 checks, the v42 fictional/control tests and the new worker/provenance wiring tests. Run the three `test_news_ner_preview*.py` modules, `test_news_ner_context_v42_wiring.py`, `test_context_association_v42.py`, `test_context_association_v41.py` and `test_location_repair_v40.py` with `pytest --noconftest -p no:cacheprovider`. These tests avoid shared database fixtures and application startup jobs. Constructed Tagalog checks do not measure real pure-Tagalog performance.

Current promotion was checked against cached predictions and saved candidate context output. No new end-to-end neural worker or database execution was performed after promotion. Previously recorded neural runtime timings remain predecessor evidence, not fresh v42 performance measurements.
