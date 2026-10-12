# Reliable news audits and Metro Manila placement

> **Last Updated:** October 13, 2026, 1:56 AM
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Local implementation complete; remaining live qualification/target replay skipped by the developer. Git publication to `roi-branch` authorized; no cloud deployment.

## Required outcome

Complete the [research-backed repair](../research/news-audit-reliability-20261012.md), geographic coverage and responsive preview verification, then run September 24–25's five checkpoints followed by September 9's twenty-six half-hour ticks. Preserve all sources, measurements, labels, prior databases and terminal evaluations. Provider outages must produce bounded retries and explainable recovery, never unsupported approvals.

## Audit and recovery contract

- Store credential-free, bounded monotonic transport diagnostics in existing evaluation JSON: phase, timeout subtype, response/request bytes, candidate count, safe model/generation/request IDs, finish reason and token usage where available.
- Keep a 60-second hard request deadline within the 120-second owned evaluation lease. Use separate connect/write/pool limits of 5/10/5 seconds. Reuse one scoped client per evaluation cycle; never hold a DB transaction over provider IO.
- Stop a scheduled evaluation cycle after six POSTs or six minutes. Defer undispatched rows without consuming attempts. Continue local evidence expiry/publication maintenance; report progress after each batch.
- Keep account quota identity independent of prompt/model revisions. Two consecutive model availability failures open a 15-minute real-clock circuit; failed recovery probes extend to 30 then 60 minutes, capped at 60. Complete valid responses reset availability without implying factual approval. HTTP 429/account exhaustion remains independent.
- Retain the full bounded article once, exact backend-owned quote/offset references and separate place/status/time/depth/access assessments. Compact requests omit redundant derived/null fields and provider hash copying. Match results by short candidate ID, bind immutable hashes server-side, reject cross-occurrence evidence and never correct an explicit wrong legacy hash.
- Version the changed audit policy; preserve terminal evaluations. Support batch profiles of four/eight and explicit optional reasoning control. Select only benchmark-qualified free models; no paid fallback, nested retry loops or parallel duplicate calls.
- Initial benchmark ceiling: twelve POSTs across two models and four/eight profiles. Repairs may receive a separately logged bounded follow-up; record total calls and actual account allowance. Select qualifying eight-claim profile first, fastest qualifying model within the profile; a backup requires independent qualification. Small benchmarks do not establish production accuracy.

## Placement and preview contract

- Review all seventeen NCR city/municipality parents. Resolve Manila district references through PSGC hierarchy, exclude identically named non-NCR places and retain per-barangay qualification/exclusion reasons.
- Preserve the old Pasig assets. Build immutable source catalogs and a bounded internal registry; qualified OSM records have precedence and reviewed additional sources fill gaps. Every selected record retains its actual provenance.
- Acquire original OCHA/HDX source records for missing coverage, prioritizing San Agustin/Tañong in Malabon. Validate identity, licensing, topology and checked city containment without repairing, clipping or fabricating polygons.
- Ground Marcos Underloop against a uniquely named mapped structure and bounded road section, or retain an explicit unresolved result. Keep NOAH, ambiguity, grade, freshness and activation gates.
- Reuse dedicated ports 3004/8004 with a worktree-specific preview build. Diagnose actual browser script/network failures, verify desktop/mobile direct loads, refresh/navigation and map fallback. Preserve port 3000, concurrent user edits and cloud data.

## Interfaces and verification

No SQL schema or migration changes. Internal audit transport/source-registry types and optional fields on the existing authenticated automation status are additive. Existing public flood endpoint contracts stay intact. Runtime configuration selects the qualified model/profile; no credential is committed.

Cover timeout/cancellation/partial response cleanup, unknown/duplicate IDs, repeated road occurrences, cross-road facts, alias/wrong-parent cases, quota/circuit recovery, cycle limits, lease/concurrency and zero-attempt deferrals. Verify catalog hashes/provenance, NCR filtering, numbered barangays and immutable source versions. Run existing responsive suites and actual API/browser checks.

The real replay must establish an initial eligible zone before claiming positive plotting/history/depth-update acceptance. Trace N.S. Amoranto/Banawe **Santo Domingo**, 19 inches at 08:55 then 10 inches at 16:30; record update, separate event or rejection without extending original evidence expiry. Repeat unchanged input to prove no repeated completed audits/duplicate rows. September 24 may correctly yield admission rejection and no zone.

## Progress and completion

Current evidence is recorded in the [implementation evaluation](../evaluations/news-reliability-goal-20261012.md). Ordered real replays, Sienna/Tatalon zone/history lifecycle and responsive previews pass. Source-line precision was handled through a [separate repair](news-source-line-precision-repair.md); Santo Domingo target audit/polygon acceptance remains open under the [follow-up plan](news-audit-and-corridor-followup.md). The original full-acceptance requirement below was subsequently waived for this task by the developer; record its result as skipped/unverified. Source exclusions/provider disagreement are retained blockers, not passing checks. Preserve reconstructed RSS membership/early indexed GMA markup limitations. No manual flood rows, synthetic approvals or evidence-policy overrides.

## Current implementation checkpoint

V20/corridors-v7 conservative construction passes strict parent/buffer/core predicates on real source claims 13/50/69; no source polygon or validator policy changed. V9's last bounded live probe verified seven of eight early candidates, including Santo Domingo; Guirayan correctly rejected a wrong depth class. Current v11 locators/null-depth/compact wire remain live-unqualified because actual allowance reached 50/50/0. Unknown allowance now also pauses free dispatch for sixty real-clock seconds without attempts; longer provider cooldowns persist. Latest 161 focused/35 native checks pass. The developer clarified that ChatGPT use means a [manual source review in this chat](../evaluations/news-chat-source-review-20261013.md); this is complete and separate from automatic approvals. A fresh v20 September 24 replay and current-code responsive preview checks now pass; September 9 preview retains v19 saved data. Combined final-code checks pass 507. Actual allowance recheck at 01:34 PHT remains 50/50/0 with cooldown through 02:04 PHT. Target activation/depth-update acceptance still needs a fresh qualified normal-worker replay. [Evidence](../evaluations/news-reliability-goal-20261012.md).

## Developer scope amendment

The developer explicitly chose to skip the remaining OpenRouter-dependent qualification and fresh September 9 target replay because the account allowance is exhausted. Local implementation/manual review and independent verification are complete. Current v11 live qualification and Santo Domingo automatic zone/depth-update acceptance are **skipped and unverified**, not passed. No further provider retries or automatic follow-up are part of this task. The developer subsequently authorized Git publication to `roi-branch`; cloud deployment remains excluded.
