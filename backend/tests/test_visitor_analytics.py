from uuid import uuid4

from app.services.visitor_analytics_service import (
    hash_visitor_identifier,
    is_automated_user_agent,
)


def test_visitor_identifier_is_stable_and_not_stored_raw() -> None:
    visitor_id = uuid4()

    visitor_hash = hash_visitor_identifier(visitor_id)

    assert visitor_hash == hash_visitor_identifier(visitor_id)
    assert visitor_hash != str(visitor_id)
    assert len(visitor_hash) == 64


def test_known_automated_clients_are_not_counted() -> None:
    assert is_automated_user_agent("Mozilla/5.0 (compatible; Googlebot/2.1)")
    assert is_automated_user_agent("curl/8.0")
    assert not is_automated_user_agent("Mozilla/5.0 (Linux; Android 14) Chrome/120.0")
