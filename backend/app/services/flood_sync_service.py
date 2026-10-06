"""Share one short-lived flood read per poll across this worker's SSE clients."""

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

from sqlalchemy.exc import OperationalError

from app.core.database import SessionLocal
from app.services.report_service import get_active_floods

logger = logging.getLogger(__name__)


def read_active_floods() -> list[dict[str, Any]] | None:
    """Close every session immediately; failed reads must not become []."""
    db = SessionLocal()
    try:
        return get_active_floods(db)
    except OperationalError:
        logger.warning("Database unavailable during live flood sync")
        return None
    except Exception:
        logger.exception("Failed to read live flood snapshot")
        return None
    finally:
        db.close()


class SyncCapacityError(Exception):
    """The worker's live-sync subscription limit has been reached."""


class FloodSyncService:
    """Poll once per worker, with one latest snapshot queued per subscriber.

    Each worker reads the authoritative database, including writes from jobs or
    other instances. The task stops polling after the last subscriber leaves.
    """

    def __init__(
        self,
        loader: Callable[[], list[dict[str, Any]] | None] = read_active_floods,
        interval_seconds: float = 15,
        max_clients: int = 100,
    ) -> None:
        self.loader = loader
        self.interval_seconds = interval_seconds
        self.max_clients = max_clients
        self._subscribers: set[asyncio.Queue[str | None]] = set()
        self._task: asyncio.Task[None] | None = None
        self._latest: str | None = None
        self._has_polled = False
        self._wake = asyncio.Event()

    @property
    def client_count(self) -> int:
        return len(self._subscribers)

    def subscribe(self) -> asyncio.Queue[str | None]:
        # Reserve capacity before yielding control or creating the response.
        if self.client_count >= self.max_clients:
            raise SyncCapacityError
        queue: asyncio.Queue[str | None] = asyncio.Queue(maxsize=1)
        was_idle = not self._subscribers
        self._subscribers.add(queue)
        if self._has_polled:
            queue.put_nowait(self._latest)
        if self._task is None:
            self._task = asyncio.create_task(self._poll())
        elif was_idle:
            self._wake.set()
        return queue

    def unsubscribe(self, queue: asyncio.Queue[str | None]) -> None:
        self._subscribers.discard(queue)
        if not self._subscribers:
            self._has_polled = False
            self._latest = None
            self._wake.set()

    async def _poll(self) -> None:
        try:
            while self._subscribers:
                self._wake.clear()
                try:
                    data = await asyncio.to_thread(self.loader)
                    self._latest = None if data is None else json.dumps(
                        sorted(data, key=lambda flood: flood["id"]),
                        sort_keys=True, separators=(",", ":"),
                    )
                except Exception:
                    logger.exception("Failed to prepare live flood snapshot")
                    self._latest = None
                self._has_polled = True
                for queue in self._subscribers:
                    if queue.full():
                        queue.get_nowait()
                    queue.put_nowait(self._latest)
                await self._wait_for_next_poll()
        finally:
            self._task = None
            self._has_polled = False
            self._latest = None
            self._wake = asyncio.Event()

    async def _wait_for_next_poll(self) -> None:
        try:
            await asyncio.wait_for(self._wake.wait(), timeout=self.interval_seconds)
        except asyncio.TimeoutError:
            pass

    async def close(self) -> None:
        """Release the polling task when the application shuts down."""
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._subscribers.clear()
        self._task = None
        self._has_polled = False
        self._latest = None
        self._wake = asyncio.Event()


flood_sync = FloodSyncService()
