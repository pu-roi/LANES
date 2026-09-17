import asyncio
import json
import logging
from fastapi import APIRouter, Request, HTTPException
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.exc import OperationalError

from app.core.database import SessionLocal
from app.services.report_service import get_active_floods

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Connection cap to prevent pool exhaustion ---
MAX_SYNC_CLIENTS = 100
_active_sync_clients = 0


def _get_active_floods_safe():
    """
    Acquire a short-lived DB session, fetch active floods, and immediately close the session.
    Guarantees connections are returned to the pool instantly and never held during SSE streaming.
    Returns None on pool exhaustion or DB errors so the stream can send a keepalive instead.
    """
    db = SessionLocal()
    try:
        return get_active_floods(db)
    except OperationalError as exc:
        logger.warning(f"DB pool exhaustion during live sync poll: {exc}")
        return None
    except Exception as exc:
        logger.warning(f"Error fetching active floods for live sync: {exc}")
        return None
    finally:
        db.close()


async def flood_event_generator(request: Request):
    """
    Generator that yields server-sent events for live flood sync.
    Runs DB queries in a worker thread and strictly closes DB sessions immediately.
    Gracefully handles pool exhaustion by sending keepalive events instead of crashing.
    """
    global _active_sync_clients
    _active_sync_clients += 1
    logger.info(f"Sync stream client connected. Active: {_active_sync_clients}/{MAX_SYNC_CLIENTS}")

    try:
        # Send an initial snapshot immediately
        initial_data = await asyncio.to_thread(_get_active_floods_safe)

        if initial_data is not None:
            yield {
                "event": "init",
                "data": json.dumps(initial_data)
            }
        else:
            # Pool was exhausted even for the initial fetch; send empty init
            yield {
                "event": "init",
                "data": json.dumps([])
            }

        # Polling loop for updates
        while True:
            if await request.is_disconnected():
                break

            await asyncio.sleep(15)  # 15s interval to reduce DB pressure (was 10s)

            if await request.is_disconnected():
                break

            current_data = await asyncio.to_thread(_get_active_floods_safe)

            if current_data is not None:
                yield {
                    "event": "update",
                    "data": json.dumps(current_data)
                }
            else:
                # Pool exhausted — send a keepalive so the client knows we're alive
                yield {
                    "event": "keepalive",
                    "data": json.dumps({"status": "pool_busy"})
                }
    finally:
        _active_sync_clients -= 1
        logger.info(f"Sync stream client disconnected. Active: {_active_sync_clients}/{MAX_SYNC_CLIENTS}")


@router.get("/stream")
async def sync_stream(request: Request):
    """
    Live sync stream (Server-Sent Events) for offline/PWA synchronization.
    Pushes flood polygons in real-time without holding database connections.

    Returns HTTP 503 when the max concurrent sync client limit is reached
    to prevent database connection pool exhaustion.
    """
    if _active_sync_clients >= MAX_SYNC_CLIENTS:
        raise HTTPException(
            status_code=503,
            detail=f"Too many active sync streams ({MAX_SYNC_CLIENTS}). Please retry later."
        )
    return EventSourceResponse(flood_event_generator(request))
