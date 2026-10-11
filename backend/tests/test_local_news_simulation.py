"""Check the local demo's real audit validator and fail-closed DB boundary."""
from datetime import datetime, timezone

import pytest

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.taglish_extraction_service import extract_taglish_flood_facts
from scripts.seed_local_news_simulation import FixtureAuditor, simulate


def fixture():
    article = NewsArticleExtractorInput(article_id=1,
        canonical_url="https://example.org/local-simulation", publisher="SIMULATION ONLY",
        title="SIMULATION: flood scenario in Manila",
        published_at=datetime(2026, 10, 9, 3, tzinfo=timezone.utc),
        article_text="As of 10:55 a.m. today, knee-deep flooding was reported on Quirino Avenue "
            "from Asuncion Street to Camia Street in Manila. "
            "The field team recorded the water level during its inspection.")
    extraction = extract_taglish_flood_facts(article)
    claim = next(c for c in extraction.claims if c.canonical_road == "Quirino Avenue")
    return claim, article


@pytest.mark.asyncio
async def test_fixture_uses_extracted_span_and_real_audit_contract():
    claim, article = fixture()
    assert claim.road_segment_raw == "Quirino Avenue from Asuncion Street to Camia Street"
    result = await FixtureAuditor().audit(claim, article)
    assert result.outcome == "verified"
    assert result.provider_request_id == "synthetic-local-audit"
    assert result.evidence.time.observed_at == claim.event_time_resolved.isoformat()
    assert result.evidence.place.evidence[0].quote in article.article_text


@pytest.mark.asyncio
async def test_fixture_cannot_skip_normal_source_offset_validation():
    claim, article = fixture()
    claim.evidence_sentence_offset = (999, 1000)
    with pytest.raises(ValueError, match="claim_evidence_mismatch"):
        await FixtureAuditor().audit(claim, article)


@pytest.mark.asyncio
@pytest.mark.parametrize("database", ["postgresql+psycopg://example.org/lanes_news_test",
    "postgresql+psycopg://127.0.0.1/lanes", "postgresql+psycopg://127.0.0.1/lanes_news_test?host=example.org"])
async def test_simulation_refuses_shared_targets_before_loading_database(monkeypatch, database):
    from app.core.config import settings
    monkeypatch.setattr(settings, "DATABASE_URL", database)
    with pytest.raises(ValueError, match="loopback PostgreSQL"):
        await simulate()
