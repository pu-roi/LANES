"""Concurrency, freshness and lifecycle checks without database writes."""

import asyncio
import json

import pytest

from app.api.v1.endpoints.sync import flood_event_generator
from app.services.flood_sync_service import FloodSyncService, SyncCapacityError
from app.services import flood_sync_service


class ConnectedRequest:
    async def is_disconnected(self) -> bool:
        return False


def test_one_read_serves_100_clients_and_late_subscribers(monkeypatch: pytest.MonkeyPatch) -> None:
    reads = 0
    data = [{"id": 2}, {"id": 1}]

    def load() -> list[dict]:
        nonlocal reads
        reads += 1
        return data

    async def scenario() -> None:
        service = FloodSyncService(load)
        tick = asyncio.Queue()
        monkeypatch.setattr(service, "_wait_for_next_poll", tick.get)
        queues = [service.subscribe() for _ in range(100)]
        try:
            with pytest.raises(SyncCapacityError):
                service.subscribe()
            results = await asyncio.wait_for(asyncio.gather(*(q.get() for q in queues)), 3)
            assert reads == 1
            assert all(json.loads(result) == [{"id": 1}, {"id": 2}] for result in results)
            service.unsubscribe(queues.pop())
            late = service.subscribe()
            assert await late.get() == results[0]
            assert reads == 1
            # A subsequent authoritative poll reaches every subscriber without
            # adding per-client database work, even when the row order changes.
            data.reverse()
            tick.put_nowait(None)
            results2 = await asyncio.wait_for(asyncio.gather(*(q.get() for q in [*queues, late])), 3)
            assert reads == 2
            assert results2 == results
        finally:
            await service.close()
        assert service.client_count == 0
        assert service._task is None

    asyncio.run(scenario())


def test_database_session_closes_after_a_failed_read(monkeypatch: pytest.MonkeyPatch) -> None:
    class Session:
        closed = False

        def close(self) -> None:
            self.closed = True

    session = Session()
    monkeypatch.setattr(flood_sync_service, "SessionLocal", lambda: session)

    def failed_read(db):
        raise RuntimeError("Simulated database failure")

    monkeypatch.setattr(flood_sync_service, "get_active_floods", failed_read)
    assert flood_sync_service.read_active_floods() is None
    assert session.closed


def test_shutdown_and_new_lifespan_can_use_a_new_event_loop() -> None:
    service = FloodSyncService(lambda: [])

    async def lifespan() -> None:
        queue = service.subscribe()
        assert json.loads(await asyncio.wait_for(queue.get(), 3)) == []
        await asyncio.sleep(0)  # Enter the interval wait, binding its event loop.
        await service.close()
        assert service.client_count == 0

    asyncio.run(lifespan())
    asyncio.run(lifespan())


def test_slow_clients_receive_latest_clearance_and_failures_recover(monkeypatch: pytest.MonkeyPatch) -> None:
    values = iter([None, [{"id": 4}], []])

    async def scenario() -> None:
        service = FloodSyncService(lambda: next(values))
        tick = asyncio.Queue()
        monkeypatch.setattr(service, "_wait_for_next_poll", tick.get)
        fast, slow = service.subscribe(), service.subscribe()
        stream = flood_event_generator(ConnectedRequest(), fast, service)
        try:
            failed = await asyncio.wait_for(anext(stream), 3)
            assert json.loads(failed["data"]) == {"status": "pool_busy"}
            tick.put_nowait(None)
            recovered = await asyncio.wait_for(anext(stream), 3)
            assert recovered["event"] == "update"
            assert json.loads(recovered["data"]) == [{"id": 4}]
            tick.put_nowait(None)
            cleared = await asyncio.wait_for(anext(stream), 3)
            assert json.loads(cleared["data"]) == []
            # The unconsumed queue does not retain stale flooding or failures.
            assert slow.qsize() == 1
            assert json.loads(slow.get_nowait()) == []
        finally:
            await stream.aclose()
            assert service.client_count == 1
            service.unsubscribe(slow)
            tick.put_nowait(None)
            await asyncio.wait_for(service._task, 3)
        assert service._task is None
        assert not service._has_polled
        # Returning after idle must read again, rather than reuse old data.
        service.loader = lambda: [{"id": 99}]
        queue = service.subscribe()
        try:
            assert json.loads(await asyncio.wait_for(queue.get(), 3)) == [{"id": 99}]
        finally:
            await service.close()

    asyncio.run(scenario())
