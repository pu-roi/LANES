# September 9 historical news plotting simulation

> **Last Updated:** October 09, 2026, 12:41 AM, Asia/Manila
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Result

Replayed three captured September 9 reports through the real RSS parser, discovery admission, article parser, rules extraction and current OSM/NOAH estimated-road builder. Discovery admits all three articles; extraction produces 46 raw claims and 33 readable locations. **Zero estimated plotting polygons are generated.** This event cannot exercise automatic zone publication with the current placement assets.

At one minute after each captured article version first became available, 30 readable claims pass the initial local evidence checks. Three evening claims lack a supported observation time. These checks do not replace independent auditing or establish publication eligibility. No provider request or database write was made.

## Source selection

The [September 9 Philstar flood list](https://www.philstar.com/nation/2026/09/09/2555106/list-flooded-metro-manila-areas-september-9/amp) reports named Quezon City roads, depths and vehicle restrictions, with observations at 4:30 PM and publication at 5:03 PM. Its original page/date were verified using web search/read. The previously captured GMA afternoon alert and evening Habagat report supply the other two article bodies. A fresh web-tool fetch of the GMA afternoon URL returned HTTP 403; original local captures were used rather than fabricated replacements.

The [September 24 Daily Tribune report](https://tribune.net.ph/amp/story/2026/09/24/minor-flooding-hits-some-metro-areas) is another confirmed September event, published September 25. It names Boni, Quirino and Gov. Pascual avenues and distinguishes cleared Quezon City roads. September 9 was selected because its detailed afternoon list was published within the observation-evidence window.

RSS inputs are reconstructed from publisher metadata, **not archived authentic feeds**. Historical source verification is reconstructed by the existing replay helper, not proof of the actual September registry. Original article/observation dates are retained. Existing replay assets remain private and Git-ignored.

## Actual stage outcomes

| Stage | Observed result |
|---|---|
| Reconstructed RSS and captured-body discovery | Two feeds parsed; three articles admitted; no discovery notices or extraction errors. |
| Extraction and reader eligibility | Philstar: 27 readable locations; GMA afternoon: 3; GMA evening: 3. Thirteen other raw claims are hidden source context/caption evidence. |
| Initial evidence checks at first available snapshot + 1 minute | Thirty pass; three fail `missing_supported_observation_time`. Philstar replay time is 5:04 PM; GMA afternoon is 3:10 PM, respecting its updated snapshot rather than its original morning publication. |
| Real estimated-road builder | 22 `missing_valid_barangay_boundary`; 7 `no_reported_road`; 2 `candidate_set_truncated`; 1 `named_road_sections_not_found`; 1 `missing_explicit_bounded_span`. No geometry generated. |
| Existing 11 PM replay clock | Thirty afternoon observations fail `observation_evidence_expired`; three evening claims still lack supported times. Delayed collection cannot reset observation expiry. |
| Independent AI audit | Not executed; no external provider request. |
| PostGIS publication, zone creation and Active Zones API | Not executed: Docker daemon is unavailable and the isolated local PostGIS database cannot run. The normal/cloud database is untouched. |
| Regression verification | **84 passed** across September 9 replay/extraction, September 24 extraction and estimated-road suites. Synthetic successful corridor tests establish the builder's supported path, not successful plotting of this event. |

## Placement limitation and next acceptance

The checked news-placement barangay catalog has 20 Pasig barangays; the failed qualified claims here name Quezon City and Malabon communities. Seven list entries do not resolve to a canonical road. Other road mentions have insufficiently bounded or ambiguous candidate sections. The separate complete Pasig prediction-location catalog does not supply validated news boundaries for these cities.

No safety gate was relaxed to manufacture a successful plot. Expand source-validated news boundaries and resolve supported road identities/sections, then restore isolated PostGIS and replay with the same original timestamps plus an explicitly identified independent audit. Full publication and frontend map acceptance remain unverified; no browser was opened.

Local structured evidence: `data/news-replay/september9/recheck-20261009.json` and `data/news-replay/september9/plotting-simulation-20261009.json`. The latter records each readable location's original time, initial evidence reason and real builder outcome. No application code, schema, dependency, cloud setting or live flood record changed.
