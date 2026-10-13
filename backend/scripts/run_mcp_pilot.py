"""Refuse shared databases and non-loopback origins before serving the pilot."""
import argparse
import os
from urllib.parse import urlsplit

from sqlalchemy.engine import make_url


def guard_local_pilot() -> None:
    database = make_url(os.environ.get("DATABASE_URL", ""))
    if (database.host not in {"localhost", "127.0.0.1", "::1"}
            or not (database.database or "").startswith("lanes_mcp_test_")):
        raise ValueError("Refusing a shared/non-MCP-test database.")
    backend = urlsplit(os.environ.get("LANES_MCP_BACKEND_URL", ""))
    if backend.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("The local pilot must use a loopback LANES backend.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("service", choices=["api", "gateway"])
    args = parser.parse_args()
    guard_local_pilot()
    if args.service == "gateway":
        from app.mcp.server import create_app
        port = 8787
    else:
        from app.api.mcp_review_app import create_app
        port = 8005
    import uvicorn
    uvicorn.run(create_app(), host="127.0.0.1", port=port,
                log_level="warning", access_log=False, proxy_headers=False)


if __name__ == "__main__":
    main()
