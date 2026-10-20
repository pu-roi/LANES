"""Deterministic, read-only spatial grouping shared by staff queues."""
import json
import math
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from shapely.affinity import scale
from shapely.errors import ShapelyError
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

T = TypeVar("T")


def complete_link_groups(items: Iterable[T], related: Callable[[T, T], bool]) -> list[list[T]]:
    """Input order establishes stable anchors; every pair must qualify."""
    groups: list[list[T]] = []
    for item in items:
        target = next((group for group in groups if all(related(item, other) for other in group)), None)
        if target is None:
            groups.append([item])
        else:
            target.append(item)
    return groups


def metric_geometry(raw: Any, *, projected: bool) -> BaseGeometry | None:
    try:
        if raw is None:
            return None
        geometry = shape(json.loads(raw) if isinstance(raw, str) else raw)
        if geometry.is_empty or not geometry.is_valid:
            return None
        # Production uses PostGIS UTM 51N. SQLite fixtures use a local WGS84 adapter.
        return geometry if projected else scale(geometry,
            xfact=111320 * math.cos(math.radians(14.58)), yfact=110574, origin=(0, 0))
    except (ValueError, TypeError, KeyError, ShapelyError):
        return None
