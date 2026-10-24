# News Flood Details to Active Zones handoff

> **Date:** October 25, 2026, Asia/Manila
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Implemented and verified locally; included in the requested `roi-branch` source publication. Deployment remains separate; no production-data operation.

## Cause and change

The existing Inspect placement on map button navigated to `review_news=run:ordinal`, selecting Needs Review and its placement preview even when the observation already had a saved active zone. It could not hand off native observations without a projected ordinal.

The button now calls staff-authenticated `GET /api/v1/admin/news/results/{run_id}/map-target` with either a saved claim ordinal or native group ID. FastAPI validates that saved identity and follows existing exact publication-zone links or native historical-import run/group lineage, using the normal active/expiry policy. It returns the first active linked zone in stable ID order; multiple zones are never combined or inferred from proximity. No placement computation, publication, evidence editing or write is performed.

A linked observation navigates to `/admin/map?tab=zones&focus_zone_id={id}`. Spatial Operations fetches that specific zone independently of list pagination or the current viewport, opens Active Zones, selects/highlights its card and geometry, and uses the existing zone camera flight. Mobile opens the map automatically; the flight waits for its visible canvas. Returning to the list retains selection. Ordinary refresh does not repeat the handoff flight.

Observations without an active linked zone retain their saved placement-review route when a projected claim exists. A native observation with neither an active zone nor projected placement shows an explicit modal message. Lookup failures remain in the details dialog with the existing action available for retry. A zone deactivated between lookup and arrival produces a visible Spatial Operations error.

## Verification

- **39 backend checks pass** against a disposable PostgreSQL/PostGIS database, covering native exact run/group links, active/expiry/pause behavior, read-only queries, identity validation, ordinal-free API results, staff session enforcement, no-link fallback and safe storage errors, plus existing result/group routes. The initial 38-case run also passed before adding ordinal-free API coverage.
- **14 desktop/mobile browser cases pass**: ten new handoff cases plus four existing source-summary/verification-notice cases. They exercise actual modal navigation, delayed zone retrieval, selected MapLibre geometry/camera, retained card selection, native ordinal-free groups, unrelated initial viewport records, error/retry, unplotted fallback and deactivation races. Desktop/mobile screenshots were inspected; the basemap/API are synthetic fixtures, while MapLibre selection and camera checks use the actual browser map instance.
- Initial browser failures were test synchronization issues: a cold Next.js route compilation exceeded the default five-second URL assertion, and a camera assertion ran while the 1.5-second flight was still moving. Assertions now wait for route completion and the final camera location.
- TypeScript and scoped lint pass for the news components/API client and new browser test. `LiveMapPage.tsx` retains exactly its committed lint baseline (**10 errors / 13 warnings**); comparison shows **zero new diagnostics**. An initial synchronous handoff effect was changed to the existing animation-frame scheduling pattern before final verification. Unrelated lint findings are not silently repaired.
- New API/PostGIS regressions are included in the existing Cloud Build runtime and mandatory disposable-history test lists.

No SQLAlchemy model, Alembic migration, dependency, flood geometry, source text, source measurement, approval rule or production setting is changed. Existing admin controls and responsive layout are retained.

## Source publication checkpoint

[@roicambe](https://github.com/roicambe) (Roi Cambe). October 25, 2026, 4:39 AM PHT. The developer requested a senior-planner update and push to `roi-branch`. Author/branch identity and matching remote head `d328b382` were checked before the full-tree commit. No new Python/Node dependencies or database models/migrations are present; the passing PostGIS fixture applied the existing migrations to a disposable database. Python AST/JSON syntax, changed-file credential patterns and documentation links are audited before staging.

This source checkpoint also includes the pre-existing [SOP 1 presentation guide](../capstone/sop1-presentation-guide-20261025.md) and its [dated cloud-state evidence](sop1-system-audit-20261025/cloud-state.json), as required by the repository's full-tree push protocol. Their recorded investigation remains separate from the map-handoff implementation and is not repeated by this push. Tech-stack, architectural decisions and database-design records require no structural update because packages, architecture and schema are unchanged. The existing feature reference is not expanded for this routine integration fix.

The commit carrying this record packages the verified source and CI gates. Deploy the new backend map-target endpoint with its matching frontend before accepting the feature live. No main merge, deployment, provider request, production setting edit or flood-record write is part of this publication.
