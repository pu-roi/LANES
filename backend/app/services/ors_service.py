import httpx
import logging
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.config import settings
from app import models
from app.models.report import ReportSeverity

logger = logging.getLogger(__name__)

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

async def fetch_ors_route(client: httpx.AsyncClient, payload: dict, profile: str) -> Optional[dict]:
    url = f"{settings.ORS_URL}/directions/{profile}/geojson"
    headers = {
        "Authorization": settings.ORS_API_KEY,
        "Accept": "application/json, application/geo+json",
        "Content-Type": "application/json"
    }
    try:
        response = await client.post(url, headers=headers, json=payload, timeout=15.0)
        if response.status_code == 200:
            return response.json()
        logger.error(f"ORS Error ({response.status_code}): {response.text}")
        return None
    except httpx.RequestError as exc:
        logger.error(f"ORS Connection Error: {exc}")
        return None

async def calculate_flood_safe_route(
    db: Session,
    start: List[float],
    end: List[float],
    ignore_floods: bool = False,
    vehicle_profile: str = "light"
) -> Dict[str, Any]:
    """Queries OpenRouteService using dynamic avoid_polygons."""
    
    try:
        red, orange, yellow = get_active_flood_polygons(db) if not ignore_floods else ([], [], [])
    except Exception as e:
        logger.warning(f"Failed to fetch flood polygons ({e}). Bypassing flood avoidance.")
        red, orange, yellow = [], [], []

    blocked = []
    if vehicle_profile == "walk":
        blocked = red + orange
    elif vehicle_profile in ["motorcycle", "light"]:
        blocked = red + orange + yellow
    elif vehicle_profile == "heavy":
        blocked = red

    # Format for ORS (list of GeoJSON Polygons coordinates)
    multi_polygon_coords = []
    for poly in blocked:
        if poly:
            multi_polygon_coords.append([poly])

    ors_profile = "driving-car"
    if vehicle_profile == "motorcycle":
        ors_profile = "driving-car" # ORS doesn't have motorcycle, use car
    elif vehicle_profile == "walk":
        ors_profile = "foot-walking"

    base_payload = {
        "coordinates": [[start[0], start[1]], [end[0], end[1]]],
        "instructions": True,
        "geometry": True,
        "units": "m",
        "preference": "fastest",
        "alternative_routes": {
            "target_count": 3,
            "weight_factor": 1.5,
            "share_factor": 0.5
        }
    }

    payload_with_avoid = base_payload.copy()
    if multi_polygon_coords and not ignore_floods:
        payload_with_avoid["options"] = {
            "avoid_polygons": {
                "type": "MultiPolygon",
                "coordinates": multi_polygon_coords
            }
        }

    async with httpx.AsyncClient() as client:
        tasks = []
        
        if multi_polygon_coords and not ignore_floods:
            # First, fetch direct route (ignoring polygons)
            tasks.append(fetch_ors_route(client, base_payload, ors_profile))
            
        tasks.append(fetch_ors_route(client, payload_with_avoid, ors_profile))
        
        results = await asyncio.gather(*tasks)

    valid_routes = []
    
    # Process direct result first
    if multi_polygon_coords and not ignore_floods:
        direct_res = results.pop(0)
        if direct_res and "features" in direct_res and len(direct_res["features"]) > 0:
            feature = direct_res["features"][0]
            props = feature.get("properties", {})
            summary = props.get("summary", {})
            geom = feature.get("geometry", {})
            
            valid_routes.append({
                "index": 0,
                "label": "Direct (Flooded)",
                "geometry": geom,
                "distance": summary.get("distance", 0.0),
                "duration": summary.get("duration", 0.0),
                "avoided_floods": True,
                "blocked": True,
                "is_truncated": False,
                "safety_score": 0.0,
                "flood_risk": "extreme",
                "instructions": props.get("segments", [{}])[0].get("steps", [])
            })

    # Process safe route result
    main_res = results[0] if results else None
    if main_res and "features" in main_res:
        label = "Recommended Detour" if (multi_polygon_coords and not ignore_floods) else "Recommended"
        
        for i, feature in enumerate(main_res["features"]):
            props = feature.get("properties", {})
            summary = props.get("summary", {})
            geom = feature.get("geometry", {})
            
            # ORS usually returns 1 feature for directions, but we'll loop just in case
            valid_routes.append({
                "index": len(valid_routes),
                "label": label if i == 0 else f"Alternative {i}",
                "geometry": geom,
                "distance": summary.get("distance", 0.0),
                "duration": summary.get("duration", 0.0),
                "avoided_floods": len(blocked) > 0 and not ignore_floods,
                "blocked": False,
                "is_truncated": False,
                "safety_score": 100.0,
                "flood_risk": "none",
                "instructions": props.get("segments", [{}])[0].get("steps", [])
            })

    if not valid_routes:
        raise HTTPException(status_code=404, detail="No route options found by the pathfinding engine.")

    return {
        "routes": valid_routes,
        "recommended_index": 1 if multi_polygon_coords and not ignore_floods and len(valid_routes) > 1 else 0
    }
