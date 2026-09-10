import logging
import math
from typing import Any, Dict, List, Optional, Tuple
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


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


def _shift_coords_perpendicular(coords: List[List[float]], offset_meters: float) -> List[List[float]]:
    """
    Shifts a list of [lng, lat] coordinates by `offset_meters` in the perpendicular
    (left-hand side) direction relative to the line's travel direction.
    Positive offset = left of travel direction (oncoming traffic lane in right-hand traffic).
    Uses a flat-earth approximation accurate for local urban road segments.
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
        lat_rad = math.radians(pt[1])
        delta_lat = (offset_meters / 111000.0) * math.cos(perp_bearing)
        delta_lng = (offset_meters / (111000.0 * math.cos(lat_rad))) * math.sin(perp_bearing)

        shifted.append([pt[0] + delta_lng, pt[1] + delta_lat])

    return shifted


def trace_road_attributes(shape_coords: List[List[float]]) -> Optional[Dict[str, Any]]:
    """
    Calls Valhalla /trace_attributes with map_snap costing=auto to extract
    underlying OSM edge names, traversability, road_class, and osm way_id.
    """
    if not shape_coords or len(shape_coords) < 2:
        return None

    shape = [{"lat": c[1], "lon": c[0]} for c in shape_coords]
    url = f"{settings.VALHALLA_URL}/trace_attributes"
    body = {
        "shape": shape,
        "costing": "auto",
        "shape_match": "map_snap",
        "filters": {
            "attributes": ["edge.names", "edge.traversability", "edge.road_class", "edge.way_id", "shape"],
            "action": "include"
        }
    }
    try:
        res = httpx.post(url, json=body, timeout=10.0)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        logger.warning(f"[trace_road_attributes] Trace error: {e}")
    return None


def find_opposite_carriageway(
    route_coords: List[List[float]],
    original_road_name: Optional[str] = None
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Decision #16: Traversability-Aware Hybrid Strategy.
    Returns a tuple of (road_type_enum, opposite_geometry).
    road_type_enum can be: "NARROW_TWO_WAY", "DIVIDED_CARRIAGEWAY", "TRUE_ONE_WAY", "UNMAPPED".
    """
    if not route_coords or len(route_coords) < 2:
        return "UNMAPPED", None

    # Step 1: Trace original road to determine traversability
    orig_trace = trace_road_attributes(route_coords)
    if not orig_trace or not orig_trace.get("edges"):
        return "UNMAPPED", None

    edges = orig_trace.get("edges", [])
    
    # Extract original names from trace
    original_names = set()
    if original_road_name:
        original_names.add(original_road_name.strip().lower())
        
    for e in edges:
        for n in e.get("names", []):
            if n.strip():
                original_names.add(n.strip().lower())
    
    # Determine majority traversability
    trav_counts = {"both": 0, "forward": 0, "backward": 0}
    for e in edges:
        t = e.get("traversability")
        if t in trav_counts:
            trav_counts[t] += 1
            
    # Default to forward if unknown
    majority_trav = max(trav_counts, key=trav_counts.get) if any(trav_counts.values()) else "forward"

    # Step 2: The Decision Tree
    if majority_trav == "both":
        logger.info("[find_opposite_carriageway] Classified as NARROW_TWO_WAY")
        return "NARROW_TWO_WAY", None

    # Step 3: Dynamic Offset Search for one-way/divided candidates
    logger.info("[find_opposite_carriageway] Classified as ONE_WAY_CANDIDATE, starting Dynamic Offset Search")
    
    offsets = [5.0, 10.0, 15.0, 20.0, 30.0]
    
    for offset in offsets:
        shifted = _shift_coords_perpendicular(route_coords, offset_meters=offset)
        reversed_shifted = list(reversed(shifted))
        
        opp_trace = trace_road_attributes(reversed_shifted)
        if not opp_trace:
            continue
            
        matched_edges = opp_trace.get("edges", [])
        matched_names = set()
        for edge in matched_edges:
            for name in edge.get("names", []):
                matched_names.add(name.strip().lower())
                
        # Step 4: Validate name matches
        if original_names:
            name_match = False
            for orig_name in original_names:
                for match_name in matched_names:
                    if orig_name in match_name or match_name in orig_name:
                        name_match = True
                        break
                if name_match:
                    break
                    
            if matched_names and not name_match:
                # Snapped to a completely different named road, reject
                continue
            
            if not matched_names and len(original_names) > 0:
                # Snapped to an unnamed alley/parking lot, but original road had a name, reject
                continue
                
        # Found valid opposite carriageway
        matched_shape_str = opp_trace.get("shape")
        if matched_shape_str:
            matched_coords = decode_polyline6(matched_shape_str)
            matched_coords = list(reversed(matched_coords))
            
            if len(matched_coords) >= 2:
                logger.info(f"[find_opposite_carriageway] Found DIVIDED_CARRIAGEWAY opposite lane at {offset}m")
                return "DIVIDED_CARRIAGEWAY", {
                    "type": "LineString",
                    "coordinates": matched_coords
                }

    # Loop finished, no valid opposite lane found
    logger.info("[find_opposite_carriageway] Dynamic search failed. Classified as TRUE_ONE_WAY")
    return "TRUE_ONE_WAY", None
