"""Shared, server-side flood-routing policy and route exposure evaluator.

Routing providers generate candidate geometries only. This module is the single
source of truth for flood eligibility, exposure and presentation ranking.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Iterable, Literal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models

VehicleProfile = Literal["walk", "motorcycle", "light", "heavy"]
Severity = Literal["low", "medium", "high", "extreme"]

SEVERITY_ORDER: dict[str, int] = {"none": 0, "low": 1, "medium": 2, "high": 3, "extreme": 4}


@dataclass(frozen=True)
class ActiveFloodZone:
    id: int
    severity: Severity
    polygon: list[list[float]]
    passable_vehicles: str | None = None


def get_active_flood_zones(db: Session) -> list[ActiveFloodZone]:
    """Load active, unexpired authoritative PostGIS zone geometries once."""
    rows = db.query(
        models.FloodAvoidanceZone,
        func.ST_AsGeoJSON(models.FloodAvoidanceZone.geometry).label("geojson"),
    ).filter(
        models.FloodAvoidanceZone.is_active.is_(True),
        (models.FloodAvoidanceZone.expires_at.is_(None))
        | (models.FloodAvoidanceZone.expires_at > func.now()),
    ).all()

    zones: list[ActiveFloodZone] = []
    for zone, geojson in rows:
        if not geojson:
            continue
        geometry = json.loads(geojson)
        if geometry.get("type") != "Polygon" or not geometry.get("coordinates"):
            continue
        raw_severity = zone.severity.value if hasattr(zone.severity, "value") else zone.severity
        severity = str(raw_severity).lower()
        if severity not in {"low", "medium", "high", "extreme"}:
            continue
        zones.append(ActiveFloodZone(
            id=zone.id,
            severity=severity,  # type: ignore[arg-type]
            polygon=geometry["coordinates"][0],
            passable_vehicles=zone.passable_vehicles,
        ))
    return zones


def _profile_tokens(profile: VehicleProfile) -> set[str]:
    return {
        "walk": {"walk", "pedestrian"},
        "motorcycle": {"motorcycle", "bicycle", "bike", "e-bike"},
        "light": {"light", "sedan", "hatchback"},
        "heavy": {"heavy", "suv", "pickup", "truck", "bus"},
    }[profile]


def _override_allows(profile: VehicleProfile, value: str | None) -> bool | None:
    """Return a restrictive official override decision, or None when unrecognised."""
    if not value:
        return None
    raw_value = value.lower()
    normalized = {item.strip().lower() for item in value.replace("/", ",").split(",") if item.strip()}
    if profile == "walk":
        if any(phrase in raw_value for phrase in ("no pedestrians", "pedestrians prohibited", "no walking", "walking prohibited")):
            return False
        # Survey lists commonly record only vehicle types. Their omission of
        # pedestrians is not an explicit instruction to forbid walking.
        if not normalized.intersection({"walk", "pedestrians", "pedestrian"}):
            return None
    known = {"walk", "pedestrians", "pedestrian", "bicycle", "bicycles", "e-bikes", "motorcycle", "motorcycles", "light", "sedans", "hatchbacks", "suv", "suvs", "pickups", "heavy", "trucks", "buses"}
    if not normalized.intersection(known):
        return None
    tokens = _profile_tokens(profile)
    return any(token in item for item in normalized for token in tokens)


def zone_decision(profile: VehicleProfile, zone: ActiveFloodZone) -> Literal["passable", "cautious", "blocked"]:
    """Apply MMDA-aligned rules; explicit official data can only tighten them."""
    if zone.severity == "extreme":
        baseline = "blocked"
    elif zone.severity == "high":
        # Public walking may traverse Orange only as a highly visible,
        # strongly discouraged option. Every vehicle remains hard-blocked.
        baseline = "cautious" if profile == "walk" else "blocked"
    elif zone.severity == "medium":
        baseline = "cautious" if profile in {"walk", "heavy"} else "blocked"
    else:
        baseline = "passable"

    if _override_allows(profile, zone.passable_vehicles) is False:
        return "blocked"
    return baseline


def polygons_for(zones: Iterable[ActiveFloodZone], profile: VehicleProfile, decisions: set[str]) -> list[list[list[float]]]:
    return [zone.polygon for zone in zones if zone_decision(profile, zone) in decisions]


def _point_in_polygon(point: list[float], polygon: list[list[float]]) -> bool:
    x, y = point
    inside = False
    for index, current in enumerate(polygon):
        previous = polygon[index - 1]
        xi, yi = current
        xj, yj = previous
        intersects = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi)
        if intersects:
            inside = not inside
    return inside


def _orientation(a: list[float], b: list[float], c: list[float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _segments_intersect(a: list[float], b: list[float], c: list[float], d: list[float]) -> bool:
    first = _orientation(a, b, c)
    second = _orientation(a, b, d)
    third = _orientation(c, d, a)
    fourth = _orientation(c, d, b)
    def on_segment(start: list[float], point: list[float], end: list[float]) -> bool:
        return min(start[0], end[0]) <= point[0] <= max(start[0], end[0]) and min(start[1], end[1]) <= point[1] <= max(start[1], end[1])
    if first == 0 and on_segment(a, c, b): return True
    if second == 0 and on_segment(a, d, b): return True
    if third == 0 and on_segment(c, a, d): return True
    if fourth == 0 and on_segment(c, b, d): return True
    return (first > 0) != (second > 0) and (third > 0) != (fourth > 0)


def _line_intersects_polygon(coordinates: list[list[float]], polygon: list[list[float]]) -> bool:
    if any(_point_in_polygon(point, polygon) for point in coordinates):
        return True
    edges = list(zip(polygon, polygon[1:] + polygon[:1]))
    return any(_segments_intersect(start, end, edge_start, edge_end) for start, end in zip(coordinates, coordinates[1:]) for edge_start, edge_end in edges)


def _meters(a: list[float], b: list[float]) -> float:
    longitude_delta = math.radians(b[0] - a[0])
    latitude_delta = math.radians(b[1] - a[1])
    latitude_a = math.radians(a[1])
    latitude_b = math.radians(b[1])
    value = math.sin(latitude_delta / 2) ** 2 + math.cos(latitude_a) * math.cos(latitude_b) * math.sin(longitude_delta / 2) ** 2
    return 6_371_000 * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def _segment_intersection_fraction(
    start: list[float], end: list[float], edge_start: list[float], edge_end: list[float],
) -> float | None:
    """Return the route-segment fraction at a non-collinear polygon-edge crossing."""
    route_x, route_y = end[0] - start[0], end[1] - start[1]
    edge_x, edge_y = edge_end[0] - edge_start[0], edge_end[1] - edge_start[1]
    divisor = route_x * edge_y - route_y * edge_x
    if abs(divisor) < 1e-12:
        return None
    offset_x, offset_y = edge_start[0] - start[0], edge_start[1] - start[1]
    route_fraction = (offset_x * edge_y - offset_y * edge_x) / divisor
    edge_fraction = (offset_x * route_y - offset_y * route_x) / divisor
    if 0 <= route_fraction <= 1 and 0 <= edge_fraction <= 1:
        return route_fraction
    return None


def _intersected_distance(coordinates: list[list[float]], polygon: list[list[float]]) -> float:
    """Clip each route segment against a polygon to measure the exposed metres."""
    exposed = 0.0
    edges = list(zip(polygon, polygon[1:] + polygon[:1]))
    for start, end in zip(coordinates, coordinates[1:]):
        fractions = [0.0, 1.0]
        for edge_start, edge_end in edges:
            crossing = _segment_intersection_fraction(start, end, edge_start, edge_end)
            if crossing is not None:
                fractions.append(crossing)
        fractions = sorted(set(fractions))
        segment_meters = _meters(start, end)
        for left, right in zip(fractions, fractions[1:]):
            midpoint = [(start[0] + (end[0] - start[0]) * (left + right) / 2), (start[1] + (end[1] - start[1]) * (left + right) / 2)]
            if _point_in_polygon(midpoint, polygon):
                exposed += segment_meters * (right - left)
    return exposed


def evaluate_route(route: dict[str, Any], zones: Iterable[ActiveFloodZone], profile: VehicleProfile) -> dict[str, Any]:
    """Attach actual geometry-based flood exposure to one provider candidate."""
    coordinates = route.get("geometry", {}).get("coordinates", [])
    hits: list[tuple[ActiveFloodZone, str]] = []
    for zone in zones:
        if _line_intersects_polygon(coordinates, zone.polygon):
            hits.append((zone, zone_decision(profile, zone)))

    blocked = any(decision == "blocked" for _, decision in hits)
    highest = max((zone.severity for zone, _ in hits), key=lambda severity: SEVERITY_ORDER[severity], default="none")
    cautious = any(decision == "cautious" for _, decision in hits)
    exposure_score = 0
    if highest == "low":
        exposure_score = 5
    if cautious:
        exposure_score = 60 if profile == "walk" and highest == "high" else 20 if profile == "walk" else 15
    if blocked:
        exposure_score = 100
    distance = sum(_intersected_distance(coordinates, zone.polygon) for zone, _ in hits)
    evaluated = dict(route)
    evaluated.update({
        "blocked": blocked,
        "avoided_floods": bool(hits) is False,
        "safety_score": float(max(0, 100 - exposure_score)),
        "flood_risk": highest,
        "flood_exposure": {
            "highest_severity": highest,
            "zone_count": len(hits),
            "intersected_distance_m": round(distance, 1),
            "exposure_score": exposure_score,
            "message": "No active flood-zone exposure." if not hits else f"Intersects {len(hits)} active flood zone{'s' if len(hits) != 1 else ''} ({highest}).",
        },
    })
    return evaluated


def _overlaps(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_points = {tuple(round(value, 4) for value in point) for point in left["geometry"]["coordinates"]}
    right_points = {tuple(round(value, 4) for value in point) for point in right["geometry"]["coordinates"]}
    smaller = min(len(left_points), len(right_points))
    return smaller > 0 and len(left_points.intersection(right_points)) / smaller >= 0.85


def rank_routes(candidates: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Return up to four distinct, navigable cards and one optional blocked baseline."""
    unique: list[dict[str, Any]] = []
    for candidate in candidates:
        if not any(_overlaps(candidate, existing) for existing in unique):
            unique.append(candidate)
    eligible = [candidate for candidate in unique if not candidate["blocked"]]
    # Explain a rejected baseline only if it really was the fastest unfiltered
    # choice.  A slower blocked route is not useful to present to the traveller.
    raw_fastest = min(unique, key=lambda candidate: candidate["duration"], default=None)
    baseline = raw_fastest if raw_fastest and raw_fastest["blocked"] else None
    if not eligible:
        return [], baseline

    fastest = min(eligible, key=lambda candidate: candidate["duration"])
    safest = min(eligible, key=lambda candidate: (candidate["flood_exposure"]["exposure_score"], candidate["duration"]))
    dry = [candidate for candidate in eligible if candidate["flood_exposure"]["exposure_score"] == 0]
    balanced = min(dry, key=lambda candidate: candidate["duration"]) if dry and min(dry, key=lambda candidate: candidate["duration"])["duration"] <= fastest["duration"] * 1.2 else safest

    ranked: list[tuple[str, dict[str, Any]]] = []
    for category, candidate in (("fastest", fastest), ("safest", safest), ("balanced", balanced)):
        if all(candidate is not selected for _, selected in ranked):
            ranked.append((category, candidate))
    for candidate in sorted(eligible, key=lambda item: (item["flood_exposure"]["exposure_score"], item["duration"])):
        if all(candidate is not selected for _, selected in ranked):
            ranked.append(("alternative", candidate))
            break
    labels = {"fastest": "Fastest", "safest": "Safest", "balanced": "Balanced", "alternative": "Alternative"}
    routes: list[dict[str, Any]] = []
    for index, (category, candidate) in enumerate(ranked[:4]):
        candidate = dict(candidate)
        candidate.update({"index": index, "category": category, "label": labels[category]})
        routes.append(candidate)
    return routes, baseline
