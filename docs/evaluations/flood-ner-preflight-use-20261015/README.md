# Study-use packet and isolated calamanCy preflight

> **Last Updated:** October 15, 2026, 8:33 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

Both preparation tracks are delivered. The source-use packet covers **139 selected articles and 400 silver samples**. Pinned **calamanCy md 0.1.0** passes an isolated **CPython 3.11.17 / spaCy 3.7.5 / CPU** loading-and-inference preflight on **24 constructed passages**, with two native-tokenizer reference-boundary gaps. The existing LANES environment, datasets, corrected contextual v2 and frozen partitions are unchanged. **586 tests pass.**

| Outcome | Measured result |
|---|---|
| Study-use packet | Prepared; three publishers, four separate proposed uses each |
| Source-use decisions | All 12 outcomes unresolved; no admission inferred |
| Research installation | Installed separately; dependency check passes |
| Pinned model artifact | 23 verified files, 161,970,218 bytes, revision 51a40433059d8a2c25b98a48eca854f8789a491a |
| Constructed preflight | Passed; 12 English and 12 Taglish cases, 240 measured calls after one warm-up pass |
| Native reference alignment | Two gaps in constructed case 20 |
| News model inference/evaluation | Zero |
| Training admission/export/training | Zero |
| Production Python 3.12 qualification / six-class accuracy | Not established |

[Status](status.json), [audit](audit.json), [study packet](study_use_packet.json), [review instructions](study-use-review.md), [review template](reviewer-form.md), [139 article links](139-article-links.csv), [400 sample links](400-sample-links.csv).

The study-use packet preserves captured publisher policies, failed live-check outcomes, attribution and retention arrangements. Academic training/evaluation, production use, article redistribution and model redistribution have separate reviewer/date/basis/evidence/outcome fields. Preparing or filling a form does not grant permission or change admission. Full-text copies remain ignored local artifacts; an external backup and retention period are not established. The actual method is same-agent AI silver annotation, not independent human/gold verification. [Decision forms](review_forms.json), [policy evidence](source_policy_evidence.json), [source register](source_register.json).

The research interpreter is managed by task-local uv 0.13.1 using an explicit install directory and `--no-bin`; The installer briefly registered its managed interpreter with the Windows launcher; that task-owned catalog entry was backed up and removed, leaving the original Python 3.12 launcher listing. No security policy or main environment was changed. Future setup uses `--no-registry` in addition to `--no-bin`. Dependencies are isolated: spaCy 3.7.5, spacy-transformers 1.2.5, transformers 4.30.2, tokenizers 0.13.3, NumPy 1.26.4, floret 0.10.5, CPU torch 2.14.1+cpu and an explicit Click 8.5.0 dependency matching LANES tooling. Exact transitive versions and wheel hashes are locked before installation. `backend/requirements.txt` registers the optional recipe through comments; production does not install it. [Lock](requirements-qualification.lock), [environment](environment_manifest-v2.json), [interpreter/build and launcher restoration](interpreter_manifest.json), [official uv controls](https://docs.astral.sh/uv/reference/cli/#uv-python-install).

The complete artifact was fetched from the approved commit, with individual response commits and Git/LFS/SHA-256 checks. The initial repository API returned a different commit identity; the pinned tree and individual responses independently confirmed the intended files. That discrepancy is preserved and no unversioned loader or replacement model was used. Model MIT license evidence is retained independently from unresolved news-text use. [Model manifest](model_manifest.json).

Model attribution: calamanCy by Lester James V. Miranda. The versioned card and metadata are retained with the artifact manifest; this run uses their declared MIT license. [Pinned model card](https://huggingface.co/ljvmiranda921/tl_calamancy_md/blob/51a40433059d8a2c25b98a48eca854f8789a491a/README.md).

The offline `preflight-model` command verifies the model and constructed-only inputs, launches the separate interpreter with UTF-8 isolation, validates returned hashes/offsets/labels and records failures without invented predictions or resource measurements. It loads only tok2vec and ner for this CPU profile; coarse LOC/ORG/PER outputs are not LANES six-class predictions. One warm-up pass is followed by ten measured passes, batch size one and two CPU threads. Predictions repeat identically. [Preflight](preflight.json), [prediction metadata](constructed_predictions_metadata.json).

Model loading took **681.95 ms**, excluding Python/module imports. Warm inference median was **13.66 ms**, p95 **15.58 ms**, and peak working set **424,759,296 bytes (~405 MiB)**. These measurements apply to the short constructed cases on the current host; they are not news-corpus performance or production service guarantees. [Resources](resource_measurements.json).

The native tokenizer treats `CITY—-Purok` as one token in the constructed `CEBU CITY—-Purok 31-A` example. The expected CITY and LOCAL_AREA boundaries therefore cannot align. The other constructed reference boundaries align. Source text and the native model tokenizer were not changed to hide this gap. The next tokenizer/model adaptation stage must preserve evidence and qualify any new artifact before news-corpus evaluation. The synthetic cases are outside the 400 and are not real-source evidence or an accuracy benchmark.

Earlier failures remain versioned: a transient Application Control interpreter-query failure, a relative-request-path bug, a missing Click dependency, and a Windows stdout encoding error on Filipino characters. Retrying the same resolver succeeded without security-policy changes. New research lock v2 adds Click; absolute request paths and an explicit UTF-8 byte protocol correct the tooling defects. Final preflight v4 passed. [Preserved failures](prior_failures.json).

The local run folder is `backend/training/flood_ner/artifacts/preflight-use-20261015/`. It contains the managed interpreter, private research environment, complete model, locked recipes, all failure logs and `actual-preflight-v4/predictions.json` with original constructed token/entity text. Full news text and model weights are not published through these metadata reports. The prior [reviewed dataset folder](../flood-ner-review-qualification-20261015/bundle_register.json) remains current for the 400 and contextual v2.

Completion is packet preparation plus research installation/preflight, not dataset admission or production qualification. Next work remains documenting the study-use basis and qualifying tokenizer adaptation and actual candidate behavior under the frozen evaluation protocol. No news training, test-set evaluation, runtime integration, database/schema change, shared-document edit, deployment or Git publication occurred.
