"""Narrow gateway delegation; never reuse application login or provider keys."""
import hashlib
import time
from collections.abc import Generator

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.api.news_publication_deps import require_news_reader
from app.core.database import SessionLocal
from app.core.mcp_review_config import MCP_ASSERTION_AUDIENCE, mcp_settings
from app.models.user import User

bearer = HTTPBearer(auto_error=False)


def review_db() -> Generator[Session, None, None]:
    """All tool transactions are enforced read-only by PostgreSQL."""
    if not mcp_settings().review_enabled:
        raise HTTPException(404, "MCP review is disabled.")
    with SessionLocal() as db:
        db.execute(text("SET TRANSACTION READ ONLY"))
        try:
            yield db
        finally:
            db.rollback()


async def get_mcp_reader(request: Request,
        credential: HTTPAuthorizationCredentials | None = Depends(bearer),
        db: Session = Depends(review_db)) -> User:
    config = mcp_settings()
    if not config.review_enabled:
        raise HTTPException(404, "MCP review is disabled.")
    if (not credential or credential.scheme.lower() != "bearer"
            or not config.assertion_public_key_file or not config.public_url
            or not config.allowed_google_subject or not config.allowed_email
            or not config.google_client_id):
        raise HTTPException(401, "MCP authentication required.", headers={"WWW-Authenticate": "Bearer"})
    from app.services.news_claim_auditor import MAX_RESPONSE_BYTES
    if not hasattr(request, "_body"):
        buffer = bytearray()
        async for chunk in request.stream():
            buffer.extend(chunk)
            if len(buffer) > MAX_RESPONSE_BYTES:
                raise HTTPException(413, "mcp_proposal_oversized")
        request._body = bytes(buffer)
    body = await request.body()
    path = request.url.path + ("?" + request.url.query if request.url.query else "")
    try:
        claims = jwt.decode(credential.credentials,
            config.assertion_public_key_file.read_text(encoding="utf-8"), algorithms=["RS256"],
            audience=MCP_ASSERTION_AUDIENCE, issuer=config.public_url,
            options={"require_exp": True, "require_iat": True, "require_sub": True})
        now = time.time()
        if (type(claims.get("iat")) is not int or type(claims.get("exp")) is not int
                or not 0 < claims["exp"] - claims["iat"] <= 60 or claims["iat"] > now + 5
                or claims["sub"] != config.allowed_google_subject
                or claims.get("email") != config.allowed_email.casefold()
                or claims.get("email_verified") is not True
                or claims.get("google_aud") != config.google_client_id
                or claims.get("method") != request.method
                or claims.get("path") != path
                or claims.get("body_sha256") != hashlib.sha256(body).hexdigest()):
            raise ValueError("assertion_invalid")
    except (JWTError, ValueError, OSError):
        raise HTTPException(401, "MCP authentication failed.",
                            headers={"WWW-Authenticate": "Bearer"}) from None
    user = db.scalar(select(User).where(func.lower(User.email) == config.allowed_email.casefold()))
    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(403, "MCP account is unavailable.")
    return require_news_reader(user)
