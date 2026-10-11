"""Scheduler-only Google identity, separate from application user JWTs."""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from app.core.config import settings

bearer = HTTPBearer(auto_error=False)


class BoundedGoogleRequest(Request):
    def __call__(self, url: str, method: str = "GET", body: bytes | None = None,
                 headers: dict | None = None, timeout: float = 10, **kwargs: object) -> object:
        return super().__call__(url, method=method, body=body, headers=headers, timeout=min(timeout, 10), **kwargs)


def require_news_scheduler(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if not credentials:
        raise HTTPException(401, "Scheduler identity required")
    if not settings.NEWS_SCHEDULER_AUDIENCE or not settings.NEWS_SCHEDULER_SERVICE_ACCOUNT:
        raise HTTPException(503, "News scheduler identity is not configured")
    try:
        payload = id_token.verify_oauth2_token(credentials.credentials, BoundedGoogleRequest(),
                                             settings.NEWS_SCHEDULER_AUDIENCE)
    except Exception as exc:
        raise HTTPException(401, "Invalid scheduler identity") from exc
    if (payload.get("iss") not in ("accounts.google.com", "https://accounts.google.com")
            or payload.get("email") != settings.NEWS_SCHEDULER_SERVICE_ACCOUNT
            or payload.get("email_verified") is not True):
        raise HTTPException(403, "Scheduler identity is not allowed")
    return payload
