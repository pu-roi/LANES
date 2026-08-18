from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
import asyncio
import json

from app.core.database import get_db
from app.models.report import FloodReport
from app.schemas.report import FloodReportResponse

router = APIRouter()

from sqlalchemy import func
from app.models.report import FloodAvoidanceZone

def get_active_floods(db: Session):
    zones = db.query(
        func.ST_AsGeoJSON(FloodAvoidanceZone.geometry).label("geojson"),
        FloodReport.severity,
        FloodAvoidanceZone.id,
    ).join(
        FloodReport, FloodAvoidanceZone.id == FloodReport.zone_id
    ).filter(
        FloodAvoidanceZone.is_active == True,
        (FloodAvoidanceZone.expires_at == None) | (FloodAvoidanceZone.expires_at > func.now())
    ).all()
    
    data = []
    for z in zones:
        geom = json.loads(z.geojson) if z.geojson else None
        data.append({
            "id": z.id,
            "status": "active",
            "severity": z.severity.value if hasattr(z.severity, "value") else z.severity,
            "polygon": geom
        })
    return data

async def flood_event_generator(request: Request, db: Session):
    """
    Generator that yields server-sent events for live flood sync.
    """
    # Send an initial snapshot immediately
    initial_data = get_active_floods(db)
    
    yield {
        "event": "init",
        "data": json.dumps(initial_data)
    }

    # Polling loop for updates
    # In a production environment with multiple workers, 
    # Redis Pub/Sub or LISTEN/NOTIFY in PostgreSQL is preferred.
    # For now, we poll every 10 seconds.
    last_count = len(initial_data)
    
    while True:
        if await request.is_disconnected():
            break
            
        await asyncio.sleep(10)
        
        current_data = get_active_floods(db)
        
        yield {
            "event": "update",
            "data": json.dumps(current_data)
        }

@router.get("/stream")
async def sync_stream(request: Request, db: Session = Depends(get_db)):
    """
    Live sync stream (Server-Sent Events) for offline/PWA synchronization.
    Pushes flood polygons in real-time.
    """
    return EventSourceResponse(flood_event_generator(request, db))
