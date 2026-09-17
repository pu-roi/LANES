import asyncio

import httpx
import pytest
from fastapi import HTTPException

from app.schemas.route import RouteRequest
from app.services import routing_service
from app.services import ors_service
from app.services import valhalla_service
from app.services.flood_routing_policy import ActiveFloodZone
from app.services.valhalla_service import ValhallaServiceUnavailable


ROUTE_RESPONSE = {
    "routes": [],
    "recommended_index": -1,
}

RAW_ROUTE = [{
    "geometry": {"type": "LineString", "coordinates": [[121.0, 14.5], [121.1, 14.6]]},
    "distance": 1000.0,
    "duration": 120.0,
    "instructions": [],
    "is_truncated": False,
}]


def payload(engine: str = "valhalla") -> RouteRequest:
    return RouteRequest(start=[121.0, 14.5], end=[121.1, 14.6], engine=engine)


def test_route_request_defaults_to_valhalla() -> None:
    assert RouteRequest(start=[121.0, 14.5], end=[121.1, 14.6]).engine == "valhalla"


def test_valhalla_request_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(valhalla_service, "get_valhalla_auth_headers", lambda: {})
    monkeypatch.setattr(
        valhalla_service.httpx,
        "post",
        lambda _url, **_: httpx.Response(200, json={"trip": {"legs": []}}),
    )

    assert valhalla_service.request_valhalla_route([121.0, 14.5], [121.1, 14.6]) == {
        "trip": {"legs": []}
    }


def test_valhalla_uses_documented_exclude_polygons_and_three_alternates(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(valhalla_service, "get_valhalla_auth_headers", lambda: {})

    def post(_url: str, **kwargs: object) -> httpx.Response:
        captured.update(kwargs["json"])  # type: ignore[arg-type]
        return httpx.Response(200, json={"trip": {"legs": []}})

    monkeypatch.setattr(valhalla_service.httpx, "post", post)
    valhalla_service.request_valhalla_route(
        [121.0, 14.5], [121.1, 14.6], avoid_polygons=[[[121.0, 14.5], [121.1, 14.5], [121.0, 14.5]]]
    )

    assert captured["alternates"] == 3
    assert "exclude_polygons" in captured
    assert "avoid_polygons" not in captured


def test_ors_uses_geojson_avoid_polygons_and_three_alternates(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    async def fake_fetch(_client: object, payload: dict, profile: str) -> dict:
        captured.update(payload)
        captured["profile"] = profile
        return {"features": []}

    monkeypatch.setattr(ors_service, "fetch_ors_route", fake_fetch)
    asyncio.run(ors_service.fetch_route_candidates(
        [121.0, 14.5], [121.1, 14.6], exclude_polygons=[[[121.0, 14.5], [121.1, 14.5], [121.0, 14.5]]], vehicle_profile="motorcycle"
    ))

    assert captured["profile"] == "driving-car"
    assert captured["alternative_routes"]["target_count"] == 3
    assert captured["options"]["avoid_polygons"]["type"] == "MultiPolygon"


def test_valhalla_timeout_is_service_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(valhalla_service, "get_valhalla_auth_headers", lambda: {})

    def timeout(_url: str, **_: object) -> None:
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(valhalla_service.httpx, "post", timeout)

    with pytest.raises(ValhallaServiceUnavailable):
        valhalla_service.request_valhalla_route([121.0, 14.5], [121.1, 14.6])


def test_valhalla_5xx_is_service_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(valhalla_service, "get_valhalla_auth_headers", lambda: {})
    monkeypatch.setattr(
        valhalla_service.httpx,
        "post",
        lambda _url, **_: httpx.Response(503, text="service unavailable"),
    )

    with pytest.raises(ValhallaServiceUnavailable):
        valhalla_service.request_valhalla_route([121.0, 14.5], [121.1, 14.6])


def test_valhalla_no_route_response_is_not_an_availability_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(valhalla_service, "get_valhalla_auth_headers", lambda: {})
    monkeypatch.setattr(
        valhalla_service.httpx,
        "post",
        lambda _url, **_: httpx.Response(400, text="No path could be found"),
    )

    assert valhalla_service.request_valhalla_route([121.0, 14.5], [121.1, 14.6]) is None


def test_valhalla_response_is_not_marked_as_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(routing_service, "get_active_flood_zones", lambda _: [])
    monkeypatch.setattr(routing_service.valhalla_service, "fetch_route_candidates", lambda **_: RAW_ROUTE)

    result = asyncio.run(routing_service.calculate_route(payload(), db=None))

    assert result["engine_used"] == "valhalla"
    assert result["fallback_used"] is False


def test_valhalla_unavailable_falls_back_to_ors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(routing_service, "get_active_flood_zones", lambda _: [])
    def unavailable(**_: object) -> list[dict]:
        raise ValhallaServiceUnavailable("connection refused")

    async def ors_response(**_: object) -> list[dict]:
        return RAW_ROUTE

    monkeypatch.setattr(routing_service.valhalla_service, "fetch_route_candidates", unavailable)
    monkeypatch.setattr(routing_service.ors_service, "fetch_route_candidates", ors_response)

    result = asyncio.run(routing_service.calculate_route(payload(), db=None))

    assert result["engine_used"] == "ors"
    assert result["fallback_used"] is True


def test_valid_valhalla_no_route_does_not_call_ors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(routing_service, "get_active_flood_zones", lambda _: [])
    def no_route(**_: object) -> list[dict]:
        return []

    async def unexpected_ors(**_: object) -> list[dict]:
        raise AssertionError("ORS must not be called for a valid no-route response")

    monkeypatch.setattr(routing_service.valhalla_service, "fetch_route_candidates", no_route)
    monkeypatch.setattr(routing_service.ors_service, "fetch_route_candidates", unexpected_ors)

    result = asyncio.run(routing_service.calculate_route(payload(), db=None))
    assert result["routes"] == []
    assert result["engine_used"] == "valhalla"


def test_both_providers_unavailable_returns_retryable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(routing_service, "get_active_flood_zones", lambda _: [])
    def unavailable(**_: object) -> list[dict]:
        raise ValhallaServiceUnavailable("timeout")

    async def ors_unavailable(**_: object) -> list[dict]:
        return []

    monkeypatch.setattr(routing_service.valhalla_service, "fetch_route_candidates", unavailable)
    monkeypatch.setattr(routing_service.ors_service, "fetch_route_candidates", ors_unavailable)

    result = asyncio.run(routing_service.calculate_route(payload(), db=None))
    assert result["engine_used"] == "ors"
    assert result["routes"] == []


def test_explicit_ors_does_not_mark_a_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(routing_service, "get_active_flood_zones", lambda _: [])
    async def ors_response(**_: object) -> list[dict]:
        return RAW_ROUTE

    monkeypatch.setattr(routing_service.ors_service, "fetch_route_candidates", ors_response)

    result = asyncio.run(routing_service.calculate_route(payload("ors"), db=None))

    assert result["engine_used"] == "ors"
    assert result["fallback_used"] is False


def test_legacy_ignore_floods_cannot_bypass_public_hard_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    flooded_zone = ActiveFloodZone(
        id=1, severity="high", polygon=[[120.9, 14.4], [121.2, 14.4], [121.2, 14.7], [120.9, 14.7], [120.9, 14.4]],
    )
    monkeypatch.setattr(routing_service, "get_active_flood_zones", lambda _: [flooded_zone])
    monkeypatch.setattr(routing_service.valhalla_service, "fetch_route_candidates", lambda **_: RAW_ROUTE)

    request = payload()
    request.ignore_floods = True
    result = asyncio.run(routing_service.calculate_route(request, db=None))

    assert result["routes"] == []
    assert result["blocked_baseline"] is not None
