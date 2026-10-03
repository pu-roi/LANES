# LANES documentation

> **Last Updated:** October 03, 2026, 5:35 PM

Start with the [project README](../README.md), [agent instructions](../AGENTS.md), and [system design](../DESIGN.md). The files below are grouped by purpose. The eight registered project records retain their established paths so existing workflows can find them.

## Project records

- [Task plan](task_plan.md) — active sprint and backlog.
- [Progress tracker](progress.md) — delivery history.
- [Feature reference](feature-reference.md) — major platform capabilities.
- [Architecture decisions](decisions.md) — significant design choices.
- [Tech stack](tech-stack.md) — technologies and deployment components.
- [System documentation](others/system-documentation.md) — screens, routes, endpoints, and components.
- [Database design plan](others/database-design-plan.md) — schema and spatial design.
- [Bug log](others/bug-log.md) — investigated issues and fixes.

## Plans

- [F4b monitoring telemetry implementation](plans/news-monitoring-telemetry-plan.md) — approved durable discovery/fallback history, tested local migration and remaining rollout/manual acceptance.

- [Priority 5 publication, review, corrections, expiry and frontend plan](plans/news-publication-review-frontend-plan.md) — F1/F2 delivered, F3 design accepted, F4a/F4b monitoring implemented; manual acceptance and review/public lifecycle checkpoint remain pending.
- [Flood event history design](plans/flood-event-history-design.md)
- [Flood report merging plan](plans/flood-report-merging-plan.md)
- [LiPAD & UP NOAH flood placement](plans/lipad-noah-flood-placement.md)
- [News activation safety gates](plans/news-activation-safety-gates.md)
- [RSS news discovery plan](plans/rss-news-discovery-plan.md)
- [Smart auto-activation and hybrid NLP plan](plans/smart-auto-activation-and-hybrid-nlp-plan.md)

## Evaluations and simulations

- [September 24 historical flood replay](evaluations/phase-36-september24-historical-replay.md) — actual publisher retrieval, street-fact corrections, v6 city-context reconciliation, private saved replay, PostgreSQL parity and pending release/placement gaps.

- [News Intelligence content correction and release](evaluations/phase-36-news-content-quality-investigation.md) — foreign/prevention false-positive audit, shared evidence/geography fixes, preserved versioned history and verified production rollout.
- [Automatic pipeline plan alignment audit](evaluations/phase-36-automatic-plan-alignment-audit.md) — automation alignment, remaining integration/telemetry rollout dependency, runtime OSM dependency isolation with 140 passing checks and residual raw-PBF restriction.
- [F4b durable monitoring verification](evaluations/phase-36-f4b-monitoring-check.md) — 214 news regressions, PostgreSQL migration/queue checks, local head and remaining visual acceptance.

- [Phase 36: F2 article browsing verification](evaluations/phase-36-f2-article-browsing-check.md)
- [Phase 36: F3 unified news reading and F4a source monitoring verification](evaluations/phase-36-f3-result-browsing-check.md)
- [Phase 36: Open article fallback check](evaluations/phase-36-open-article-fallback-check.md)
- [Phase 36: Three 2026 flood article extraction check](evaluations/phase-36-three-article-check.md)
- [Phase 36: Three full-article backend simulation](evaluations/phase-36-new-article-service-simulation.md)
- [Phase 36: Publisher body and pagination audit](evaluations/phase-36-publisher-body-and-pagination-audit.md)
- [Phase 36: Santo Domingo article-to-road-span audit](evaluations/phase-36-sto-domingo-road-span-audit.md)
- [Phase 36: Reusable article-to-road match check](evaluations/phase-36-reusable-road-match-check.md)
- [Phase 36: NOAH road-section ranking check](evaluations/phase-36-noah-road-ranking-check.md)
- [Phase 36: Article and DRRMO road-section context check](evaluations/phase-36-article-road-context-check.md)
- [Phase 36: Metro Manila OSM and NOAH coverage audit](evaluations/phase-36-metro-spatial-coverage-audit.md)

## Guides

- [Private local News Intelligence replay](guides/local-news-replay.md) — Docker test database, guarded historical article persistence, loopback launchers and return to cloud-backed development.
- [Flood history verification](guides/flood-history-verification.md)
- [Routing logic](guides/routing-logic.md)
- [Vehicle passability](guides/vehicle-passability.md)

## Research and capstone

- [Routing engine research](<research/Routing Engine Research.md>) — research context; use the current [tech stack](tech-stack.md) and [decisions](decisions.md) for adopted architecture.
- [Capstone defense reviewer](capstone/capstone_defense_reviewer.md)
- [Capstone defense Q&A and suggestions](capstone/capstone_defense_qna_suggestions.md)

`others/` also contains local, Git-ignored working notes. Those notes are outside the shared documentation index.
