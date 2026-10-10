"""Presentation-only linework for one news claim; never activation evidence."""
from __future__ import annotations

from shapely.affinity import scale
from shapely.geometry import MultiLineString, mapping, shape
from shapely.ops import linemerge, unary_union

from app.schemas.configuration import OperationalSettings
from app.schemas.news_placement import NewsPlacementPreview, PlacementDisplaySection, PlacementDisplayZone, PlacementSection
from app.services.noah_vector_catalog_service import X_METRES, Y_METRES, metric_geometry
from app.services.placement_geometry_service import geometry_id, line_parts


def placement_display_sections(candidates: list[PlacementSection]) -> list[PlacementDisplaySection]:
    """Draw coincident coverage once and join exact touching pieces.

    Candidate identities/evidence remain unchanged. No snapping, buffering or
    gap filling is permitted here; parallel carriageways stay separate.
    """
    originals = [(candidate.candidate_id, shape(candidate.preview_geometry))
                 for candidate in candidates if candidate.preview_geometry]
    if not originals:
        return []
    if any(not geometry.is_valid or geometry.geom_type not in ("LineString", "MultiLineString")
           for _, geometry in originals):
        raise ValueError("invalid_news_display_linework")
    union = unary_union([geometry for _, geometry in originals])
    merged = linemerge(union) if union.geom_type != "LineString" else union
    result = []
    for part in line_parts(merged):
        members = sorted(candidate_id for candidate_id, geometry in originals
                         if part.intersection(geometry).length > 0)
        if not members:
            raise ValueError("news_display_line_has_no_source")
        result.append(PlacementDisplaySection(display_id=geometry_id("news-display", part),
                      candidate_ids=members, geometry=mapping(part)))
    return sorted(result, key=lambda item: item.display_id)


def placement_display_zone(sections: list[PlacementDisplaySection]) -> PlacementDisplayZone | None:
    """Use the staff default road margin for a single presentation-only halo.

    The union avoids stacking translucent carriageway/fragment halos. The
    original centerlines keep all gaps; the halo is decoration, not flood
    width, evidence or a routing footprint. No publication data is changed.
    """
    if not sections:
        return None
    lines = [shape(section.geometry) for section in sections]
    core = lines[0] if len(lines) == 1 else MultiLineString(lines)
    margin = OperationalSettings.model_fields["staff_road_buffer_metres"].default
    halo = unary_union([metric_geometry(line).buffer(margin) for line in lines])
    halo = scale(halo, xfact=1 / X_METRES, yfact=1 / Y_METRES, origin=(0, 0))
    return PlacementDisplayZone(candidate_ids=sorted({identity for section in sections for identity in section.candidate_ids}),
                                core_geometry=mapping(core), aura_geometry=mapping(halo))


def resolved_placement_display_zone(preview: NewsPlacementPreview) -> PlacementDisplayZone | None:
    """Supply Active-style geometry only for the resolved placement, not alternatives.

    This is presentation eligibility, never publication or a staff approval.
    Preserve every candidate for inspection, including opposing carriageways.
    """
    if (preview.status != "predicted_candidate" or not preview.selected_candidate_id
            or preview.candidates_truncated or preview.uncertainty_reasons):
        return None
    selected = [candidate for candidate in preview.candidates
                if candidate.candidate_id == preview.selected_candidate_id]
    if len(selected) != 1:
        return None
    candidate = selected[0]
    if (candidate.ambiguous_carriageway or candidate.article_place_level < 1
            or candidate.fragment_status != "available" or not candidate.preview_geometry):
        return None
    return placement_display_zone(placement_display_sections(selected))
