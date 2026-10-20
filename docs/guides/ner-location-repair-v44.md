# V44 offline location study evidence guide

> **Last Updated:** October 20, 2026, 12:22 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

V44 completed one frozen attempt and remains **blocked**. It is not connected to the backend. [Outcome](../evaluations/flood-ner-location-repair-v44-20261020/README.md) · [Plan](../plans/ner-location-repair-v44.md) · [Verification](../evaluations/flood-ner-location-repair-v44-20261020/verification.json).

## Implementation and interpretation

The separate prototype, fictional cases, worker, study controller and reference-side scorer live under `backend/training/flood_ner/` with `_v44` names. The independent saved-output verifier is `backend/scripts/verify_location_v44.py`. No application file or dependency was changed. Keep v40 and v42 frozen.

Inputs consist of exact text, saved neural mentions and saved combined-control mentions. Output separates immutable neural/control mentions from effective mentions and explicit `add`, `replace` or `retag` proposals. Replacement preserves the original ID in the effective view while recording the changed span/type and provenance. Added locations have rule IDs. Evidence and offsets always refer to the unchanged source. Neither operation changes a trained prediction.

The frozen new-case scorer has a known JSON list/tuple comparison defect. Its published raw fixture counts must not be interpreted as extraction accuracy. The separate diagnostic confirms representation-normalized expected spans from saved outputs, without replacing the official frozen score. Three older incomplete-target fixture conflicts remain independently blocking, and the type family has no real correction evidence. Do not promote a family based on the diagnostic.

## Private evidence

The following ignored directories are under `backend/training/flood_ner/artifacts/`:

- `location-repair-authoring-20261020-v44`: 560-check receipt bound to the frozen code.
- `location-repair-prepared-20261020-v44`: raw request, new fictional expectations, acceptance, preservation and freeze manifest.
- `location-repair-execution-20261020-v44`: single-attempt claim, isolation receipts and saved worker outputs. The claim itself is beside the packages under artifacts.
- `location-repair-analysis-20261020-v44`: frozen metrics/details, source outcome ledger, independent verification, scorer diagnostic and original/control counts.

Freeze SHA-256: `4a5e38d5e9c6de4adf9d8d231d6a0de6a53f194fe48bd282c6c1d9b0747cdafd`. Each method accounts for 34 target occurrences, 19 article rows, 93 affected facts and seven historical misses. Source text, identities and individual evidence remain private.

## Read-only review

Use the study controller's `check` action to authenticate the package; it performs no extraction. Use the independent verifier against the saved execution/analysis packages and a fresh receipt path. Verification reads saved outputs and does not rerun the worker. Preserve existing receipts and occupied destinations. The study claim refuses a second execution; changing destination does not authorize a retry.

Future work must first qualify serialized scoring and specify how preserved original-control expectations coexist with additional repaired-view expectations. No current fixture, reference or score should be rewritten to accommodate v44. Observation versus onset and subsided-history requirements remain unchanged; interface and map work remain separate.
