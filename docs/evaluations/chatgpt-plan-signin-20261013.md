# ChatGPT plan sign-in and MCP implementation checks

> **State:** Real ChatGPT plan authorization verified; subsequent news inference fails full evidence qualification. MCP connection and production acceptance remain pending.
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

The developer clarified that the goal is automatic news auditing using their ChatGPT plan. The earlier Google OAuth/ngrok gateway implements interactive read/preview tools only and remains disabled; it is preserved. Added a separate local Windows sign-in helper using the documented SIWC dynamic client flow. It makes no inference requests or database calls and does not replace the provider configuration.

## Measured sign-in checks

- Initial suite: 23 passing offline checks. Final combined suite: **88 passed**, comprising 24 local sign-in checks and 64 MCP review/auth/transport checks, launched through dotenvx in `backend/.venv`.
- Actual Windows DPAPI round trip; synthetic credentials are encrypted at rest. Restart preserves host/client identity. Verified issuer, audience, signature/expiry/nonce, granted plan scopes, valid token fields and original account binding. Invalid state, Unicode state, denial, malformed identity tokens, missing registration/scopes, callback replay, duplicate parameters, wrong host/origin and oversized input are rejected without saving unvalidated credentials.
- Mock transport only for token exchange/JWKS tests. No model/Responses request is possible through this helper. Safe error pages/status omit tokens and upstream bodies.
- Actual local loopback process listens on 127.0.0.1:1455. Status before user authorization: connected=false, plan_permission_verified=false, inference_verified=false, news_worker_enabled=false.
- Desktop and mobile **Chromium**: two passing browser checks, both screenshots inspected. Button/instructions visible, no horizontal overflow. Initial mobile project selected WebKit via its iPhone device preset; the WebKit executable exited before page loading. This helper's test explicitly selects Chromium while retaining both viewport/device profiles. No Safari/WebKit success is claimed.
- `git diff --check` passed. No SQLAlchemy models/migrations or new dependency for this helper. HTTPX, python-jose and standard-library Windows protection are reused. Google OAuth/ngrok configuration is preserved. No Git push or cloud deployment.

## Earlier shared-upgrade implementation evidence

The developer selected shared requirements rather than the initially recommended isolated gateway dependency environment. The candidate uses Python 3.12 with FastAPI 0.143.0, Pydantic 2.14.1, Starlette 1.7.0, Uvicorn 0.54.0, FastMCP 4.1.0 and MCP 2.3.0; original development venv retained. Fresh candidate install/pip check succeeded. Canonical audit and Gemini profile schemas are byte-for-byte equivalent after upgrade. 258 focused existing provider/quota/weather/recovery tests passed. A broader news run had 1007 passes, 266 skips and five failures; the same five failures were reproduced on the original framework environment. They remain unresolved baseline failures, not upgraded acceptance passes.

Previous existing desktop/mobile application flow checks passed 16 tests. Native osmium imports are blocked by Windows Application Control in the candidate. Docker startup is blocked by stale runtime sockets; automatic review rejected the recovery command with only “blocked by policy.” Linux image, fresh PostGIS migration/read-only/worker ownership checks and full shared-upgrade acceptance remain pending. No workaround deleting runtime sockets was executed.

The five MCP tools and strict backend preview are implemented locally, but their real authenticated ChatGPT connection is not established. Google client credentials and ngrok were configured privately; Google subject/account binding and ChatGPT callback allowlist remain incomplete. They do not grant ChatGPT plan usage.

## Remaining gates

User completes personal ChatGPT authorization; verify account-specific model availability; qualify five bounded original-evidence inference cases; implement refresh/recovery and a separately identified provider adapter if qualified. Never persist a ChatGPT result as OpenRouter/Gemini or alter terminal evaluations. Cloud hosting eligibility and production worker/publication acceptance remain separate. [Local runbook](../guides/chatgpt-plan-local-signin.md).

## Follow-up: Chrome Continue form rejected

The user reported HTTP 403 after clicking Continue. Actual local Chrome reproduction (all OpenAI navigation intercepted) proved Origin: null, caused by no-referrer policy. Landing page now uses same-origin policy; callback/status keep no-referrer. Null/foreign origins remain denied. New checks exercise actual browser clicks without starting an OAuth attempt and verify local form acceptance/callback privacy in the backend. Previous 88/2 checks are historical counts; the final focused rerun passed 25 backend checks and four desktop/mobile Chromium checks. Actual account authorization is still pending. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Real callback diagnostic follow-up

The user returned from OpenAI to a combined identity/permission rejection. Exact cause is unknown; invalid tokens were not retained. Added fixed codes for missing/malformed tokens, signing-key/signature/claims, issuer/audience/expiry/nonce, account binding, granted scopes and token fields. No check bypassed or unvalidated credential saved. 35 focused tests pass (ten diagnostic cases). Corrected an exception import exposed by the initial test collection. Automatic review rejected the combined stop/restart/documentation command with blocked by policy; it did not execute. Launched a new helper safely on port 1456; original 1455 left running. Real account authorization and inference remain unverified. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## at_hash-bearing identity token compatibility

Actual user reported id_token_claims. Inspection of installed python-jose shows missing access_token raises JWTClaimsError when optional at_hash is present. The helper omitted that argument; previous signed fixtures omitted this standard optional claim. Adding a valid independently calculated at_hash reproduces a failing success test before repair. Passing the returned access token into JWT validation restores success; 42 focused tests pass, including missing optional claim, wrong hash, changed/missing access token and optional nbf/jti diagnostics. Do not infer the exact real-token claim from this reproduction: discarded credentials cannot be inspected. New v3 helper runs on 1457; actual authorization is pending. [OpenID token binding specification](https://openid.net/specs/openid-connect-core-1_0.html#CodeIDToken). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Real sign-in subsequently verified

The user completed authorization on v3 port 1457. Current runtime status confirms connected and granted plan permission, with unexpired credentials. This closes the local sign-in gate but not actual MCP discovery/tool calls. Subsequent real Responses requests and incomplete news qualification are recorded in [the live evaluation](chatgpt-news-live-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Senior-planner pre-push checkpoint

Developer explicitly requested updating documentation and pushing all local work to roi-branch. Remote fetch shows no divergence. Final combined run: **129 passed, one skipped** (fresh guarded PostGIS requires unavailable Docker). Final opt-in helper Chromium checks: **four passed**, desktop/mobile. Initial pre-push browser retry failed connection-refused because the helper was stopped; starting the loopback process restored all checks. Browser spec is now explicit LANES_CHATGPT_SIGNIN_URL opt-in so normal LANES test runs do not depend on it. Windows-only credential sign-in is separate from production app UI.

Python dependency check, AST parse, new documentation links and git diff --check pass. Direct cryptography import is recorded at installed 50.0.2; all new gateway/runtime imports are in the shared manifest. SQLAlchemy/Alembic definitions and existing Cloud Build configuration are unchanged. No new migration to test; existing Alembic upgrade on a fresh local PostGIS under the candidate remains **unrun**, not passed. Reviewed all eight core records; database-design-plan needs no definition change. Major architecture/shared-candidate decision and existing News Intelligence feature record are synchronized.

Staged source excludes private dotenv/OAuth/ngrok/bridge keys, DPAPI files and raw experiment streams/ledgers. Pattern and known-local-secret checks pass without printing secret values. Commit/push follows these measured checks; no deployment, additional inference or automatic worker activation is authorized by this checkpoint. Preserve the previously recorded five baseline news failures and unqualified Linux runtime. [@roicambe](https://github.com/roicambe) (Roi Cambe)
