# LANES validation study — partial results, October 16, 2026

> **Last Updated:** October 16, 2026, 6:18 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

Validation-only comparisons for completed seeds 0/1 and the frozen baselines pass. Seed 2 fails in redirected console-output encoding; its failed folder and logs are preserved. The repair passes a reproduced regression test. Under the approved stop-on-failure rule, further training is stopped pending an explicit retry decision. No seed 2 completion, three-seed aggregate, recipe improvement or final test result is claimed.

## Measured validation results

All comparisons use the same 60 development passages (30 English / 30 Taglish), with exact record identity and original character boundaries. Six-class matching also requires the class. Model inference receives raw passage strings, never reference Docs/Examples or entities.

| System | Six-class micro F1 | Separate coarse LOC F1 |
|---|---:|---:|
| Original primary seed 0 | 67.15 | 79.81 |
| Original robustness seed 1 | 70.59 | 82.84 |
| Frozen mention rules | 63.28 | 63.88 |
| Native pretrained NER | Not a six-class model | 68.83 |
| Original seed 2 | Incomplete | Incomplete |

Each loaded selected checkpoint reproduces its recorded development F1. Seed 0 remains primary; seed 1 is not promoted for scoring higher. The native model retains its original tokenizer and scores only native LOC predictions in the separate coarse task; ORG/PER counts remain diagnostics. All six reference classes collapse to LOC without joining adjacent entities. Coarse F1 must not be compared directly with six-class F1.

The [comparison manifest](comparison-manifest.json) includes precision, recall, TP/FP/FN, class/language/language-class slices, native non-LOC diagnostics and negative support. Rules cannot emit LOCAL_AREA; legacy locality emissions stay LANDMARK, without annotation-driven repairs or relabeling.

There are six negative development passages, all Taglish. Rules and both trained models produce zero false-positive passages on those six. English negative support is zero, so its rate is null, not a measured zero. This small subset does not establish general specificity.

## Seed 2 failure and repair

The existing launcher selects the RTX 3060 Ti, then its parent process raises UnicodeEncodeError when printing a spaCy information symbol through a redirected cp1252 stdout. The parent preserves failed state and terminates the remaining worker. No model/checkpoint is saved. Optimizer updates in the interrupted worker are not established from the retained log.

The launcher now explicitly configures stdout/stderr as UTF-8. A constructed redirected-cp1252 regression reproduces the failure before repair and passes afterward. A further integration test runs a real standard-library child that emits Unicode through the redirected parent, writes constructed stub metadata in a temporary directory, and verifies log capture and completion status. It loads no model and runs no GPU code. No training configuration, dependency, GPU policy, annotations or original checkpoint is changed. A separate recovery configuration changes only the output/checkpoint location; its original model/optimizer/stopping settings remain identical. It is checked but unrun.

Three nvidia-smi samples cover startup/the failed-attempt interval, not sustained training. They cannot establish utilization during earlier seed 0/1 training. Logs are private in validation-study-execution-20261016-v1.

## Bounded recipes prepared, not executed

The [preregistered study manifest](study-manifest.json) binds seven configurations: one relocated seed 2 recovery, and seeds 0/1/2 for each of A and B.

| Recipe | Patience | Learning rate |
|---|---:|---:|
| Original / recovery | 175 | 0.001 |
| A | 350 | 0.001 |
| B | 350 | 0.0005 |

All other settings remain frozen, including batch 8, dropout 0.1, eval_frequency 35, max_epochs 30 and max_steps 1000. A/B are evaluated first with seed 0; the original wins equal F1, then A precedes B. Only a strictly improving recipe receives robustness seeds 1/2. No trial/winner exists yet. The session records its 50-minute cutoff for starting new training; changing the deadline is not an automatic recovery action.

## Verification and preservation

Forty-three focused standard-library tests pass: ten launcher, nine preparation, twelve export regressions, eight comparison and four recipe tests. Coverage includes raw-string inference, Unicode, exact/coarse scoring, negatives and undefined slices, missing/duplicate identities, selected-model status, overwrite refusal, controlled recipe changes even after rehashing, and fixed selection ties. The historical full suite is not rerun.

All **10,859 pre-existing artifact hashes**, **23 model files**, **22,759 audited research-environment file stats**, **109 CLI package versions**, requirements and .env verify unchanged. Research-environment preservation uses size/mtime and excludes bytecode consistently; it is not complete environment content hashing. The admitted 400 samples / 138 articles / 40 context pairs / 1,465 spans / 48 negatives, 200/200 languages and 280/60/60 splits remain unchanged. [Preservation](preservation.json); [complete verification](verification.json).

New private request data contains 60 copies of the same validation passage strings; 5 selected validation passages equal their original complete source body. These are existing selected passages, not newly collected articles or additional samples. Private predictions contain offsets/labels rather than article bodies. Public reports contain metadata only.

Original training folders, annotations, contextual pairs, source-use flags, GPU environment, original model and tokenizer remain unchanged. Historical acquisition/use evidence, three audit-reference limitations and the detailed desktop predecessor remain as previously recorded; no new source-use conclusion or permission is supplied. The 40 context pairs remain training references, not a held-out contextual benchmark.

No held-out test predictions/metrics, export, dependency installation, API/schema change, deployment, correspondence, commit, push or shutdown occurs. All scores are development agreement with same-AI silver references, not independent gold accuracy.

## Remaining work

Await the retry decision before further training. If authorized within a valid session budget, use a fresh recovery folder and the checked encoding repair; preserve the failed seed 2 attempt. Then finish the original family comparison and bounded A/B trials. If authorization arrives after the cutoff, establish a new bounded session and fresh preregistration instead of silently extending the old deadline.

[Task plan](../../task_plan.md); [manual training guide](../../guides/ner-first-manual-training-20261016.md).
