# Reviewed OSM community boundaries for Pasig previews

These **community administrative polygons** support locality narrowing. They are
not official legal delineations, field verification, observed inundation or
routing closure geometry.

Source: the archived Metro Manila OpenStreetMap extract, snapshot
`2026-09-27T00:56:56Z`, SHA-256
`0fa54508ad7fe5e9debd6f46b6cd5ca01eeb57b26e2ba5d5b751a5539b6b2b1d`.
Original extract listing: https://download.openstreetmap.fr/extracts/asia/philippines/
The original PBF remains archived separately under ignored `data/`; it is not
duplicated into these small runtime assets. Each record retains its original
OpenStreetMap relation ID and source URL. Ugong is relation `108731`.

Attribution and license: **© OpenStreetMap contributors**, Open Database License
(ODbL 1.0), https://www.openstreetmap.org/copyright . This derived polygon catalog
is distributed under the same ODbL attribution/share-alike terms. Identity
crosswalk: Philippine Statistics Authority PSGC, including exact current and
correspondence codes from the bundled reference CSV. The official Pasig identity
listing is https://psa.gov.ph/classification/psgc/barangays/1381200000 .

Actual reviewer: **Codex geometry agent (automated asset validation)**. Review
checks exact PSGC code/name/parent relationships, complete original OSM ring
members, absence of unclosed/invalid linework, valid unsimplified WGS84 polygons
and strict containment in the checked same-snapshot OSM Pasig relation. No source
ring was repaired, simplified or snapped. This records automated asset checks;
it does not claim human, cadastral, field or legal-boundary review.

Twenty of Pasig's thirty barangays pass these checks. The omitted coverage is
**Bambang, Kalawaan, Malinao, Palatiw, Pinagbuhatan, San Joaquin, San Miguel,
San Nicolas, Santa Cruz and Santo Tomas**. Kalawaan, Pinagbuhatan and San Joaquin
have unclosed source linework; San Miguel lacks an explicit PSGC reference. Other
missing names have no accepted matching relation. `review_receipt.json` retains
every excluded candidate/reason and the PSGC/road-catalog checksums; missing areas
remain unresolved without broader city or synthetic polygon fallback.

The receipt's `psgc_reference_sha256` records the original reference input bytes
used for this build, including Windows line endings. Git may normalize that CSV
on another platform; this historical input hash is not a runtime checkout gate.
Runtime validation checks PSGC identities and the exact boundary catalog bytes.
The original CSV input is preserved alongside the ignored local source review.

`boundaries.json` SHA-256:
`4b596be585945502fffd1ca9e14f282fb5a10e3b844c3ca2b21eda1a157894c2`.
`manifest.json` identifies the exact bytes. `provisioning_receipt.json` records
the checked separately archived source and ODbL attribution. Processes cache one
immutable version; restart and verify asset revision when replacing a catalog.

From `backend/`, build a new review directory and inspect its exclusion receipt:

```powershell
.\venv\Scripts\python.exe -m scripts.build_news_barangay_catalog ../data/metro_manila_road_audit.osm.pbf ../data/new_barangay_review
.\venv\Scripts\python.exe -m scripts.audit_news_spatial_assets --city Pasig --road C5 --barangay Ugong
```

Use `scripts.provision_news_barangay_catalog` for new immutable installation
directories, with an actual licensing reviewer and original source checksum.
The builder deliberately rejects replacements of an existing directory.
