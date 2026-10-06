"""Operational flood footprint validation service.

Enforces that an operational avoidance zone requires a valid PostGIS POLYGON
with positive area and explicit source provenance, contained within the
reported administrative locality. Centerlines, point markers, and ungrounded
buffer guesses are rejected.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from math import isfinite

from shapely import get_coordinates, get_srid

from app.crud.news_evaluation import canonical_sha256
from app.schemas.news_publication import OperationalFootprintProvenance
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


def validate_operational_shape(
    geometry_input: Any,
    *,
    parent_boundary: BaseGeometry | None = None,
    geometry_srid: int | None = None,
) -> OperationalFootprintValidation:
    """Check declared WGS84 shape, topology, area and full parent containment.

    Valid shape alone is not approval. Preserve every disconnected component;
    reject invalid/tiny parts rather than repairing, clipping or dropping them.
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
            if set(geometry_input) - {"type", "coordinates"}:
                return OperationalFootprintValidation(False, "invalid_geometry_syntax")
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

    if type(geometry_srid) is not int or geometry_srid != 4326:
        return OperationalFootprintValidation(False, "unsupported_or_missing_geometry_srid")
    if isinstance(geometry_input, BaseGeometry) and get_srid(geom) != 4326:
        return OperationalFootprintValidation(False, "geometry_srid_mismatch")
    if geom.has_z or getattr(geom, "has_m", False):
        return OperationalFootprintValidation(False, "unsupported_coordinate_dimensions")
    if len(get_coordinates(geom)) > 10000:
        return OperationalFootprintValidation(False, "operational_geometry_size_limit")
    area_sqm = float(metric_geometry(geom).area)
    if not isfinite(area_sqm) or area_sqm < 1.0:
        return OperationalFootprintValidation(
            is_eligible=False,
            reason_code="zero_or_negligible_area",
            geometry=geom,
            area_sqm=area_sqm,
        )
    if parent_boundary is not None:
        if (not isinstance(parent_boundary, BaseGeometry) or parent_boundary.geom_type not in ("Polygon", "MultiPolygon")
                or parent_boundary.is_empty or not parent_boundary.is_valid or get_srid(parent_boundary) != 4326):
            return OperationalFootprintValidation(False, "invalid_parent_boundary")
        if not parent_boundary.covers(geom):
            return OperationalFootprintValidation(False, "outside_parent_locality")

    parts: list[dict[str, Any]] = []
    if geom.geom_type == "Polygon":
        parts.append(mapping(geom))
    elif geom.geom_type == "MultiPolygon":
        for part in geom.geoms:
            if not part.is_empty and metric_geometry(part).area >= 1.0:
                parts.append(mapping(part))

    if len(parts) > 25:
        return OperationalFootprintValidation(False, "operational_component_limit")
    expected_count = 1 if geom.geom_type == "Polygon" else len(geom.geoms)
    if len(parts) != expected_count:
        return OperationalFootprintValidation(False, "zero_or_negligible_component_area")
    computed_checksum = canonical_sha256(mapping(geom))

    return OperationalFootprintValidation(
        is_eligible=True,
        reason_code="valid_operational_shape",
        geometry=geom,
        geojson=mapping(geom),
        polygon_parts=parts,
        area_sqm=area_sqm,
        provenance_checksum=computed_checksum,
    )


def validate_operational_footprint(geometry_input: Any, *, provenance_source: str | None = None,
        provenance_checksum: str | None = None, parent_boundary: BaseGeometry | None = None,
        allow_unverified: bool = False, geometry_srid: int | None = None,
        trusted_provenance: OperationalFootprintProvenance | None = None) -> OperationalFootprintValidation:
    """Only the server evidence service supplies trusted_provenance.

    Client labels/checksums and the deprecated preview flag cannot approve a zone.
    """
    result = validate_operational_shape(geometry_input, geometry_srid=geometry_srid, parent_boundary=parent_boundary)
    if not result.is_eligible:
        return result
    if trusted_provenance is None or trusted_provenance.binding is None:
        return replace(result, is_eligible=False, reason_code=("unverified_geometry_provenance"
            if provenance_source or allow_unverified else "missing_geometry_provenance"))
    if parent_boundary is None:
        return replace(result, is_eligible=False, reason_code="missing_parent_locality_boundary")
    binding = trusted_provenance.binding
    if (not trusted_provenance.source_checksum
            or trusted_provenance.geometry_sha256 != canonical_sha256(result.geojson)
            or trusted_provenance.parent_boundary_sha256 != canonical_sha256(mapping(parent_boundary))
            or binding.component_sha256 != [canonical_sha256(part) for part in result.polygon_parts]
            or binding.srid != geometry_srid):
        return replace(result, is_eligible=False, reason_code="operational_geometry_evidence_mismatch")
    return replace(result, reason_code="verified_operational_footprint",
                   provenance_source=trusted_provenance.source, provenance_checksum=trusted_provenance.source_checksum)
