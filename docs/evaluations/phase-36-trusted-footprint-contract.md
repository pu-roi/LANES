# Phase 36: Trusted current incident footprint contract

> **Last Updated:** October 05, 2026, 11:28 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** BUG-110 contract implemented locally; this historical checkpoint records its verification. The [later worker integration](phase-36-automatic-footprint-worker.md) passes locally; real current footprint provisioning and desktop/mobile map integration remain open.

Valid shapes and arbitrary source labels can no longer authorize operational news zones. Approval comes from an operator-owned current incident catalog or an authenticated staff review of the exact claim and footprint. Missing approval stays a source alert. This delivers the contract prerequisite, not automatic news-derived polygons on the public map.

## Contract and implementation

`validate_operational_shape` checks Polygon/MultiPolygon topology, explicit WGS84 declaration, actual Shapely SRID, two-dimensional coordinates and full locality coverage. Every component needs at least 1 m²; limits are 25 components and 10,000 coordinates. Empty, negligible, invalid and oversized geometry rejects without repair, clipping, reprojection, dropping parts or bridging gaps. `validate_operational_footprint` additionally requires the private server-approved binding. Client labels/checksums and `allow_unverified=True` cannot supply that approval.

GeoJSON uses WGS84 longitude/latitude under [RFC 7946 §4](https://www.rfc-editor.org/rfc/rfc7946.html#section-4). Coordinate ranges alone do not establish a Shapely SRID: newly created geometries default to 0. [Shapely SRID reference](https://shapely.readthedocs.io/en/stable/reference/shapely.get_srid.html). Full coverage uses `parent.covers(footprint)`, including holes and boundary contact; any point outside the parent rejects. [Shapely coverage reference](https://shapely.readthedocs.io/en/stable/reference/shapely.covers.html). These library semantics inform the contract; they do not prove current flooding.

The evidence service resolves the reported city and, when named, its qualified barangay from existing checksummed locality assets. Missing named barangay never falls back to a city polygon. Boundaries constrain placement; OSM/NOAH/historical/community geometry cannot independently establish a current affected extent.

The server-approved binding records article ID, immutable input/claim hashes, incident identity, observation time, canonical city/barangay, SRID, boundary revision, parent/whole/component geometry hashes and approval identity. Current observation must satisfy `observed_at <= now < observed_at + 2 hours`. Authoritative records include catalog digest and record ID. Staff reviews record the stored active/capable actor and request UUID with a server-derived review checksum. Deleted, inactive and Commuter actors reject. Staff classification remains explicit rather than being relabeled as authoritative data.

Automatic activation requires `geometry_srid=4326` and `evidence_record_id` alongside existing revision/source/policy inputs. Staff preview and submit require `operational_footprint_srid=4326` with geometry and run the same approval checks. Empty submitted geometry rejects. Request identity includes declared SRID and record reference; exact retries return the original result without extending lifetime. Existing-zone relinking requires matching article/incident provenance and unchanged accepted component geometry/depth/access; legacy unbound attribution is readable but cannot authorize relinking.

Newer article evidence cannot silently renew an old perimeter. Renewal needs one current approved record for the exact new input/claim/observation, identical extent, matching persisted components and metadata, and active unexpired linked zones. Otherwise the new decision is a text-only Active alert with `newer_observation_footprint_unverified`, a private failure reason and no routing geometry. The prior case's unsupported links are withdrawn; independent citizen/news support remains protected. Changed extent/depth needs a new activation. Immutable history retains its original binding.

## Catalog and operator boundary

No real authoritative current incident catalog was found or provisioned. The opt-in process environment variable `LANES_NEWS_OPERATIONAL_FOOTPRINT_DIR` points to an operator-owned directory containing:

- `manifest.json`: exactly `catalog_sha256` (SHA-256 of raw catalog bytes) and `approved_source_ids` (operator-approved source IDs).
- `footprints.json`: `format_version: 1` and `records`, at most 500 entries. Each entry supplies `record_id`, `source_id`, HTTPS `source_url`, `source_sha256`, `evidence_kind: authoritative_current_incident`, the complete article/input/claim/incident/time/locality identity, `srid: 4326`, polygon geometry and ordered canonical component hashes.

Compute component hashes from the validator's GeoJSON parts using the existing `canonical_sha256` helper. Serialization is canonical; geometry is not repaired. Manifest/catalog limits are 8,192 bytes/4 MB. Checksum drift, duplicate IDs, unapproved sources, missing files, invalid time/SRID/components, modeled classifications and malformed records fail closed. Catalog reads do not download remote URLs or write database state. The manifest is an operator trust boundary and integrity check, not a digital certificate or independent verification of a feed. Retain the reviewed source capture and immutable catalog revision for audit. Do not generate a production catalog from the synthetic test fixtures or accept user-provided manifests as approval.

Staff API approval remains authenticated; no public catalog upload or provenance override endpoint was added. Capability checks now share a service helper with the existing API dependency. No SQLAlchemy models, Alembic definitions or dependencies changed; private bindings use existing decision JSONB and legacy snapshots remain readable.

## Verification

| Scope | Distinct passing checks |
|---|---:|
| Nine targeted geometry/evidence/pipeline/publication/read/routing suites | 200 |
| Eight related auditor/evaluation/schema/presentation/road/locality suites | 194 |
| Existing flood-event suite | 4 |
| Total | **398** |

The targeted suite adds 60 checks over the prior 140-check checkpoint: 19 shape/provenance cases, 14 catalog integrity cases and 27 native approval/refresh/relink/preview cases. Related suites additionally test actual locality-provider resolution and missing named barangay behavior. Native tests use fresh guarded local PostGIS databases and synthetic operator-owned incident/boundary assets. They test approval failures without operational writes, staff capability, preview parity, immutable history, safe refresh fallback and existing public zone/routing reads. No real flood perimeter, live provider request, actual Valhalla detour or browser/PWA run is claimed.

Run from the repository root:

```powershell
& .\backend\venv\Scripts\python.exe .\docs\evaluations\phase-36-integration-audit-20261005\verify.py
& .\backend\venv\Scripts\python.exe .\docs\evaluations\phase-36-integration-audit-20261005\verify.py --additional-regressions --zone-metadata-regressions
```

Final commands pass and remove all four allocated disposable databases. Existing migrations reach `d7e4b9a21c60`. Diagnostic probes reject partial overlap, retain high/waist metadata and supported same-case coverage, reject stale/policy-changed observations and end unsupported coverage/event on clearance/expiry. Existing multipart/`datetime.utcnow` warnings remain. Normal/cloud data, frontend and deployment were untouched; no Git commit/push occurred.

## Next delivery slice

Provision an approved actual current extent source and connect saved extraction → independent evaluation → alert or eligible footprint activation in the real automatic worker, with current revision/retry/refresh/clearance/expiry handling and per-article failures. Then connect public/staff operational geometry, news attribution and observation/status controls on desktop/mobile, followed by full article → polygon → map → routing → expiry and staging/PWA acceptance. Source text alone, modeled risk and administrative boundaries cannot supply missing affected width or perimeter.

[Active delivery plan](../task_plan.md), [operator guide](../guides/news-publication-lifecycle.md), [previous metadata/support checkpoint](phase-36-zone-metadata-support-repair.md).
