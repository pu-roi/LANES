# Successor preparation under the approved research standard

> **Last Updated:** October 18, 2026, 10:14 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Adopted provenance standard

The user explicitly chose **“Use documented limitations: prepare 345/60/60 as an AI-assisted silver research comparison, explicitly acknowledging incomplete history and no certified-fresh test claim.”** This adopts option A from the [earlier decision proposal](ner-provenance-standard-decision-20261018.md). That historical proposal and its pinned audit remain unchanged.

The missing original search/transport evidence and incomplete historical collection scope are documented limitations for this research comparison. Their old verification flags remain false. This decision does not certify retrospective collection-budget compliance, exhaustive independence, human-gold annotation or measured model improvement. It does not authorize new collection, broader source use, upload, push or a training run.

The following is the concrete specification for the separate implementation task described by the adopted decision. This document records approval and preparation design; it does not itself admit records, freeze splits or serialize training data. No further decision about accepting these same provenance limitations is required.

## Fixed inputs and membership

- Use the latest validation-gap membership proposal as the authoritative development selection: 568 considered records, with exactly **405 propose_include / qualified_proposal_member** records, comprising **345 train / 60 dev**. Keep its **99 holds and 64 exclusions** outside membership. Do not combine that proposal with its 565-record predecessor as additional samples.
- Preserve the current measured language distribution: training **170 English / 175 Taglish**; validation **38 English / 22 Taglish**. Do not copy the old 200/200 corpus quotas or rebalance groups to force them.
- Have an isolated curator prepare the **60 selected research-holdout records** from the v11 selection and v13 source-bound audit. Use `fork_turns=none`, scoped conventions, source-use guidance and source-only exclusions; exclude coordinator conversation, development annotations, model outputs/scores and whole-chat exports. The holdout has **30 English / 30 Taglish**, each with **27 positives and three genuine negatives**. Its v13 checks cover **96 entity spans / 37 source groups**, with no known overlap under the available recorded exclusions.
- Bind the exact latest membership, selected-record evidence, supported annotation corrections, source/capture hashes, scoped use decisions, frozen-tokenizer identity, historical fitted-source anchors and protocol approval in new manifests. Existing private helpers are evidence only; do not execute or import them.
- Preserve the historical dataset, contextual pairs, fixtures, old exports, seed runs, models, scores and all previous review packages. Historical validation/test/context/fixtures cannot become new training samples. All 280 historical fitted-record anchors, including now-held/excluded examples, remain training-side exclusion anchors.

The exact private input paths and hashes are recorded in the ignored preparation-design package. Public documentation must contain only aggregate counts and verification hashes, not holdout IDs, URLs, titles, passages or individual annotations.

## Implementation behavior

### Scoped admission and grouped freezing

Implement a successor-only workflow under the offline training package. Preserve the existing fixed-400 export, qualification and manual-training entry points unchanged. No production API, dependency or database change is needed.

Admission must verify a new grant bound to the adopted protocol and exact input manifests. Its scope is `limited_provenance_silver_research`. Keep `global_history_verified=false` and `acquisition_accounting_verified=false`; do not force the historical readiness schema to pass or reuse a review-only authorization as an admission grant.

For every selected record, require captured original source text, complete reviewed six-class location-only silver references, exact Unicode offsets, passage/raw/source hash consistency, non-overlap and supported selected-extent source use. Explicitly complete empty references are genuine negatives; missing/null/incomplete references are held. Repeated literal mentions require supported occurrence-level handling. Do not invent taxonomy or change text/tokenizer rules for alignment.

Build a new immutable admission ledger with original IDs, pool/provenance, correction lineage, per-record scoped admission, accepted groups, split, evidence bindings and the protocol limitations. Freeze exactly **345 train / 60 dev / 60 research_holdout**, totaling **465 records**, only after all checks pass. A new substantive hold stops finalization and reports affected counts; it cannot be bypassed to retain 465.

Apply actual article/event/syndication/duplicate relationships across both pools using source-only metadata. Enforce historical fitted components as train-only, no cross-partition group fragmentation, exact/near-copy exclusions, mutually exclusive windows and passage non-overlap. Preserve the holdout's three-passage-per-article cap. Source-only grouping metadata may cross the coordinator boundary; test text and individual references may not. Unknown reporting relationships cannot be relabeled to create apparent independence.

Report per-split language, all six labels, positive/negative passages, flood role, theme and independent group counts. Preserve and report any missing validation language/label coverage, including existing Taglish ROAD/LANDMARK gaps if still absent. Do not manufacture examples to fill a table.

### Qualification and separate exports

Use the existing qualified research Python 3.11 / spaCy 3.7.5 environment and exact frozen `lanes.xx.address-v2` tokenizer. Verify the pinned model revision, vocabulary and tokenizer manifests from the recorded qualification inputs. Tokenizer SHA-256 remains `3f666f61346b7196d931ab9781a3d83f41d688e24b298e8e494b3d92c384a588`. Do not install or replace environments, models, tokenizers or dependencies.

Create a successor-specific tokenizer/serialization worker with explicit **development** and **isolated-holdout** capabilities. Do not reuse the legacy parent validators that require 400 records, 1,465 spans or train=280. The old worker's text/token/span and serialization checks are the reference behavior, but its always-three-split output must not create an empty or fake test export for a development-only job.

The development worker accepts only the 405 admitted train/dev records and writes `train.spacy`, `dev.spacy`, tokenizer bytes and its qualification manifest. It never receives holdout text or labels. The isolated holdout worker accepts only the 60 admitted research-holdout records and writes its private `research-holdout.spacy` and qualification manifest. The coordinator receives only allowlisted aggregate status, hashes and nontext grouping metadata. Never combine both reference pools in one curator context or a raw coordinator-readable request.

Both workers require exact original text, strict `char_span` alignment, the six location labels only, non-overlap, complete references, reproducible token boundaries and DocBin serialization/reload equality. Derive entity/language/negative counts from actual records, not historical constants. Use the model-bound vocabulary and serialization excluding vocabulary in tokenizer bytes; no model pipeline predictions or training. Shared artifacts and worker implementations are hash-bound, and failed/partial outputs cannot be marked qualified.

Produce a frozen evaluation contract naming the adopted scope and unresolved limitations. Research-holdout scoring stays outside preparation and training/configuration selection. No old fresh-test sealing claim is reused; if access is locked, label it a frozen limited-provenance research holdout rather than certified fresh or independently human verified.

### Portable desktop preparation

Create a successor-specific default-read-only launcher. Require explicit checkout/preparation/interpreter locations, resolve paths against the actual desktop checkout, and verify package, implementation, model, tokenizer and config hashes. Remove laptop/desktop hardcoded drive assumptions. The old launcher remains historical.

Keep seeds **0, 1 and 2**, with seed 0 primary and seeds 1/2 robustness runs, following the existing declared recipe. Change only successor data/output bindings and necessary portable paths; no holdout-driven hyperparameter tuning. Configs reference only train/dev exports, and the trainer must not receive the holdout package. Preserve old checkpoints and require new output directories and a single active run.

Require actual desktop GPU qualification before any later training launch. No automatic CPU fallback, security-policy change, environment installation or hidden training start. Preparation validates manifests, tokenizer/serialization and config structure; actual training requires an explicit later launch action. A laptop-only check cannot certify the desktop GPU.

Stage local private handoff materials and a short desktop guide describing what Git carries and what remains ignored. Verify trainer payload completeness separately from isolated evaluation payloads. Do not assume public reports or a Git pull transfer private datasets. No upload, external delivery, commit or push occurs without separate authorization.

## Tests and acceptance

Use constructed fixtures and mocked processes/transports, never private passages in public tests. Test wrong/stale protocol grants, input tampering, unsupported source use, historical nontraining reuse, fitted-component leakage, split groups, duplicate/overlapping alternatives, article caps, incomplete references counted as negatives, strict Unicode/tokenizer failure, forged aggregate readiness and serialization/reload mismatches.

Test that a development request cannot include/export holdout text, holdout capability cannot access development annotations, trainer configs/requests cannot reference evaluation data, and safe outputs reject individual source/reference content. Test wrong interpreter/model/vocab/tokenizer hashes, changed implementations, existing destinations, concurrent writers/runs, paths on another checkout and read-only launcher behavior. Missing GPU or dependencies must produce an explicit blocker without installing or training.

Run affected shared schema, reference/selection, privacy, export and launcher regressions. Report actual new counts separately from historical results. Hash-check preserved inputs and legacy helpers. Validate unique record accounting and all 465 memberships from source-bound manifests; no hardcoded guard or class totals may substitute for actual checks.

Implementation completion requires a reproducible scoped admission/freeze package, **qualified development exports**, an **isolated qualified research-holdout export**, the declared evaluation contract, tested portable launcher and an accurate handoff status. It may complete with desktop GPU verification or authorized private delivery still pending; neither is implied. Publish aggregate findings and synchronize the task plan, progress, roadmap, index, operator guides and training README.

**Actual training is a later desktop action after preparation and GPU/handoff verification.** This implementation task must not collect, infer, train, upload, commit or push.
