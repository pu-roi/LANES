# Frozen context-safeguard validation operator guide

> **Last Updated:** October 19, 2026, 12:02 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Latest completed task:** the separate [training-only boundary study](../evaluations/flood-ner-road-boundaries-20261019/README.md) produced zero corrective actions and no qualifying rules. V19 control remains retained; no additional validation comparison, integration or retraining follows. See the [boundary operator guide](ner-road-boundary-study.md). The earlier dated instructions/results below remain historical and unchanged in their frozen packages.


**Completed:** the joint shadow method scores 76.54% versus control 71.60% validation F1, but fails the frozen zero-new-strict-FP requirement. V19 corrected control seed 0 remains retained. Read the [evaluation report](../evaluations/flood-ner-context-validation-20261019/README.md) before interpreting the result. No integration, retraining or further rule tuning is authorized.

## Scope and interfaces

The standalone `backend/training/flood_ner/context_safeguard_validation.py` reuses the frozen text rules and strict scorer without changing the training-study helpers, neural models, frozen rules baseline or production extraction. It runs saved-span arithmetic in the existing Python 3.12 backend environment; no installation or GPU is required.

- `prepare`: authenticate the grant, unchanged training-study result, implementation/tests and constructed-check evidence; filter the qualified parent containers into exactly 60 validation records. Non-validation records and other seeds are not emitted. Validate complete silver references, source text, Unicode offsets, language, polarity and non-fitted group separation. Keep references out of the raw decision envelope.
- `evaluate`: require the exact frozen subset (`named_asset`, `shared_identifier`), protocol and validation-only view; check the 48 fictional cases, then consume a persistent attempt claim. Reproduce the saved baseline before applying the one joint rule combination. It never reopens the parent development containers or loads a neural model.

Both CLI operations block neural-library imports, network transport and child/training processes. Source files and scoped views are hash-checked; missing references cannot become negatives. The decision function receives only unchanged text, an opaque ID and original spans. Only keep/drop/retag actions are permitted; no additions, boundary repair or cascading edits are allowed.

## Frozen acceptance policy

Qualification for a later integration proposal required all five conditions: overall strict micro F1 improvement beyond 1e-12, zero introduced strict FP, zero introduced strict FN, no supported class/language F1 decline beyond tolerance, and no increase in negative-passage errors. A tie fails the improvement requirement. Unsupported slices remain unmeasured.

The live result fails the strict FP transition condition. One already-truncated road span changes type but stays incomplete; it remains an error, with a new typed FP identity. Total FP decreases and no previously correct entity is lost, but the prospective criterion remains unchanged. Do not reinterpret this as a new textual entity, a destructive dataset change or a trained-model regression. Do not retry with a different subset, resize that span, revise the reference or change the gate to pass this result.

## Private packages and attempts

The ignored `artifacts/` directories are `context-safeguard-validation-coordination-20261019-v24`, `context-safeguard-validation-view-20261019-v24` and `context-safeguard-validation-20261019-v24`. Coordination contains frozen source/test bytes, protocol/grant, source-bound reviews and preservation evidence. The view contains four scoped input files plus its manifest. The output contains metrics, all sixty private record decisions, an aggregate summary and its manifest.

The consumed claim lives under `artifacts/context-validation-attempts/`. It binds the training-study identity, parent prediction hash, partition hash and frozen protocol, so a different output destination does not permit a second evaluation. Never delete/refund the claim or overwrite an output to rerun the comparison. Existing destinations, competing writers, changed members, stale bindings and incompatible capabilities stop execution. A failure after claim consumption saves failure evidence and stops without retry.

The following describes the completed operation, **not instructions to launch it again**:

```text
context_safeguard_validation.py prepare --checkout <checkout> --input <authenticated-grant> --input-sha256 <grant-hash> --output <new-scoped-view>
context_safeguard_validation.py evaluate --checkout <checkout> --input <verified-view> --input-sha256 <view-manifest-hash> --output <new-result-directory>
```

A Git pull does not transfer these private packages. No upload or publication occurred. The completed holdout remains outside all tuning and comparison inputs. The prior unresolved validation boundary and every annotation remain unchanged. This task ends with reporting and unchanged control retention; any future experiment or integration work needs its own explicit scope.
