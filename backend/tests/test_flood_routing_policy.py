from app.services.flood_routing_policy import ActiveFloodZone, evaluate_route, rank_routes, zone_decision


def zone(severity: str, passable_vehicles: str | None = None) -> ActiveFloodZone:
    return ActiveFloodZone(id=1, severity=severity, polygon=[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]], passable_vehicles=passable_vehicles)  # type: ignore[arg-type]


def candidate(duration: float, coordinates: list[list[float]]) -> dict:
    return {"geometry": {"type": "LineString", "coordinates": coordinates}, "distance": 1000.0, "duration": duration, "instructions": [], "is_truncated": False}


def test_mmda_profile_matrix() -> None:
    expected = {
        "low": {"walk": "passable", "motorcycle": "passable", "light": "passable", "heavy": "passable"},
        "medium": {"walk": "cautious", "motorcycle": "blocked", "light": "blocked", "heavy": "cautious"},
        "high": {"walk": "cautious", "motorcycle": "blocked", "light": "blocked", "heavy": "blocked"},
        "extreme": {"walk": "blocked", "motorcycle": "blocked", "light": "blocked", "heavy": "blocked"},
    }
    for severity, profiles in expected.items():
        for profile, decision in profiles.items():
            assert zone_decision(profile, zone(severity)) == decision


def test_official_passability_can_only_restrict() -> None:
    assert zone_decision("light", zone("low", "Pedestrians, Motorcycles")) == "blocked"
    assert zone_decision("heavy", zone("high", "SUVs / Pickups")) == "blocked"
    assert zone_decision("walk", zone("medium", "SUVs / Pickups, Sedans / Hatchbacks")) == "cautious"
    assert zone_decision("walk", zone("medium", "No pedestrians")) == "blocked"


def test_geometry_exposure_is_route_specific() -> None:
    flooded = evaluate_route(candidate(60, [[-1, 1], [3, 1]]), [zone("medium")], "light")
    dry = evaluate_route(candidate(90, [[-1, -1], [-2, -2]]), [zone("medium")], "light")
    assert flooded["blocked"] is True
    assert flooded["flood_exposure"]["zone_count"] == 1
    assert dry["blocked"] is False
    assert dry["flood_exposure"]["zone_count"] == 0


def test_walking_orange_zone_is_cautious_at_40_percent_safety() -> None:
    walking_route = evaluate_route(candidate(60, [[-1, 1], [3, 1]]), [zone("high")], "walk")
    assert walking_route["blocked"] is False
    assert walking_route["flood_exposure"]["highest_severity"] == "high"
    assert walking_route["safety_score"] == 40


def test_ranking_excludes_blocked_baseline_and_uses_categories() -> None:
    blocked = evaluate_route(candidate(50, [[-1, 1], [3, 1]]), [zone("high")], "heavy")
    fastest = evaluate_route(candidate(60, [[-1, -1], [-2, -2]]), [zone("high")], "heavy")
    safest = evaluate_route(candidate(70, [[-1, -2], [-2, -3]]), [zone("high")], "heavy")
    routes, baseline = rank_routes([blocked, fastest, safest])
    assert baseline is not None and baseline["blocked"] is True
    assert all(not route["blocked"] for route in routes)
    assert routes[0]["category"] == "fastest"
    assert routes[0]["duration"] == 60


def test_ranking_deduplicates_categories_and_caps_at_four_cards() -> None:
    flood = zone("low")
    candidates = [
        evaluate_route(candidate(60, [[-1, -1], [-2, -2]]), [flood], "light"),
        evaluate_route(candidate(65, [[-1, -2], [-2, -3]]), [flood], "light"),
        evaluate_route(candidate(70, [[-1, -3], [-2, -4]]), [flood], "light"),
        evaluate_route(candidate(75, [[-1, -4], [-2, -5]]), [flood], "light"),
        evaluate_route(candidate(80, [[-1, -5], [-2, -6]]), [flood], "light"),
    ]
    routes, baseline = rank_routes(candidates)
    assert baseline is None
    assert len(routes) <= 4
    assert len({route["duration"] for route in routes}) == len(routes)
    assert routes[0]["category"] == "fastest"


def test_blocked_baseline_is_only_returned_when_it_is_fastest_raw_candidate() -> None:
    slow_blocked = evaluate_route(candidate(100, [[-1, 1], [3, 1]]), [zone("high")], "light")
    fast_dry = evaluate_route(candidate(60, [[-1, -1], [-2, -2]]), [zone("high")], "light")
    _, baseline = rank_routes([slow_blocked, fast_dry])
    assert baseline is None
