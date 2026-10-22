from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Any
import json

from app import models
from app.core.database import get_db
from app.services.flood_heatmap_service import severity_weight

router = APIRouter()

@router.get("/heatmap")
def get_heatmap_data(db: Session = Depends(get_db)) -> Any:
    """
    Returns a GeoJSON FeatureCollection of all approved flood reports for the Heatmap.
    """
    reports = db.query(
        models.FloodReport.id,
        models.FloodReport.severity,
        func.ST_AsGeoJSON(models.FloodReport.geometry).label("geojson")
    ).filter(
        models.FloodReport.status == "approved",
        models.FloodReport.deleted_at.is_(None),
        models.FloodReport.geometry.is_not(None)
    ).all()

    features = []
    for r in reports:
        if r.geojson:
            geometry = json.loads(r.geojson)
            # Map severity to a numerical weight for the heatmap
            if hasattr(r.severity, "value"):
                severity_val = r.severity.value
            else:
                severity_val = str(r.severity)
                
            weight = severity_weight(severity_val)
            
            features.append({
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "id": r.id,
                    "severity": severity_val,
                    "weight": weight
                }
            })
            
    return {
        "type": "FeatureCollection",
        "features": features
    }

@router.get("/stats")
def get_analytics_stats(db: Session = Depends(get_db)) -> Any:
    """
    Returns Top Flooded Barangays and Top Flooded Locations based on approved reports.
    """
    top_barangays_query = db.query(
        models.FloodReport.barangay,
        func.count(models.FloodReport.id).label("count")
    ).filter(
        models.FloodReport.status == "approved",
        models.FloodReport.deleted_at.is_(None),
        models.FloodReport.barangay.is_not(None)
    ).group_by(models.FloodReport.barangay).order_by(desc("count")).limit(5).all()

    top_barangays = [{"barangay": row.barangay, "count": row.count} for row in top_barangays_query]

    top_locations_query = db.query(
        models.FloodReport.human_readable_location,
        func.count(models.FloodReport.id).label("count")
    ).filter(
        models.FloodReport.status == "approved",
        models.FloodReport.deleted_at.is_(None),
        models.FloodReport.human_readable_location.is_not(None),
        models.FloodReport.human_readable_location != ""
    ).group_by(models.FloodReport.human_readable_location).order_by(desc("count")).limit(5).all()
    
    top_locations = [{"location": row.human_readable_location, "count": row.count} for row in top_locations_query]

    return {
        "top_barangays": top_barangays,
        "top_locations": top_locations
    }
