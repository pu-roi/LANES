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
The October 11 source-preserving rebuild adds 1,374 named locality points and
their explicit source aliases. Every point has one checked containing city;
conflicting city tags are excluded. Road ways, city boundaries and original
PBF identity remain identical to the preceding catalog. For example, OSM node
`11155381066` retains `Sitio Sais`, its `Sitio 6` alias and Catmon quarter tag.
No manually supplied coordinate or inferred alias is inserted.

A complete, unique locality-name match can associate the report with the
nearest junction-bounded section of its named road within 500 metres. That
distance is a locality-centre association limit, not a neighbourhood boundary,
flood radius or measured affected extent. Equal-distance sections remain
candidates for existing ambiguity checks. Additional unresolved crossings,
missing required barangay boundaries, duplicate names and distant points fail.
The existing NOAH fragment selection, grade checks, 25-metre corridor margin
and independent live-report publication checks still apply. These are estimated
road corridors; the locality point and susceptibility data do not confirm a flood.
Catalog SHA-256: `b43240e75fb0eeeeb3e9a9d15724c162f24197c4bc0a05e834ae11776062b801`.

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
