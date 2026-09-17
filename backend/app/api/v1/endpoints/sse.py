import asyncio
import logging
from fastapi import APIRouter, Request, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.core.sse import manager

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Connection cap to prevent resource exhaustion ---
MAX_SSE_CLIENTS = 200
_active_sse_clients = 0


@router.get("/stream")
async def sse_stream(request: Request):
    """
    Public Server-Sent Events endpoint for real-time map updates.
    Provides unidirectional data flow from server to client.

    Returns HTTP 503 when the max concurrent SSE client limit is reached
    to prevent server resource exhaustion.
    """
    global _active_sse_clients

    if _active_sse_clients >= MAX_SSE_CLIENTS:
        raise HTTPException(
            status_code=503,
            detail=f"Too many active SSE connections ({MAX_SSE_CLIENTS}). Please retry later."
        )

    q = manager.subscribe()

    async def event_generator():
        global _active_sse_clients
        _active_sse_clients += 1
        logger.info(f"SSE client connected. Active: {_active_sse_clients}/{MAX_SSE_CLIENTS}")

        try:
            while True:
                # If client closes connection, stop sending events
                if await request.is_disconnected():
                    break
                
                # Wait for next event with a timeout to check disconnects
                try:
                    data = await asyncio.wait_for(q.get(), timeout=1.0)
                    yield {"data": data}
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            raise
        finally:
            _active_sse_clients -= 1
            manager.unsubscribe(q)
            logger.info(f"SSE client disconnected. Active: {_active_sse_clients}/{MAX_SSE_CLIENTS}")

    return EventSourceResponse(event_generator(), ping=5)
