# Chapters III–IV: source-grounded documentation review

> **Reviewed:** October 24, 2026, Asia/Manila
> **Reviewer context:** Roi Cambe (@roicambe), `roi-branch`
> **Source baseline:** `eea154504a62f4931df430ed84818169bee7f938`, including the existing uncommitted implementation at review time.

Document: [LANES_Original_Revisions](https://docs.google.com/document/d/1TcpT2REz48FL-H6w_3vwmgL-9B8EumRj8TroDAgyTsc/edit?tab=t.0). Review covers Chapter III, Chapter IV, and the surrounding methodological statements necessary to interpret them. The Google Doc was not edited. Source code, model metadata and hashes, saved aggregate results, selected existing tests, and relevant earlier chats were inspected. Cloud status below comes from dated retained acceptance records, not a fresh production inspection.

## 1. Verdict and NER identity

**The retained neural model really is corrected v19 control, seed 0.** Later version numbers describe location repairs, context association, integration, experiments, or deployment revisions. Replacing “v19” everywhere with “v40” would make the paper less accurate.

| Layer | Verified implementation | Meaning |
|---|---|---|
| Trained recognizer | `v19-control-seed-0`; selected step 945 | Six learned location labels: BARANGAY, CITY, LANDMARK, LOCAL_AREA, PROVINCE, ROAD |
| Model runtime | spaCy 3.7.5; isolated Linux/Python 3.12 CPU worker | Loads the retained model and its authenticated tokenizer/resources |
| Location proposals | `lanes-location-repair-v40` | Separate rules applied after neural recognition |
| Additional location repairs | v44, combined method | Source-supported proposals; original neural mentions remain preserved |
| Context association | `lanes-context-association-v42` | Rule-based depth, time, status and access association |
| Shared location adapter | `lanes-location-pipeline-v46` | Composes v40 → v44 → v42; does not retrain the model |
| Persisted processing method | `ner_rules_v1`, with content-derived pipeline identity | Identifies a complete processing configuration rather than a new neural checkpoint |
| Optional correction stage | Saved Gemini resolution, with separately versioned policies | Derived evidence-linked output; does not change neural weights or replace the original run |

Primary source evidence: [runtime model loading](../../backend/app/services/news_ner_runtime/worker.py), [shared adapter](../../backend/app/services/news_ner/location_pipeline.py), [trusted identities](../../backend/app/services/news_ner_durable/assets.py), [checkpoint selection and encoder initialization](../../backend/training/flood_ner/experiment_registry.py), and [bundle preparation](../../backend/scripts/prepare_ner_preview_bundle.py).

This conclusion is not based only on a hardcoded model name. All **11 selected control-seed-0 checkpoint file hashes** in the retained development-selection record match the local runtime bundle. Its metadata records step **945**. All manifested runtime files pass byte-size/hash checks. The packaged cloud context's `ner/model` bytes match the same selected neural weights. The spaCy package metadata says `version: 0.0.0`; that is generic package metadata, not the LANES experimental version. The trained weight SHA-256 is `a2e232cd04174488c97c4f6b45454ab1189646d1def0ea8f4bd2432344a547d8`.

**Important operating-path distinction:** the ordinary scheduler calls `run_news_pipeline` without a native context. That path invokes captured-article extraction in `rules_only` mode. The native NER path is selected explicitly, and manual cloud pilots have separate controls. “LANES uses v19 NER” is accurate for that implemented neural path; “every scheduled RSS article currently runs through v19” is not supported. See [scheduler](../../backend/app/services/news_scheduler_service.py), [pipeline dispatch](../../backend/app/services/news_pipeline_service.py), and [legacy extraction](../../backend/app/services/news_discovery_service.py).

Suggested paper wording:

> LANES retains the corrected-v19 spaCy location recognizer, control seed 0. Its neural output passes through separately versioned v40/v44 location rules and v42 contextual association, composed by the v46 adapter. Depth, time, status and access processing in this configuration is rule based. Optional Gemini resolution produces a separately recorded derived result. These processing and deployment revisions do not indicate retraining of the retained neural checkpoint.

## 2. Chapter III: numerical validation and revisions

| Section/table | Review result | Required revision |
|---|---|---|
| Introduction and capabilities; Table 2 | Mostly consistent, but mixes present capabilities with measurements proposed earlier | State the evaluation cutoff and attach a date/configuration to each result. Keep unmeasured end-to-end latency and geocoding success explicitly unmeasured. |
| Table 3 | **Freshly reproduced:** 50 inputs, 68 expected claims; flood/forecast/history 50/50, negation 48/50; barangay 47/50, depth 43/43, condition 59/59 | Retain the numbers. Identify the tested path as the constructed-input rule extractor. Describe the latter fields as expected-value coverage, not neural accuracy. |
| Table 4 | Diagnostic examples, not a representative failure rate | Add the dated extractor/reference identity. Recheck examples on the declared snapshot before presenting them as current outputs. Distinguish textual recognition, locality resolution and claim-level association. |
| Table 5 | 78 TP, 1 FP, 1 FN correctly calculate to 98.73% for precision, recall and F1 | Preserve as a separately dated constructed-input result only with its original mention references, scorer and output receipt. The current 50-input evaluation script does not calculate this span score, so this review does not independently reproduce it. |
| Tables 5A–5C | Saved JSON supports the displayed v19 counts, scores, class support and language slices | Keep v19. Add the layered pipeline explanation and exact experimental identity. The neural-only score is not a score for v46 or the Gemini-assisted article-to-map path. |
| Table 5D | Saved C3b JSON supports 754 distinct checks, ten neural requests, 4,483 span matches, 53 reviewed matches, 75.772 seconds and the listed resource figures | Keep as October 21 local integration evidence. Parity is reproducibility, not accuracy. Do not pool test counts across overlapping runs. |
| Table 6 | All eight gauge values and four severity assignments match current server constants | Keep as configured reference values. Rounded meter displays are not exact inch equivalents or field sensor measurements. |
| Table 7 | **Freshly reproduced:** inches 8/8, meters 3/8, centimeters 7/8; total 18/24 | Replace the “reconciled from totals” explanation with this dated, explicit probe and retain its input list. Do not claim the missing original log has been recovered. |
| Table 8 | Controlled component-test scope is sound; the old 75-case selection is not a current whole-system test count | Supply the original commit, exact test selection and receipt. Add new acceptance separately. Correct the total row's copied “tested boundary” text to describe the entire selection. |
| Table 9 | **All four behaviors remain reproducible in current code** | Retain the findings and identify the specific loader/evaluator path. Do not say the later geometry-generation work repaired this routing evaluator. |
| Table 10 | Matches current baseline `zone_decision` matrix | Add that explicit restrictive access information can tighten the baseline; “Passable” is a software-policy decision rather than proof of physical safety. |
| Table 11 | 34 is a historical selected queue/grouping/authorization count | Identify the exact selection/receipt. It does not measure approval-decision correctness or the full moderation-to-routing workflow. |
| Table 11A | Accurate for its explicitly dated October 22 v4 checkpoint; incomplete as the latest system status | Keep the historical row, then add the successful provider acceptance and later scoped article pilots. Do not describe HTTP 402 as the current unresolved provider barrier. |
| Tables 12–14 | Means can be checked for plausibility, but respondent-level SDs cannot be verified from source code | Preserve existing survey values pending raw responses. Attach instrument, scale anchors, scoring procedure, response counts, eligibility and exclusion evidence. |
| Discussion and Table 14A | Correctly separates several evidence types but omits the later pipeline and pilot status | Update SOP 1's implementation, SOP 3's geometry provenance and SOP 4's approval pathways; retain the stated field-evaluation limits. |

### Verified v19 research results

| Partition | Passages | Reference spans | TP | FP | FN | Precision | Recall | Strict typed-span micro F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Training | 345 | 840 | 821 | 13 | 19 | 98.44% | 97.74% | 98.09% |
| Validation | 60 | 85 | 58 | 19 | 27 | 75.32% | 68.24% | 71.60% |
| Research holdout | 60 | 96 | 67 | 19 | 29 | 77.91% | 69.79% | 73.63% |

The corpus total is **465 passages / 1,021 reference spans**, not 465 independent articles or flood incidents. Holdout F1 by label is BARANGAY 86.36%, CITY 80.46%, LANDMARK 20.00%, PROVINCE 50.00%, ROAD 66.67%; LOCAL_AREA has zero reference support and is unmeasured. English and Taglish each have 30 holdout passages, with F1 74.47% and 72.73%. There is no separately measured pure-Filipino neural holdout slice.

Sources: [development metrics](../evaluations/flood-ner-v19-diagnosis-evaluation-20261018/development-metrics.json), [holdout aggregate](../evaluations/flood-ner-v19-diagnosis-evaluation-20261018/holdout-aggregate.json), and [dataset/development guide](../guides/ner-groupmate-handoff.md). These are retained saved results; this audit did not reopen holdout texts or run inference.

Keep the AI-assisted silver-reference and incomplete source-history qualifications. If discussing why v19 was retained, report validation-based selection. The same saved comparison gives v16 seed 0 **74.74%** holdout F1 versus v19 seed 0 **73.63%**; it does not establish a v19 holdout improvement. Repeated training-set/rule diagnostics are not new independent evaluation samples.

### Coverage matching needs a clearer explanation

[The 50-input evaluation script](../../backend/scripts/evaluate_taglish_extraction.py) checks whether **any extracted claim** contains each expected barangay, depth or condition. It does not require all expected fields to occur together on the correct claim. Extra predictions are not penalized by these coverage percentages. Thus 43/43 depth coverage does not establish 43 correctly located, timed flood observations. The manuscript already uses “coverage”; add this matching definition so readers understand its limits.

### Numeric-depth probe and root cause

The six unresolved displayed reference values are **0.20 m, 0.25 m, 0.48 m, 1.14 m, 1.40 m and 140 cm**, tested with spelled-out unit tokens (`meters`, `centimeters`). The parser converts measured numbers to inches and accepts only a gauge within **0.05 inch** of its configured inch value. Some rounded meter values exceed that tolerance; the neck reference also uses 140 cm alongside 55 inches, which are not exactly equivalent. Unmatched measurements remain explicit noncanonical numeric evidence.

Document the literals, conversion, tolerance and abstention rule. Distinguish a source measurement from a rounded UI gauge reference. A future repair should define the intended rounding/interval policy and preserve ranges and qualifiers; the evidence does not justify simply snapping every numeric depth to the nearest gauge. Sources: [gauge constants](../../backend/app/services/flood_depth.py) and [numeric extraction](../../backend/app/services/taglish_extraction_service.py).

### Spatial findings remain current

Using mocked database rows and synthetic geometry, the current loader retained a Polygon but skipped a MultiPolygon. A 222.4 m route inside a Polygon hole was blocked because only its exterior ring reached evaluation. Adding a duplicate zone doubled exposure from **222.4 m to 444.8 m**. Empty route coordinates yielded **blocked=false, safety_score=100**. The exact lengths depend on the synthetic geometry; the underlying failures match Table 9. This does not establish acceptance of an empty route by the public endpoint. Source: [routing policy](../../backend/app/services/flood_routing_policy.py).

## 3. Update implementation and operational descriptions

**Approval is not one universal manual gate.** Citizen submission invokes a policy-controlled automatic-approval service as well as staff review. Its eligibility checks include trust and human-review history, current observation evidence, consistent depth/severity/access and validated road geometry; new incidents require qualifying independent corroboration. The code also has a supporting-report path for an existing compatible zone. News has a separately gated publication path. Describe these branches rather than saying every report must receive an individual staff approval. These code paths do not establish that their automatic settings are enabled in production. See [citizen approval](../../backend/app/services/citizen_approval_service.py), [submission caller](../../backend/app/services/report_service.py), and [news pipeline](../../backend/app/services/news_pipeline_service.py).

**Location recognition, flood evidence and placement are separate stages.** OSM establishes road identity/geometry; NOAH supplies modeled susceptibility; Pasig historical records supply local context. None independently confirms present flooding. Connected-road placement is an explicitly selected policy; its 25 m corridor margin is application policy, not a measured wet width. Estimated road zones must not be described as field-verified inundation footprints. Source: [connected-road acceptance](../evaluations/gma-connected-road-20261023.md).

**Keep the paper's study geography separate from implementation coverage.** Pasig is the stated study/client context, while the implemented place catalog, selected sources and later Malabon/Marikina/Mandaluyong/Manila pilots extend into Metro Manila. This is a scope clarification, not evidence of validated field performance across NCR.

### Dated follow-up to Table 11A

| Checkpoint | Retained evidence | Interpretation |
|---|---|---|
| October 21 | [C3b local integration](../evaluations/rss-ner-rss-integration-20261021/README.md) | Controlled RSS delivery and actual NER; historical publication paused |
| October 22, v4 | [Guarded release](../evaluations/ner-gemini-cloud-release-20261022/README.md) | One HTTP 402 provider probe; no resulting zones |
| October 22, v5 | [Provider repair](../evaluations/three-article-cloud-pilot-20261022/provider-repair.md) | Real HTTP 200 response accepted by backend and independently recomputed; initial payment/request failures retained |
| October 23 | [GMA connected-road rollout](../evaluations/gma-connected-road-20261023.md) | Three scoped presentation instances; historical article dates preserved; excluded from ordinary routing and history |
| October 24 | [Tribune reviewed-time acceptance](../evaluations/tribune-reviewed-time-20261024.md) | Three Tribune roads plus three GMA observations; additional bounded polygons; explicit developer-reviewed shared-time interpretation |
| October 24 recorded checkpoint | [Philstar pilot](../evaluations/philstar-saved-article-20261024.md) | NER run completed; verification stopped by internal budget cap; no accepted Philstar polygons at that checkpoint |

**Publication follow-up — October 24, 2026, 05:02 PM Asia/Manila:** [@roicambe](https://github.com/roicambe) (Roi Cambe). The earlier budget-stop row is a historical checkpoint. Subsequent retained acceptance records now confirm Philstar correction 401, ten accepted observations and three zones (83–85), served by `lanes-api-philstar-20261024-v2`. The cumulative approved cap was explicitly raised to US$1.50; the final conservative estimate is US$1.0215894. Seven accepted placements and nineteen verification targets remain unresolved. [Completed rollout evidence](../evaluations/philstar-saved-article-20261024.md). This note does not change the original audit baseline, JSON receipt, study cutoff or evaluation metrics.

These dated reports do not prove continuous production automation, current real flooding, live-route safety or independent extraction accuracy. Retained pilot records report news automation paused. Current source contains further local work; prospective code must not be reported as already deployed. Do not make a present-tense production claim without a fresh read-only inspection and a fixed documentation cutoff.

## 4. Chapter IV revisions

1. **Conclusion 1:** retain the 98.73% constructed-input versus 73.63% neural-holdout distinction. Add the actual v19 + rule-pipeline identity. Do not recast later rules or Gemini output as a new learned model or a newly measured F1 improvement.
2. **Conclusion 2:** retain the 18/24 numeric outcome, now supported by a fresh explicit probe. Explain exact-gauge matching versus rounded displayed units. Keep four-class severity accuracy and user comprehension unmeasured.
3. **Conclusion 3:** retain the 75-case historical scope and the four still-reproducible geometry failures. Add later bounded placement/map acceptance as a distinct result if the study cutoff includes it. Neither passing checks nor controlled map displays establish field detour safety or general latency.
4. **Conclusion 4:** distinguish staff moderation, conditional citizen automation and gated news publication. Preserve the limit that the selected 34 checks do not establish human decision correctness. Do not claim an untested live approval-to-route chain.
5. **Recommendation 1:** keep ROAD/LANDMARK improvements and a new independent test set. Add separate evaluation of neural recognition, repaired mentions, context association, locality resolution, verification and spatial publication.
6. **Recommendation 2:** specify numeric rounding/tolerance, exact inputs, ranges, qualifiers and abstention. Retain task-based interpretation checks for map colors and labels.
7. **Recommendation 3:** the four routing-evaluator defects remain valid repair targets. Require regression cases and complete provider/geometry/profile checks before making wider route claims.
8. **Recommendation 4:** test each approval branch and its database-to-map-to-route effects, preserving automatic versus human provenance.
9. **Recommendation 5:** preserve the distinction between the 2.90 security perception rating and demonstrated vulnerabilities. Original item responses are needed to interpret it.
10. **Recommendation 6 and technical-records section:** replace a blanket unresolved-provider-access statement with the dated successful acceptance and remaining automation/quality limits. Cite exact reports, commits, dataset identities and execution receipts instead of unnamed “team records.” Keep finalized surveys unchanged until originals justify a correction.

Survey verification remains incomplete: source code cannot recover respondent answers, sample SDs or inclusion criteria. The earlier chat **Testing Audit Plan** flagged a three-of-six expert-label inclusion issue. Reconcile that historical concern against the final respondent roster; it is not proof that the current three-person table is wrong. Rounded category means alone cannot reproduce respondent-level overall SDs. Compatibility is explicitly unmeasured in the current document.

Small editorial repairs: update the table of contents, which currently lists Chapters I–II and references but omits III–IV; remove the stray closing quotation mark before Table 2; repair “Tables 5A 5D,” “Table 4 The…,” “Table 11 presents All…,” and “Figure 11.DRRMO…”. Preserve the existing figure/table design. Screenshot appearance and page layout were not visually audited in this source review.

## 5. Verification and earlier-chat context

Fresh evidence is summarized in [verification.json](../evaluations/chapter3-4-audit-20261024/verification.json):

- **325 selected existing tests passed**, with zero failures/errors/skips in the corrected harness. SQLAlchemy emitted 405 Python datetime-adapter deprecation warnings. Routing providers were mocked, review tests used local fixtures, and no live provider or shared database was contacted.
- The 50-input rule-extractor evaluator reproduces Table 3. Table 7's 24 numeric inputs and all four Table 9 behavior classes were checked independently.
- Model hashes, checkpoint identity and saved metric arithmetic were checked without loading the neural model, retraining or reevaluating the holdout.
- An initial audit harness blocked Windows' internal asyncio socket pair, producing 26 failures and seven setup errors alongside 292 passes. The corrected harness permits only the internal socket-pair construction while retaining the outbound Python socket restriction; the same selected suite then passed. No application code was changed to obtain a pass.

Relevant earlier chats reviewed: **Review Chapters 3 and 4 tables**, **Rewrite Chapter 3 Tables**, **Testing Audit Plan**, **Document NER for roi-branch**, **Review flood NER dataset relevance**, **Plan flood NER integration**, **Connecting NER to LANES**, **Begin phase 1 flood plan**, and the recent **Review flood plan progress** chat. They explain the earlier arithmetic corrections, the separation of constructed and neural results, retained-model/rule integration, cloud qualification and later manual pilots. Earlier messages supply context; source code and dated receipts govern factual conclusions.

Priority order: clarify version/processing identity; define the study cutoff and update the deployment chronology; attach per-table reproducibility records; revise Chapter IV and Table 14A consistently; then complete survey-source and editorial reconciliation.
