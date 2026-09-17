import asyncio
import json
import logging
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from app.core.database import SessionLocal
from app.services.report_service import get_active_floods

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_active_floods_safe():
    """
    Acquire a short-lived DB session, fetch active floods, and immediately close the session.
    Guarantees connections are returned to the pool instantly and never held during SSE streaming.
    """
    db = SessionLocal()
    try:
        return get_active_floods(db)
    except Exception as exc:
        logger.warning(f"Error fetching active floods for live sync: {exc}")
        return []
    finally:
        db.close()


async def flood_event_generator(request: Request):
    """
    Generator that yields server-sent events for live flood sync.
    Runs DB queries in a worker thread and strictly closes DB sessions immediately.
    """
    # Send an initial snapshot immediately
    initial_data = await asyncio.to_thread(_get_active_floods_safe)
    
    yield {
        "event": "init",
        "data": json.dumps(initial_data)
    }

    # Polling loop for updates
    while True:
        if await request.is_disconnected():
            break
            
        await asyncio.sleep(10)

        if await request.is_disconnected():
            break
        
        current_data = await asyncio.to_thread(_get_active_floods_safe)
        
        yield {
            "event": "update",
            "data": json.dumps(current_data)
        }


@router.get("/stream")
async def sync_stream(request: Request):
    """
    Live sync stream (Server-Sent Events) for offline/PWA synchronization.
    Pushes flood polygons in real-time without holding database connections.
    """
    return EventSourceResponse(flood_event_generator(request))
