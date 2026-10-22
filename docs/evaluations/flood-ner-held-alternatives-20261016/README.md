# Alternatives for the seventeen held NER passages

Completed October 16, 2026. Project attribution: [@roicambe](https://github.com/roicambe) (Roi Cambe).

**A smaller 400-slot proposal is conditionally feasible with all 383 unaffected records fixed.** It retains five existing Dolomite windows and proposes twelve new complete-sentence windows. The proposed aggregate selects 2,057 characters instead of 3,087 across the same four held articles. The twelve new windows are drafts: their language and complete location annotations still require review. No dataset was replaced or admitted.

The current accepted research dataset remains **cohort-v4: 400 passages from 138 articles**, with contextual-v4's 40 pairs, 200 English/200 Taglish and 280/60/60 partitions. Current project-use dispositions remain **134 adopted article bases/383 passages and four held articles/17 passages**. Training admission/export remain zero. The detailed desktop predecessor remains unavailable and unreconciled.

## What the finite scenarios establish

| Scenario | Result | Limitation |
|---|---|---|
| Unused reviewed alternatives only | Solver-proven infeasible in this finite scenario | Twenty Philstar Taglish reserves exist; nineteen have complete existing annotations. Overlap and label-support constraints prevent filling all seventeen slots. |
| Reviewed alternatives plus retained windows in changed article scopes | Verified 400-slot annotation/quota witness | The changed selection increases total selected text to 4,619 characters; it is not the recommended reduction and does not resolve source use. |
| Five retained windows plus twelve new sentence proposals | Conditional 400-slot witness | Every hard quota passes if the provisional language and labels are accepted. Selected text falls to 2,057 characters. This is a proposal, not a reviewed revision. |

Each solver call used the 60-second bound and completed with status 0 or 2; no 300-second retry was needed. Stable inputs and ordering reproduce the reviewed and conditional outputs byte-for-byte. Solver optimality applies to its finite objective, not to the globally smallest or best possible corpus revision. No global minimum or model-performance claim is made.

ABS-CBN and GMA each already contribute 160 fixed samples, their publisher maximum. With every unaffected record fixed, all seventeen slots must therefore be Philstar Taglish training samples. A new publisher would need at least 25 samples in each language, which cannot fit those slots. The fixed Taglish training records have 54 ROAD spans/26 positive passages and 16 LANDMARK spans; the proposed Dolomite windows provide the missing six ROAD spans/four passages and four LANDMARK spans. All other label, publisher, article, group and partition checks also pass.

Verified the saved 1,340-record pool, 110 additional accepted windows and current annotations as a 1,450-record union with 1,050 unused records. The twenty unused reviewed Philstar Taglish windows all come from the four held editorials. Read their complete text and source context; one older first-paragraph annotation omits Estero San Antonio Abad. That historical record is preserved and excluded from verified witnesses. A later, already reviewed overlapping alternative includes the missing occurrence. Structural validity alone did not establish annotation completeness.

Four explicit omitted content intervals ensure the tested selections change actual article coverage. Changing only record IDs or repartitioning the same text cannot satisfy these scenario guards. The guards are analysis choices, not assertions that those omitted intervals are legally forbidden.

## Proposed scope changes

| Held article | Current samples / characters | Conditional samples / characters |
|---|---:|---:|
| Dolomite Beach editorial | 8 / 1,468 | 5 / 961 |
| Logging/landslide editorial | 3 / 629 | 5 / 503 |
| Pera sa bulsa, bangkay sa baha | 5 / 694 | 6 / 429 |
| Hindi baha…kundi kurapsyon | 1 / 296 | 1 / 164 |
| Total | 17 / 3,087 | 17 / 2,057 |

All proposed new boundaries are manually screened complete sentences, including questions and qualified allegations. Source text, soft hyphens and nonbreaking spaces remain unchanged. Source-bound projection supplies three provisional place spans: Batangas, Agoncillo and Maguindanao del Norte. Nine draft windows project no named location. No location is inherited from adjacent prose, and historical dates, counts, generic barangay and institutional names do not become unsupported place labels.

Taglish is provisional under the existing Filipino-plus-untranslated-English lexical convention. Each draft records actual lexical evidence; proper names alone do not establish mixing. In particular, the VIP-only mixing case needs language adjudication. A rejected language or incomplete annotation invalidates the conditional witness until an eligible replacement is reviewed. Twelve of the permitted forty proposal slots were used; the earlier 120-window annotation checkpoint was not reopened and new annotation acceptance is zero.

## Source-use and contextual work still needed

The four changed article selections require explicit scope-specific reassessment, including the five retained windows. Smaller amounts and quota utility do not establish a supported use basis. The logging and corruption examples retain causal or rhetorical editorial expression; the remaining Dolomite windows still include an alleged causal link, project criticism and a mangrove recommendation. Analytical necessity and qualitative importance need actual consideration. Complete article bodies and existing working/archive copies remain retained; the selected-text reduction does not reduce those copies or resolve contract and market uncertainty. Acquisition remains Unknown / Codex collected and retention remains undecided. No new permission or legal assessment is claimed here.

Both held contextual pairs would be replaced in the shorter proposal: revision3-13d600f079388082fadb and revision3-d44c297c267072d6ac6b. Preserve the other 38 pairs exactly. Those 38 already meet all category supports and article minimums: 20 English/18 Taglish, with 14/17 articles. Two freshly reviewed Taglish training pairs are still necessary to restore 20/20. Their missing clocks or targets must remain unknown. Forty paired records do not increase the passage count to 440.

**Recommended next task:** review the twelve draft windows' language and all location occurrences, assess the four complete proposed article selections, and prepare two contextual replacements. Assemble a separate revision only after the 400/40 annotation and quota checks pass; applying supported admission remains separate. This is a bounded follow-up to a concrete proposal, not another unchanged review of the original held scopes.

## Verification and files

Verified exact preservation of the 383 fixed records, including metadata and partitions, all sixty test samples and ten pilots. Both witnesses pass independent source-offset, Unicode, saved-tokenizer, duplicate/near-copy, overlap, grouped-leakage and full coverage-policy checks. Drafts remain incomplete and unaccepted. All current research-only records still refuse export before an output directory is created.

The verification packet records seventeen direct negative artifact checks, deterministic replay, 2,839 preserved checkpoint files, 35 unchanged existing tooling files and all 23 model hashes checked without loading a model. These are artifact checks, not pytest results or evidence of legal/content adequacy. No reusable code changed and no pytest suite was rerun; **772 passed/one skipped remains the historical software baseline**. See [verification](verification.json) for measured checks and [status](status.json) for separate outcomes.

The ignored packet is `backend/training/flood_ner/artifacts/held-alternatives-20261016-v1/`. START-HERE.md explains the reviewed witness, conditional proposal, replay instructions and hashes. Tracked deliverables contain metadata and original analyst prose only: [candidate register](candidate-register.json), [exclusions](exclusion-register.json), [proposed 400 slots](conditional-selection-register.csv), [four article links and scopes](article-scope-changes.csv), [quota results](quota-results.json), [context impact](context-impact.json), [next-review work](next-review.json) and [paper-method notes](paper-method-notes.md).

No collection, current-dataset replacement, admission, model inference/training, GPU change, message, upload, deployment or Git publication occurred. The isolated desktop GPU setup is already complete; it is not repeated by this feasibility task.
