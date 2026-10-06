"""Source DBF decimals, ring orientation, CRS and exact derived tile geometry."""
import struct
from zipfile import ZipFile

import pytest
from shapely.geometry import LineString, box
from shapely.geometry.polygon import orient

from scripts.build_noah_placement_catalog import build_catalog, read_source_rings
from app.services.noah_vector_catalog_service import NoahVectorCatalog, metric_geometry


def archive(path, *, bad_crs=False):
    polygons = [box(121, 14.6, 121.02, 14.62).difference(box(121.005, 14.605, 121.015, 14.615)),
                box(121.03, 14.6, 121.04, 14.61), box(121.03, 14.615, 121.04, 14.62)]
    shp = bytearray(100)
    struct.pack_into("<I", shp, 32, 5)
    for record, polygon in enumerate(polygons, 1):
        polygon = orient(polygon, sign=-1)
        rings = [list(polygon.exterior.coords), *[list(ring.coords) for ring in polygon.interiors]]
        starts, points = [], []
        for ring in rings:
            starts.append(len(points))
            points.extend(ring)
        content = struct.pack("<I4dII", 5, *polygon.bounds, len(rings), len(points))
        content += struct.pack(f"<{len(starts)}i", *starts)
        content += struct.pack(f"<{len(points) * 2}d", *[v for point in points for v in point])
        shp.extend(struct.pack(">II", record, len(content) // 2) + content)
    dbf = bytearray(65)
    struct.pack_into("<IHH", dbf, 4, 3, 65, 21)
    dbf[32:35] = b"Var"
    dbf[43], dbf[48], dbf[64] = ord("N"), 20, 13
    for hazard in (1, 2, 3):
        dbf.extend(b" " + f"{hazard:.11e}".rjust(20).encode())
    with ZipFile(path, "w") as target:
        target.writestr("fixture.shp", shp)
        target.writestr("fixture.dbf", dbf)
        target.writestr("fixture.prj", 'PROJCS["wrong"]' if bad_crs else 'GEOGCS["GCS_WGS_1984"]')


def test_source_builder_retains_holes_and_decimal_var_fields(tmp_path):
    source = tmp_path / "source.zip"
    archive(source)
    output = tmp_path / "catalog"
    build_catalog({p: source for p in (5, 25, 100)}, output, (121, 14.6, 121.04, 14.62))
    provider = NoahVectorCatalog(output)
    assert provider.error is None and not provider.revision.startswith("bad-")
    line = LineString([(121.01, 14.6), (121.01, 14.62)])
    for values in provider.overlaps(line).values():
        assert values[1] == pytest.approx(metric_geometry(line).length / 2)
        assert values[2] == values[3] == 0
    with pytest.raises(ValueError, match="new output directory"):
        build_catalog({p: source for p in (5, 25, 100)}, output, (121, 14.6, 121.04, 14.62))


def test_unknown_projection_cannot_build_a_catalog(tmp_path):
    source = tmp_path / "source.zip"
    archive(source, bad_crs=True)
    with pytest.raises(ValueError, match="WGS84"):
        read_source_rings(source)
