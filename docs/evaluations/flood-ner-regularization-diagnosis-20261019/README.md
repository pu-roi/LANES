# Why the regularization candidate lost screening

> **Last Updated:** October 19, 2026, 02:23 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The saved predictions reproduce the screening loss. Keep corrected v19 control, seed 0 primary.** The unchanged 345 training / 60 validation records were compared without loading models, running inference or changing annotations. No new optimizer experiment is authorized.

## Reproduced result

| Primary seed 0 | Control | L2 = 0.05 candidate |
|---|---:|---:|
| Training F1 | 98.09% | 98.81% |
| Validation precision | 75.32% | 67.78% |
| Validation recall | 68.24% | 71.76% |
| Validation F1 | 71.60% | 69.71% |
| Train-minus-validation gap | 26.48 points | 29.10 points |
| Validation TP / FP / FN | 58 / 19 / 27 | 61 / 29 / 24 |
| Negative passages with false positives | 0 / 27 | 2 / 27 |

Every strict count matches the saved desktop and laptop evidence. All floating metrics agree within 1e-12; macro summation order can differ at approximately 1e-16 without changing the decision. The independent comparison accounts for all 405 records, 840 training spans and 85 validation spans. [Complete metrics](metrics.json) · [Class/language gaps](gaps.json).

| Validation label | Reference spans | Control F1 | Candidate F1 |
|---|---:|---:|---:|
| BARANGAY | 19 | 74.29% | 62.86% |
| CITY | 23 | 85.11% | 85.19% |
| LANDMARK | 7 | 58.82% | 47.06% |
| LOCAL_AREA | 12 | 58.82% | 73.68% |
| PROVINCE | 10 | 85.71% | 80.00% |
| ROAD | 14 | 48.00% | 53.33% |

| Validation language | Passages | Control F1 | Candidate F1 |
|---|---:|---:|---:|
| english | 38 | 69.47% | 67.33% |
| taglish | 22 | 74.63% | 72.97% |

Taglish validation ROAD has zero reference support; its F1 remains unmeasured. Taglish LANDMARK has one span. Precision/recall/F1 and negative errors are retained for every supported slice; unsupported values are not replaced with zero.

## What changed

There are **17 validation passages with changed predictions** and **22 passages with an error in at least one model**. Net errors alone hide transitions:

| Strict validation transition | Count |
|---|---:|
| Introduced false-positive typed spans | 18 |
| Resolved false-positive typed spans | 8 |
| Persistent false positives | 11 |
| Gained correct entities | 7 |
| Lost correct entities | 4 |
| Persistent correct entities | 54 |
| Persistent missed reference entities | 20 |

Thus FP changes by 18 minus 8 = **+10**, TP by 7 minus 4 = **+3**, and FN by **-3**. The candidate emits 90 entities versus 77 for control. Its extra recall does not compensate for the loss of precision.

The 18 introduced false positives contain **nine exact-boundary wrong types, three same-type boundary errors, three combined boundary/type errors and three without reference overlap**. The latter concern organization/professional-role or excluded geographic scope under the existing six-class conventions. Six boundary-related predictions do not imply six independent passages or reference entities. Overlap links remain diagnostic and never replace strict scoring.

Introduced false positives by predicted label: CITY 5, ROAD 4, LANDMARK 4, BARANGAY 4, PROVINCE 1, LOCAL_AREA 0. Shared list antecedents, physical facility versus road distinctions, administrative names, road compounds/crossings/directions and integral suffixes explain observed error forms. These are evidence-backed error descriptions, not a proven unique causal mechanism for weight decay.

All **22 affected validation passages and their 18 complete saved source articles** were reviewed. The sixty dispositions are 21 retain-reference, one retain-unresolved-boundary and 38 carried-forward supported reviews whose predictions agree with the frozen reference. The school/center-versus-gymnasium proper-name boundary remains unresolved and is still scored against its original reference. **No supported annotation correction or demonstrated training/scoring defect was found.**

A focused review of **33 existing training passages and adjacent source context** confirms relevant road, locality and organization-only contrasts already exist. This includes all sixteen positive LOCAL_AREA training passages and the existing shared numeric-identifier example. Presence is not proof of sufficient diversity or learned generalization, and absence is not an adequate blanket explanation for these errors. Nothing was relabeled or added.

## Groups and training evidence

Validation has **20 connected reporting groups**; the 22 affected passages lie in 15 groups. Introduced false positives occur in 11 groups, with contributions 3, 3, 2, 2, 2, 1, 1, 1, 1, 1, 1. Training has 38 conservative components; its three largest contain 178 of 345 passages. These relationships remain unchanged and do not assert one physical incident per component. [Coverage and concentration](coverage.json).

The authenticated raw candidate log contains **29 rounded evaluation rows**, every 35 steps from 0 through 980. Its unique displayed maximum occurs at selected step **945**; saved selection and predictions independently establish full-precision F1 0.6971428571428572. At step 980 the displayed validation F1 is 66.67%. The recorded desktop stopping reason is the 1,000-step cap. The backup omits final model-last metadata/weights, so that terminal step is retained as recorded desktop evidence, not recreated from the console table.

The resolved run config differs from control only in **L2 0.01 to 0.05** plus eight expected portable resource/output bindings. Fresh-head/pinned-encoder initialization metadata records zero updates at transfer. Dropout, learning rate, budgets, patience, checkpoint policy and tokenizer stay unchanged. Earlier control raw learning curves remain unavailable locally; rounded candidate curves do not establish an optimum or justify extending training.

## Recommendation and verification

**Do not start another optimizer search from this result.** Keep v19 control. A separate development-only feasibility task can examine conservative, convention-derived context safeguards using existing training cases and constructed contrasts, especially organization/role exclusions and explicit shared designators. Any prototype is a separate derived method, must abstain on unsupported cases and must not silently alter neural predictions, references or the retained model. No gain or threshold is promised. [Prioritized proposals](proposals.json).

Fresh checks pass **197 tests and 20 subtests**, including 51 new constructed comparison tests. The 291 execution tests, 341 preparation tests and 359 delivery tests remain historical results from different selections. One existing spaCy/Click deprecation warning is recorded. Constructed fixtures stay outside dataset membership. The actual comparison process blocks neural-library imports, transport and child processes; no neural model is loaded.

All **416 protected file hashes** and **55 stat-only completed-holdout entries** remain unchanged. The private package binds the authenticated archive and all 146 member hashes, control predictions/metrics, qualified development inputs, conventions, source reviews, helper/test bytes and output hashes. A temporary diagnostic-annex list/tuple boundary comparison was corrected in a separate v2 annex; its predecessor and correction receipt are retained, and all eighteen corrected classifications match the shared diagnostic function. Strict counts/scores, core outputs and annotations were unaffected. A final explicit evidence end-offset guard was separately qualified in a new output; all real metric, comparison and review files match the preserved first comparison byte-for-byte.

See [verification](verification.json) and [operator guide](../../guides/ner-regularization-comparison.md). Individual texts, identities, source snippets, annotations and predictions remain private. References remain **AI-assisted silver**, with reused-validation, incomplete-history/accounting, support and single-candidate-seed limitations. No holdout access, inference, training, model-selection change, new data, applied correction, integration, upload, commit or push occurs. The desktop can remain off.
