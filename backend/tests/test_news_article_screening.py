"""Actual-flood admission checks, using paraphrased publisher examples and adversarial variants."""
from datetime import datetime, timezone
import json

import httpx
import pytest
from sqlalchemy import create_engine, literal, select

from app.crud.news_results import readable_claim
from app.schemas.news_extraction import ExtractedClaim
from app.services.news_discovery_service import body_has_metro_manila_flood_claim, discover_news
from app.services.news_feed_service import NewsEntry
from app.services.news_presentation_service import claim_reading_reason
from test_news_discovery import ARTICLE_URL, FEED_URL, rss, source


# Paraphrased real reporting, used as historical test inputs, never live data:
# GMA /956643/flooded-roads-metro-manila/story/ (August 22, 2025): measured flooded roads.
# GMA /1004280/.../story/ (September 30, 2026): planned UP-PGH drainage construction.
# Philstar /2026/09/30/2559999/... (September 30, 2026): project investigation.
SCREENING_CASES = [
    ("Taguig flood control investigation", "Officials discussed suspected irregularities in flood-control contracts in Taguig City.", False),
    ("Manila drainage amid flooding", "Drainage construction at UP-PGH in Manila aims to help address flooding.", False),
    ("QC flood prevention", "A detention basin in Quezon City is intended to curb flooding.", False),
    ("Pasig flood management budget", "Pasig City allocated funds for flood management and drainage maintenance.", False),
    ("Pasig flooding discussed", "Officials in Pasig City discussed flooding and drainage at a meeting.", False),
    ("Manila flooding study", "Researchers in Manila studied flooding and modeled water levels.", False),
    ("Pasig knee-deep forecast", "Possible flooding in Pasig City may reach knee-deep levels tomorrow.", False),
    ("Pasig future flooding", "Pasig City will be flooded with knee-deep water tomorrow.", False),
    ("Pasig simulation", "A simulation predicts knee-deep flooding on C. Raymundo Avenue in Pasig City.", False),
    ("Pasig habitual flooding", "C. Raymundo Avenue in Pasig City is regularly flooded during heavy rains.", False),
    ("Pasig habitual Taglish", "Madalas binabaha ang Maybunga sa Pasig City kapag malakas ang ulan.", False),
    ("Pasig flood design", "Drainage works in Pasig City aim to prevent knee-deep flooding.", False),
    ("Pasig flood-free update", "There is no flooding in Pasig City and all roads remain dry.", False),
    ("Pasig old flood", "In 2020, Pasig City was flooded with knee-deep water.", False),
    ("Bangkok floods", "Roads in Bangkok were flooded with waist-deep water this morning.", False),
    ("Cebu flooding", "Knee-deep flooding affected roads in Cebu City this morning.", False),
    ("Metro Manila weather and Cebu flood", "Weather officials in Manila issued a forecast. Roads in Cebu City were flooded with knee-deep water.", False),
    ("Manila rainfall", "Heavy rain fell in Manila today. Residents checked the weather forecast.", False),
    ("Manila flood response exercise", "A flood drill in Manila simulated knee-deep floodwater for rescue training.", False),
    ("Flood control and an actual flood", "Flood-control contracts are being investigated. Roads in Pasig City were flooded this morning.", True),
    ("Measured Manila flooding", "Roxas Boulevard in Manila was flooded with gutter-deep water at 9 AM.", True),
    ("Pasig roads flooded", "Flooding affected C. Raymundo Avenue in Pasig City this morning.", True),
    ("Floodwaters in Pasig", "Floodwaters hit C. Raymundo Avenue in Pasig City this morning.", True),
    ("Baha sa Pasig", "Binaha ang Maybunga sa Pasig City, abot-tuhod ang tubig kaninang umaga.", True),
    ("Floodwater receding", "Floodwater was receding on C. Raymundo Avenue in Pasig City as of 10 AM.", True),
    ("Floodwater subsided", "Floodwater subsided on C. Raymundo Avenue in Pasig City as of 11 AM.", True),
    ("Flooded roads in Manila", "Flooded roads in Manila stranded residents this morning.", True),
]


def entry(title: str, body: str = "") -> NewsEntry:
    return NewsEntry(source_id="test", publisher="Example News", feed_url=FEED_URL,
        feed_id="screening", article_url=ARTICLE_URL, title=title, excerpt=body,
        published_at=datetime.now(timezone.utc))


@pytest.mark.parametrize("title,body,expected", SCREENING_CASES)
def test_actual_flood_article_admission(title: str, body: str, expected: bool) -> None:
    assert body_has_metro_manila_flood_claim(entry(title), body) is expected


@pytest.mark.parametrize("title", ["Taguig flood control probe", "Knee-deep flooding in Pasig City"])
def test_unreadable_new_articles_never_enter_collection(title: str) -> None:
    requests = []
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if str(request.url) == FEED_URL:
            return httpx.Response(200, content=rss(f'<item><title>{title}</title><link>{ARTICLE_URL}</link></item>'))
        return httpx.Response(403)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        run = discover_news((source(),), client)
    assert requests == [FEED_URL, ARTICLE_URL]
    assert not run.candidates
    assert any("body verification unavailable" in notice.reason for notice in run.notices)


@pytest.mark.parametrize("sentence,expected", [
    ("Pasig City discussed flooding and drainage.", False),
    ("A flood-control project in Pasig City was announced.", False),
    ("Flooding affected C. Raymundo Avenue in Pasig City.", True),
    ("Roads in Pasig City were flooded this morning.", True),
])
def test_reader_sql_and_detail_require_affirmative_evidence(sentence: str, expected: bool) -> None:
    claim = ExtractedClaim(raw_place_name="Pasig City", canonical_city="City of Pasig",
        condition="active", evidence_sentence=sentence, flood_mentioned=True,
        place_char_start=0, place_char_end=10, evidence_sentence_offset=(0, len(sentence)))
    fields = claim.model_dump()
    fields["uncertainty_reasons"] = json.dumps(fields["uncertainty_reasons"])
    with create_engine("sqlite+pysqlite:///:memory:").connect() as connection:
        accepted = bool(connection.scalar(select(readable_claim(lambda field: literal(fields.get(field))))))
    assert accepted is expected
    assert (claim_reading_reason(claim) is None) is expected
