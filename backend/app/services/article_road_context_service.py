"""Ground article and Pasig DRRMO place clues to bounded OSM road sections.

This is read-only placement evidence. An unmatched historical row is never
silently assigned to a road section, and no result verifies a live flood.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry

from app.schemas.news_extraction import ExtractedClaim
from app.services.article_road_match_service import (
    OSMRoadSection,
    _span_cross_streets,
    normalize_name,
)


@dataclass(frozen=True)
class GroundedHistoryRow:
    source_year: str
    source_record_no: str
    barangay: str
    street: str
    landmark: str
    section_ids: tuple[str, ...]


@dataclass(frozen=True)
class RoadContextResult:
    candidate_section_ids: tuple[str, ...]
    article_place_levels: dict[str, int]
    historical_rows_by_section: dict[str, tuple[GroundedHistoryRow, ...]]
    unmatched_history_rows: tuple[GroundedHistoryRow, ...]
    reason: str


def _contains_name(text: str, name: str) -> bool:
    """Find complete normalized road words; C. and G. Raymundo stay distinct."""
    value, target = normalize_name(text), normalize_name(name)
    if not value or not target:
        return False
    if re.search(r"(?:^|\s)" + re.escape(target) + r"(?:\s|$)", value):
        return True
    parts = target.split()
    suffixes = {"street", "avenue", "road", "boulevard", "highway", "drive", "lane"}
    if parts[-1] not in suffixes:
        return False
    base = " ".join(parts[:-1])
    if not base:
        return False
    for match in re.finditer(r"(?:^|\s)" + re.escape(base) + r"(?=\s|$)", value):
        following = value[match.end():].strip().split()
        if not following or following[0] not in suffixes:
            return True
    return False


def _is_pasig(city: str | None) -> bool:
    return normalize_name(city or "") in {"pasig", "pasig city", "city of pasig"}


def match_article_road_context(
    claim: ExtractedClaim,
    sections: Sequence[OSMRoadSection],
    city_boundary: BaseGeometry,
    pasig_csv: Path | None = None,
    barangay_boundary: BaseGeometry | None = None,
) -> RoadContextResult:
    """Match precise article clues first, then ground Pasig history by road and crossing.

    ``barangay_boundary`` must be a verified polygon for the article barangay.
    Without it, a barangay name does not establish which side of a road lies
    in that barangay. Historical rows with no mapped crossing stay unmatched.
    """
    if not claim.canonical_city or city_boundary.is_empty or not city_boundary.is_valid:
        raise ValueError("A named article city and checked city boundary are required")
    road = claim.canonical_road or claim.raw_place_name
    eligible = [section for section in sections
                if normalize_name(section.road_name) == normalize_name(road)
                and city_boundary.covers(LineString(section.centerline_geojson["coordinates"]))]
    ids = {section.section_id for section in eligible}
    if len(ids) != len(eligible):
        raise ValueError("OSM road section IDs must be unique")
    if not eligible:
        return RoadContextResult((), {}, {}, (), "named_road_not_found")
    if barangay_boundary is not None and (barangay_boundary.is_empty or not barangay_boundary.is_valid):
        raise ValueError("Barangay boundary must be a valid geometry")

    levels: dict[str, int] = {section.section_id: 0 for section in eligible}
    if claim.canonical_barangay and barangay_boundary is not None:
        for section in eligible:
            if barangay_boundary.covers(LineString(section.centerline_geojson["coordinates"])):
                levels[section.section_id] = 1

    span = _span_cross_streets(claim.road_segment_raw)
    if span is not None:
        for section in eligible:
            first, second = section.end_cross_streets
            if (any(_contains_name(name, span[0]) for name in first)
                    and any(_contains_name(name, span[1]) for name in second)) or (
                    any(_contains_name(name, span[1]) for name in first)
                    and any(_contains_name(name, span[0]) for name in second)):
                levels[section.section_id] = 3
        matched = tuple(section_id for section_id, level in levels.items() if level == 3)
        if not matched:
            return RoadContextResult((), levels, {}, (), "reported_span_not_grounded")
    else:
        local_clue = " ".join(filter(None, (claim.local_area_raw, claim.road_segment_raw)))
        if local_clue:
            for section in eligible:
                if any(_contains_name(local_clue, name) for end in section.end_cross_streets for name in end):
                    levels[section.section_id] = 2
        strongest = max(levels.values())
        matched = tuple(section_id for section_id, level in levels.items()
                        if level == strongest) if strongest else tuple(levels)

    history: dict[str, list[GroundedHistoryRow]] = {section_id: [] for section_id in matched}
    unmatched: list[GroundedHistoryRow] = []
    if pasig_csv is not None and _is_pasig(claim.canonical_city):
        with pasig_csv.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                street = (row.get("street_normalized") or "").strip()
                landmark = (row.get("landmark_normalized") or "").strip()
                if not (_contains_name(street, road) or _contains_name(landmark, road)):
                    continue
                barangay = (row.get("barangay_canonical") or "").strip()
                # Never transfer a named barangay's history to another named
                # barangay. Without a boundary, place the row only at a mapped
                # crossing, not along every section of the named road.
                if claim.canonical_barangay and normalize_name(barangay) != normalize_name(claim.canonical_barangay):
                    continue
                crossing_text = landmark if _contains_name(street, road) else street
                section_ids = tuple(section.section_id for section in eligible
                                    if section.section_id in history
                                    and any(_contains_name(crossing_text, name)
                                            for end in section.end_cross_streets for name in end)
                                    and (not claim.canonical_barangay or barangay_boundary is None
                                         or barangay_boundary.covers(LineString(section.centerline_geojson["coordinates"]))))
                record = GroundedHistoryRow(
                    source_year=(row.get("source_year") or "").strip(),
                    source_record_no=(row.get("source_record_no") or "").strip(),
                    barangay=barangay, street=street, landmark=landmark,
                    section_ids=section_ids,
                )
                if section_ids:
                    for section_id in section_ids:
                        history[section_id].append(record)
                else:
                    unmatched.append(record)

    return RoadContextResult(
        candidate_section_ids=matched,
        article_place_levels={section_id: levels[section_id] for section_id in matched},
        historical_rows_by_section={section_id: tuple(rows) for section_id, rows in history.items()},
        unmatched_history_rows=tuple(unmatched),
        reason=("matched_article_place" if max(levels.values()) else
                "local_place_not_grounded" if claim.local_area_raw or claim.road_segment_raw else
                "road_name_only"),
    )
