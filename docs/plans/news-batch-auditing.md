# Batch news auditing with quota-aware retries

> **Last Updated:** October 12, 2026, 4:06 AM
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Implemented and verified locally on `roi-branch`; the developer subsequently authorized Git publication. Real positive plotting acceptance remains blocked by provider quota. Cloud rollout remains separate.

## Contract and workflow

Local rules/NLP filter and extract first. Forecast, negation, unsupported locality/context and expired observation gates complete locally without an audit request. Missing measurements and access facts remain unknown. Due claims from the same immutable extraction run and audit policy are collected in their existing queue order into groups of at most eight eligible claims; rejected claims do not occupy provider batch slots. Article versions and publishers cannot mix.

`NewsClaimAuditor.audit_batch` supplies typed metadata, the complete saved body once, exact source-span options and candidate identifiers/immutable hashes. Strict Pydantic wire types and backend evidence validation remain required even when OpenRouter enforces structured output. Match each response by identifier and hash, never ordering. Unknown or duplicate identifiers invalidate the entire batch; missing results retry only those claims; malformed individual results cannot approve them while valid neighbors can complete. Single-claim callers use this same method with one candidate.

Prompt `news-independent-audit-v5-batch` and response `news-independent-evidence-v3-batch` change evaluation policy identity. Existing extraction and previous terminal evaluations remain immutable. Each result is saved in its existing evaluation row, then existing publication, placement, zone, clearance and Flood History services run independently. Deduplication/placement rules are unchanged.

Article/request/response byte limits remain 200,000 / 350,000 / 65,536. Output allowance is 8,192 tokens and provider timeout is at most 60 seconds. Groups exceeding the request bound split before dispatch; oversized bodies finish as review. Failure never triggers a one-request-per-location fallback. Dispatch renews the existing 120-second token-owned lease.

## Quota and durable ownership

Before OpenRouter dispatch, read the documented `GET /api/v1/key` request counters. Cache successful checks for 60 seconds, decrement remaining requests locally after dispatch, and report absent/invalid counters as unknown. A zero free allowance blocks dispatch until the next check in 30 minutes or a valid provider retry/reset deadline. HTTP 429 stops all further audit dispatch in that cycle, using a supplied deadline or 15 minutes. Other transient failures retain the existing bounded exponential retry and five actual attempts.

Only dispatched claims consume attempts. Admission, policy, source selection and observation freshness are checked again after quota IO and before sending. Waiting cannot extend evidence validity. If evidence expires before cooldown, an `auditor_quota_evidence_due` deferral wakes local maintenance at that original deadline; ordinary quota cooldowns do not keep launching the worker. Collection, extraction, clearance and expiry maintenance retain their due-work checks and 60/15/30-minute weather policy.

Grouped queue leases are atomic. A database-scoped session advisory lock serializes audit dispatch, with an autocommit connection and no open transaction or evaluation row locks during provider calls. Token-checked completion and interrupted-worker recovery remain enforced.

`SystemSetting` JSON key `news_audit_quota_v1` stores credential-free quota/cooldown state, an opaque policy/credential identity, successful-check cache marker and bounded counters. Failed/retry evaluations can store a bounded whitelist of diagnostics in existing `result` JSON. HTTP status, normalized reason, validated request identifier and retry delay are permitted; credentials and unrestricted provider bodies are excluded. Protected automation GET adds optional server-derived `audit` diagnostics. Overview displays these inside its existing expandable diagnostics; location cards and existing labels are preserved.

## Verification and release gates

- [x] Eight eligible claims per initial group; native 26-claim case produces 8/8/8/2 requests and 26 independent verified results, including reordered output. Seven locally excluded neighbors do not add requests.
- [x] Missing/unknown/duplicate/malformed results, wrong hashes, cross-claim evidence, truncation/size limits, provider errors, timeout, quota exhaustion/recovery, expiry, leases, interrupted work and concurrency checked with isolated fixtures.
- [x] Native queue/publication and desktop/mobile status verification; authentication/read-only response remains protected. Existing migrations apply cleanly; no model, migration, dependency or gathering-policy change.
- [x] Historical reports replayed through normal scheduled workers into fresh databases, without synthetic auditor approvals. A separate port-3004 preview uses the September 9 replay database; existing port-3000 snapshot configuration is preserved.
- [ ] Real successful provider verification followed by map/history creation and observed 19-inch-to-10-inch update outcome. Current real allowance is exhausted; do not claim positive acceptance or change placement/deduplication to obtain it.
- [ ] Separate coordinated API/worker/frontend cloud rollout and activation. The subsequent Git publication request does not deploy or activate these services.

See [verification, commands and screenshots](../evaluations/news-batch-audit-20261012/README.md), [existing historical source qualifications](../evaluations/news-scheduled-historical-workflow-20261012.md), [OpenRouter limits](https://openrouter.ai/docs/api_reference/limits) and [structured output](https://openrouter.ai/docs/guides/features/structured-outputs).
