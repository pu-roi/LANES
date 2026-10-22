# Pilot preparation: source readiness and draft passage queue

> **Last Updated:** October 14, 2026, 1:26 PM (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Initial research-only review queue delivered. Reuse admission, semantic group review, passage selection/language review and labels remain pending.

**Later conditional readiness audit:** [Review and corrected queue](../flood-ner-readiness-review-20261014/README.md) verifies all 100 source-exact windows, fixes candidate identity/hold validation, preserves source-review notes and records editorial diagnostics. The expanded suite passes 378 checks. The latest queue is review-queue-v3/; the original v1 remains preserved. Readiness is still open, so no annotation/training advancement is claimed.

After the completed-work audit, the developer authorized proceeding to the next task. Prepared one contiguous draft context window from each of the 100 reviewed news articles, inventoried publisher reuse evidence and retained the 37 proposed event buckets for review. This prepares a review queue; it does not close the pilot-readiness gate or create a balanced/admitted annotation corpus.

## Deliverables

- [candidate_register.json](candidate_register.json): 100 source-exact draft windows with article/source identity, version/hash, publication day, offsets, passage hash, article-level language, research cues and explicit holds. Full source/passages remain only in ignored artifacts.
- [group_review_queue.json](group_review_queue.json): 37 conservative proposed event buckets and their article IDs. Every group remains pending; no train/dev/test membership is assigned. Month-wide rain buckets may merge different episodes, and unidentified copied or syndicated reports may connect other buckets. Review source chronology and actual event/syndication evidence before freezing splits.
- [reuse_register.json](reuse_register.json): five publisher assessments covering all 100 sources, linked to eight primary publisher-policy references with retrieval times and verified raw snapshot hashes. No training basis has been recorded or source admitted.
- [readiness.json](readiness.json): measured counts and holds. Article tags remain English 64, Tagalog 33 and Taglish 3; **all 100 passage languages remain unknown pending review**. Zero labels, assigned splits, training-admitted passages or reviewed split groups.
- Offline `prepare-pilot` command and versioned `lanes-flood-ner-candidate-v1` contract. Full candidate JSONL and policy snapshots live under ignored backend/training/flood_ner/artifacts/readiness-20261014/. The final queue is review-queue-v1/; prior proposal folders are preserved.

## Source-use evidence

| Publisher | Articles | Evidence inspected | Admission conclusion for this queue |
|---|---:|---|---|
| GMA News | 88 | [User policy](https://www.gmanetwork.com/news/user-policy/) describes personal, educational and noncommercial viewing/downloading. [AI policy](https://www.gmanetwork.com/news/artificial-intelligence-policy/) describes newsroom AI review/publication practices. | Educational access is documented; the exact intended training/model/data redistribution basis remains unrecorded. |
| ABS-CBN | 5 | [Terms](https://www.abs-cbn.com/terms) reserve content rights and condition copying/derivative uses on express permission. [AI policy](https://www.abs-cbn.com/ai-policy) addresses internal INCA staff/editorial workflows. | No recorded training basis; internal AI practice is not a third-party license. |
| RMN | 5 | [Terms](https://rmn.ph/terms-and-conditions/) describe limited personal noncommercial transitory viewing and restrictions on reproduction, modification and transfer. | Intended training/reuse scope needs a documented basis. |
| Philstar | 1 | [Copyright notice](https://www.philstar.com/copyright-notice) permits limited personal noncommercial downloading and requires permission for broader reproduction/distribution. | No recorded training basis. |
| Daily Tribune | 1 | [Privacy](https://tribune.net.ph/privacy) and [editorial standards](https://tribune.net.ph/editorial-standards) reviewed. | No applicable content-training grant identified in these pages; scope remains unknown. |

This is a policy-evidence inventory, not a determination about applicable legal exceptions or the legality of a specific training use. Research access, raw-text/data redistribution, training and later deployment/model distribution have different intended-use questions. The publisher's own use of AI does not itself establish permission to train LANES on its content. Original source reuse/admission metadata remains unchanged. No publisher was contacted, permission requested or granted, and no raw dataset was published.

## Selection and remaining review

The proposal uses the previously reviewed body anchor and an adjacent short heading where appropriate, retaining contiguous source characters and following paragraphs up to a soft context limit. It retains source text exactly, including LF/CRLF, and maps only research-cue offsets into passage coordinates. Caption/frontmatter residue and incomplete scope remain possible; every passage carries an editorial-bounds hold. These drafts must be inspected and adjusted before complete annotation, rather than treated as negative examples because they have no labels.

The queue deliberately represents all 100 articles for review. It inherits GMA dominance and the three article-level Taglish tags; it is not a balanced 100-passage pilot selection. Passage-level language is not inferred from publisher/URL/article tags. Only six draft windows currently contain the recorded numbered-locality cues (eight articles contained such cues somewhere in their full body). Longer or alternate windows are needed for some later facts. Missing high-number/borrowed-written-number/abbreviation/Roman/suffix/combined-address, shared-exception and negative/forecast slices remain open. The separate official directory/Wikipedia inventory remains outside the primary news queue.

Two legacy sources retain their original HTML/retrieval gaps; the preceding [audit](../flood-ner-review-20261014/README.md) corroborates their publication evidence and records Philstar's conflicting AMP structured date. This queue does not rewrite those immutable source records. These issues remain visible in review holds and the source audit.

Next review work is to establish the planned reuse basis, review passage boundaries/languages and replace or supplement missing slices, then qualify event/revision/syndication groups. Only after those gates should the final pilot be selected and annotated. The exporter rejects provisional group placeholders and research-only sources. CandidatePassage is a separate schema without entities/facts/relations/split fields; it cannot be consumed as accepted AnnotationRecord training data.

## Verification

**371 focused checks passed in 23.73s**, including nine new candidate-preparation checks plus the existing source/tooling/PSGC/number/locality/heading/temporal/replay/source-validation/processing suite. New checks cover source-exact LF/CRLF offsets, heading context, cue relocation/hashes, schema round trips, rejection of corrupted or prematurely admitted candidates, deterministic outputs, no full text in metadata registers, preservation of prior queues and refusal to write raw candidates outside ignored artifacts.

The actual command reverified the 100-article source register before preparing windows. All 100 full JSONL candidates round-trip through the strict candidate contract, reference distinct reviewed articles and retain research-only admission. All eight policy snapshot hashes pass. Existing source captures and the original news register remain unchanged. Tests use the isolated source_rules configuration with empty provider credentials/unreachable test-only PostgreSQL and existing in-memory fixtures. No operational database, model selection/training, dependency/schema change, runtime publication, deployment, commit or push occurred. The existing spaCy/Click deprecation warning remains.

See [tooling](../../../backend/training/flood_ner/README.md), [annotation guide](../../guides/flood-ner-annotation-v1.md), [roadmap](../../plans/lanes-ner-training-plan.md) and the [completed-work audit](../flood-ner-review-20261014/README.md).
