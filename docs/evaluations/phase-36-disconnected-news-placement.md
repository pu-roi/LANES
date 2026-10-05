# Phase 36: Locality repair and disconnected news placement

> **Last Updated:** October 05, 2026, 7:02 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Later October 5 continuation:** source-alert publication/lifecycle, F6 decisions and F7 desktop/mobile alert views are now implemented locally. This earlier assessment/placement record remains historical; operational zone activation and deployment are still gated. [Current lifecycle evaluation](phase-36-news-publication-lifecycle.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Local code and preview UI implemented. Real barangay polygon provisioning, independent auditing, automatic activation/publication/expiry and production rollout remain pending.

**Subsequent October 5 follow-up:** the [independent evaluation/spatial coverage implementation](phase-36-independent-evaluation-and-spatial-coverage.md) repairs C5 catalog coverage through explicit route relations in the same September 27 snapshot: 45 Pasig ways and 14 ambiguous sections. The earlier zero-section probe below remains historical evidence. Independent auditing/leased evaluation and twenty Pasig OSM community preview polygons, including Ugong, are now delivered locally. The current C5/Ugong probe yields thirteen clipped candidates/250 modeled fragments, eleven disconnected previews and no out-of-boundary linework. Missing barangays, operational flood footprints and publication/expiry remain pending; the original missing-boundary probe below is historical.

## Delivered behavior

`C5 in Pasig City` now keeps Pasig as its city and has no invented barangay. `C5 in Barangay Ugong, Pasig City` keeps Ugong under Pasig. Shared administrative aliases are validated against actual barangays and exact parent identities; a city alias cannot escape as a barangay. Explicit nearby clues and immutable previous extraction runs remain preserved. OSM road matching now equates C5/C-5 spellings (including the Road suffix), and a city qualifier is treated as administrative scope rather than an unmatched landmark.

`BarangayBoundaryProvider` loads versioned, checksummed, reviewed polygons and validates name/PSGC/parent identity, clocks, duplicates, geographic extent and polygon validity. Placement requires the boundary to be contained in the checked parent-city polygon. Missing or incompatible polygons return an explicit coverage reason, never a city-only fallback. The existing OSM catalog is unchanged. Partial sections are clipped; disconnected results get distinct stable candidate IDs. Original reported spans are grounded before clipping, while removed cross-street endpoints cannot supply historical crossing evidence.

The NOAH catalog now exposes exact line/polygon intersections as well as overlap lengths. Typed `modeled_fragments` preserve stable IDs, individual geometries, approximate lengths, scenario/class, NOAH source ID and archive hash. `preview_geometry` dissolves duplicate overlapping linework across all 5/25/100-year classes into a modeled envelope, merging only touching pieces. A real gap in that envelope remains a gap. Differences between individual scenarios remain in fragment evidence. This envelope is a placement suggestion, not an observed flood footprint; source susceptibility never supplies current depth, status, passability or routing geometry.

Each candidate reports `fragment_status`; zero overlap and point-only contacts have no preview geometry. Missing/corrupt sources or more than 512 fragments per candidate return explicit failures and suppress partial map fragments. Candidate centerlines and earlier overlap/history fields remain available for inspection. Claimed depth supplies backend `reported_severity` through the existing gauge mapping; absent depth remains unknown.

Spatial Operations renders the backend preview geometry with shared `PENDING_REPORT_ROAD_AURA_PAINT` and existing severity colors, or gray for unknown depth. Blue dashed suggestion lines are replaced with the lighter aura only. Selection, click handling, style reload, layer cleanup and desktop/mobile Evidence/Map switching remain. Full candidate roads are not substituted when modeled fragments are unavailable. Citizen report and Active Zone layers are unchanged. Explanatory text distinguishes the modeled envelope from reported flooding.

## Storage, APIs and assets

The existing protected placement GET and shared captured-article extraction return additive fragment/boundary/severity fields. No route, auth policy, SQLAlchemy model, migration, dependency or public write was added. `rules-spatial-preview-v11` and a hashed analytical revision distinguish new results; source identity now includes the barangay catalog and fragment policy. Existing extraction results remain immutable and are not backfilled or reprocessed by this task.

No verified real barangay polygon catalog was available in this checkout. Tests use clearly synthetic polygons with real reference identities; they do not establish real Ugong boundaries. Configure `LANES_NEWS_BARANGAY_DIR` for both API and extraction/evaluator processes after source review. [Asset contract](../guides/news-barangay-boundary-assets.md). Existing city/NOAH assets were not refreshed, and no cloud deployment occurred.

## Verification

- Final combined backend run: **226 passed** across extraction, shared location normalization, OSM aliases, matching/context, administrative clipping, NOAH fragments/limits, immutable processing/results and article replays. Includes C5/C-5 alias regressions and administrative-only qualifier handling. Earlier targeted runs overlap this combined count.
- TypeScript (`tsc --noEmit`) and scoped ESLint passed for modified frontend code/tests.
- Ten desktop/mobile placement cases passed: mixed queue, aura rendering/selection, style replacement/cleanup, mobile Map/Evidence, unresolved placement, source failure, rate limit and queue failure. Pixel checks were updated to detect severity auras rather than the old blue line treatment.
- Four additional responsive/active-zone/Create Zone regression cases passed; two project-inapplicable cases were intentionally skipped. **14 distinct browser cases passed, two skipped**. These use mocked authenticated API responses and an empty fixture basemap, not live production evidence.
- Generated desktop and mobile map screenshots were visually inspected: disconnected yellow auras, stronger selection opacity and no solid news core. Backend tests establish gap geometry, source provenance and no publication/routing eligibility.

**Real local asset probe:** constructed C5/Pasig text now extracts the city without inventing a barangay, and C5/C-5 catalog identities match. The current city-only probe still returns `named_road_sections_not_found`: all 85 indexed C5/C-5 ways in this catalog lie outside the Pasig polygon. Real Pasig C5 alias/road coverage needs a source-catalog update; the matcher does not infer aliases for unrelated named roads. Adding Ugong returns `missing_valid_barangay_boundary` because no real reviewed polygon catalog is installed. These are explicit unresolved results, not a successful live C5 flood footprint. A separate constructed C. Raymundo/Pasig claim against real local OSM/NOAH/history assets produced 25 candidates and 141 modeled fragments; 13 candidates have disconnected display geometry. The result remains `unique_ranked_prediction_not_verified_flood_extent`, with routing disabled. Neither constructed probe establishes current flooding.

## Remaining operational work

Provision real reviewed barangay polygons, reconcile their parent-city coverage and deploy matching analytical assets. Then implement the independent auditor and durable claim/evaluation/decision services, public activation/correction/expiry and F6/F7 against the existing readiness contract. Selecting a fragment does not approve an operational zone. The accepted two-hour fallback and Active/Unconfirmed/Cleared semantics remain future runtime work.
