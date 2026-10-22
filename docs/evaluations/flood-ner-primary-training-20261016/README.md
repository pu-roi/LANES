# Primary seed 0 training result — October 16, 2026

> **Last Updated:** October 16, 2026, 5:51 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The researcher manually completed seed 0 training using the frozen recipe on the RTX desktop. Exit code 0; elapsed time 148.13 seconds including initialization and launcher checks. The development-selected checkpoint is step 455: strict six-class micro F1 67.15, precision 68.32 and recall 66.03 on the 60 development samples. These are same-AI silver-reference agreement scores, not independent gold accuracy.

Training stopped normally at logged step 630: 175 steps since the best development checkpoint, matching the unchanged patience setting. The configured limits remain max_epochs 30, max_steps 1000 and eval_frequency 35. The authoritative model is the private seed-0/selected-checkpoint/model, not model-last. No held-out test predictions or final evaluation occurred.

[Run status](run-status.json), [selection](selection.json), and [verification](verification.json) are metadata only. All 103 seed 0 files rehash unchanged during launcher extension; .env and the frozen configuration/admission/export/model/tokenizer bindings verify unchanged. No trained weights or article text are copied into this report. The original seed 0 launcher source is preserved under ignored robustness-launcher-20261016-v1/previous-manual_training.py, with a hash matching the run request. Extending the launcher changes no prepared recipe or historical run file.

The next tasks are the already planned robustness seeds 1/2 and matched baseline comparisons. The researcher may launch both manually, one at a time. Each independently initializes the same pinned encoder/fresh head; neither resumes seed 0. Seed 0 remains the primary result, regardless of which seed scores highest.

The generic RUN-TRAINING.ps1 launcher requires an explicit Seed parameter and -StartTraining to train. Without that switch it checks inputs only. It preserves seed 0 compatibility, refuses existing outputs/non-frozen seeds and blocks another run while a run status is marked running. Both seed 1/2 check-only invocations and PowerShell parsing pass; 29 focused tests pass (eight launcher tests and 21 preparation/export regressions). No seed 1/2 training starts during this task.

Historical source-use/acquisition and detailed desktop-predecessor limitations remain explicit. Independent label/language review, baseline comparisons, final frozen test evaluation and distribution/deployment decisions remain separate. There are no dependency, public API, database schema, export, deployment, correspondence, commit or push changes.

[Manual commands](../../guides/ner-first-manual-training-20261016.md); [task plan](../../task_plan.md).
