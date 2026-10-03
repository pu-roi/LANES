"""Unqualified passability is retained without claiming vehicle eligibility."""
from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.news_extraction import ExtractedClaim, LLMAuditResult, RankedLocationCandidate
from app.services.hybrid_extraction_service import HybridExtractionService
from tests.test_news_september9_extraction import extract


@pytest.mark.parametrize("body, expected", [
    ("Ortigas Avenue in Pasig City was flooded at knee level but remained passable.", "passable_unspecified"),
    ("Ortigas Avenue in Pasig City was flooded at knee level and remained passable.", "passable_unspecified"),
    ("Ortigas Avenue in Pasig City was flooded at knee level. The road remained passable.", "passable_unspecified"),
    ("Ortigas Avenue in Pasig City was flooded at knee level.\nThe road remained passable.", "unknown"),
    ("Ortigas Avenue in Pasig City was flooded at knee level but was not passable.", "unknown"),
    ("Ortigas Avenue in Pasig City was flooded at knee level but was no longer passable.", "unknown"),
    ("Ortigas Avenue in Pasig City was flooded at knee level but was passable only to heavy vehicles.", "unknown"),
    ("Ortigas Avenue in Pasig City was flooded at knee level but was passable for buses only.", "unknown"),
    ("Ortigas Avenue in Pasig City was flooded at knee level. Elsewhere, the road remained passable.", "unknown"),
])
def test_generic_inline_and_single_road_adjacency(body: str, expected: str):
    _, claims = extract(body)
    road = next(c for c in claims if c.canonical_road == "Ortigas Avenue")
    assert road.road_passability == expected
    if expected == "passable_unspecified":
        assert "passable" in road.evidence_sentence


PAIR = ("Quirino Avenue near Guazon Street in Manila was flooded at approximately 8 inches, "
        "while Gov. Pascual Avenue in Sitio 6, Malabon City was flooded at 8 inches.")


def test_two_corridor_anaphor_keeps_both_explicit_sites_and_vehicle_uncertainty():
    body = PAIR + " Traffic remained passable through both corridors."
    _, claims = extract(body)
    roads = [c for c in claims if c.canonical_road]
    assert len(roads) == 2
    assert {c.canonical_city for c in roads} == {"City of Manila", "City of Malabon"}
    assert all(c.road_passability == "passable_unspecified" and c.evidence_sentence == body for c in roads)
    assert all(c.event_time_resolved is None for c in roads)


@pytest.mark.parametrize("tail", [
    "\nTraffic remained passable through both corridors.",
    " Road authorities issued an advisory. Traffic remained passable through both corridors.",
    " Traffic did not remain passable through both corridors.",
    " Traffic remained passable on another corridor.",
])
def test_two_corridor_passability_requires_exact_adjacent_same_paragraph_context(tail: str):
    _, claims = extract(PAIR + tail)
    assert all(c.road_passability == "unknown" for c in claims if c.canonical_road)


def test_both_corridors_does_not_select_two_roads_from_three_candidates():
    _, claims = extract("Ortigas Avenue, Shaw Boulevard and C. Raymundo Avenue in Pasig City were flooded at knee level. "
                        "Traffic remained passable through both corridors.")
    roads = [c for c in claims if c.canonical_road]
    assert len(roads) == 3
    assert all(c.road_passability == "unknown" for c in roads)


@pytest.mark.parametrize("restriction, expected", [
    ("passable with caution", "passable_with_caution"),
    ("passable to all types of vehicles", "passable_all"),
    ("not passable to light vehicles", "light_vehicle_closed"),
    ("impassable to all vehicles", "impassable_all"),
])
def test_general_adjacent_passability_cannot_override_specific_vehicle_fact(restriction: str, expected: str):
    _, claims = extract(f"Ortigas Avenue in Pasig City was flooded at knee level and remained {restriction}. "
                        "The road remained passable.")
    road = next(c for c in claims if c.canonical_road == "Ortigas Avenue")
    assert road.road_passability == expected


def test_generic_passability_blocks_automatic_closure_with_all_other_gates_satisfied():
    now = datetime.now(timezone.utc)
    claim = ExtractedClaim(raw_place_name="Example Avenue", canonical_city="City of Pasig", place_type="street",
        place_char_start=0, place_char_end=14, evidence_sentence="Example Avenue was flooded at knee level but remained passable.",
        evidence_sentence_offset=(0, 61), depth_canonical="knee", condition="active", event_time_kind="observation",
        event_time_resolved=now-timedelta(minutes=10), road_passability="passable_unspecified")
    location = RankedLocationCandidate(raw_place_name="Example Avenue", precision_level="road", resolved_city="City of Pasig",
        geometry_geojson={"type":"Polygon","coordinates":[]}, geometry_provenance="verified_segment", is_auto_approvable=True)
    audit = LLMAuditResult(is_confirmed=True, status_classification="active", depth_confirmed=True)
    service = HybridExtractionService()
    assert service.evaluate_claim_action(claim.model_copy(update={"road_passability":"unknown"}), audit, location, now)[0] == "auto_approved"
    action, reason = service.evaluate_claim_action(claim, audit, location, now)
    assert action == "flagged_review" and "without specified vehicle types" in reason
