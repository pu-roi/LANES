"""Server-derived estimated road corridors from current checked placement assets.

The existing 25-m road-zone margin is a routing/display policy, not measured
water width. Only a uniquely selected, article-grounded OSM/NOAH section enters
this path; independent current flood auditing remains the activation service's
responsibility. Every disconnected component retains its own source line.
"""
from __future__ import annotations

from dataclasses import dataclass

from shapely import set_srid, union_all
from shapely.affinity import scale
from shapely.geometry import MultiLineString, MultiPolygon, mapping, shape

from app.crud.news_evaluation import canonical_sha256
from app.crud.news_publication import NewsPublicationError
from app.schemas.news_extraction import ExtractedClaim
from app.schemas.news_publication import EstimatedRoadEvidence
from app.services.news_placement_preview_service import NewsPlacementPreviewService, get_news_placement_preview_service
from app.services.noah_vector_catalog_service import X_METRES, Y_METRES, metric_geometry
from app.services.operational_footprint_service import validate_operational_shape
from app.services.placement_geometry_service import LINE_PRECISION_METRES, line_parts


@dataclass(frozen=True)
class EstimatedRoadZone:
    geometry: dict
    evidence: EstimatedRoadEvidence
    source_id: str
    checksum: str


def estimated_road_asset_revision() -> str:
    return get_news_placement_preview_service().revision


def build_estimated_road_zone(claim: ExtractedClaim, *,
        service: NewsPlacementPreviewService | None = None) -> EstimatedRoadZone:
    service = service or get_news_placement_preview_service()
    placement = service.roads.resolve(claim)
    preview = service.preview(claim, placement)
    if preview.status != "predicted_candidate" or not preview.selected_candidate_id:
        raise NewsPublicationError(preview.reason)
    if preview.candidates_truncated or preview.uncertainty_reasons:
        raise NewsPublicationError("estimated_road_evidence_incomplete")
    selected = [item for item in preview.candidates if item.candidate_id == preview.selected_candidate_id]
    if len(selected) != 1:
        raise NewsPublicationError("estimated_road_selection_ambiguous")
    candidate = selected[0]
    if candidate.carriageway_candidate_ids and claim.road_passability != "passable_all":
        # A road-level location estimate must not turn unknown lane access into
        # a closure on both mapped carriageways. Depth/access is independently
        # rechecked at persistence; deeper conflicts remain review-only.
        raise NewsPublicationError("estimated_corridor_access_unresolved")
    if candidate.article_place_level < 1 or candidate.ambiguous_carriageway:
        raise NewsPublicationError("estimated_road_requires_grounded_section")
    if candidate.fragment_status != "available" or not candidate.preview_geometry or not candidate.modeled_fragments:
        raise NewsPublicationError("estimated_road_requires_noah_overlap")
    if not preview.osm_catalog_sha256 or not preview.noah_catalog_sha256:
        raise NewsPublicationError("estimated_road_assets_unavailable")
    ways = {way.osm_id: way for way in service.roads.catalog.ways}
    for way_id in candidate.osm_way_ids:
        way = ways.get(way_id)
        if way is None or way.bridge not in ("", "no") or way.tunnel not in ("", "no") or way.layer not in ("", "0"):
            raise NewsPublicationError("estimated_road_elevation_unresolved")
    parent = service.roads.locality_boundary(claim)
    if parent is None:
        raise NewsPublicationError("missing_qualified_locality_boundary")
    parent = set_srid(parent, 4326)
    line = shape(candidate.preview_geometry)
    original = shape(candidate.centerline_geojson)
    if (line.geom_type not in ("LineString", "MultiLineString") or not line.is_valid
            or not parent.covers(line)
            or not metric_geometry(original).buffer(LINE_PRECISION_METRES).covers(metric_geometry(line))
            or metric_geometry(line).length > metric_geometry(original).length + LINE_PRECISION_METRES):
        raise NewsPublicationError("estimated_road_line_outside_supported_section")
    parts = line_parts(line)
    if not 1 <= len(parts) <= 25 or sum(len(part.coords) for part in parts) > 10000:
        raise NewsPublicationError("estimated_road_component_limit")
    polygons, cores, owners = [], [], []
    original_parts = line_parts(original)
    continuous_owners = {index for index, source in enumerate(original_parts)
                         if any(metric_geometry(part).buffer(LINE_PRECISION_METRES).covers(metric_geometry(source))
                                for part in parts)}
    for part in parts:
        # Generate inside the qualified parent; never clip an external supplied
        # footprint. Do not dissolve separate buffered fragments across gaps.
        buffered = scale(metric_geometry(part).buffer(25.0), xfact=1 / X_METRES,
                         yfact=1 / Y_METRES, origin=(0, 0)).intersection(parent)
        if buffered.geom_type != "Polygon" or not buffered.is_valid or not buffered.covers(part):
            raise NewsPublicationError("estimated_road_corridor_incomplete")
        supported_by = [index for index, source in enumerate(original_parts)
                        if metric_geometry(source).buffer(LINE_PRECISION_METRES).covers(metric_geometry(part))]
        if len(supported_by) != 1:
            raise NewsPublicationError("estimated_road_component_source_ambiguous")
        owner = supported_by[0]
        if any(buffered.intersects(existing) and (
                not candidate.carriageway_candidate_ids
                or (owner == existing_owner and not (continuous_owners - {owner})))
               for existing, existing_owner in zip(polygons, owners)):
            raise NewsPublicationError("estimated_road_corridors_would_bridge_gap")
        polygons.append(buffered)
        cores.append(mapping(part))
        owners.append(owner)
    if candidate.carriageway_candidate_ids:
        # Dissolve overlapping policy margins for this certified single road
        # corridor. Keep both exact source lines and their modeled gaps; there
        # is no interpolated median or duplicate translucent polygon.
        # An uninterrupted supported carriageway can carry the corridor margin
        # past a modeled gap on its counterpart, but no gap is filled in either
        # source core. A gap across both carriageways still fails above.
        merged = union_all(polygons)
        if merged.geom_type not in ("Polygon", "MultiPolygon") or not merged.is_valid:
            raise NewsPublicationError("estimated_road_corridor_incomplete")
        polygons = [merged] if merged.geom_type == "Polygon" else list(merged.geoms)
        cores = []
        for polygon in polygons:
            contained = [part for part in parts if polygon.covers(part)]
            if not contained:
                raise NewsPublicationError("estimated_road_corridor_incomplete")
            cores.append(mapping(contained[0] if len(contained) == 1 else MultiLineString(contained)))
    extent = polygons[0] if len(polygons) == 1 else MultiPolygon(polygons)
    validated = validate_operational_shape(set_srid(extent, 4326), geometry_srid=4326, parent_boundary=parent)
    if not validated.is_eligible:
        raise NewsPublicationError(validated.reason_code)
    # Match each line to the exact validated polygon component.
    by_hash = {canonical_sha256(mapping(polygon)): core for polygon, core in zip(polygons, cores)}
    ordered = [by_hash[canonical_sha256(part)] for part in validated.polygon_parts]
    policy_version = "news-estimated-road-v2" if candidate.carriageway_candidate_ids else "news-estimated-road-v1"
    evidence = EstimatedRoadEvidence(policy_version=policy_version,
        candidate_id=candidate.candidate_id, placement_revision=service.revision,
        osm_catalog_sha256=preview.osm_catalog_sha256, noah_catalog_sha256=preview.noah_catalog_sha256,
        component_centerlines=ordered, carriageway_candidate_ids=candidate.carriageway_candidate_ids)
    checksum = canonical_sha256({"evidence": evidence.model_dump(mode="json"), "geometry": validated.geojson})
    return EstimatedRoadZone(validated.geojson, evidence, policy_version, checksum)
