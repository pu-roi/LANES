"""Observation clocks belong to their supported list or clause, not all news."""
from datetime import datetime

import pytest

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.taglish_extraction_service import extract_taglish_flood_facts


@pytest.mark.parametrize("body, expected", [
    (
        "As of 2:47 p.m., the following roads were flooded:\n"
        "Pasig City\nOrtigas Avenue - gutter deep\n"
        "Marikina City\nMarcos Highway - knee deep",
        {"Ortigas Avenue": "14:47", "Marcos Highway": "14:47"},
    ),
    (
        "As of 2:00 p.m., flooding on Ortigas Avenue in Pasig City reached gutter level, "
        "while as of 3:00 p.m., flooding on Marcos Highway in Marikina City reached knee level.",
        {"Ortigas Avenue": "14:00", "Marcos Highway": "15:00"},
    ),
    (
        "As of 2:47 p.m., flooding affected Ortigas Avenue in Pasig City "
        "and Marcos Highway in Marikina City.\n"
        "Shaw Boulevard in Mandaluyong City was flooded at knee level.",
        {"Ortigas Avenue": "14:47", "Marcos Highway": "14:47", "Shaw Boulevard": None},
    ),
    (
        "As of 2:47 p.m., flooding affected Ortigas Avenue in Pasig City.\n"
        "Marcos Highway in Marikina City was flooded at knee level.",
        {"Ortigas Avenue": "14:47", "Marcos Highway": None},
    ),
    (
        "As of 2:47 p.m., the following roads were flooded:\n"
        "Pasig City\nOrtigas Avenue - gutter deep\n"
        "Classes have been suspended across the region.\n"
        "Marcos Highway in Marikina City was flooded at knee level.",
        {"Ortigas Avenue": "14:47", "Marcos Highway": None},
    ),
])
def test_shared_and_local_observation_clock_scope(body: str, expected: dict[str, str | None]) -> None:
    result = extract_taglish_flood_facts(NewsArticleExtractorInput(
        article_id=-9, canonical_url="https://example.org/metro-flood-report",
        publisher="Local test fixture", title="Metro Manila flood observations",
        article_text=body, published_at=datetime.fromisoformat("2026-09-09T17:03:00+08:00"),
    ))
    roads = {c.canonical_road: c for c in result.claims if c.canonical_road}
    assert set(roads) == set(expected)
    for road, clock in expected.items():
        claim = roads[road]
        if clock is None:
            assert claim.event_time_resolved is None
            assert "event_time_unknown" in claim.uncertainty_reasons
        else:
            assert claim.event_time_resolved == datetime.fromisoformat(f"2026-09-09T{clock}:00+08:00")
            assert claim.event_time_kind == "observation"
        start, end = claim.evidence_sentence_offset
        assert body[start:end] == claim.evidence_sentence
        assert not claim.is_forecast
