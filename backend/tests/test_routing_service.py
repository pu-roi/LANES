import asyncio

import httpx
import pytest
from fastapi import HTTPException

from app.schemas.route import RouteRequest
from app.services import routing_service
from app.services import valhalla_service
from app.services.valhalla_service import ValhallaServiceUnavailable


ROUTE_RESPONSE = {
    "routes": [],
    "recommended_index": -1,
}


def payload(engine: str = "valhalla") -> RouteRequest:
    return RouteRequest(start=[121.0, 14.5], end=[121.1, 14.6], engine=engine)


def test_route_request_defaults_to_valhalla() -> None:
    assert RouteRequest(start=[121.0, 14.5], end=[121.1, 14.6]).engine == "valhalla"


def test_valhalla_request_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(valhalla_service, "get_valhalla_auth_headers", lambda: {})
    monkeypatch.setattr(
        valhalla_service.httpx,
        "post",
        lambda **_: httpx.Response(200, json={"trip": {"legs": []}}),
    )

    assert valhalla_service.request_valhalla_route([121.0, 14.5], [121.1, 14.6]) == {
        "trip": {"legs": []}
    }


def test_valhalla_timeout_is_service_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(valhalla_service, "get_valhalla_auth_headers", lambda: {})

    def timeout(**_: object) -> None:
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(valhalla_service.httpx, "post", timeout)

    with pytest.raises(ValhallaServiceUnavailable):
        valhalla_service.request_valhalla_route([121.0, 14.5], [121.1, 14.6])


def test_valhalla_5xx_is_service_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(valhalla_service, "get_valhalla_auth_headers", lambda: {})
    monkeypatch.setattr(
        valhalla_service.httpx,
        "post",
        lambda **_: httpx.Response(503, text="service unavailable"),
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
        lambda **_: httpx.Response(400, text="No path could be found"),
    )

    assert valhalla_service.request_valhalla_route([121.0, 14.5], [121.1, 14.6]) is None


def test_valhalla_response_is_not_marked_as_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(routing_service.valhalla_service, "calculate_flood_safe_route", lambda **_: ROUTE_RESPONSE)

    result = asyncio.run(routing_service.calculate_route(payload(), db=None))

    assert result["engine_used"] == "valhalla"
    assert result["fallback_used"] is False


def test_valhalla_unavailable_falls_back_to_ors(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(**_: object) -> dict:
        raise ValhallaServiceUnavailable("connection refused")

    async def ors_response(**_: object) -> dict:
        return ROUTE_RESPONSE

    monkeypatch.setattr(routing_service.valhalla_service, "calculate_flood_safe_route", unavailable)
    monkeypatch.setattr(routing_service.ors_service, "calculate_flood_safe_route", ors_response)

    result = asyncio.run(routing_service.calculate_route(payload(), db=None))

    assert result["engine_used"] == "ors"
    assert result["fallback_used"] is True


def test_valid_valhalla_no_route_does_not_call_ors(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_route(**_: object) -> dict:
        raise HTTPException(status_code=404, detail="No route options found")

    async def unexpected_ors(**_: object) -> dict:
        raise AssertionError("ORS must not be called for a valid no-route response")

    monkeypatch.setattr(routing_service.valhalla_service, "calculate_flood_safe_route", no_route)
    monkeypatch.setattr(routing_service.ors_service, "calculate_flood_safe_route", unexpected_ors)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(routing_service.calculate_route(payload(), db=None))

    assert exc_info.value.status_code == 404


def test_both_providers_unavailable_returns_retryable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(**_: object) -> dict:
        raise ValhallaServiceUnavailable("timeout")

    async def ors_unavailable(**_: object) -> dict:
        raise HTTPException(status_code=404, detail="ORS unavailable")

    monkeypatch.setattr(routing_service.valhalla_service, "calculate_flood_safe_route", unavailable)
    monkeypatch.setattr(routing_service.ors_service, "calculate_flood_safe_route", ors_unavailable)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(routing_service.calculate_route(payload(), db=None))

    assert exc_info.value.status_code == 503


def test_explicit_ors_does_not_mark_a_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    async def ors_response(**_: object) -> dict:
        return ROUTE_RESPONSE

    monkeypatch.setattr(routing_service.ors_service, "calculate_flood_safe_route", ors_response)

    result = asyncio.run(routing_service.calculate_route(payload("ors"), db=None))

    assert result["engine_used"] == "ors"
    assert result["fallback_used"] is False
