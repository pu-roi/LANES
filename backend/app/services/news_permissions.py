"""Shared server-owned news role capability checks."""
from app.models.user import User


def may_write_news_claims(user: User) -> bool:
    role = getattr(user, "role", None)
    permissions = getattr(role, "permissions", None)
    return bool(role is not None and role.name != "Commuter" and isinstance(permissions, dict)
                and permissions.get("reports") == "full")
