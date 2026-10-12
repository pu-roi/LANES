"""Versioned, reviewed administrative polygons; no online geocoding or writes.

Verification metadata records asset review, not field flood confirmation.
Missing/invalid coverage must never fall back to a broader city boundary.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from shapely.errors import ShapelyError
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from app.services.article_road_match_service import normalize_name
from app.services.philippine_location_service import get_philippine_location_service

DEFAULT_DIRECTORY = Path(__file__).resolve().parents[2] / "runtime_data" / "barangay-ncr"


class BoundaryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    city: str = Field(min_length=1, max_length=200)
    barangay: str = Field(min_length=1, max_length=200)
    psgc_code: str = Field(pattern=r"^[0-9]{9,10}$")
    geometry: dict
    osm_relation_id: int | None = Field(default=None, gt=0)
    source_url: str | None = Field(default=None, pattern=r"^https://", max_length=1000)


class BoundaryCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")
    format_version: Literal[1]
    source_id: str = Field(min_length=1, max_length=200)
    source_url: str = Field(pattern=r"^https://", max_length=1000)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    snapshot_at: datetime
    verified_at: datetime
    verified_by: str = Field(min_length=1, max_length=200)
    attribution: str = Field(min_length=1, max_length=1000)
    source_classification: Literal["reviewed_source", "osm_community"] = "reviewed_source"
    review_method: str | None = Field(default=None, min_length=1, max_length=1200)
    records: list[BoundaryRecord] = Field(min_length=1, max_length=2000)


class BoundaryCatalogReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    directory: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,99}$")
    catalog_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class BoundaryCatalogRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    format_version: Literal[2]
    catalogs: list[BoundaryCatalogReference] = Field(min_length=1, max_length=8)


def _city_key(name: str) -> str:
    value = normalize_name(name)
    if value.startswith("city of "):
        value = value[8:]
    return value[:-5] if value.endswith(" city") and value != "quezon city" else value


class BarangayBoundaryProvider:
    def __init__(self, directory: Path) -> None:
        self.digest: str | None = None
        self.catalog: BoundaryCatalog | None = None
        self.error: str | None = None
        self.records: dict[tuple[str, str], tuple[BoundaryRecord, BaseGeometry]] = {}
        self._record_catalogs: dict[tuple[str, str], BoundaryCatalog] = {}
        try:
            manifest_path, path = directory / "manifest.json", directory / "boundaries.json"
            if manifest_path.stat().st_size > 4096:
                raise ValueError("asset size limit")
            manifest_blob = manifest_path.read_bytes()
            manifest = json.loads(manifest_blob)
            if not isinstance(manifest, dict):
                raise ValueError("invalid boundary manifest")
            if manifest.get("format_version") == 2:
                registry = BoundaryCatalogRegistry.model_validate(manifest)
                if len({item.directory for item in registry.catalogs}) != len(registry.catalogs):
                    raise ValueError("duplicate boundary source")
                for item in registry.catalogs:
                    child_path = (directory / item.directory).resolve()
                    if child_path.parent != directory.resolve():
                        raise ValueError("boundary source escaped registry")
                    child_manifest = child_path / "manifest.json"
                    if child_manifest.stat().st_size > 4096:
                        raise ValueError("boundary source manifest size")
                    child_metadata = json.loads(child_manifest.read_bytes())
                    if not isinstance(child_metadata, dict):
                        raise ValueError("invalid boundary source manifest")
                    if child_metadata.get("format_version") == 2:
                        raise ValueError("nested boundary registry")
                    child = BarangayBoundaryProvider(child_path)
                    if child.error or child.catalog is None or child.digest != item.catalog_sha256:
                        raise ValueError("invalid boundary registry source")
                    # Only leaf source catalogs can be composed. First qualified
                    # source has explicit precedence; later sources fill gaps.
                    if child._record_catalogs:
                        raise ValueError("nested boundary registry")
                    if self.catalog is None:
                        self.catalog = child.catalog
                    for key, record in child.records.items():
                        if key not in self.records:
                            self.records[key] = record
                            self._record_catalogs[key] = child.catalog
                if len(self.records) > 2000:
                    raise ValueError("boundary registry size")
                self.digest = hashlib.sha256(manifest_blob).hexdigest()
                return
            if path.stat().st_size > 32_000_000:
                raise ValueError("asset size limit")
            expected = manifest["catalog_sha256"]
            raw = path.read_bytes()
            self.digest = hashlib.sha256(raw).hexdigest()
            if expected != self.digest:
                raise ValueError("boundary checksum")
            catalog = BoundaryCatalog.model_validate_json(raw)
            if (catalog.snapshot_at.tzinfo is None or catalog.verified_at.tzinfo is None
                    or catalog.verified_at < catalog.snapshot_at):
                raise ValueError("boundary clock")
            locations = get_philippine_location_service()
            for record in catalog.records:
                if catalog.source_classification == "osm_community" and (not catalog.review_method
                        or record.osm_relation_id is None
                        or record.source_url != f"https://www.openstreetmap.org/relation/{record.osm_relation_id}"):
                    raise ValueError("boundary community provenance")
                canonical = locations.normalize_barangay_name(record.barangay, record.city)
                entries = locations.barangays.get((canonical or "").casefold(), [])
                if not canonical or not any(e["psgc_code"] == record.psgc_code
                        and _city_key(e["city_municipality"]) == _city_key(record.city) for e in entries):
                    raise ValueError("boundary parent identity")
                key = (_city_key(record.city), normalize_name(canonical))
                polygon = shape(record.geometry)
                if (key in self.records or polygon.geom_type not in {"Polygon", "MultiPolygon"}
                        or polygon.is_empty or not polygon.is_valid):
                    raise ValueError("boundary geometry or duplicate identity")
                west, south, east, north = polygon.bounds
                if not (120 <= west < east <= 123 and 13 <= south < north <= 16):
                    raise ValueError("boundary extent")
                self.records[key] = (record, polygon)
            self.catalog = catalog
        except FileNotFoundError:
            self.catalog = None
            self.records = {}
            self._record_catalogs = {}
            self.error = "missing_valid_barangay_boundary"
        except (OSError, ValueError, TypeError, KeyError, ShapelyError):
            self.catalog = None
            self.records = {}
            self._record_catalogs = {}
            self.error = "invalid_barangay_boundary_catalog"

    def catalog_for(self, city: str, barangay: str) -> BoundaryCatalog | None:
        key = (_city_key(city), normalize_name(barangay))
        return self._record_catalogs.get(key, self.catalog) if key in self.records else None

    @property
    def revision(self) -> str:
        return f"{'bad-' if self.error else ''}{self.digest or 'none'}"

    def resolve(self, city: str, barangay: str, city_boundary: BaseGeometry) -> BaseGeometry | None:
        value = self.records.get((_city_key(city), normalize_name(barangay)))
        # Never trust a polygon from a different parent or repair it silently.
        if self.error or value is None or not city_boundary.covers(value[1]):
            return None
        return value[1]

    def resolution_reason(self, city: str, barangay: str, city_boundary: BaseGeometry) -> str | None:
        """Expose missing coverage separately from a checked-parent disagreement."""
        if self.error:
            return self.error
        value = self.records.get((_city_key(city), normalize_name(barangay)))
        if value is None:
            return "missing_valid_barangay_boundary"
        if not city_boundary.covers(value[1]):
            return "barangay_boundary_parent_mismatch"
        return None


@lru_cache(maxsize=1)
def get_barangay_boundary_provider() -> BarangayBoundaryProvider:
    return BarangayBoundaryProvider(Path(os.environ.get("LANES_NEWS_BARANGAY_DIR", str(DEFAULT_DIRECTORY))))
