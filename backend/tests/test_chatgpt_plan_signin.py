"""Offline OAuth proof with synthetic signed identities. No real OpenAI/DB requests."""
import base64
import hashlib
import json
import os
import re
import time
from urllib.parse import parse_qs, urlsplit

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
import httpx
from jose import jwk, jwt
import pytest

from app.services.chatgpt_plan_auth import CredentialStore, LocalChatGPTSignIn, SignInError, ISSUER, windows_protect
from scripts.chatgpt_plan_signin import create_app


pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows-only encrypted credential pilot")


@pytest.fixture
def provider():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption())
    public = key.public_key().public_bytes(serialization.Encoding.PEM,
                                           serialization.PublicFormat.SubjectPublicKeyInfo)
    jwks = jwk.construct(public, "RS256").to_dict()
    jwks.update(kid="fixture-key", use="sig", alg="RS256")
    state = {"nonce": "", "requests": [], "claims": {}, "token_changes": {}}

    def handler(request):
        state["requests"].append((request.method, str(request.url), request.content))
        if request.url.path == "/api/accounts/oauth/token":
            body = parse_qs(request.content.decode())
            assert body["grant_type"] == ["authorization_code"]
            assert body["client_id"] == ["oaiapp_fixture"]
            assert body["redirect_uri"] == ["http://127.0.0.1:1455/auth/callback"]
            assert "client_secret" not in body
            claims = {"sub": "fixture-user", "email": "fixture@example.org", "iat": int(time.time()),
                      "exp": int(time.time()) + 3600, "iss": ISSUER, "aud": "oaiapp_fixture",
                      "at_hash": base64.urlsafe_b64encode(hashlib.sha256(b"fixture-access").digest()[:16]).decode().rstrip("="),
                      "nonce": state["nonce"], **state["claims"]}
            if state.get("omit_at_hash"):
                claims.pop("at_hash")
            token = jwt.encode(claims, private, algorithm="RS256", headers={"kid": "fixture-key"})
            return httpx.Response(200, json={"id_token": token, "access_token": "fixture-access",
                "refresh_token": "fixture-refresh", "token_type": "Bearer", "expires_in": 3600,
                "scope": "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct",
                **state["token_changes"]})
        if request.url.path == "/.well-known/openid-configuration":
            return httpx.Response(200, json={"issuer": ISSUER,
                "jwks_uri": ISSUER + "/.well-known/jwks.json"})
        if request.url.path == "/.well-known/jwks.json":
            return httpx.Response(200, json={"keys": [jwks]})
        raise AssertionError("Unexpected request: inference and DB operations are forbidden")

    return state, httpx.MockTransport(handler)


def start(client, state):
    document = client.get("/")
    token = re.search(r'name="csrf" value="([^"]+)"', document.text).group(1)
    response = client.post("/connect", data={"csrf": token}, follow_redirects=False)
    assert response.status_code == 303
    query = parse_qs(urlsplit(response.headers["location"]).query)
    state["nonce"] = query["nonce"][0]
    return query


def callback(client, query, **changes):
    return client.get("/auth/callback", params={"code": "fixture-code", "client_id": "oaiapp_fixture",
        "state": query["state"][0], **changes}, follow_redirects=False)


def test_success_restart_encryption_and_no_inference(tmp_path, provider):
    state, transport = provider
    with TestClient(create_app(tmp_path, 1455, transport), base_url="http://127.0.0.1:1455") as client:
        query = start(client, state)
        assert query["client_id"] == ["dynamic_agent_client"]
        assert query["agent_name_hint"] == ["LANES News Auditor"]
        assert query["code_challenge_method"] == ["S256"]
        assert callback(client, query).status_code == 303
        status = client.get("/status").json()
        assert status["connected"] and status["plan_permission_verified"]
        assert not status["inference_verified"] and not status["news_worker_enabled"]
        assert "fixture-access" not in client.get("/").text
        assert "fixture-access" not in client.get("/status").text
        saved = CredentialStore(tmp_path).load("account.dpapi")
        assert saved["access_token"] == "fixture-access"
        assert b"fixture-access" not in (tmp_path / "account.dpapi").read_bytes()
        original_host = saved["ext_agent_host_id"]
        assert callback(client, query).status_code == 400
        assert len(state["requests"]) == 3
    with TestClient(create_app(tmp_path, 1455, transport), base_url="http://127.0.0.1:1455") as client:
        query = start(client, state)
        assert query["client_id"] == ["oaiapp_fixture"]
        assert query["ext_agent_host_id"] == [original_host]
        assert "id_token_hint" in query and "agent_name_hint" not in query
        assert callback(client, query).status_code == 303


@pytest.mark.parametrize("changes", [{"state": "wrong"}, {"state": "非ASCII"},
    {"error": "access_denied"}, {"client_id": "dynamic_agent_client"}, {"client_id": ""}, {"code": ""}])
def test_rejected_callbacks_never_exchange(tmp_path, provider, changes):
    state, transport = provider
    with TestClient(create_app(tmp_path, 1455, transport), base_url="http://127.0.0.1:1455") as client:
        query = start(client, state)
        assert callback(client, query, **changes).status_code == 400
        assert state["requests"] == []
        assert not (tmp_path / "account.dpapi").exists()


@pytest.mark.parametrize("changes", [{"nonce": "wrong"}, {"nonce": 42}, {"aud": "other-client"},
    {"iss": "https://other.example"}, {"exp": 1}, {"iat": int(time.time()) + 3600}, {"sub": ""}])
def test_identity_rejections(tmp_path, provider, changes):
    state, transport = provider
    state["claims"] = changes
    with TestClient(create_app(tmp_path, 1455, transport), base_url="http://127.0.0.1:1455") as client:
        query = start(client, state)
        response = callback(client, query)
        assert response.status_code == 400
        assert "fixture-access" not in response.text
        assert not (tmp_path / "account.dpapi").exists()


@pytest.mark.parametrize("changes", [{"scope": "openid profile email"}, {"refresh_token": ""},
    {"expires_in": "3600"}, {"access_token": None}, {"token_type": "other"}, {"id_token": "malformed.jwt"}])
def test_missing_plan_permission_or_bad_tokens(tmp_path, provider, changes):
    state, transport = provider
    state["token_changes"] = changes
    with TestClient(create_app(tmp_path, 1455, transport), base_url="http://127.0.0.1:1455") as client:
        query = start(client, state)
        assert callback(client, query).status_code == 400
        assert not (tmp_path / "account.dpapi").exists()


def test_wrong_host_origin_csrf_duplicates_and_expiry(tmp_path, provider):
    state, transport = provider
    with TestClient(create_app(tmp_path, 1455, transport), base_url="http://127.0.0.1:1455") as client:
        assert client.get("/", headers={"Host": "attacker.example"}).status_code == 403
        assert client.post("/connect", headers={"Origin": "https://attacker.example"}).status_code == 403
        assert client.post("/connect", headers={"Origin": "null"}).status_code == 403
        assert client.post("/connect", data={"csrf": "bad"}).status_code == 403
        assert client.post("/connect", content=b"x" * 1025).status_code == 413
        assert client.get("/", headers={"Sec-Fetch-Site": "cross-site", "Sec-Fetch-Mode": "navigate"}).status_code == 200
        query = start(client, state)
        assert client.post("/connect", data={"csrf": re.search(r'name="csrf" value="([^"]+)"', client.get("/").text).group(1)}).status_code == 409
        assert client.get("/auth/callback?state=a&state=b").status_code == 400
        assert client.get("/auth/callback?state=" + "a"*17000).status_code == 413
        client.app.state.signin.pending["expires_at"] = 1
        assert callback(client, query).status_code == 400
        assert not state["requests"]


def test_form_referrer_preserves_origin_without_leaking_callback(tmp_path, provider):
    state, transport = provider
    with TestClient(create_app(tmp_path, 1455, transport), base_url="http://127.0.0.1:1455") as client:
        response = client.get("/")
        assert response.headers["referrer-policy"] == "same-origin"
        token = re.search(r'name="csrf" value="([^"]+)"', response.text).group(1)
        response = client.post("/connect", data={"csrf": token},
            headers={"Origin": "http://127.0.0.1:1455"}, follow_redirects=False)
        assert response.status_code == 303
        query = parse_qs(urlsplit(response.headers["location"]).query)
        state["nonce"] = query["nonce"][0]
        response = callback(client, query)
        assert response.status_code == 303
        assert response.headers["referrer-policy"] == "no-referrer"
        assert client.get("/status").headers["referrer-policy"] == "no-referrer"


def test_other_account_does_not_replace_original(tmp_path, provider):
    state, transport = provider
    with TestClient(create_app(tmp_path, 1455, transport), base_url="http://127.0.0.1:1455") as client:
        query = start(client, state)
        assert callback(client, query).status_code == 303
        old = (tmp_path / "account.dpapi").read_bytes()
        query = start(client, state)
        state["claims"] = {"sub": "another-user"}
        assert callback(client, query).status_code == 400
        assert (tmp_path / "account.dpapi").read_bytes() == old


def test_provider_errors_are_safe(tmp_path):
    def provider(request):
        return httpx.Response(429, json={"error": "secret-provider-detail"})
    with TestClient(create_app(tmp_path, 1455, httpx.MockTransport(provider)), base_url="http://127.0.0.1:1455") as client:
        query = start(client, {})
        response = callback(client, query)
        assert response.status_code == 400 and "secret-provider-detail" not in response.text
        assert not (tmp_path / "account.dpapi").exists()


def test_dpapi_round_trip():
    protected = windows_protect(b"synthetic-local-secret")
    assert b"synthetic-local-secret" not in protected
    assert windows_protect(protected, decrypt=True) == b"synthetic-local-secret"
    with pytest.raises(SignInError):
        windows_protect(b"invalid-protected-record", decrypt=True)


@pytest.mark.parametrize("claim_changes,token_changes,expected", [
    ({"aud": "wrong"}, {}, "id_token_audience"),
    ({"iss": "https://wrong.example"}, {}, "id_token_issuer"),
    ({"nonce": None}, {}, "id_token_nonce"),
    ({"exp": 1}, {}, "id_token_expired"),
    ({}, {"id_token": "broken.jwt"}, "id_token_malformed"),
    ({}, {"id_token": None}, "id_token_missing"),
    ({}, {"scope": "openid profile email"}, "plan_scope_missing"),
    ({}, {"scope": "openid profile email chatgpt.tokens.use.direct offline_access"}, "invoke_scope_missing"),
    ({}, {"scope": None}, "granted_scopes_missing"),
    ({}, {"refresh_token": None}, "token_fields_invalid"),
])
def test_failure_codes_explain_stage_without_secrets(tmp_path, provider, claim_changes, token_changes, expected):
    state, transport = provider
    state["claims"] = claim_changes
    state["token_changes"] = token_changes
    with TestClient(create_app(tmp_path, 1455, transport), base_url="http://127.0.0.1:1455") as client:
        query = start(client, state)
        response = callback(client, query)
        assert response.status_code == 400
        assert "Diagnostic code: " + expected in response.text
        result = client.get("/status")
        assert result.json()["last_error_code"] == expected
        for secret in ["fixture-access", "fixture-refresh", "fixture-user", state["nonce"]]:
            assert secret not in response.text and secret not in result.text
        assert not (tmp_path / "account.dpapi").exists()
        start(client, state)
        assert client.get("/status").json()["last_error_code"] is None


@pytest.mark.parametrize("claims,tokens,expected", [
    ({"at_hash": "incorrect"}, {}, "id_token_access_hash_mismatch"),
    ({}, {"access_token": "different-token"}, "id_token_access_hash_mismatch"),
    ({}, {"access_token": None}, "id_token_access_hash_input"),
    ({"nbf": int(time.time()) + 3600}, {}, "id_token_not_before"),
    ({"nbf": "invalid"}, {}, "id_token_not_before"),
    ({"jti": 42}, {}, "id_token_jti_format"),
])
def test_token_binding_and_optional_claims(tmp_path, provider, claims, tokens, expected):
    state, transport = provider
    state["claims"] = claims
    state["token_changes"] = tokens
    with TestClient(create_app(tmp_path, 1455, transport), base_url="http://127.0.0.1:1455") as client:
        query = start(client, state)
        assert callback(client, query).status_code == 400
        assert client.get("/status").json()["last_error_code"] == expected
        assert not (tmp_path / "account.dpapi").exists()


def test_optional_access_hash_absence_is_supported(tmp_path, provider):
    state, transport = provider
    state["omit_at_hash"] = True
    with TestClient(create_app(tmp_path, 1455, transport), base_url="http://127.0.0.1:1455") as client:
        query = start(client, state)
        assert callback(client, query).status_code == 303
