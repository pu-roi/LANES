"""Local SIWC registration only; independent of LANES login, databases and inference."""
from __future__ import annotations

import base64
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import time
from typing import Any
from urllib.parse import urlencode, urlsplit
import uuid

import httpx
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError

ISSUER = "https://auth.openai.com"
RESOURCE = "https://api.openai.com/v1"
AUTHORIZE = ISSUER + "/api/accounts/authorize"
TOKEN = ISSUER + "/api/accounts/oauth/token"
SCOPES = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct"
REVISION = "chatgpt-local-signin-v3-token-binding"


class SignInError(Exception):
    """Contains only a public, actionable error; never provider bodies or credentials."""

    def __init__(self, message: str, code: str = "signin_failed") -> None:
        super().__init__(message)
        self.code = code


def windows_protect(data: bytes, *, decrypt: bool = False) -> bytes:
    """Windows DPAPI CurrentUser protection; credentials cannot be moved to another user."""
    if os.name != "nt":
        raise SignInError("This local sign-in helper requires Windows credential protection.")

    class Blob(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    function = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                         ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    # CRYPTPROTECT_UI_FORBIDDEN, without CRYPTPROTECT_LOCAL_MACHINE.
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise SignInError("Windows could not protect or unlock the local credential file.")
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree.restype = ctypes.c_void_p
        kernel.LocalFree(target.data)


class CredentialStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory.resolve()

    def path(self, name: str) -> Path:
        return self.directory / name

    def load(self, name: str) -> dict[str, Any] | None:
        path = self.path(name)
        if not path.exists():
            return None
        try:
            if path.stat().st_size > 65536:
                raise SignInError("The local credential file is too large.")
            value = json.loads(windows_protect(path.read_bytes(), decrypt=True))
            if not isinstance(value, dict):
                raise ValueError()
            return value
        except SignInError:
            raise
        except (ValueError, OSError):
            raise SignInError("The local credential file could not be read.") from None

    def save(self, name: str, value: dict[str, Any]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        encrypted = windows_protect(json.dumps(value).encode())
        temporary = self.path(name + "." + secrets.token_hex(8) + ".tmp")
        try:
            with temporary.open("xb") as file:
                file.write(encrypted)
                file.flush()
                os.fsync(file.fileno())
            temporary.replace(self.path(name))
        finally:
            temporary.unlink(missing_ok=True)


class LocalChatGPTSignIn:
    def __init__(self, store: CredentialStore, callback_uri: str, client: httpx.AsyncClient) -> None:
        parsed = urlsplit(callback_uri)
        if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
                or parsed.path != "/auth/callback" or not parsed.port
                or parsed.query or parsed.fragment or parsed.username):
            raise ValueError("An exact IPv4 loopback callback is required.")
        self.store = store
        self.callback_uri = callback_uri
        self.client = client
        self.pending: dict[str, Any] | None = None
        self.error: str | None = None
        self.host: dict[str, Any] = store.load("host.dpapi") or {
            "ext_agent_host_id": "urn:uuid:" + str(uuid.uuid4())}
        store.save("host.dpapi", self.host)
        # This pilot binds one explicitly selected account. It never auto-switches identities.
        self.account = store.load("account.dpapi")

    def begin(self) -> str:
        if self.pending and self.pending["expires_at"] > time.time():
            raise SignInError("A sign-in is already in progress. Finish it or wait ten minutes.")
        self.error = None
        verifier = secrets.token_urlsafe(48)
        self.pending = {
            "state": secrets.token_urlsafe(32), "nonce": secrets.token_urlsafe(32),
            "verifier": verifier, "expires_at": time.time() + 600,
            "client_id": self.account["client_id"] if self.account else "dynamic_agent_client",
        }
        query = {
            "client_id": self.pending["client_id"],
            "ext_agent_host_id": self.host["ext_agent_host_id"],
            "response_type": "code", "redirect_uri": self.callback_uri,
            "scope": SCOPES, "resource": RESOURCE, "state": self.pending["state"],
            "nonce": self.pending["nonce"], "code_challenge_method": "S256",
            "code_challenge": base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("="),
        }
        if self.account:
            query["id_token_hint"] = self.account["id_token"]
        else:
            query["agent_name_hint"] = "LANES News Auditor"
        return AUTHORIZE + "?" + urlencode(query)

    async def _json(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        try:
            async with self.client.stream(method, url, **kwargs) as response:
                if response.status_code != 200:
                    raise SignInError("OpenAI did not accept the sign-in request. Start a fresh sign-in.")
                data = bytearray()
                async for chunk in response.aiter_bytes():
                    data.extend(chunk)
                    if len(data) > 65536:
                        raise SignInError("OpenAI returned an oversized sign-in response.")
                result = json.loads(data)
                if not isinstance(result, dict):
                    raise ValueError()
                return result
        except (httpx.HTTPError, ValueError):
            raise SignInError("OpenAI sign-in could not finish. Check the connection and start again.") from None

    async def complete(self, query: dict[str, str]) -> dict[str, Any]:
        pending = self.pending
        if (not pending or pending["expires_at"] <= time.time()
                or not secrets.compare_digest(query.get("state", "").encode(), pending["state"].encode())):
            raise SignInError("The sign-in callback is expired or does not match this attempt.")
        # Consume before exchanging: callback replay cannot trigger another token exchange.
        self.pending = None
        if query.get("error"):
            raise SignInError("ChatGPT authorization was declined or unavailable. No account was connected.")
        client_id = query.get("client_id", pending["client_id"])
        if (not re.fullmatch(r"[A-Za-z0-9._:-]{1,256}", client_id) or client_id == "dynamic_agent_client"
                or (self.account and client_id != self.account["client_id"])):
            raise SignInError("OpenAI did not return the expected registered client identity.")
        code = query.get("code", "")
        if not code or len(code) > 8192:
            raise SignInError("The sign-in callback did not contain a valid authorization code.")
        tokens = await self._json("POST", TOKEN, data={
            "grant_type": "authorization_code", "client_id": client_id, "code": code,
            "code_verifier": pending["verifier"], "redirect_uri": self.callback_uri,
            "resource": RESOURCE,
        })
        discovery = await self._json("GET", ISSUER + "/.well-known/openid-configuration")
        jwks_uri = discovery.get("jwks_uri", "")
        location = urlsplit(jwks_uri)
        if (discovery.get("issuer") != ISSUER or location.scheme != "https"
                or location.netloc != "auth.openai.com" or location.fragment or location.query):
            raise SignInError("OpenAI identity discovery could not be verified.")
        keys = await self._json("GET", jwks_uri)
        id_token = tokens.get("id_token")
        if not isinstance(id_token, str) or not id_token:
            raise SignInError("OpenAI did not return an identity token. No credentials were saved.", "id_token_missing")
        try:
            header = jwt.get_unverified_header(id_token)
        except JWTError:
            raise SignInError("OpenAI returned an unreadable identity token. No credentials were saved.", "id_token_malformed") from None
        if header.get("alg") != "RS256":
            raise SignInError("The identity token uses an unsupported signing algorithm. No credentials were saved.", "id_token_algorithm")
        try:
            key = next(key for key in keys["keys"] if key.get("kid") == header.get("kid")
                       and key.get("kty") == "RSA" and key.get("use", "sig") == "sig"
                       and key.get("alg", "RS256") == "RS256")
        except (KeyError, TypeError, StopIteration):
            raise SignInError("The identity signing key was not in OpenAI's published keys. No credentials were saved.", "id_token_key_not_found") from None
        try:
            identity = jwt.decode(id_token, key, algorithms=["RS256"], audience=client_id,
                access_token=tokens.get("access_token") if isinstance(tokens.get("access_token"), str) else None,
                issuer=ISSUER, options={"require_exp": True, "require_iat": True,
                                      "require_sub": True, "leeway": 5})
        except ExpiredSignatureError:
            raise SignInError("The identity token is expired. Check the computer clock and sign in again.", "id_token_expired") from None
        except JWTClaimsError as error:
            # Library diagnostics are mapped to fixed codes, never echoed as raw text.
            reason = str(error)
            code = {"Invalid audience": "id_token_audience", "Invalid issuer": "id_token_issuer",
                "Invalid claim format in token": "id_token_audience_format",
                "Issued At claim (iat) must be an integer.": "id_token_issue_time",
                "Not Before claim (nbf) must be an integer.": "id_token_not_before",
                "The token is not yet valid (nbf)": "id_token_not_before",
                "Expiration Time claim (exp) must be an integer.": "id_token_expiry_format",
                "Subject must be a string.": "id_token_subject",
                "JWT ID must be a string.": "id_token_jti_format",
                "No access_token provided to compare against at_hash claim.": "id_token_access_hash_input",
                "Unable to calculate at_hash to verify against token claims.": "id_token_access_hash_input",
                "at_hash claim does not match access_token.": "id_token_access_hash_mismatch",
            }.get(reason, "id_token_claims")
            raise SignInError("The identity token did not match LANES's registered sign-in identity. No credentials were saved.", code) from None
        except (JWTError, ValueError, TypeError):
            raise SignInError("The identity signature or required claims could not be verified. No credentials were saved.", "id_token_signature_or_claims") from None
        if not isinstance(identity.get("sub"), str) or not identity["sub"]:
            raise SignInError("The verified identity token did not contain an account identity.", "id_token_subject")
        nonce = identity.get("nonce")
        if not isinstance(nonce, str) or not secrets.compare_digest(nonce.encode(), pending["nonce"].encode()):
            raise SignInError("The identity token did not match this sign-in attempt. No credentials were saved.", "id_token_nonce")
        if not isinstance(identity.get("iat"), (int, float)) or identity["iat"] > time.time() + 5:
            raise SignInError("The identity token's issue time is invalid. Check the computer clock.", "id_token_issue_time")
        if self.account and identity["sub"] != self.account["subject"]:
            raise SignInError("The signed-in account differs from the previously connected account.", "account_mismatch")
        scope_text = tokens.get("scope")
        if not isinstance(scope_text, str):
            raise SignInError("OpenAI did not return the granted permissions. No credentials were saved.", "granted_scopes_missing")
        scopes = scope_text.split()
        if "chatgpt.tokens.use.direct" not in scopes:
            raise SignInError("Your identity was verified, but permission to use your ChatGPT plan was not granted. No credentials were saved.", "plan_scope_missing")
        if "resource.invoke" not in scopes:
            raise SignInError("Your identity was verified, but model-request permission was not granted. No credentials were saved.", "invoke_scope_missing")
        if "offline_access" not in scopes:
            raise SignInError("Your identity was verified, but renewable access was not granted. No credentials were saved.", "offline_scope_missing")
        if (not isinstance(tokens.get("token_type"), str) or tokens["token_type"].lower() != "bearer"
                or not isinstance(tokens.get("access_token"), str) or not tokens["access_token"]
                or not isinstance(tokens.get("refresh_token"), str) or not tokens["refresh_token"]
                or type(tokens.get("expires_in")) is not int or tokens["expires_in"] <= 0):
            raise SignInError("OpenAI did not return a complete renewable token set. No credentials were saved.", "token_fields_invalid")
        account = {
            "issuer": ISSUER, "subject": identity["sub"], "email": identity.get("email"),
            "client_id": client_id, "ext_agent_host_id": self.host["ext_agent_host_id"],
            "id_token": id_token, "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"], "token_type": "Bearer", "scopes": scopes,
            "saved_at": int(time.time()), "expires_at": int(time.time()) + tokens["expires_in"],
            "revision": REVISION,
        }
        self.store.save("account.dpapi", account)
        self.account = account
        return self.status()

    def status(self) -> dict[str, Any]:
        return {"connected": self.account is not None,
                "plan_permission_verified": bool(self.account and "chatgpt.tokens.use.direct" in self.account["scopes"]),
                "access_token_current": bool(self.account and self.account["expires_at"] > time.time()),
                "inference_verified": False, "news_worker_enabled": False,
                "last_error_code": self.error,
                "revision": REVISION}
