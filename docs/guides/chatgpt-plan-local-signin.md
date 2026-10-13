# Local ChatGPT plan sign-in

> **State:** Real account authorization verified; eight-claim inference works, but automatic evidence qualification is blocked.
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

This helper tests the account authorization needed for the developer's automatic news-auditing goal. It is separate from the Google OAuth-protected MCP review pilot. Keep the ngrok domain, Google client and existing provider implementation; neither Google OAuth nor an ngrok tunnel is needed for this loopback sign-in. MCP alone does not supply the worker's inference transport.

From `backend/`, using the candidate environment:

```powershell
dotenvx run -f .env -- .venv/Scripts/python.exe -m scripts.chatgpt_plan_signin --port 1455
```

Open `http://127.0.0.1:1455/` in ordinary Chrome. Click **Continue with ChatGPT**, sign in to the personal Plus account, and review OpenAI's plan-use permissions. A successful callback returns to the helper. Do not copy callback codes or tokens into chat. If authorization fails, the local page reports a safe error; report that message and its Diagnostic code, not the callback URL. Local /status retains only the fixed last_error_code.

The helper uses an issued dynamic client ID, stable per-host identifier, PKCE S256, one-use state, nonce and signature/issuer/audience/expiry validation. Credentials and the host record are saved atomically under `%LOCALAPPDATA%/LANES/ChatGPTPlan/`, encrypted with Windows DPAPI CurrentUser protection. These records are outside the repository and cannot simply be transferred to another user or hosting environment. No credentials are read from Codex's own account files. Callback and authorization URLs are excluded from access logs.

Only a single selected ChatGPT identity is supported. Returning authorization must match its client and subject. `/status` reports sanitized connection/permission/expiry booleans. It deliberately reports `inference_verified=false` and `news_worker_enabled=false`; authorization is not audit qualification. Token refresh, account switching/revocation controls, model listing, inference and worker integration are not implemented by this sign-in helper. A separate qualification runner has now tested model discovery/inference; see the latest measured outcome below. To revoke permission, disconnect the app in ChatGPT settings. Stop this local process when it is no longer needed.

After actual authorization, separately qualify five frozen cases (19-inch, 10-inch, eight-claim, ambiguous and forecast/negation) without database writes or publication, with at most five inference dispatches and no automatic retries. Preserve strict validation and stop on account/permission/quota errors. The previous Gemini/Groq twelve-call ledger remains exhausted and unchanged. No production provider changes occur through this helper.

ChatGPT plan usage remains limited. Cloud Run eligibility is unverified; automatic production integration and deployment require subsequent qualification. The shared backend upgrade is still a candidate: Linux/PostGIS checks are pending, so the existing qualified development environment is preserved.

Sources: [Registration and sign-in](https://developers.openai.com/siwc/token-sharing-open-source/sign-in), [models and inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference), [accounts and sessions](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions), [hosting scope](https://developers.openai.com/siwc/token-sharing-open-source).

Measured local checks are recorded in [the sign-in evaluation](../evaluations/chatgpt-plan-signin-20261013.md).

## Current diagnostic retry

Use http://127.0.0.1:1456/ for the updated v2 helper. The previous 1455 process remains; its generic failure cannot identify the actual validation stage. New startup can use --port 1456; only the callback port changes, permitted by the official sign-in contract. No credentials were saved by the failed real attempt. 35 focused offline checks pass; actual fresh authorization remains pending.

## Latest token-binding repair

The latest v3 helper is at http://127.0.0.1:1457/. Use this instead of older 1455/1456 processes. Its JWT decoder receives access_token so an optional at_hash claim can be verified. All signature/identity/permission checks remain; no bypass or account settings change. 42 focused offline tests pass; actual account authorization is still pending.

## Real connection and first inference outcome

The user completed sign-in on 1457 and plan scopes are verified; do not repeat authorization merely because qualification fails. The separate qualification runner now exists and uses original captured fixtures, not the MCP gateway or a production DB. Its fixed ledger records three of five allowed inference requests: the eight-claim response parses, but no positive case qualifies (seven missing-time reviews and a saved/source gauge disagreement). The semantic failure stopped dispatches; two requests remain unused. Do not rerun the runner with a new ledger, reset counters or use transport repair to bypass this evidence failure. [Actual live results](../evaluations/chatgpt-news-live-20261013.md). Refresh/worker/hosting acceptance remains pending.
