"""Historical publisher replay regressions; no live records or alerts are created.

Paraphrased facts from Daily Tribune's September 24 event (published Sept 25):
https://tribune.net.ph/2026/09/24/minor-flooding-hits-some-metro-areas
The live replay script separately fetches the original article.
"""
from datetime import datetime
import json

import httpx
import pytest
from sqlalchemy import create_engine, literal, select

from app.crud.news_results import readable_claim
from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_discovery_service import fetch_article_text, extract_captured_news_article
from app.services.news_presentation_service import claim_reading_reason
from app.services.news_sources import NewsSource
from app.services.taglish_extraction_service import extract_taglish_flood_facts
from test_news_processing import queue_db

URL = "https://tribune.net.ph/2026/09/24/minor-flooding-hits-some-metro-areas"
BODY = (
    "On Thursday afternoon, flooding affected roads in Mandaluyong City, according to the Metropolitan Manila Development Authority.\n"
    "As of 4:34 p.m., 10-inch floodwater was recorded along Boni Avenue at the corner of F. Ortigas Street in Mandaluyong. "
    "Officials confirmed the road remained passable to all types of vehicles.\n"
    "In Manila, approximately 8 inches of gutter-deep flooding affected Quirino Avenue near Guazon Street, "
    "while an 8-inch flood was reported on Gov. Pascual Avenue in Sitio 6, Malabon City.\n"
    "Floodwaters receded in affected areas of Quezon City.\n"
    "Flooding along East Avenue corner EDSA cleared by 3:20 p.m., while water along Aurora Boulevard at Araneta Avenue subsided by 3:29 p.m."
)


def article(body: str = BODY) -> NewsArticleExtractorInput:
    return NewsArticleExtractorInput(article_id=-24, canonical_url=URL, publisher="Daily Tribune",
        title="Minor flooding hits some metro areas", article_text=body,
        published_at=datetime.fromisoformat("2026-09-25T04:41:00+08:00"))


def roads(body: str = BODY) -> dict:
    return {c.canonical_road: c for c in extract_taglish_flood_facts(article(body)).claims if c.place_type == "street"}


def test_replay_keeps_five_reported_sites_and_crossing_roads_as_qualifiers() -> None:
    claims = roads()
    assert set(claims) == {"Boni Avenue", "Quirino Avenue", "Gov. Pascual Avenue", "East Avenue", "Aurora Boulevard"}
    assert claims["Boni Avenue"].road_segment_raw == "Boni Avenue at the corner of F. Ortigas Street"
    assert claims["Quirino Avenue"].road_segment_raw == "Quirino Avenue near Guazon Street"
    assert claims["Aurora Boulevard"].road_segment_raw == "Aurora Boulevard at Araneta Avenue"
    assert claims["Gov. Pascual Avenue"].local_area_raw == "Sitio 6"


def test_replay_keeps_each_roads_own_city_depth_and_passability() -> None:
    claims = roads()
    assert claims["Boni Avenue"].canonical_city == "City of Mandaluyong"
    assert claims["Boni Avenue"].depth_raw == "10-inch"
    assert claims["Boni Avenue"].road_passability == "passable_all"
    assert claims["Quirino Avenue"].canonical_city == "City of Manila"
    assert claims["Quirino Avenue"].depth_raw == "approximately 8 inches"
    assert claims["Gov. Pascual Avenue"].canonical_city == "City of Malabon"
    assert claims["Gov. Pascual Avenue"].depth_raw == "8-inch"
    assert all(claims[name].canonical_city == "Quezon City" for name in ["East Avenue", "Aurora Boulevard"])
    assert all(claims[name].depth_raw is None for name in ["East Avenue", "Aurora Boulevard"])


def test_replay_does_not_extract_manila_from_agency_name() -> None:
    claims = extract_taglish_flood_facts(article()).claims
    assert not any(c.raw_place_name == "Manila" and "Development Authority" in c.evidence_sentence for c in claims)


def test_article_city_summaries_are_context_and_keep_original_evidence() -> None:
    claims = extract_taglish_flood_facts(article()).claims
    city_summaries = [c for c in claims if c.place_type == "city" and c.canonical_city in {"City of Mandaluyong", "Quezon City"}
                      and not any(road in c.evidence_sentence for road in ["Boni", "East", "Aurora"])]
    assert len(city_summaries) == 2
    for claim in city_summaries:
        assert not claim.flood_mentioned
        assert "location_context_only" in claim.uncertainty_reasons
        assert claim_reading_reason(claim) is not None
        start, end = claim.evidence_sentence_offset
        assert BODY[start:end] == claim.evidence_sentence
        assert claim.canonical_road is None and claim.event_time_resolved is None
    assert city_summaries[0].depth_raw is None  # The paraphrased lead has no measured depth.


@pytest.mark.parametrize("specific", [
    "",  # City-only report must still appear.
    " Quirino Avenue in Manila was flooded with 8 inches of water.",  # Other city.
    " Boni Avenue in Mandaluyong might flood tomorrow.",
    " Boni Avenue in Mandaluyong was not flooded.",
    " A flood-control project on Boni Avenue in Mandaluyong was approved.",
])
def test_city_report_survives_without_a_specific_actual_flood_in_that_city(specific: str) -> None:
    body = "10-inch flooding was recorded in Mandaluyong City." + specific
    claim = next(c for c in extract_taglish_flood_facts(article(body)).claims
                 if c.place_type == "city" and c.canonical_city == "City of Mandaluyong")
    assert claim.flood_mentioned and "location_context_only" not in claim.uncertainty_reasons
    assert claim_reading_reason(claim) is None


@pytest.mark.parametrize("reason", ["photo_caption_only", "city_context_ambiguous", "contradictory_update"])
def test_unreliable_specific_place_cannot_hide_a_city_observation(reason: str) -> None:
    from app.services.taglish_extraction_service import mark_city_summaries_as_context
    city = extract_taglish_flood_facts(article("10-inch flooding was recorded in Mandaluyong City.")).claims[0]
    street = roads()["Boni Avenue"].model_copy(deep=True)
    street.uncertainty_reasons.append(reason)
    mark_city_summaries_as_context([city, street])
    assert city.flood_mentioned and "location_context_only" not in city.uncertainty_reasons


def test_explicitly_different_observation_times_keep_the_city_observation() -> None:
    from app.services.taglish_extraction_service import mark_city_summaries_as_context
    city = extract_taglish_flood_facts(article("10-inch flooding was recorded in Mandaluyong City.")).claims[0]
    street = roads()["Boni Avenue"].model_copy(deep=True)
    city.event_time_resolved = datetime.fromisoformat("2026-09-24T14:00:00+08:00")
    city.event_time_kind = "observation"
    mark_city_summaries_as_context([city, street])
    assert city.flood_mentioned and "location_context_only" not in city.uncertainty_reasons


def test_replay_cleared_roads_are_subsided_with_distinct_original_times() -> None:
    claims = roads()
    assert claims["Boni Avenue"].event_time_resolved.isoformat() == "2026-09-24T16:34:00+08:00"
    for name, clock in [("East Avenue", "15:20"), ("Aurora Boulevard", "15:29")]:
        claim = claims[name]
        assert claim.condition == "subsided"
        assert claim.event_time_resolved.isoformat() == f"2026-09-24T{clock}:00+08:00"
        assert claim.event_time_kind == "observation"


def test_replay_reader_sql_and_detail_agree_and_offsets_remain_exact() -> None:
    with create_engine("sqlite+pysqlite:///:memory:").connect() as db:
        for claim in roads().values():
            assert claim_reading_reason(claim) is None
            fields = claim.model_dump()
            fields["uncertainty_reasons"] = json.dumps(fields["uncertainty_reasons"])
            assert db.scalar(select(readable_claim(lambda field: literal(fields.get(field)))))
            start, end = claim.evidence_sentence_offset
            assert BODY[start:end] == claim.evidence_sentence
            assert BODY[claim.place_char_start:claim.place_char_end] == claim.raw_place_name


@pytest.mark.asyncio
async def test_actual_processing_entry_keeps_historical_and_cleared_claims_out_of_activation(monkeypatch) -> None:
    from app.services.hybrid_extraction_service import HybridExtractionService
    def forbidden(*args, **kwargs):
        pytest.fail("Historical replay attempted external audit")
    monkeypatch.setattr(HybridExtractionService, "audit_claim_with_llm", forbidden)
    result = await extract_captured_news_article(article())
    assert result.error is None and result.extraction is not None
    claims = {c.canonical_road: c for c in result.extraction.claims if c.place_type == "street"}
    assert len(claims) == 5
    assert all(c.action_type != "auto_approved" for c in claims.values())
    assert all(not c.road_placement.may_affect_routing for c in claims.values())
    assert claims["East Avenue"].action_type == "suppressed_subsided"


def test_regular_tribune_streamed_body_excludes_sidebar_and_preserves_paragraphs() -> None:
    source = NewsSource("replay", "Daily Tribune", ("tribune.net.ph",), (), None, False)
    html = ('<article><h1>Minor flooding</h1></article>'
            '<div hidden id="S:18"><div class="story-text"><p>Flooding affected Boni Avenue in Mandaluyong.</p></div></div>'
            '<aside><p>Flooding on a different road in Cebu City.</p></aside>'
            '<div hidden id="S:1a"><div class="story-text"><p>Floodwater on Boni Avenue was 10 inches deep. Officials said the road remained passable to all vehicles.</p></div></div>')
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(
            200, text=html, headers={"content-type": "text/html"}))) as client:
        body, error = fetch_article_text(source, URL, client)
    assert error is None
    assert body == ("Flooding affected Boni Avenue in Mandaluyong.\nFloodwater on Boni Avenue was 10 inches deep. "
                    "Officials said the road remained passable to all vehicles.")


@pytest.mark.parametrize("body", [
    BODY.replace("On Thursday afternoon", "On Thursday afternoon, September 10"),
    BODY.replace("On Thursday afternoon", "On Thursday afternoon yesterday"),
    BODY + "\nOn Wednesday afternoon, flooding affected roads in Pasig City.",
    BODY.replace("On Thursday afternoon", "On Monday afternoon"),
])
def test_ambiguous_or_old_event_calendar_does_not_invent_observation_date(body: str) -> None:
    assert roads(body)["Boni Avenue"].event_time_resolved is None


def test_anaphoric_passability_does_not_cross_paragraphs_or_choose_between_roads() -> None:
    split_paragraph = BODY.replace("Mandaluyong. Officials", "Mandaluyong.\nOfficials")
    assert roads(split_paragraph)["Boni Avenue"].road_passability == "unknown"
    ambiguous = ("Boni Avenue and F. Ortigas Street in Mandaluyong had flooding. "
                 "Officials confirmed the road remained passable to all vehicles.")
    assert all(c.road_passability == "unknown" for c in roads(ambiguous).values())


def test_cleared_forecast_and_project_completion_cannot_pass_new_reader_pattern() -> None:
    from app.services.news_discovery_service import body_has_metro_manila_flood_claim
    from app.services.news_feed_service import NewsEntry
    entry = NewsEntry("replay", "Daily Tribune", "replay", URL, "Metro Manila flood update", "", URL, article().published_at)
    for body in ["Flood-control works on East Avenue in Quezon City were cleared for construction.",
                 "Flooding on East Avenue in Quezon City might subside by 3:20 p.m."]:
        assert not body_has_metro_manila_flood_claim(entry, body)


def test_explicit_road_city_does_not_keep_a_homonymous_barangays_psgc() -> None:
    claim = roads("Roxas Boulevard in Manila was flooded with gutter-deep water.")["Roxas Boulevard"]
    assert claim.canonical_city == "City of Manila" and claim.psgc_code == "1380600000"
    assert claim_reading_reason(claim) is None


@pytest.mark.asyncio
async def test_durable_queue_and_main_reader_preserve_historical_evidence(queue_db) -> None:
    from app.crud.news import save_candidate
    from app.crud.news_results import list_result_rows
    from app.crud.news_collection import list_collection
    from app.models.news import NewsArticleVersion
    from app.services.news_discovery_service import NewsCandidate
    from app.services.news_feed_service import NewsEntry
    from app.services.news_processing_service import process_saved_news

    entry = NewsEntry("replay", "Daily Tribune", "historical-replay", URL, article().title, "", URL, article().published_at)
    with queue_db() as db, db.begin():
        row = save_candidate(db, entry, NewsCandidate(entry.source_id, entry.publisher, entry.feed_id, URL,
            entry.title, "", entry.published_at, entry.published_at, BODY, None))
        article_id = row.id
    processed = await process_saved_news(queue_db)
    assert processed.completed == 1 and not processed.failed
    with queue_db() as db:
        rows, total, _, _ = list_result_rows(db, page=1, page_size=100, search="", publisher=None,
            condition=None, placement=None, order="publication_newest")
        assert total >= 5
        claims = [json.loads(row["claim"]) if isinstance(row["claim"], str) else row["claim"] for row in rows]
        road_claims = {c["canonical_road"]: c for c in claims if c["place_type"] == "street"}
        assert len(road_claims) == 5
        assert total == 5  # City summaries remain evidence, not additional sites.
        assert road_claims["East Avenue"]["condition"] == "subsided"
        assert road_claims["Boni Avenue"]["road_passability"] == "passable_all"
        version = db.query(NewsArticleVersion).filter_by(article_id=article_id).one()
        assert datetime.fromisoformat(version.input_snapshot["published_at"]) == entry.published_at
        assert version.input_snapshot["article_text"] == BODY
        collection, count, _, _, _ = list_collection(db, page=1, page_size=12, search="", publisher=None, status="all")
        assert count == 1 and tuple(collection[0][4:]) == ("ready", 5, 0)
        _, attention_count, _, _, _ = list_collection(db, page=1, page_size=12, search="", publisher=None, status="attention")
        assert attention_count == 0


def test_context_qualifier_flag_cannot_become_a_separate_readable_flood() -> None:
    claim = next(c for c in extract_taglish_flood_facts(article()).claims if "location_context_only" in c.uncertainty_reasons)
    claim.flood_mentioned = True  # The context flag is an independent reader guard.
    fields = claim.model_dump()
    fields["uncertainty_reasons"] = json.dumps(fields["uncertainty_reasons"])
    with create_engine("sqlite+pysqlite:///:memory:").connect() as db:
        assert not db.scalar(select(readable_claim(lambda field: literal(fields.get(field)))))
    assert claim_reading_reason(claim) is not None


def test_discovery_accepts_historical_replay_clock_but_rejects_real_current_age(monkeypatch) -> None:
    from app.services import news_discovery_service as discovery
    from test_news_discovery import rss
    feed = "https://tribune.net.ph/feed"
    source = NewsSource("replay", "Daily Tribune", ("tribune.net.ph",), (feed,), datetime.now().date(), True)
    feed_xml = rss(f'<item><title>{article().title}</title><link>{URL}</link>'
                   '<pubDate>Thu, 24 Sep 2026 20:41:00 GMT</pubDate></item>')
    calls = []
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, content=feed_xml) if str(request.url) == feed else httpx.Response(
            200, text='<div class="story-text"><p>' + BODY.replace("\n", "</p><p>") + '</p></div>',
            headers={"content-type": "text/html"})
    class ReplayClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromisoformat("2026-09-25T05:00:00+08:00").astimezone(tz)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        monkeypatch.setattr(discovery, "datetime", ReplayClock)
        run = discovery.discover_news((source,), client)
        assert len(run.candidates) == 1
        monkeypatch.setattr(discovery, "datetime", datetime)
        calls.clear()
        current = discovery.discover_news((source,), client)
        assert not current.candidates and calls == [feed]
