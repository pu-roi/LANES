# Phase 36: Reusable Article-to-Road Match Check

> **Checked:** September 29, 2026, 5:18 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The new `backend/app/services/article_road_match_service.py` accepts an extracted road claim, named OSM ways from a bounded local PBF search, a checked city polygon, and optional barangay polygon. It returns a source-identified centerline candidate or an explicit unresolved reason. It does not label the line as an observed flooded extent, generate a routing polygon, write to PostGIS, or activate a zone. `backend/scripts/audit_article_road_span.py` now calls this service for its OSM decision and retains its read-only NOAH overlap calculation.

The matcher recognizes exact normalized road names, `Sto.`/`Santo` and common road suffixes, OSM `alt_name`, an explicit `between A and B` span, and `from A to B` wording. A suffixless cross-street name must exactly match an OSM name without its road suffix. It requires one shared OSM junction at each crossing, a connected unique named-road path, containment in the supplied city polygon, and containment in a supplied barangay polygon when the claim names one. A second path, including a longer carriageway, overlapping OSM ways, or bridge/tunnel/layer tag leaves the claim unresolved for review.

## Local read-only checks

| Claim/input | Result |
| --- | --- |
| GMA August 29: Sto. Domingo Avenue between Atok and Calamba Streets, Quezon City | One 86.2 m centerline candidate on OSM way `9793981`, junctions `60449727` and `43082816`, inside OSM Quezon City relation `106569`. The local three NOAH source vectors each overlap the full candidate line at modeled `Var=3`. This repeats the prior research finding through the reusable service. |
| PNA August 17 expected-facts phrase: Araneta Avenue from Maria Clara to Florentino, Quezon City | `missing_or_ambiguous_cross_street_junction` in the bounded local extract. No candidate or zone was produced. This is a tracked fixture phrase, not a fresh publisher-body retrieval; the PNA article has recently returned HTTP 500. Road-name and cross-street aliases need source checking before the matcher can resolve it. |

The PBF and NOAH archives are ignored local research files. Their operational update policy, full Metro Manila coverage, NOAH vintage, and authoritative barangay boundary source remain open. The manually supplied box and OSM city relation still prevent this command from being a production provider. Neither a unique OSM centerline nor modeled hazard overlap proves current flooding, its carriageway direction, or the actual flooded width.

Five new service tests and six existing span-audit tests passed (`11/11`). They include a longer alternative carriageway, unsupported unbounded wording, missing or conflicting barangay geometry, grade separation, and a `from A to B` alias case. The real GMA read-only command succeeded; the PNA read-only command correctly stopped unresolved. No database or public-map operation was run.
