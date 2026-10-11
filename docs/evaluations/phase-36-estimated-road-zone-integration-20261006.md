# Automatic estimated news-road zones and existing map integration

> **Last Updated:** October 06, 2026, 01:15 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Implemented and verified locally. Matching deployment, preserved real-article acceptance and physical PWA checks remain open.

## Delivered behavior

The explicit news pipeline now tries an estimated road corridor when a current, independently audited source alert lacks an exact approved incident footprint. It uses the existing extracted road/city/barangay/nearby clues, checked OSM catalog and NOAH modeled road fragments. It accepts only one article-grounded, untruncated, unambiguous selection inside its qualified locality. Missing assets/history, uncertain elevated ways, no modeled overlap, unsupported facts and corridor buffers that would join disconnected gaps cannot activate.

The existing 25 m road-zone margin is applied in the established local metric projection. This is a routing/display margin, not measured water width or a claim that NOAH observed this event. The generated corridor is explicitly labeled **Estimated road corridor**. The current news audit supplies flood condition/depth/access and observation; modeled susceptibility supplies placement evidence. Each disconnected accepted component creates its own polygon and stores its corresponding centerline in existing `source_geometry`.

Approval recomputes the estimate from server assets inside the common activation transaction and requires exact geometry/checksum/context. Private `estimated_news_road` binding records asset revisions/digests, component hashes/lines and margin. A client flag, supplied polygon or checksum cannot substitute for that computation. Current evidence, actor protections, source/audit policy, incident supersession, revision/request identity, atomic writes and finite observation expiry remain enforced. Catalog-backed authoritative incident footprints retain their separate strict path.

Unresolved automatic alerts acquire an append-only Needs Review decision without a routing extent. Repeated sweeps skip the same reviewed asset revision, preventing unsupported early cases from starving later candidates. Changed assets or newly evaluated evidence can be reconsidered. Exact catalog matches retain priority. Unchanged estimates and metadata may refresh only after recomputation and current component/core checks; changed modeled extent withdraws unsupported old links and requires a new activation. Re-fetching or retrying does not renew expiry.

## Existing UI and data contracts

- Public `/reports/active-zones` and staff zone details attach safe current news projections: article/publisher/link, observation, status, expiry and geometry basis. Private audit/provenance bindings stay private. News evidence is not assigned a fabricated commuter trust score.
- `useFloodZonesLayer` still uses the shared polygon aura and solid road-core paint. New estimated zones supply the missing line through `report_geometry`. Existing selected Needs Review previews retain the transparent layer only. No severity colors, new layer style, panel design or component framework was introduced.
- `FloodZonePopup` and the existing `FloodRecordSummary` staff facts show article and estimated-placement details on desktop/mobile. Public alert and staff effect types accept operational results; expired/cleared projections no longer claim current routing effect.
- Screenshot review also corrected the existing desktop popup's height/side placement and scroll limit so added source details stay accessible within the viewport; existing mobile modal/drawer patterns are retained.
- Existing SSE update handling invalidates public/staff zone and news caches, and staff decisions invalidate the affected map queries. The public map surfaces a failed refresh through the existing toast system while retaining cached data.
- A committed accepted zone is available to public API/routing reads immediately. Existing database-backed SSE/polling remains bounded at roughly 15 seconds for map refresh; this is not a sub-second cross-process push guarantee. Matching API/job deployment is still required.

## Verification

Final targeted verification: **272 passed** across thirteen suites, including real disposable PostGIS activation, safe public HTTP reads, stored cores, routing, expiry, review retry skipping, unchanged refresh, changed NOAH extent fallback, parallel workers and tampered-estimate rejection. Related auditor/evaluation/spatial/schema/presentation regressions: **194 passed** across eight suites; event regressions: **4 passed**. These are **470 distinct backend checks** across twenty-two suites. The earlier focused preview/pipeline run also passed 33 checks; overlapping results are not added to this total.

The existing migration upgrades reached **`d7e4b9a21c60`** in fresh loopback disposable databases; verifier cleanup removed each allocated database. No normal application/cloud database was migrated or changed. Earlier fixture failures were corrected: native sweeps are scoped to their created cases, newer test observations do not conflict with prior supersession fixtures, and refresh adds a support-history link rather than another zone.

**20 distinct browser cases pass** across desktop/mobile and four suites. They verify actual severity core/aura pixels, popup source/basis/time, existing staff facts, ordinary zone/contributor actions, decision retries and source-alert freshness/offline behavior. API/session responses are mocked; this establishes rendering/interaction, not live article accuracy or real-device acceptance. The map pixel test uses CSS screenshot coordinates and a stable street-level viewport. One existing mobile mixed-queue test timed out during concurrent verification and passed when rerun alone; it remains a potential test-stability concern.

TypeScript passes. Scoped lint comparison reports **35 existing errors in both HEAD and the touched files**, with no introduced error; whole-file lint is not clean. Existing errors include legacy `any`, render-time refs and the recursive SSE callback rule. No dependencies were added. SQLAlchemy models and migrations are unchanged; new typed fields use existing JSONB and API DTOs.

## Main code paths

| Concern | Existing/new paths |
|---|---|
| Corridor derivation | `backend/app/services/news_estimated_road_service.py` |
| Server approval and activation/refresh/review | `operational_footprint_evidence_service.py`, `news_publication_service.py`, `news_footprint_worker_service.py` |
| Safe zone/news projection | `news_zone_projection_service.py`, report/publication DTOs, public report and staff zone readers |
| Shared rendering/details | `useFloodZonesLayer.ts`, `FloodZonePopup.tsx`, `ActiveZonesPanel.tsx`, existing shared summary |
| Status, refresh and types | `NewsAlertsPanel.tsx`, `publicNewsApi.ts`, `useLiveSync.ts`, `MapCanvas.tsx`, existing staff API/decision controls |
| Verification | `test_news_estimated_road.py`, native publication suite, `news-zone-map.spec.ts`, existing spatial/public-alert/decision suites, guarded verifier |

## Remaining acceptance

1. Replay preserved real news using approved spatial assets and configured independent auditing; evaluate Pasig placement and unsupported NCR locations. Fixture approval does not establish real-event accuracy.
2. Verify matching API/job packaging/configuration for OSM, NOAH, qualified boundaries/history and evaluator credentials; restart cached asset providers after replacing catalogs. Deploy only in the separately authorized release workflow. Estimated road activation does not require a real authoritative current-footprint catalog; that remains optional for the separate verified-extent path.
3. Run controlled staging article → zone → desktop/mobile map → routing → refresh/clearance/expiry acceptance, then physical PWA cache/offline/permissions checks.
4. Finish optional staff footprint/existing-zone geometry editor handoff. Existing server preview/save contracts are available; this slice does not add those editor fields or broaden unsupported San Miguel/barangay coverage.
5. Catalog-only polygons with no supported road line remain polygon extents. The repaired two-layer road presentation applies to accepted estimated road corridors; it does not invent a centerline for arbitrary measured polygons.

No commit, push, deployment, paid provider request or live news-to-zone write was performed in this slice.

## Saved browser evidence

Fixture screenshots retain the existing design:

- [Desktop map layers](phase-36-estimated-road-zone-integration-20261006/desktop-news-zone-layers.png), [news details](phase-36-estimated-road-zone-integration-20261006/desktop-news-zone-details.png), [staff summary](phase-36-estimated-road-zone-integration-20261006/desktop-news-zone-staff-summary.png).
- [Mobile map layers](phase-36-estimated-road-zone-integration-20261006/mobile-news-zone-layers.png), [news details](phase-36-estimated-road-zone-integration-20261006/mobile-news-zone-details.png), [staff summary](phase-36-estimated-road-zone-integration-20261006/mobile-news-zone-staff-summary.png).
