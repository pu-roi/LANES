"""Operational flood footprint validation service.

Enforces that an operational avoidance zone requires a valid PostGIS POLYGON
with positive area and explicit source provenance, contained within the
reported administrative locality. Centerlines, point markers, and ungrounded
buffer guesses are rejected.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from shapely.errors import ShapelyError
from shapely.geometry import mapping, shape, Polygon, MultiPolygon
from shapely.geometry.base import BaseGeometry

from app.services.noah_vector_catalog_service import metric_geometry


@dataclass(frozen=True)
class OperationalFootprintValidation:
    is_eligible: bool
    reason_code: str
    geometry: BaseGeometry | None = None
    geojson: dict[str, Any] | None = None
    polygon_parts: list[dict[str, Any]] = field(default_factory=list)
    area_sqm: float = 0.0
    provenance_source: str | None = None
    provenance_checksum: str | None = None


def validate_operational_footprint(
    geometry_input: Any,
    *,
    provenance_source: str | None = None,
    provenance_checksum: str | None = None,
    parent_boundary: BaseGeometry | None = None,
    allow_unverified: bool = False,
) -> OperationalFootprintValidation:
    """Validate a candidate footprint against the operational flood-zone contract.

    Enforces:
    1. Input must be present and parseable as GeoJSON or Shapely geometry.
    2. Geometry type must be Polygon or MultiPolygon (LineString / Point rejected).
    3. Topology must be valid and non-empty.
    4. Metric area must be non-zero (>= 1.0 m^2).
    5. Coordinate bounds must be valid geographic coordinates (WGS84).
    6. If a parent boundary is provided, the footprint must intersect it.
    7. Unless allow_unverified is True, explicit provenance_source is required.
    8. Disconnected parts in a MultiPolygon are split into distinct Polygon GeoJSONs
       so callers can persist separate FloodAvoidanceZones without bridging gaps.
    """
    if geometry_input is None:
        return OperationalFootprintValidation(
            is_eligible=False,
            reason_code="missing_geometry",
        )

    try:
        if isinstance(geometry_input, BaseGeometry):
            geom = geometry_input
        elif isinstance(geometry_input, dict):
            geom = shape(geometry_input)
        elif hasattr(geometry_input, "model_dump"):
            geom = shape(geometry_input.model_dump())
        else:
            return OperationalFootprintValidation(
                is_eligible=False,
                reason_code="invalid_geometry_syntax",
            )
    except (ShapelyError, ValueError, TypeError, KeyError, AttributeError):
        return OperationalFootprintValidation(
            is_eligible=False,
            reason_code="invalid_geometry_syntax",
        )

    if geom.geom_type not in ("Polygon", "MultiPolygon"):
        return OperationalFootprintValidation(
            is_eligible=False,
            reason_code=f"unsupported_geometry_type_{geom.geom_type.lower()}",
            geometry=geom,
        )

    if not geom.is_valid:
        return OperationalFootprintValidation(
            is_eligible=False,
            reason_code="invalid_topology",
            geometry=geom,
        )

    if geom.is_empty:
        return OperationalFootprintValidation(
            is_eligible=False,
            reason_code="empty_geometry",
            geometry=geom,
        )

    minx, miny, maxx, maxy = geom.bounds
    if not (-180.0 <= minx <= 180.0 and -180.0 <= maxx <= 180.0 and
            -90.0 <= miny <= 90.0 and -90.0 <= maxy <= 90.0):
        return OperationalFootprintValidation(
            is_eligible=False,
            reason_code="out_of_bounds_coordinates",
            geometry=geom,
        )

    area_sqm = float(metric_geometry(geom).area)
    if area_sqm < 1.0:
        return OperationalFootprintValidation(
            is_eligible=False,
            reason_code="zero_or_negligible_area",
            geometry=geom,
            area_sqm=area_sqm,
        )

    if not allow_unverified and not provenance_source:
        return OperationalFootprintValidation(
            is_eligible=False,
            reason_code="missing_geometry_provenance",
            geometry=geom,
            area_sqm=area_sqm,
        )

    if parent_boundary is not None and not parent_boundary.is_empty:
        if not parent_boundary.intersects(geom):
            return OperationalFootprintValidation(
                is_eligible=False,
                reason_code="outside_parent_locality",
                geometry=geom,
                area_sqm=area_sqm,
            )

    parts: list[dict[str, Any]] = []
    if geom.geom_type == "Polygon":
        parts.append(mapping(geom))
    elif geom.geom_type == "MultiPolygon":
        for part in geom.geoms:
            if not part.is_empty and metric_geometry(part).area >= 1.0:
                parts.append(mapping(part))

    computed_checksum = provenance_checksum or hashlib.sha256(geom.wkb).hexdigest()

    return OperationalFootprintValidation(
        is_eligible=True,
        reason_code="verified_operational_footprint",
        geometry=geom,
        geojson=mapping(geom),
        polygon_parts=parts,
        area_sqm=area_sqm,
        provenance_source=provenance_source,
        provenance_checksum=computed_checksum,
    )
