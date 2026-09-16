"""Authentication headers for calls to the private Cloud Run Valhalla service."""

import time

from app.core.config import settings


class ValhallaAuthenticationError(RuntimeError):
    """Application default credentials could not mint a Cloud Run ID token."""


_identity_token: str | None = None
_identity_token_expires_at = 0.0


def get_valhalla_auth_headers() -> dict[str, str]:
    """Return a cached ID token only when a private-service audience is configured."""
    global _identity_token, _identity_token_expires_at
    if not settings.VALHALLA_AUDIENCE:
        return {}
    if _identity_token and time.monotonic() < _identity_token_expires_at:
        return {"Authorization": f"Bearer {_identity_token}"}
    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import id_token

        _identity_token = id_token.fetch_id_token(Request(), settings.VALHALLA_AUDIENCE)
        _identity_token_expires_at = time.monotonic() + (45 * 60)
        return {"Authorization": f"Bearer {_identity_token}"}
    except Exception as exc:
        raise ValhallaAuthenticationError(
            "Unable to obtain a Cloud Run identity token for Valhalla."
        ) from exc
