"""Exact line parts shared by administrative clipping and modeled previews."""
from __future__ import annotations

import hashlib

from shapely import normalize
from shapely.geometry.base import BaseGeometry


def line_parts(geometry: BaseGeometry) -> list[BaseGeometry]:
    """Discard point contacts; never join lines across gaps or simplify them."""
    if geometry.is_empty:
        return []
    if geometry.geom_type == "LineString":
        return [normalize(geometry)] if geometry.length > 0 else []
    parts = [part for child in getattr(geometry, "geoms", ()) for part in line_parts(child)]
    return sorted(parts, key=lambda part: part.wkb_hex)


def geometry_id(namespace: str, geometry: BaseGeometry) -> str:
    return hashlib.sha256(namespace.encode() + normalize(geometry).wkb).hexdigest()
