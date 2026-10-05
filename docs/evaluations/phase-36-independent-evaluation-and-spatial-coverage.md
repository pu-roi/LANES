# Phase 36: Independent evaluation and spatial coverage

> **Last Updated:** October 05, 2026, 7:02 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Independent evaluation/spatial coverage implemented locally in parallel, including twenty reviewed OSM community Pasig polygons. The later source-alert lifecycle and F6/F7 interfaces are delivered locally; remaining locality coverage, operational flood footprints/activation and deployed public-map acceptance remain pending.

**Later October 5 follow-up:** [Automatic source-alert lifecycle](phase-36-news-publication-lifecycle.md) records locked publication, qualified refresh/clearance, two-hour Unconfirmed expiry, finite retention, staff controls and public desktop/mobile text-only alerts. The earlier evaluation below remains its separate verification checkpoint; no operational zone activation is implied. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Independent evidence evaluation

Fixed the auditor's provider credential crossover and incomplete article context. `news_claim_auditor.py` uses explicit provider/model configuration, separate OpenRouter/Gemini transports, trusted system instructions and full immutable publisher evidence as untrusted data. Strict structured responses carry place/status/time/depth/access confirmations, exact quotes/offsets, original qualifiers, source/claim hashes and provider request identity. Local PSGC parent/alias checks retain supported spelling variants while rejecting impossible parents. Forecast, negation, historical evidence, conflicting updates, bad JSON, fabricated evidence and unavailable providers remain unconfirmed. Unknown depth can stay unknown without an invented measurement.

Twenty-second total deadlines, input/response budgets, disabled redirects, bounded response streaming, strict response fields/duplicate-key validation and sanitized failures apply. No live or paid provider call was made. Model availability and production credentials remain unverified. A nonsecret configuration revision supports recovery after repaired credentials without changing or deleting a finalized evaluation.

Added `crud/news_evaluation.py`, `services/news_evaluation_service.py` and `scripts/evaluate_news_claims.py` using the five approved publication tables. Completed extraction is independently committed. An explicit bounded seed step validates source snapshots, completed result identity/offsets, current policy/assets, source approval and admission before creating unpublished cases/source bindings/evaluations. Retries reuse run/ordinal/hash identity. Different extraction runs receive separate unpublished cases; continuity is not guessed from ordinal or proximity.

Evaluation leases are committed before external requests. Concurrent binding serializes the immutable run; `SKIP LOCKED`, UUID ownership, expiration, five attempts and bounded retries protect worker recovery. A lost lease writes no terminal result and is not repeatedly reclaimed by the same batch. Storage failures propagate. Completion records both publication and observation freshness. The two-hour observation fallback and twelve-hour admission gate remain distinct; a recent fetch or retry cannot refresh old observed evidence.

Terminal evaluations are immutable. This slice creates no decisions, citizen reports, domain events, operational zones or public state; completed results explicitly deny publication/routing permission. The existing extraction worker and deployed discovery scheduling are unchanged. [Evaluator runbook](../guides/news-claim-evaluation.md).

## C5/Pasig source coverage

The September 27 PBF already contained road-route relations **417210** and **14448353** with `ref=C-5`, including Pasig sections named E. Rodriguez Jr. Avenue. The catalog builder previously retained way names/alternate names but omitted those relation references. It now retains explicit `type=route, route=road` references and their relation IDs; bus-route membership never becomes a road alias. No guessed C5-to-street dictionary was added. [OSM route schema](https://wiki.openstreetmap.org/wiki/Relation:route).

Rebuilt the bundled catalog from the **same** original PBF: 66,129 named ways, seventeen checked city boundaries, three incomplete named ways and 5,257 route-referenced named ways. Expanded catalog SHA-256: `5edd1284a00003ed2d97ff7d500f02b58d7f53521864e149311628df3d338386`. Source snapshot and original PBF checksum remain in the [bundled manifest](../../backend/runtime_data/osm/manifest.json). Future extraction policy identity changes with the catalog digest; existing extraction is not rewritten.

Real local C5/Pasig audit now finds **502 NCR matches, 45 ways with positive length inside Pasig and fourteen ambiguous road sections**. The earlier zero-section result is resolved for candidate geometry. These are road candidates, not current flooding, known affected length/width or automatic-zone eligibility. Disconnected NOAH fragments remain modeled susceptibility.

Added read-only spatial auditing and offline immutable-version barangay provisioning with archived source checksums, explicit licensing/reviewer metadata, PSGC identity and strict checked-city containment. Parent disagreements now return `barangay_boundary_parent_mismatch`, separately from absent coverage.

## Real barangay source findings

The [GeoRisk PSA barangay service](https://ulap-nga.georisk.gov.ph/arcgis/rest/services/PSA/Barangay_2020/MapServer/0) returned JSON error **499, Token Required**, so public search metadata did not establish downloadable polygons.

The accessible [Pasig barangay layer](https://services1.arcgis.com/GMAJGrCZkLEPNMcz/ArcGIS/rest/services/PasigBarangay/FeatureServer/1) cites generalized 1986 atlas/2000 NSO source data and exposes twenty-four valid polygons against thirty current reference barangays. Ugong is missing; only eleven polygons pass strict containment in the checked OSM Pasig city boundary. Licensing/redistribution terms were not established. These findings prevent installing it as reviewed road-scale runtime coverage. Tiny original metadata/query responses, capture checksums and local coverage audits are retained under ignored `data/news_spatial_source_review_20261005/`; none were installed as approved assets.

The same archived PBF also supplies acceptable **OSM community administrative polygons for twenty of Pasig's thirty barangays**, including Ugong relation **108731**. Its explicit OSM reference `137403029` corresponds to current PSGC `1381200029` through the bundled reference's correspondence column. The builder accepts only exact code/name/parent identities, complete original rings, valid unsimplified polygons and containment within the checked same-snapshot Pasig boundary. No rings were repaired or snapped. Source classification, relation URLs, ODbL attribution, actual automated reviewer and exclusions are retained in the [installed catalog](../../backend/runtime_data/barangay/README.md); this is not official legal or field verification. Boundary catalog SHA-256: `4b596be585945502fffd1ca9e14f282fb5a10e3b844c3ca2b21eda1a157894c2`.

The real installed **C5 + Ugong/Pasig** preview produces **thirteen clipped candidates, 250 modeled fragments and eleven disconnected display geometries, with zero candidates or fragments outside Ugong**. It remains `predicted_candidate` / `unique_ranked_prediction_not_verified_flood_extent`, with current-flood proof and routing permission false. Additive API provenance includes barangay source classification, OSM relation ID and source URL.

**Bambang, Kalawaan, Malinao, Palatiw, Pinagbuhatan, San Joaquin, San Miguel, San Nicolas, Santa Cruz and Santo Tomas** remain uncovered or excluded. Their explicit reasons remain visible; no broader city or synthetic polygon fallback is installed. Remaining geometry work must expand suitable source coverage and establish supported operational affected-footprint provenance. A centerline, hazard envelope or arbitrary buffer cannot substitute for observed flooded width.

## Verification

- Combined backend regression: **449 passed** across twenty auditor/hybrid/access/ingestion/saved extraction/processing/geometry/extraction/replay/preflight suites. Targeted earlier selections overlap this count.
- Native evaluation/PostGIS: **20 passed**, full existing Alembic history upgraded to `d7e4b9a21c60` in a fresh disposable loopback database, then that database removed. Covers concurrent binding/leases, retries and crashed-worker exhaustion, lost leases, policy/config recovery, immutable history, adapter MockTransport integration, completion freshness, storage failure, admission/cursor/repeat guards and absence of publication/domain writes.
- Read-only `validate_run` compatibility probes rejected none of 154 deterministic outputs/320 claims or 43 captured article outputs/1,965 claims. Historical captured evidence was not activated or inserted into normal storage.
- Existing multipart deprecation warning remains. No new dependency, SQLAlchemy model or migration change. No frontend edit or new desktop/mobile acceptance claim.

Docker initially reproduced the ingest socket startup failure. After Docker stopped, both exact runtime socket directories were preserved under unique backup names and recreated. Existing PostGIS and Valhalla containers resumed; no factory reset, volume removal or application/cloud database cleanup occurred. This repeats the local [documented socket workaround](../others/bug-log.md#bug-100-local-docker-startup-fails-on-stale-windows-unix-sockets), not an upstream permanent fix.

## Next integration

Implement atomic eligibility decisions, freshness/expiry/correction/shared-support lifecycle and safe public reads; connect supported operational geometry only when its source gates pass. Then reuse existing desktop/mobile zone rendering for F6/F7 and run end-to-end acceptance. Branch commits, push, release, migration of normal/cloud storage and scheduling of the evaluator were not performed by this task.
