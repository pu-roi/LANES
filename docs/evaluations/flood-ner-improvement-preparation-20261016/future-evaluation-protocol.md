# Future NER improvement evaluation protocol v1

> **Last Updated:** October 16, 2026, 8:57 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

Prepared, not executed. This specification versions a future improvement experiment while preserving the completed benchmark. **Original seed 0 stays the historical primary; Recipe A stays exploratory.** The exposed 60-test benchmark is historical diagnostic evidence and cannot become a fresh final test for improvements prompted by its errors.

## Data and reference freeze

1. Freeze the [reference-scope addendum](../../guides/flood-ner-reference-scope-addendum-v1.md) and resolve any additional convention needed by newly acquired material before selecting training settings. Keep unsupported type/sense/identity separate; source-exact names do not certify PSGC/OSM identity.
2. The subsequent dataset-readiness task will acquire additional development material using the eight-theme coverage requirements. Each new source needs an applicable source-use/admission assessment, full captured provenance, source-exact references, reviewed language and article/event/syndication/duplicate grouping. The old scoped project admission does not blanket-authorize new material.
3. Reserve **60 newly acquired test passages: 30 English / 30 Taglish**, with **3 no-location negatives and 27 positive passages per language**. A negative has no in-scope location entities, regardless of flood status. Ambiguous candidate references remain in a separate unresolved inventory and do not fill a test slot.
4. Exclude all previously captured/reviewed/training/validation/test/contextual material and all new development material at article, revision, event, syndication and exact/near-duplicate levels. Review canonical URL aliases and semantic event relationships; a different URL/hash/date alone is insufficient. Unknown or provisional group relationships block test admission.
5. Reconcile the locally indexed historical source inventory with other laptop/history inventories before certifying freshness. The ignored index includes 712 structured source-metadata variants (348 source-ID values), not 348 certified distinct articles. Its incomplete-history flag is intentional. The prior acquisition/history limitations remain disclosed.
6. Use an actual held-out curator (human or isolated agent context) with no model-development role or model outputs. It may inspect references for labeling and grouping, while model development receives only package identities/counts/hashes and exclusion metadata. Record actual identities and access logs; context separation alone is not independent gold adjudication. No curator is appointed or agent spawned by this task.
7. Before any new training, seal the final 60 memberships, convention version, source/reference hashes, group decisions, tokenizer bindings and access policy. If development sees test texts/labels, uses model results to choose cases, or tunes from new test results, disclose the exposure and acquire a replacement untouched holdout before another fresh-test claim. New to this project does not mean unseen during native-model pretraining.

## Experiment and scoring

- Preserve the original 400/138/40 corpus and original/A checkpoint roles. A later improvement dataset/experiment gets new manifests and destinations; never overwrite the completed experiment. Additional corpus size, recipes, seed family, selection/tie policy and prospective numerical acceptance criteria remain decisions for dataset-readiness/experiment preparation, before training or opening test results.
- Develop using training/validation and disclosed constructed fixtures only. The 48 fixtures are exposed development material and cannot be counted as new captured samples or held-out accuracy evidence. Changes to conventions require re-review in a new dataset version; do not mix old and new label rules silently.
- Run a separately authorized, single exclusive test attempt after the new experiment/model roster is frozen. Give inference raw passage strings; references support identity checks and scoring only. Preserve failed-attempt diagnostics and require explicit recovery authorization rather than silently retrying.
- Strict scoring matches record ID, start, end and six-class label exactly. Report TP/FP/FN, precision, recall and F1 overall, by class, language and class/language. Retain reference/prediction support and null for undefined denominators. Report false-positive spans and affected negative passages with their per-language denominators.
- Report collapsed location matching separately for trained models, frozen rules and native pretrained LOC. Native ORG/PER are diagnostic, and rules' unavailable LOCAL_AREA output remains explicit. Record family seed variability/sample SD when preregistered; no seed promotion using test scores or significance claim from a small seed family.
- Report agreement with AI silver references unless independent review actually establishes a stronger reference status. Sparse or absent slices remain unsupported. The 60-test design is a bounded research comparison, not proof of field safety or guaranteed precision.

## Remaining Gate 3 and next task

**Next task: prepare and admit the additional dataset.** Reconcile historical exclusions; acquire source-eligible examples for the recorded gaps; review references/grouping and separate held-out access; record actual counts; then choose additional corpus size and a bounded training protocol from that evidence. Readiness requires source-use eligibility, clear labels/language, no group leakage, frozen conventions, tokenizer alignment and complete input bindings. No new corpus, export or training is delivered now.

CPU/target-Linux model loading and tokenizer parity, missing/corrupt-model visible failures, and cold/warm latency/memory/long-text qualification remain Gate 3 requirements. This preparation does not perform them or close operational qualification. The roadmap's numerical targets remain proposals. Gate 4 integration, contextual association/identity/placement and later publication/lifecycle safety need their separate evidence and authorization.

Historical evidence limitations remain: two restored historical references hash-match without formal reconciliation; the IPOPHL historical reference is hash-divergent; the detailed desktop predecessor is unreconciled. Eleven invalid-fixture references and ten manifest aliases remain separately classified. Six paper/dataset and six production/model-distribution outcomes stay deferred for those uses.

No source research/acquisition, annotation revision, inference, export, training, dependency change, public API/schema change, deployment, correspondence, commit or push occurs in this preparation.
