# First manual LANES NER training run

> **Last Updated:** October 17, 2026, 3:50 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current successor targets clarified: retain 345 proposed training passages and target 60 validation + 60 independent test passages (465 total if all qualify).** The reviewed development proposal still contains **345 training / 57 validation**; **three additional eligible validation passages are needed**. The independent test still has only **37 conditionally supported passages / 23 positive passages missing (10 English, 13 Taglish)** for its current joint witness. These are targets and conditional counts, not admitted/frozen records. Keep all historical fitted-source groups training-only; never use isolated test material to fill validation or validation material to fill test. **Next: run and reconcile the original desktop history inventory before further collection; then qualify additional validation/test material under separate roles and resolve the recorded acquisition-budget failure.** No new search, capture, admission, export or training is authorized by this count clarification. Previous review/design/qualification packages and their completed counts remain historical. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Desktop continuation:** Follow the [pull-and-inventory guide](ner-desktop-history-inventory.md), including its copyable desktop Codex prompt. The helper runs directly from the pulled repository with Python 3.10+ standard libraries. Inventory the original desktop before any backup restoration or collection. Git supplies code/public reports; the linked Drive folder is the October 16 historical backup, while newer private reviews remain on the laptop. Return the private inventory/manifest for reconciliation; do not start the old training launchers. [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the successor targets above are newer.

**Targeted isolated collection and desktop-history handoff completed with blockers:** Review five pre-breach captures and preserve all prior material. Nine complete positive proposals are added; the supported finite-pool joint witness after known history/use filters is **37/60**, conditional on unresolved global history and the failed acquisition gate. **Discovery reached 202/200 URLs (17 new versus at most 15); collection stopped and the entire final 11-URL batch remains held/ineligible.** Capture attempts stay **37/100**. The **402 qualified development candidates / proposed 345+57** remain unchanged. A portable, tested metadata/hash inventory and desktop instructions are ready; the original desktop has not yet been inventoried. **Next: run and reconcile the desktop inventory, resolve acquisition compliance and independent-test coverage/evidence before admission/freeze/export or desktop GPU training.** No training has started; the test remains unsealed with zero admitted/scored records. [Report](../evaluations/flood-ner-targeted-test-history-handoff-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the targeted-collection/handoff outcome above is newer:

**Archive history and saved-test selection completed; training remains pending:** Verify all **3,863 recorded v3 payloads / 11 parts / 2,357 objects**, **seven historical ZIP entries** and metadata for **19 known Drive items**, with no missing/conflicting recorded payload. Complete isolated positive-window selection and source-only historical comparisons in a separate private curator package; retain the unchanged **60 / 30+30 / 27-positive+3-negative-per-language** target. **Unknown external cross-computer history remains unresolved; test stays unsealed with zero admitted/scored records.** The **402 qualified development candidates / proposed 345+57** remain unchanged. **Next: address the specific remaining independent-test history/evidence/coverage gaps before admission/freeze/export and desktop GPU handoff.** [Archive and saved-test outcome](../evaluations/flood-ner-archive-history-test-selection-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the archive/selection outcome above is newer:

**Successor qualification and isolated-test reassessment complete; training remains pending:** **402 qualified proposal candidates / 149 source cases**, retaining **345 proposed training / 57 validation**; all 259 relationship entries qualify for supported conservative joint grouping without incident-identity or independence claims. Carry forward 64 exclusions and 99 holds; record 16 scoped project-use adoptions for 20 saved-source windows. **The separate 60-passage test stays unsealed: the user is unsure whether all older cross-computer article histories are represented.** Curator-specific evidence/count gaps remain in the safe report. No actual admission, freeze, export or training. **Next: resolve the concrete history/isolated-test gaps; reuse completed development qualification before a separate admission/export/desktop GPU handoff.** [Qualification and test reassessment](../evaluations/flood-ner-successor-qualification-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the qualification status above is newer:

**Successor dataset design complete; retraining remains pending:** Use all **402 provisional candidates** in a separate **345 training / 57 validation proposal** (170/175 training English/Taglish; 37/20 validation). Actual original/A/recovery/B input bindings anchor all 280 historical training records, including now-excluded/held examples. **The old additional 240 / exact-balance quotas are prospectively superseded for this version by explicit user choice; historical specifications and results remain unchanged.** Validation has no Taglish ROAD/LANDMARK or short-code-theme examples; conservative grouping does not certify event independence. **Next: resolve proposed-member source-use/group admission qualifications and complete the separate unchanged 60-passage fresh-test boundary before admission/freeze/export and desktop training.** No actual admission or partition freeze occurs. [Successor design](../evaluations/flood-ner-successor-design-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the successor design above is the current status:

**Current status:** The original seeds and held-out benchmark are complete; the original 400/138/40 experiment remains frozen. The [consistency review](../evaluations/flood-ner-consistency-review-20261016/README.md) verifies the shared six-class data format and repairs Windows checkout-byte hashes. New data remains unadmitted/unpartitioned. **Use the laptop for data review, validation and preparation; actual training stays on the existing qualified desktop GPU.** No new run is ready or needed under the historical commands below.

Before preparing a new desktop run:

1. Use the separate 402-candidate / proposed 345-training + 57-validation successor design as the review proposal; actual admission/group qualification and freeze are still pending. Preserve the historical benchmark and six-class annotation conventions.
2. Reuse the completed source/reference/group qualification for the 402 candidates; keep old holds and validation coverage limits visible. Reuse the recorded-archive reconciliation and isolated saved-test selection; resolve their remaining external-history and test evidence/coverage gaps before sealing the independent fresh test.
3. Produce a new admitted dataset and qualified export with one consistent tokenizer/vocabulary and exact hashes; never point the original fixed-400 export at the drafts.
4. Prepare new desktop-local manifests/configuration and a new output destination. Keep original/A settings and model roles traceable; the historical GPU launcher has no CPU fallback and is not a generic trainer for new data.
5. Verify the handoff on the actual desktop. The local .gitattributes repair must reach its checkout before relying on frozen source hashes. Training begins only with the finished dataset/experiment contract, not by rerunning the old commands.

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
