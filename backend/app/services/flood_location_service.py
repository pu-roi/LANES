"""Complete source-consistent Pasig locality detection, separate from flood extent."""
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

from shapely.geometry import shape
from shapely.ops import unary_union
from shapely.errors import ShapelyError

from app.services.barangay_boundary_service import BarangayBoundaryProvider
from app.services.philippine_location_service import get_philippine_location_service

DEFAULT_DIRECTORY = Path(__file__).resolve().parents[2]/"runtime_data/flood-location"


class FloodLocationProvider(BarangayBoundaryProvider):
    def __init__(self, directory: Path):
        super().__init__(directory)
        self.city_boundary = None
        if self.error:
            return
        try:
            manifest = json.loads((directory/"manifest.json").read_text(encoding="utf-8"))
            raw = (directory/"city.geojson").read_bytes()
            if len(raw) > 1_000_000 or hashlib.sha256(raw).hexdigest() != manifest["city_sha256"]:
                raise ValueError("Parent city checksum")
            self.city_boundary = shape(json.loads(raw)["geometry"])
            if not self.city_boundary.is_valid or self.city_boundary.is_empty:
                raise ValueError("Parent city geometry")
            expected = set(get_philippine_location_service().get_pasig_barangays())
            if {r.barangay for r,_ in self.records.values()} != expected or len(self.records) != 30:
                raise ValueError("Incomplete Pasig locality identities")
            polygons = [p for _,p in self.records.values()]
            if any(r.city != "City of Pasig" or not self.city_boundary.covers(p) for r,p in self.records.values()):
                raise ValueError("Wrong parent or mismatched source partition")
            if self.city_boundary.symmetric_difference(unary_union(polygons)).area > 1e-12:
                raise ValueError("Source partition gap")
            if any(a.intersection(b).area > 1e-12 for i,a in enumerate(polygons) for b in polygons[i+1:]):
                raise ValueError("Ambiguous source interiors")
        except (OSError, ValueError, TypeError, KeyError, ShapelyError):
            self.records = {}
            self.city_boundary = None
            self.error = "invalid_flood_location_catalog"


@lru_cache(maxsize=1)
def get_flood_location_provider() -> FloodLocationProvider:
    return FloodLocationProvider(Path(os.getenv("LANES_FLOOD_LOCATION_DIR",str(DEFAULT_DIRECTORY))))
