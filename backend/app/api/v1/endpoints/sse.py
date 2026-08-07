import asyncio
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from app.core.sse import manager

router = APIRouter()

@router.get("/stream")
async def sse_stream(request: Request):
    """
    Public Server-Sent Events endpoint for real-time map updates.
    Provides unidirectional data flow from server to client.
    """
    q = manager.subscribe()

    async def event_generator():
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
            manager.unsubscribe(q)

    return EventSourceResponse(event_generator(), ping=5)
