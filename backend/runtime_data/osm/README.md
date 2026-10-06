# NCR road placement snapshot

Source: OpenStreetMap contributors, under the Open Database License (ODbL).
Attribution and license: https://www.openstreetmap.org/copyright

`roads.json.gz` is derived from the existing local Metro Manila OSM extract,
replication timestamp `2026-09-27T00:56:56Z`. `manifest.json` records the original
PBF SHA-256, compressed catalog SHA-256, byte counts, and coverage counts.
This is an identified community map snapshot, not an authoritative inventory,
a live observation, a predicted flood extent, or a closure polygon.

The catalog retains 66,129 complete named highway ways and 17 checked city
relations. Three incomplete named ways remain explicit coverage gaps; a claim
using one of those road/cross-street names cannot receive a bounded match.
100,264 unnamed highways cannot be resolved by the named-road matcher.
The separate reviewed community-boundary catalog supplies 20 Pasig barangays,
including Ugong, from this same OSM snapshot. Claims requiring missing barangay
coverage stay unresolved. There is no automatic source refresh.

The October 5 source-preserving rebuild additionally retains explicit road-route
references for 5,257 named ways. Each reference records its OSM relation ID;
bus-route names and inferred street-name equivalences are excluded. In particular,
road relations `417210` and `14448353` identify the C-5 northbound/southbound
members, including Pasig ways named E. Rodriguez Jr. Avenue. The provider indexes
these source references without renaming the original roads. A local C5/Pasig
coverage audit now finds 45 matching ways with positive road length inside the
checked city boundary and 14 ambiguous road sections. No reported affected span,
flooded width, operational footprint or routing permission follows from this.
Catalog SHA-256: `5edd1284a00003ed2d97ff7d500f02b58d7f53521864e149311628df3d338386`.

Inspect current assets without database or network access:

```powershell
.\venv\Scripts\python.exe -m scripts.audit_news_spatial_assets --city Pasig --road C5
```

To replace the snapshot, from `backend/` run:

```powershell
.\venv\Scripts\python.exe -m scripts.build_news_osm_catalog ../data/metro_manila_road_audit.osm.pbf
```

Review the new source, manifest, and coverage; run placement/extraction tests;
then rebuild and restart the runtime. The provider caches one immutable catalog
per process. A changed catalog checksum creates new pipeline runs while retaining
old artifacts. A source failure is visible and uses a distinct pipeline identity;
repairing the source and restarting permits reprocessing. Never edit a loaded
catalog in place or silently replace a source without reviewing its metadata.
