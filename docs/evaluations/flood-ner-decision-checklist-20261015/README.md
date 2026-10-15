# Source-use decision checklist preparation — October 15, 2026

Checklist preparation is complete. Actual researcher decisions, source admission and other-use outcomes remain unresolved.

## Deliverables

The private, ignored checkpoint is backend/training/flood_ner/artifacts/academic-decision-checklist-20261015-v1:

- [Decision checklist](../../../backend/training/flood_ner/artifacts/academic-decision-checklist-20261015-v1/CHECKLIST.md): publisher questions, next actions, saved evidence links and blank researcher fields.
- [Article register](../../../backend/training/flood_ner/artifacts/academic-decision-checklist-20261015-v1/article-register.csv): exactly 139 article rows, all 400 sample memberships, saved recommendations/actions, AI provenance and hash-bound evidence.
- [Verification record](../../../backend/training/flood_ner/artifacts/academic-decision-checklist-20261015-v1/verification.json), input/evidence references and a SHA-256 manifest.

Private links require the local checkpoint and are not distributed through Git. This report contains metadata only; it copies no article text, private access facts or completed decisions.

## Reconciliation

| Publisher | Recommended articles / passages | Held articles / passages |
| --- | ---: | ---: |
| GMA | 70 / 157 | 1 / 3 |
| ABS-CBN | 0 / 0 | 50 / 158 |
| Philstar | 0 / 0 | 18 / 82 |
| **Total** | **70 / 157** | **69 / 243** |

All 139 articles and 400 memberships reconcile with no duplicates or omissions. The 157 recommended passages do not meet the required 400-sample cohort. English/Taglish remains 200/200; training/validation/testing remains 280/60/60; all 40 contextual-v3 pairs remain paired to the frozen training records.

## Verification

- Existing validate_decision_proposal passes using the existing isolated GPU research interpreter; no dependency or environment change.
- All nine required proposal bindings, all nine used evidence records (including saved file/clause hashes) and all 31 proposal packet files verify.
- Independent Python CSV parsing compares every exported field, sample membership, evidence pointer and proposal JSON pointer to the saved proposal. Artifact-tool workbook values, error scan and preview also pass.
- Original annotations, contextual pairs, partitions, decision forms, source-use flags, model/tokenizer and GPU checkpoint files, preexisting desktop work and .env remain byte-identical. The three core documents receive only the new preparation record and timestamp; their prior bodies are retained verbatim.
- GPU evidence remains unchanged: 71 checkpoint files and 73 installed packages. No GPU qualification, model inference, export, training, deployment or external message was performed.
- Three historical audit references remain absent, as already reported in the [restoration checkpoint](../flood-ner-desktop-restore-20261015/README.md). They are listed separately in the private checklist/verification and do not block checklist preparation.

[Metadata and output hashes](summary.json) record the final validation. [Report hash manifest](manifest.json) binds this README and summary.

## Next task

The researcher must record the actual decision-maker, date, exact article scope, adopted basis, supporting evidence and explicit exception dispositions. Decide the 70 recommended GMA articles and AFP-credit case separately; resolve ABS-CBN contractual/website-use applicability separately from the proposed exception rationale; resolve Philstar copying/derivation and opinion/QA-source cases.

Publisher replies remain optional evidence, not a universal prerequisite. All decisions stay unfilled here. Supported admission remains a later, separate step, followed by news-cohort tokenizer qualification, export and training under the existing task plan. Public demonstration/deployed inference and other distribution scopes remain separate.
