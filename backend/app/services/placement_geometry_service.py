"""Exact line parts shared by administrative clipping and modeled previews."""
from __future__ import annotations

import hashlib

from shapely import normalize
from shapely.affinity import scale
from shapely.geometry import LineString, MultiLineString, Point
from shapely.geometry.base import BaseGeometry
from shapely.ops import substring

# Numerical precision only (ten micrometres), never a placement/search radius.
LINE_PRECISION_METRES = 0.00001


def source_aligned_line_union(source: BaseGeometry, fragments: list[BaseGeometry]) -> BaseGeometry:
    """Union hazard overlaps along their original line without duplicate slivers.

    Polygon intersection roundoff can make coincident scenario fragments form
    tiny parallel lines. Validate and project them to source-distance intervals,
    then rebuild the original bends. Only numerical gaps below ten micrometres
    are joined; actual dry gaps and scenario evidence remain separate.
    """
    from app.services.noah_vector_catalog_service import metric_geometry, X_METRES, Y_METRES

    if source.geom_type != "LineString" or not source.is_simple or source.length <= 0:
        raise ValueError("invalid_source_centerline")
    metric = metric_geometry(source)
    intervals: list[tuple[float, float]] = []
    tolerance = metric.buffer(LINE_PRECISION_METRES)
    for fragment in fragments:
        part = metric_geometry(fragment)
        if part.geom_type != "LineString" or not tolerance.covers(part):
            raise ValueError("modeled_fragment_outside_source_line")
        bounds = sorted(metric.project(Point(point)) for point in (part.coords[0], part.coords[-1]))
        start, end = bounds
        if end - start <= 0:
            continue
        section = substring(metric, start, end)
        if not section.buffer(LINE_PRECISION_METRES).covers(part) or not part.buffer(LINE_PRECISION_METRES).covers(section):
            raise ValueError("modeled_fragment_shortcuts_source_line")
        intervals.append((start, end))
    merged: list[list[float]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1] + LINE_PRECISION_METRES:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([start, end])
    parts = [scale(substring(metric, start, end), xfact=1 / X_METRES,
                   yfact=1 / Y_METRES, origin=(0, 0)) for start, end in merged]
    return parts[0] if len(parts) == 1 else MultiLineString(parts) if parts else LineString()


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
