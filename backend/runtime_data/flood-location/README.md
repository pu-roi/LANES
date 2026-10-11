# Complete Pasig prediction locality catalog

Purpose: automatic locality of saved zone geometry for staff prediction/simulation and model-input snapshots. This catalog does not establish current flood extent or replace the separate OSM/NOAH news activation catalog.

Source: OCHA Philippines/HDX Philippines COD-AB v03, attributed NAMRIA/PSA, [source dataset](https://data.humdata.org/dataset/cod-ab-phl). Licence: Creative Commons Attribution for Intergovernmental Organisations (CC BY-IGO). Current/legacy PSGC crosswalk uses the existing 30-name reference. Source valid_on 2025-02-13 is a data-version attribute; no new cadastral survey, legal delineation or field flood verification is claimed.

All 30 source polygons are valid and disjoint and partition the source-consistent Pasig city polygon. No clipping, simplification, repair, buffering or synthesized geometry. San Nicolas (Pob.) has an explicit code-bound canonical-name crosswalk. Outside/cross-boundary ambiguity remains explicit.

- boundaries.json: `65d88755d7e0f25d4f1648406cfa16ed76244bae6d4849098ed233b22a1b9724`
- source_subset.geojson: `a2c20c736a71590f00f2580504ec9518028eb2f9b64721f39ff966c7c1eeb767`
- city.geojson: `ec4134725657a52a26dbcc54b2b3b7bc502549b36840d172a9afe28966b7c594`

Manifest records licence, source input/builder hashes and prediction-only/no-routing meaning. Exact original selected SHP records, source DBF/SHX CRC verification, ZIP transfer receipts and approximately 206 MiB of compressed source prefixes remain under ignored data/pasig-local-model-20261008; full national-archive SHA or partial-stream full-member CRC is not claimed. Runtime subset/city/catalog is small and is bundled by the existing Docker COPY.

Environment override: LANES_FLOOD_LOCATION_DIR. Provider caches one checked version; restart after an intentional source update. Runtime verification checks all 30 identities and exact source parent topology. [Implementation and acceptance](../../../docs/evaluations/pasig-location-feature-models-20261008/README.md).
