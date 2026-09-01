import json
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
import httpx
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app import models
from app.models.report import ReportSeverity
from app.core.config import settings

ROUTE_LABELS = ["Recommended", "Alternative 1", "Alternative 2"]

def decode_polyline6(encoded_str: str) -> List[List[float]]:
    """Decodes Valhalla's 6-digit precision polyline string into GeoJSON [lng, lat] coordinates."""
    index = 0
    lat = 0
    lng = 0
    coordinates = []
    length = len(encoded_str)
    
    while index < length:
        shift = 0
        result = 0
        while True:
            b = ord(encoded_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        shift = 0
        result = 0
        while True:
            b = ord(encoded_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        coordinates.append([lng / 1000000.0, lat / 1000000.0])
        
    return coordinates

def get_active_flood_polygons(db: Session) -> Tuple[List[List[List[float]]], List[List[List[float]]], List[List[List[float]]]]:
    """
    Fetches active flood avoidance zones and groups them by severity.
    Returns lists of Valhalla-compatible polygons (exterior rings).
    """
    zones = db.query(
        func.ST_AsGeoJSON(models.FloodAvoidanceZone.geometry).label("geojson"),
        models.FloodReport.severity
    ).join(
        models.FloodReport, models.FloodAvoidanceZone.report_id == models.FloodReport.id
    ).filter(
        models.FloodAvoidanceZone.is_active == True,
        (models.FloodAvoidanceZone.expires_at == None) | (models.FloodAvoidanceZone.expires_at > func.now())
    ).all()
    
    red_polygons = []
    orange_polygons = []
    yellow_polygons = []
    
    for z in zones:
        geom = json.loads(z.geojson)
        if geom["type"] == "Polygon" and len(geom["coordinates"]) > 0:
            exterior_ring = geom["coordinates"][0] # Valhalla expects an array of points for each polygon
            if z.severity == ReportSeverity.LOW:
                # White/Low is passable. No detour required.
                continue
            elif z.severity == ReportSeverity.EXTREME:
                red_polygons.append(exterior_ring)
            elif z.severity == ReportSeverity.HIGH:
                orange_polygons.append(exterior_ring)
            elif z.severity == ReportSeverity.MEDIUM:
                yellow_polygons.append(exterior_ring)
                
    return red_polygons, orange_polygons, yellow_polygons

def request_valhalla_route(start: List[float], end: List[float], avoid_polygons: Optional[List[List[List[float]]]] = None, vehicle_profile: str = "light", heading: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Queries the Valhalla server for routes between start and end coordinates, optionally avoiding polygons."""
    
    # Map our vehicle profiles to Valhalla's native costing models
    costing = "auto"
    if vehicle_profile == "motorcycle":
        costing = "motorcycle"
    elif vehicle_profile == "walk":
        costing = "pedestrian"
        
    start_loc = {"lat": start[1], "lon": start[0]}
    end_loc = {"lat": end[1], "lon": end[0]}
    
    if heading is not None:
        start_loc["heading"] = heading
        end_loc["heading"] = heading
        
    body: Dict[str, Any] = {
        "locations": [start_loc, end_loc],
        "costing": costing,
        "alternates": 2,
        "units": "kilometers"
    }
    
    if avoid_polygons and len(avoid_polygons) > 0:
        body["avoid_polygons"] = avoid_polygons
        
    url = f"{settings.VALHALLA_URL}/route"
    
    try:
        response = httpx.post(url, json=body, timeout=10.0)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400 and "avoid_polygons" in response.text:
             # If Valhalla rejects the route because it cannot avoid the polygons
             return None
        else:
            # For logging/debugging unhandled errors
            print(f"Valhalla Error: {response.text}")
            return None
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to communicate with Valhalla routing server: {exc}"
        )

def process_valhalla_response(
    data: Dict[str, Any], 
    avoided_floods: bool = False, 
    blocked: bool = False,
    safety_score: float = 100.0,
    flood_risk: str = "none"
) -> List[Dict[str, Any]]:
    """Converts a Valhalla route response into our MultiRouteResponse candidate list."""
    if not data or "trip" not in data:
        return []
        
    candidates = []
    
    def extract_route(trip_data: Dict[str, Any], idx: int):
        if "legs" not in trip_data or len(trip_data["legs"]) == 0:
            return None
            
        leg = trip_data["legs"][0]
        summary = trip_data.get("summary", {})
        
        # Length is in km, convert to meters
        distance_m = summary.get("length", 0.0) * 1000
        duration_s = summary.get("time", 0.0)
        
        shape_str = leg.get("shape", "")
        coords = decode_polyline6(shape_str) if shape_str else []
        
        label = ROUTE_LABELS[idx] if idx < len(ROUTE_LABELS) else f"Alternative {idx}"
        
        return {
            "index": idx,
            "label": label,
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            },
            "distance": distance_m,
            "duration": duration_s,
            "avoided_floods": avoided_floods,
            "blocked": blocked,
            "is_truncated": False, # Valhalla generates native alternates, so we don't need distance heuristics
            "safety_score": safety_score,
            "flood_risk": flood_risk
        }
        
    primary = extract_route(data["trip"], 0)
    if primary:
        candidates.append(primary)
        
    alternates = data.get("alternates", [])
    for i, alt in enumerate(alternates):
        alt_route = extract_route(alt.get("trip", {}), i + 1)
        if alt_route:
            candidates.append(alt_route)
            
    return candidates

def calculate_flood_safe_route(
    db: Session,
    start: List[float],
    end: List[float],
    ignore_floods: bool = False,
    vehicle_profile: str = "light",
    heading: Optional[int] = None
) -> Dict[str, Any]:
    """Queries Valhalla to find a route, intelligently falling back on flood avoidance rules based on vehicle profile."""
    
    # 1. Fast path: completely ignore all floods
    if ignore_floods:
        data = request_valhalla_route(start, end, vehicle_profile=vehicle_profile, heading=heading)
        if not data:
            raise HTTPException(status_code=404, detail="No route options found by the pathfinding engine.")
        candidates = process_valhalla_response(data, avoided_floods=False, blocked=False, safety_score=100.0, flood_risk="none")
        return {
            "routes": candidates,
            "recommended_index": 0
        }
        
    # 2. Get active flood polygons
    try:
        red, orange, yellow = get_active_flood_polygons(db)
    except Exception as e:
        print(f"Warning: Failed to fetch flood polygons ({e}). Bypassing flood avoidance.")
        red, orange, yellow = [], [], []

    # 3. Vehicle Profile Matrix Definitions
    blocked = []
    penalized = []
    risk_map = {}

    if vehicle_profile == "walk":
        blocked = red + orange
        penalized = yellow
        risk_map = {"yellow": ("medium", 80.0)}
    elif vehicle_profile in ["motorcycle", "light"]:
        blocked = red + orange + yellow
        penalized = []
        risk_map = {}
    elif vehicle_profile == "heavy":
        blocked = red
        penalized = orange + yellow
        risk_map = {"orange": ("high", 35.0), "yellow": ("medium", 85.0)}
    else:
        # Fallback default (treat as light)
        blocked = red + orange + yellow
        penalized = []
        risk_map = {}

    all_to_avoid = blocked + penalized

    # 4. Helper function to inject the direct route if it differs from the safe detour
    def build_response(safe_data: Dict[str, Any], is_blocked: bool, detour_label: str, safety_score: float, flood_risk: str, direct_primary: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        safe_candidates = process_valhalla_response(
            safe_data, avoided_floods=True, blocked=is_blocked, 
            safety_score=safety_score, flood_risk=flood_risk
        )
        if not safe_candidates:
            return None
            
        final_candidates = []
        
        # If the direct route is blocked (0% safe), we don't even want to show it.
        if direct_primary and direct_primary.get("blocked", False):
            direct_primary = None
            
        # If we have a direct_primary that is physically different from the safest route
        if direct_primary and abs(direct_primary["distance"] - safe_candidates[0]["distance"]) > 10:
            final_candidates.append(direct_primary)
            for sc in safe_candidates:
                sc["index"] = len(final_candidates)
                if sc["index"] == 1:
                    sc["label"] = detour_label
                elif sc["index"] == 2:
                    sc["label"] = "Alternative 1"
                else:
                    sc["label"] = f"Alternative {sc['index'] - 1}"
                final_candidates.append(sc)
        else:
            final_candidates = safe_candidates
            for i, sc in enumerate(final_candidates):
                sc["index"] = i
                if i == 0:
                    sc["label"] = "Recommended"
                elif i == 1:
                    sc["label"] = "Alternative 1"
                else:
                    sc["label"] = f"Alternative {i}"
            
        return {"routes": final_candidates, "recommended_index": 0 if not direct_primary else 1}

    # 5. Determine the Direct Route (Baseline Comparison)
    # We always avoid Red (unless we want to show it, but Red is impassable for all).
    # To accurately show the direct route they would take if they didn't detour, we ask Valhalla to avoid ONLY Red.
    direct_primary = None
    if orange or yellow:
        data_direct = request_valhalla_route(start, end, avoid_polygons=red, vehicle_profile=vehicle_profile, heading=heading)
        if data_direct:
            # Did this direct route pass through Blocked or Penalized zones?
            # We assume if Orange/Yellow exist, it hit the worst available.
            hits_orange = len(orange) > 0
            hits_yellow = len(yellow) > 0
            
            is_direct_blocked = False
            worst_direct_safety = 100.0
            worst_direct_risk = "none"

            if vehicle_profile == "walk":
                if hits_orange: is_direct_blocked = True
                elif hits_yellow: 
                    worst_direct_safety = risk_map["yellow"][1]
                    worst_direct_risk = risk_map["yellow"][0]
            elif vehicle_profile in ["motorcycle", "light"]:
                if hits_orange or hits_yellow: is_direct_blocked = True
            elif vehicle_profile == "heavy":
                if hits_orange:
                    worst_direct_safety = risk_map["orange"][1]
                    worst_direct_risk = risk_map["orange"][0]
                elif hits_yellow:
                    worst_direct_safety = risk_map["yellow"][1]
                    worst_direct_risk = risk_map["yellow"][0]
            
            if is_direct_blocked:
                worst_direct_safety = 0.0
                worst_direct_risk = "extreme"

            direct_candidates = process_valhalla_response(
                data_direct, avoided_floods=(len(red) > 0), blocked=is_direct_blocked, 
                safety_score=worst_direct_safety, flood_risk=worst_direct_risk
            )
            if direct_candidates:
                direct_primary = direct_candidates[0]
                direct_primary["label"] = "Direct (Flooded)"
                direct_primary["index"] = 0

    # 6. Attempt 1: Avoid EVERYTHING (Blocked + Penalized)
    # This gives a 100% safe route if available.
    data = request_valhalla_route(start, end, avoid_polygons=all_to_avoid, vehicle_profile=vehicle_profile, heading=heading)
    if data:
        res = build_response(data, is_blocked=False, detour_label="Safe Detour", safety_score=100.0, flood_risk="none", direct_primary=direct_primary)
        if res: return res

    # 7. Attempt 2: Avoid only BLOCKED (traverse Penalized)
    if penalized:
        data = request_valhalla_route(start, end, avoid_polygons=blocked, vehicle_profile=vehicle_profile, heading=heading)
        if data:
            # We traversed penalized. Assume worst penalized.
            worst_safety = 100.0
            worst_risk = "none"
            if vehicle_profile == "heavy":
                if len(orange) > 0:
                    worst_safety = risk_map["orange"][1]
                    worst_risk = risk_map["orange"][0]
                elif len(yellow) > 0:
                    worst_safety = risk_map["yellow"][1]
                    worst_risk = risk_map["yellow"][0]
            elif vehicle_profile == "walk":
                if len(yellow) > 0:
                    worst_safety = risk_map["yellow"][1]
                    worst_risk = risk_map["yellow"][0]

            res = build_response(data, is_blocked=True, detour_label="Best Detour", safety_score=worst_safety, flood_risk=worst_risk, direct_primary=direct_primary)
            if res: return res

    # 8. Attempt 3: Trapped!
    # If we reach this point, it means no safe detours exist. 
    # Since we explicitly discard 0% safe direct routes, we have no valid routes to show.
    return {"routes": [], "recommended_index": -1}


def _shift_coords_perpendicular(coords: List[List[float]], offset_meters: float) -> List[List[float]]:
    """
    Shifts a list of [lng, lat] coordinates by `offset_meters` in the perpendicular
    (left-hand side) direction relative to the line's travel direction.
    Positive offset = left of travel direction (oncoming traffic lane in right-hand traffic).
    Uses a simple flat-earth approximation which is accurate enough for short road segments.
    """
    if len(coords) < 2:
        return coords

    shifted = []
    for i, pt in enumerate(coords):
        # Use neighboring points to compute bearing at each vertex
        if i == 0:
            p1, p2 = coords[0], coords[1]
        elif i == len(coords) - 1:
            p1, p2 = coords[-2], coords[-1]
        else:
            p1, p2 = coords[i - 1], coords[i + 1]

        # Bearing of the segment (in radians)
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        bearing = math.atan2(dx, dy)

        # Perpendicular to the left is bearing - 90 degrees
        perp_bearing = bearing - math.pi / 2

        # Convert offset_meters to degrees (approx: 1 degree ≈ 111,000m)
        # Latitude offset is straightforward; longitude is scaled by cos(lat)
        lat_rad = math.radians(pt[1])
        delta_lat = (offset_meters / 111000.0) * math.cos(perp_bearing)
        delta_lng = (offset_meters / (111000.0 * math.cos(lat_rad))) * math.sin(perp_bearing)

        shifted.append([pt[0] + delta_lng, pt[1] + delta_lat])

    return shifted


def find_opposite_carriageway(
    route_coords: List[List[float]],
    original_road_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Hybrid Strategy: Given the [lng, lat] coordinates of a road segment, attempts to
    find and return the geometry of the parallel, opposite-direction carriageway.

    Algorithm:
    1. Shifts all coordinates ~15m to the left (perpendicular hint away from original road).
    2. Reverses the order (so map-matching sees the opposite travel direction).
    3. Calls Valhalla /trace_attributes to snap to the nearest matching road.
    4. Validates the matched road name against `original_road_name` to avoid false positives.
    5. Returns a GeoJSON LineString of the opposite carriageway, or None if not found.
    """
    if not route_coords or len(route_coords) < 2:
        return None

    # Step 1: Apply 15m perpendicular left-hand offset as a "hint"
    shifted = _shift_coords_perpendicular(route_coords, offset_meters=15.0)

    # Step 2: Reverse the coordinate order so map-matching sees the opposite direction
    reversed_shifted = list(reversed(shifted))

    # Step 3: Call Valhalla /trace_attributes (Map Matching — no U-turns, pure shape snap)
    shape = [{"lat": c[1], "lon": c[0]} for c in reversed_shifted]
    body = {
        "shape": shape,
        "costing": "auto",
        "shape_match": "map_snap",
        "filters": {
            "attributes": ["edge.names", "edge.length", "shape"],
            "action": "include"
        }
    }

    url = f"{settings.VALHALLA_URL}/trace_attributes"
    try:
        response = httpx.post(url, json=body, timeout=10.0)
        if response.status_code != 200:
            logger.warning(f"[find_opposite_carriageway] Valhalla trace_attributes failed: {response.text}")
            return None

        data = response.json()
    except httpx.RequestError as e:
        logger.warning(f"[find_opposite_carriageway] Valhalla unreachable: {e}")
        return None

    # Step 4: Validate — check that matched road has the same name as the original
    matched_edges = data.get("edges", [])
    matched_names = set()
    for edge in matched_edges:
        for name in edge.get("names", []):
            matched_names.add(name.strip().lower())

    if original_road_name:
        original_normalized = original_road_name.strip().lower()
        # Allow if any matched edge shares the same name
        name_match = any(
            original_normalized in n or n in original_normalized
            for n in matched_names
        )
        # If the road has a name AND the matched road has a completely different name, reject it
        if matched_names and not name_match:
            logger.info(
                f"[find_opposite_carriageway] Name mismatch. Original: '{original_road_name}', "
                f"Matched: {matched_names}. Likely a different road — aborting."
            )
            return None

    # Step 5: Decode the matched shape from the response
    matched_shape_str = data.get("shape")
    if not matched_shape_str:
        return None

    # The matched shape is returned reversed (we fed in a reversed trace), so re-reverse it
    matched_coords = decode_polyline6(matched_shape_str)
    # Re-reverse so the geometry flows in the same spatial direction as the original line
    matched_coords = list(reversed(matched_coords))

    if len(matched_coords) < 2:
        return None

    logger.info(
        f"[find_opposite_carriageway] Successfully matched opposite carriageway "
        f"with {len(matched_coords)} points. Road names: {matched_names}"
    )

    return {
        "type": "LineString",
        "coordinates": matched_coords
    }

