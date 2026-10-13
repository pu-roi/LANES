# MCP library selection for LANES

> **Last Updated:** October 13, 2026, 12:06 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Historical research with implementation follow-up; actual ChatGPT connection remains pending.

## Developer-selected implementation follow-up

The isolated recommendation below is historical. The developer requested a shared framework/dependency upgrade; the candidate environment installs successfully and passes focused runtime checks, while Linux/PostGIS gates remain pending. Existing development venv is preserved. The separate gateway process shares the new manifest; it is not deployed or connected. [Measured implementation](../evaluations/chatgpt-plan-signin-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Recommendation

Use standalone **FastMCP 4.1.0** for a separate Python 3.12 gateway, with the underlying official **MCP SDK 2.3.0** explicitly qualified/pinned for the pilot. Keep LANES's FastAPI/NLP environment intact and call its protected APIs over HTTP. This is an engineering-fit recommendation for this application, not an inference-quality/performance benchmark or a verified ChatGPT connection. [Current phased plan](../plans/lanes-mcp-chatgpt-review.md), [first system review](lanes-mcp-chatgpt-feasibility-20261013.md).

Read stable PyPI package metadata and release-tagged upstream files, in addition to current docs. FastMCP's website explicitly describes its main branch and can include unreleased behavior; implementation must check features against the pinned version rather than copy latest examples blindly. FastMCP 4.1.0 was published October 8; official Python MCP 2.3.0 was published October 2. [FastMCP release](https://pypi.org/project/fastmcp/4.1.0/), [SDK release](https://pypi.org/project/mcp/2.3.0/), [documentation caveat](https://gofastmcp.com/getting-started/welcome).

## Compared options

| Option | Fit for LANES | Tradeoff / disposition |
| --- | --- | --- |
| Standalone FastMCP 4.1.0 | Python tools, structured schemas, authentication provider/proxy helpers, HTTP serving and an in-process test client | Recommended gateway framework; adds dependencies and does not supply LANES authorization automatically |
| Official Python MCP SDK 2.3.0 | Direct maintained protocol primitives, tools, transports and authentication interfaces | Good alternative for a small server using an already established identity provider; more application-specific assembly for this proposed gateway |
| Official TypeScript SDK v2 | Separate service using official server/framework-adapter packages; avoids sharing Python dependencies | Viable alternative, but introduces a Node backend runtime and a second language for this backend integration; not chosen for the Python-first pilot |
| Older bundled FastMCP / hand-written protocol | May resemble older tutorials or avoid some current package floors | Do not choose merely to satisfy old pins; adds compatibility/maintenance risks and does not resolve identity/policy design |

FastMCP and the official Python SDK are not mutually exclusive protocol stacks: the recommended FastMCP package depends on the SDK. The old `from mcp.server.fastmcp import FastMCP` API belonged to SDK v1; SDK v2 renamed that high-level class to `MCPServer`. Standalone FastMCP uses `from fastmcp import FastMCP`. These imports must not be confused. [SDK migration](https://py.sdk.modelcontextprotocol.io/migration/), [FastMCP installation](https://gofastmcp.com/getting-started/installation), [official TypeScript v2](https://ts.sdk.modelcontextprotocol.io/v2/).

## Measured dependency compatibility

Local LANES Python is **3.12.14**; its production Dockerfile specifies Python **3.12**. Both candidate Python packages declare Python >=3.10. There is no demonstrated need to upgrade Python to create this gateway.

| Dependency | LANES currently installed/pinned | Relevant proposed package requirement |
| --- | --- | --- |
| Pydantic | 2.7.4 | FastMCP and SDK require >=2.12.0 |
| FastAPI / Starlette | FastAPI 0.111.0, Starlette 0.37.2 | FastAPI requires Starlette >=0.37.2,<0.38.0; FastMCP server/client requires >=1.0.1 |
| Uvicorn | Backend manifest pins 0.30.1 | FastMCP server requires >=0.35; SDK requires >=0.31.1 |
| HTTP client | HTTPX 0.27.0 | Modern MCP/FastMCP depend on the separate HTTPX2 package; do not substitute it for LANES imports without qualification |
| spaCy | 3.7.5 | Existing NLP dependency graph is not installed in the separate gateway; broad backend upgrade compatibility remains untested |

Direct package floors were checked against [FastMCP's release-tagged manifest](https://raw.githubusercontent.com/PrefectHQ/fastmcp/v4.1.0/fastmcp_slim/pyproject.toml) and [the SDK manifest](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/v2.3.0/pyproject.toml). Parent FastMCP 4.1.0 delegates to `fastmcp-slim[client,server]==4.1.0`; its requirement list alone does not show every runtime dependency.

Three real pip resolver checks ran with `--dry-run --ignore-installed --no-cache-dir` on local Python 3.12.14:

1. `fastmcp==4.1.0` plus `pydantic==2.7.4`: **ResolutionImpossible**. Metadata/resolver identifies the required newer Pydantic floor.
2. `fastmcp==4.1.0` plus `fastapi==0.111.0`: **ResolutionImpossible**. FastAPI's <0.38 Starlette range conflicts with FastMCP's >=1.0.1 requirement.
3. Isolated `fastmcp==4.1.0` plus `mcp==2.3.0`: **resolution succeeds**, selecting 68 distributions on Windows, including Pydantic 2.14.1, Starlette 1.7.0, HTTPX2 2.13.1 and Uvicorn 0.54.0.

The successful dry run is not a lockfile, installation, runtime smoke test, security review or proof of Linux/Cloud Run compatibility. Before implementation, build a dedicated locked environment/image and test imports, transport, authentication and the target Linux platform. No package was installed; reinspection confirms FastMCP/MCP absent and all existing LANES framework versions unchanged. Resolver logs, metadata and the resolution report are preserved privately under ignored `data/mcp-research/`.

## System review and integration implications

Rechecked actual source after the first review. All eighteen inspected source/design/manifest hashes remain unchanged. Existing provider builders and strict evidence validators are retained. The stored read APIs expose the exact captured source and claim identity; lifecycle permissions already have reports=view/full and reports=full checks. Generic staff dependencies alone remain insufficient for MCP write authorization.

Use a few manually registered gateway tools that call a fixed allowlist of LANES API routes. Do not import `app.main` into the gateway: its lifespan seeds roles/users and starts retention maintenance. Do not copy database connections, article queries, validation or publication logic into MCP. Keep source/claim hashes, response revisions, freshness and exact-span validation backend-owned.

FastMCP can convert a FastAPI/OpenAPI surface automatically, but its own docs recommend curated tools for complex APIs. LANES contains discovery/processing and staff-decision POSTs; bulk conversion could advertise operations outside this evidence-review pilot. Manual tools give stable schemas and let us keep the advertised read/preview contract narrow. [FastAPI integration](https://gofastmcp.com/integrations/fastapi), [release-tagged integration guidance](https://raw.githubusercontent.com/PrefectHQ/fastmcp/v4.1.0/docs/integrations/fastapi.mdx).

FastMCP's JWT verifier only validates supplied tokens; it does not provide the OAuth discovery/login flow required by ChatGPT. Its remote-auth and OAuth-proxy helpers make that flow easier to build, while LANES account mapping, resource audiences, scopes and per-tool capabilities still require implementation. Existing Google sign-in does not automatically become an MCP authorization server. [FastMCP authentication](https://gofastmcp.com/servers/auth/authentication), [release-tagged auth guide](https://raw.githubusercontent.com/PrefectHQ/fastmcp/v4.1.0/docs/servers/auth/authentication.mdx), [OpenAI auth requirements](https://developers.openai.com/plugins/build/auth).

For a gateway scaled on Cloud Run, qualify Streamable HTTP and actual client protocol behavior across replicas/restarts. FastMCP documents sessionless serving for load-balanced deployments. OAuth proxy deployments additionally need stable signing keys and durable encrypted network-accessible token storage; sessionless transport does not make OAuth state persistent. An external managed issuer can reduce gateway-owned OAuth storage, but provider selection and account binding remain open. [HTTP deployment](https://gofastmcp.com/deployment/http), [release-tagged deployment](https://raw.githubusercontent.com/PrefectHQ/fastmcp/v4.1.0/docs/deployment/http.mdx).

## Next verification and preservation

Start with synthetic/frozen read-only tools and in-process client tests, then Inspector/HTTP, then an authenticated ChatGPT connection. Explicitly verify unsupported tools, permission failures, bad IDs, provider-call count zero, secret-free results and original evidence identity. FastMCP offers a Client/Pytest pattern, but no server tests were run in this research. [Testing guide](https://gofastmcp.com/servers/testing), [ChatGPT connection procedure](https://developers.openai.com/plugins/deploy/connect-chatgpt).

Audit preview and any durable handoff still need additive backend interfaces and the policy/120-second ownership design in the existing plan. Neither library makes Plus unlimited or establishes autonomous cloud inference. Provider code, credentials, public weather, normal workers, historical databases, schema and deployment configuration stay intact. The immediate fallback is disconnecting the separate gateway; returning the normal worker to OpenRouter remains a deliberate configured choice with its existing quota checks.
