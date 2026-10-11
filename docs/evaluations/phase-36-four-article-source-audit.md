# Four-article source, database and display-contract audit

> **Last Updated:** October 03, 2026, 8:09 PM
> Author: [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Scope and source coverage

The developer requested a complete recheck of News Intelligence and News Flood Details against saved records and original articles. Three actual agents independently checked source content, database/API parity and presentation. Every current publisher body was fetched again through the normal bounded fetcher into separate ignored captures; all four bodies were byte-identical to the original captures. Originals were not overwritten.

| Source | Reporting-body sites | Audited meaning |
| --- | --- | --- |
| [September 9 Philstar](https://www.philstar.com/nation/2026/09/09/2555106/list-flooded-metro-manila-areas-september-9/amp/) | 27 | Five all-vehicle closures, two light-vehicle closures, twenty caution reports; supported shared 4:30 PM list scope |
| [September 9 GMA alert](https://www.gmanetwork.com/news/topstories/metro/1001693/list-flooded-roads-in-metro-manila-wednesday-sept-9-2026/story/) | 3 | Separate Malabon/Marikina sites; qualitative gutter depth, all-vehicle passability, 2:47 PM observations supported by the explicit same-day update |
| [September 9 GMA evening](https://www.gmanetwork.com/news/weather/content/1001808/several-metro-manila-areas-flood-due-to-habagat/story/) | 3 | Three named Manila/Quezon City body roads; no fabricated depths, passability or observation clocks |
| [September 24 event, Tribune](https://tribune.net.ph/2026/09/24/minor-flooding-hits-some-metro-areas) | 5 | One explicit all-vehicle report, two generally passable corridors with vehicle classes unstated, two cleared roads with separate bounded clearance clocks |

No missing named reporting-body road was found in these four articles under the existing conservative reading policy. This is not a guarantee for arbitrary future articles. Captions, warnings, unnamed areas and the unbounded GMA pump-water context were inspected separately, rather than treated as missing confirmed road closures.

## Reproduced defects and local v9 corrections

- **Source precision:** summary preferred the canonical formatted gauge over raw source depth. GMA gutter descriptions appeared as measured eight-inch depths, and Tribune's approximate Quirino depth appeared exact. Summary now prefers reported wording; normalization fields stay intact in the saved claim. Legacy formatted-only claims retain their available fallback.
- **Missing generic passability:** the developer delegated the contract decision. Added `passable_unspecified`, displayed as **Passable; vehicle types not specified**, with an explicit no-automatic-closure guard. Only a bare inline statement, one adjacent road, or exactly two adjacent same-paragraph corridors can supply it; exact source offsets are expanded. Specific restrictions/caution take precedence. Unsupported heavy-only/bus-only wording stays unknown.
- **Wrong provinces:** administrative homonyms supplied Laguna, Quezon, Pangasinan or Negros Occidental to four roads whose city/PSGC was already grounded in Quezon City or Manila. Ranking now derives province/island fields together from the grounded parent city; NCR has no provincial label. Valid outside-NCR parent provinces remain intact, and an unresolved road does not inherit a homonym's province.
- **Clearance meaning:** two subsided-road timestamps were labeled as flood observations. Resolved clearance observations now use a subsidence label and preserve the source's **by** bound. Forecast, negated and historical flags cannot trigger this label.
- **Exclusion explanation:** a missing affirmative observation alone no longer receives the combined forecast/past/absence explanation. Existing conservative reading eligibility is unchanged.

The pipeline is `rules-psgc-osm-2026-10-03-v9`, extractor `taglish-rules-v1.7`. No SQLAlchemy model, Alembic revision, dependency or frontend source changed. Existing JSONB stores the additional claim value; backend-owned labels serve the existing shared mobile/desktop layouts. No production configuration, collector schedule, source registry or map publication changed.

## Verification and saved state

- **595 related backend tests passed**, including the prior 555 cross-system checks and new source-precision, passability and province-parent cases. One existing multipart deprecation warning remains. A separate agent's broader run encountered Windows temporary-directory setup permissions; the parent completed suite above passed without setup errors.
- Guarded private reprocessing added four new immutable runs, one per article. The database now contains four articles, five source versions and fourteen runs; the main list remains **38** locations. Old snapshots/results are preserved. Repeating identical September 9 processing creates no extra records.
- Final audit used an explicitly read-only PostgreSQL transaction and compared all 38 stored/latest claims, detail responses, summaries, evidence offsets, source fingerprints, four article histories and Collection data. Both real backend and frontend proxy endpoints match, with **zero mismatches** and unauthenticated 401 responses. The corrected province findings are absent.
- September 9 remains 33 locations and twenty caution records. September 24 remains five locations, with the two generic-passability records and the two clearance labels corrected. Reports and avoidance zones remain zero.
- The backend was explicitly restarted to serve final v9 code. Deterministic tests use generated source paraphrases; original/fresh bodies and private audit outputs remain ignored.

## Limits and remaining decisions

The browser tool again rejected access to the open loopback page because a saved browser preference blocks it. No alternative browser, raw browser commands or indirect visual-verification workaround was attempted. **Actual visual page/modal acceptance is incomplete**; API parity and component rendering-contract review are complete, not substitutes for a screenshot-based display check.

Collection retains three September 9 articles needing checks and one ready Tribune article. Ready means readable source-backed locations, not current flood confirmation or fully specified facts. Caption-only records remain excluded. Some GMA caption exclusion explanations could identify caption provenance more precisely; this is an open explanation refinement, not permission to promote captions. The pump report provides an unbounded water-accumulation area rather than a measured, timed road restriction. No third Quezon City road is invented from Tribune's unnamed three-area reference; G. Araneta/Baloy's source depth remains unknown.

Minor source aliases/separator formatting remain traceable in evidence. The existing freshness gap, scheduled GDELT integration and automatic verified map placement/publication remain separate pending work. These follow-up fixes are local and uncommitted; the prior v8 commit remains the last pushed bundle.
