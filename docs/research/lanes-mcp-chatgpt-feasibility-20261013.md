# LANES MCP and ChatGPT feasibility review

> **Last Updated:** October 13, 2026, 12:06 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Historical research with implementation follow-up; actual ChatGPT connection remains pending.

## Implementation follow-up

The historical investigation below led to locally implemented, disabled read/preview MCP tooling and a shared candidate dependency upgrade. The developer clarified automatic auditing as the goal. Official SIWC documentation describes separate plan-use authorization for eligible local/open-source clients; hosted inference eligibility remains unverified. A tested local sign-in helper now awaits real personal-account authorization. [Evidence](../evaluations/chatgpt-plan-signin-20261013.md), [official sign-in](https://developers.openai.com/siwc/token-sharing-open-source/sign-in). [@roicambe](https://github.com/roicambe) (Roi Cambe)

The developer requests an additive experiment and explicitly retains existing provider code so LANES can return to OpenRouter if necessary. This review changes documentation only. No LLM POST, database query/write, dependency installation, credential/configuration edit, deployment, push or repository reorganization occurs. Findings describe the roi-branch source at `e8cf65f`; production state is not freshly inspected here. [Proposed phased implementation](../plans/lanes-mcp-chatgpt-review.md).

**Follow-up library comparison:** Standalone FastMCP 4.1.0 is now the recommended gateway framework, on existing Python 3.12 with a qualified SDK 2.3.0 dependency. Same-environment resolver checks prove both Pydantic and FastAPI/Starlette conflicts; isolated resolution succeeds without installation. The initial SDK-only candidate discussion below records the first review. [Detailed selection and deployment/auth tradeoffs](lanes-mcp-library-selection-20261013.md).

## What MCP can provide

An MCP server exposes tools and data to a host such as ChatGPT. The useful initial LANES workflow is user-driven: ask ChatGPT to read a saved source and its extracted claims, then return an evidence-bound audit proposal. The gateway supplies evidence rather than calling a second LLM itself. [OpenAI MCP concept](https://developers.openai.com/plugins/concepts/mcp-server), [server implementation guide](https://developers.openai.com/plugins/build/mcp-server).

MCP does not, by itself, provide an unattended Plus-backed inference endpoint to LANES's Cloud Run worker. The protocol includes optional sampling, but client support must be negotiated and model choice remains client-controlled; the reviewed OpenAI documentation does not establish that ChatGPT exposes the required sampling behavior for this workload. Do not build the collector around that assumption. [MCP sampling specification](https://modelcontextprotocol.io/specification/2025-11-25/client/sampling).

Sign in with ChatGPT is a separate integration that allows eligible applications to use a user's ChatGPT plan for eligible Responses requests. Its documentation covers open-source/local apps and directs paid or remotely hosted apps to an interest process; LANES Cloud Run eligibility is unestablished. Plus plan-sharing limits are shared across apps. This review neither authorizes account sharing nor assumes unlimited included inference. [Plan usage](https://developers.openai.com/siwc/token-sharing-open-source), [account/usage limits](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions).

## Relevant repository findings

Read `AGENTS.md`, `DESIGN.md`, the architecture/news/API/security/test/planner skills, the docs catalog and core project records, and the relevant news safety, batch, Gemini, reliability, replay, manual source-review and provider-trial records. Older dated runtime/deployment/3-of-12 notes are historical evidence; the latest trial record is 12-of-12, with Gemini quota blocked and Groq only a research candidate. There is no existing MCP implementation or MCP runtime dependency in the inspected source/manifests.

| Existing component | Useful capability | Integration limit |
| --- | --- | --- |
| `backend/app/api/v1/endpoints/admin_news.py` | Protected article browse/detail, extraction-run history, result browse/detail, placement preview | No external model-audit submission endpoint; processing/discovery POSTs may write or dispatch and must not be exposed as review tools |
| `backend/app/services/news_results_service.py` | `read_news_result` returns an exact run/claim ordinal, captured source and input fingerprint | Result listing represents latest readable locations, not the complete pending audit queue; negative/context-only claims can be absent |
| `backend/app/crud/news_results.py` | Reads complete saved runs by exact identity | MCP cannot infer pending/completed audit state from visible location cards |
| `backend/app/services/news_claim_auditor.py` | Builds a bounded batch document and server-owned evidence options; strict evidence expansion, validation and classification | External proposals need an additive shared-validation entry point; gateway must not duplicate this logic or use mock transport in production |
| `backend/app/crud/news_evaluation.py` | Immutable run validation, policy-based uniqueness, owned completion and recovery | Worker leases last 120 seconds; holding one open while a person chats is unsuitable |
| `backend/app/services/news_evaluation_service.py` | Admission/freshness checks, source/claim hashes, policy identity, bounded unpublished evaluations | A long chat result must be rechecked at submission time; terminal evaluations cannot be overwritten |
| `backend/app/services/news_publication_service.py` | Revalidates completed audit identity/evidence before lifecycle decisions | Publication expects the current auditor policy/provider/model; a ChatGPT proposal cannot be inserted under Gemini/OpenRouter identity |
| `backend/app/api/v1/endpoints/admin_news_publication.py` | Revision-guarded staff decision preview/write and private history | A staff decision is not an independent model-audit upload and must not be used to bypass missing audit evidence |
| `backend/app/api/news_publication_deps.py`, `news_permissions.py` | Reader requires reports=view/full; writer requires reports=full | Prefer these explicit server-owned capabilities for new review interfaces |
| `backend/app/api/deps.py` | Existing user JWT verification and staff dependency | `get_current_active_admin` currently excludes Commuter rather than requiring a precise role/capability; do not treat that alone as MCP write authorization |
| `backend/app/main.py`, `cloudbuild.yaml` | FastAPI lifecycle and coordinated API/news/expiry image deployment | Mounting an SDK impacts lifecycle/dependencies and the current shared deployment; a separate gateway is easier to isolate initially |

The existing password-token login and Google sign-in issue LANES JWTs. They are not a complete MCP authorization server with discovery, authorization-code/PKCE and MCP resource audiences. Protecting a remote MCP endpoint requires additional authentication integration; uploading a reusable LANES bearer token into a chat is not the connection method.

## SDK/deployment compatibility

The official Python SDK supports mounting an MCP app inside FastAPI/Starlette, but the top-level app must start its session manager. A mount alone is insufficient. [ASGI integration](https://py.sdk.modelcontextprotocol.io/run/asgi/).

Read-only PyPI metadata on October 13 reports `mcp==2.3.0` with `pydantic>=2.12.0` and `httpx2>=2.10.0`. LANES pins `pydantic==2.7.4`, FastAPI 0.111.0, HTTPX 0.27.0 and spaCy 3.7.5. The Pydantic requirement is a direct incompatibility with the existing pin; other compatibility has not been resolved or installed. Do not run a broad backend upgrade to create the prototype. The package declares Python >=3.10 while the current docs landing page states 3.11+; use a tested supported interpreter and actual package metadata. LANES's backend image already uses Python 3.12. [Release metadata](https://pypi.org/project/mcp/2.3.0/), [maintainer dependency declaration](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/v2.3.0/pyproject.toml), [SDK guide](https://py.sdk.modelcontextprotocol.io/).

Recommendation: prototype a separate gateway process/environment that talks only to authenticated LANES APIs. It owns MCP transport, schemas and auth, while FastAPI retains data queries, evidence validation and publication decisions. Implementation must choose and document the separate dependency manifest in accordance with repository dependency rules; no new requirement is added during research. A same-process mount remains a later option after dependency qualification.

For ChatGPT, use Streamable HTTP at a tested exact `/mcp` URL, exposed through HTTPS or an eligible Secure MCP Tunnel. Local stdio is useful for compatible local clients/Inspector; ChatGPT cannot simply reach an ordinary private localhost URL. Start with no custom UI. Declare truthful read-only/destructive/open-world annotations and provide concise structured results with stable IDs; these annotations are not authorization. [Build tools](https://developers.openai.com/plugins/build/mcp-server), [connect/test](https://developers.openai.com/plugins/deploy/connect-chatgpt), [protocol transport](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports).

Remote private-data access requires OAuth discovery, authorization-code/PKCE, issuer/audience/expiry/scope validation and binding the authenticated identity to the correct LANES user. OpenAI recommends an established authorization provider. An MCP-audience token must not simply be forwarded as a LANES JWT; use a reviewed delegated backend credential/identity boundary. Real private data remains inaccessible until this is resolved. Host/Origin allowlists, exact endpoint redirects and supported protocol versions also need testing. [OpenAI auth guide](https://developers.openai.com/plugins/build/auth), [SDK deployment](https://py.sdk.modelcontextprotocol.io/run/deploy/).

## Safest first result and remaining questions

First prove transport and read-only evidence retrieval using synthetic/frozen local fixtures and a dedicated local dataset. Then prove an authenticated ChatGPT session can read the exact source/version/claim without provider calls. Add a dry-run validation tool only after the backend supports shared strict validation; its result is a proposal/preview, not a terminal evaluation or public flood approval. Persisting or publishing external reviews is a separate stage with explicit provenance, policy isolation, stale-result handling and idempotency.

Remaining implementation gates are the gateway runtime/dependency layout, identity provider/account binding, actual ChatGPT connection availability, and storage/policy design if durable review is later needed. No database migration is assumed; any necessary model/migration change requires the developer's authorization under AGENTS.md. Weather explanations and autonomous collection remain outside this initial MCP trial. Existing OpenRouter/Gemini transports, secrets, configuration, cooldowns and historical results stay available; disconnecting the new gateway is the initial rollback.
