# Philstar source-bound UP NOAH junction estimates

> **Last Updated:** October 24, 2026, 07:58 PM Asia/Manila

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). October 24, 2026, Asia/Manila.

## Direction and measured evidence

The developer requested plotting the matched Philstar intersections using UP NOAH. Reuse article 274/source 573 and accepted result 401; repeat no NER/Gemini requests and preserve the stopped budget. Both adjoining candidates at NS Amoranto/Don Jose, Palali, Tabayoc and Ubay have 100% hazard-class-3 line coverage in all three checked 5-, 25- and 100-year scenarios. There is no uniquely more susceptible side. This models susceptibility, not observed depth or measured wet extent.

## Explicit estimate policy

The opt-in `source-junction-noah-v1` policy requires two candidates sharing an exact OSM node/endpoint, primary road, article crossing and checked locality. Ground-level ways, complete OSM/NOAH assets and all three scenarios are required. The 25 m radius around that reported junction is an application display window adapting the existing 25 m margin, not a radius stated in the article. Intersect the window with the NOAH envelope, preserving holes/gaps and source-bound road cores. Barangays identify the junction but do not clip a boundary-road display window; the complete window must stay within the checked city. Numerical cut-vertex adjustments remain inside the existing ten-micrometre source precision; original OSM vertices and exact containment predicates are preserved.

Limit this apply to Palali and Tabayoc. Ubay overlaps existing zone 83; NS Amoranto/Don Jose overlaps zone 84 with differing reported depth/access. Keep those cases outside this authority. Bind run 401, its original source/result, two group IDs, assets, application/release identity and the complete preview checksum. Retain article depth/passability independently of NOAH class.

## Execution gates

1. Fresh full backup and row fingerprints; restore into disposable PostGIS.
2. Regress junction identity, wrong/disconnected roads, extra branches, grade, missing assets/scenarios, dry gaps and locality-boundary behavior.
3. Rehearse actual-source qualification, rollback, concurrent application, old/new-policy reuse, no reactivation and deactivation-to-history.
4. Publish a pinned manual worker with zero generation; recompute cloud preview and match the rehearsal before atomic apply.
5. Verify all original records, stopped ledger, unchanged serving API, paused automation and desktop/mobile source/map/history behavior.

Status: complete shared apply for zones/events **88/89**, duplicate-free reuse, **126** scoped checks, restored rollback/concurrency/history rehearsal, original-row preservation and hosted desktop/mobile selected/public map acceptance. [Final evidence](../evaluations/philstar-noah-junctions-20261024.md). Source publication is pending on `roi-branch`. Ubay overlap and Don Jose conflict remain intentionally unresolved; unrelated frontend edits are preserved. No database schema or public API change.
