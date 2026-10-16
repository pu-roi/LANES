# First manual LANES NER training run

> **Last Updated:** October 16, 2026, 8:37 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current status:** All approved training, the fixed held-out evaluation and the full 60-passage qualification review are complete. Original seed 0 stays primary at 63.12 test F1; A seed 0 stays exploratory at 67.72. No manual run is needed. Preserve the existing freeze/attempt marker and checkpoints. Next prepare the remaining Gate 3 qualification specification; operational qualification and runtime integration remain open. [Review](../evaluations/flood-ner-model-qualification-20261016/README.md).

Historical manual instructions follow; do not rerun their seed 2 command into the existing failed destination.

**Earlier manual checkpoint:** Seed 0 finished successfully. Its development-selected checkpoint is step 455 (F1 67.15). The next manual runs are seeds 1 and 2. [Primary result](../evaluations/flood-ner-primary-training-20261016/README.md).

Run one at a time from the repository root:

~~~powershell
.\backend\training\flood_ner\RUN-TRAINING.ps1 -Seed 1 -StartTraining
~~~

Wait for the explicit completion message. If it succeeds, run:

~~~powershell
.\backend\training\flood_ner\RUN-TRAINING.ps1 -Seed 2 -StartTraining
~~~

Omit -StartTraining to perform only the frozen-input check. Both seed checks pass; 29 focused tests pass. Neither run has started. Do not rerun seed 0. Each robustness run starts independently from the same pinned encoder with a fresh six-class head; it does not continue seed 0. Different seeds measure variability, not guaranteed improvement. Keep settings unchanged and seed 0 primary.

Results are saved separately to seed-1 and seed-2 under the same academic-training-20261016-v1 directory. Each produces training.log, run-status.json and selected-checkpoint/model. Keep PowerShell open/computer awake. If a run fails, preserve its output and report the error before launching another run.

The instructions below describe the completed first run and remain for reference.

You run primary seed 0 in PowerShell on this RTX desktop. Codex can inspect the saved result and run seeds 1/2 afterward. No additional application or dependency installation is needed, and the later seeds do not start automatically.

The launcher is ready. Only its check-only mode has run; training has not started. PowerShell parsing, actual input verification and 26 focused unittest methods pass. [Launcher verification](../evaluations/flood-ner-experiment-preparation-20261016/manual-launcher-verification.json); [frozen experiment](../evaluations/flood-ner-experiment-preparation-20261016/README.md).

## Start the first run

Open PowerShell, paste these two lines and press Enter:

~~~powershell
Set-Location 'E:\Files\Documents\GitHub\LANES'
.\backend\training\flood_ner\RUN-SEED-0.ps1 -StartTraining
~~~

The StartTraining switch starts actual model training after frozen-input verification. Running the script without that switch checks inputs only. The launcher verifies the passing preparation, admission, qualification, export, model/tokenizer and rules hashes using the repaired backend interpreter. It refuses changed inputs or an existing seed 0 output folder. The isolated Python 3.11 GPU process runs the saved configuration without overrides or CPU fallback.

Keep this PowerShell window open and the computer awake until it finishes. Codex can remain open, but this externally launched process does not require an active Codex turn. If Windows blocks script execution, preserve the exact error for review rather than changing policy blindly.

## What the terminal shows

First you will see frozen-input verification and the output/log paths. Initialization can take time before the training table appears. It then prints epoch/step progress, NER loss and development entity precision, recall and F1. NER loss measures training error; lower is generally better. Development F1 is the selection measure; one row need not improve on the previous row.

The run trains on 280 samples and checks 60 development samples. It never predicts or scores the 60 test samples. This is one frozen recipe for seed 0, not a search. Early stopping can finish it before the configured limits. No reliable duration estimate has been measured for the actual corpus.

Expect the explicit launcher message:

~~~text
Training completed. Preserve this folder for result review.
~~~

A spaCy saved-model message by itself does not establish completion: the launcher also checks exit status, unchanged bindings and the authoritative selected model. Read run-status.json; state must be completed. Scores measure agreement with AI silver annotations, not independently verified gold accuracy.

## Saved results

Everything stays private under:

~~~text
E:\Files\Documents\GitHub\LANES\backend\training\flood_ner\artifacts\academic-training-20261016-v1\seed-0
~~~

- training.log: terminal training output and errors.
- run-status.json: running, completed, failed or interrupted status.
- launch-request.json: paths and frozen configuration/code identities.
- selected-checkpoint/model: authoritative development-selected model.
- selected-checkpoint/selection.json: development score and selected step.
- model-best and model-last: standard spaCy outputs; use the separate selected checkpoint for the frozen earlier-step tie rule.

The seed 0 configuration, datasets, tokenizer and original model remain unchanged. New model weights are saved only in the new ignored run folder. This does not evaluate test samples, deploy, reassess source use, install dependencies, commit or push.

## Stop or hand back to Codex

Press Ctrl+C if you need to stop. Partial logs/checkpoints may remain; interrupted output is not a completed experiment. Do not delete or rerun into an existing seed 0 folder. Send Codex the terminal error or report that the run finished; Codex can read the saved files directly from this checkout.

After successful completion, tell Codex: "Seed 0 finished; inspect the result and handle the next runs." Codex should verify completion and select the frozen checkpoint before proceeding with robustness seeds 1/2 and baseline comparisons. Test predictions stay held out until experiment choices are frozen.
