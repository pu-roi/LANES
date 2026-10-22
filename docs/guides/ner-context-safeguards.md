# Offline training-only context safeguards

> **Last Updated:** October 19, 2026, 12:02 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Latest completed task:** the separate [training-only boundary study](../evaluations/flood-ner-road-boundaries-20261019/README.md) produced zero corrective actions and no qualifying rules. V19 control remains retained; no additional validation comparison, integration or retraining follows. See the [boundary operator guide](ner-road-boundary-study.md). The earlier dated instructions/results below remain historical and unchanged in their frozen packages.


**Latest completed task:** the separately authorized [frozen validation comparison](../evaluations/flood-ner-context-validation-20261019/README.md) scores 76.54% shadow F1 versus 71.60% control, but fails its zero-new-strict-FP gate. V19 control remains retained and the prototype remains unintegrated. See the [validation operator guide](ner-context-safeguard-validation.md); do not rerun the consumed comparison or tune rules from these findings. The instructions and next-step wording below describe their earlier dated scope.


The [completed study](../evaluations/flood-ner-context-safeguards-20261019/README.md) supports proposing a later validation comparison of frozen `named_asset` and `shared_identifier` rules. **This guide does not authorize validation evaluation, training or application integration.** Keep v19 corrected control seed 0 retained; the completed holdout stays excluded.

## Interfaces and separation

- `context_safeguards.py`: pure text-only `propose(opaque_id, text, predictions, enabled=...)`, or strict `raw_record` accepting exactly those three fields. It cannot accept references, expected labels, language or source identities. It proposes keep/drop/retag from original spans without cascading, additions or resized boundaries.
- `context_safeguard_cases.py`: 48 fictional design cases with explicit occurrence offsets. Twelve ambiguous cases have null references and cannot be scored as negatives.
- `context_safeguard_study.py prepare`: coordinator-only deterministic filtering of authenticated qualified development files and saved seed-0 predictions. It emits only 345 training rows, with references separate. Parent development files contain validation records; they are authenticated by the coordinator, not supplied to the decision function or study worker.
- `context_safeguard_study.py study`: verifies the frozen training-only view, sources/tests and 48 fixtures, then scores frozen individual rules, combined rules and the qualifying subset against separate training references. It never reopens parent development files or loads a model. Both CLI operations install guards against neural imports, network and child processes.

The private preparation grant binds the development status, prediction/metric files, training grounding, conventions, seven implementation files and the new test file. Paths are explicit and repository-relative; private outputs must be new direct children of `backend/training/flood_ner/artifacts/`. Existing destinations, changed bindings and competing writers are rejected. Saved inputs are never updated in place.

## Reproduction

Use the existing backend interpreter; no installation or GPU is required. Commands below are structural examples using locally authenticated private paths/hashes. Do not reuse an occupied destination or regenerate an authorization to bypass a mismatch.

```powershell
& .\backend\.venv\Scripts\python.exe -B .\backend\training\flood_ner\context_safeguard_study.py prepare --checkout (Get-Location).Path --input <private-grant.json> --input-sha256 <grant-sha256> --output <new-private-training-view>
& .\backend\.venv\Scripts\python.exe -B .\backend\training\flood_ner\context_safeguard_study.py study --checkout (Get-Location).Path --input <verified-training-view> --input-sha256 <view-manifest-sha256> --output <new-private-study-output>
```

The completed local version is `context-safeguard-coordination-20261019-v23`, `context-safeguard-training-view-20261019-v23`, `context-safeguard-study-20261019-v23` and its separate `-replay`. A Git pull does not transfer these ignored packages. No private delivery is required or performed for this laptop study.

## Frozen interpretation

A rule requires passing constructed checks, observed corrective training actions and zero introduced strict training FP/FN before it can enter a later validation proposal. No-firing or already-correct-only rules remain unproven. The joint subset must pass the same no-harm guard. Training agreement never establishes generalization.

This study was motivated by exposed validation findings, so it is not blinded. Two road-suffix retags and one shared-identifier retag improve training F1 from 98.09% to 98.45%; the 342 remaining passages stay unchanged. Organization/role removal, direct designator corrections and physical-facility retagging have no observed corrective training applicability. Do not describe the shadow results as a model improvement or production acceptance.

Failures preserve inputs and any exclusive output evidence. Investigate a stale hash, failed fixture, missing reference or malformed span; do not weaken checks, change boundaries, infer geography or change expected labels to pass. A substantive repair requires a separate preserved version and qualification. No article-specific exceptions or proper-name allowlists are permitted.

Actual next work, if separately authorized, is a frozen **validation-only** comparison of the qualifying subset. No retraining is needed for that comparison; use saved predictions. Never reopen the completed holdout for tuning. Data, annotations, source-use scope, model selection, production APIs and dependencies remain unchanged.
