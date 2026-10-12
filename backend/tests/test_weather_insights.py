"""Public weather errors never disclose upstream bodies, identifiers or secrets."""
import asyncio
import json
from datetime import datetime, timezone

import httpx
import pytest
from pydantic import ValidationError

from app.main import app
from app.schemas.weather_insights import WeatherInsightsRequest
from app.services.weather_insights_service import (
    PUBLIC_UNAVAILABLE, WeatherInsightsConfig, WeatherInsightsService, WeatherInsightsUnavailable,
    gemini_cooldown,
)

CONFIG = WeatherInsightsConfig(api_key="synthetic-weather-test")


def forecast(**changes):
    return {"dt": 1791849600, "time": "2026-10-13 08:00:00", "temp": 28,
            "pop": 33, "condition": "Cloudy", "icon": "cloudy", "precip_mm": 0,
            "humidity_pct": 80, "wind_kmh": 3, **changes}


def request():
    return WeatherInsightsRequest(location="Pasig City", forecast=[forecast()]*12)


def reply(*, content=None, **changes):
    parts = [{"thought": True, "text": "private thinking"}, {"text": json.dumps(content or {
        "storm_risk": "Next four hours: 33% chance of rain, with 0 mm forecast precipitation.",
        "environment": "Temperature is 28 degrees Celsius, humidity 80% and wind 3 km/h."})}]
    return httpx.Response(200, json={"modelVersion": "gemini-3.8-flash", "candidates": [
        {"finishReason": "STOP", "content": {"parts": parts}}], **changes})


@pytest.mark.asyncio
async def test_gemini_uses_only_four_slots_and_caches_concurrent_public_requests():
    calls = []
    async def transport(req):
        assert req.url.host == "generativelanguage.googleapis.com"
        assert req.headers["x-goog-api-key"] == CONFIG.api_key and "authorization" not in req.headers
        payload = json.loads(req.content)
        assert len(json.loads(payload["contents"][0]["parts"][0]["text"])["forecast"]) == 4
        calls.append(req.method)
        await asyncio.sleep(0)
        return reply()
    service = WeatherInsightsService()
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        first, second = await asyncio.gather(*[service.explain(request(), config=CONFIG, client=client) for _ in range(2)])
    assert calls == ["POST"] and first == second
    assert first.model == CONFIG.model and "private thinking" not in first.model_dump_json()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 401, 402, 403, 429, 500, 503])
async def test_provider_errors_are_safe_and_cooldown_prevents_repeat(status, caplog):
    calls = []
    private = {"error": {"message": "upstream-billing-remedy"}, "user_id": "private-account", "key": CONFIG.api_key}
    def transport(req):
        calls.append(req.method)
        return httpx.Response(status, json=private, headers={"retry-after": "120"})
    service = WeatherInsightsService()
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        for _ in range(2):
            with pytest.raises(WeatherInsightsUnavailable) as failure:
                await service.explain(request(), config=CONFIG, client=client)
            assert str(failure.value) == PUBLIC_UNAVAILABLE and failure.value.retry_after > 0
    assert calls == ["POST"]
    assert "upstream-billing-remedy" not in caplog.text and CONFIG.api_key not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("problem", ["timeout", "transport", "malformed", "truncated", "oversized", "extra", "wrong_type", "incomplete", "thought_only"])
async def test_failed_or_invalid_output_is_not_returned_as_generated_insights(problem):
    def transport(req):
        if problem == "timeout": raise httpx.ReadTimeout("private-error-text", request=req)
        if problem == "transport": raise httpx.ConnectError("private-error-text", request=req)
        if problem == "truncated": return httpx.Response(200, content=b'{"candidates":')
        if problem == "oversized": return httpx.Response(200, content=b" "*65537)
        if problem == "malformed": return reply(candidates=[None])
        if problem == "incomplete": return reply(candidates=[{"finishReason": "MAX_TOKENS"}])
        if problem == "thought_only": return reply(candidates=[{"finishReason": "STOP", "content": {"parts": [{"thought": True, "text": "{}"}]}}])
        return reply(content={"storm_risk": "forecast", "environment": 42 if problem == "wrong_type" else "conditions",
                             **({"extra": "private"} if problem == "extra" else {})})
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        with pytest.raises(WeatherInsightsUnavailable) as failure:
            await WeatherInsightsService().explain(request(), config=CONFIG, client=client)
    assert str(failure.value) == PUBLIC_UNAVAILABLE


@pytest.mark.parametrize("body", [[], [forecast(pop=101)], [forecast(temp=float("inf"))], [forecast()]*73])
def test_invalid_forecast_is_rejected_before_generation(body):
    with pytest.raises(ValidationError):
        WeatherInsightsRequest(location="Pasig", forecast=body)


@pytest.mark.asyncio
async def test_public_endpoint_maps_failure_to_safe_message_and_retry_header(monkeypatch):
    async def unavailable(_request):
        raise WeatherInsightsUnavailable(retry_after=900)
    monkeypatch.setattr("app.api.v1.endpoints.weather.weather_insights_service.explain", unavailable)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/weather/insights", json=request().model_dump(mode="json"))
    assert response.status_code == 503 and response.json() == {"detail": PUBLIC_UNAVAILABLE}
    assert response.headers["retry-after"] == "900"


@pytest.mark.asyncio
async def test_credential_rotation_does_not_inherit_previous_weather_cooldown():
    service = WeatherInsightsService()
    calls = []
    def transport(req):
        calls.append(req.headers["x-goog-api-key"])
        return httpx.Response(429) if len(calls) == 1 else reply()
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        with pytest.raises(WeatherInsightsUnavailable):
            await service.explain(request(), config=CONFIG, client=client)
        result = await service.explain(request(), config=WeatherInsightsConfig(api_key="rotated-synthetic"), client=client)
    assert result.insights and calls == [CONFIG.api_key, "rotated-synthetic"]


def test_gemini_retry_info_is_honored_and_daily_limit_waits_for_pacific_midnight():
    body = {"error": {"details": [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "34.5s"}]}}
    assert gemini_cooldown(httpx.Headers(), json.dumps(body).encode(), 429) == 35
    body["error"]["details"].append({"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [
        {"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]})
    # October is PDT: next midnight Pacific is 07:00 UTC / 15:00 Manila.
    assert gemini_cooldown(httpx.Headers(), json.dumps(body).encode(), 429,
        now=datetime(2026, 10, 12, 20, tzinfo=timezone.utc)) == 11*3600


@pytest.mark.parametrize("body", [b"not JSON", b'null', b'{"error":null}', b'{"error":{"details":"invalid"}}'])
def test_unknown_quota_error_keeps_conservative_cooldown(body):
    assert gemini_cooldown(httpx.Headers(), body, 429) == 900
