# C3a follow-up — bounded CLI startup errors

> **Last Updated:** October 20, 2026, 11:00 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Status: fixed and verified locally.** This is a later CLI-only correction to the [historical C3a qualification](../rss-ner-native-worker-20261020/README.md), not runtime requalification or automatic-processing activation. [Current task plan](../../task_plan.md#phase-c--connect-automatic-article-processing).

## Failure and correction

Settings initialization and application imports previously ran outside the CLI's error handlers. An invalid boolean setting, failed dependency import or startup interruption could emit an unbounded traceback before processing. The older in-process tests had already cached application imports and therefore missed this stage.

`scripts.run_news_ner_processing.main` now protects the complete bootstrap invocation. `_run` classifies Pydantic validation failures during application imports as configuration failures, then enters the existing processing handlers only after their exception classes are available. Missing dependencies and other unexpected startup exceptions are bounded by the outer handler. Existing worker behavior, guards, argument parsing and engine cleanup are retained.

| Startup outcome | JSON error code | Exit |
|---|---|---:|
| Invalid settings | `ner_configuration_invalid` | 1 |
| Missing dependency or unexpected import failure | `ner_runtime_failed` | 1 |
| Keyboard interruption or async cancellation | `ner_runtime_cancelled` | 130 |

Each tested startup failure emits exactly one JSON record and no stderr traceback or raw diagnostics. These errors appear in process output, before article processing; this change adds no saved article error or frontend display.

## Verification

Run from `backend` with the existing virtual environment and plugin autoload disabled:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
venv/Scripts/python.exe -m pytest --noconftest tests/test_news_ner_processing_cli.py -q
```

**16 checks pass without skips:**

- Seven existing checks preserve runtime/asset errors, cancellation, engine disposal, environment/platform guards and malformed database URL reporting.
- Seven fresh-interpreter failure cases cover actual settings validation, missing Pydantic, import failure at processing/assets/contracts, KeyboardInterrupt and async cancellation. All seven reproduced the startup defect before the fix.
- Two fresh-interpreter cases preserve help (exit 0) and missing-argument usage (exit 2), before application bootstrap.

Fresh children run with isolated Python, no inherited application configuration/credentials and a temporary working directory without `.env`. Database connections, socket connections and subprocess launches are forbidden and checked even if an exception handler would otherwise hide their failure. No actual database connection, model process or inference occurs. One existing Starlette multipart deprecation warning appears in the parent test process; failure-case child stderr remains empty.

## Separate source record and preserved history

Private evidence is stored in the ignored `backend/training/flood_ner/artifacts/rss-ner-cli-bootstrap-20261020` package: before-source snapshots, failing/passing JUnit receipts, before/after CLI hashes, changed-source diff and a preservation check. The existing C3a v1/v2 packages retain all **613 files byte-for-byte**, including their source snapshots, prediction/integration receipts and prior CLI correction freeze. No earlier report, qualification claim or receipt is rewritten.

The CLI and its tests are the only executable-source changes for this correction. Documentation records the later result separately; the historical 251-check C3a count is unchanged and is not added to this overlapping 16-check suite.

## Remaining gates

Overall Phase C stays open. C3b RSS admission/corrections, feed provenance, intended-method readers, downstream acceptance and frontend work remain pending. No schema, dependencies, trained assets, inference-worker/rules, Google Cloud configuration, deployment or automatic-processing switch changes are included.
