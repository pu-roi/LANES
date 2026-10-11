"""Audit Metro Manila OSM boundary/road coverage and NOAH sample coverage.

The OSM extract is a community-maintained snapshot, not an authoritative road
inventory. NOAH flood polygons show modeled hazard, not current flood reports.
The script reports sample intersections; it does not claim that every parcel
in a city is covered or that an unhit point is safe.

Run from backend/ with the ignored local Metro Manila OSM PBF and NOAH ZIPs::

    python scripts/audit_phase36_metro_spatial_coverage.py \
      ../data/metro_manila_road_audit.osm.pbf \
      ../data/noah_metro_5yr_inspect.zip \
      ../data/noah_metro_25yr_inspect.zip \
      ../data/noah_metro_100yr_inspect.zip
"""

from __future__ import annotations

import argparse
import struct
import sys
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import osmium
import shapely
from shapely.geometry import LineString, Point
from shapely.ops import polygonize, unary_union


EXPECTED_NCR_CITIES = (
    "Manila", "Quezon City", "Pasig", "Mandaluyong", "Makati", "Pasay",
    "Marikina", "Taguig", "Caloocan", "Valenzuela", "Navotas", "Malabon",
    "Muntinlupa", "Las Piñas", "Parañaque", "San Juan", "Pateros",
)
MAJOR_ROAD_CLASSES = frozenset({
    "motorway", "trunk", "primary", "secondary", "tertiary", "unclassified",
})


def folded(value: str) -> str:
    import unicodedata
    return "".join(char for char in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(char))


def city_key(value: str) -> str:
    result = folded(value).strip()
    if result.startswith("city of "):
        result = result[8:]
    if result.endswith(" city") and result != "quezon city":
        result = result[:-5]
    return result


def assemble_boundary(
    relation_id: int,
    city_name: str,
    members: list[tuple[int, str]],
    way_coordinates: dict[int, list[tuple[float, float]]],
) -> shapely.Geometry:
    """Build a city multipolygon from relation ways; reject incomplete rings."""
    outer: list[LineString] = []
    inner: list[LineString] = []
    for way_id, role in members:
        coordinates = way_coordinates.get(way_id)
        if not coordinates or len(coordinates) < 2:
            raise ValueError(f"OSM relation {relation_id} ({city_name}) is missing way {way_id}")
        line = LineString(coordinates)
        (outer if role == "outer" else inner).append(line)
    if not outer:
        raise ValueError(f"OSM relation {relation_id} ({city_name}) has no outer ways")
    polygons = list(polygonize(unary_union(outer)))
    if not polygons:
        raise ValueError(f"OSM relation {relation_id} ({city_name}) does not form a polygon")
    boundary = shapely.union_all(polygons)
    if inner:
        holes = list(polygonize(unary_union(inner)))
        if not holes:
            raise ValueError(f"OSM relation {relation_id} ({city_name}) has invalid inner ways")
        boundary = boundary.difference(shapely.union_all(holes))
    if not boundary.is_valid:
        boundary = shapely.make_valid(boundary)
    if boundary.is_empty or not boundary.is_valid:
        raise ValueError(f"OSM relation {relation_id} ({city_name}) is not a valid polygon")
    return boundary


class AdminRelations(osmium.SimpleHandler):
    def __init__(self) -> None:
        super().__init__()
        expected = {city_key(name): name for name in EXPECTED_NCR_CITIES}
        self.relations: dict[str, tuple[int, str, list[tuple[int, str]]]] = {}
        self.all_highway_ways = 0
        self.named_highway_ways = 0
        self.highway_counts: Counter[str] = Counter()
        self.named_highway_counts: Counter[str] = Counter()
        self.expected = expected

    def way(self, way: osmium.osm.Way) -> None:
        highway = way.tags.get("highway")
        if not highway:
            return
        self.all_highway_ways += 1
        self.highway_counts[highway] += 1
        if way.tags.get("name") or way.tags.get("name:en") or way.tags.get("alt_name"):
            self.named_highway_ways += 1
            self.named_highway_counts[highway] += 1

    def relation(self, relation: osmium.osm.Relation) -> None:
        if relation.tags.get("boundary") != "administrative" or relation.tags.get("admin_level") != "6":
            return
        names = (relation.tags.get("name") or "", relation.tags.get("name:en") or "")
        canonical = next((self.expected[city_key(name)] for name in names
                          if city_key(name) in self.expected), None)
        if not canonical:
            return
        members = [(member.ref, member.role) for member in relation.members
                   if member.type == "w" and member.role in {"outer", "inner"}]
        self.relations[canonical] = (relation.id, canonical, members)


class BoundaryWays(osmium.SimpleHandler):
    def __init__(self, required_ids: set[int]) -> None:
        super().__init__()
        self.required_ids = required_ids
        self.coordinates: dict[int, list[tuple[float, float]]] = {}

    def way(self, way: osmium.osm.Way) -> None:
        if way.id in self.required_ids:
            if way.is_closed() and len(way.nodes) >= 4:
                try:
                    self.coordinates[way.id] = [(float(node.lon), float(node.lat)) for node in way.nodes]
                except Exception:
                    return
            else:
                try:
                    self.coordinates[way.id] = [(float(node.lon), float(node.lat)) for node in way.nodes]
                except Exception:
                    return


def load_city_boundaries(pbf_path: Path) -> tuple[dict[str, shapely.Geometry], dict[str, int], str | None, str | None]:
    reader = osmium.io.Reader(str(pbf_path))
    header = reader.header()
    timestamp = header.get("osmosis_replication_timestamp")
    replication_url = header.get("osmosis_replication_base_url")
    reader.close()

    relations = AdminRelations()
    relations.apply_file(str(pbf_path), locations=False)
    missing = sorted(set(EXPECTED_NCR_CITIES) - set(relations.relations))
    if missing:
        raise ValueError("Metro Manila city relations missing from OSM extract: " + ", ".join(missing))
    required_ids = {way_id for _, _, members in relations.relations.values() for way_id, _ in members}
    ways = BoundaryWays(required_ids)
    ways.apply_file(str(pbf_path), locations=True)
    boundaries = {
        name: assemble_boundary(relation_id, name, members, ways.coordinates)
        for name, (relation_id, _, members) in relations.relations.items()
    }
    relation_ids = {name: item[0] for name, item in relations.relations.items()}
    return boundaries, relation_ids, timestamp, replication_url


def sample_city_points(boundary: shapely.Geometry, divisions: int = 5) -> list[Point]:
    """Create a small deterministic interior grid for hazard-layer spot checks."""
    min_x, min_y, max_x, max_y = boundary.bounds
    points = [Point(float(x), float(y))
              for x in np.linspace(min_x, max_x, divisions + 2)[1:-1]
              for y in np.linspace(min_y, max_y, divisions + 2)[1:-1]
              if boundary.covers(Point(float(x), float(y)))]
    if not points:
        points = [boundary.representative_point()]
    return points


def point_in_ring(points: list[Point], ring: np.ndarray) -> np.ndarray:
    x = np.asarray([point.x for point in points], dtype=np.float64)
    y = np.asarray([point.y for point in points], dtype=np.float64)
    start, end = ring[:-1], ring[1:]
    crosses = ((start[:, 1, None] > y) != (end[:, 1, None] > y)) & (
        x < (end[:, 0, None] - start[:, 0, None]) *
        (y - start[:, 1, None]) /
        np.where(end[:, 1, None] == start[:, 1, None], 1.0,
                 end[:, 1, None] - start[:, 1, None]) + start[:, 0, None]
    )
    return np.count_nonzero(crosses, axis=0) % 2 == 1


def sample_hazard_classes(zip_path: Path, points: list[Point]) -> dict[int, set[int]]:
    """Return sample-point indexes hit by each Var class in a NOAH archive."""
    matches: dict[int, set[int]] = {}
    with ZipFile(zip_path) as archive:
        shp = archive.read(next(name for name in archive.namelist() if name.lower().endswith(".shp")))
        dbf = archive.read(next(name for name in archive.namelist() if name.lower().endswith(".dbf")))
    if struct.unpack_from("<I", shp, 32)[0] != 5:
        raise ValueError(f"{zip_path.name} is not a polygon shapefile")
    record_count = struct.unpack_from("<I", dbf, 4)[0]
    header_length, record_length = struct.unpack_from("<HH", dbf, 8)
    field_count = (header_length - 33) // 32
    fields = [dbf[32 + index * 32:43 + index * 32].split(b"\0", 1)[0].decode("ascii")
              for index in range(field_count)]
    if "Var" not in fields:
        raise ValueError(f"{zip_path.name} has no NOAH Var field")
    var_index = fields.index("Var")
    var_offset = 1 + sum(dbf[32 + index * 32 + 16] for index in range(var_index))
    point_x = np.asarray([point.x for point in points])
    point_y = np.asarray([point.y for point in points])
    matched_by_var: dict[int, np.ndarray] = {}
    position = 100
    for record_index in range(record_count):
        content_bytes = struct.unpack_from(">I", shp, position + 4)[0] * 2
        start = position + 8
        if struct.unpack_from("<I", shp, start)[0] != 5:
            raise ValueError(f"{zip_path.name} contains a non-polygon record")
        part_count, point_count = struct.unpack_from("<II", shp, start + 36)
        starts = np.frombuffer(shp, dtype="<i4", count=part_count, offset=start + 44)
        coords = np.frombuffer(
            shp, dtype="<f8", count=2 * point_count,
            offset=start + 44 + 4 * part_count,
        ).reshape((-1, 2))
        ends = np.append(starts[1:], point_count)
        lows = np.minimum.reduceat(coords, starts, axis=0)
        highs = np.maximum.reduceat(coords, starts, axis=0)
        record_matches = np.zeros(len(points), dtype=bool)
        for ring_index in range(part_count):
            bbox_points = np.flatnonzero(
                (point_x >= lows[ring_index, 0]) & (point_x <= highs[ring_index, 0]) &
                (point_y >= lows[ring_index, 1]) & (point_y <= highs[ring_index, 1])
            )
            if not len(bbox_points):
                continue
            ring = coords[starts[ring_index]:ends[ring_index]]
            ring_hits = point_in_ring([points[index] for index in bbox_points], ring)
            record_matches[bbox_points] ^= ring_hits
        raw_value = dbf[
            header_length + record_index * record_length + var_offset:
            header_length + (record_index + 1) * record_length
        ].decode("ascii").strip()
        var = int(float(raw_value))
        matched_by_var[var] = record_matches
        position = start + content_bytes
    for var in (1, 2, 3):
        if var not in matched_by_var:
            raise ValueError(f"{zip_path.name} does not include Var={var}")
    return {var: set(np.flatnonzero(mask).tolist()) for var, mask in matched_by_var.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("osm_pbf", type=Path)
    parser.add_argument("noah_5yr", type=Path)
    parser.add_argument("noah_25yr", type=Path)
    parser.add_argument("noah_100yr", type=Path)
    args = parser.parse_args()
    inputs = (args.osm_pbf, args.noah_5yr, args.noah_25yr, args.noah_100yr)
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        raise FileNotFoundError("Required local audit input is missing: " + ", ".join(missing))

    boundaries, relation_ids, timestamp, replication_url = load_city_boundaries(args.osm_pbf)
    way_counts = AdminRelations()
    way_counts.apply_file(str(args.osm_pbf), locations=False)
    print(f"OSM source snapshot: {timestamp or 'not supplied'}")
    print(f"OSM replication source: {replication_url or 'not supplied'}")
    print(f"OSM administrative boundaries: {len(boundaries)}/17 expected NCR LGUs; "
          f"all relation member ways assembled")
    print(f"OSM highway ways: {way_counts.all_highway_ways}; named by name/name:en/alt_name: "
          f"{way_counts.named_highway_ways} ({way_counts.named_highway_ways / max(1, way_counts.all_highway_ways):.1%})")
    for highway in sorted(MAJOR_ROAD_CLASSES):
        total = way_counts.highway_counts[highway]
        named = way_counts.named_highway_counts[highway]
        print(f"  {highway}: {named}/{total} named ways" if total else f"  {highway}: none")
    print("OSM road names are incomplete coverage; this local snapshot has no automatic refresh in LANES.")

    points_by_city = {city: sample_city_points(boundaries[city]) for city in EXPECTED_NCR_CITIES}
    offsets: dict[str, tuple[int, int]] = {}
    all_points: list[Point] = []
    for city, points in points_by_city.items():
        offsets[city] = (len(all_points), len(all_points) + len(points))
        all_points.extend(points)
    scenarios = ((5, args.noah_5yr), (25, args.noah_25yr), (100, args.noah_100yr))
    print(f"NOAH sample grid: {len(all_points)} interior points across 17 OSM city boundaries")
    for period, archive in scenarios:
        hits = sample_hazard_classes(archive, all_points)
        city_hits = []
        for city in EXPECTED_NCR_CITIES:
            start, end = offsets[city]
            local_hits = {var: len(indexes.intersection(range(start, end))) for var, indexes in hits.items()}
            total_points = end - start
            any_hits = len(set().union(*(indexes.intersection(range(start, end)) for indexes in hits.values())))
            city_hits.append((city, any_hits, total_points, local_hits))
        covered = sum(1 for _, count, _, _ in city_hits if count)
        print(f"{period}-year archive: sample points intersecting any hazard class in {covered}/17 cities")
        for city, count, total_points, local_hits in city_hits:
            print(f"  {city}: {count}/{total_points} points; "
                  f"Var1/2/3={local_hits[1]}/{local_hits[2]}/{local_hits[3]}")
    print("NOAH source-map modeling date is not published in the checked archive metadata; "
          "ZIP member timestamps do not establish it.")


if __name__ == "__main__":
    main()
