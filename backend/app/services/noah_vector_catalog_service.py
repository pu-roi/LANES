"""Checksummed, tiled NOAH source vectors; no network, DB or public writes.

Tiles retain source polygon holes and are never simplified. An affine local
projection reports approximate metres, while intersections use exact WGS84
vectors. Missing/corrupt assets are errors, never zero hazard or safe roads.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from shapely.affinity import scale
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

X_METRES = 111320.0 * math.cos(math.radians(14.58))
Y_METRES = 110574.0
DEFAULT_DIRECTORY = Path(__file__).resolve().parents[3] / "data" / "noah-placement"


def metric_geometry(geometry: BaseGeometry) -> BaseGeometry:
    return scale(geometry, xfact=X_METRES, yfact=Y_METRES, origin=(0, 0))


def tile_keys(bounds: tuple[float, float, float, float], size: float) -> list[str]:
    west, south, east, north = bounds
    return [f"{x}:{y}" for x in range(math.floor(west / size), math.floor(east / size) + 1)
            for y in range(math.floor(south / size), math.floor(north / size) + 1)]


class NoahAssetError(ValueError):
    """Public reason codes avoid leaking filesystem paths."""


class ScenarioManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str = Field(min_length=1, max_length=200)
    archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    tiles: dict[str, str]


class NoahManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    format_version: Literal[1] = 1
    tile_size: float = Field(ge=0.005, le=0.05)
    bounds: tuple[float, float, float, float]
    attribution: str = Field(min_length=1, max_length=1000)
    license: str
    scenarios: dict[int, ScenarioManifest]


class NoahVectorCatalog:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.manifest: NoahManifest | None = None
        self.digest: str | None = None
        self.error: str | None = None
        self._assets_checked = False
        try:
            path = directory / "manifest.json"
            if path.stat().st_size > 1_000_000:
                raise ValueError("manifest limit")
            raw = path.read_bytes()
            self.digest = hashlib.sha256(raw).hexdigest()
            manifest = NoahManifest.model_validate_json(raw)
            west, south, east, north = manifest.bounds
            if (set(manifest.scenarios) != {5, 25, 100} or manifest.license != "ODbL-1.0"
                    or not (120 <= west < east <= 123 and 13 <= south < north <= 16)
                    or east - west > 1 or north - south > 1):
                raise ValueError("invalid catalog extent or scenarios")
            required = set(tile_keys(manifest.bounds, manifest.tile_size))
            for scenario in manifest.scenarios.values():
                if set(scenario.tiles) != required or any(
                        len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)
                        for digest in scenario.tiles.values()):
                    raise ValueError("incomplete tile manifest")
            self.manifest = manifest
        except FileNotFoundError:
            self.error = "noah_catalog_not_configured"
        except (OSError, ValueError, TypeError):
            self.error = "invalid_noah_catalog"

    @property
    def revision(self) -> str:
        self._check_assets()
        return f"{'bad-' if self.error else ''}{self.digest or 'none'}"

    def _check_assets(self) -> None:
        if self._assets_checked or self.error or self.manifest is None:
            return
        self._assets_checked = True
        total = 0
        try:
            for period, scenario in self.manifest.scenarios.items():
                for key, expected in scenario.tiles.items():
                    path = self.directory / str(period) / f"{key.replace(':', '_')}.json.gz"
                    size = path.stat().st_size
                    total += size
                    if size > 4_000_000 or total > 256_000_000:
                        raise ValueError("catalog asset limit")
                    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                        raise ValueError("tile checksum")
        except (OSError, ValueError):
            self.error = "missing_or_invalid_noah_tile"

    @lru_cache(maxsize=48)
    def _tile(self, period: int, key: str) -> dict[int, BaseGeometry]:
        if self.manifest is None:
            raise NoahAssetError(self.error or "noah_catalog_not_configured")
        expected = self.manifest.scenarios[period].tiles[key]
        # Keys are computed from numeric coordinates, never caller filenames.
        path = self.directory / str(period) / f"{key.replace(':', '_')}.json.gz"
        try:
            if path.stat().st_size > 4_000_000:
                raise ValueError("tile compressed limit")
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError("tile checksum")
            with gzip.open(path, "rb") as stream:
                decoded = stream.read(24_000_001)
            if len(decoded) > 24_000_000:
                raise ValueError("tile expanded limit")
            payload = json.loads(decoded)
            if set(payload) != {"1", "2", "3"}:
                raise ValueError("missing classes")
            polygons = {int(k): shape(v) for k, v in payload.items()}
            for polygon in polygons.values():
                if (polygon.geom_type not in {"Polygon", "MultiPolygon"}
                        or not polygon.is_valid):
                    raise ValueError("invalid hazard polygon")
            return polygons
        except (OSError, ValueError, TypeError, KeyError, EOFError) as exc:
            raise NoahAssetError("missing_or_invalid_noah_tile") from exc

    def overlaps(self, line: BaseGeometry) -> dict[int, dict[int, float]]:
        return {period: {hazard: metric_geometry(geometry).length for hazard, geometry in classes.items()}
                for period, classes in self.intersections(line).items()}

    def intersections(self, line: BaseGeometry) -> dict[int, dict[int, BaseGeometry]]:
        """Exact per-scenario/class intersections, preserving holes and gaps."""
        self._check_assets()
        if self.error or self.manifest is None:
            raise NoahAssetError(self.error or "noah_catalog_not_configured")
        west, south, east, north = line.bounds
        cw, cs, ce, cn = self.manifest.bounds
        if (line.geom_type != "LineString" or line.is_empty or not line.is_valid
                or line.length <= 0 or not (cw <= west <= east <= ce and cs <= south <= north <= cn)):
            raise NoahAssetError("road_outside_noah_catalog_extent")
        keys = tile_keys(line.bounds, self.manifest.tile_size)
        if len(keys) > 128:
            raise NoahAssetError("noah_query_extent_limit")
        # Union before measuring to avoid double counting a road on tile edges.
        from shapely import union_all
        from shapely.errors import ShapelyError
        try:
            result = {}
            for period in (5, 25, 100):
                tiles = [self._tile(period, key) for key in keys]
                result[period] = {hazard: union_all([
                    line.intersection(tile[hazard]) for tile in tiles])
                    for hazard in (1, 2, 3)}
                if sum(metric_geometry(g).length for g in result[period].values()) > metric_geometry(line).length + 0.1:
                    raise NoahAssetError("overlapping_noah_classes")
            return result
        except ShapelyError as exc:
            raise NoahAssetError("invalid_noah_intersection") from exc


@lru_cache(maxsize=1)
def get_noah_vector_catalog() -> NoahVectorCatalog:
    return NoahVectorCatalog(Path(os.environ.get("LANES_NEWS_NOAH_DIR", str(DEFAULT_DIRECTORY))))
