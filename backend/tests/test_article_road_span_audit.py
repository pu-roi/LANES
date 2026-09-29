"""Read-only OSM road-span selection must fail on missing or ambiguous evidence."""

import pytest
from shapely.geometry import LineString

from scripts.audit_article_road_span import (
    city_boundary_from_osm_xml,
    cross_streets_from_span,
    normalize_road_name,
    shortest_named_road_path,
    unique_junction,
)
from scripts.audit_noah_road_intersections import RoadWay


def way(osm_id: int, name: str, nodes: tuple[tuple[int, float, float], ...]) -> RoadWay:
    return RoadWay(osm_id, name, nodes, "residential", "", "", "")


def test_reported_between_span_selects_only_the_cross_street_path() -> None:
    assert normalize_road_name("Sto. Domingo Ave.") == normalize_road_name("Santo Domingo Avenue")
    first, second = cross_streets_from_span("between Atok and Calamba Streets")
    assert (first, second) == ("Atok Street", "Calamba Street")
    main = [way(10, "Santo Domingo Avenue", (
        (1, 121.0, 14.63), (2, 121.0, 14.631), (3, 121.0, 14.632), (4, 121.0, 14.633),
    ))]
    start = unique_junction(main, [way(20, first, ((5, 120.999, 14.631), (2, 121.0, 14.631)))], first)
    end = unique_junction(main, [way(30, second, ((3, 121.0, 14.632), (6, 121.001, 14.632)))], second)
    coords, way_ids, flags = shortest_named_road_path(main, start, end)
    assert coords == [(121.0, 14.631), (121.0, 14.632)]
    assert way_ids == {10} and not flags


def test_missing_or_multiple_cross_street_junctions_are_not_guessed() -> None:
    main = [way(10, "Main Road", ((1, 121.0, 14.63), (2, 121.0, 14.631)))]
    with pytest.raises(ValueError, match="found 0"):
        unique_junction(main, [way(20, "Cross", ((3, 121.001, 14.63), (4, 121.001, 14.631)))], "Cross")
    with pytest.raises(ValueError, match="found 2"):
        unique_junction(main, [way(21, "Cross", ((1, 121.0, 14.63), (2, 121.0, 14.631)))], "Cross")


def test_unconnected_named_road_does_not_create_a_whole_road_candidate() -> None:
    main = [
        way(10, "Main Road", ((1, 121.0, 14.63), (2, 121.0, 14.631))),
        way(11, "Main Road", ((3, 121.0, 14.632), (4, 121.0, 14.633))),
    ]
    with pytest.raises(ValueError, match="No connected"):
        shortest_named_road_path(main, 2, 3)


def test_equal_length_carriageway_alternatives_are_rejected() -> None:
    main = [
        way(10, "Main Road", ((1, 121.0, 14.63), (2, 121.001, 14.631), (4, 121.0, 14.632))),
        way(11, "Main Road", ((1, 121.0, 14.63), (3, 120.999, 14.631), (4, 121.0, 14.632))),
    ]
    with pytest.raises(ValueError, match="equally short"):
        shortest_named_road_path(main, 1, 4)


def test_unbounded_span_is_rejected() -> None:
    with pytest.raises(ValueError, match="not a supported"):
        cross_streets_from_span("flooding along Santo Domingo Avenue")


def test_complete_city_relation_contains_only_its_own_road_paths() -> None:
    xml = b'''<osm>
      <node id="1" lon="121.0" lat="14.6"/><node id="2" lon="121.02" lat="14.6"/>
      <node id="3" lon="121.02" lat="14.62"/><node id="4" lon="121.0" lat="14.62"/>
      <way id="10"><nd ref="1"/><nd ref="2"/><nd ref="3"/><nd ref="4"/><nd ref="1"/></way>
      <relation id="42"><member type="way" ref="10" role="outer"/>
      <tag k="boundary" v="administrative"/><tag k="admin_level" v="6"/>
      <tag k="name" v="Quezon City"/></relation></osm>'''
    boundary = city_boundary_from_osm_xml(xml, 42, "Quezon City")
    assert boundary.covers(LineString([(121.005, 14.605), (121.01, 14.61)]))
    assert not boundary.covers(LineString([(121.03, 14.605), (121.04, 14.61)]))
    with pytest.raises(ValueError, match="reported city"):
        city_boundary_from_osm_xml(xml, 42, "Pasig")
    with pytest.raises(ValueError, match="incomplete boundary way"):
        city_boundary_from_osm_xml(xml.replace(b'<node id="4" lon="121.0" lat="14.62"/>', b""), 42, "Quezon City")
