"""Conservative float construction for an internally generated policy corridor.

Never used to import/repair submitted or source polygons. Final containment
predicates remain exact; unsupported construction always fails closed.
"""
from __future__ import annotations

import math
from shapely import get_coordinates
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.geometry.base import BaseGeometry
from app.services.noah_vector_catalog_service import X_METRES, Y_METRES
from app.services.placement_geometry_service import LINE_PRECISION_METRES

MAX_FLOAT_STEPS = 4
MAX_CONSTRUCTION_VERTICES = 10_000


def generated_corridor_intersection(buffer: BaseGeometry, parent: BaseGeometry,
                                    core: BaseGeometry) -> BaseGeometry:
    """Construct a contained subset of the unchanged policy buffer and parent.

    Only new intersection coordinates may be conservatively rounded to nearby
    representable floats. Input vertices, holes and components are preserved.
    """
    result = buffer.intersection(parent)
    if (result.geom_type not in {"Polygon", "MultiPolygon"} or result.is_empty
            or not result.is_valid or len(get_coordinates(result)) > MAX_CONSTRUCTION_VERTICES):
        raise ValueError("generated_corridor_precision_unresolved")
    if parent.covers(result) and buffer.covers(result) and result.covers(core):
        return result
    if not parent.covers(core) or not buffer.covers(core) or not result.covers(core):
        raise ValueError("generated_corridor_precision_unresolved")
    preserved = {tuple(point) for source in (buffer, parent, core) for point in get_coordinates(source)}

    def neighbors(value: float) -> list[float]:
        values = [value]
        for direction in (-math.inf, math.inf):
            current = value
            for _ in range(MAX_FLOAT_STEPS):
                current = math.nextafter(current, direction)
                values.append(current)
        return values

    def displacement(point: tuple[float, float], candidate: tuple[float, float]) -> float:
        return math.hypot((candidate[0]-point[0])*X_METRES, (candidate[1]-point[1])*Y_METRES)

    def construct_ring(ring: BaseGeometry) -> list[tuple[float, float]]:
        coordinates = []
        for raw in ring.coords:
            point = tuple(raw)
            if parent.covers(Point(point)) and buffer.covers(Point(point)):
                coordinates.append(point)
                continue
            if point in preserved:
                raise ValueError("generated_corridor_precision_unresolved")
            candidates = [(x, y) for x in neighbors(point[0]) for y in neighbors(point[1])
                if displacement(point, (x, y)) <= LINE_PRECISION_METRES
                and parent.covers(Point(x, y)) and buffer.covers(Point(x, y))]
            if not candidates:
                raise ValueError("generated_corridor_precision_unresolved")
            coordinates.append(min(candidates, key=lambda value: (displacement(point, value), value)))
        return coordinates

    originals = [result] if result.geom_type == "Polygon" else list(result.geoms)
    parts = [Polygon(construct_ring(part.exterior), [construct_ring(ring) for ring in part.interiors])
             for part in originals]
    constructed = parts[0] if result.geom_type == "Polygon" else MultiPolygon(parts)
    if (not constructed.is_valid or constructed.is_empty
            or not parent.covers(constructed) or not buffer.covers(constructed) or not constructed.covers(core)):
        raise ValueError("generated_corridor_precision_unresolved")
    return constructed
