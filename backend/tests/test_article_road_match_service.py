"""Article road matching must not turn ambiguous map evidence into a closure."""

from shapely.geometry import box

from app.schemas.news_extraction import ExtractedClaim
from app.services.article_road_match_service import (
    OSMRoadWay, match_article_road_span, split_named_road_at_intersections,
)


CITY = box(120.99, 14.60, 121.03, 14.67)


def claim(road: str, span: str, barangay: str | None = None) -> ExtractedClaim:
    return ExtractedClaim(
        raw_place_name=road, canonical_road=road, canonical_city="Quezon City",
        canonical_barangay=barangay, road_segment_raw=span, place_type="street",
        place_char_start=0, place_char_end=len(road),
        evidence_sentence=f"Flooding on {road} {span}.",
        evidence_sentence_offset=(0, len(road) + len(span) + 14),
    )


def way(way_id: int, name: str, *nodes: tuple[int, float, float],
        aliases: tuple[str, ...] = (), bridge: str = "") -> OSMRoadWay:
    return OSMRoadWay(way_id, name, nodes, aliases=aliases, bridge=bridge)


def sto_domingo_ways() -> list[OSMRoadWay]:
    return [
        way(9793981, "Santo Domingo Avenue", (1, 121.0, 14.63),
            (2, 121.0, 14.6305), (3, 121.0, 14.631)),
        way(20, "Atok Street", (4, 120.999, 14.63), (1, 121.0, 14.63)),
        way(30, "Calamba Street", (3, 121.0, 14.631), (5, 121.001, 14.631)),
    ]


def test_explicit_sto_domingo_span_is_a_candidate_only() -> None:
    result = match_article_road_span(
        claim("Sto. Domingo Avenue", "between Atok and Calamba Streets"),
        sto_domingo_ways(), CITY, "metro-manila-osm-test",
    )
    assert result.status == "bounded_candidate"
    assert result.osm_way_ids == (9793981,)
    assert result.junction_ids == (1, 3)
    assert result.centerline_geojson["type"] == "LineString"
    assert result.approximate_length_m > 0


def test_from_to_span_and_osm_alt_name_are_supported() -> None:
    roads = [
        way(10, "Araneta Avenue", (1, 121.0, 14.63), (2, 121.0, 14.631)),
        way(20, "Maria Clara Street", (3, 120.999, 14.63), (1, 121.0, 14.63)),
        way(30, "F. Florentino Street", (2, 121.0, 14.631), (4, 121.001, 14.631),
            aliases=("Florentino Street",)),
    ]
    result = match_article_road_span(
        claim("Araneta Avenue", "Araneta Avenue from Maria Clara to Florentino"),
        roads, CITY, "metro-manila-osm-test",
    )
    assert result.status == "bounded_candidate"
    assert result.cross_streets == ("Maria Clara", "Florentino")


def test_unequal_carriageway_paths_remain_unresolved() -> None:
    roads = [
        way(10, "Main Road", (1, 121.0, 14.63), (2, 121.0, 14.6305), (4, 121.0, 14.631)),
        way(11, "Main Road", (1, 121.0, 14.63), (3, 121.002, 14.6305), (4, 121.0, 14.631)),
        way(20, "First Street", (5, 120.999, 14.63), (1, 121.0, 14.63)),
        way(30, "Last Street", (4, 121.0, 14.631), (6, 121.001, 14.631)),
    ]
    result = match_article_road_span(
        claim("Main Road", "between First and Last Streets"), roads, CITY, "osm-test",
    )
    assert result.status == "unresolved"
    assert result.reason == "multiple_named_road_paths"
    assert result.centerline_geojson is None


def test_city_and_barangay_context_must_cover_entire_path() -> None:
    flood = claim("Sto. Domingo Avenue", "between Atok and Calamba Streets", "San Antonio")
    missing = match_article_road_span(flood, sto_domingo_ways(), CITY, "osm-test")
    assert missing.reason == "missing_valid_barangay_boundary"
    outside = match_article_road_span(flood, sto_domingo_ways(), CITY, "osm-test",
                                      box(121.01, 14.63, 121.02, 14.64))
    assert outside.reason == "outside_reported_barangay"
    wrong_city = match_article_road_span(
        claim("Sto. Domingo Avenue", "between Atok and Calamba Streets"),
        sto_domingo_ways(), box(121.01, 14.63, 121.02, 14.64), "osm-test",
    )
    assert wrong_city.reason == "outside_reported_city"


def test_unbounded_or_grade_separated_claim_cannot_be_a_candidate() -> None:
    unbounded = match_article_road_span(
        claim("Sto. Domingo Avenue", "along Sto. Domingo Avenue"),
        sto_domingo_ways(), CITY, "osm-test",
    )
    assert unbounded.reason == "missing_explicit_bounded_span"
    roads = sto_domingo_ways()
    roads[0] = way(9793981, "Santo Domingo Avenue", *roads[0].nodes, bridge="yes")
    bridge = match_article_road_span(
        claim("Sto. Domingo Avenue", "between Atok and Calamba Streets"),
        roads, CITY, "osm-test",
    )
    assert bridge.reason == "grade_separation_requires_review"


def test_long_road_splits_only_between_mapped_cross_streets() -> None:
    roads = [
        way(10, "C. Raymundo Avenue", (1, 121.0, 14.630), (2, 121.0, 14.631)),
        way(11, "C. Raymundo Avenue", (2, 121.0, 14.631), (3, 121.0, 14.632),
            (4, 121.0, 14.633), (5, 121.0, 14.634)),
        way(20, "Bernal Street", (6, 120.999, 14.631), (2, 121.0, 14.631)),
        way(21, "Mercedes Avenue", (7, 120.999, 14.633), (4, 121.0, 14.633)),
    ]
    sections = split_named_road_at_intersections("C. Raymundo Avenue", roads, CITY, "osm-test")
    assert len(sections) == 1
    assert sections[0].section_id == "osm:2-4"
    assert sections[0].osm_way_ids == (11,)
    assert sections[0].end_cross_streets == (("Bernal Street",), ("Mercedes Avenue",))
    assert not sections[0].ambiguous_carriageway


def test_parallel_road_paths_are_kept_ambiguous() -> None:
    roads = [
        way(10, "Main Road", (1, 121.0, 14.630), (2, 121.0, 14.631), (4, 121.0, 14.632)),
        way(11, "Main Road", (1, 121.0, 14.630), (3, 121.002, 14.631), (4, 121.0, 14.632)),
        way(20, "First Street", (5, 120.999, 14.630), (1, 121.0, 14.630)),
        way(21, "Last Street", (4, 121.0, 14.632), (6, 121.001, 14.632)),
    ]
    sections = split_named_road_at_intersections("Main Road", roads, CITY, "osm-test")
    assert len(sections) == 2
    assert all(section.ambiguous_carriageway for section in sections)


def test_road_without_two_mapped_crossings_does_not_invent_section() -> None:
    sections = split_named_road_at_intersections(
        "Santo Domingo Avenue", sto_domingo_ways()[:2], CITY, "osm-test",
    )
    assert sections == []


def test_two_nodes_for_one_cross_street_do_not_define_flood_section() -> None:
    roads = [
        way(10, "Main Road", (1, 121.0, 14.630), (2, 121.0, 14.631)),
        way(20, "Mercedes Avenue", (3, 120.999, 14.630), (1, 121.0, 14.630)),
        way(21, "Mercedes Avenue", (4, 120.999, 14.631), (2, 121.0, 14.631)),
    ]
    assert split_named_road_at_intersections("Main Road", roads, CITY, "osm-test") == []
