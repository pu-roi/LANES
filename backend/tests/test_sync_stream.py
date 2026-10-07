"""Change-driven flood sync must preserve offline data and real updates."""
import asyncio
import json

from app.api.v1.endpoints import sync


class ConnectedRequest:
    async def is_disconnected(self) -> bool:
        return False


def test_unchanged_snapshots_send_keepalives_and_clearance_still_updates() -> None:

    async def scenario() -> list[dict]:
        queue = asyncio.Queue()
        for data in [[{"id": 1, "severity": "high"}], [{"severity": "high", "id": 1}], []]:
            queue.put_nowait(json.dumps(data, sort_keys=True))
        stream = sync.flood_event_generator(ConnectedRequest(), queue)
        try:
            return [await anext(stream) for _ in range(3)]
        finally:
            await stream.aclose()

    initial, unchanged, cleared = asyncio.run(scenario())
    assert initial["event"] == "init"
    assert unchanged["event"] == "keepalive"
    assert json.loads(unchanged["data"]) == {"status": "unchanged"}
    assert cleared["event"] == "update"
    assert json.loads(cleared["data"]) == []


def test_failed_initial_read_does_not_publish_a_false_empty_snapshot() -> None:

    async def scenario() -> list[dict]:
        queue = asyncio.Queue()
        queue.put_nowait(None)
        queue.put_nowait(json.dumps([{"id": 9}]))
        stream = sync.flood_event_generator(ConnectedRequest(), queue)
        try:
            return [await anext(stream) for _ in range(2)]
        finally:
            await stream.aclose()

    unavailable, recovered = asyncio.run(scenario())
    assert unavailable["event"] == "keepalive"
    assert json.loads(unavailable["data"]) == {"status": "pool_busy"}
    assert recovered["event"] == "update"
    assert json.loads(recovered["data"]) == [{"id": 9}]
