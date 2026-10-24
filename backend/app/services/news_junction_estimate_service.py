"""Opt-in, source-matched junction display estimates using checked NOAH vectors.

The 25 m review window is application policy, not measured flood extent. A tie
between adjoining sections identifies one junction; it never invents a wetter
side, transfers article depth, or authorizes a write by itself.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any

from shapely import set_srid, union_all
from shapely.affinity import scale
from shapely.geometry import LineString, Point, mapping, shape

from app.crud.news_publication import NewsPublicationError
from app.services.article_road_match_service import normalize_name
from app.services.news_ner_durable.contracts import sha
from app.services.generated_corridor_geometry_service import generated_corridor_intersection
from app.services.news_placement_preview_service import get_news_placement_preview_service
from app.services.news_road_placement_service import city_key
from app.services.noah_vector_catalog_service import X_METRES, Y_METRES, metric_geometry, tile_keys
from app.services.operational_footprint_service import validate_operational_shape
from app.services.placement_geometry_service import LINE_PRECISION_METRES, line_parts, source_aligned_line_union

VERSION = 'source-junction-noah-v1'
RADIUS_METRES = 25.0


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise NewsPublicationError(reason)


@dataclass(frozen=True)
class JunctionEstimate:
    geometry: dict
    evidence: dict
    checksum: str


def contained_core(line: Any, source: Any, window: Any, parent: Any) -> Any:
    """Round only new cut vertices inward by ULPs, within source precision.

    Interpolating a cut on an administrative edge can land one representable
    float outside it. Original OSM vertices are retained; no physical gap is
    bridged and every returned line must pass exact containment predicates.
    """
    originals = set(map(tuple, source.coords)); coordinates = []
    tolerance = metric_geometry(source).buffer(LINE_PRECISION_METRES)
    def neighbors(value: float) -> list[float]:
        result = [value]
        for direction in (-math.inf, math.inf):
            current = value
            for _ in range(4):
                current = math.nextafter(current, direction); result.append(current)
        return result
    for coordinate in map(tuple, line.coords):
        point = Point(coordinate)
        if (parent.covers(point) and window.covers(point) if coordinate in originals
                else parent.contains(point) and window.contains(point)):
            coordinates.append(coordinate); continue
        require(coordinate not in originals, 'junction_original_vertex_outside_bounds')
        options = [(x,y) for x in neighbors(coordinate[0]) for y in neighbors(coordinate[1])
                   if parent.contains(Point(x,y)) and window.contains(Point(x,y))
                   and tolerance.covers(metric_geometry(Point(x,y)))]
        require(bool(options), 'junction_cut_vertex_precision_unresolved')
        coordinates.append(min(options,key=lambda p:metric_geometry(Point(p)).distance(metric_geometry(point))))
    result = LineString(coordinates)
    require(parent.covers(result) and window.covers(result) and tolerance.covers(metric_geometry(result)),
            'junction_source_core_containment_unresolved')
    return result


def matched_junction(claim: Any, candidates: list) -> tuple[Point, int]:
    section = claim.road_segment_raw or ''
    names = re.split(r'\s+(?:cor\.?|corner(?:\s+of)?)\s+', section, flags=re.I)
    require(len(names) == 2 and bool(claim.canonical_city) and bool(claim.canonical_barangay)
            and normalize_name(names[0]) == normalize_name(claim.canonical_road or ''),
            'junction_reported_intersection_required')
    require(len(candidates) == 2, 'junction_two_adjoining_sections_required')
    lines, node_sets, ways = [], [], []
    for c in candidates:
        require(c.kind == 'road_section' and not c.ambiguous_carriageway,
                'junction_bounded_ground_level_sections_required')
        match = re.fullmatch(r'osm:(\d+)-(\d+):bgy:[a-f0-9]{64}', c.candidate_id)
        require(match is not None, 'junction_catalog_node_binding_required')
        node_sets.append(set(map(int, match.groups())))
        line = shape(c.centerline_geojson)
        require(line.geom_type == 'LineString' and line.is_simple and not line.is_empty,
                'junction_source_line_invalid')
        lines.append(line); ways.append(set(c.osm_way_ids))
    nodes = node_sets[0] & node_sets[1]
    endpoints = lambda line: {tuple(line.coords[0]), tuple(line.coords[-1])}
    common = endpoints(lines[0]) & endpoints(lines[1])
    require(len(nodes) == 1 and len(common) == 1 and bool(ways[0] & ways[1]),
            'junction_sections_do_not_share_one_mapped_junction')
    coordinate = next(iter(common))
    for c, line in zip(candidates, lines, strict=True):
        end = 0 if tuple(line.coords[0]) == coordinate else 1
        require(any(normalize_name(n) == normalize_name(names[1]) for n in c.cross_streets[end]),
                'junction_cross_street_not_bound_to_shared_endpoint')
    return Point(*coordinate), next(iter(nodes))


def build_junction_estimate(claim: Any, *, service: Any = None) -> JunctionEstimate:
    service = service or get_news_placement_preview_service()
    preview = service.preview(claim)
    require(preview.reason == 'multiple_equally_supported_sections'
            and not preview.candidates_truncated and not preview.uncertainty_reasons,
            'junction_complete_tied_preview_required')
    candidates = preview.candidates
    point, node_id = matched_junction(claim, candidates)
    locality = service.roads.locality_boundary(claim)
    require(locality is not None and locality.covers(point), 'junction_outside_reported_locality')
    # As in the connected-road policy, a barangay identifies the source
    # junction but is not a physical flood edge at a boundary road.
    city = service.roads.boundaries.get(city_key(claim.canonical_city))
    require(city is not None and city.covers(point), 'junction_city_boundary_unavailable')
    parent = set_srid(city, 4326)
    ways = {w.osm_id: w for w in service.roads.catalog.ways}
    for c in candidates:
        require(c.fragment_status == 'available' and bool(c.modeled_fragments)
                and set(c.modeled_overlap_m) == {5, 25, 100}, 'junction_noah_evidence_incomplete')
        for way_id in c.osm_way_ids:
            w = ways.get(way_id)
            require(w is not None and w.bridge in ('', 'no') and w.tunnel in ('', 'no')
                    and w.layer in ('', '0'), 'junction_grade_unresolved')
    require(bool(preview.osm_catalog_sha256) and bool(preview.noah_catalog_sha256),
            'junction_asset_binding_required')
    window = scale(metric_geometry(point).buffer(RADIUS_METRES),
                   xfact=1 / X_METRES, yfact=1 / Y_METRES, origin=(0, 0))
    require(parent.covers(window), 'junction_review_window_crosses_city_boundary')
    noah = service.noah
    require(noah.manifest is not None and set(noah.manifest.scenarios) == {5, 25, 100},
            'junction_all_noah_scenarios_required')
    envelope = union_all([g for period in (5, 25, 100)
        for key in tile_keys(window.bounds, noah.manifest.tile_size)
        for g in noah._tile(period, key).values()])
    core_parts = []
    for c in candidates:
        source = shape(c.centerline_geojson)
        pieces = [part for fragment in c.modeled_fragments
                  for part in line_parts(shape(fragment.centerline_geojson).intersection(window))]
        core_parts.extend(contained_core(part,source,window,parent.intersection(envelope))
                          for part in line_parts(source_aligned_line_union(source, pieces)))
    require(bool(core_parts), 'junction_no_modeled_road_overlap')
    sources = union_all(core_parts)
    try:
        extent = generated_corridor_intersection(window, parent, sources)
        extent = generated_corridor_intersection(extent, envelope, sources)
    except ValueError as exc:
        raise NewsPublicationError('junction_geometry_precision_unresolved') from exc
    polygons = [extent] if extent.geom_type == 'Polygon' else list(getattr(extent, 'geoms', ()))
    retained = [p for p in polygons if p.geom_type == 'Polygon' and line_parts(sources.intersection(p))]
    require(bool(retained), 'junction_no_modeled_road_overlap')
    geometry = set_srid(union_all(retained), 4326)
    validation = validate_operational_shape(geometry, geometry_srid=4326, parent_boundary=parent)
    require(validation.is_eligible, validation.reason_code)
    cores = [mapping(union_all(line_parts(sources.intersection(shape(p))))) for p in validation.polygon_parts]
    evidence = dict(policy_version=VERSION, placement_revision=service.revision,
        osm_catalog_sha256=preview.osm_catalog_sha256, noah_catalog_sha256=preview.noah_catalog_sha256,
        junction_osm_node_id=node_id, junction=mapping(point), estimated_radius_metres=RADIUS_METRES,
        measured_flood_extent=False, proves_current_flood=False,
        administrative_boundaries_clip=False, junction_inside_reported_barangay=True,
        selection_basis='same_reported_junction_with_equal_modeled_susceptibility',
        candidate_ids=[c.candidate_id for c in candidates],
        source_centerlines=[c.centerline_geojson for c in candidates], component_centerlines=cores,
        source_node_coordinates=[[node_id,point.x,point.y]],
        noah_source_ids=preview.noah_source_ids,
        scenario_measurements=[dict(candidate_id=c.candidate_id, length_metres=c.approximate_length_m,
            modeled_overlap_m=c.modeled_overlap_m, modeled_overlap_fraction=c.modeled_overlap_fraction)
            for c in candidates])
    return JunctionEstimate(validation.geojson, evidence, sha(dict(geometry=validation.geojson,evidence=evidence)))
