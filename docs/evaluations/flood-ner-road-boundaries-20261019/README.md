# Training-only road-boundary feasibility

> **Last Updated:** October 19, 2026, 12:02 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**No boundary rule qualifies for a later comparison.** Trimming and splitting pass constructed checks but have no observed corrective applicability on the 345 original training predictions. Both families are **partially supported: constructed behavior works, empirical repair remains unproven**. Keep v19 corrected control seed 0 retained; no validation comparison follows from this result.

## Evidence and scope

The study authenticated the existing training-only view: **170 English / 175 Taglish passages**, original v19 control seed-0 predictions and unchanged six-class silver references. It did not compose the earlier type safeguards. Validation references/predictions and completed-holdout content were excluded from prototype development and scoring.

For saved-article review, the coordinator deterministically filtered training records from the authenticated development source container. No validation row was printed, reviewed, scored or supplied to the prototype. The study worker used only the existing training-only view and source-bound training evidence; it never reopened parent development containers.

All **seven training passages with ROAD errors** were reviewed against their **five unique complete saved articles**. Their strict ROAD counts are six FP and eight FN. Six missed ROAD references involve boundary problems, including one also predicted with the wrong type; two misses have correct boundaries but wrong types. Three ROAD false positives involve boundaries and three are type-only errors. Overlap explanations remain separate from strict counts: one merged prediction can overlap two missed references.

The saved material contains useful contrasts for separate crossing roads, integral compound names, terminal intersection wording and traffic qualifiers outside names. However, the observed merged predictions lack an explicit crossing connector, and the descriptor-bearing ROAD predictions lack the complete explicit road-name pattern required by this prototype. Correct-boundary type mistakes are outside a label-preserving method. No source or annotation was changed to make a rule applicable.

## Frozen prototype

The new standalone helper accepts only unchanged text, an opaque ID and original predicted spans. It permits keep/trim/split on ROAD predictions, preserving labels and every non-ROAD prediction. Each child must remain inside its original span; outputs must be non-overlapping and source-exact. The prototype cannot restore missing prefixes or infer a geographic identity.

- **Terminal descriptor:** trim separate final Intersection/Junction only after a complete explicit road name. Bare names, naming ambiguity and compounds remain held.
- **Traffic direction:** trim separate final direction words/abbreviations, including bounded directional pairs, only after a complete explicit road name. Integral names remain unchanged.
- **Explicit crossing:** split one cor./corner connector only when both sides independently satisfy the bounded explicit road-name grammar. Unmarked adjacency, ordinary hyphens/slashes, incomplete sides and multiple connectors remain unchanged.

Rules inspect original predictions without cascading. Conflicting or ambiguous proposals abstain. No article IDs, expected references, source identities, gazetteers or proper-name exceptions enter the decision function. Code, evidence, fictional fixtures, tests and qualification policy were hash-bound before the empirical boundary study. Rules were not revised after results.

## Training result

| Rule | Matched predicted spans | Abstentions | Trims / splits | Gained TP / resolved FP | Introduced FP / FN | Qualification |
|---|---:|---:|---:|---:|---:|---|
| Terminal descriptor | 2 | 2 | 0 / 0 | 0 / 0 | 0 / 0 | Unproven; no corrective action |
| Traffic direction | 0 | 0 | 0 / 0 | 0 / 0 | 0 / 0 | Unproven; no applicability |
| Explicit crossing | 0 | 0 | 0 / 0 | 0 / 0 | 0 / 0 | Unproven; no applicability |

All **345 passages and 834 predicted spans remain unchanged**. The combined rules and the empty qualifying subset reproduce every baseline metric. Zero introduced errors alone is insufficient: qualification also requires observed corrective training actions. No such action occurred, so there is no qualifying subset to take to validation. This describes these bounded rules; it does not establish that all possible boundary methods or the saved collection are exhausted.

| Training metric | Original control | Boundary shadow |
|---|---:|---:|
| Strict TP / FP / FN | 821 / 13 / 19 | 821 / 13 / 19 |
| Precision | 98.44% | 98.44% |
| Recall | 97.74% | 97.74% |
| Micro F1 | 98.09% | 98.09% |
| Supported-label macro F1 | 97.25% | 97.25% |
| English F1, 525 reference spans | 97.99% | 97.99% |
| Taglish F1, 315 reference spans | 98.25% | 98.25% |
| Negative passages with false positives | 0 / 103 | 0 / 103 |

| Label | Training reference spans | Original and shadow F1 |
|---|---:|---:|
| BARANGAY | 85 | 100.00% |
| CITY | 308 | 99.35% |
| LANDMARK | 58 | 91.23% |
| LOCAL_AREA | 19 | 97.30% |
| PROVINCE | 169 | 99.12% |
| ROAD | 201 | 96.50% |

All six labels have reference support in both training languages. Negative supports are 38 English and 65 Taglish. [Complete class/language precision, recall, F1, supports and negative errors](metrics.json) · [Rule/family dispositions and counts](summary.json).

## Verification and preservation

**269 fresh tests pass, including 71 new boundary-study checks.** The 24 fictional core cases cover three behaviors × English/Taglish × supported action, valid-location counterexample, ambiguity and Unicode/repeated mentions. Eighteen have definitive references; six ambiguous cases remain unscored. Constructed fixtures stay outside corpus membership.

Tests cover compounds, crossing connectors, ambiguous adjacency, hyphens/slashes, direction words, non-ROAD preservation, contained children, overlap rejection, reference separation, null references, stale bindings, occupied destinations, concurrency and blocked model/network/training execution. The study uses existing Python 3.12 saved-span arithmetic; no dependency was installed or neural model loaded.

A separate training-only replay reproduces **all ten output files byte-for-byte**. All individual, combined and qualifying-subset metrics equal the original baseline; all 345 original-prediction decisions were checked. This replay is unrelated to the consumed prior validation comparison, which was neither opened nor rerun.

**507 protected file hashes** remain unchanged. **55 completed-holdout entries and 27 prior-validation entries** were checked through size/mtime metadata only; their content was not supplied to this study. Private coordination contains source-bound ROAD reviews, complete saved training articles, frozen implementation/test copies, grant/protocol and reproducible hashes. Study/replay packages contain the fictional cases, immutable shadow decisions, transitions, metrics and manifests. Individual training texts, annotations, source identities and predictions remain ignored by Git. [Verification and exact preservation counts](verification.json).

## Completion

Close this bounded feasibility study with **partially supported trimming and splitting, zero qualifying rules and no measured improvement**. Retain v19 control and keep these prototypes separate from production. Do not launch another validation comparison, expand rules from exposed findings or reinterpret no-op agreement as success. Any future development direction requires a separate task.

This work was motivated by exposed validation findings and is not blinded. References remain **AI-assisted silver**, with incomplete-history/accounting limitations; training agreement does not establish generalization. Data, annotations, partitions, tokenizer, models, historical results, frozen type safeguards and production extraction remain unchanged. No new articles/passages, exports, neural inference, training, validation rerun, holdout access, integration, upload, commit or push occurred. The desktop can remain off. [Operator guide](../../guides/ner-road-boundary-study.md).
