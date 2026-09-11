"""Authoritative road-segment and opposite-carriageway detection.

Decision #16 uses the routing graph as the source of truth. Geometric offsets
are only search hints and are never returned without graph validation.
"""

from __future__ import annotations

import logging
import math
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

Coordinate = List[float]
LineCoordinates = List[Coordinate]

SEARCH_OFFSETS_METERS = (5.0, 10.0, 15.0, 20.0, 30.0)
MIN_LATERAL_SEPARATION_METERS = 4.0
MAX_LATERAL_SEPARATION_METERS = 35.0
MAX_PARALLEL_ANGLE_DEGREES = 30.0
MIN_LENGTH_RATIO = 0.70
MAX_LENGTH_RATIO = 1.30
MIN_LONGITUDINAL_OVERLAP = 0.70


def decode_polyline6(encoded_str: str) -> LineCoordinates:
    """Decode a Valhalla precision-6 polyline to GeoJSON ``[lng, lat]``."""
    index = lat = lng = 0
    coordinates: LineCoordinates = []
    while index < len(encoded_str):
        deltas: List[int] = []
        for _ in range(2):
            shift = result = 0
            while True:
                value = ord(encoded_str[index]) - 63
                index += 1
                result |= (value & 0x1F) << shift
                shift += 5
                if value < 0x20:
                    break
            deltas.append(~(result >> 1) if result & 1 else result >> 1)
        lat += deltas[0]
        lng += deltas[1]
        coordinates.append([lng / 1_000_000.0, lat / 1_000_000.0])
    return coordinates


def _distance_meters(first: Coordinate, second: Coordinate) -> float:
    mean_latitude = math.radians((first[1] + second[1]) / 2.0)
    dx = (second[0] - first[0]) * 111_000.0 * math.cos(mean_latitude)
    dy = (second[1] - first[1]) * 111_000.0
    return math.hypot(dx, dy)


def _line_length_meters(coords: LineCoordinates) -> float:
    return sum(_distance_meters(coords[index - 1], coords[index]) for index in range(1, len(coords)))


def _connect_route_to_anchors(
    coords: LineCoordinates,
    start: Coordinate,
    end: Coordinate,
) -> LineCoordinates:
    """Keep the routed shape while making its visible coverage meet both pins."""
    connected = [list(coordinate) for coordinate in coords]
    if _distance_meters(connected[0], start) > 0.5:
        connected.insert(0, list(start))
    else:
        connected[0] = list(start)
    if _distance_meters(connected[-1], end) > 0.5:
        connected.append(list(end))
    else:
        connected[-1] = list(end)
    return connected


def _bearing_degrees(coords: LineCoordinates) -> float:
    if len(coords) < 2:
        return 0.0
    start, end = coords[0], coords[-1]
    mean_latitude = math.radians((start[1] + end[1]) / 2.0)
    dx = (end[0] - start[0]) * math.cos(mean_latitude)
    dy = end[1] - start[1]
    return (math.degrees(math.atan2(dx, dy)) + 360.0) % 360.0


def _angle_difference(first: float, second: float) -> float:
    return abs((first - second + 180.0) % 360.0 - 180.0)


def _normalize_name(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    aliases = {"avenue": "ave", "street": "st", "road": "rd", "boulevard": "blvd"}
    return " ".join(aliases.get(token, token) for token in value.split())


def _edge_names(edges: Iterable[Dict[str, Any]]) -> set[str]:
    return {
        normalized
        for edge in edges
        for name in edge.get("names", []) or []
        if (normalized := _normalize_name(str(name)))
    }


def _edge_way_ids(edges: Iterable[Dict[str, Any]]) -> set[int]:
    return {int(edge["way_id"]) for edge in edges if edge.get("way_id") is not None}


def _dominant_value(edges: Iterable[Dict[str, Any]], key: str) -> Tuple[Optional[str], float]:
    weights: Dict[str, float] = defaultdict(float)
    total = 0.0
    for edge in edges:
        value = edge.get(key)
        if value is None:
            continue
        weight = float(edge.get("length") or 0.001)
        weights[str(value)] += weight
        total += weight
    if not weights or total <= 0:
        return None, 0.0
    value, weight = max(weights.items(), key=lambda item: item[1])
    return value, weight / total


def _shift_coords_perpendicular(coords: LineCoordinates, offset_meters: float) -> LineCoordinates:
    """Shift a line left (positive) or right (negative) as a map-match hint."""
    if len(coords) < 2:
        return coords
    shifted: LineCoordinates = []
    for index, point in enumerate(coords):
        if index == 0:
            first, second = coords[0], coords[1]
        elif index == len(coords) - 1:
            first, second = coords[-2], coords[-1]
        else:
            first, second = coords[index - 1], coords[index + 1]
        bearing = math.atan2(second[0] - first[0], second[1] - first[1])
        perpendicular = bearing - math.pi / 2.0
        latitude_radians = math.radians(point[1])
        delta_latitude = (offset_meters / 111_000.0) * math.cos(perpendicular)
        delta_longitude = (offset_meters / (111_000.0 * math.cos(latitude_radians))) * math.sin(perpendicular)
        shifted.append([point[0] + delta_longitude, point[1] + delta_latitude])
    return shifted


def trace_road_attributes(shape_coords: LineCoordinates) -> Optional[Dict[str, Any]]:
    """Map-match a shape and return the OSM edge evidence used for validation."""
    if len(shape_coords) < 2:
        return None
    body = {
        "shape": [{"lat": coordinate[1], "lon": coordinate[0]} for coordinate in shape_coords],
        "costing": "auto",
        "shape_match": "map_snap",
        "filters": {
            "attributes": [
                "edge.names", "edge.traversability", "edge.road_class",
                "edge.way_id", "edge.length", "shape",
            ],
            "action": "include",
        },
    }
    try:
        response = httpx.post(f"{settings.VALHALLA_URL}/trace_attributes", json=body, timeout=10.0)
        if response.status_code == 200:
            return response.json()
        logger.warning("Valhalla trace failed with status %s", response.status_code)
    except (httpx.HTTPError, ValueError):
        logger.warning("Valhalla trace request failed", exc_info=True)
    return None


def _request_route_geometry(start: Coordinate, end: Coordinate) -> Optional[LineCoordinates]:
    body = {
        "locations": [{"lat": start[1], "lon": start[0]}, {"lat": end[1], "lon": end[0]}],
        "costing": "auto",
        "alternates": 0,
        "directions_options": {"units": "kilometers"},
    }
    try:
        response = httpx.post(f"{settings.VALHALLA_URL}/route", json=body, timeout=10.0)
        if response.status_code != 200:
            return None
        shape = response.json().get("trip", {}).get("legs", [{}])[0].get("shape")
        return decode_polyline6(shape) if shape else None
    except (httpx.HTTPError, IndexError, KeyError, TypeError, ValueError):
        logger.warning("Valhalla route request failed", exc_info=True)
        return None


def _point_to_segment_distance(point: Coordinate, start: Coordinate, end: Coordinate) -> float:
    mean_latitude = math.radians((start[1] + end[1] + point[1]) / 3.0)
    scale_x = 111_000.0 * math.cos(mean_latitude)
    px, py = (point[0] - start[0]) * scale_x, (point[1] - start[1]) * 111_000.0
    ex, ey = (end[0] - start[0]) * scale_x, (end[1] - start[1]) * 111_000.0
    denominator = ex * ex + ey * ey
    if denominator == 0:
        return math.hypot(px, py)
    position = max(0.0, min(1.0, (px * ex + py * ey) / denominator))
    return math.hypot(px - position * ex, py - position * ey)


def _lateral_separation(original: LineCoordinates, candidate: LineCoordinates) -> float:
    samples = (candidate[0], candidate[len(candidate) // 2], candidate[-1])
    distances = [
        min(_point_to_segment_distance(point, original[i - 1], original[i]) for i in range(1, len(original)))
        for point in samples
    ]
    return sum(distances) / len(distances)


def _longitudinal_overlap(original: LineCoordinates, candidate: LineCoordinates) -> float:
    start, end = original[0], original[-1]
    mean_latitude = math.radians((start[1] + end[1]) / 2.0)
    scale_x = 111_000.0 * math.cos(mean_latitude)
    vx, vy = (end[0] - start[0]) * scale_x, (end[1] - start[1]) * 111_000.0
    denominator = vx * vx + vy * vy
    if denominator == 0:
        return 0.0

    def projection(point: Coordinate) -> float:
        px, py = (point[0] - start[0]) * scale_x, (point[1] - start[1]) * 111_000.0
        return (px * vx + py * vy) / denominator

    low, high = sorted((projection(candidate[0]), projection(candidate[-1])))
    return max(0.0, min(1.0, high) - max(0.0, low))


def _candidate_is_valid(
    original: LineCoordinates,
    original_edges: List[Dict[str, Any]],
    candidate_reversed: LineCoordinates,
    candidate_edges: List[Dict[str, Any]],
) -> bool:
    original_names = _edge_names(original_edges)
    candidate_names = _edge_names(candidate_edges)
    if not original_names or not candidate_names or original_names.isdisjoint(candidate_names):
        return False
    original_class, _ = _dominant_value(original_edges, "road_class")
    candidate_class, _ = _dominant_value(candidate_edges, "road_class")
    if original_class and candidate_class and original_class != candidate_class:
        return False
    original_way_ids = _edge_way_ids(original_edges)
    candidate_way_ids = _edge_way_ids(candidate_edges)
    if not original_way_ids or not candidate_way_ids or not original_way_ids.isdisjoint(candidate_way_ids):
        return False

    original_length = _line_length_meters(original)
    candidate_length = _line_length_meters(candidate_reversed)
    if original_length <= 0 or not MIN_LENGTH_RATIO <= candidate_length / original_length <= MAX_LENGTH_RATIO:
        return False
    expected_reverse_bearing = (_bearing_degrees(original) + 180.0) % 360.0
    if _angle_difference(_bearing_degrees(candidate_reversed), expected_reverse_bearing) > MAX_PARALLEL_ANGLE_DEGREES:
        return False

    display_candidate = list(reversed(candidate_reversed))
    separation = _lateral_separation(original, display_candidate)
    if not MIN_LATERAL_SEPARATION_METERS <= separation <= MAX_LATERAL_SEPARATION_METERS:
        return False
    if _longitudinal_overlap(original, display_candidate) < MIN_LONGITUDINAL_OVERLAP:
        return False
    chord = _distance_meters(candidate_reversed[0], candidate_reversed[-1])
    return chord > 0 and candidate_length / chord <= 1.8


def find_opposite_carriageway(
    route_coords: LineCoordinates,
    original_road_name: Optional[str] = None,
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Classify a routed segment and return only a graph-validated counterpart."""
    if len(route_coords) < 2:
        return "UNMAPPED", None
    original_trace = trace_road_attributes(route_coords)
    if not original_trace or not original_trace.get("edges"):
        return "UNMAPPED", None
    original_edges = list(original_trace["edges"])
    if original_road_name:
        original_edges.append({"names": [original_road_name], "length": 0.001})
    traversability, confidence = _dominant_value(original_edges, "traversability")
    if confidence < 0.70 or traversability not in {"both", "forward", "backward"}:
        return "AMBIGUOUS", None
    if traversability == "both":
        return "NARROW_TWO_WAY", None

    probe_responded = False
    for offset in SEARCH_OFFSETS_METERS:
        for signed_offset in (offset, -offset):
            shifted_reversed = list(reversed(_shift_coords_perpendicular(route_coords, signed_offset)))
            opposite_trace = trace_road_attributes(shifted_reversed)
            probe_responded = probe_responded or opposite_trace is not None
            if not opposite_trace or not opposite_trace.get("edges") or not opposite_trace.get("shape"):
                continue
            try:
                matched_reversed = decode_polyline6(opposite_trace["shape"])
            except (IndexError, TypeError, ValueError):
                logger.warning("Valhalla returned an invalid opposite-carriageway shape", exc_info=True)
                continue
            if len(matched_reversed) >= 2 and _candidate_is_valid(
                route_coords, original_edges, matched_reversed, list(opposite_trace["edges"])
            ):
                return "DIVIDED_CARRIAGEWAY", {
                    "type": "LineString",
                    "coordinates": list(reversed(matched_reversed)),
                }
    return ("TRUE_ONE_WAY" if probe_responded else "UNMAPPED"), None


def build_road_segment_preview(
    start: Coordinate,
    end: Coordinate,
    is_bidirectional: bool = True,
    road_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the conservative authoritative preview used by every road workflow."""
    fallback = [list(start), list(end)]
    direct_distance = _distance_meters(start, end)
    if direct_distance <= 1.0:
        return _preview_result(fallback, None, "UNMAPPED", "unmapped", "Choose two different points on the road.")

    # Both directions are independent. Running them together avoids making the
    # user wait for two sequential Valhalla round trips.
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="road-preview") as executor:
        forward_future = executor.submit(_request_route_geometry, start, end)
        reverse_future = executor.submit(_request_route_geometry, end, start)
        forward = forward_future.result()
        reverse = reverse_future.result()
    candidates = [candidate for candidate in (forward, list(reversed(reverse)) if reverse else None) if candidate]
    max_route_length = max(direct_distance * 1.8, direct_distance + 100.0)
    valid_routes = [
        candidate
        for candidate in candidates
        if _line_length_meters(candidate) <= max_route_length
        and _distance_meters(candidate[0], start) <= MAX_LATERAL_SEPARATION_METERS
        and _distance_meters(candidate[-1], end) <= MAX_LATERAL_SEPARATION_METERS
    ]
    if not valid_routes:
        return _preview_result(
            fallback, None, "AMBIGUOUS", "fallback",
            "The routing graph could not verify one continuous road segment. Only the selected line will be used.",
        )

    selected_route = min(
        valid_routes,
        key=lambda candidate: (
            _distance_meters(candidate[0], start) + _distance_meters(candidate[-1], end),
            _line_length_meters(candidate),
        ),
    )
    # Topology is classified from the snapped road only; raw anchor connectors
    # may touch a junction and must not pollute carriageway edge evidence.
    road_type, opposite = find_opposite_carriageway(selected_route, road_name) if is_bidirectional else ("SINGLE_DIRECTION", None)
    original = _connect_route_to_anchors(selected_route, start, end)
    messages = {
        "NARROW_TWO_WAY": "This two-way street uses one mapped centerline; that line covers both directions.",
        "DIVIDED_CARRIAGEWAY": "Both mapped carriageways were verified.",
        "TRUE_ONE_WAY": "No distinct opposite carriageway was verified; only the selected road will be used.",
        "AMBIGUOUS": "The road structure is ambiguous; no opposite line was added.",
        "UNMAPPED": "Road verification is unavailable; no opposite line was added.",
        "SINGLE_DIRECTION": "The selected road segment is ready.",
    }
    status = "validated" if road_type in {
        "NARROW_TWO_WAY", "DIVIDED_CARRIAGEWAY", "TRUE_ONE_WAY", "SINGLE_DIRECTION"
    } else road_type.lower()
    return _preview_result(original, opposite, road_type, status, messages[road_type])


def _preview_result(
    original_coords: LineCoordinates,
    opposite: Optional[Dict[str, Any]],
    road_type: str,
    validation_status: str,
    message: str,
) -> Dict[str, Any]:
    original = {"type": "LineString", "coordinates": original_coords}
    coverage: Dict[str, Any] = original
    if opposite:
        coverage = {"type": "MultiLineString", "coordinates": [original_coords, opposite["coordinates"]]}
    return {
        "original": original,
        "opposite": opposite,
        "coverage_geometry": coverage,
        "is_divided": opposite is not None,
        "road_type": road_type,
        "validation_status": validation_status,
        "message": message,
    }
