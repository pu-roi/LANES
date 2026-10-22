# Phase D — backend monitoring and error classification

> **Last Updated:** October 21, 2026, 01:19 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Status: backend Phase D passed locally.** Saved APIs distinguish publisher eligibility, worker selection, retrieval, flood eligibility, processing and retry history. Frontend presentation remains Phase E; production deployment is not included. [Aggregate](summary.json) · [Roadmap](../../task_plan.md#phase-d--correct-monitoring-and-error-classification).

## Source and article health

The protected sources GET keeps `enabled` as the registry flag and adds:

| Field | Meaning |
|---|---|
| `registry_eligible` | Registry enabled, dated verification and configured feeds |
| `selected_for_collection` | Selected through the same existing configuration logic as the worker |
| `collection_active` | Selected and global collection enabled |
| `feed_health` | Each configured feed's saved check/success timestamps, `not_recorded` / `ok` / `error` and bounded error code |
| `body_counts` | Publisher totals for available, missing and errored article text |

Health is saved evidence, not a live probe or promise of freshness. A check timestamp without a recorded successful outcome cannot establish `ok`. Successful RSS does not establish successful body retrieval or a flood observation. Raw network diagnostics are not copied into the new source-health response. Registry-owned feeds and grouped article metadata are read in aggregate; article bodies are not loaded for these counts.

Collection GET adds `retrieval=available|missing|error` and independent `retrieval_counts`. Existing collection/flood classifications remain authoritative. For troubleshooting excluded articles, use `status=all&retrieval=error`; `attention` retains its narrower meaning and all filters intersect. Existing pagination, search, publisher and native intended-pipeline selection remain unchanged. Retrieval counts cover the saved article population, independently of the active list filters, matching the existing collection-overview count convention.

A failed refresh does not erase a previously saved observation. Such an article can honestly have a retrieval problem and retained native locations at the same time. An excluded legacy article without credible observations remains excluded even when retrieval filtering exposes it.

All GETs retain staff authorization and perform no probes, inference, publication or writes. Storage failures return the existing bounded 503 behavior; schema validation rejects unknown retrieval values.

## Counters and error boundaries

Feed history now exposes `articles_saved_or_seen` computed from the existing stored `candidates_saved` value. The old field and database column remain; rediscoveries and commuter updates do not become newly discovered flood candidates. Collection-to-alert delay remains unavailable with reason `not_computed`: publication records exist, but this reader does not calculate the metric. C3b's actual linked publication lifecycle is reused without inferring publication from extraction completion.

`HybridExtractionService` no longer reads auditor environment settings during rules-only initialization. Existing credential properties/overrides remain compatible through lazy loading. Auditor environment parsing raises bounded `AuditorConfigurationError`; existing semantic configuration codes remain specific. No exception payload exposes environment values or credentials.

Article snapshot parsing alone can produce `invalid_input_snapshot`. Validation failure after that boundary is an extraction-result error under the existing bounded retry policy. Required auditor configuration is checked before evaluation claims; invalid settings return a service error without consuming evaluation attempts or opening a provider session. The scheduled pipeline reports the service configuration error rather than draining an article batch.

Automation status still returns worker, collection, weather and queue information if audit configuration is invalid. Only its audit section becomes `requires_attention`. Database failures continue to propagate to the storage boundary; they are not caught as configuration errors. Existing extraction/evaluation leases, completion ownership and publication safeguards remain intact.

## Ten-attempt history

The existing runtime settings JSON now retains `recent_cycles`, newest first, capped at ten. Each completed entry records timestamps, outcome, bounded counts, known-stage outcomes/errors and validated Cloud Run execution/task/attempt identity when supplied. Missing/invalid metadata remains unknown. `last_cycle` remains available; older JSON without the new fields stays readable. No table, migration or historical-row conversion is added.

Finalization is idempotent. A later successful retry appends its own entry and retains the preceding failure. Collection skipped as `not_due` does not replace the prior collection failure or advance its successful-retrieval timestamp. Aggregate failures without individual errors receive a bounded stage-failure code; cancellation is not recorded as successful completion. Scheduled output includes stage errors/outcomes and execution identity while preserving normal exit/retry behavior and the collection cadence.

History is a bounded operational window, not permanent forensic storage. Earlier attempts are not reconstructed from final job status, and successful job execution is distinct from successful source retrieval. Completed-cycle `stage_outcomes` and worker `stage_results` describe actual outcomes; legacy worker `stage_outcomes` configuration flags remain compatible. Enabled does not mean completed.

## Cloud finding disposition

Read-only Google Cloud inspection on October 21 rechecked execution `lanes-news-discovery-mnmjd` in `lanes-project-508809`, `asia-east1`:

| Evidence | Verified result |
|---|---|
| Task attempt 0 | `requires_attention` at October 20, 2:00:49 AM PHT; container exited 1 |
| Task attempt 1 | `completed` at 2:01:17 AM PHT; container exited 0 |
| Execution | One retry, one successful task, final execution success |
| Logged extraction/evaluation work | Zero failed/retry/lost-lease counters and no recorded operations |
| Missing diagnostics | Neither attempt's retained summary contains collection details or its failing-stage error |

**Disposition:** attempts and final retry outcome are reconciled; the underlying collection failure reason cannot be recovered from the retained execution logs. The current scheduler's control flow is consistent with a failed collection followed by a retry where collection is not due, and the fictional scheduler regression demonstrates that sequence. This is an inference, not proof of the historical publisher/error. No particular HTTP status, publisher recovery or infrastructure fault is established. The new diagnostics prevent the same loss of context in future deployed attempts; they do not repair or backfill the old execution. Detailed HTTP 403 investigation remains Phase F.

No cloud configuration, job launch, deployment, shared database write or production-history backfill occurred. Existing 60/15/30 policy and scheduler exit/retry behavior remain unchanged.

## Verification and preservation

**608 distinct tests pass, including 21 new Phase D checks, with zero final failures/errors/skips.** Results are deduplicated by test class/name across targeted runs; the corrected rerun supersedes the earlier result for the same case. Coverage includes:

- Registry selection/defaults/pause, disabled publishers, mixed or unrecorded feeds and successful RSS with body failure.
- Legacy exclusions and native retained observations, retrieval counts/filtering/pagination, unauthorized/commuter access, no-network/no-write GETs and status during configuration failure.
- Invalid auditor batch/reasoning/revision, lazy dotenv/credential compatibility, rules-only independence, pre-claim audit rejection, input versus result errors and separate storage failure.
- Failed collection followed by a successful retry, preserved stage health, ten-entry retention, idempotent finalization, old JSON, unknown Cloud Run metadata, aggregate failures and cancellation.
- Existing processing/telemetry/readers, source evidence, hybrid/pipeline/CLI, native method/projection/integration, operational settings, weather/controller/cadence, evaluation ownership/concurrency and publication/clearance/expiry behavior.

Forty evaluation/publication persistence checks pass on fresh dedicated databases; native reader/retry cases use per-case clones of an empty migrated template. The unchanged migration chain reaches head `e8a6f1c2d903`; immutable-history protections remain enabled. **788 cached inputs and 407 saved graphs** also match the unchanged qualified pure adapter, with zero neural inference. No runtime/resource qualification was repeated.

Two initial failed checks are preserved: a new fixture incorrectly expected failed refresh to erase retained native locations, and an existing dotenv regression exposed eager credential-property compatibility expectations. The fixture now asserts retained evidence and lazy properties restore compatibility; neither safeguard nor failing test was removed. Final targeted runs pass. Existing library warnings are unrelated and unchanged.

All **9,796 predecessor receipt files**, including C3b, schema and failed/passing runtime qualification packages, match their original hashes. Twenty-one current Python source/test files have a separate source-difference manifest, patch and snapshot. The normalizer's existing code binding naturally distinguishes new orchestration code; old native results/manifests are not relabeled or rewritten. Trained model, tokenizer, inference worker and qualified extraction/grouping rules remain unchanged.

The one owned PostgreSQL 15/PostGIS 3.4 container uses the inspected local image ID and generated loopback credentials. Its fictional test databases are dumped privately, the container is stopped and PID is zero. Raw logs, database URLs, dumps and receipts remain ignored; only aggregates are published. No frontend, new dependency, SQLAlchemy model, Alembic, cloud-resource or activation change occurs.

## Phase E handoff

Use the new fields to replace the misleading Enabled badge with separate registry/selection/health meaning; surface excluded-article retrieval issues, the saved/seen label, `not_computed` limitation and retained retry-stage errors. These visible corrections, shared-component section renaming, NER evidence/cards and automatic saved-data updates remain unimplemented Phase E work. Browser/mobile acceptance, Phase F 403 diagnosis and production release remain open.
