"""Claim admission policy checks; no DB, external provider or public writes."""
from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput
from app.services.news_evaluation_service import preliminary_reason, publication_is_current, source_is_approved
from app.services.news_sources import NewsSource

NOW = datetime(2026, 10, 5, 3, tzinfo=timezone.utc)


def claim(**changes) -> ExtractedClaim:
    return ExtractedClaim(**{
        "raw_place_name": "C5", "canonical_road": "C5", "canonical_city": "Pasig",
        "place_type": "street", "place_char_start": 0, "place_char_end": 2,
        "evidence_sentence": "C5 in Pasig City is flooded, knee-deep as of 10:55 AM.",
        "evidence_sentence_offset": (0, 57), "condition": "active",
        "event_time_kind": "observation", "event_time_resolved": NOW - timedelta(minutes=5),
        **changes,
    })


@pytest.mark.parametrize("changes,reason", [
    ({}, None),
    ({"canonical_city": "Cebu"}, "unsupported_locality"),
    ({"is_forecast": True}, "forecast_claim"),
    ({"is_negated": True}, "negated_claim"),
    ({"is_historical": True}, "historical_claim"),
    ({"uncertainty_reasons": ["location_context_only"]}, "unsupported_claim_context"),
    ({"uncertainty_reasons": ["city_context_ambiguous"]}, "unsupported_claim_context"),
    ({"event_time_kind": "report"}, "missing_supported_observation_time"),
    ({"event_time_resolved": NOW.replace(tzinfo=None)}, "missing_supported_observation_time"),
    ({"event_time_resolved": NOW + timedelta(seconds=1)}, "observation_outside_admission_window"),
    ({"event_time_resolved": NOW - timedelta(hours=2)}, "observation_evidence_expired"),
    ({"event_time_resolved": NOW - timedelta(hours=13)}, "observation_outside_admission_window"),
    ({"condition": "subsided", "event_time_resolved": NOW - timedelta(hours=3)}, None),
    ({"condition": "unknown"}, "unclear_flood_status"),
])
def test_preflight_preserves_observation_and_clearance_meaning(changes, reason):
    assert preliminary_reason(claim(**changes), NOW) == reason


@pytest.mark.parametrize("age,accepted", [(0, True), (12, True), (12.01, False), (-1, False)])
def test_publication_admission_is_separate_from_two_hour_evidence_lifetime(age, accepted):
    article = NewsArticleExtractorInput(article_id=1, publisher="fixture", title="Flood",
        canonical_url="https://example.org/flood", published_at=NOW - timedelta(hours=age))
    assert publication_is_current(article, NOW) is accepted


@pytest.mark.parametrize("url,accepted", [
    ("https://example.org/flood", True), ("https://news.example.org/flood", True),
    ("https://example.org.evil.test/flood", False), ("https://user:secret@example.org/flood", False),
    ("http://example.org/flood", False), ("https://example.org:444/flood", False),
])
def test_saved_source_must_match_reviewed_enabled_publisher(url, accepted):
    source = NewsSource("fixture", "Fixture", ("example.org",), ("https://example.org/feed",), NOW.date(), True)
    article = NewsArticleExtractorInput(article_id=1, publisher="fixture", title="Flood", canonical_url=url)
    assert source_is_approved(article, (source,)) is accepted


def test_unknown_depth_can_be_audited_without_inventing_a_measurement():
    value = claim(depth_canonical=None, depth_raw=None, depth_meters=None)
    assert preliminary_reason(value, NOW) is None
    assert value.depth_meters is None


@pytest.mark.parametrize("database", ["postgresql+psycopg://example.org/lanes_news_test",
    "postgresql+psycopg://127.0.0.1/lanes", "postgresql+psycopg://127.0.0.1/lanes_news_test?host=example.org"])
def test_historical_publication_clock_cannot_be_used_on_normal_or_shared_database(monkeypatch, database):
    from types import SimpleNamespace
    from sqlalchemy.engine import make_url
    from app.core.config import settings
    from app.core import database as connection
    from app.services.news_evaluation_service import EvaluationPolicy
    monkeypatch.setattr(settings, "DATABASE_URL", database)
    monkeypatch.setattr(connection, "engine", SimpleNamespace(url=make_url(database)))
    with pytest.raises(ValueError, match="dedicated loopback replay database"):
        EvaluationPolicy("a" * 64, "fixture", {}, publication_admission_at=NOW)


def test_private_reconstruction_uses_later_evidence_without_extending_observation_expiry(monkeypatch):
    from types import SimpleNamespace
    from sqlalchemy.engine import make_url
    from app.core.config import settings
    from app.core import database
    from app.services.news_evaluation_service import EvaluationPolicy
    target = "postgresql+psycopg://127.0.0.1/lanes_news_test"
    monkeypatch.setattr(settings, "DATABASE_URL", target)
    monkeypatch.setattr(database, "engine", SimpleNamespace(url=make_url(target)))
    later = NOW + timedelta(hours=12)
    policy = EvaluationPolicy("a" * 64, "fixture", {}, publication_admission_at=later)
    article = NewsArticleExtractorInput(article_id=1, publisher="fixture", title="Flood",
        canonical_url="https://example.org/flood", published_at=later)
    assert not publication_is_current(article, NOW)
    assert publication_is_current(article, NOW, policy)
    assert article.published_at == later
    assert preliminary_reason(claim(), NOW, policy) is None
    assert preliminary_reason(claim(), NOW + timedelta(hours=2), policy) == "observation_evidence_expired"
