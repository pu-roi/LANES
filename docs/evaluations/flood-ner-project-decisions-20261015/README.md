# Researcher-delegated academic-use project decisions — October 15, 2026

The existing source-use finalization task has advanced. **Overall finalization remains open for 69 articles / 243 passages.**

Codex recorded the following project dispositions under the researcher's explicit delegation and implementation instruction. The record claims no independent human reviewer, publisher authorization or legal approval and introduces no new legal conclusion.

| Case | Articles / passages | Recorded disposition |
| --- | ---: | --- |
| GMA recommended subset | 70 / 157 | Adopt the saved recommendation for owner-only private academic NER training/evaluation, with its recorded rationale, limitations and exceptions. |
| GMA AFP-credit case | 1 / 3 | Retain the hold; third-party-rights question unresolved. |
| ABS-CBN | 50 / 158 | Retain holds; website-use/contractual applicability unresolved separately from the proposed exception rationale. |
| Philstar | 18 / 82 | Retain holds; copying/derivation and opinion/QA-source questions unresolved. |

## Decision record and provenance

The versioned private checkpoint is [academic-project-decisions-20261015-v1](../../../backend/training/flood_ner/artifacts/academic-project-decisions-20261015-v1/README.md). It is ignored by Git and requires the local private artifacts.

- [decisions.json](../../../backend/training/flood_ner/artifacts/academic-project-decisions-20261015-v1/decisions.json) contains the delegation, actual actor/date, four case dispositions and all 139 article identities / 400 memberships, adopted rationale, saved limitations, evidence references and exception dispositions.
- The original AI proposals and three blank historical forms remain byte-identical. The original proposal validator still reports zero decisions within that historical proposal; the separate current record contains four delegated case dispositions.
- No human researcher name, signature, legal finding or publisher permission has been fabricated. Documentation attribution identifies the repository contributor, not an independent reviewer of the decision.

## Validation

All 139 articles and 400 memberships reconcile without duplicates or omissions. The 70/69 article and 157/243 passage totals are preserved. Every adopted-basis article is in the explicitly recommended GMA subset; the AFP article remains held. Adopted-basis fields stay null for the 69 holds.

The nine required proposal bindings, nine used evidence records, saved file/clause hashes, all 31 original proposal packet files and existing read-only proposal validator pass. Twelve negative validation scenarios reject scope expansion, invented human review, release of AFP, missing/duplicate memberships, evidence changes, loss of adopted rationale/exceptions, changed nonacademic outcomes, publisher-permission claims, admission and a false full-cohort claim.

Original annotations, all 40 contextual-v3 pairs, 200/200 languages, 280/60/60 partitions, source-use flags, model/tokenizer artifacts, GPU checkpoint, preexisting desktop work and .env are preserved. GPU verification includes 71 checkpoint files and 73 installed packages. The three missing historical audit references remain separately recorded and do not block this decision record.

[summary.json](summary.json) contains metadata and hashes; [manifest.json](manifest.json) binds this report. Detailed private results are in [verification.json](../../../backend/training/flood_ner/artifacts/academic-project-decisions-20261015-v1/verification.json).

## Remaining work in the same task

Resolve the AFP third-party-rights, ABS-CBN website-use/contractual and Philstar copying/derivation plus opinion/QA-source questions. The existing task-plan item stays unchecked and now records this partial progress. Publisher replies remain optional evidence.

The 157 passages with an adopted project basis do not satisfy the required 400-sample cohort. Supported admission, news-cohort tokenizer qualification, export and training remain separate subsequent steps. No source-use flag, admission or existing dataset membership is changed.

All six paper-excerpt/dataset-distribution outcomes remain separate and pending before those uses; the six production/model-distribution outcomes remain deferred. Their original twelve assessments are unchanged.

No export, model inference, training, deployment, dependency/API/schema change or external message was performed.
