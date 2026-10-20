# Remaining NER extraction gaps — assessment complete

> **Last Updated:** October 19, 2026, 9:41 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**All seven missed associations and three held references have evidence-backed dispositions.** This assessment changes no model, source, reference, saved output or score. It does not clear a LANES connection. The intended output remains location, flood depth and observation time grouped by the report's actual observations.

## What the saved errors mean

The seven links involve **three target occurrences across three training passages**: two exact-boundary mentions have incorrect types; one mention is absent with no overlapping neural prediction. No boundary correction is supported by these three cases. These are three occurrences, not seven missing locations or seven flood events.

| Private case alias | Recognition finding | Missed keys | Effect on requested output |
|---|---|---|---|
| A | Exact road span typed as a landmark | One access | This statement concerns a landslide closure, not an observed road flood. A different location's explicit flood depth remains correctly linked. There is no supported flood depth or observation clock to fill for this road. |
| B | Named transport asset absent | Local depth, local status, local access, collective depth inventory | Relative depth and passability text survive as unassigned facts. The location is missing. The adjacent row retains its own linked depth. No passage-local observation clock is supplied. |
| C | Shared locality numeral typed as a road instead of a local area | Collective depth and collective status | Indoor depth and active status survive as unassigned facts because the complete correctly typed location set is unavailable. Preserve the collective observation and indoor scope. |

The exact predictions, offsets, original article context and all seven individual dispositions remain in the ignored owner-private assessment package. Public reporting omits source text, identities and per-source error identifiers.

### Individual association accounting

| Link | Kind | Saved evidence and disposition |
|---|---|---|
| A1 | Access | No access fact is emitted for the non-flood closure; its exact target also has the wrong type. Retain the miss and investigate the general access cue separately if required. |
| B1 | Access | Access fact recognized, but unassigned because its target mention is absent. |
| B2 | Depth inventory | Cross-row null collective inventory absent; both raw depth expressions survive. This inventory is not an additional physical measurement or a uniform depth for all rows. |
| B3 | Local depth | Relative depth expression and fact recognized but unassigned. |
| B4 | Local status | Local status fact absent as well as its target mention; downstream recovery has not been demonstrated. |
| C1 | Collective depth | Depth fact recognized but unassigned because the jointly described target set is incorrectly typed. |
| C2 | Collective status | Status fact recognized but unassigned for the same target-set problem. This is another link for the same observation. |

**Important correction to the earlier shorthand:** absence of the exact typed target explains why strict reference links cannot be satisfied, but it is not proof that repairing the mention alone fixes every downstream omission. Case A also lacks an access fact; case B lacks a local status and the collective inventory. No counterfactual repair or extractor rerun was performed.

None of these seven errors is a missed TIME association. This does not establish error-free time extraction. Class-suspension days, report days and publication timestamps must not be substituted for missing observation clocks. Full-source clocks outside the supplied passage are documented as context, not silently injected into the saved extraction.

## Held references and language evidence

All three references remain held and outside resolved-reference scoring. Source-supported proposals are recorded separately; existing references and scores remain unchanged.

| Hold | Assessment | Disposition |
|---|---|---|
| Holiday-meal/event timing | The wording does not itself establish a precise flood-observation clock or calendar date. Separate explicit flood/access statements remain source evidence. | Retain the hold; propose preserving the wording as source context until its temporal annotation convention is settled. |
| Depth aliases and updates | The source explicitly distinguishes earlier and later depth/time pairs and a separate city recession update. The unresolved issue includes span/alias conventions and complete relation encoding. | Propose separate raw observations and a separate recession statement; retain the hold pending a frozen reference clarification. Do not overwrite earlier values with the latest depth. |
| Vague depth and translation | Both original and translated vague depth occur in the source. Neither supplies a numerical gauge or precise affected road. City flooding, recession and later neighboring-area measurements have distinct scopes. | Propose unspecified raw depth with unresolved exact target; retain the completeness/translation hold. Do not borrow the neighboring measurement. |

The existing eligible reference subset contains **11 English and 12 Taglish passages**, with **zero pure-Tagalog eligible passages**. Previously recorded fictional checks passed English 90/90, Tagalog 58/58 and Taglish 90/90. Those are historical constructed checks, not fresh tests or measurements of real-world Tagalog accuracy. A held article containing Tagalog does not create a qualified, scored pure-Tagalog evaluation. Language classifications remain AI-assisted, with borrowing/classification uncertainty.

The earlier 96.55% association F1 remains an exposed silver training-subset result. It is unchanged and is not new generalization evidence. The trained model still recognizes six location classes; rules recognize DEPTH/TIME and match facts to locations. Learned DEPTH/TIME remains unfinished.

## Authentication and preservation

- Verified the existing v38 grant and linked request/protocol, v37 references, execution/analysis manifests, saved v19 seed-0 training prediction manifest and prediction bytes.
- Joined the three reviewed cases by opaque identity, unchanged text/hash, reference hash, output hash, original article window and exact Unicode source slices. Every supplied mention matches its saved neural prediction and provenance; v38 did not add, resize or retag it.
- Verified source-use identity/extents for all 26 existing training counterparts. Reviewed complete embedded source context for the three error cases and three held records. Source-use permissions were not expanded and no external retrieval occurred.
- **208 hash-bound files** remain byte-identical. **1,539 historical protected entries** and **82 excluded validation/holdout entries** retain size/mtime metadata; the latter comprise 27 validation and 55 holdout entries. These sets overlap and must not be summed as unique files.
- Historical mixed-split packages receive metadata checks only. No fresh byte-verification claim is made for all historical artifacts. No validation/holdout contents were opened, including for hashing.
- Seven unique error IDs, three target occurrences and three held records reconcile exactly, with individual dispositions and unchanged historical errors. Source and evidence slices validate.

Verification used standard-library saved-evidence checks, **not model inference, extraction, training or a new software test suite**. Historical test counts remain historical. The private ledger and reproducibility scripts are under the Git-ignored `extraction-gap-assessment-20261019-v39` artifact package. Pulling Git alone will not transfer them. [Aggregate verification](verification.json).

## Recommended next task

**Separately scope a training-only recognition feasibility study**, prioritizing missed transport assets and shared locality designators because these prevent grouping the requested flood fields. Include exact road typing as a distinct family, with the non-flood access cue tracked separately rather than forcing it into a flood record.

Use the existing training evidence and fictional positive/counterexamples. Preserve source spans and all frozen references; do not automatically introduce postprocessors, model changes or fallback. A later proposed method must freeze its behavior and downstream checks before any separately authorized comparison. Check both required positive recovery and retention of supported correct links, qualifiers and scope. Decide whether any repair is justified from that evidence; another training run is not automatically required.

The held reference conventions need a separate clarification proposal before their scoring eligibility can change. Real pure-Tagalog performance remains an explicit limitation; measuring it requires a separately scoped suitable evaluation. These limitations must accompany any later connection proposal.

Assessment is complete, including retained unresolved cases. No new articles, corpus changes, inference, model/extractor repair, public API/schema/UI change, database write, application connection, upload, commit or push occurred. Preserve 345 training / 60 validation / 60 research-holdout membership and all predecessor artifacts.
