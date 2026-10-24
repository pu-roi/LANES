"""Reviewed street roles and rounded corner estimates; no publication authority."""
from __future__ import annotations

import json
import re
from typing import Any

from shapely import set_srid, union_all
from shapely.geometry import LineString, Point, mapping, shape
from sqlalchemy import text

from app.crud.news_publication import NewsPublicationError
from app.services.article_road_match_service import OSMRoadWay, _way_matches, initial_road_aliases, normalize_name
from app.services.news_placement_preview_service import get_news_placement_preview_service
from app.services.news_road_placement_service import city_key, road_aliases, road_initial_aliases
from app.services.noah_vector_catalog_service import metric_geometry, tile_keys
from app.services.operational_footprint_service import validate_operational_shape
from app.services.placement_geometry_service import line_parts

VERSION = 'philstar-reviewed-street-corner-v1'
MAX_ARM_METRES = 25.0
# Exact accepted claim ordinals: these roles were reviewed by the developer.
STREETS = {0: ('Don Jose St', 'NS Amoranto'), 1: ('Palali St', 'NS Amoranto'),
    2: ('Banawe St', 'NS Amoranto'), 3: ('Tabayoc St', 'NS Amoranto'),
    4: ('Ubay St', 'NS Amoranto'), 6: ('Don Jose St', 'Sct Alcaraz St'),
    9: ('G Araneta', 'Kitanlad')}
EXISTING = {1: 88, 2: 83, 3: 89, 6: 84, 9: 85}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise NewsPublicationError(reason)


def name_matches(mapped: str, reported: str) -> bool:
    reported = re.sub(r'\bsct\b','scout',normalize_name(reported))
    return _way_matches(OSMRoadWay(1, mapped, (), initial_aliases=initial_road_aliases(mapped)), reported)


def projected_buffer(db: Any, core: dict, margin: float) -> dict:
    """Same EPSG:32651 ST_Buffer construction as the staff road editor."""
    return json.loads(db.scalar(text("""SELECT ST_AsGeoJSON(ST_Transform(ST_Buffer(
        ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(:core),4326),32651),:margin,
        'quad_segs=8 endcap=round join=round'),4326),12)"""),
        {'core': json.dumps(core), 'margin': margin}))


def bounded_arm(db: Any, line: Any, endpoint: int) -> Any:
    coordinates = list(line.coords)
    if endpoint == 1:
        coordinates.reverse()
    raw = json.dumps(mapping(LineString(coordinates)))
    value = db.scalar(text("""WITH source AS (SELECT ST_Transform(
        ST_SetSRID(ST_GeomFromGeoJSON(:line),4326),32651) g)
        SELECT ST_AsGeoJSON(ST_Transform(ST_LineSubstring(g,0,
        LEAST(1.0,:limit / NULLIF(ST_Length(g),0))),4326),15) FROM source"""),
        {'line': raw, 'limit': MAX_ARM_METRES})
    require(value is not None, 'reviewed_corner_empty_arm')
    return shape(json.loads(value))


def build_reviewed_corner(db: Any, claim: Any, ordinal: int, margin: float,
                          service: Any = None) -> dict:
    require(ordinal in STREETS and 1 <= margin <= 100, 'reviewed_corner_scope_invalid')
    service = service or get_news_placement_preview_service()
    target, reference = STREETS[ordinal]
    reviewed = claim.model_copy(update={'canonical_road':target, 'raw_place_name':target,
        'road_segment_raw':f'{target} cor {reference}'})
    preview = service.preview(reviewed)
    require(not preview.candidates_truncated and not preview.uncertainty_reasons
        and bool(preview.osm_catalog_sha256) and bool(preview.noah_catalog_sha256),
        'reviewed_corner_assets_incomplete')
    # Identify the exact intersection on the reviewed street, not a ranking score.
    incident = []
    for candidate in preview.candidates:
        for end, names in enumerate(candidate.cross_streets):
            if any(name_matches(name, reference) for name in names):
                line = shape(candidate.centerline_geojson)
                coordinate = tuple(line.coords[0 if end == 0 else -1])
                incident.append((candidate, line, end, coordinate))
    anchors = {i[3] for i in incident}
    require(len(anchors) == 1 and 1 <= len(incident) <= 2, 'reviewed_corner_junction_ambiguous')
    coordinate = next(iter(anchors)); point = Point(coordinate)
    locality = service.roads.locality_boundary(reviewed)
    city = service.roads.boundaries.get(city_key(claim.canonical_city or ''))
    require(locality is not None and locality.covers(point) and city is not None and city.covers(point),
        'reviewed_corner_locality_mismatch')
    ways = {w.osm_id:w for w in service.roads.catalog.ways}
    noah = service.noah
    require(noah.manifest is not None and set(noah.manifest.scenarios) == {5,25,100},
        'reviewed_corner_noah_incomplete')
    arms, measurements, identities = [], [], []
    for candidate, line, end, _ in incident:
        require(candidate.kind == 'road_section' and not candidate.ambiguous_carriageway,
            'reviewed_corner_road_ambiguous')
        for way_id in candidate.osm_way_ids:
            way = ways.get(way_id)
            require(way is not None and way.bridge in ('','no') and way.tunnel in ('','no')
                and way.layer in ('','0') and _way_matches(OSMRoadWay(way.osm_id,way.name,(),
                    road_aliases(way),initial_aliases=road_initial_aliases(way)),target),
                'reviewed_corner_wrong_road_or_grade')
        arm = bounded_arm(db, line, end)
        scenario, wet = {}, []
        for period in (5,25,100):
            classes: dict[int,list] = {}
            for key in tile_keys(arm.bounds,noah.manifest.tile_size):
                for hazard, polygon in noah._tile(period,key).items():
                    classes.setdefault(hazard,[]).append(polygon)
            scenario[period] = {int(hazard):round(metric_geometry(arm.intersection(union_all(parts))).length,6)
                for hazard,parts in classes.items()}
            wet.extend(p for parts in classes.values() for p in parts)
        require(bool(wet), 'reviewed_corner_noah_missing')
        pieces = line_parts(arm.intersection(union_all(wet)))
        require(bool(pieces), 'reviewed_corner_no_modeled_road')
        arms.extend(pieces); measurements.append(dict(candidate_id=candidate.candidate_id,
            scenario_class_overlap_metres=scenario, source_centerline=candidate.centerline_geojson,
            estimated_arm=mapping(arm)))
        identities.append(candidate.candidate_id)
    core = union_all(arms)
    # Buffer each supported core; retain gaps in the core, never crop the outer aura.
    polygon = shape(projected_buffer(db,mapping(core),margin))
    validation = validate_operational_shape(set_srid(polygon,4326),geometry_srid=4326)
    require(validation.is_eligible, validation.reason_code)
    require(polygon.covers(core), 'reviewed_corner_buffer_lost_core')
    evidence = dict(policy_version=VERSION, reviewed_street=target, junction_reference=reference,
        interpretation_basis='developer_reviewed_this_article', junction=mapping(point),
        candidate_ids=identities, component_centerlines=[mapping(core)],
        osm_way_ids=sorted({w for c, _line, _end, _point in incident for w in c.osm_way_ids}),
        max_arm_metres=MAX_ARM_METRES, buffer_metres=margin, projection=32651,
        measured_flood_extent=False, proves_current_flood=False, outer_buffer_clipped=False,
        osm_catalog_sha256=preview.osm_catalog_sha256, noah_catalog_sha256=preview.noah_catalog_sha256,
        noah_source_ids=preview.noah_source_ids, scenario_measurements=measurements)
    return dict(geometry=validation.geojson,core=mapping(core),geometry_evidence=evidence,
        label=f'{target} at {reference}')
