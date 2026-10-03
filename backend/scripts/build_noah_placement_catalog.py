"""Build exact, indexed NOAH vector tiles from the three Metro Manila ZIPs.

No source ZIPs are packaged into the API image. Publish the generated catalog
as a versioned external asset/mount and set LANES_NEWS_NOAH_DIR at runtime.
Repaired rings and holes are retained; there is no geometry simplification.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from shapely import make_valid, union_all
from shapely.geometry import LinearRing, MultiPolygon, Polygon, box, mapping
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.noah_vector_catalog_service import NoahManifest, tile_keys


def polygon_parts(geometry: BaseGeometry) -> list[Polygon]:
    if geometry.geom_type == "Polygon":
        return [geometry] if not geometry.is_empty else []
    if hasattr(geometry, "geoms"):
        return [polygon for part in geometry.geoms for polygon in polygon_parts(part)]
    return []


def read_source_rings(path: Path) -> dict[int, tuple[STRtree, STRtree]]:
    """Read bounded WGS84 polygon shapefile and named Var field, not DBF guesses."""
    if path.stat().st_size > 64_000_000:
        raise ValueError("Only the Metro Manila source archives are supported")
    with ZipFile(path) as archive:
        members = {suffix: [item for item in archive.infolist()
                            if item.filename.lower().endswith(suffix)]
                   for suffix in (".shp", ".dbf", ".prj")}
        if any(len(items) != 1 for items in members.values()):
            raise ValueError("Expected one source shapefile with DBF and CRS")
        if sum(item.file_size for items in members.values() for item in items) > 512_000_000:
            raise ValueError("Expanded source archive limit exceeded")
        prj = archive.read(members[".prj"][0]).decode("ascii").upper()
        if not ("GEOGCS" in prj and "WGS" in prj and "1984" in prj and "PROJCS" not in prj):
            raise ValueError("Expected WGS84 geographic source vectors")
        shp, dbf = (archive.read(members[suffix][0]) for suffix in (".shp", ".dbf"))
    if len(shp) < 100 or struct.unpack_from("<I", shp, 32)[0] != 5:
        raise ValueError("Expected polygon shapefile")
    count = struct.unpack_from("<I", dbf, 4)[0]
    header, width = struct.unpack_from("<HH", dbf, 8)
    offset, var_field = 1, None
    for pos in range(32, header - 1, 32):
        name = dbf[pos:pos + 11].split(b"\0")[0].decode("ascii").lower()
        length = dbf[pos + 16]
        if name == "var":
            var_field = (offset, length)
        offset += length
    if var_field is None or count != 3:
        raise ValueError("Expected three Var source classes")
    result, position = {}, 100
    for record in range(count):
        start = position + 8
        length = struct.unpack_from(">I", shp, position + 4)[0] * 2
        if start + length > len(shp) or struct.unpack_from("<I", shp, start)[0] != 5:
            raise ValueError("Invalid polygon record")
        parts, points = struct.unpack_from("<II", shp, start + 36)
        starts = np.frombuffer(shp, dtype="<i4", count=parts, offset=start + 44)
        coords = np.frombuffer(shp, dtype="<f8", count=points * 2,
                               offset=start + 44 + parts * 4).reshape((-1, 2))
        if (not len(starts) or starts[0] != 0 or np.any(np.diff(starts) <= 0)
                or starts[-1] >= points or not np.all(np.isfinite(coords))
                or np.any(coords[:, 0] < 120) or np.any(coords[:, 0] > 123)
                or np.any(coords[:, 1] < 13) or np.any(coords[:, 1] > 16)):
            raise ValueError("Invalid NCR ring coordinates")
        endings = np.append(starts[1:], points)
        shells, holes = [], []
        for first, last in zip(starts, endings):
            ring = coords[first:last]
            if len(ring) < 4 or not np.array_equal(ring[0], ring[-1]):
                raise ValueError("Unclosed source ring")
            polygon = Polygon(ring)
            target = holes if LinearRing(ring).is_ccw else shells
            target.extend(polygon_parts(polygon if polygon.is_valid else make_valid(polygon)))
        row = dbf[header + record * width:header + (record + 1) * width]
        if not row or row[0:1] != b" ":
            raise ValueError("Invalid/deleted source class")
        at, size = var_field
        numeric_class = float(row[at:at + size].decode("ascii").strip())
        if not numeric_class.is_integer():
            raise ValueError("Non-integer Var identity")
        hazard = int(numeric_class)
        if hazard not in {1, 2, 3} or hazard in result:
            raise ValueError("Unexpected Var identity")
        result[hazard] = (STRtree(shells), STRtree(holes))
        position = start + length
    return result


def build_catalog(archives: dict[int, Path], output: Path,
                  bounds: tuple[float, float, float, float], tile_size: float = 0.02) -> str:
    # Refuse overwriting a published immutable catalog.
    if (output / "manifest.json").exists():
        raise ValueError("Choose a new output directory for a new catalog version")
    west, south, east, north = bounds
    if not (120 <= west < east <= 123 and 13 <= south < north <= 16
            and east - west <= 1 and north - south <= 1 and 0.005 <= tile_size <= 0.05
            and set(archives) == {5, 25, 100}):
        raise ValueError("Invalid catalog build extent/scenarios")
    keys = tile_keys(bounds, tile_size)
    scenarios = {}
    for period, archive in sorted(archives.items()):
        source_digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        trees = read_source_rings(archive)
        destination = output / str(period)
        destination.mkdir(parents=True, exist_ok=True)
        hashes = {}
        for key in keys:
            x, y = (int(value) for value in key.split(":"))
            cell = box(x * tile_size, y * tile_size, (x + 1) * tile_size, (y + 1) * tile_size)
            payload = {}
            for hazard, (shells, holes) in trees.items():
                area = union_all([shells.geometries[i].intersection(cell)
                                  for i in shells.query(cell, predicate="intersects")])
                if not area.is_empty:
                    hole_area = union_all([holes.geometries[i].intersection(cell)
                                           for i in holes.query(cell, predicate="intersects")])
                    area = area.difference(hole_area)
                payload[str(hazard)] = mapping(MultiPolygon(polygon_parts(area)))
            raw = gzip.compress(json.dumps(payload, separators=(",", ":"), allow_nan=False).encode(), mtime=0)
            (destination / f"{key.replace(':', '_')}.json.gz").write_bytes(raw)
            hashes[key] = hashlib.sha256(raw).hexdigest()
        scenarios[period] = dict(source_id=f"noah-metro:{period}yr:{source_digest}",
                                 archive_sha256=source_digest, tiles=hashes)
        print(f"Built {period}-year scenario: {len(keys)} exact vector tiles", flush=True)
    manifest = NoahManifest(tile_size=tile_size, bounds=bounds,
        attribution="Project NOAH and its contributors; derived from Metro Manila source vectors",
        license="ODbL-1.0", scenarios=scenarios)
    raw = manifest.model_dump_json().encode()
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--noah-5yr", required=True, type=Path)
    parser.add_argument("--noah-25yr", required=True, type=Path)
    parser.add_argument("--noah-100yr", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--bounds", nargs=4, type=float, default=(120.90, 14.35, 121.14, 14.79))
    args = parser.parse_args()
    digest = build_catalog({5: args.noah_5yr, 25: args.noah_25yr, 100: args.noah_100yr},
                           args.output, tuple(args.bounds))
    print(f"Catalog SHA-256: {digest}")


if __name__ == "__main__":
    main()
