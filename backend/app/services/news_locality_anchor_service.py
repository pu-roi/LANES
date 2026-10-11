"""Source-backed locality points used only to locate an estimated road section.

A point is not a flood polygon or a locality boundary. Candidate bounds remain
the mapped road junctions and all NOAH/publication checks remain downstream.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field
from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry

from app.schemas.news_extraction import ExtractedClaim, RoadPlacementCandidate
from app.services.article_road_match_service import normalize_name
from app.services.noah_vector_catalog_service import metric_geometry
from app.services.placement_geometry_service import LINE_PRECISION_METRES

# Association distance for an OSM neighbourhood centre; never a zone radius.
# Remote names must not select a road elsewhere in the parent city.
MAX_LOCALITY_ROAD_DISTANCE_METRES = 500.0


class CatalogLocality(BaseModel):
    model_config = ConfigDict(extra="forbid")
    osm_node_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=300)
    aliases: list[str] = Field(default_factory=list, max_length=100)
    place: Literal["neighbourhood", "quarter", "suburb", "hamlet", "locality", "village"]
    city: str = Field(min_length=1, max_length=200)
    quarter: str | None = Field(default=None, max_length=200)
    longitude: float = Field(ge=120, le=123, allow_inf_nan=False)
    latitude: float = Field(ge=13, le=16, allow_inf_nan=False)


@dataclass(frozen=True)
class LocalityAnchorMatch:
    reason: str
    locality: CatalogLocality | None = None
    section_ids: frozenset[str] = frozenset()
    distance_metres: float | None = None


def _reference(value: str) -> str:
    return re.sub(r"^(?:in|at|near|sa) ", "", normalize_name(value))


def match_locality_anchor(claim: ExtractedClaim, localities: Sequence[CatalogLocality],
                          candidates: Sequence[RoadPlacementCandidate],
                          boundary: BaseGeometry) -> LocalityAnchorMatch:
    reference = _reference(claim.local_area_raw or "")
    if not reference:
        return LocalityAnchorMatch("local_place_not_grounded")
    # Never discard another unresolved crossing or span to use a place point.
    if claim.road_segment_raw:
        span = normalize_name(claim.road_segment_raw)
        road = normalize_name(claim.canonical_road or "")
        if span not in {reference, f"{road} in {reference}", f"{road} at {reference}",
                         f"in {reference}", f"at {reference}", f"near {reference}"}:
            return LocalityAnchorMatch("local_place_not_grounded")
    matches = [place for place in localities
               if reference in {normalize_name(name) for name in (place.name, *place.aliases)}
               and (not claim.canonical_barangay or
                    normalize_name(place.quarter or "") == normalize_name(claim.canonical_barangay))
               and boundary.covers(Point(place.longitude, place.latitude))]
    if len(matches) != 1:
        return LocalityAnchorMatch("locality_anchor_ambiguous" if matches else "local_place_not_grounded")
    place = matches[0]
    anchor = metric_geometry(Point(place.longitude, place.latitude))
    distances = {}
    for candidate in candidates:
        line = shape(candidate.centerline_geojson)
        if boundary.covers(line) and len(candidate.cross_streets) == 2 and all(candidate.cross_streets):
            distances[candidate.candidate_id] = metric_geometry(line).distance(anchor)
    if not distances:
        return LocalityAnchorMatch("locality_anchor_has_no_bounded_road", place)
    nearest = min(distances.values())
    if nearest > MAX_LOCALITY_ROAD_DISTANCE_METRES:
        return LocalityAnchorMatch("locality_anchor_too_far_from_reported_road", place, distance_metres=nearest)
    ids = frozenset(key for key, distance in distances.items()
                    if distance <= nearest + LINE_PRECISION_METRES)
    return LocalityAnchorMatch("source_locality_anchor_candidate", place, ids, nearest)
