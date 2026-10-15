# GPU preflight timeout logging fix

> **Last Updated:** October 15, 2026, 4:09 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

Resolved the review's P2 finding: timed-out GPU or CPU workers now retain partial stdout/stderr in their named log files before the failed report is written. Empty streams produce empty files. Report hashes cover both logs, and the timeout still leaves GPU qualification failed.

Four regression scenarios failed before the fix and pass afterward. The focused GPU/preflight/inventory/tokenizer selection now passes **126 tests**, with the same two previously documented dependency warnings. Fault injection verifies both worker modes, partial/absent output, exact log bytes, file hashes and saved failure state without waiting 600 seconds or running training. [Verification](verification.json).

The [original two GPU runs and their metadata](../flood-ner-desktop-gpu-20261015/README.md) remain unchanged. That environment manifest's parent-helper hash identifies the pre-fix snapshot; a byte-identical copy is preserved locally as `artifacts/gpu-qualification-20261015/gpu_preflight-reviewed-v1.py`. The current helper hash is recorded in this follow-up. The successful execution path, environment, dependencies, pinned weights and tokenizer are unchanged, so GPU training was not repeated for this logging fix.

The review also identified a coverage limitation: the temporary trial model emitted no entities on the 24 probes. The historical CPU replay therefore confirms loading and matching empty predictions, while the native model separately produced 39 entities on each device. Useful six-class extraction accuracy remains a later real-training/evaluation gate; this logging fix makes no accuracy claim and changes no news admission or data.
