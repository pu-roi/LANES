# Disabled LANES MCP pilot startup and rollback

> **State:** Local read/preview implementation; real authenticated ChatGPT MCP tool call and Linux/PostGIS qualification are pending. No production deployment.
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

The separate FastMCP gateway calls five protected FastAPI interfaces; it does not import app.main or run extraction/publication/database business logic. Its shared candidate dependencies use Python 3.12, FastAPI 0.143.0, Pydantic 2.14.1, Starlette 1.7.0, Uvicorn 0.54.0, FastMCP 4.1.0 and MCP 2.3.0. Existing development `backend/venv` is retained. Install the candidate into a separate `backend/.venv`, then run `python -m pip check`. The manifest includes all direct runtime imports; existing NLP/spatial pins remain.

## Protected MCP startup sequence

1. Copy `.env.mcp.example` to ignored `.env.mcp.local`; never overwrite encrypted provider configuration. Keep both enable flags false while preparing credentials and a disposable database.
2. Use a new local PostGIS database whose name starts with `lanes_mcp_test_`. With that database selected through `LANES_MCP_TEST_DATABASE_URL`, run `dotenvx run -f .env -f .env.mcp.local -- .venv/Scripts/python.exe -m pytest tests/test_mcp_postgres.py --confcutdir=tests -q`. The test refuses nonlocal/nonempty databases and runs the existing Alembic upgrade head; it seeds synthetic data only inside this disposable database. This check has not run on this computer because Docker is unavailable. Do not target existing/shared/historical databases.
3. Configure the dedicated Google web client callback as `<ngrok-public-origin>/auth/callback`. Bind an allowed Google subject and verified email to an existing active LANES account with reports=view/full. Populate separate RSA assertion keys, stable OAuth signing secret and an encrypted OAuth storage directory outside Git. No MCP account creation, promotion or reactivation is permitted.
4. Set `LANES_MCP_CLIENT_REDIRECT_URIS` to the exact HTTPS callback presented by ChatGPT. Wildcards are rejected. Real Google identity binding and this callback allowlist are not completed in the current private configuration.
5. Once the above prerequisites qualify, set the independent review/gateway enable flags true only in the private pilot configuration. Run the local API and gateway in separate terminals from `backend/`:

```powershell
dotenvx run -f .env -f .env.mcp.local -- .venv/Scripts/python.exe -m scripts.run_mcp_pilot api
dotenvx run -f .env -f .env.mcp.local -- .venv/Scripts/python.exe -m scripts.run_mcp_pilot gateway
```

The launcher binds API 8005 and gateway 8787 to loopback and refuses shared/non-pilot databases or nonlocal backend origins. Expose only gateway 8787 through the configured ngrok domain after its OAuth protections are active. Example, substitute your configured domain:

```powershell
ngrok http 8787 --url https://YOUR-ASSIGNED-DOMAIN.ngrok-free.dev
```

Connect the public `/mcp` URL using ChatGPT's custom MCP connection procedure, inspect the five discovered tools and prove an actual authenticated call. The currently prepared account token belongs to **Sign in with ChatGPT plan usage**, a separate inference route; it does not authenticate these Google-protected MCP tools. The gateway has never been connected to ChatGPT successfully and should remain disabled until this sequence qualifies. Do not paste Google secrets, bridge keys, ngrok tokens or browser callbacks into chat.

Tools: get_connection_status, list_saved_news, get_claim_evidence, get_audit_bundle and preview_audit_proposal. Reads/previews include original negative/ambiguous claims, preserve immutable source identity, reject incomplete selections and perform no model calls, evaluation leases or writes. PostgreSQL read-only transactions enforce the write boundary. Preview responses explicitly prohibit publication and routing effects.

## ChatGPT plan-use test

For the developer's automatic-auditing goal, use the separate [local ChatGPT sign-in guide](chatgpt-plan-local-signin.md). Real account authorization is verified. The [three measured news requests](../evaluations/chatgpt-news-live-20261013.md) have not qualified automatic use; do not reset the ledger or activate the worker. Two of the five requests remain unused after semantic failure. OpenRouter/Gemini and scheduled workers are preserved.

## Rollback and release gates

Stop the gateway/tunnel and set both MCP flags false. Preserve captured sources, extraction runs, evaluations and credentials needed for deliberate revocation. No database migration rollback is needed because no model/migration was introduced. Return development work to the retained qualified `backend/venv`. To build a fresh environment with previous framework dependencies, obtain `backend/requirements.txt` from baseline commit `e8cf65feea3094ebab04e8babec568dff1a9e8cc` into an ignored requirements file and install it into a new environment; never overwrite a working venv blindly. The original manifest contains unpinned direct dependencies, so it is not an exact transitive lock; use the preserved environment for the qualified local baseline.

`backend/Dockerfile.mcp` prepares a separate gateway image entrypoint while sharing the candidate manifest. The Linux image is unbuilt/unqualified, not a released artifact. Production Cloud Run rollout requires a separate accepted pilot/hosting plan, durable encrypted OAuth storage, Secret Manager credentials, replica behavior and serving-revision checks. Current Cloud Build API/news/expiry structure is unchanged. Pushing this implementation does not qualify it for production; inspect actual CI/CD trigger scope before merging or deploying.

## Local browser checks

The local-helper browser spec is opt-in so ordinary LANES frontend tests do not depend on an unrelated local process. From frontend/, with the helper running:

```powershell
$env:LANES_CHATGPT_SIGNIN_URL="http://127.0.0.1:1457"
npx playwright test tests/chatgpt-plan-signin.spec.ts --project=desktop-chromium --project=mobile-chromium
```

The click test intercepts the browser POST before authorization, so it does not consume model requests or initiate another sign-in.
