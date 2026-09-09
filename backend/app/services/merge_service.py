import json
import logging
import math
import re
import struct
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from geoalchemy2 import WKBElement
from sqlalchemy import func, or_, and_, desc
from sqlalchemy.orm import Session

from app.models.report import FloodReport, FloodAvoidanceZone, ReportStatus, ReportSeverity
from app.models.user import User
from app.models.profile import Profile
from app.schemas.common import (
    parse_ewkb_point,
    parse_ewkb_linestring,
    parse_ewkb_multilinestring,
    parse_ewkb_polygon,
)
from app.schemas.report import MergeCandidateItem, MergeConflict, MergeCandidatesListResponse
from app.services.carriageway_service import (
    trace_road_attributes,
    find_opposite_carriageway,
    decode_polyline6,
)

logger = logging.getLogger(__name__)

ROAD_SUFFIXES = [
    r"\bavenue\b", r"\bave\b", r"\bstreet\b", r"\bst\b", r"\bboulevard\b", r"\bblvd\b",
    r"\bhighway\b", r"\bhwy\b", r"\broad\b", r"\brd\b", r"\bdrive\b", r"\bdr\b",
    r"\blane\b", r"\bln\b", r"\bextension\b", r"\bext\b", r"\bcircle\b", r"\bcir\b"
]


def normalize_road_name(name: Optional[str]) -> str:
    """
    Normalizes a street/road name by removing common abbreviations, suffixes, and punctuation.
    e.g., 'Ortigas Ave.' -> 'ortigas'
    """
    if not name:
        return ""
    cleaned = name.lower().strip()
    for pattern in ROAD_SUFFIXES:
        cleaned = re.sub(pattern, "", cleaned)
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    return " ".join(cleaned.split())


def calculate_name_similarity(name_a: Optional[str], name_b: Optional[str]) -> float:
    """
    Computes token-based and character-level similarity between two road names.
    Returns 0.0 to 1.0.
    """
    norm_a = normalize_road_name(name_a)
    norm_b = normalize_road_name(name_b)
    if not norm_a or not norm_b:
        return 0.0
    if norm_a == norm_b:
        return 1.0
    if norm_a in norm_b or norm_b in norm_a:
        return 0.85

    # Levenshtein distance ratio
    len_a, len_b = len(norm_a), len(norm_b)
    matrix = [[0] * (len_b + 1) for _ in range(len_a + 1)]
    for i in range(len_a + 1):
        matrix[i][0] = i
    for j in range(len_b + 1):
        matrix[0][j] = j

    for i in range(1, len_a + 1):
        for j in range(1, len_b + 1):
            cost = 0 if norm_a[i - 1] == norm_b[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,
                matrix[i][j - 1] + 1,
                matrix[i - 1][j - 1] + cost
            )
    dist = matrix[len_a][len_b]
    max_len = max(len_a, len_b)
    return 1.0 - (dist / max_len) if max_len > 0 else 0.0


def extract_geojson_geometry(geom_value: Any) -> Optional[dict]:
    """Converts WKBElement or GeoAlchemy object to Python dict GeoJSON."""
    if geom_value is None:
        return None
    try:
        if isinstance(geom_value, dict):
            return geom_value
        if isinstance(geom_value, WKBElement):
            data = bytes.fromhex(geom_value.desc) if isinstance(geom_value.desc, str) else bytes(geom_value.data)
            byte_order = '<' if data[0] == 1 else '>'
            geom_type = struct.unpack(f"{byte_order}I", data[1:5])[0]
            pure_geom_type = geom_type & 0x0fffffff
            
            if pure_geom_type == 1:
                return {"type": "Point", "coordinates": parse_ewkb_point(data)}
            elif pure_geom_type == 2:
                return {"type": "LineString", "coordinates": parse_ewkb_linestring(data)}
            elif pure_geom_type == 3:
                return {"type": "Polygon", "coordinates": parse_ewkb_polygon(data)}
            elif pure_geom_type == 5:
                return {"type": "MultiLineString", "coordinates": parse_ewkb_multilinestring(data)}
    except Exception as e:
        logger.warning(f"Error extracting GeoJSON: {e}")
    return None


def get_linestring_coords(geom: Any) -> List[List[float]]:
    """Extracts a flat list of [lng, lat] coordinate pairs from a geometry."""
    g_dict = extract_geojson_geometry(geom)
    if not g_dict:
        return []
    g_type = g_dict.get("type")
    coords = g_dict.get("coordinates", [])
    if g_type == "LineString":
        return coords
    elif g_type == "MultiLineString" and coords:
        return coords[0]
    elif g_type == "Point" and coords:
        return [coords]
    return []


def calculate_spatial_corridor_overlap(geom_a: Any, geom_b: Any, db: Session) -> float:
    """
    Computes spatial corridor overlap ratio via PostGIS ST_Buffer and ST_Intersection.
    Returns 0.0 to 1.0.
    """
    try:
        query = db.query(
            func.ST_Area(
                func.ST_Intersection(
                    func.ST_Buffer(geom_a, 0.00025),  # ~25 meters
                    func.ST_Buffer(geom_b, 0.00025)
                )
            ).label("intersection_area"),
            func.LEAST(
                func.ST_Area(func.ST_Buffer(geom_a, 0.00025)),
                func.ST_Area(func.ST_Buffer(geom_b, 0.00025))
            ).label("min_area")
        ).first()

        if query and query.min_area and query.min_area > 0:
            ratio = float(query.intersection_area or 0.0) / float(query.min_area)
            return min(1.0, max(0.0, ratio))
    except Exception as e:
        logger.warning(f"Spatial corridor calculation error: {e}")
    return 0.0


def calculate_azimuth_alignment(geom_a: Any, geom_b: Any, db: Session) -> float:
    """
    Checks if lines point in the same direction or opposite directions.
    Returns 1.0 if aligned within 30 degrees (same or opposite for 2-way), else lower.
    """
    try:
        az_a = db.query(func.ST_Azimuth(func.ST_StartPoint(geom_a), func.ST_EndPoint(geom_a))).scalar()
        az_b = db.query(func.ST_Azimuth(func.ST_StartPoint(geom_b), func.ST_EndPoint(geom_b))).scalar()
        if az_a is not None and az_b is not None:
            deg_diff = abs(math.degrees(az_a) - math.degrees(az_b)) % 360
            if deg_diff > 180:
                deg_diff = 360 - deg_diff
            # Same direction (0-30 deg) or opposite direction (150-180 deg)
            if deg_diff <= 30.0 or deg_diff >= 150.0:
                return 1.0
            return max(0.2, 1.0 - (abs(deg_diff - 90.0) / 90.0))
    except Exception:
        pass
    return 0.5


def detect_conflicts(primary: FloodReport, candidate: FloodReport) -> List[MergeConflict]:
    """Identifies discrepancies between two reports that require admin review."""
    conflicts = []

    # 1. Severity Conflict
    sev_rank = {
        ReportSeverity.LOW: 1,
        ReportSeverity.MEDIUM: 2,
        ReportSeverity.HIGH: 3,
        ReportSeverity.EXTREME: 4,
    }
    prim_rank = sev_rank.get(primary.severity, 2)
    cand_rank = sev_rank.get(candidate.severity, 2)
    if prim_rank != cand_rank:
        # Suggest higher severity for disaster safety
        suggested = primary.severity.value if prim_rank > cand_rank else candidate.severity.value
        conflicts.append(MergeConflict(
            field="severity",
            message=f"Conflicting severity: Primary is '{primary.severity.value}', Candidate is '{candidate.severity.value}'",
            suggested_value=suggested
        ))

    # 2. Water Depth Conflict
    if primary.depth and candidate.depth and primary.depth.strip().lower() != candidate.depth.strip().lower():
        conflicts.append(MergeConflict(
            field="depth",
            message=f"Depth mismatch: '{primary.depth}' vs '{candidate.depth}'",
            suggested_value=primary.depth
        ))

    # 3. Passable Vehicles Conflict
    p_veh = primary.survey.passable_vehicles if primary.survey else None
    c_veh = candidate.survey.passable_vehicles if candidate.survey else None
    if p_veh and c_veh and set(p_veh.split(",")) != set(c_veh.split(",")):
        conflicts.append(MergeConflict(
            field="passable_vehicles",
            message="Disagreement on passable vehicle types",
            suggested_value=p_veh
        ))

    return conflicts


def find_merge_candidates(report_id: int, db: Session) -> MergeCandidatesListResponse:
    """
    Core Multi-Factor Candidate Engine:
    Finds pending reports and active zones spatially and topologically related to report_id.
    """
    primary = db.query(FloodReport).filter(FloodReport.id == report_id).first()
    if not primary:
        raise ValueError(f"Report with ID {report_id} not found")

    if not primary.geometry:
        return MergeCandidatesListResponse(
            primary_report=primary,
            candidates=[],
            total_candidates=0,
            detected_conflicts=[]
        )

    # 1. Spatial bounding box pre-filter (~500m radius)
    nearby_reports = db.query(FloodReport).filter(
        FloodReport.id != primary.id,
        FloodReport.status == ReportStatus.PENDING,
        FloodReport.geometry.isnot(None),
        func.ST_DWithin(FloodReport.geometry, primary.geometry, 0.005)  # ~500m
    ).all()

    # 2. Trace primary road network properties (Decision #16 & OSM way_id)
    primary_coords = get_linestring_coords(primary.geometry)
    primary_trace = trace_road_attributes(primary_coords) if len(primary_coords) >= 2 else None

    primary_way_ids = set()
    primary_road_class = None
    primary_road_names = set()
    if primary.human_readable_location:
        primary_road_names.add(primary.human_readable_location.strip().lower())

    if primary_trace and primary_trace.get("edges"):
        for edge in primary_trace["edges"]:
            w_id = edge.get("way_id")
            if w_id:
                primary_way_ids.add(w_id)
            if not primary_road_class and edge.get("road_class"):
                primary_road_class = edge.get("road_class")
            for n in edge.get("names", []):
                primary_road_names.add(n.strip().lower())

    scored_candidates: List[MergeCandidateItem] = []
    all_conflicts: List[MergeConflict] = []

    for cand in nearby_reports:
        match_reasons = []
        score = 0
        cand_coords = get_linestring_coords(cand.geometry)

        # A. Road / Street & OSM Network Identity (Max 35 pts)
        cand_trace = trace_road_attributes(cand_coords) if len(cand_coords) >= 2 else None
        cand_way_ids = set()
        cand_names = set()
        cand_road_class = None

        if cand.human_readable_location:
            cand_names.add(cand.human_readable_location.strip().lower())

        if cand_trace and cand_trace.get("edges"):
            for edge in cand_trace["edges"]:
                w_id = edge.get("way_id")
                if w_id:
                    cand_way_ids.add(w_id)
                if not cand_road_class and edge.get("road_class"):
                    cand_road_class = edge.get("road_class")
                for n in edge.get("names", []):
                    cand_names.add(n.strip().lower())

        # Check OSM way_id direct match
        shared_ways = primary_way_ids.intersection(cand_way_ids)
        shared_osm_way_id = list(shared_ways)[0] if shared_ways else None
        if shared_ways:
            score += 35
            match_reasons.append(f"Identical OSM Way Segment ({len(shared_ways)} shared edges)")
        else:
            # Fallback to normalized road name similarity
            best_sim = 0.0
            for p_name in primary_road_names:
                for c_name in cand_names:
                    sim = calculate_name_similarity(p_name, c_name)
                    if sim > best_sim:
                        best_sim = sim
            if best_sim >= 0.75:
                points = int(best_sim * 30)
                score += points
                match_reasons.append(f"Same Street Name ({int(best_sim * 100)}% match)")
            elif best_sim < 0.4 and cand.barangay == primary.barangay and (cand_names and primary_road_names):
                # Disqualify reports in same barangay on different streets
                continue

        # Firewall: Reject merging highway with service road/alley if classes mismatch drastically
        if primary_road_class and cand_road_class:
            if ("motorway" in primary_road_class or "trunk" in primary_road_class) and ("service" in cand_road_class or "residential" in cand_road_class):
                continue

        # B. Spatial & Topological Corridor Overlap (Max 35 pts)
        overlap_ratio = calculate_spatial_corridor_overlap(primary.geometry, cand.geometry, db)
        if overlap_ratio > 0.05:
            azimuth_weight = calculate_azimuth_alignment(primary.geometry, cand.geometry, db)
            spatial_pts = int(overlap_ratio * 30 * azimuth_weight)
            score += spatial_pts
            match_reasons.append(f"{int(overlap_ratio * 100)}% Corridor Overlap")

        # C. Locality Context (Max 15 pts)
        if primary.city and cand.city and primary.city.lower() == cand.city.lower():
            score += 5
        if primary.barangay and cand.barangay and primary.barangay.lower() == cand.barangay.lower():
            score += 10
            match_reasons.append(f"Same Barangay ({cand.barangay})")

        # D. Temporal Proximity & Crowd Consensus (Max 15 pts)
        time_diff = abs((primary.created_at - cand.created_at).total_seconds()) / 60.0  # in minutes
        if time_diff <= 30:
            score += 15
            match_reasons.append(f"Reported {int(time_diff)} mins apart")
        elif time_diff <= 120:
            score += 10
            match_reasons.append(f"Reported {int(time_diff / 60)} hr apart")
        elif time_diff <= 720:
            score += 5

        # Minimum score threshold to qualify as candidate
        if score >= 45:
            cand_conflicts = detect_conflicts(primary, cand)
            all_conflicts.extend(cand_conflicts)

            # High trust score boost
            trust_score = cand.reporter_trust_score or 100.0
            is_consensus = score >= 80 and time_diff <= 45

            scored_candidates.append(MergeCandidateItem(
                report_id=cand.id,
                road_name=cand.human_readable_location,
                barangay=cand.barangay,
                city=cand.city,
                severity=cand.severity.value,
                depth=cand.depth,
                passable_vehicles=cand.survey.passable_vehicles if cand.survey else None,
                hidden_hazards=cand.survey.hidden_hazards.value if (cand.survey and hasattr(cand.survey.hidden_hazards, 'value')) else None,
                reporter_username=cand.reporter_username,
                reporter_name=cand.reporter_name,
                reporter_trust_score=trust_score,
                media_urls=cand.media_urls,
                raw_text=cand.raw_text,
                reported_at=cand.created_at,
                geometry=extract_geojson_geometry(cand.geometry),
                match_score=min(100, score),
                match_reasons=match_reasons,
                is_crowd_consensus=is_consensus,
                osm_way_id=shared_osm_way_id,
                road_class=cand_road_class,
                corridor_overlap_ratio=round(overlap_ratio, 2),
                conflicts=cand_conflicts
            ))

    # Sort descending by match score
    scored_candidates.sort(key=lambda x: x.match_score, reverse=True)

    # 3. Synthesize Initial Proposed Merged Geometry (Linear Referencing)
    all_reports = [primary] + [cand for cand in nearby_reports if cand.id in [c.report_id for c in scored_candidates[:5]]]
    synthesized_geom, is_bidirectional = synthesize_merged_geometry(all_reports, db=db)

    return MergeCandidatesListResponse(
        primary_report=primary,
        candidates=scored_candidates,
        total_candidates=len(scored_candidates),
        detected_conflicts=all_conflicts,
        suggested_merged_geometry=synthesized_geom,
        is_bidirectional_detected=is_bidirectional
    )


def synthesize_merged_geometry(
    reports: List[FloodReport],
    db: Session,
    is_bidirectional: bool = False
) -> Tuple[Optional[dict], bool]:
    """
    Linear Referencing Geometry Synthesis:
    1. Finds the longest, continuous centerline along the verified road graph.
    2. Projects each report's start and end points via ST_LineLocatePoint (0.0 - 1.0).
    3. Slices the continuous road extent using min(t) and max(t) via ST_LineSubstring.
    4. Evaluates opposite carriageways via Decision #16 if bidirectional is requested or detected.
    """
    valid_geoms = [r.geometry for r in reports if r.geometry is not None]
    if not valid_geoms:
        return None, False

    try:
        # Check if any report is a Polygon (TerraDraw shape)
        for r in reports:
            g_dict = extract_geojson_geometry(r.geometry)
            if g_dict and g_dict.get("type") in ["Polygon", "MultiPolygon"]:
                # If an admin or user drew a polygon, union the shapes
                union_poly = db.query(func.ST_AsGeoJSON(func.ST_UnaryUnion(func.ST_Collect(*valid_geoms)))).scalar()
                if union_poly:
                    return json.loads(union_poly), is_bidirectional

        # Centerline Linear Referencing for LineStrings
        # Find the line that spans the longest distance to serve as the baseline route
        primary_line = valid_geoms[0]
        max_len = 0.0
        for g in valid_geoms:
            length = db.query(func.ST_Length(g)).scalar() or 0.0
            if length > max_len:
                max_len = length
                primary_line = g

        # Compute min(t) and max(t) across all report start and end vertices
        t_values = []
        for g in valid_geoms:
            t_start = db.query(func.ST_LineLocatePoint(primary_line, func.ST_StartPoint(g))).scalar()
            t_end = db.query(func.ST_LineLocatePoint(primary_line, func.ST_EndPoint(g))).scalar()
            if t_start is not None:
                t_values.append(float(t_start))
            if t_end is not None:
                t_values.append(float(t_end))

        min_t = min(t_values) if t_values else 0.0
        max_t = max(t_values) if t_values else 1.0
        if max_t - min_t < 0.01:
            min_t = 0.0
            max_t = 1.0

        merged_line_json = db.query(
            func.ST_AsGeoJSON(func.ST_LineSubstring(primary_line, min_t, max_t))
        ).scalar()

        if merged_line_json:
            merged_dict = json.loads(merged_line_json)
            coords = merged_dict.get("coordinates", [])

            # Check Decision #16 two-way road status
            road_name = reports[0].human_readable_location
            road_type, opp_geom = find_opposite_carriageway(coords, original_road_name=road_name)

            if is_bidirectional or any(r.is_bidirectional for r in reports):
                if road_type == "DIVIDED_CARRIAGEWAY" and opp_geom:
                    opp_coords = opp_geom.get("coordinates", [])
                    return {
                        "type": "MultiLineString",
                        "coordinates": [coords, opp_coords]
                    }, True
                return merged_dict, True

            return merged_dict, (road_type == "NARROW_TWO_WAY")

    except Exception as e:
        logger.warning(f"Error in synthesize_merged_geometry: {e}")

    # Fallback to first report's geometry
    return extract_geojson_geometry(valid_geoms[0]), is_bidirectional
