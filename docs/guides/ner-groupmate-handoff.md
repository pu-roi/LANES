# LANES NER: development, dataset and evaluation guide

> **Last Updated:** October 21, 2026, 12:44 AM Asia/Manila
> **Prepared by:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

This is the starting document for a groupmate who needs to understand how LANES NER was created, what data it uses and what its recorded results mean. It consolidates repository evidence through the October 21 controlled local integration checkpoint. Numbers below are saved research results; preparing this guide did not run training, inference or another holdout evaluation.

## 1. What the NER does

Named Entity Recognition (NER) finds a place name in article text and assigns a location category. LANES retains **corrected v19 control, seed 0**, with six learned location labels. It is a server-side spaCy model initialized from a pinned Calamancy model.

The current extraction method combines learned location recognition with separately identified rules:

```text
Exact captured article text
  -> v19 learned location mentions
  -> v40 location proposals + v44 combined location repairs
  -> v42 rule-based depth/time/status/access association
  -> saved evidence and unresolved groups
  -> source, placement and publication checks
```

Depth, time, status and access association are **rule based** in this retained method. They are not trained DEPTH/TIME NER classes. A recognized place alone does not establish current flooding, coordinates, an affected road boundary or permission to publish an alert. Original neural mentions remain separate from effective mentions and rule repairs. See the [v46 backend report](../evaluations/flood-ner-backend-location-v46-20261020/README.md).

## 2. Entity labels and annotation structure

| Learned label | Meaning |
|---|---|
| `ROAD` | A road or street name |
| `LANDMARK` | A named physical landmark or facility |
| `LOCAL_AREA` | A named locality below or outside the other administrative categories |
| `BARANGAY` | A barangay name or identifier |
| `CITY` | A city name |
| `PROVINCE` | A province name |

These descriptions introduce the categories; the [annotation schema](../../backend/training/flood_ner/annotation/schema.py) and frozen annotation conventions govern exact inclusion and boundaries. The trained label roster and encoder initialization are implemented in [experiment_registry.py](../../backend/training/flood_ner/experiment_registry.py).

An annotation binds an unchanged passage to its original captured source. Important fields are:

| Field group | Recorded information |
|---|---|
| Source | Source ID, publisher, URL, capture version, exact text/hash and publication evidence |
| Passage | Record ID, source-relative start/end, exact text/hash and reviewed passage language |
| Entity | Entity ID, label, exact mention text and start/end offsets |
| Review | Annotation revision, teacher/reviewer, quality, review status and completion |
| Membership | Train/dev/test split plus article/event/syndication grouping evidence |
| Separate context references | Facts, supporting evidence, target entity IDs, temporal roles, qualifiers and relations |

Offsets use half-open Unicode character ranges: `text[start:end]` must equal the recorded mention. Complete empty entity lists represent reviewed negative passages; incomplete annotation cannot be treated as a negative.

**Constructed illustration, outside the dataset:** in `Baha sa Ortigas Avenue.`, `Ortigas Avenue` occupies `[8, 22)` and can illustrate `ROAD`. The flood wording requires separate fact/context processing. This illustration supplies no measured training or evaluation evidence.

## 3. How the model was created

1. Capture publisher article text and preserve source/publication evidence and hashes. Review passages without rewriting their source characters.
2. Annotate place spans under the six-class location profile. Preserve teacher/reviewer and correction history. The actual references are **AI-assisted silver**, rather than independently human-verified gold.
3. Review source identity, complete annotations, reuse/admission state and related article/event/syndication groups. Exclude held or rejected proposals; group related reports before assigning partitions.
4. Lock the selected membership and qualify the tokenizer. Export spaCy `DocBin` corpora and verify that serialization/reloading preserves text, tokens, entity offsets, labels and record IDs. Keep holdout data outside the trainer payload.
5. Initialize a fresh six-class NER head, copy the pinned pretrained NER encoder and preserve its static vocabulary. Train using the qualified tokenizer and recorded GPU environment.
6. Select checkpoints by strict validation entity micro F1; retain the earlier step when scores tie. Screen the specified recipes, then run the prescribed robustness seeds. Seed 0 remains primary.
7. Perform the separately frozen research-holdout comparison once after selection. Preserve predictions and error evidence privately; publish aggregate metrics.
8. Qualify the retained model for runtime use, then connect separately versioned location/context rules and guarded backend processing. Runtime qualification does not change the model's measured recognition score.

The [successor preparation report](../evaluations/flood-ner-successor-preparation-20261018/README.md), [corrected-data preparation](../evaluations/flood-ner-corrected-experiment-preparation-20261018/README.md), [desktop training report](../evaluations/flood-ner-corrected-v19-execution-20261018/README.md) and [diagnosis/evaluation report](../evaluations/flood-ner-v19-diagnosis-evaluation-20261018/README.md) document these stages.

## 4. Dataset used for corrected v19

The retained research corpus contains **465 passages**, split **345 training / 60 validation / 60 research holdout**. A passage is a selected text window, not an entire article. Multiple related passages must not be counted as independent articles or flood events.

| Partition | Passages | English | Taglish | Positive | Reviewed negative | Location spans | Recorded connected groups |
|---|---:|---:|---:|---:|---:|---:|---:|
| Training | 345 | 170 | 175 | 242 | 103 | 840 | 38 |
| Validation | 60 | 38 | 22 | 33 | 27 | 85 | 20 |
| Research holdout | 60 | 30 | 30 | 54 | 6 | 96 | 30 |
| **Total** | **465** | **238** | **227** | **329** | **136** | **1,021** | **88** |

Connected groups reflect recorded article/event/syndication/duplicate relationships, not proof of exhaustive physical-event independence. Development contains 126 training and 25 validation article identifiers; the holdout has 37 recorded article groups. Aliases and connected reporting mean these are not a verified unique-source or incident total.

### Location-class distribution

| Label | Train EN | Train Taglish | Train total | Validation EN | Validation Taglish | Validation total | Holdout total |
|---|---:|---:|---:|---:|---:|---:|---:|
| BARANGAY | 34 | 51 | 85 | 10 | 9 | 19 | 22 |
| CITY | 186 | 122 | 308 | 9 | 14 | 23 | 45 |
| LANDMARK | 38 | 20 | 58 | 6 | 1 | 7 | 7 |
| LOCAL_AREA | 6 | 13 | 19 | 9 | 3 | 12 | 0 |
| PROVINCE | 106 | 63 | 169 | 2 | 8 | 10 | 9 |
| ROAD | 155 | 46 | 201 | 14 | 0 | 14 | 13 |
| **Total** | **525** | **315** | **840** | **50** | **35** | **85** | **96** |

Source: [partition and coverage report](../evaluations/flood-ner-successor-preparation-20261018/README.md) and its [aggregate JSON](../evaluations/flood-ner-successor-preparation-20261018/summary.json). Corrected v19 adopted **12 supported boundary extensions in nine training records**, preserving texts, entity types/counts and split membership. Validation references and tokenizer bytes were unchanged; see [correction evidence](../evaluations/flood-ner-corrected-experiment-preparation-20261018/README.md).

Earlier reports describe a **400-passage / 280-60-60** historical corpus and its October 16 test. Those figures and scores belong to an earlier experiment. Do not combine them with corrected v19's 465-passage corpus or its 96-span research holdout. Separate contextual reference pairs and constructed software fixtures add no independent location-training samples.

## 5. Training configuration and selection

| Setting | Retained corrected-v19 setup |
|---|---|
| Base model | `tl_calamancy_md`, version `0.1.0` |
| Pinned revision | `51a40433059d8a2c25b98a48eca854f8789a491a` |
| Initialization | Fresh six-class head; transferred pretrained NER encoder; pinned static vocabulary |
| Tokenizer | Frozen `lanes.xx.address-v2` |
| Training runtime | Python 3.11.17; spaCy 3.7.5; recorded RTX 3060 Ti GPU run |
| Batch size | 8 |
| Optimizer / learning rate | Adam / 0.001 |
| Dropout / L2 | 0.1 / 0.01 |
| Maximum budget | 1,000 optimizer steps; 30 epochs |
| Validation frequency / patience | Every 35 steps / 175 optimizer steps |
| Seeds | 0 primary; 1 and 2 robustness checks |
| Checkpoint selection | Strict validation micro F1; earlier step on equal score |
| Authoritative selected model | `selected-checkpoint/model`, with `selection.json` |

The built-in spaCy `model-best` tie behavior does not implement the project's earlier-step policy; use the recorded selected checkpoint. The encoder/lower network used GPU while the upper classifier used CPU by design. See [registry implementation](../../backend/training/flood_ner/experiment_registry.py) and [training evidence](../evaluations/flood-ner-corrected-v19-execution-20261018/README.md).

| Screened recipe, seed 0 | Validation precision | Recall | F1 | Selected step | Outcome |
|---|---:|---:|---:|---:|---|
| Corrected control | 75.32% | 68.24% | 71.60% | 945 | Retained |
| Higher dropout: 0.2 | 56.47% | 56.47% | 56.47% | 420 | Not retained |
| Lower learning rate: 0.0005 | 65.06% | 63.53% | 64.29% | 875 | Not retained |
| Later stronger L2: 0.05 | 67.78% | 71.76% | 69.71% | 945 | Failed its separate screen |

The first screen retained control and completed its seeds 1/2, for five successful v19 training runs. Control validation F1 across seeds 0/1/2 was **71.60% / 71.52% / 66.27%**, mean **69.80%**, sample SD **3.05 percentage points**. The later L2 candidate increased false positives and was not adopted; see the [regularization diagnosis](../evaluations/flood-ner-regularization-diagnosis-20261019/README.md). These experiments do not establish an optimal recipe.

## 6. How to read the accuracy tables

The main metric is **strict entity micro F1**, rather than classification accuracy. An entity is correct only when both its exact start/end offsets and its label match the reference. A correct name with the wrong boundary or category does not count as a strict true positive. Counts are pooled across the six labels for the overall micro score.

```text
Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
F1        = 2 * TP / (2 * TP + FP + FN)
```

TP means a matching typed span; FP means an unmatched predicted span; FN means an unmatched reference span. Wrong-type/boundary predictions can contribute both an FP and an FN. These measures do not use token-level true negatives. A zero-support class is reported as unmeasured where applicable, rather than assigned an invented accuracy.

### Primary v19 seed-0 results

| Partition | Reference spans | Precision | Recall | Strict F1 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| Training | 840 | 98.44% | 97.74% | 98.09% | 821 | 13 | 19 |
| Validation | 85 | 75.32% | 68.24% | 71.60% | 58 | 19 | 27 |
| Research holdout | 96 | 77.91% | 69.79% | 73.63% | 67 | 19 | 29 |

The **26.48-point training/validation F1 gap** is consistent with memorization and differences between fitted and validation examples. High training F1 is not evidence of equally high performance on new articles.

### Per-class results for primary v19

| Label | Training support | Training F1 | Validation support | Validation F1 | Holdout support | Holdout F1 |
|---|---:|---:|---:|---:|---:|---:|
| BARANGAY | 85 | 100.00% | 19 | 74.29% | 22 | 86.36% |
| CITY | 308 | 99.35% | 23 | 85.11% | 45 | 80.46% |
| LANDMARK | 58 | 91.23% | 7 | 58.82% | 7 | 20.00% |
| LOCAL_AREA | 19 | 97.30% | 12 | 58.82% | 0 | Unmeasured |
| PROVINCE | 169 | 99.12% | 10 | 85.71% | 9 | 50.00% |
| ROAD | 201 | 96.50% | 14 | 48.00% | 13 | 66.67% |

### Language slices for primary v19

| Language | Validation passages | Validation F1 | Holdout passages | Holdout F1 |
|---|---:|---:|---:|---:|
| English | 38 | 69.47% | 30 | 74.47% |
| Taglish | 22 | 74.63% | 30 | 72.73% |
| Pure Tagalog | No measured slice | Unmeasured | No measured slice | Unmeasured |

Taglish validation has **zero ROAD reference spans and one LANDMARK span**. The holdout has **zero LOCAL_AREA references**. Passing constructed Tagalog fixtures cannot establish measured pure-Tagalog model performance.

### Frozen research-holdout comparison

All systems below used the same 60 passages and 96 reference location spans.

| System | Precision | Recall | Strict F1 | Negative passages with any FP, out of 6 |
|---|---:|---:|---:|---:|
| v19 control seed 0, primary | 77.91% | 69.79% | 73.63% | 0 |
| v19 control seed 1 | 65.98% | 66.67% | 66.32% | 2 |
| v19 control seed 2 | 69.31% | 72.92% | 71.07% | 2 |
| Historical v16 seed 0 | 75.53% | 73.96% | 74.74% | 1 |
| Historical v16 seed 1 | 78.41% | 71.88% | 75.00% | 0 |
| Historical v16 seed 2 | 75.26% | 76.04% | 75.65% | 1 |
| Frozen location-mention rules | 60.53% | 47.92% | 53.49% | 0 |

Control's holdout mean is **70.34%**, sample SD **3.71 points**; historical v16's mean is **75.13%**, sample SD **0.47 points**. V19 was retained from validation and was not reselected using holdout results. These numbers do not establish an overall holdout improvement over v16. Six negative passages cannot establish a general false-alert rate; this comparison scores location mentions, not complete flood decisions.

Sources for all recognition tables: [diagnosis and interpretation](../evaluations/flood-ner-v19-diagnosis-evaluation-20261018/README.md), [full development metrics](../evaluations/flood-ner-v19-diagnosis-evaluation-20261018/development-metrics.json) and [holdout aggregate](../evaluations/flood-ner-v19-diagnosis-evaluation-20261018/holdout-aggregate.json). JSON retains full precision, per-label/language counts and unsupported slices; percentages here are rounded to two decimals.

## 7. Context and runtime checks are separate measurements

| Evidence | Recorded outcome | What it measures |
|---|---|---|
| v38 fixed-reference association study | 98 TP / 0 FP / 7 FN; 96.55% association F1 | Association against 23 exposed silver training references; not independent recognition/system accuracy |
| v46 backend preview | 1,281 software checks; saved article retains all 53 original neural mentions | Adapter, context, provenance and runtime preservation for that checkpoint |
| C3b controlled local RSS integration | 754 distinct software tests; one session preserves all 4,483 saved neural spans | Software integration and output parity; not a 100% accuracy score |
| C3b resources | Peak 2,492.09 MiB; main invocation 75.772 seconds on one CPU / 3 GiB | Local runtime/resource compatibility; not a cloud benchmark |

The v38 association result belongs to an earlier rule version and exposed subset; it is not a score for current v42 grouping on unseen articles. Test counts describe their own dated selections and must not be added as independent accuracy observations. Sources: [v38 study](../evaluations/flood-ner-context-fixed-links-20261019/README.md), [v46 integration](../evaluations/flood-ner-backend-location-v46-20261020/README.md), [C3b report](../evaluations/rss-ner-rss-integration-20261021/README.md).

As of C3b, controlled local backend integration passed. Eight inputs entered through mocked RSS and two short pre-existing controls entered processing directly. Historical publication was paused: no alerts or zones were created. Scheduled production processing remains legacy; monitoring, interface acceptance, 403 investigation and release verification remain separate work. The reviewed article still has eleven unresolved rows; model recognition and contextual coverage are incomplete.

## 8. What a groupmate receives through Git

| Material | Repository location | Transferred by a normal branch pull? |
|---|---|---|
| This explanation and result tables | `docs/guides/ner-groupmate-handoff.md` | Yes, once committed/pushed |
| Aggregate metrics and dated evidence | `docs/evaluations/flood-ner-*/`, `docs/evaluations/rss-ner-*/` | Yes, for committed files |
| Annotation, qualification and training helpers | `backend/training/flood_ner/` excluding `artifacts/` | Yes, for committed files |
| Runtime/backend extraction implementation | `backend/app/services/news_ner*/` and related API/schema/CRUD files | Yes, for committed files |
| Captured article bodies, full annotations, DocBins, individual predictions, trained weights and raw logs | `backend/training/flood_ner/artifacts/` | **No: ignored private artifacts** |
| Prepared local preview assets | `backend/runtime_data/ner_preview/` | **No: ignored runtime assets** |

Reading the guide and aggregate JSON requires no model, database, GPU or new training run. Reproducing an already documented run additionally requires the matching private inputs, model/tokenizer assets, runtime and authenticated manifests from Roi. A Git pull alone cannot supply them. Do not rerun historical training/evaluation commands just to read this work; many name completed output directories, and the exposed holdout is closed to tuning or repeat evaluation under its existing protocol.

## 9. Limitations to preserve in the paper or presentation

- Scores measure agreement with **AI-assisted silver references**, not independently verified real-world accuracy. Global source-history and acquisition-accounting gaps remain documented; the holdout is not certified fresh or human gold.
- Data is small, imbalanced and grouped. ROAD, LANDMARK and LOCAL_AREA coverage is weak; unsupported class/language slices remain unmeasured.
- Validation has been reused during development. The completed holdout's aggregate results are exposed and cannot become an untouched tuning test again. Further tuned-model claims require a fresh untouched evaluation design.
- Learned DEPTH/TIME remains unfinished; qualified context rules support the retained interim method. Unresolved facts, scope and reference holds are not silently resolved.
- Recognition F1, contextual association, runtime parity, publication correctness and road placement are different outcomes. No single reported F1 measures the entire RSS-to-map system.

A suitable project statement is: **“Corrected v19 control seed 0 achieved 71.60% strict six-class entity micro F1 on validation and 73.63% on a separately frozen research holdout, measured against AI-assisted silver references. Depth/time/context association uses separately qualified rules.”**

For the pending branch contents and the checks performed while preparing this documentation, see the [NER handoff branch review](../evaluations/ner-handoff-review-20261021/README.md).
