"""Actual proxy tokens survive restart/refresh; upstream Google is mocked."""
import time
from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient
from fastmcp.server.auth.auth import AccessToken
from fastmcp.server.auth.oauth_proxy.models import JTIMapping, UpstreamTokenSet

from app.mcp.server import create_server, SCOPES
from tests.test_mcp_auth_gateway import config, StubBackend


async def seed_reference(auth, *, expired=False):
    auth.get_routes(mcp_path="/mcp")
    now=time.time()
    await auth._upstream_token_store.put(key="upstream",value=UpstreamTokenSet(
        upstream_token_id="upstream",access_token="expired-google" if expired else "valid-google",
        refresh_token="private-refresh",refresh_token_expires_at=now+3600,
        expires_at=now-5 if expired else now+600,token_type="Bearer",scope=" ".join(SCOPES),
        client_id="fixture-client",created_at=now),ttl=3600)
    await auth._jti_mapping_store.put(key="fixture-jti",value=JTIMapping(
        jti="fixture-jti",upstream_token_id="upstream",created_at=now),ttl=600)
    return auth.jwt_issuer.issue_access_token(client_id="fixture-client",scopes=SCOPES,
                                            jti="fixture-jti",expires_in=600)


def mock_google(auth, config, monkeypatch):
    async def verify(token):
        if token != "valid-google": return None
        return AccessToken(token=token,client_id="fixture-client",scopes=SCOPES,
            expires_at=int(time.time())+600,subject=config.allowed_google_subject,
            claims={"sub":config.allowed_google_subject,"email":config.allowed_email,
                    "email_verified":True,"aud":config.google_client_id})
    monkeypatch.setattr(auth._token_validator,"verify_token",verify)


@pytest.mark.asyncio
async def test_reference_token_validates_after_gateway_restart_and_wrong_issuer_denied(config,monkeypatch):
    first=create_server(config,backend=StubBackend())
    token=await seed_reference(first.auth)
    second=create_server(config,backend=StubBackend())
    second.http_app(path="/mcp",stateless_http=True)
    mock_google(second.auth,config,monkeypatch)
    assert (await second.auth.verify_token(token)).claims["email"] == config.allowed_email
    expired=second.auth.jwt_issuer.issue_access_token(client_id="fixture-client",scopes=SCOPES,
                                                    jti="fixture-jti",expires_in=-60)
    assert await second.auth.verify_token(expired) is None
    changed=config.model_copy(update={"public_url":"https://other.example"})
    wrong=create_server(changed,backend=StubBackend())
    wrong.http_app(path="/mcp",stateless_http=True)
    assert await wrong.auth.verify_token(token) is None


@pytest.mark.asyncio
async def test_transparent_google_refresh_rotates_and_persists_without_model_calls(config,monkeypatch):
    server=create_server(config,backend=StubBackend())
    token=await seed_reference(server.auth,expired=True)
    mock_google(server.auth,config,monkeypatch)
    calls=[]
    class Upstream:
        async def refresh_token(self,**kwargs):
            calls.append(kwargs["refresh_token"])
            return {"access_token":"valid-google","refresh_token":"rotated-private-refresh","expires_in":600}
    @asynccontextmanager
    async def upstream(): yield Upstream()
    monkeypatch.setattr(server.auth,"_upstream_oauth_client",upstream)
    assert await server.auth.verify_token(token) is not None
    assert calls==["private-refresh"]
    state=await server.auth._upstream_token_store.get(key="upstream")
    assert state.refresh_token=="rotated-private-refresh"
    assert await server.auth.verify_token(token) is not None
    assert len(calls)==1


@pytest.mark.asyncio
async def test_authenticated_initialization_and_tools_over_real_http_asgi(config,monkeypatch):
    server=create_server(config,backend=StubBackend())
    token=await seed_reference(server.auth)
    mock_google(server.auth,config,monkeypatch)
    app=server.http_app(path="/mcp",stateless_http=True,json_response=True)
    with TestClient(app) as client:
        headers={"Authorization":"Bearer "+token,"Accept":"application/json, text/event-stream"}
        response=client.post("/mcp",headers=headers,json={"jsonrpc":"2.0","id":1,
            "method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},
            "clientInfo":{"name":"lanes-local-verifier","version":"1"}}})
        assert response.status_code==200
        headers["MCP-Protocol-Version"]="2025-03-26"
        result=client.post("/mcp",headers=headers,json={"jsonrpc":"2.0","id":2,"method":"tools/list"})
        assert result.status_code==200 and len(result.json()["result"]["tools"])==5
        called=client.post("/mcp",headers=headers,json={"jsonrpc":"2.0","id":3,"method":"tools/call",
            "params":{"name":"get_connection_status","arguments":{}}})
        assert called.status_code==200
        assert called.json()["result"]["structuredContent"]["operation"]=="connection"
