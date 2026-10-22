"""Read-only comparison against the existing PSGC and bundled OSM services."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.locality_number_service import normalize_locality_numbers, numbered_localities
from app.services.philippine_location_service import get_philippine_location_service
from app.services.article_road_match_service import normalize_name
from app.services.news_road_placement_service import NewsRoadPlacementProvider


def inspect_place(name: str, context: str, city: str | None = None) -> dict[str, Any]:
    """Return candidates, never assign an annotation or fabricate a map identity."""
    key = normalize_name(name)
    hierarchy = get_philippine_location_service().resolve_location_hierarchy(
        normalize_locality_numbers(name), text_context=context,
    )
    provider = NewsRoadPlacementProvider(Path(__file__).resolve().parents[2] / "runtime_data" / "osm")
    provider._load()
    city_key = normalize_name(city or "").removeprefix("city of ").removesuffix(" city")
    matches = [
        {"osm_type": "node", "osm_id": item.osm_node_id, "name": item.name, "city": item.city,
         "quarter": item.quarter, "reference_url": f"https://www.openstreetmap.org/node/{item.osm_node_id}"}
        for parent, items in provider.localities.items() if parent == city_key
        for item in items if key in {normalize_name(n) for n in (item.name, *item.aliases)}
    ] if city else []
    return {"raw_name": name, "comparison_key": key, "psgc_candidate": hierarchy,
            "numbered_components": [{"kind": n.kind, "number": n.number, "suffix": n.suffix,
                                      "start": n.start, "end": n.end} for n in numbered_localities(name)],
            "osm_locality_candidates": matches, "osm_catalog_error": provider.error,
            "note": "Candidates only; source-supported parent review and road/publication gates remain required."}
