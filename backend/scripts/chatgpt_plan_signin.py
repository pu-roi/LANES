"""Serve a local sign-in page. No app.main, DB access, provider inference or ngrok."""
from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
import html
import os
from pathlib import Path
import secrets
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import httpx
import uvicorn

from app.services.chatgpt_plan_auth import CredentialStore, LocalChatGPTSignIn, SignInError


def page(message: str, form_token: str | None = None) -> str:
    action = (f'<form method="post" action="/connect"><input type="hidden" name="csrf" '
              f'value="{html.escape(form_token)}"><button type="submit">Continue with ChatGPT</button></form>'
              if form_token else '<p><a href="/">Return to connection status</a></p>')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>LANES ChatGPT connection</title></head><body><main>'
            '<h1>LANES ChatGPT connection</h1><p>' + html.escape(message) + '</p>' + action +
            '<p>This local pilot requests permission to use your ChatGPT plan. '
            'It does not run news audits or publish alerts. Usage remains subject to your plan limits.</p>'
            '</main></body></html>')


def create_app(directory: Path, port: int, transport: httpx.AsyncBaseTransport | None = None) -> FastAPI:
    origin = f"http://127.0.0.1:{port}"
    form_token = secrets.token_urlsafe(32)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False, trust_env=False,
                                     transport=transport) as client:
            app.state.signin = LocalChatGPTSignIn(CredentialStore(directory), origin + "/auth/callback", client)
            yield

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        if (request.headers.get("host") != f"127.0.0.1:{port}"
                or request.headers.get("origin", origin) != origin
                or (request.headers.get("sec-fetch-site") == "cross-site"
                    and request.url.path != "/auth/callback"
                    and not (request.method == "GET" and request.url.path == "/"
                             and request.headers.get("sec-fetch-mode") == "navigate"))):
            return JSONResponse({"error": "This helper accepts only local browser requests."}, status_code=403)
        response = await call_next(request)
        # Chrome serializes a form POST Origin as "null" under no-referrer.
        # The landing page needs same-origin for its protected local POST. Other
        # responses, especially OAuth callbacks containing codes, send no referrer.
        response.headers.update({"Cache-Control": "no-store", "Referrer-Policy":
            "same-origin" if request.url.path == "/" else "no-referrer",
            "X-Content-Type-Options": "nosniff", "Content-Security-Policy":
            "default-src 'none'; form-action 'self' https://auth.openai.com; frame-ancestors 'none'; base-uri 'none'"})
        return response

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request) -> str:
        status = request.app.state.signin.status()
        message = ("ChatGPT sign-in and plan permission were verified. News auditing has not been tested."
                   if status["connected"] and status["access_token_current"] else
                   "Sign in with your personal ChatGPT account to test whether its plan can authorize LANES.")
        return page(message, form_token)

    @app.get("/status")
    async def status(request: Request) -> dict:
        return request.app.state.signin.status()

    @app.post("/connect")
    async def connect(request: Request):
        # Bound streaming form size; no uploaded files, account override or arbitrary redirect.
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 1024:
                return HTMLResponse(page("The sign-in request was too large."), status_code=413)
        from urllib.parse import parse_qs
        try:
            values = parse_qs(body.decode(), strict_parsing=True)
            if values.keys() != {"csrf"} or values["csrf"] != [form_token]:
                raise ValueError()
        except (ValueError, UnicodeDecodeError):
            return HTMLResponse(page("The local sign-in request did not match this browser page."), status_code=403)
        try:
            url = request.app.state.signin.begin()
            return RedirectResponse(url, status_code=303)
        except SignInError as error:
            return HTMLResponse(page(str(error)), status_code=409)

    @app.get("/auth/callback", response_class=HTMLResponse)
    async def callback(request: Request):
        if len(request.scope["query_string"]) > 16384:
            return HTMLResponse(page("The callback was too large."), status_code=413)
        if len(request.query_params.multi_items()) != len(request.query_params):
            return HTMLResponse(page("The callback contained duplicate fields."), status_code=400)
        try:
            await request.app.state.signin.complete(dict(request.query_params))
            # Remove codes/state from the address bar before rendering connection status.
            return RedirectResponse(origin + "/", status_code=303)
        except SignInError as error:
            request.app.state.signin.error = error.code
            return HTMLResponse(page(str(error) + " Diagnostic code: " + error.code + "."), status_code=400)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=1455)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535 or os.name != "nt":
        parser.error("Use a Windows local port between 1024 and 65535.")
    directory = Path(os.environ["LOCALAPPDATA"]) / "LANES" / "ChatGPTPlan"
    app = create_app(directory, args.port)
    print(f"Open http://127.0.0.1:{args.port}/ in Chrome. No news requests will be sent.", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False,
                log_level="warning", proxy_headers=False)


if __name__ == "__main__":
    main()
