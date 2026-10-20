# Phase C2 — durable NER projection and source evidence

> **Last Updated:** October 20, 2026, 9:09 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Status: C2 complete locally. Scope:** backend library qualification, without automatic activation. [Aggregate verification](summary.json) · [Integration contract](../../plans/rss-ner-integration-contract.md) · [Remaining roadmap](../../task_plan.md#phase-c--connect-automatic-article-processing).

## Delivered behavior

`backend/app/services/news_ner_durable/` adds native capture serialization, independently authenticated assets, deterministic observation projection and `source-ner-v1` checking. It is separate from the unchanged preview/runtime packages. There are no new dependencies, model/migration edits, routes or frontend changes. Scheduled extraction/evaluation still uses the existing legacy path; it cannot consume native results yet.

The adapter accepts owned run/version context, saved original predictions and an independently supplied `TrustedAssets` object. `load_trusted_assets` requires the approved bundle digest and worker-code digest supplied outside the saved result. It authenticates bundle files without loading a model, runtime code, projection/source code and geographic references. The result's own manifest cannot authenticate itself. The pipeline identity binds the model, tokenizer, runtime, location/context rules, projection, source checker and geography. Asset/configuration drift fails closed.

`lanes-news-ner-input-v1` binds URL, publisher, title, excerpt, exact body, publication metadata, `capture_schema` and `publication_evidence`. Fetch/seen clocks and article IDs do not enter the native content fingerprint. Legacy serialization/fingerprints remain unchanged. Raw publisher-feed publication evidence must support its claimed aware timestamp; a normalized historical timestamp alone does not prove its original timezone. Such provenance defaults to unknown. C1's inspection-only fixtures remain readable but fail this stricter operational contract.

The unchanged pure adapter recomputes v40 → v44 → v42 from original saved predictions. Exact untrimmed Unicode offsets, occurrence IDs, ordered proposals, abstentions, complete graph and original grouped output survive. No neural inference, location-rule tuning or graph repair occurs during C2 verification.

## Projection rules and limits

`ner-claim-projection-v1` partitions facts by exact targets and observation evidence. Separate paragraphs, updates and clocks stay separate; equal location strings cannot merge them. Deterministic group IDs/order and complete fact accounting distinguish projected, native-only, contextual and unresolved facts. Valid native-only/no-observation results have an explicit disposition and reasons with no fabricated inference error.

Only affirmative Metro Manila reporting-body observations with representable single targets become compatibility claims. Existing Philippine geographic references plus source-supported clause/list-heading context resolve administrative parents. Ambiguous names, unrelated datelines, narrative boundaries and unsupported locality remain unresolved. There is no default Pasig parent. Unknown roads with a source-supported Metro parent retain their raw name with unassessed geometry.

Intersections, collective scopes and LOCAL_AREA targets remain native-only, preserving all shared evidence. Ranges, maxima, relative/conflicting quantities and all qualifiers remain in the graph; a scalar is selected only where its meaning is unambiguous. Unknown confidence remains `null`. Existing 500-claim, 4,000-character quote and 12-span limits are enforced; omitted projection units remain native with reasons. Native source audits exceeding 64 KiB return bounded review results while the complete native evidence remains saved.

All seven temporal roles are preserved. Only supported observation evidence may resolve an observation instant: explicit dates/clocks with supported timezone context, or explicit relative dates with authenticated publisher-feed timezone provenance. Bare clocks, invalid/conflicting dates, unknown publication provenance and another role's timezone cannot fill missing observation time. Report, publication, onset, recession and clearance never substitute for observation. Existing freshness/status/expiry policy still applies.

Access remains evidence-bound. A narrow normalizer preserves an explicitly adjacent caution modifier even where frozen v42 saves only “passable”; the supplemental exact source slice is labeled separately and the graph is unchanged. Unsupported vehicle-specific access remains unknown. No vehicle policy, action, audit or placement decision is manufactured by projection.

## Source checking contract

`check_native_source` / `check_native_sources` require completed owned native run/version context, the saved result, claim ordinals, trusted assets and an aware checking time. They recompute the full projection, exact evidence slices and bindings. Persisted result, source hash, identity, manifest, mentions, proposals, graph, groups or extraction-field tampering is refused. An old recognizer miss does not invalidate valid native evidence; the legacy checker and its identities remain unchanged.

The policy fingerprint separately binds `source-ner-v1`, the trusted manifest, native pipeline and optional existing publication policy. It cannot reuse legacy source audits. Existing placement enrichment fields are excluded only from extraction-field comparison; the whole enriched claim remains bound by its normal full claim hash. Source consistency does not certify geometry, field truth, publisher admission, conflict resolution or publication eligibility.

Forecasts, captions, prevention, historical references, negation and unsupported locality do not become verified current observations. Receding/subsided/cleared evidence retains its status meaning and existing policy restrictions. Missing supported observation time returns review and remains publication-ineligible. Errors expose four bounded families: input binding, result contract, assets unavailable and configuration invalid; they do not include source text, credentials or private paths.

## Verification evidence

The final constructed/regression run passes **211 checks**; the owned disposable PostgreSQL run passes **14 checks**. Coverage includes Unicode/whitespace/repeated names, joint/collective/range facts, ambiguous parents/headings/datelines, temporal roles/provenance, negative evidence, evidence/claim limits, null confidence, all binding layers, enriched hashes, legacy source policy and C1 ownership/history. PostgreSQL verifies JSONB round trips, immutable input versions, lease ownership, legacy history and source proof without publication records/zones. The unchanged migration chain reaches `e8a6f1c2d903`. The pinned PostgreSQL 15/PostGIS 3.4 container uses generated credentials and an ephemeral loopback port; it is stopped after verification. These small fixtures are not production resource measurements.

Two initial software failures revealed caution-modifier loss and unsupported vehicle scope. Both were corrected in the new projection normalizer; failed receipts are retained. The first retained replay controller stopped at a destination-path guard before processing any record. The replacement controller verifies the authenticated cache chain directly instead of invoking an old whole-application preservation controller against an intentionally changed checkout. No historical controller, frozen identity or prediction is rewritten.

The second replay was deliberately stopped after 353 completed envelopes when the 100,000-character stress case exposed repeated sentence-boundary recomputation for each target. Its partial outputs and cancellation receipt remain preserved. The new projection adapter now computes the unchanged sentence boundaries once per article. Software/PostGIS regressions and the complete saved-output replay are repeated against a new source freeze; no inference or qualified-rule change is involved. This does not qualify combined queue/runtime performance, which remains C3 work.

The third replay stopped at that stress case because duplicated projection metadata exceeded C1's unchanged 8 MiB saved-result limit. Native-only projection groups now declare `evidence_storage: native_graph` and reference their exact target/fact/relation IDs instead of copying native evidence and unused compatibility normalizations. The complete original graph and original grouped output remain present. Projected claims retain inline source-checking evidence. Earlier oversize failure receipts are preserved; this is a storage-format efficiency correction in the new adapter, not a raised limit or discarded fact.

The fourth replay confirmed that evidence references alone were insufficient. The final compact representation also uses deterministic artifact-local ordinal group IDs, matching the native graph's artifact-local ID convention, and retains specific disposition reasons without repeating a generic reason beside them. Exact source/run bindings and full-result recomputation provide integrity; a group ID is not an authentication credential. Every prior attempt/source freeze remains historical and unchanged.

One database rerun initially targeted a database erased when the temporary server stopped; a subsequent harness attempt reached its temporary initialization server too early. These setup failures are retained separately from application assertions. Later runs recreate the owned disposable database, wait for authenticated external readiness, apply the unchanged migration chain and stop the server afterward. No shared database URL is used.

Private receipts live under `backend/training/flood_ner/artifacts/rss-ner-phase-c2-20261020-v1` and remain ignored. Only aggregate results are public. Retained replay and independent preservation outcomes are recorded in the aggregate; source text, individual predictions, raw manifests/credentials and private failure traces stay private. Retained native envelopes use fictional development identities around authenticated existing text/predictions; they are not new captures or production alerts. Historical publication timezone provenance stays unknown. Replay counts establish compatibility, not accuracy/F1 or new runtime performance.

## Final replay and independent review

The complete saved-output replay passes **355 retained records**: 345 existing training-only passages, six complete articles, three fictional stress cases and the reviewed article. All **352 saved prediction records**, **53 reviewed predictions**, and **788 cached inputs / 407 saved context graphs** match. The largest final durable envelope is **8,203,832 bytes**, below the unchanged **8,388,608-byte** limit. No original native graph/grouped output is removed to meet that bound.

The replay accounts for 5,341 facts across 4,525 observation groups and emits 17 compatibility claims from 14 records. All 17 receive **review**, because supported observation time remains unresolved; no retained historical/fictional case becomes a current alert. The remaining records have explicit native-only (139) or no-eligible-observation (202) dispositions. These counts describe this retained development workload, not recall/accuracy or production traffic.

Independent verification authenticates final source/test/replay bindings and all **five prior receipt packages / 1,327 files**, with all 12 C1 source bindings intact. The old runtime freeze still has exactly the same eight previously approved schema/C1 deltas; 1,032 of 1,040 bindings match. C2 additions have separate source freezes. The owned PostGIS image/owner/stopped PID state is verified. Core documentation is synchronized; architecture decisions were reviewed without inventing a new decision outside the approved contract.

## Remaining gates

C3 must integrate the qualified runtime with the actual queue, 450-second session budget, 125-second startup/request/cleanup envelope, 300-second lease and 600-second job limit; qualify RSS admission and corrections; finish intended-method/native readers and nullable-confidence downstream consumers; and complete controlled end-to-end extraction/placement/evaluation/publication acceptance. Existing publisher, body-completeness, geometry, conflict, freshness, expiry and vehicle gates stay authoritative.

No new inference, training/data collection, runtime requalification, shared/cloud write, schema revision, frontend change or deployment is included. The historical 60/15/30-minute policy is unchanged, without a new live-cloud health claim. Shared migration, cloud resource/asset delivery, full-job verification and deployment retain their separate release gates. C2 does not mean automatic NER or News Intelligence changes have shipped.
