# Phase 36: News Claim Activation Safety Gates

> **Drafted:** September 27, 2026 by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Decision states

Each extracted location is an independent claim. A claim can be `flagged_review`, `suppressed_forecast`, `suppressed_negated`, `suppressed_subsided`, or `auto_approved`. Automatic operation is the intended path for complete current claims; staff review is for exceptions. An otherwise credible claim lacking exact road closure geometry should become a prompt, source-labeled public news alert once that separate feature exists, without changing routing. Simulation output and a location suggestion are not public map zones. The current geometry provider still sends active claims to `flagged_review` because it cannot verify an affected segment.

## Required evidence for a future automatic zone

1. **Source and time:** An approved publisher or authenticated staff submission has a traceable URL or source identity, complete evidence text, a publication timestamp, and an explicit recent flood observation timestamp. A fetched-at timestamp and article publication time do not establish flood onset or current status. Historical articles are review-only.
2. **Flood status and road access:** The sentence describes observed active or rising flooding. Forecast, negation, and subsided claims are suppressed. A road explicitly passable to all vehicles must never generate an avoidance closure. A light-vehicle closure must retain its vehicle class and cannot be promoted to an all-vehicle closure.
3. **Depth:** Preserve the source measurement and qualifiers. A canonical gauge key can be assigned only under the documented mapping. A shared range or an area-level depth must not become an exact measurement for each road.
4. **Place:** The road or landmark must be tied to an unambiguous parent city and the affected segment or locality. Repeated road names and a single road mentioned in two barangays remain separate claims. City or barangay mentions alone cannot close an entire jurisdiction.
5. **Geometry:** A map candidate must record the geometry source and the exact evidence it matches. Offline coordinates, generated centerline rectangles, city/barangay buffers, and an entire OSM road way are suggestion previews only. Pasig DRRMO history and LiPAD/UP NOAH susceptibility layers can help rank and corroborate locations but cannot by themselves prove that a specific segment is currently flooded. Automatic routing activation requires a checked, bounded road segment or landmark footprint with geometry provenance and conflict resolution. The current service does not yet produce such verified geometry; see [spatial integration plan](lipad-noah-flood-placement.md).
6. **Independent audit:** A successful external audit must explicitly confirm the same place, active status, and claimed depth. Missing credentials, timeout, malformed response, or audit disagreement go to staff review. The deterministic extractor is the primary parser, not a substitute independent auditor.
7. **Decision and persistence:** The decision must be made before any public report, event, or zone insert. The ingestion service must check the same gates independently so a stale `action_type` cannot bypass them. A complete claim proceeds automatically; missing closure evidence uses the fast public alert path once implemented, with staff correction available. Staff decisions and automatic activations need durable per-claim records and an audit trail, designed before any database schema change.

## Confidence

The existing `0.95` and post-decision `0.98` values are ranking heuristics, not calibrated probabilities. They must not justify automatic publication. Keep a score only as an explainable suggestion ranking until a labeled real-article set measures false activations and the threshold is approved.

## Current rollout boundary

The collector saves candidates and is not connected to `NewsAutoIngestionService`. The three August 2026 publisher examples are simulations. The activation code remains capable of automatic publication when every gate passes; the current geometry provider never marks a segment verified. Gate 3 will integrate spatial evidence, Gate 4 will connect fast alerts and automatic zones, and Gate 5 will provide staff exception decisions.
