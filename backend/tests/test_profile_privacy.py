import pytest
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import ProfileUpdate, ProfileResponse, ProfileBase
from app.crud.user import get_user_avatar_url


def test_profile_schema_hide_profile_picture():
    # ProfileBase default
    base = ProfileBase(first_name="John", last_name="Doe")
    assert base.hide_profile_picture is False

    # ProfileUpdate accepts hide_profile_picture
    update_true = ProfileUpdate(hide_profile_picture=True)
    assert update_true.hide_profile_picture is True

    update_false = ProfileUpdate(hide_profile_picture=False)
    assert update_false.hide_profile_picture is False


def test_get_user_avatar_url_respects_privacy():
    # User with no profile
    user_no_profile = User(id=1, username="testuser", email="test@example.com")
    assert get_user_avatar_url(user_no_profile) is None

    # User with profile and photo visible
    user_with_photo = User(id=2, username="photouser", email="photo@example.com")
    profile_visible = Profile(
        id=1,
        user_id=2,
        first_name="Jane",
        last_name="Doe",
        avatar_url="https://example.com/avatar.jpg",
        hide_profile_picture=False,
    )
    user_with_photo.profile = profile_visible
    assert get_user_avatar_url(user_with_photo) == "https://example.com/avatar.jpg"

    # User with profile and photo hidden
    user_hidden_photo = User(id=3, username="hiddenuser", email="hidden@example.com")
    profile_hidden = Profile(
        id=2,
        user_id=3,
        first_name="Alex",
        last_name="Smith",
        avatar_url="https://example.com/avatar.jpg",
        hide_profile_picture=True,
    )
    user_hidden_photo.profile = profile_hidden
    assert get_user_avatar_url(user_hidden_photo) is None
