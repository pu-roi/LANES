"""Read-only C. Raymundo / NOAH spatial audit for two Pasig intersections.

Run from backend/ with the three locally downloaded Metro Manila NOAH ZIPs::

    python scripts/audit_noah_road_intersections.py \
        ../data/metro_manila_road_audit.osm.pbf \
        ../data/noah_metro_5yr_inspect.zip \
        ../data/noah_metro_25yr_inspect.zip \
        ../data/noah_metro_100yr_inspect.zip

The 100 m windows are research probes, not reported flood spans or live zones.
This script does not access the application database or publish map geometry.
"""

from __future__ import annotations

import argparse
import csv
import math
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import osmium
import shapely
from shapely.geometry import LineString, LinearRing, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.noah_road_prediction_service import RoadSectionEvidence, rank_noah_road_sections


ROAD_NAME = "C. Raymundo Avenue"
CROSS_STREETS = ("Bernal Street", "Mercedes Avenue")
REPO_ROOT = Path(__file__).resolve().parents[2]
HISTORY_CSV = REPO_ROOT / "data/flooded_areas_pasig_clean.csv"
WINDOW_METERS = 100.0
X_METERS_PER_DEGREE = 111_320.0 * math.cos(math.radians(14.58))
Y_METERS_PER_DEGREE = 110_574.0


@dataclass(frozen=True)
class RoadWay:
    osm_id: int
    name: str
    nodes: tuple[tuple[int, float, float], ...]
    highway: str
    bridge: str
    tunnel: str
    layer: str


class NamedRoads(osmium.SimpleHandler):
    def __init__(self) -> None:
        super().__init__()
        self.ways: dict[str, list[RoadWay]] = {
            ROAD_NAME: [], **{name: [] for name in CROSS_STREETS}
        }

    def way(self, way: osmium.osm.Way) -> None:
        name = way.tags.get("name", "")
        if name not in self.ways or "highway" not in way.tags:
            return
        nodes = tuple(
            (node.ref, node.lon, node.lat)
            for node in way.nodes
            if node.location.valid()
        )
        if len(nodes) < 2 or not any(
            121.07 < lon < 121.11 and 14.55 < lat < 14.60
            for _, lon, lat in nodes
        ):
            return
        self.ways[name].append(RoadWay(
            osm_id=way.id,
            name=name,
            nodes=nodes,
            highway=way.tags.get("highway", ""),
            bridge=way.tags.get("bridge", ""),
            tunnel=way.tags.get("tunnel", ""),
            layer=way.tags.get("layer", ""),
        ))


def local_projector():
    """Return a local meter projection; its distances are approximate."""
    return lambda x, y, z=None: (x * X_METERS_PER_DEGREE, y * Y_METERS_PER_DEGREE)


def junction_windows(roads: NamedRoads) -> dict[str, BaseGeometry]:
    raymundo = roads.ways[ROAD_NAME]
    ray_nodes: dict[int, tuple[float, float]] = {
        node_id: (lon, lat)
        for way in raymundo for node_id, lon, lat in way.nodes
    }
    output = {}
    for cross_name in CROSS_STREETS:
        shared = {
            node_id: ray_nodes[node_id]
            for way in roads.ways[cross_name]
            for node_id, _, _ in way.nodes
            if node_id in ray_nodes
        }
        if not shared:
            raise ValueError(f"No mapped shared road node for {cross_name}")
        print(f"{cross_name}: {len(shared)} shared C. Raymundo nodes")
        windows = []
        for node_id, point in sorted(shared.items()):
            projection = local_projector()
            center = Point(*projection(*point))
            relevant = [
                way for way in raymundo
                if any(node[0] == node_id for node in way.nodes)
            ]
            for way in relevant:
                line = transform(
                    projection,
                    LineString([(lon, lat) for _, lon, lat in way.nodes]),
                )
                clipped = line.intersection(center.buffer(WINDOW_METERS))
                if not clipped.is_empty:
                    windows.append(clipped)
                print(
                    f"  node={node_id} lon={point[0]:.7f} lat={point[1]:.7f} "
                    f"road_way={way.osm_id} bridge={way.bridge or '-'} "
                    f"tunnel={way.tunnel or '-'} layer={way.layer or '-'}"
                )
        # Nearby duplicate carriageway windows are kept as separate linework.
        metric_lines = shapely.union_all(windows)
        output[cross_name] = metric_lines
        print(f"  road line within 100 m window(s): {metric_lines.length:.1f} m")
        if len(shared) > 1:
            print("  Note: multiple mapped junction nodes/carriageways; not one road point")
    return output


def hazard_overlap(zip_path: Path, road_metric: BaseGeometry) -> dict[int, float]:
    """Intersect original polygon rings with a bounded road line, preserving holes."""
    projection = local_projector()
    inverse_x = 1 / X_METERS_PER_DEGREE
    inverse_y = 1 / Y_METERS_PER_DEGREE
    min_x, min_y, max_x, max_y = road_metric.bounds
    longitude_bounds = (min_x * inverse_x, max_x * inverse_x)
    latitude_bounds = (min_y * inverse_y, max_y * inverse_y)
    overlaps: dict[int, float] = {}
    with ZipFile(zip_path) as archive:
        shp = archive.read(next(name for name in archive.namelist() if name.lower().endswith(".shp")))
        dbf = archive.read(next(name for name in archive.namelist() if name.lower().endswith(".dbf")))
        header_length, record_length = struct.unpack_from("<HH", dbf, 8)
        record_count = struct.unpack_from("<I", dbf, 4)[0]
        position = 100
        for record_index in range(record_count):
            content_bytes = struct.unpack_from(">I", shp, position + 4)[0] * 2
            start = position + 8
            if struct.unpack_from("<I", shp, start)[0] != 5:
                raise ValueError("Expected NOAH polygon shapefile")
            part_count, point_count = struct.unpack_from("<II", shp, start + 36)
            starts = np.frombuffer(shp, dtype="<i4", count=part_count, offset=start + 44)
            coords = np.frombuffer(
                shp, dtype="<f8", count=2 * point_count,
                offset=start + 44 + 4 * part_count,
            ).reshape((-1, 2))
            ends = np.append(starts[1:], point_count)
            lows = np.minimum.reduceat(coords, starts, axis=0)
            highs = np.maximum.reduceat(coords, starts, axis=0)
            candidate_indices = np.flatnonzero(
                (lows[:, 0] <= longitude_bounds[1]) &
                (highs[:, 0] >= longitude_bounds[0]) &
                (lows[:, 1] <= latitude_bounds[1]) &
                (highs[:, 1] >= latitude_bounds[0])
            )
            shells = []
            holes = []
            for index in candidate_indices:
                ring = coords[starts[index]:ends[index]]
                if len(ring) < 4:
                    continue
                polygon = Polygon(ring)
                if not polygon.is_valid:
                    polygon = shapely.make_valid(polygon)
                if LinearRing(ring).is_ccw:
                    holes.append(polygon)
                else:
                    shells.append(polygon)
            value = dbf[
                header_length + record_index * record_length + 1:
                header_length + (record_index + 1) * record_length
            ].decode("ascii").strip()
            hazard_class = int(float(value))
            area = shapely.union_all(shells) if shells else None
            if area is not None and not area.is_empty:
                if holes:
                    area = area.difference(shapely.union_all(holes))
                overlap = road_metric.intersection(transform(projection, area))
                overlaps[hazard_class] = overlap.length
            else:
                overlaps[hazard_class] = 0.0
            position = start + content_bytes
    return overlaps


def history_matches(cross_name: str) -> None:
    token = "bernal" if cross_name == "Bernal Street" else "mercede"
    with HISTORY_CSV.open(encoding="utf-8-sig", newline="") as handle:
        rows = [
            row for row in csv.DictReader(handle)
            if "raymundo" in (
                row["street_normalized"] + " " + row["landmark_normalized"]
            ).lower()
            and token in (
                row["street_normalized"] + " " + row["landmark_normalized"]
            ).lower()
        ]
    for row in rows:
        print(
            f"  DRRMO year={row['source_year']} barangay={row['barangay_canonical']} "
            f"road={row['street_normalized']!r} landmark={row['landmark_normalized']!r} "
            f"depth={row['water_level_raw']!r}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("osm_pbf", type=Path)
    parser.add_argument("noah_zips", type=Path, nargs=3)
    args = parser.parse_args()
    roads = NamedRoads()
    roads.apply_file(str(args.osm_pbf), locations=True)
    print(f"C. Raymundo named OSM ways: {len(roads.ways[ROAD_NAME])}")
    windows = junction_windows(roads)
    for cross_name, road_metric in windows.items():
        print(f"\n{cross_name} audit window:")
        history_matches(cross_name)
        for zip_path in args.noah_zips:
            lengths = hazard_overlap(zip_path, road_metric)
            print(
                f"  NOAH {zip_path.name}: " +
                ", ".join(f"Var {key}={value:.1f} m" for key, value in sorted(lengths.items()))
            )
    prediction = rank_noah_road_sections(
        [RoadSectionEvidence(
            section_id=name, metric_centerline=geometry,
            osm_source_id=f"local-osm-pbf:{args.osm_pbf.name}",
            bounded_road_section=False,
        ) for name, geometry in windows.items()],
        dict(zip((5, 25, 100), args.noah_zips)),
        hazard_overlap,
    )
    print("\nModeled-susceptibility ranking of research windows:")
    for section in prediction.ranked_sections:
        print(f"  {section.section_id}: " + ", ".join(
            f"{period}-year={section.modeled_overlap_fraction[period]:.2f} of window"
            for period in (5, 25, 100)
        ))
    print(f"Predicted bounded section: {prediction.predicted_section_id or 'unresolved'} ({prediction.reason})")


if __name__ == "__main__":
    main()
