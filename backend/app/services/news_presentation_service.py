"""Server-owned labels preserve source uncertainty and separate the two clocks."""

from app.schemas.news_extraction import ExtractedClaim
from app.schemas.news_presentation import NewsFloodSummary
from app.services.news_evidence_policy import has_flood_observation, metro_manila_claim, non_observation_only


def claim_reading_reason(claim: ExtractedClaim) -> str | None:
    """Explain questionable evidence without changing the stored extraction."""
    place = claim.raw_place_name.strip(" ")
    if not place or len(place) > 120 or "\n" in place or (place == claim.evidence_sentence.strip() and len(place) > 60):
        return "The extracted location looks like a sentence or an incomplete place name."
    if not claim.evidence_sentence.strip():
        return "No supporting sentence was saved."
    if "location_context_only" in claim.uncertainty_reasons:
        return "This name provides location context for a reported road, rather than a separate flood site."
    if "photo_caption_only" in claim.uncertainty_reasons:
        return "The flood mention appears only in a photo caption, without reporting-body evidence."
    if non_observation_only(claim.evidence_sentence):
        return "This sentence describes flood prevention or habitual flooding, without a current observation."
    if not metro_manila_claim(claim):
        return "The location is outside Metro Manila or its Metro Manila city is unresolved."
    if not claim.flood_mentioned or claim.is_negated or claim.is_forecast or claim.is_historical:
        return "This mention describes a forecast, past reference or absence of flooding."
    if not has_flood_observation(claim.evidence_sentence):
        return "This sentence does not provide affirmative evidence of actual flooding."
    if (claim.condition == "unknown" and not (claim.depth_raw or "").strip()
            and not (claim.depth_formatted or "").strip()
            and claim.road_passability not in {"impassable_all", "light_vehicle_closed"}):
        return "A place was mentioned, but a flood observation was not clearly extracted."
    return None


def summarize_news_claim(claim: ExtractedClaim) -> NewsFloodSummary:
    location = claim.road_segment_raw or claim.raw_place_name
    if not claim.road_segment_raw and claim.local_area_raw:
        broad_names = {value.casefold() for value in [claim.canonical_barangay, claim.canonical_city, claim.canonical_province] if value}
        if claim.raw_place_name.casefold() in broad_names or claim.raw_place_name.casefold() in claim.local_area_raw.casefold():
            location = claim.local_area_raw
    if claim.road_segment_raw and claim.raw_place_name.casefold() not in location.casefold():
        location = f"{claim.raw_place_name} · {location}"
    # Preserve the reported segment; never invent an intersection or coordinates.
    if len(location.strip()) > 180 or "\n" in location:
        location = claim.raw_place_name
    area = list(dict.fromkeys(value for value in [claim.canonical_barangay, claim.canonical_city, claim.canonical_province] if value and value.casefold() != location.casefold()))
    qualifiers = list(dict.fromkeys(value for value in [claim.local_area_raw] if value and value.casefold() != location.casefold() and value not in area))
    reason = claim_reading_reason(claim)
    condition = {"active": "Flooding reported", "rising": "Water rising", "receding": "Water receding",
                 "subsided": "Floodwater subsided", "unknown": "Condition not stated"}[claim.condition]
    if claim.is_negated:
        condition = "No flooding reported"
    elif claim.is_forecast:
        condition = "Forecast only"
    elif claim.is_historical:
        condition = "Historical flood reference"
    return NewsFloodSummary(
        location=location, area=", ".join(area) or None,
        location_qualifier=" · ".join(qualifiers) or None,
        water_level=claim.depth_formatted or claim.depth_raw or "Not stated in article",
        passability={"passable_all": "Passable to all vehicles",
                     "passable_with_caution": "Passable with caution; vehicle types not specified",
                     "light_vehicle_closed": "Not passable to light vehicles",
                     "impassable_all": "Not passable to any vehicles"}.get(
                         claim.road_passability, "Not stated in article"),
        condition=condition, flood_time=claim.event_time_resolved,
        flood_time_label={"observation": "Flood observed in article", "report": "Flood reported in article",
                          "unspecified": "Flood time in article"}[claim.event_time_kind],
        map_status={"bounded_candidate": "Map location needs confirmation", "ambiguous": "Several possible map locations",
                    "unresolved": "Exact map location unknown", "source_unavailable": "Map data unavailable"}.get(
                        claim.road_placement.status if claim.road_placement else None, "Map location not checked"),
        reading_status="needs_checking" if reason else "reported_location", reading_reason=reason,
    )
