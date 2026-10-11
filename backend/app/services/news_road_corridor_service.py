"""Recognize one bounded road corridor while retaining its mapped carriageways.

Only two close parallel source lines between the same named crossings qualify.
This groups location evidence, not confirmed flooded directions or water width.
Original candidates remain available for review and provenance.
"""
from __future__ import annotations

from shapely.geometry import MultiLineString, Point, mapping, shape

from app.schemas.news_placement import PlacementSection
from app.services.article_road_match_service import normalize_name
from app.services.noah_vector_catalog_service import metric_geometry
from app.services.placement_geometry_service import geometry_id, line_parts

# Maximum separation for recognizing nearby representations of one road.
# It does not extend the affected road length or alter the 25-m zone margin.
MAX_CARRIAGEWAY_SEPARATION_METRES = 25.0


def bounded_road_corridors(candidates: list[PlacementSection]) -> list[PlacementSection]:
    groups: dict[tuple, list[PlacementSection]] = {}
    for candidate in candidates:
        if (candidate.kind != "road_section" or candidate.article_place_level < 1
                or len(candidate.cross_streets) != 2 or not all(candidate.cross_streets)
                or candidate.fragment_status != "available" or not candidate.preview_geometry):
            continue
        anchors = tuple(sorted(tuple(sorted(normalize_name(name) for name in end))
                               for end in candidate.cross_streets))
        if set(anchors[0]) & set(anchors[1]):
            continue
        groups.setdefault(anchors, []).append(candidate)
    corridors = []
    for members in groups.values():
        if len(members) != 2:
            continue  # A third branch/duplicate is unresolved, never dropped.
        if sum(len(member.modeled_fragments) for member in members) > 512:
            continue
        members.sort(key=lambda item: item.candidate_id)
        originals = [shape(member.centerline_geojson) for member in members]
        if any(line.geom_type != "LineString" or not line.is_simple for line in originals):
            continue
        left, right = map(metric_geometry, originals)
        if (left.intersects(right) or min(left.length, right.length) < .8 * max(left.length, right.length)
                or left.hausdorff_distance(right) > MAX_CARRIAGEWAY_SEPARATION_METRES):
            continue
        # Anchor names and corresponding endpoint coordinates must agree, not
        # just a short nearest-point distance between unrelated roads.
        endpoint_distances = []
        for names, coordinate in zip(members[0].cross_streets, (left.coords[0], left.coords[-1])):
            key = {normalize_name(name) for name in names}
            positions = [coordinate2 for names2, coordinate2 in zip(
                members[1].cross_streets, (right.coords[0], right.coords[-1]))
                if key == {normalize_name(name) for name in names2}]
            if len(positions) != 1:
                break
            endpoint_distances.append(Point(coordinate).distance(Point(positions[0])))
        if len(endpoint_distances) != 2 or max(endpoint_distances) > MAX_CARRIAGEWAY_SEPARATION_METRES:
            continue
        core = MultiLineString(originals)
        preview_parts = [part for member in members for part in line_parts(shape(member.preview_geometry))]
        preview = MultiLineString(preview_parts)
        overlaps = {period: {hazard: sum(member.modeled_overlap_m[period][hazard] for member in members)
                             for hazard in (1, 2, 3)} for period in (5, 25, 100)}
        length = left.length + right.length
        corridors.append(PlacementSection(
            candidate_id="osm-corridor:" + geometry_id(":".join(m.candidate_id for m in members), core),
            kind="road_section", centerline_geojson=mapping(core),
            osm_way_ids=sorted({way for member in members for way in member.osm_way_ids}),
            cross_streets=members[0].cross_streets, ambiguous_carriageway=False,
            carriageway_candidate_ids=[member.candidate_id for member in members],
            article_place_level=min(member.article_place_level for member in members),
            approximate_length_m=length, modeled_overlap_m=overlaps,
            modeled_overlap_fraction={p: min(1.0, sum(overlaps[p].values()) / length) for p in overlaps},
            matching_history=members[0].matching_history,
            modeled_fragments=[fragment for member in members for fragment in member.modeled_fragments],
            preview_geometry=mapping(preview), fragment_status="available"))
    return corridors
