"""Rank bounded road sections using article place context and NOAH overlap.

The result is a location prediction, not a flood observation or routing decision.
NOAH return periods and Var classes never replace article depth or status.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from shapely.geometry.base import BaseGeometry


RETURN_PERIODS = (5, 25, 100)
OverlapProvider = Callable[[Path, BaseGeometry], dict[int, float]]


@dataclass(frozen=True)
class RoadSectionEvidence:
    section_id: str
    metric_centerline: BaseGeometry
    osm_source_id: str
    # 0 = named road only, 1 = matching barangay, 2 = matching landmark,
    # 3 = explicit article cross-street span. These are evidence levels, not probabilities.
    article_place_level: int = 0
    matching_drrmo_rows: int = 0
    bounded_road_section: bool = False


@dataclass(frozen=True)
class RankedRoadSection:
    section_id: str
    article_place_level: int
    matching_drrmo_rows: int
    modeled_overlap_m: dict[int, dict[int, float]]
    modeled_overlap_fraction: dict[int, float]
    average_modeled_overlap_fraction: float
    average_class_fraction: dict[int, float]
    osm_source_id: str
    bounded_road_section: bool


@dataclass(frozen=True)
class RoadPrediction:
    ranked_sections: tuple[RankedRoadSection, ...]
    predicted_section_id: str | None
    reason: str
    noah_source_ids: dict[int, str]


def rank_noah_road_sections(
    sections: Sequence[RoadSectionEvidence],
    noah_archives: Mapping[int, Path],
    overlap_provider: OverlapProvider,
) -> RoadPrediction:
    """Compare exact line/polygon overlap, retaining every alternative and source.

    A unique leading section is a *predicted map location* only. The caller
    must separately assess article recency, active condition, conflicts,
    corroboration, expiry, and routing geometry before any public write.
    """
    if not sections or len({section.section_id for section in sections}) != len(sections):
        raise ValueError("Provide one or more uniquely identified road sections")
    if set(noah_archives) != set(RETURN_PERIODS):
        raise ValueError("All three Metro Manila NOAH scenarios are required")
    for section in sections:
        if (section.metric_centerline.is_empty or section.metric_centerline.length <= 0
                or section.metric_centerline.geom_type not in {"LineString", "MultiLineString"}
                or not section.osm_source_id or not 0 <= section.article_place_level <= 3
                or section.matching_drrmo_rows < 0):
            raise ValueError(f"Invalid road-section evidence: {section.section_id}")

    ranked: list[RankedRoadSection] = []
    for section in sections:
        overlap_by_scenario: dict[int, dict[int, float]] = {}
        fractions: dict[int, float] = {}
        for period in RETURN_PERIODS:
            measured = overlap_provider(noah_archives[period], section.metric_centerline)
            if set(measured) != {1, 2, 3} or any(length < 0 for length in measured.values()):
                raise ValueError(f"Incomplete NOAH class coverage for {period}-year scenario")
            if sum(measured.values()) > section.metric_centerline.length + 0.1:
                raise ValueError(f"Overlapping NOAH classes exceed road length for {period}-year scenario")
            overlap_by_scenario[period] = measured
            fractions[period] = min(1.0, sum(measured.values()) / section.metric_centerline.length)
        ranked.append(RankedRoadSection(
            section_id=section.section_id,
            article_place_level=section.article_place_level,
            matching_drrmo_rows=section.matching_drrmo_rows,
            modeled_overlap_m=overlap_by_scenario,
            modeled_overlap_fraction=fractions,
            average_modeled_overlap_fraction=sum(fractions.values()) / len(RETURN_PERIODS),
            average_class_fraction={hazard_class: sum(
                overlap_by_scenario[period][hazard_class] / section.metric_centerline.length
                for period in RETURN_PERIODS
            ) / len(RETURN_PERIODS) for hazard_class in (1, 2, 3)},
            osm_source_id=section.osm_source_id,
            bounded_road_section=section.bounded_road_section,
        ))

    # Source place specificity outranks historical record presence; modeled
    # susceptibility breaks remaining ties. DRRMO row counts are not event counts.
    def rank_key(item: RankedRoadSection) -> tuple[int, bool, float, float, float]:
        return (item.article_place_level, item.matching_drrmo_rows > 0,
                round(item.average_modeled_overlap_fraction, 3),
                round(item.average_class_fraction[3], 3),
                round(item.average_class_fraction[2], 3))

    ranked.sort(key=lambda item: (rank_key(item), item.section_id), reverse=True)
    top = ranked[0]
    if not top.bounded_road_section:
        reason = "top_section_has_arbitrary_bounds"
        chosen = None
    elif top.average_modeled_overlap_fraction == 0 and top.article_place_level < 3:
        reason = "no_modeled_overlap_or_explicit_span"
        chosen = None
    elif len(ranked) > 1 and rank_key(top) == rank_key(ranked[1]):
        reason = "multiple_equally_supported_sections"
        chosen = None
    else:
        reason = "unique_ranked_prediction_not_verified_flood_extent"
        chosen = top.section_id
    return RoadPrediction(
        ranked_sections=tuple(ranked), predicted_section_id=chosen,
        reason=reason,
        noah_source_ids={period: str(noah_archives[period]) for period in RETURN_PERIODS},
    )
