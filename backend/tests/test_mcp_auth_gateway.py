"""Signed per-request delegation and OAuth-protected curated transport."""
import hashlib
import json
import time
from types import SimpleNamespace

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastmcp import Client
from fastmcp.exceptions import ToolError
from jose import jwt

from app.api import mcp_review_deps as deps
from app.api.v1.endpoints.mcp_review import router
from app.core.mcp_review_config import MCPReviewSettings, MCP_ASSERTION_AUDIENCE
from app.mcp import server as gateway


@pytest.fixture
def config(tmp_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private = tmp_path / "private.pem"
    public = tmp_path / "public.pem"
    private.write_bytes(key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    public.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo))
    return MCPReviewSettings(_env_file=None, review_enabled=True, gateway_enabled=True,
        public_url="https://mcp.example", backend_url="https://backend.example",
        google_client_id="fixture-client", google_client_secret="synthetic-google-secret",
        allowed_google_subject="fixture-sub", allowed_email="staff@example.org",
        assertion_private_key_file=private, assertion_public_key_file=public,
        oauth_signing_key="synthetic-stable-signing-key-0123456789",
        oauth_storage_directory=tmp_path / "oauth", client_redirect_uris=["https://chatgpt.example/callback"])


def identity(config):
    return {"sub": config.allowed_google_subject, "email": config.allowed_email,
            "email_verified": True, "google_aud": config.google_client_id}


@pytest.fixture
def api(config, monkeypatch):
    user = SimpleNamespace(id=9, is_active=True, deleted_at=None,
        role=SimpleNamespace(name="Super Admin", permissions={"reports": "view"}))
    db = SimpleNamespace(scalar=lambda query: user)
    monkeypatch.setattr(deps, "mcp_settings", lambda: config)
    app = FastAPI()
    app.include_router(router, prefix=gateway.PREFIX)
    app.dependency_overrides[deps.review_db] = lambda: db
    return TestClient(app), user


def token(config, method="GET", suffix="connection", body=b"", **changes):
    now = int(time.time())
    payload = {**identity(config), "iss": config.public_url, "aud": MCP_ASSERTION_AUDIENCE,
        "iat": now, "exp": now+60, "method": method, "path": gateway.PREFIX+"/"+suffix,
        "body_sha256": hashlib.sha256(body).hexdigest(), **changes}
    return jwt.encode(payload, config.assertion_private_key_file.read_text(), algorithm="RS256")


def test_valid_reader_and_revoked_role_checked_each_request(config, api):
    client, user = api
    headers={"Authorization": "Bearer "+token(config)}
    assert client.get(gateway.PREFIX+"/connection", headers=headers).json()["account_id"] == 9
    user.role.permissions["reports"] = "none"
    assert client.get(gateway.PREFIX+"/connection", headers=headers).status_code == 403


@pytest.mark.parametrize("changes", [
    {"sub": "other"}, {"email": "other@example.org"}, {"email_verified": "true"},
    {"google_aud": "other"}, {"iss": "https://other.example"}, {"aud": "other"},
    {"exp": 1}, {"method": "POST"}, {"path": "/other"}, {"body_sha256": "0"*64},
    {"iat": 1, "exp": int(time.time())+60}, {"exp": int(time.time())+600},
])
def test_bad_actor_signature_claims_or_request_binding_denied(config, api, changes):
    client, _ = api
    assert client.get(gateway.PREFIX+"/connection",
        headers={"Authorization": "Bearer "+token(config, **changes)}).status_code == 401


@pytest.mark.parametrize("state", ["inactive", "deleted", "commuter"])
def test_unavailable_account_denied_without_mutation(config, api, state):
    client, user = api
    if state == "inactive": user.is_active=False
    elif state == "deleted": user.deleted_at="historical"
    else: user.role.name="Commuter"
    assert client.get(gateway.PREFIX+"/connection",
        headers={"Authorization": "Bearer "+token(config)}).status_code == 403


def test_disabled_missing_token_and_normal_lanes_jwt_rejected(config, api):
    client, _ = api
    assert client.get(gateway.PREFIX+"/connection").status_code == 401
    wrong = jwt.encode({"sub": "9", "exp": int(time.time())+60}, "synthetic-lanes-key", algorithm="HS256")
    assert client.get(gateway.PREFIX+"/connection", headers={"Authorization": "Bearer "+wrong}).status_code == 401
    config.review_enabled=False
    assert client.get(gateway.PREFIX+"/connection", headers={"Authorization": "Bearer "+token(config)}).status_code == 404


@pytest.mark.parametrize("body,status", [(b'{"actor":99}',422), (b'{"bundle":{},"bundle":{}}',422),
                                        (b'{"bundle":',422), (b'x'*65537,413)],
                         ids=["actor_injection", "duplicate_json", "truncated", "oversized"])
def test_preview_body_limits_and_unsafe_json(config, api, body, status):
    client, _ = api
    assert client.post(gateway.PREFIX+"/preview", content=body,
        headers={"Authorization": "Bearer "+token(config,"POST","preview",body)}).status_code == status


@pytest.mark.parametrize("change", ["subject", "email", "verified", "audience"])
def test_gateway_google_identity_cannot_be_replaced(config, change):
    claims = {"sub": config.allowed_google_subject, "email": config.allowed_email,
              "email_verified": True, "aud": config.google_client_id}
    fields={"subject":"sub","email":"email","verified":"email_verified","audience":"aud"}
    claims[fields[change]]="other"
    with pytest.raises(ToolError): gateway.checked_identity(claims,config)


class StubBackend:
    async def call(self, suffix, **kwargs): return {"operation": suffix, "preview_only": True}


@pytest.mark.asyncio
async def test_exact_five_tools_discovered_and_preview_is_read_only(config):
    server=gateway.create_server(config, backend=StubBackend())
    async with Client(server) as client:
        tools=await client.list_tools()
        assert {t.name for t in tools} == {"get_connection_status","list_saved_news","get_claim_evidence",
                                          "get_audit_bundle","preview_audit_proposal"}
        assert all(t.annotations.read_only_hint and not t.annotations.destructive_hint for t in tools)
        result=await client.call_tool("get_connection_status",{})
        assert result.data["operation"]=="connection"


def test_http_discovery_and_unauthenticated_tool_access(config):
    server=gateway.create_server(config, backend=StubBackend())
    app=server.http_app(path="/mcp",stateless_http=True)
    with TestClient(app) as client:
        assert client.get("/.well-known/oauth-authorization-server").status_code==200
        metadata=client.get("/.well-known/oauth-protected-resource/mcp")
        assert metadata.status_code==200
        assert metadata.json()["resource"]==config.public_url+"/mcp"
        response=client.post("/mcp",json={"jsonrpc":"2.0","id":1,"method":"tools/list"})
        assert response.status_code==401
        assert "resource_metadata" in response.headers["www-authenticate"]


@pytest.mark.asyncio
async def test_backend_allowlist_signed_query_and_safe_error(config,monkeypatch):
    claims={"sub":config.allowed_google_subject,"email":config.allowed_email,
            "email_verified":True,"aud":config.google_client_id}
    monkeypatch.setattr(gateway,"get_access_token",lambda:SimpleNamespace(claims=claims))
    def respond(request):
        payload=jwt.decode(request.headers["authorization"][7:],config.assertion_public_key_file.read_text(),
                           algorithms=["RS256"],audience=MCP_ASSERTION_AUDIENCE,issuer=config.public_url)
        assert payload["path"]==request.url.raw_path.decode()
        assert payload["body_sha256"]==hashlib.sha256(request.content).hexdigest()
        return httpx.Response(503,json={"detail":"secret-provider-body"})
    backend=gateway.Backend(config,httpx.MockTransport(respond))
    with pytest.raises(ToolError,match="temporarily unavailable"):
        await backend.call("bundle",params=[("run_id",1),("claim_indexes",2),("claim_indexes",5)])
    with pytest.raises(ToolError,match="Unsupported"): await backend.call("runs")


@pytest.mark.asyncio
async def test_oauth_storage_encrypted_and_reopens_with_stable_key(config):
    first=gateway.create_server(config,backend=StubBackend())
    await first.auth._client_storage.put(key="fixture",value={"refresh_token":"private-refresh-value"})
    files=list(config.oauth_storage_directory.rglob("*"))
    assert files and all(b"private-refresh-value" not in p.read_bytes() for p in files if p.is_file())
    second=gateway.create_server(config,backend=StubBackend())
    assert (await second.auth._client_storage.get(key="fixture"))["refresh_token"]=="private-refresh-value"


@pytest.mark.parametrize("field",["gateway_enabled","client_redirect_uris","oauth_signing_key","allowed_google_subject"])
def test_gateway_missing_configuration_fails_closed(config,field):
    value=False if field=="gateway_enabled" else [] if field=="client_redirect_uris" else ""
    changed=config.model_copy(update={field:value})
    if field=="oauth_signing_key":
        from pydantic import SecretStr
        changed.oauth_signing_key=SecretStr("")
    with pytest.raises(ValueError): gateway.create_server(changed)
