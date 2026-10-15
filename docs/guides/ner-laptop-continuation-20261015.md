# LANES laptop continuation — October 15, 2026

Updated: October 15, 2026, 6:44 PM (Asia/Manila). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Resume the same source-use task

The current completed record is academic-project-decisions-20261015-v1: Codex, acting under explicit researcher delegation, adopted the existing private academic-use recommendation for 70 GMA articles / 157 passages. The AFP-credit GMA article, 50 ABS-CBN articles and 18 Philstar articles remain held: 69 articles / 243 passages.

All 139 articles / 400 memberships, 40 contextual-v3 pairs, 200 English / 200 Taglish and 280 training / 60 validation / 60 testing partitions remain unchanged. Admission and exports remain zero. Six paper-excerpt/dataset-distribution outcomes remain separate and pending before those uses; six production/model-distribution outcomes remain deferred.

**The approved official-source review of the 69 holds is unfinished.** Preliminary web browsing and local inspection occurred, but no dated/hash-bound new research snapshots, completed 69-article reassessment or academic-project-decisions-20261015-v2 checkpoint were saved. Re-fetch and bind evidence on the laptop before revising decisions. No additional hold has been lifted.

Current references:
- [Delegated decision checkpoint](../../backend/training/flood_ner/artifacts/academic-project-decisions-20261015-v1/README.md)
- [Decision checklist](../../backend/training/flood_ner/artifacts/academic-decision-checklist-20261015-v1/CHECKLIST.md)
- [Metadata-only decision report](../evaluations/flood-ner-project-decisions-20261015/README.md)
- [Current task plan](../task_plan.md)

## Transfer and preserve local work

The desktop repository is E:/Files/Documents/GitHub/LANES on roi-branch. Discover the actual laptop checkout; do not assume its drive or directory. Inspect its branch, Git status and existing artifacts before synchronizing. Preserve laptop and desktop uncommitted work and local backend/.env edits. Do not reset, force-pull or overwrite differing files.

A local transfer ZIP is prepared under backend/training/flood_ner/artifacts/laptop-handoff-20261015-v1:
- LANES-laptop-continuation-20261015-v1.zip
- LANES-laptop-continuation-20261015-v1.zip.sha256
- [Handoff report](../../backend/training/flood_ner/artifacts/laptop-handoff-20261015-v1/handoff-report.json)
- [Transfer manifest](../../backend/training/flood_ner/artifacts/laptop-handoff-20261015-v1/transfer-manifest.json)

This is a delta package: the two new private desktop checkpoints plus current documentation snapshots. It does not contain the complete research corpus, older proposal/evidence dependencies, models, configuration secrets or a Python environment. The laptop must already have, or separately restore, the original corrected study/proposal/evidence artifacts. Check all nine proposal bindings before continuing.

Copy the ZIP and checksum through a private owner-only channel. Verify the archive SHA-256 and member hashes before restoring. Entries use repository-relative paths, including backend/training/...; extract relative to the repository root without adding an extra backend directory. Skip identical files, restore missing files, and report differing hashes before overwriting. Tracked documentation snapshots are for comparison/manual merge when the laptop has its own edits. Keep private checkpoint files ignored.

The handoff report records the state when the local package was created; it does not confirm Git publication, cloud upload or laptop restoration. Synchronize tracked code and documentation through roi-branch separately. The transfer package must be copied privately; Git does not carry the ignored checkpoints.

The previous review found no actionable issue in the completed decision checkpoint. Its separate broader-diff finding remains open: a populated SMTP credential is present in tracked backend/.env. Preserve the local configuration, keep it out of any commit/transfer, and resolve that publication issue before using the repository's stage-all push procedure. No credential is reproduced in this guide or ZIP.

## Environment and research boundaries

The measured RTX 3060 Ti GPU environment belongs to the desktop. Preserve it there; do not copy its virtual environment to the laptop or assume the laptop has the same GPU capability. Official-source research and evidence review do not require running a model or installing desktop GPU dependencies. Use an existing compatible laptop research interpreter for the read-only validator after checking it.

Continue official-source research for:
1. AFP-credit GMA: verify the credit, selected passages and applicable rights/terms; assess independently of GMA's general policy. Do not automatically apply AFP-platform contracts or French-law exceptions to the GMA-hosted story.
2. ABS-CBN: separate the copyright/statutory-exception analysis from website-use/contractual applicability; individually address the Reuters-origin lead and AFP-caption wording.
3. Philstar: assess personal copying, research derivation and repeated copies; individually review the eight opinion sources and verify QA-host notices/provenance.

Primary-source starting points are research leads, not completed v2 findings:
- [Amending legislation, RA 10372](https://elibrary.judiciary.gov.ph/thebookshelf/showdocs/2/53393)
- [IPOPHL fair-use guidance](https://www.ipophil.gov.ph/news/ipophl-releases-statutory-fair-use-guidelines-to-clarify-rules-on-copyright-exceptions/)
- [ABS-CBN terms](https://www.abs-cbn.com/terms)
- [Philstar agreement](https://www.philstar.com/member-agreement) and [copyright notice](https://www.philstar.com/copyright-notice)
- [AFP platform terms](https://www.afp.com/en/useful-links/terms-use)

Distinguish current terms from capture-date evidence, evaluate all four fair-use factors and record missing facts/inferences. Adopt a revised basis only where supported; otherwise retain the hold with the precise unresolved question and evidence needed. Publisher replies are optional evidence, not a universal prerequisite. Do not invent human review, publisher permission or legal approval.

Record the research in an ignored academic-project-decisions-20261015-v2 checkpoint, preserving v1, the adopted GMA subset and every historical proposal/form. Include dated/hash-bound evidence and all 139 article decisions. Reconcile all 400 memberships, nine original bindings, every new reference and original read-only proposal validation. Preserve annotations, contexts, partitions, source-use flags, model/tokenizer checkpoints, GPU environment and .env.

Update the existing task-plan item, progress and index with the actual outcome. Keep finalization open for unsupported required articles. The 157 adopted-basis passages cannot replace the 400-sample cohort. No admission, export, training, deployment, API/schema/dependency change or external correspondence is authorized in this research step.

## Prompt to use on the laptop

```text
Continue the existing LANES source-use checkpoint on this laptop. Read AGENTS.md,
DESIGN.md, docs/task_plan.md and docs/guides/ner-laptop-continuation-20261015.md.
Verify the actual checkout, feature branch, Git status and private artifacts;
preserve local work and backend/.env. Restore the two new private checkpoints
from the verified laptop handoff ZIP if missing; skip identical files and report
conflicts before overwriting. Verify all nine original proposal bindings.

The authoritative completed state is academic-project-decisions-20261015-v1:
70 GMA articles / 157 passages have the delegated narrow recommendation adopted;
69 articles / 243 passages remain held. There is no completed v2 checkpoint.
Continue the already approved official-source research for those 69 holds:
AFP-credit GMA, ABS-CBN contractual/origin/caption questions, and Philstar
copying/derivation, eight opinion cases and QA-host provenance. Distinguish
statutory exceptions from contract applicability and current from capture-date
terms. Record actual evidence, four-factor reasoning, uncertainty and precise
remaining actions. Revise a disposition only when supported; otherwise retain it.

Save an ignored academic-project-decisions-20261015-v2 with dated/hash-bound
evidence and updated decisions for all 139 articles. Preserve all prior records
and frozen 400 memberships/40 contexts/partitions. Reconcile counts and bindings,
run the existing read-only proposal validator, and update the same task-plan
item, progress and documentation index. Keep finalization open where unsupported.
Keep the six paper-excerpt/dataset-distribution outcomes separately pending.
No admission, export, training, deployment or external messages; preserve the
desktop GPU environment and do not copy its virtual environment to this laptop.
```
