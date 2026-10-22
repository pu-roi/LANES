# Saved-prediction regularization comparison

> **Last Updated:** October 19, 2026, 12:02 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Latest completed task:** the separate [training-only boundary study](../evaluations/flood-ner-road-boundaries-20261019/README.md) produced zero corrective actions and no qualifying rules. V19 control remains retained; no additional validation comparison, integration or retraining follows. See the [boundary operator guide](ner-road-boundary-study.md). The earlier dated instructions/results below remain historical and unchanged in their frozen packages.


**Latest completed task:** the separately authorized [frozen validation comparison](../evaluations/flood-ner-context-validation-20261019/README.md) scores 76.54% shadow F1 versus 71.60% control, but fails its zero-new-strict-FP gate. V19 control remains retained and the prototype remains unintegrated. See the [validation operator guide](ner-context-safeguard-validation.md); do not rerun the consumed comparison or tune rules from these findings. The instructions and next-step wording below describe their earlier dated scope.


**Latest checkpoint:** the separate [training-only context study](../evaluations/flood-ner-context-safeguards-20261019/README.md) is complete. Three shadow retags pass the training no-harm gate; no validation gain has been measured. V19 control remains retained. A [separate frozen validation proposal](ner-context-safeguards.md) is the next gate; no training or completed-holdout evaluation is authorized. The instructions below describe preserved regularization/comparison history.


**Completed locally: the v21 candidate lost overall screening, and v19 control seed 0 remains retained.** Read the [diagnosis](../evaluations/flood-ner-regularization-diagnosis-20261019/README.md). No additional training, collection or completed-holdout evaluation is authorized.

The offline comparison helper reads authenticated saved train/dev predictions and frozen references. It never loads a neural model or runs inference. Its CLI requires an explicit checkout, SHA-bound private request and absent private output directory. The request binds the candidate archive/manifest, public publication receipt, control predictions/metrics, qualified development exports, prior/source/training reviews, conventions, preservation ledger and exact helper/test bytes. It rejects stale inputs, incomplete references and holdout capabilities.

The completed private output is `backend/training/flood_ner/artifacts/regularization-comparison-20261019-v22-run02`. Source decisions, log review, corrected diagnostic annex v2, proposals and regression evidence are separately preserved under `regularization-comparison-coordination-20261019-v22`. Preserve all predecessors, including the first completed comparison and its source/test snapshots. Requalification added an explicit evidence end-offset bound; all actual metrics, comparisons and review outputs remain byte-identical. The v1 temporary diagnostic annex is superseded; use the v2 coverage and introduced-FP review files identified by its correction receipt.

For an explicitly requested local reproduction, use the existing backend interpreter and the recorded request SHA-256, selecting a **new** output destination:

~~~powershell
& .\backend\.venv\Scripts\python.exe -I -B .\backend\training\flood_ner\regularization_comparison.py --checkout (Get-Location).Path --request .\backend\training\flood_ner\artifacts\regularization-comparison-coordination-20261019-v22\comparison-request-run02.json --request-sha256 992c8d8fcd9da4168afa67e5f5e8b1fcde2f4d5b89322f4df440cfd21507c0a2 --output .\backend\training\flood_ner\artifacts\regularization-comparison-20261019-v22-replay01
if ($LASTEXITCODE -ne 0) { throw 'Stop; preserve comparison failure and input evidence.' }
~~~

Do not reuse that output if it exists. The guarded CLI forbids neural-library imports, network and subprocess dispatch. It verifies raw hashes before/after and completed-holdout metadata by stat only. No archived script is imported. Output consists of private per-record transitions/reviews, source hashes, strict metrics/gaps, grouping metadata and an input/output manifest; only aggregates belong in public documentation.

Keep strict TP/FP/FN separate from overlap diagnostics. Wrong type on the same text creates FP+FN; a newly recognized surface string is not necessarily a recovered TP. Eight resolved and eighteen introduced FPs yield a net increase of ten, not ten newly introduced predictions. Unsupported language/class slices remain unmeasured. Floating tolerance is 1e-12; counts and identities must be exact.

The next possible task is a separately scoped feasibility review of training/convention-derived context safeguards and constructed contrasts. It is not permission to apply rules, correct labels, select another model or train. The school/gymnasium boundary, completed-holdout exclusion, AI-assisted silver status and incomplete-history limitations remain unchanged.
