# Pilot readiness review: preparation gate remains open

> **Last Updated:** October 14, 2026, 1:42 PM (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Review completed; technical corrections verified. Not ready to advance to annotation/training.

The developer requested another double-check and permitted advancement only if ready. Re-read preparation code/tests, reverified the complete 100-candidate queue, audited passage-context diagnostics and all eight policy snapshots, and tested forged candidate metadata. The first preparation/collection/export rerun passed 126 checks, but adversarial probes exposed additional candidate-contract gaps. Corrections below are delivered; unresolved editorial/group/language/use-basis work prevents closing readiness.

## Corrections

- Candidate article keys now must match the captured source's normalized article identity. Candidate IDs must match the source ID/version and passage bounds; arbitrary or forged identifiers are rejected.
- Drafts must retain language/group/editorial/annotation holds, plus unresolved reuse and missing original HTML/retrieval holds where applicable. Removing mandatory holds no longer makes a draft appear qualified. Empty cue roles are rejected.
- Added explicit per-candidate diagnostics for publisher interface text, caption origin, source truncation and recorded numbered-locality cues outside the selected window. These are review signals, not automatic flood labels or proof that truncation is wrong.
- Carried the existing source-review notes into proposed passages. The source-observed crop-height versus flood-depth ambiguity now has an explicit measurement-role hold; that warning is not lost when selecting a passage.

Rebuilt the queue as ignored artifacts/readiness-20261014/review-queue-v3/. Earlier v1/v2 queues remain intact. All 100 candidate/source/text/hash/boundary identities match the original queue; only review metadata/holds were enriched. Source captures and the 100-news register are unchanged. Older authentic v1 records remain readable; forged identities or suppressed mandatory holds do not.

## Evidence and remaining defects of readiness

| Check | Result |
|---|---|
| Candidate source text/hash/offset reproduction | 100/100 pass |
| Publisher-policy raw snapshot hashes | 8/8 pass |
| Forged article key / forged candidate ID / missing mandatory holds | All three original probes now reject |
| Publisher interface text detected | 9 windows require review |
| Possible caption origin | 1 window requires review |
| Window ends before full source ends | 43 windows require scope/completeness review; truncation alone is not an error |
| Recorded numbered-locality cue omitted by window | 2 windows require expansion or an alternate passage |
| Known measurement-role ambiguity | 1 crop-height case requires explicit semantic review |
| Passage languages reviewed | 0/100 |
| Event/syndication groups qualified | 0; 37 provisional buckets remain |
| Training-admitted sources/passages | 0; no recorded training-use basis |

Flags overlap, and they are diagnostics rather than an accuracy benchmark. Source-exact text does not establish complete contextual evidence, valid training reuse or independent review. The queue also retains its known GMA/language imbalance and missing number/address/negative/shared-exception slices.

[audit.json](audit.json) contains each candidate's diagnostic flags and policy/probe checks. [candidate_register.json](candidate_register.json), [group_review_queue.json](group_review_queue.json) and [readiness.json](readiness.json) provide the corrected metadata queue. Full bodies remain ignored; no new entity/fact labels or train/dev/test memberships were created. Publisher-policy assessments remain in the [initial source-use register](../flood-ner-readiness-20261014/reuse_register.json).

## Verification and decision

**378 focused checks passed in 25.24s** after the final corrections: 16 candidate checks plus existing collection/export/source/PSGC/number/locality/heading/temporal/replay/source-validation/processing coverage. New checks cover candidate identity/provenance hold tampering, invalid cue roles, missing retrieval times, context diagnostics and preservation of known source ambiguity. Full candidates round-trip through the strict contract, reproduce the current proposal and retain research-only status; the original queue's source/text/bounds remain unchanged.

Tests used --noconftest and the existing isolated source_rules test environment with empty provider credentials/unreachable test-only PostgreSQL and in-memory fixtures. No operational database or training/export/deployment process was invoked. Dependency manifests and SQL schema/models remain unchanged; the existing spaCy/Click deprecation warning remains.

Do not advance to annotation/training from this review. Finish passage boundary/caption/interface-text and language review, qualify event/revision/syndication membership, fill necessary real-source slices and record the intended reuse basis first. The research-only queue is usable for that preparation work; it is not a completed pilot corpus. See the [roadmap](../../plans/lanes-ner-training-plan.md), [initial readiness packet](../flood-ner-readiness-20261014/README.md) and [offline tooling guide](../../../backend/training/flood_ner/README.md).
