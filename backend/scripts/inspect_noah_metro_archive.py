"""Inspect a local Metro Manila NOAH ZIP without importing hazard data.

Usage: python scripts/inspect_noah_metro_archive.py path/to/archive.zip
The grid check establishes whether sample points inside Pasig fall in each
hazard class. It is not a precise area-coverage or road-intersection measure.
"""

from __future__ import annotations

import json
import math
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
PASIG_BOUNDARY = REPO_ROOT / "frontend/public/pasig-boundary.geojson"


def inside_ring(point: tuple[float, float], ring: np.ndarray) -> bool:
    """Return even-odd point containment for one closed coordinate ring."""
    x, y = point
    a = ring[:-1]
    b = ring[1:]
    crosses = ((a[:, 1] > y) != (b[:, 1] > y)) & (
        x < (b[:, 0] - a[:, 0]) * (y - a[:, 1]) /
        np.where(b[:, 1] == a[:, 1], 1.0, b[:, 1] - a[:, 1]) + a[:, 0]
    )
    return bool(np.count_nonzero(crosses) % 2)


def pasig_rings() -> list[np.ndarray]:
    boundary = json.loads(PASIG_BOUNDARY.read_text(encoding="utf-8-sig"))
    return [np.asarray(ring, dtype=np.float64) for ring in boundary["coordinates"]]


def inside_pasig(point: tuple[float, float], rings: list[np.ndarray]) -> bool:
    return bool(sum(inside_ring(point, ring) for ring in rings) % 2)


def pasig_sample_points(steps: int = 35) -> list[tuple[float, float]]:
    rings = pasig_rings()
    outer = rings[0]
    min_x, min_y = outer.min(axis=0)
    max_x, max_y = outer.max(axis=0)
    points = []
    for x in np.linspace(min_x, max_x, steps + 2)[1:-1]:
        for y in np.linspace(min_y, max_y, steps + 2)[1:-1]:
            point = (float(x), float(y))
            if inside_pasig(point, rings):
                points.append(point)
    return points


def road_sample_points(path: Path) -> list[tuple[int, tuple[float, float]]]:
    """Sample named OSM ways about every 15 m for a feasibility check."""
    rings = pasig_rings()
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    samples = []
    for element in payload["elements"]:
        if element.get("tags", {}).get("name") != "C. Raymundo Avenue":
            continue
        geometry = element.get("geometry", [])
        for start, end in zip(geometry, geometry[1:]):
            mid_lat = math.radians((start["lat"] + end["lat"]) / 2)
            dx = (end["lon"] - start["lon"]) * 111_000 * math.cos(mid_lat)
            dy = (end["lat"] - start["lat"]) * 111_000
            count = max(1, math.ceil(math.hypot(dx, dy) / 15))
            for index in range(count):
                fraction = (index + 0.5) / count
                point = (
                    start["lon"] + fraction * (end["lon"] - start["lon"]),
                    start["lat"] + fraction * (end["lat"] - start["lat"]),
                )
                if inside_pasig(point, rings):
                    samples.append((element["id"], point))
    return samples


def inspect(zip_path: Path, road_path: Path | None = None) -> None:
    pasig_points = pasig_sample_points()
    road_samples = road_sample_points(road_path) if road_path else []
    points = pasig_points + [point for _, point in road_samples]
    print(
        f"archive={zip_path.name} Pasig grid points={len(pasig_points)} "
        f"C. Raymundo road samples={len(road_samples)}"
    )
    with ZipFile(zip_path) as archive:
        if archive.testzip() is not None:
            raise ValueError("Archive CRC check failed")
        names = archive.namelist()
        shp_name = next(name for name in names if name.lower().endswith(".shp"))
        dbf_name = next(name for name in names if name.lower().endswith(".dbf"))
        prj_name = next(name for name in names if name.lower().endswith(".prj"))
        shp = archive.read(shp_name)
        dbf = archive.read(dbf_name)
        print(f"files={names}")
        print(f"shape_type={struct.unpack_from('<I', shp, 32)[0]}")
        print(f"archive_bbox={struct.unpack_from('<4d', shp, 36)}")
        print(f"projection={archive.read(prj_name).decode('utf-8', errors='replace')}")
        record_count = struct.unpack_from("<I", dbf, 4)[0]
        header_length, record_length = struct.unpack_from("<HH", dbf, 8)
        print(f"DBF records={record_count} fields={dbf[32:43].split(bytes([0]))[0].decode()}")
        position = 100
        road_classes: dict[int, int] = {}
        for record_number in range(record_count):
            content_bytes = struct.unpack_from(">I", shp, position + 4)[0] * 2
            start = position + 8
            shape_type = struct.unpack_from("<I", shp, start)[0]
            if shape_type != 5:
                raise ValueError(f"Expected polygon shape type 5, got {shape_type}")
            part_count, point_count = struct.unpack_from("<II", shp, start + 36)
            starts = np.frombuffer(shp, dtype="<i4", count=part_count, offset=start + 44)
            coords = np.frombuffer(
                shp, dtype="<f8", count=2 * point_count,
                offset=start + 44 + 4 * part_count,
            ).reshape((-1, 2))
            ends = np.append(starts[1:], point_count)
            minimum = np.minimum.reduceat(coords, starts, axis=0)
            maximum = np.maximum.reduceat(coords, starts, axis=0)
            boxes = np.column_stack((minimum, maximum))
            matched = []
            for point_index, point in enumerate(points):
                x, y = point
                candidate_parts = np.flatnonzero(
                    (boxes[:, 0] <= x) & (x <= boxes[:, 2]) &
                    (boxes[:, 1] <= y) & (y <= boxes[:, 3])
                )
                if sum(inside_ring(point, coords[starts[i]:ends[i]]) for i in candidate_parts) % 2:
                    matched.append(point_index)
            value = dbf[
                header_length + record_number * record_length + 1:
                header_length + (record_number + 1) * record_length
            ].decode("ascii").strip()
            hazard_class = int(float(value))
            for point_index in matched:
                if point_index >= len(pasig_points):
                    road_classes[point_index] = max(road_classes.get(point_index, 0), hazard_class)
            grid_matches = [index for index in matched if index < len(pasig_points)]
            print(
                f"Var={value} parts={part_count} vertices={point_count} "
                f"Pasig grid matches={len(grid_matches)} "
                f"first_match={pasig_points[grid_matches[0]] if grid_matches else None}"
            )
            position = start + content_bytes
        if road_samples:
            by_way: dict[int, Counter[int]] = defaultdict(Counter)
            for index, (way_id, _) in enumerate(road_samples, start=len(pasig_points)):
                by_way[way_id][road_classes.get(index, 0)] += 1
            print("C. Raymundo way samples by highest modeled hazard class (0=none):")
            for way_id, counts in sorted(by_way.items()):
                print(f"  OSM way {way_id}: {dict(sorted(counts.items()))}")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit("Usage: inspect_noah_metro_archive.py archive.zip [road-overpass.json]")
    inspect(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) == 3 else None)
