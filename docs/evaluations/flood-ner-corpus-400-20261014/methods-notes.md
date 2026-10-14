# Paper-preparation notes: actual 400-sample dataset work

> **Last Updated:** October 14, 2026, 6:47 PM (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

Use the supplied document's actual chapter structure: Chapter II methodology, Chapter III results/discussion and Chapter IV conclusions/recommendations. The shared Google document has not been edited.

## Chapter II: performed method

Suggested wording:

> Public Philippine flood-related news and documented non-flood/control contexts published between January 2022 and October 14, 2026 were captured with source URLs, publication evidence, retrieval metadata and hashes. An AI assistant annotated source-exact location spans and reviewed the passage language and labels. These references are silver annotations; independent human verification was not performed. From 561 reviewed candidate records, 400 distinct location-annotated passages from 132 articles were selected. The dataset contains 200 English and 200 Taglish passages under a declared lexical-mixing definition. Related reporting was grouped conservatively before assigning 280 training, 60 validation and 60 testing records, with equal language counts in each partition. Reuse assessments and training admission remained unresolved at this preparation checkpoint.

Explain the six-label Philippine-place taxonomy, exclusions, original-text offsets, actual AI teacher/reviewer provenance, lexical language definition and publisher/language confounding. Describe the constrained selection and reporting components; do not equate 400 passages with 400 independent storms or articles. Do not describe solely AI-created labels as manually produced by researchers.

## Chapter III: measured dataset results

Report **400 accepted silver location records, 132 represented articles, 1,374 location spans, 200/200 language totals and 280/60/60 research partitions**. The [coverage report](coverage.json) supplies publisher/year/label counts; the [register](selection_register.json) supplies identities and offsets. Retained pilot records are part of the 400, and context views do not add samples.

Record **zero training admission, zero corpus DocBin export, zero independent gold verification and zero trained models**. The latest follow-up review records 425 passing checks after contextual JSONL correction; these are software/source-integrity tests, not training-sample counts or precision/recall/F1. The paper's separate constructed 50-input rule results and 60–100 baseline-testing proposal must not be relabeled as this trained NER evaluation.

## Chapter IV: conclusions supported so far

Dataset preparation and reproducible offline tooling are delivered. NER accuracy, calibrated severity mapping, runtime performance, production flood extraction and map/routing improvement remain unmeasured. Explain coverage gaps, AI label/language uncertainty, source dependence, conservative grouping and the publisher/language association. Report future model scores as teacher-label agreement unless independently verified references are actually established.

Next, resolve training-use evidence, qualify remaining source/event/language/label uncertainties and complete separate context/severity references. Model/tokenizer compatibility and a frozen evaluation contract must be established before training and model comparison.
