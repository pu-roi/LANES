# Phase 36: Article and DRRMO Road-Section Context Check

> **Checked:** September 30, 2026 by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The read-only `article_road_context_service.py` now takes an `ExtractedClaim`, a checked city polygon, and bounded OSM road sections. It excludes sections outside the checked city. An explicit two-cross-street span must match both ends of a section; an unmatched span does not fall back to a hazard-only guess. A named crossing keeps the adjacent sections as candidates. A barangay narrows sections only when the caller supplies a checked polygon covering the entire centerline. The service does not infer a barangay from an unverified name.

For Pasig claims, the service reads the cleaned DRRMO CSV row by row. It attaches a row only when the named road and a mapped crossing agree, with the article's barangay checked when stated. A road-only row or an unlocated shop remains in `unmatched_history_rows`. A similarly named road such as G. Raymundo Street cannot support C. Raymundo Avenue. Non-Pasig claims never use the Pasig CSV. Row counts are source records, not independent event counts or current observations.

The existing `audit_noah_ranked_road_sections.py` accepts a saved claim JSON and optional Pasig CSV. It passes article place level and grounded row counts to the existing three-scenario NOAH ranker. It remains a local command, not an operational provider.

With the repository's Pasig polygon, local Metro Manila OSM PBF, all three local NOAH ZIPs, and a **constructed** `C. Raymundo Avenue near Bernal Street` claim, the audit found 25 between-intersection sections, then narrowed to the two adjoining Bernal Street sections. Three real DRRMO CSV rows naming the Rosario/Bernal corner support both. NOAH ranks one side ahead on its numerical tie breakers; this is a location hypothesis, not evidence that only that side is flooded or a routing decision. Eleven other C. Raymundo-related rows were not grounded to these two candidates. The script did not write a Flood Report, alert, zone, or route.

Focused tests: 21 passed across the new context service, road matcher, and NOAH ranker. The tests cover Pasig-only history, exact road and crossing identity, the real Bernal DRRMO rows, explicit-span rejection, and city/barangay polygon scope.

Still open for Gate 3: feed actual saved RSS extraction claims into this provider; obtain checked barangay and city boundaries across Metro Manila; geocode non-road landmarks without inventing coordinates; validate OSM carriageways and source coverage; set the decision margin and automatic outcome for two adjacent or several separated candidates. The current ranking's unique top result is not sufficient on its own to certify a live flood footprint or close a road.
