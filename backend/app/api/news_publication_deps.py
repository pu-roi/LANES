"""News lifecycle permissions use server-owned role capabilities."""
from fastapi import Depends, HTTPException

from app.api.deps import get_current_user
from app.models.user import User


def may_write_news_claims(user: User) -> bool:
    role = getattr(user, "role", None)
    permissions = getattr(role, "permissions", None)
    return bool(role is not None and role.name != "Commuter" and isinstance(permissions, dict)
                and permissions.get("reports") == "full")


def require_news_reader(user: User = Depends(get_current_user)) -> User:
    role = getattr(user, "role", None)
    permissions = getattr(role, "permissions", None)
    if (role is None or role.name == "Commuter" or not isinstance(permissions, dict)
            or permissions.get("reports") not in ("view", "full")):
        raise HTTPException(403, "You do not have permission to inspect news decisions.")
    return user


def require_news_writer(user: User = Depends(require_news_reader)) -> User:
    if not may_write_news_claims(user):
        raise HTTPException(403, "You do not have permission to change news decisions.")
    return user
