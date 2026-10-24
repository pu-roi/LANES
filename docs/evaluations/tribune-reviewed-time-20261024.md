# Tribune reviewed shared time and remaining road polygons

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). October 24, 2026, 11:21 AM Asia/Manila.

## Completed result

The developer explicitly reviewed the article's 4:34 PM clock as an article-wide “as of” time and authorized its application to Quirino Avenue near Guazon Street and Gov. Pascual Avenue in Sitio 6. Zero-provider correction **397** records **September 24, 2026, 4:34 PM PHT** for all three Tribune roads. This is a recorded developer-reviewed interpretation; the original Gemini responses did not supply a clock for the latter two roads and remain immutable. The V3 manifest, identity, adoption receipts and new output timeline snapshots retain that distinction. V1/V2 results remain saved.

The actual cloud preview qualifies both bounded OSM/NOAH road estimates. The selected additional group IDs are `resolved-n5` and `resolved-n7`; existing Boni 80 is not replotted. New zone IDs: **81, 82**. All six active road groups (three GMA and three Tribune) pass hosted desktop/mobile map inspection. News Intelligence retains six flooded-road observations, displays the shared clock on the three Tribune roads and excludes the subsided Quezon City card. Saved cleared evidence remains inspectable. Current API: `lanes-api-tribune-time-20261024-v1`.

Gov. Pascual's source-supported “Sitio 6” is projected as a local-area clue instead of a canonical barangay. This enables the existing authenticated locality-point-to-bounded-road association. Neither the locality point nor the 25-metre policy margin represents measured inundated width. Quirino/Gov. Pascual retain their own eight-inch depth and passable/unspecified-vehicle evidence; Boni retains ten inches and all-vehicle passability. No field is borrowed beyond the explicitly reviewed time context.

## Future article time handling

Location-specific clocks retain precedence. Existing supported heading/scope rules govern shared clocks; an arbitrary first location's clock is not copied across unrelated reports or clearance updates. Active/rising timestamp-free articles may use aware publication time as a recorded `publication_time_fallback` proxy. It does not establish flood onset. Uncited article clocks, conflicting/historical evidence, past supported dates and clearance reports cannot silently acquire this fallback. The Tribune shared-time exception remains restricted to its exact body hash, original response hashes, reviewed roads and explicit V3 identity.

## Verification and preservation

- Normal CI gate: **401 passed**, three optional database/repository skips. Additional selected resolution/Tribune suites: **198 passed**, two optional skips.
- Mandatory isolated PostGIS: **45 passed** with fresh/repeated migration head `f1a9c7e2b604`; no schema or dependency changes.
- Two network-disabled retained-response replays pass. Restored actual-data geometry, stale-preview rejection, late atomic rollback, concurrent application, idempotent reuse and manual-deactivation-to-unified-history checks pass.
- Candidate/serving protected news/source/history/collection/authentication checks and hosted desktop/mobile news/map checks pass. No frontend design or endpoint shape change.
- All original database rows remain unchanged; only the selected correction and two new road outputs plus their supporting records are appended. GMA 388/zones 77–79, Boni 80 and genuine history 76 remain intact. Ordinary routing remains unaffected; new Tribune instances enter existing unified history after final manual deactivation. GMA retains its permanent history exclusion.
- The stopped provider ledger content and object generation remain unchanged at 46 attempts / US$0.7683261 conservative commitment. No new NER, Gemini or token-count requests. Automation stays paused and both expiry flags remain OFF. Four unrelated frontend edits are preserved.

Reader manifest SHA-256: `b3d290134c9c93d3e0fbf18add09661510513f77e2dbfd306a30c1b0dcb53c2d`. Worker release SHA-256: `980e4455c4e5dcb75bcd591a01094ddac2bf52bdfd7eab3dd355e875b618ae66`. Private backups, original responses, grants, fingerprints, cloud receipts and UI evidence: ignored `data/tribune-time-20261024/`.

Source follow-up is published on `roi-branch` in [PR #143](https://github.com/pu-roi/LANES/pull/143). Main review/integration remains pending; no main merge is claimed.
