import pytest
from app.schemas.profile import ProfileUpdate
from app.models.user import User


def test_profile_update_schema_includes_username():
    update = ProfileUpdate(username="newhandle123")
    assert update.username == "newhandle123"

    update_none = ProfileUpdate(first_name="Juan")
    assert update_none.username is None


def test_username_validation_rules():
    import re
    valid_usernames = ["juan", "juan.dela_cruz", "user_123", "a.b_c"]
    invalid_usernames = ["ju", "a" * 31, "juan dela", ".juan", "juan.", "_juan", "juan_", "juan..cruz", "juan__cruz", "juan@cruz"]

    pattern = r"^[a-zA-Z0-9._]+$"
    for u in valid_usernames:
        assert len(u) >= 3 and len(u) <= 30
        assert re.match(pattern, u) is not None
        assert not (u.startswith((".", "_")) or u.endswith((".", "_")) or ".." in u or "__" in u)

    for u in invalid_usernames:
        is_invalid = (
            len(u) < 3
            or len(u) > 30
            or not re.match(pattern, u)
            or u.startswith((".", "_"))
            or u.endswith((".", "_"))
            or ".." in u
            or "__" in u
        )
        assert is_invalid is True
