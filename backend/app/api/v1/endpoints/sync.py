import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from starlette.background import BackgroundTask

from app.services.flood_sync_service import FloodSyncService, SyncCapacityError, flood_sync

router = APIRouter()


async def flood_event_generator(
    request: Request,
    queue: asyncio.Queue[str | None],
    service: FloodSyncService = flood_sync,
):
    """Send the shared poll result, preserving each client's change tracking."""
    previous_snapshot = None
    first_poll = True
    try:
        while not await request.is_disconnected():
            try:
                snapshot = await asyncio.wait_for(queue.get(), timeout=1)
            except asyncio.TimeoutError:
                continue
            if snapshot is None:
                yield {"event": "keepalive", "data": json.dumps({"status": "pool_busy"})}
            elif snapshot != previous_snapshot:
                yield {"event": "init" if first_poll else "update", "data": snapshot}
                previous_snapshot = snapshot
            else:
                yield {"event": "keepalive", "data": json.dumps({"status": "unchanged"})}
            first_poll = False
    finally:
        service.unsubscribe(queue)


@router.get("/stream")
async def sync_stream(request: Request):
    """Public PWA flood sync with bounded subscribers and shared database polls."""
    try:
        queue = flood_sync.subscribe()
    except SyncCapacityError:
        raise HTTPException(status_code=503, detail="Too many active sync streams. Please retry later.")
    async def release_subscription() -> None:
        flood_sync.unsubscribe(queue)

    return EventSourceResponse(
        flood_event_generator(request, queue),
        background=BackgroundTask(release_subscription),
    )
