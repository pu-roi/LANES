"""A synchronous weather provider must not stall unrelated ASGI requests."""

import asyncio
import threading

import httpx
from fastapi import FastAPI

from app.api.v1.endpoints import weather


def test_slow_weather_requests_leave_health_responsive(monkeypatch) -> None:
    app = FastAPI()
    app.include_router(weather.router)
    started = threading.Event()
    release = threading.Event()

    @app.get("/probe")
    async def probe() -> dict:
        return {"ok": True}

    def slow_weather(*args, **kwargs):
        started.set()
        assert release.wait(3), "ASGI loop was blocked by weather provider"
        raise RuntimeError("Simulated provider unavailable")

    monkeypatch.setattr(weather.openmeteo, "weather_api", slow_weather)

    async def scenario() -> None:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            for endpoint in ("/current", "/forecast"):
                started.clear()
                release.clear()
                task = asyncio.create_task(client.get(endpoint))
                try:
                    assert await asyncio.to_thread(started.wait, 2)
                    response = await asyncio.wait_for(client.get("/probe"), 1)
                    assert response.json() == {"ok": True}
                finally:
                    release.set()
                assert (await task).status_code == 200

    asyncio.run(scenario())
