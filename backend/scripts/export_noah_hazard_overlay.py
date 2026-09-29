"""Render the three Metro Manila NOAH archives as transparent map display images.

Run from the repository root after placing the inspected archives in ``data/``::

    python backend/scripts/export_noah_hazard_overlay.py

These images are for map presentation only. Road intersection and routing logic
must continue to use source vectors and independently verified flood reports.
"""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path
from zipfile import ZipFile

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "frontend" / "public" / "noah-hazard"
ARCHIVES = {
    5: ROOT / "data" / "noah_metro_5yr_inspect.zip",
    25: ROOT / "data" / "noah_metro_25yr_inspect.zip",
    100: ROOT / "data" / "noah_metro_100yr_inspect.zip",
}
COLORS = {1: (250, 204, 21, 255), 2: (249, 115, 22, 255), 3: (220, 38, 38, 255)}
WIDTH = 2048
HEIGHT = 4096


def mercator_y(latitude: float) -> float:
    radians = math.radians(latitude)
    return math.log(math.tan(math.pi / 4 + radians / 2))


def archive_bounds(path: Path) -> tuple[float, float, float, float]:
    with ZipFile(path) as archive:
        shp_name = next(name for name in archive.namelist() if name.lower().endswith(".shp"))
        with archive.open(shp_name) as shp:
            shp.seek(36)
            return struct.unpack("<4d", shp.read(32))


def render(path: Path, bounds: tuple[float, float, float, float]) -> Image.Image:
    min_x, min_y, max_x, max_y = bounds
    top_y, bottom_y = mercator_y(max_y), mercator_y(min_y)
    image = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))

    with ZipFile(path) as archive:
        shp = archive.read(next(name for name in archive.namelist() if name.lower().endswith(".shp")))
        dbf = archive.read(next(name for name in archive.namelist() if name.lower().endswith(".dbf")))
        header_length, record_length = struct.unpack_from("<HH", dbf, 8)
        record_count = struct.unpack_from("<I", dbf, 4)[0]
        if record_count != 3:
            raise ValueError(f"Expected three NOAH hazard classes in {path}")

        position = 100
        for record_index in range(record_count):
            content_bytes = struct.unpack_from(">I", shp, position + 4)[0] * 2
            start = position + 8
            if struct.unpack_from("<I", shp, start)[0] != 5:
                raise ValueError(f"Expected polygon shapefile in {path}")
            part_count, point_count = struct.unpack_from("<II", shp, start + 36)
            offsets = struct.unpack_from(f"<{part_count}I", shp, start + 44)
            point_offset = start + 44 + 4 * part_count
            value_offset = header_length + record_index * record_length + 1
            value = dbf[value_offset:value_offset + record_length - 1].decode("ascii").strip()
            hazard_class = int(float(value))
            if hazard_class not in COLORS:
                raise ValueError(f"Unknown hazard class {hazard_class} in {path}")

            # Keep holes in a separate class mask. Clearing a hole must not erase
            # another class that may appear beneath it.
            mask = Image.new("L", (WIDTH, HEIGHT), 0)
            draw = ImageDraw.Draw(mask)
            for part_index, first in enumerate(offsets):
                last = offsets[part_index + 1] if part_index + 1 < part_count else point_count
                if last - first < 4:
                    continue
                raw = list(struct.iter_unpack("<dd", shp[point_offset + first * 16:point_offset + last * 16]))
                ring = [
                    (
                        round((lng - min_x) / (max_x - min_x) * (WIDTH - 1)),
                        round((top_y - mercator_y(lat)) / (top_y - bottom_y) * (HEIGHT - 1)),
                    )
                    for lng, lat in raw
                ]
                # ESRI polygons use clockwise exterior rings and counterclockwise holes.
                signed_area = sum(
                    raw[i][0] * raw[i + 1][1] - raw[i + 1][0] * raw[i][1]
                    for i in range(len(raw) - 1)
                )
                draw.polygon(ring, fill=255 if signed_area < 0 else 0)
            image.paste(Image.new("RGBA", image.size, COLORS[hazard_class]), (0, 0), mask)
            position = start + content_bytes
    return image


def main() -> None:
    missing = [str(path) for path in ARCHIVES.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing NOAH source archives: {', '.join(missing)}")
    boxes = [archive_bounds(path) for path in ARCHIVES.values()]
    bounds = (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for scenario, path in ARCHIVES.items():
        image = render(path, bounds)
        target = OUTPUT / f"metro-manila-{scenario}yr.png"
        image.save(target, optimize=True)
        print(f"{scenario}-year: {target.relative_to(ROOT)} ({target.stat().st_size:,} bytes)")
    manifest = {"bounds": bounds, "width": WIDTH, "height": HEIGHT, "scenarios": sorted(ARCHIVES)}
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
