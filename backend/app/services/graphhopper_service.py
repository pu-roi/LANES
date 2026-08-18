import json
import httpx
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.models.report import ReportSeverity
from app.core.config import settings

def get_active_flood_polygons(db: Session) -> Tuple[List[List[List[float]]], List[List[List[float]]], List[List[List[float]]]]:
    """
    Fetches active flood avoidance zones and groups them by severity.
    Returns lists of GeoJSON polygon exterior rings.
    """
    zones = db.query(
        func.ST_AsGeoJSON(models.FloodAvoidanceZone.geometry).label("geojson"),
        models.FloodReport.severity
    ).join(
        models.FloodReport, models.FloodAvoidanceZone.id == models.FloodReport.zone_id
    ).filter(
        models.FloodAvoidanceZone.is_active == True,
        (models.FloodAvoidanceZone.expires_at == None) | (models.FloodAvoidanceZone.expires_at > func.now())
    ).all()
    
    red, orange, yellow = [], [], []
    for z in zones:
        geom = json.loads(z.geojson)
        if geom["type"] == "Polygon" and len(geom["coordinates"]) > 0:
            exterior_ring = geom["coordinates"][0]
            if z.severity == ReportSeverity.EXTREME:
                red.append(exterior_ring)
            elif z.severity == ReportSeverity.HIGH:
                orange.append(exterior_ring)
            elif z.severity == ReportSeverity.MEDIUM:
                yellow.append(exterior_ring)
                
    return red, orange, yellow

async def fetch_graphhopper_route(client: httpx.AsyncClient, payload: dict) -> Optional[dict]:
    url = f"{settings.GRAPHHOPPER_URL}/route"
    try:
        response = await client.post(url, json=payload, timeout=10.0)
        if response.status_code == 200:
            return response.json()
        print(f"GraphHopper Error: {response.text}")
        return None
    except httpx.RequestError as exc:
        print(f"GraphHopper Connection Error: {exc}")
        return None

async def calculate_flood_safe_route(
    db: Session,
    start: List[float],
    end: List[float],
    ignore_floods: bool = False,
    vehicle_profile: str = "light"
) -> Dict[str, Any]:
    """Queries GraphHopper using multi-profile requests with dynamic custom_model flood areas."""
    
    try:
        red, orange, yellow = get_active_flood_polygons(db) if not ignore_floods else ([], [], [])
    except Exception as e:
        print(f"Warning: Failed to fetch flood polygons ({e}). Bypassing flood avoidance.")
        red, orange, yellow = [], [], []

    blocked = []
    if vehicle_profile == "walk":
        blocked = red + orange
    elif vehicle_profile in ["motorcycle", "light"]:
        blocked = red + orange + yellow
    elif vehicle_profile == "heavy":
        blocked = red

    areas = {}
    priorities = []
    
    for i, poly in enumerate(blocked):
        area_id = f"blocked_{i}"
        areas[area_id] = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [poly]
            }
        }
        priorities.append({
            "if": f"in_{area_id}",
            "multiply_by": "0.0"
        })

    gh_profile = "car"
    if vehicle_profile == "motorcycle":
        gh_profile = "motorcycle"
    elif vehicle_profile == "walk":
        gh_profile = "foot"

    def create_payload(profile_modifier=None):
        custom_model = {
            "areas": areas,
            "priority": list(priorities),
            "speed": []
        }
        
        # We can't query 'road_class' unless the GH profile supports it, but standard 'car' profile does.
        if profile_modifier == "main_roads":
            custom_model["priority"].append({"if": "road_class == PRIMARY || road_class == TRUNK", "multiply_by": "1.5"})
        elif profile_modifier == "alleys":
            custom_model["priority"].append({"if": "road_class == RESIDENTIAL || road_class == UNCLASSIFIED", "multiply_by": "1.2"})
        elif profile_modifier == "direct":
            # Direct ignores all flood areas to show what would happen without avoidance
            custom_model["areas"] = {}
            custom_model["priority"] = []

        return {
            "points": [[start[0], start[1]], [end[0], end[1]]],
            "profile": gh_profile,
            "ch.disable": True,
            "points_encoded": False,
            "custom_model": custom_model
        }

    # Query multiple models simultaneously
    payload_recommended = create_payload()
    payload_main = create_payload("main_roads")
    payload_alleys = create_payload("alleys")
    payload_direct = create_payload("direct") if len(blocked) > 0 and not ignore_floods else None

    async with httpx.AsyncClient() as client:
        tasks = [
            fetch_graphhopper_route(client, payload_recommended),
            fetch_graphhopper_route(client, payload_main),
            fetch_graphhopper_route(client, payload_alleys)
        ]
        if payload_direct:
            tasks.insert(0, fetch_graphhopper_route(client, payload_direct))
            
        results = await asyncio.gather(*tasks)

    valid_routes = []
    seen_distances = set()
    
    # Process results mapping
    if payload_direct:
        direct_res = results.pop(0)
        if direct_res and "paths" in direct_res and len(direct_res["paths"]) > 0:
            path = direct_res["paths"][0]
            coords = path.get("points", {}).get("coordinates", [])
            valid_routes.append({
                "index": 0,
                "label": "Direct (Flooded)",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                },
                "distance": path.get("distance", 0.0),
                "duration": path.get("time", 0.0) / 1000.0,
                "avoided_floods": True,
                "blocked": True, # We mark direct as blocked since it goes through areas we want to avoid
                "is_truncated": False,
                "safety_score": 0.0,
                "flood_risk": "extreme"
            })

    labels = ["Recommended", "Main Roads Preferred", "Allow Small Alleys"]
    
    for res, label in zip(results, labels):
        if res and "paths" in res and len(res["paths"]) > 0:
            path = res["paths"][0]
            dist = path.get("distance", 0.0)
            
            # Simple deduplication based on distance matching within 20 meters
            rounded_dist = round(dist / 20) * 20
            if rounded_dist not in seen_distances:
                seen_distances.add(rounded_dist)
                coords = path.get("points", {}).get("coordinates", [])
                
                valid_routes.append({
                    "index": len(valid_routes),
                    "label": label if len(valid_routes) > 0 or not payload_direct else "Recommended Detour",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": coords
                    },
                    "distance": dist,
                    "duration": path.get("time", 0.0) / 1000.0,
                    "avoided_floods": len(blocked) > 0 and not ignore_floods,
                    "blocked": False,
                    "is_truncated": False,
                    "safety_score": 100.0,
                    "flood_risk": "none"
                })

    if not valid_routes:
        raise HTTPException(status_code=404, detail="No route options found by the pathfinding engine.")

    return {
        "routes": valid_routes,
        "recommended_index": 1 if payload_direct and len(valid_routes) > 1 else 0
    }
