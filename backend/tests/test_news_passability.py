"""Vehicle restrictions remain source-grounded and cannot authorize closures."""
from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.news_extraction import ExtractedClaim, LLMAuditResult, RankedLocationCandidate
from app.services.hybrid_extraction_service import HybridExtractionService
from tests.test_news_september9_extraction import extract


@pytest.mark.parametrize("body, expected", [
    ("Ortigas Avenue in Pasig City was flooded at knee level and remained passable with caution.", "passable_with_caution"),
    ("Ortigas Avenue in Pasig City was flooded at knee level and remained passable to all types of vehicles.", "passable_all"),
    ("Ortigas Avenue in Pasig City was flooded at knee level. The road remained passable with caution.", "passable_with_caution"),
    ("Ortigas Avenue in Pasig City was flooded at knee level.\nThe road remained passable with caution.", "unknown"),
    ("Ortigas Avenue and Shaw Boulevard in Pasig City were flooded at knee level. The road remained passable with caution.", "unknown"),
])
def test_inline_and_adjacent_caution_stays_with_supported_road(body: str, expected: str):
    _, claims = extract(body)
    roads = [c for c in claims if c.canonical_road]
    assert all(c.road_passability == expected for c in roads)
    if expected == "passable_with_caution":
        assert all("passable with caution" in c.evidence_sentence for c in roads)


def test_caution_list_evidence_and_category_reset():
    _, claims = extract("As of 4:30 p.m., the following roads were flooded:\nPasig City\n"
                        "Passable with caution\nOrtigas Avenue - knee deep\n"
                        "Impassable to light vehicles\nShaw Boulevard - waist deep\n"
                        "Classes were suspended.\nC. Raymundo Avenue in Pasig City was flooded at knee level.")
    roads = {c.canonical_road: c for c in claims if c.canonical_road}
    assert roads["Ortigas Avenue"].road_passability == "passable_with_caution"
    assert "Passable with caution" in roads["Ortigas Avenue"].evidence_sentence
    assert roads["Shaw Boulevard"].road_passability == "light_vehicle_closed"
    assert roads["C. Raymundo Avenue"].road_passability == "unknown"


def test_caution_heading_without_article_intro_stays_in_source_evidence():
    body = "Passable with caution\nPasig City\nOrtigas Avenue - knee deep"
    _, claims = extract(body)
    road = next(c for c in claims if c.canonical_road == "Ortigas Avenue")
    assert road.road_passability == "passable_with_caution"
    assert road.evidence_sentence == body


def test_caution_cannot_auto_approve_even_when_audit_and_geometry_pass():
    now = datetime.now(timezone.utc)
    claim = ExtractedClaim(raw_place_name="Example Avenue", canonical_city="City of Pasig", place_type="street",
        place_char_start=0, place_char_end=14, evidence_sentence="Example Avenue was flooded at knee level, passable with caution.",
        evidence_sentence_offset=(0, 63), depth_canonical="knee", condition="active", event_time_kind="observation",
        event_time_resolved=now-timedelta(minutes=10), road_passability="passable_with_caution")
    location = RankedLocationCandidate(raw_place_name="Example Avenue", precision_level="road", resolved_city="City of Pasig",
        geometry_geojson={"type":"Polygon","coordinates":[]}, geometry_provenance="verified_segment", is_auto_approvable=True)
    audit = LLMAuditResult(is_confirmed=True, status_classification="active", depth_confirmed=True, place_confirmed=True, time_confirmed=True)
    service = HybridExtractionService()
    assert service.evaluate_claim_action(claim.model_copy(update={"road_passability":"unknown"}), audit, location, now)[0] == "auto_approved"
    action, reason = service.evaluate_claim_action(claim, audit, location, now)
    assert action == "flagged_review" and "passable with caution" in reason
    assert ExtractedClaim.model_validate(claim.model_dump()).road_passability == "passable_with_caution"
