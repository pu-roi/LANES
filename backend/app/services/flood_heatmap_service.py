"""Read-only heatmap display data; never changes flood eligibility or routing."""
import json
import math
from collections.abc import Iterable
from typing import Any

from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from shapely.errors import ShapelyError
from shapely.geometry import shape

from app.schemas.flood_event import HistoricalHeatmapFeature, HistoricalHeatmapPoint


def severity_weight(severity: Any) -> int:
    return {"low": 1, "medium": 2, "high": 3, "extreme": 5}.get(getattr(severity, "value", severity), 2)


def historical_heatmap_features(event_id: int, severity: Any, zones: Iterable[Any]) -> list[HistoricalHeatmapFeature]:
    """One point on each valid saved footprint, including multipart polygons."""
    features: list[HistoricalHeatmapFeature] = []
    for zone in zones:
        raw = zone.geometry
        try:
            geometry = to_shape(raw) if isinstance(raw, WKBElement) else shape(json.loads(raw) if isinstance(raw, str) else raw)
            if geometry.geom_type not in {"Polygon", "MultiPolygon"} or geometry.is_empty or not geometry.is_valid:
                continue
            west, south, east, north = geometry.bounds
            if not all(math.isfinite(v) for v in geometry.bounds) or not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
                continue
            point = geometry.representative_point()
            features.append(HistoricalHeatmapFeature(
                geometry=HistoricalHeatmapPoint(coordinates=(point.x, point.y)),
                properties={"event_id": event_id, "zone_id": zone.id, "weight": severity_weight(severity)},
            ))
        except (AttributeError, ValueError, TypeError, KeyError, ShapelyError):
            continue
    return features
