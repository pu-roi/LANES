"""Build an immutable server-owned NCR named-road snapshot from a local OSM PBF.

No provider requests, database writes, or public flood operations occur here.
Run from backend: python -m scripts.build_news_osm_catalog ../data/metro_manila_road_audit.osm.pbf
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import osmium
from shapely.geometry import mapping
from shapely.ops import polygonize_full, unary_union
from shapely.geometry import LineString

from app.services.news_road_placement_service import DEFAULT_CATALOG_DIR, MAX_CATALOG_BYTES, MAX_COMPRESSED_BYTES
from scripts.audit_phase36_metro_spatial_coverage import AdminRelations, BoundaryWays, load_city_boundaries


class NamedRoads(osmium.SimpleHandler):
    def __init__(self) -> None:
        super().__init__()
        self.ways: list[dict] = []
        self.unnamed_highways = 0
        self.incomplete_ways: list[dict] = []

    def way(self, way: osmium.osm.Way) -> None:
        if "highway" not in way.tags:
            return
        name = way.tags.get("name") or way.tags.get("name:en")
        if not name:
            self.unnamed_highways += 1
            return
        aliases = [n.strip() for n in way.tags.get("alt_name", "").split(";") if n.strip()]
        if way.tags.get("name:en") and way.tags["name:en"] != name:
            aliases.append(way.tags["name:en"])
        if len(way.nodes)<2 or any(not node.location.valid() for node in way.nodes):
            self.incomplete_ways.append(dict(osm_id=way.id,name=name,aliases=aliases))
            return
        nodes = [(node.ref, node.lon, node.lat) for node in way.nodes]
        self.ways.append(dict(osm_id=way.id, name=name, nodes=nodes, aliases=aliases,
            bridge=way.tags.get("bridge", ""), tunnel=way.tags.get("tunnel", ""), layer=way.tags.get("layer", "")))


def validate_boundary_rings(pbf: Path) -> None:
    """Reject dangling or unclosed relation members before using audit polygons."""
    relations = AdminRelations()
    relations.apply_file(str(pbf), locations=False)
    required = {ref for _, _, members in relations.relations.values() for ref, _ in members}
    ways = BoundaryWays(required)
    ways.apply_file(str(pbf), locations=True)
    for _, name, members in relations.relations.values():
        for role in ("outer", "inner"):
            refs = [ref for ref, r in members if r == role]
            if not refs:
                continue
            lines = [LineString(ways.coordinates[ref]) for ref in refs]
            polygons, cuts, dangles, invalid = polygonize_full(unary_union(lines))
            if polygons.is_empty or not all(g.is_empty for g in (cuts, dangles, invalid)):
                raise ValueError(f"Incomplete administrative rings for {name}")


def build_catalog(pbf: Path, output: Path) -> dict:
    boundaries, relations, snapshot_at, _ = load_city_boundaries(pbf)
    if not snapshot_at:
        raise ValueError("OSM extract must identify its replication snapshot time")
    validate_boundary_rings(pbf)
    roads = NamedRoads()
    roads.apply_file(str(pbf), locations=True)
    osm_digest = hashlib.sha256(pbf.read_bytes()).hexdigest()
    source_id = f"osm-ncr:{snapshot_at}:{osm_digest[:16]}"
    payload = dict(format_version=1, source_id=source_id, snapshot_at=snapshot_at, osm_sha256=osm_digest,
        attribution="OpenStreetMap contributors (ODbL); https://www.openstreetmap.org/copyright",
        cities=[dict(name=name, relation_id=relations[name], boundary=mapping(boundaries[name])) for name in sorted(boundaries)],
        ways=roads.ways, incomplete_ways=roads.incomplete_ways)
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    if len(raw)>MAX_CATALOG_BYTES:
        raise ValueError("Expanded road catalog exceeds runtime limit")
    compressed = gzip.compress(raw, mtime=0)
    if len(compressed)>MAX_COMPRESSED_BYTES:
        raise ValueError("Compressed road catalog exceeds runtime limit")
    output.mkdir(parents=True, exist_ok=True)
    (output / "roads.json.gz").write_bytes(compressed)
    summary = dict(catalog_sha256=hashlib.sha256(compressed).hexdigest(), source_id=source_id,
                   snapshot_at=snapshot_at, osm_sha256=osm_digest, named_ways=len(roads.ways),
                   unnamed_highways=roads.unnamed_highways, cities=len(boundaries),
                   incomplete_named_ways=len(roads.incomplete_ways),
                   compressed_bytes=len(compressed), expanded_bytes=len(raw))
    (output / "manifest.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("osm_pbf", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_CATALOG_DIR)
    args = parser.parse_args()
    print(json.dumps(build_catalog(args.osm_pbf, args.output), indent=2))


if __name__ == "__main__":
    main()
