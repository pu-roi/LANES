import threading
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from app.services import carriageway_service as service
from app.services import report_service


ORIGINAL = [[121.0, 14.0], [121.0, 14.001]]
OPPOSITE_REVERSED = [[121.0001, 14.001], [121.0001, 14.0]]


def edge(
    *,
    name: str = "Example Avenue",
    traversability: str = "forward",
    way_id: int = 1,
    road_class: str = "primary",
    length: float = 0.111,
) -> dict[str, Any]:
    return {
        "names": [name],
        "traversability": traversability,
        "way_id": way_id,
        "road_class": road_class,
        "length": length,
    }


def test_narrow_two_way_uses_one_centerline(monkeypatch):
    monkeypatch.setattr(service, "trace_road_attributes", lambda _coords: {"edges": [edge(traversability="both")]})

    road_type, opposite = service.find_opposite_carriageway(ORIGINAL)

    assert road_type == "NARROW_TWO_WAY"
    assert opposite is None


def test_distinct_right_side_carriageway_is_accepted(monkeypatch):
    calls = 0

    def trace(_coords):
        nonlocal calls
        calls += 1
        if calls == 1:
            return {"edges": [edge(way_id=1)]}
        if calls == 2:  # Positive/left probe finds the original edge again.
            return {"edges": [edge(way_id=1)], "shape": "candidate"}
        return {"edges": [edge(way_id=2)], "shape": "candidate"}

    monkeypatch.setattr(service, "trace_road_attributes", trace)
    monkeypatch.setattr(service, "decode_polyline6", lambda _shape: OPPOSITE_REVERSED)

    road_type, opposite = service.find_opposite_carriageway(ORIGINAL)

    assert road_type == "DIVIDED_CARRIAGEWAY"
    assert opposite == {"type": "LineString", "coordinates": list(reversed(OPPOSITE_REVERSED))}
    assert calls == 3


def test_same_way_id_is_never_accepted_as_opposite(monkeypatch):
    responses = iter(
        [{"edges": [edge(way_id=1)]}]
        + [{"edges": [edge(way_id=1)], "shape": "candidate"}] * 10
    )
    monkeypatch.setattr(service, "trace_road_attributes", lambda _coords: next(responses))
    monkeypatch.setattr(service, "decode_polyline6", lambda _shape: OPPOSITE_REVERSED)

    road_type, opposite = service.find_opposite_carriageway(ORIGINAL)

    assert road_type == "TRUE_ONE_WAY"
    assert opposite is None


def test_split_way_id_on_same_physical_line_is_rejected(monkeypatch):
    too_close = [[121.000005, 14.001], [121.000005, 14.0]]
    responses = iter(
        [{"edges": [edge(way_id=1)]}]
        + [{"edges": [edge(way_id=2)], "shape": "candidate"}] * 10
    )
    monkeypatch.setattr(service, "trace_road_attributes", lambda _coords: next(responses))
    monkeypatch.setattr(service, "decode_polyline6", lambda _shape: too_close)

    road_type, opposite = service.find_opposite_carriageway(ORIGINAL)

    assert road_type == "TRUE_ONE_WAY"
    assert opposite is None


def test_unrelated_nearby_road_is_rejected(monkeypatch):
    responses = iter(
        [{"edges": [edge(name="Example Avenue", way_id=1)]}]
        + [{"edges": [edge(name="Parking Access", way_id=2)], "shape": "candidate"}] * 10
    )
    monkeypatch.setattr(service, "trace_road_attributes", lambda _coords: next(responses))
    monkeypatch.setattr(service, "decode_polyline6", lambda _shape: OPPOSITE_REVERSED)

    road_type, opposite = service.find_opposite_carriageway(ORIGINAL)

    assert road_type == "TRUE_ONE_WAY"
    assert opposite is None


def test_mixed_traversability_is_ambiguous(monkeypatch):
    monkeypatch.setattr(
        service,
        "trace_road_attributes",
        lambda _coords: {"edges": [
            edge(traversability="both", length=0.05),
            edge(traversability="forward", way_id=2, length=0.05),
        ]},
    )

    road_type, opposite = service.find_opposite_carriageway(ORIGINAL)

    assert road_type == "AMBIGUOUS"
    assert opposite is None


def test_route_is_split_when_road_or_traversability_changes():
    route = [[121.0, 14.0], [121.0, 14.001], [121.0, 14.002], [121.0, 14.003]]
    trace = {
        "edges": [
            {"begin_shape_index": 0, "end_shape_index": 1, "names": ["Caruncho Avenue"], "traversability": "forward"},
            {"begin_shape_index": 1, "end_shape_index": 2, "names": ["Urbano Velasco Avenue"], "traversability": "forward"},
            {"begin_shape_index": 2, "end_shape_index": 3, "names": ["Urbano Velasco Avenue"], "traversability": "both"},
        ]
    }

    assert service._split_route_by_topology(route, trace) == [
        [route[0], route[1]],
        [route[1], route[2]],
        [route[2], route[3]],
    ]


def test_parallel_component_removes_a_junction_connector():
    original = [[121.0, 14.0], [121.0, 14.001]]
    candidate_reversed = [
        [121.0001, 14.001],
        [121.0001, 14.0002],
        [121.0, 14.0002],
        [121.0, 14.0],
    ]

    assert service._longest_parallel_component(original, candidate_reversed) == [
        [121.0001, 14.001],
        [121.0001, 14.0002],
    ]


def test_y_merge_transition_is_retained_only_at_matching_road_endpoints():
    original = [[121.0, 14.0], [121.0, 14.001]]
    candidate_reversed = [
        [121.0001, 14.001],
        [121.0001, 14.0002],
        [121.0, 14.0],
    ]
    parallel_reversed = [[121.0001, 14.001], [121.0001, 14.0002]]

    assert service._candidate_with_validated_merge_transitions(
        original, candidate_reversed, parallel_reversed
    ) == candidate_reversed


def test_unattached_transition_is_not_retained():
    original = [[121.0, 14.0], [121.0, 14.001]]
    candidate_reversed = [
        [121.0001, 14.001],
        [121.0001, 14.0002],
        [121.0004, 14.0],
    ]
    parallel_reversed = [[121.0001, 14.001], [121.0001, 14.0002]]

    assert service._candidate_with_validated_merge_transitions(
        original, candidate_reversed, parallel_reversed
    ) == parallel_reversed


def test_mixed_route_can_keep_a_verified_shorter_counterpart():
    candidate_reversed = [[121.0001, 14.00055], [121.0001, 14.0]]

    assert service._candidate_is_valid(
        ORIGINAL,
        [edge(way_id=1)],
        candidate_reversed,
        [edge(way_id=2, length=0.061)],
        service.MIN_PARTIAL_COUNTERPART_RATIO,
        service.MIN_PARTIAL_COUNTERPART_OVERLAP,
        service.MIN_PARTIAL_LATERAL_SEPARATION_METERS,
    )


def test_long_legal_driving_loop_falls_back_to_selected_segment(monkeypatch):
    loop = [[121.0, 14.0], [121.01, 14.0], [121.0, 14.001]]
    monkeypatch.setattr(service, "_request_route_geometry", lambda _start, _end: loop)

    preview = service.build_road_segment_preview(ORIGINAL[0], ORIGINAL[-1])

    assert preview["road_type"] == "AMBIGUOUS"
    assert preview["validation_status"] == "fallback"
    assert preview["original"]["coordinates"] == ORIGINAL
    assert preview["opposite"] is None


def test_route_snapped_to_wrong_nearby_road_falls_back(monkeypatch):
    displaced_route = [[121.001, 14.0], [121.001, 14.001]]
    monkeypatch.setattr(service, "_request_route_geometry", lambda _start, _end: displaced_route)

    preview = service.build_road_segment_preview(ORIGINAL[0], ORIGINAL[-1])

    assert preview["road_type"] == "AMBIGUOUS"
    assert preview["validation_status"] == "fallback"
    assert preview["original"]["coordinates"] == ORIGINAL
    assert preview["opposite"] is None


def test_valid_snapped_route_returns_road_only_geometry(monkeypatch):
    snapped = [[121.0, 14.0001], [121.0, 14.0009]]
    reverse_snapped = list(reversed(snapped))
    classified = {}
    monkeypatch.setattr(
        service,
        "_request_route_geometry",
        lambda start, _end: snapped if start == ORIGINAL[0] else reverse_snapped,
    )
    def classify(coords, _name):
        classified["coordinates"] = coords
        return "NARROW_TWO_WAY", None

    monkeypatch.setattr(service, "find_opposite_carriageway", classify)

    preview = service.build_road_segment_preview(ORIGINAL[0], ORIGINAL[-1])

    coordinates = preview["original"]["coordinates"]
    assert coordinates == snapped
    assert ORIGINAL[0] not in coordinates
    assert ORIGINAL[-1] not in coordinates
    assert classified["coordinates"] == snapped


def test_shorter_reverse_route_is_normalized_to_start_end(monkeypatch):
    long_route = [[121.0, 14.0], [121.003, 14.0], [121.0, 14.001]]
    reverse_route = [[121.0, 14.001], [121.0, 14.0]]
    monkeypatch.setattr(
        service,
        "_request_route_geometry",
        lambda start, _end: long_route if start == ORIGINAL[0] else reverse_route,
    )
    monkeypatch.setattr(service, "find_opposite_carriageway", lambda coords, _name: ("NARROW_TWO_WAY", None))

    preview = service.build_road_segment_preview(ORIGINAL[0], ORIGINAL[-1])

    assert preview["original"]["coordinates"] == ORIGINAL
    assert preview["road_type"] == "NARROW_TWO_WAY"
    assert preview["coverage_geometry"] == preview["original"]


def test_directional_route_checks_run_concurrently(monkeypatch):
    rendezvous = threading.Barrier(2)

    def route(start, _end):
        rendezvous.wait(timeout=1.0)
        return ORIGINAL if start == ORIGINAL[0] else list(reversed(ORIGINAL))

    monkeypatch.setattr(service, "_request_route_geometry", route)
    monkeypatch.setattr(service, "find_opposite_carriageway", lambda coords, _name: ("NARROW_TWO_WAY", None))

    preview = service.build_road_segment_preview(ORIGINAL[0], ORIGINAL[-1])

    assert preview["validation_status"] == "validated"
    assert preview["original"]["coordinates"] == ORIGINAL


def test_valhalla_unavailable_never_fabricates_opposite(monkeypatch):
    monkeypatch.setattr(service, "_request_route_geometry", lambda _start, _end: None)

    preview = service.build_road_segment_preview(ORIGINAL[0], ORIGINAL[-1])

    assert preview["road_type"] == "AMBIGUOUS"
    assert preview["opposite"] is None
    assert preview["coverage_geometry"]["type"] == "LineString"


def test_opposite_probe_outage_is_unmapped_not_true_one_way(monkeypatch):
    calls = 0

    def trace(_coords):
        nonlocal calls
        calls += 1
        return {"edges": [edge(way_id=1)]} if calls == 1 else None

    monkeypatch.setattr(service, "trace_road_attributes", trace)

    road_type, opposite = service.find_opposite_carriageway(ORIGINAL)

    assert road_type == "UNMAPPED"
    assert opposite is None


def test_preview_endpoint_accepts_raw_anchors(monkeypatch):
    expected = service._preview_result(
        ORIGINAL,
        None,
        "NARROW_TWO_WAY",
        "validated",
        "One centerline covers both directions.",
    )
    monkeypatch.setattr(service, "build_road_segment_preview", lambda **_kwargs: expected)

    response = TestClient(app).post(
        "/api/v1/reports/preview-bidirectional",
        json={"start": ORIGINAL[0], "end": ORIGINAL[-1], "is_bidirectional": True},
    )

    assert response.status_code == 200
    assert response.json()["road_type"] == "NARROW_TWO_WAY"
    assert response.json()["coverage_geometry"]["type"] == "LineString"


def test_public_report_persistence_revalidates_submitted_road_geometry(monkeypatch):
    captured = {}

    def preview(**kwargs):
        captured.update(kwargs)
        return service._preview_result(
            ORIGINAL,
            {"type": "LineString", "coordinates": list(reversed(OPPOSITE_REVERSED))},
            "DIVIDED_CARRIAGEWAY",
            "validated",
            "Both mapped carriageways were verified.",
        )

    monkeypatch.setattr(report_service, "build_road_segment_preview", preview)

    # The import-level dependency used by process_new_report is now the full
    # authoritative builder, not the old detector-only compatibility export.
    result, road_type = report_service.validate_report_road_geometry(
        {"type": "LineString", "coordinates": ORIGINAL},
        "Example Avenue",
        True,
    )

    assert captured["start"] == ORIGINAL[0]
    assert captured["end"] == ORIGINAL[-1]
    assert result["type"] == "MultiLineString"
    assert road_type == "DIVIDED_CARRIAGEWAY"


def test_single_road_report_persistence_revalidates_submitted_geometry(monkeypatch):
    captured = {}

    def preview(**kwargs):
        captured.update(kwargs)
        return service._preview_result(
            ORIGINAL,
            None,
            "SINGLE_DIRECTION",
            "validated",
            "The selected road segment is ready.",
        )

    monkeypatch.setattr(report_service, "build_road_segment_preview", preview)

    result, road_type = report_service.validate_report_road_geometry(
        {"type": "LineString", "coordinates": ORIGINAL},
        "Example Avenue",
        False,
    )

    assert captured["start"] == ORIGINAL[0]
    assert captured["end"] == ORIGINAL[-1]
    assert captured["is_bidirectional"] is False
    assert result == {"type": "LineString", "coordinates": ORIGINAL}
    assert road_type == "SINGLE_DIRECTION"
