# V40 location-repair study operator guide

> **Last Updated:** October 19, 2026, 10:01 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Study complete; complete acceptance blocked.** Transport proposals recover four prior strict links; shared locality introduces one scope error. Unchanged v38 fails seven of 36 temporal cases. [Outcome and next task](../evaluations/flood-ner-location-repair-20261019/README.md).

## Components and private evidence

- `location_repair_v40.py` is the pure proposal function. It accepts opaque ID, original text and authenticated mentions; it returns original neural mentions separately from effective rule-assisted mentions, proposals and abstentions.
- `location_repair_cases_v40.py` authors 36 location and 36 time/status software cases. They are outside corpus membership. Expected answers are not worker inputs.
- `location_repair_worker_v40.py` executes the four predeclared views and unchanged v38 context handling. It cannot load neural libraries, connect to a database or dispatch network/process activity.
- `location_repair_scoring_v40.py` and `location_repair_study_v40.py` keep references coordinator-only, freeze inputs, enforce a single attempt and preserve failed/partial evidence. Existing v38 and earlier prototypes are unchanged.
- Private `location-repair-authoring-20261019-v40` holds the bound 347-pass software receipt. `location-repair-prepared-20261019-v40` holds fixtures, raw workload, freeze and immutable `analysis-v1`. `location-repair-execution-20261019-v40` holds isolation receipts, stopped container state and incremental raw outputs. `location-repair-verification-20261019-v40` holds separate saved-output verification and individual outcome review.

The prepared package binds 50 source/test files and exact training/reference/output hashes. It uses the already authenticated 345-record training-only view; do not reopen the mixed train/validation parent. Three reference holds remain unscored. Git does not transfer ignored private packages.

## Read-only verification

From the repository root on the laptop containing the private packages:

```powershell
$env:PYTHONPATH = 'backend'
.\backend\.venv\Scripts\python.exe -B -m training.flood_ner.location_repair_study_v40 verify --freeze backend/training/flood_ner/artifacts/location-repair-prepared-20261019-v40/freeze.json --sha256 990c387cc4218e2490c0bb820ea8a0e42bd730223ff4be4c5393213317b7b65a
```

Require `verified_read_only` and `records: 679`. This rechecks bindings and preservation; it does not run proposal/extraction functions or grant system readiness.

The single-use execution claim is consumed. Do not invoke `execute` again, remove its claim, reuse its destination or regenerate a grant to bypass this result. Saved `score` outputs also use exclusive destinations; preserve the completed analysis rather than overwriting it. Existing private preparation/verification scripts write new files and are not generic read-only commands.

## Interpretation

Keep per-family, combination, recognition and association results separate. A corrected location label does not guarantee correct depth/time grouping. A scope disagreement remains a strict error under unchanged references. Software checks are distinct from empirical or constructed behavior results: 347 software checks pass, but only 29/36 new temporal cases pass.

Recorded observation/report times are not inferred onset. Subsidence and its time remain extraction evidence; the user's future history-without-current-map-display policy belongs to downstream integration. This study changes neither database retention nor map plotting.

No neural inference, training, validation/holdout content, deployment, source upload, commit or push is needed to inspect this result. The desktop GPU can remain off.
