# Retained v19 runtime qualification and shadow integration design

> **Last Updated:** October 19, 2026, 2:58 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Requirements checkpoint before the next integration task

The offline comparison is complete; the original learned DEPTH/TIME objective remains unfinished. Consult [current tasks](../task_plan.md#current-ner-scope-and-defense-checkpoint) before implementing the association seam. The proposed October 25 interim hybrid uses location NER with existing depth/time rules; it does not mean those fields were learned or permanently removed from the user's goal. Next proposed work is existing-data/context gap review and a bounded plan. This documentation update authorizes no integration, training or permanent scope reduction. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier implementation checkpoints below are historical.**

**Repaired offline location comparison completed.** One explicitly authorized new Linux attempt processed all **six saved training articles and eight fictional cases**. Independent verification reconciles every input/hash, Unicode span, label and comparison count. Startup **5.688 s**, slowest input **0.666 s**, peak worker RSS **450.79 MiB** and wall time **9.206 s** all pass unchanged limits. The previous failed attempt, source bindings and claim are preserved; its verified stopped-owner lock was archived. The successful attempt is stopped and its active lease is cleared. [Executed outcome](../evaluations/flood-ner-shadow-execution-20261019/README.md).

**Next:** separately design and test how location mentions associate with clause-local flood status, time, depth and uncertainty. No live processing is connected. Preserve all **345 training / 60 validation / 60 research-holdout passages**; no new data, retraining or validation/holdout evaluation occurred. The 604 passing software checks remain preparation evidence; this task adds actual execution and independent verification, with no source change or suite rerun. [Operator guide](../guides/ner-shadow-comparison.md).

**Earlier dated checkpoints below are historical.**

**Offline location shadow adapter implemented; comparison execution remains pending.** The single Linux attempt stopped during startup before processing any article. An ORM-import/engine-construction conflict is reproduced with a constructed probe. The repaired offline import boundary passes **604 checks / 62 new checks** and read-only preparation verification, but has not been rerun in Linux. Failed receipts, original source bindings, stopped container and lease remain preserved; no automatic retry occurred. [Outcome](../evaluations/flood-ner-shadow-comparison-20261019/README.md).

**Next:** explicitly reconcile the stopped failed attempt and execute one new offline comparison with the repaired grant and an absent destination. Only after that comparison completes should claim-context integration be scoped. Gate 3 remains passed for its earlier frozen Linux profile; the shadow-comparison gate is still open. No new data, training, validation/holdout evaluation or live connection occurred. Membership remains **345/60/60**. [Operator guide](../guides/ner-shadow-comparison.md).

**Earlier dated checkpoints below are historical.**

**Current result: local Linux CPU qualification passes.** V29 executes against Docker Desktop 4.95.0 / Linux engine 29.8.2; all 345 predictions match, fixed runtime limits pass and eight real fictional fault probes verify containment. No live adapter is implemented. [Executed evidence](../evaluations/flood-ner-linux-execution-20261019/README.md). Next separately implement the read-only shadow adapter. Earlier blocked/next-step statements below are preserved historical scope, superseded by this result; no training or holdout rerun follows.

**Historical v27 Linux attempt was blocked before image build.** The latest Docker startup log records an inaccessible ingest-socket rename; a normal restart did not produce a completed receipt and the Linux API remains unavailable. No Linux inference/performance or actual fault recovery is claimed. See the [v27 outcome](../evaluations/flood-ner-linux-qualification-20261019/README.md); preserve the passed Windows smoke and complete Gate 3 before a shadow connection.

**Historical pre-qualification checkpoint: Gate 3 was open; Gate 4 implementation had not started.** V19 corrected control seed 0 remains retained. Dataset membership is unchanged: 345 training / 60 validation / 60 completed research-holdout passages. The rejected type safeguards and unproven boundary prototype are not part of this design.

The Windows/Python 3.12 CPU smoke test passes using existing dependencies and fixed fictional inputs. This establishes a useful compatibility bridge from the research runtime, not Linux qualification, production performance or improved accuracy. [Measured outcome](../evaluations/flood-ner-runtime-preflight-20261019/README.md).

## Existing path and proposed seam

Current durable processing captures immutable article snapshots in `news_processing_service.py` and calls `news_discovery_service.extract_captured_news_article`. Its `_extract_article_inputs` constructs `HybridExtractionService`, calls `extract_hybrid(..., mode="rules_only")`, then resolves road placement and previews. The Taglish service currently obtains place mentions through `find_place_mentions` inside `extract_claims_from_sentence`; it also uses place mentions for title/heading/context handling. Separate Metro Manila/Pasig body-shortlist helpers call the rules extractor directly.

The next implementation should add an **offline shadow adapter**, initially outside durable processing. It should receive an immutable article body and emit location mentions plus diagnostic status, without creating reports, zones, database rows, provider requests or routing changes. Do not claim that placing a neural call in one caller replaces all location logic. Trace title, heading, caption, dateline, locality and shortlist paths before any later integration.

Proposed stages:

1. Verify a private inference artifact's checkpoint, tokenizer, vocabulary, runtime and implementation hashes. Load once per bounded worker; initialize no training pipeline or optimizer. The research checkpoint has desktop paths and a custom tokenizer registry. The smoke worker replaces the tokenizer factory in memory; it never edits the frozen config or imports training callbacks. A production artifact still needs a separate reproducible inference-only resource binding.
2. Run location recognition on unchanged article text. Return internal mentions with `start`, `end`, `text`, six-class `label`, model/tokenizer revision and source-text hash. Require `text[start:end] == mention.text`, Unicode character offsets, valid labels and non-overlap. No entity confidence should be invented from a hard label or reported F1.
3. Associate mentions with clause-local flood evidence through a separately tested context service. Preserve negation, forecast, historical/prevention status, clearing, temporal anchors, direction, depth ranges, passability and parent-location ambiguity. Mention recognition alone must never construct an `ExtractedClaim` whose default `flood_mentioned=True` implies a flood.
4. Compare shadow evidence with existing rules output without choosing labels from references. Record disagreements privately; errors remain visible. Do not compose rejected postprocessors or silently substitute rules while reporting neural success.
5. Only after a separately scoped acceptance decision, implement the app seam and deployment controls. Keep current production behavior intact until then.

## Six-label mapping

| NER label | Existing claim representation | Constraint |
|---|---|---|
| ROAD | `place_type="street"` | Road recognition does not establish a flooded segment or geometry. |
| BARANGAY | `place_type="barangay"` | Keep raw text; canonical parent identity needs evidence. |
| CITY | `place_type="city"` | Do not spread city facts to every road. |
| PROVINCE | `place_type="province"` | Broad mentions may remain context or unresolved. |
| LANDMARK | `place_type="landmark"` | A facility mention does not establish affected access roads. |
| LOCAL_AREA | retain six-class label internally; existing `local_area_raw` where supported | `PlaceType` has no local-area member. An unattached mention stays unresolved (`unknown` if projected); never coerce it to barangay/city. Decide any public schema extension separately. |

## Offset and identity contract

Use article-body offsets against the exact captured snapshot. The existing extractor strips the article body before sentence processing; feeding original-body NER offsets into that coordinate space would be unsafe. A future adapter must retain the original body, carry explicit sentence base offsets and require source-slice equality. If compatibility requires a stripped view, record its leading offset explicitly and translate once. Never normalize Unicode or use a first-occurrence search to relocate repeated names. Title/excerpt mentions need distinct text-field identities; their offsets cannot be passed as body offsets.

Preserve pipeline fingerprints, extraction leases, attempt ownership, prior results and idempotency. `crud/news_processing.py` currently hashes placement revisions into `rules-spatial-preview-v21` and uses mode `rules_only`. A neural pipeline identity must also bind model, tokenizer, context code and assets. **`NewsExtractionRun` has a database check constraint `mode = 'rules_only'`.** Do not relabel neural runs as rules-only to bypass it. Durable neural mode requires a separately approved schema/migration task; a file-only shadow adapter does not.

Provider-disconnect work remains separate. Shared source-hash/evidence helpers imported from `news_claim_auditor.py` must be extracted/qualified before removing the compatibility provider. Weather credentials and other ingestion functions remain outside this task.

## Remaining Gate 3 acceptance work

- Obtain a functioning Linux engine; pin the actual Python 3.12 image digest and resolved dependency identities. The current `python:3.12-slim` tag alone is not a reproducible runtime binding. Do not modify the existing backend environment or dependency list to bypass a failed check.
- Run with read-only asset mounts, no network, no database credentials, explicit CPU/RAM limits, one worker and a wall-clock timeout. Record host/image/runtime/architecture and thread settings. Python monkeypatches in the smoke probe are research guards, not an OS sandbox.
- Authenticate the exact checkpoint and qualify inference-only tokenizer/resource paths in Linux. Require tokenizer serialization/reconstruction equality and prediction parity against saved **training-only** v19 predictions, with exact opaque-ID/text joins. Supply no validation references/predictions or completed holdout content. Any mismatch stops qualification; it does not authorize retraining or relabeling.
- Freeze a representative training-only workload and the deployment resource envelope/latency thresholds before benchmarking. Cover English/Taglish, Unicode, repeated names, empty input, malformed types, long text and the current 100,000-character article limit. Define deterministic chunking with offset preservation before accepting articles longer than model capacity; never silently truncate.
- Measure cold startup including imports, model load, warm median/p95/max, throughput and peak RSS under the chosen concurrency. The current smoke load timer excludes imports and four tiny fictional inputs cannot establish an article SLA. No RAM figure has yet been measured.
- Exercise unavailable/mismatched assets, timeouts, crashes, worker restart, oversized requests and duplicate work. Return explicit extraction errors. No automatic CPU/GPU installation or hidden fallback.

Gate 3 passes only when this evidence and thresholds pass. Then separately implement and test the shadow adapter and compare claim meaning using constructed/captured development evidence. Database-backed replay, durable mode/migration, provider replacement, publication gates and deployment remain later scopes.

The system must retain evidence/time/status/depth/geometry/conflict/expiry checks and staff-visible uncertainty. A local model, OSM match, NOAH susceptibility or Pasig historical placement cannot prove a current flood or authorize routing avoidance. References remain AI-assisted silver with documented incomplete history/accounting; the completed holdout is not reopened.
