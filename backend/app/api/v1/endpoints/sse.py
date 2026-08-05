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
                
                # Wait for next event
                data = await q.get()
                yield {"data": data}
        except asyncio.CancelledError:
            pass
        finally:
            manager.unsubscribe(q)

    return EventSourceResponse(event_generator())
