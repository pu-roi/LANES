"""Read-only zone attention groups. Publication and routing stay independent."""
from typing import Any
from math import isfinite

from shapely.errors import ShapelyError
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
from shapely import STRtree
from sqlalchemy.orm import Session

from app.crud.zone_queue import queue_metadata, queue_zone_details, active_zone_ids
from app.schemas.report import FloodAvoidanceZoneResponse
from app.schemas.spatial_review import SpatialReviewFacets
from app.schemas.zone_queue import ZoneSource, ZoneQueueItem, ZoneQueuePage, ZoneMembersPage
from app.services.merge_service import normalize_road_name
from app.services.news_zone_projection_service import zone_responses_with_news, zone_response_bases, brief_zone_response_bases
from app.services.spatial_grouping import metric_geometry
from app.services.spatial_review_grouping import locality, utc

GROUP_REASON = "Original flood geometries within 50 m on a confirmed matching road and city. Missing or conflicting locations stay separate. Creation time does not limit grouping. Each zone retains its own evidence and actions."
SOURCES = ("user_reports", "news", "official", "other")
SEVERITIES = ("low", "medium", "high", "extreme")


def normalized(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def names(values: list[str | None]) -> list[str]:
    return sorted({normalized(value): value.strip() for value in values if value and value.strip()}.values(), key=str.casefold)


def summary(values: list[str | None]) -> str:
    items = names(values)
    return " · ".join(items[:3]) + (f" · +{len(items) - 3} more" if len(items) > 3 else "")


def original_geometry(row: dict[str, Any], *, projected: bool, geometry_reader: Any = metric_geometry) -> BaseGeometry | None:
    """Use original extents, never the expanded operational avoidance polygon."""
    source = geometry_reader(row.get("source_geometry"), projected=projected)
    if source is not None:
        return source
    reports = [geometry for report in row["reports"]
               if (geometry := geometry_reader(report.get("geometry"), projected=projected)) is not None]
    if not reports:
        return None
    try:
        return unary_union(reports)
    except ShapelyError:
        # Unusable evidence remains browsable as an individual zone.
        return None


def zone_facts(row: dict[str, Any], *, projected: bool, road_normalizer: Any = normalize_road_name,
               geometry_reader: Any = metric_geometry) -> dict[str, Any]:
    reports = row["reports"]
    news = row["news"]
    locations = [(report["human_readable_location"], report["city"], report["barangay"]) for report in reports]
    locations += [(item["claim"].get("canonical_road"), item["claim"].get("canonical_city"),
                   item["claim"].get("canonical_barangay")) for item in news]
    normalized_locations = [(road_normalizer(road), locality(city)) for road, city, _ in locations]
    road_cities = {pair for pair in normalized_locations if pair[0] and pair[1]}
    # Every location must establish the same road and city before grouping.
    reliable = len(road_cities) == 1 and all(road and city for road, city in normalized_locations)
    level_values = [str(getattr(report["severity"], "value", report["severity"])) for report in reports]
    override = getattr(row["severity_override"], "value", row["severity_override"])
    severity = str(override) if override else next((level for level in reversed(SEVERITIES) if level in level_values), "medium")
    depth = row["depth_override"] or next((report["depth"] for report in reports if report["depth"]), None)
    source = "user_reports" if any(str(getattr(report["source"], "value", report["source"])) == "direct_user" for report in reports) else (
        "news" if news else "official" if row["curated_by_admin_id"] is not None else "other")
    public = next(((item["snapshot"].get("public") or {}) for item in news), {})
    evidence = next((report["raw_text"] for report in reports if report["raw_text"]), None) or public.get("evidence_excerpt") or row["admin_notes"] or ""
    searchable = [f"Zone #{row['id']}", row["name"], row["admin_notes"]]
    for report in reports:
        searchable.extend([f"Report #{report['id']}", report["raw_text"], report["human_readable_location"], report["city"], report["barangay"]])
    for item in news:
        saved = item["snapshot"].get("public") or {}
        searchable.extend([saved.get("source_title"), saved.get("evidence_excerpt"), saved.get("location_label")])
        searchable.extend(item["claim"].get(name) for name in ("canonical_road", "canonical_city", "canonical_barangay"))
    return {**row, "metric": geometry_reader(row["geometry"], projected=projected), "locations": locations,
            "group_geometry": original_geometry(row, projected=projected, geometry_reader=geometry_reader),
            "map_geometry": geometry_reader(row.get("map_geometry"), projected=True),
            "road_city": next(iter(road_cities)) if reliable else None, "severity": severity, "depth": depth,
            "source": source, "evidence": evidence, "searchable": normalized(" ".join(str(value or "") for value in searchable)),
            "location": row["name"] or summary([road for road, _, _ in locations]) or public.get("location_label") or f"Zone #{row['id']}",
            "area": summary([", ".join(filter(None, [barangay, city])) for _, city, barangay in locations])}


def related_zones(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if not a["road_city"] or a["road_city"] != b["road_city"]:
        return False
    if a["group_geometry"] is None or b["group_geometry"] is None:
        return False
    return a["group_geometry"].distance(b["group_geometry"]) <= 50.0


def camera_bounds(group: list[dict[str, Any]]) -> tuple[float, float, float, float] | None:
    """WGS84 camera extent of all members, independent of member pagination."""
    extents = [row["map_geometry"].bounds for row in group if row["metric"] is not None and row["map_geometry"] is not None]
    if not extents:
        return None
    west, south = min(bounds[0] for bounds in extents), min(bounds[1] for bounds in extents)
    east, north = max(bounds[2] for bounds in extents), max(bounds[3] for bounds in extents)
    if not all(isfinite(value) for value in (west, south, east, north)) or not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
        return None
    return west, south, east, north


def current_groups(db: Session, *, active_only: bool) -> list[list[dict[str, Any]]]:
    from functools import lru_cache
    # This memo belongs to one read only; evidence/expiry changes are never cached.
    normalize = lru_cache(maxsize=4096)(normalize_road_name)
    projected = db.get_bind().dialect.name == "postgresql"
    decode_binary = lru_cache(maxsize=4096)(metric_geometry)
    def decode(raw: Any, *, projected: bool) -> BaseGeometry | None:
        # Shapely geometries are immutable. Share repeated binary geometry only
        # inside this request, with a bounded cache; unique evidence still decodes.
        return decode_binary(bytes(raw), projected=projected) if isinstance(raw, (bytes, bytearray, memoryview)) else metric_geometry(raw, projected=projected)
    rows = [zone_facts(row, projected=projected, road_normalizer=normalize, geometry_reader=decode) for row in queue_metadata(db, active_only=active_only)]
    ordered = sorted(rows, key=lambda row: row["id"])
    groups = indexed_zone_groups(ordered) if active_only else [[row] for row in ordered]
    return sorted(groups, key=lambda group: (-max(utc(row["created_at"]).timestamp() for row in group), group[0]["id"]))


def indexed_zone_groups(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Prune impossible pairs, retaining the original greedy complete-link result."""
    from collections import defaultdict
    buckets = defaultdict(list)
    groups = []
    for row in sorted(rows, key=lambda item: item["id"]):
        if row["road_city"] and row["group_geometry"] is not None:
            buckets[row["road_city"]].append(row)
        else:
            groups.append([row])
    for members in buckets.values():
        tree = STRtree([row["group_geometry"] for row in members])
        assignments: dict[int, int] = {}
        local_groups: list[list[int]] = []
        first_bounds = None
        first_identical = members[0]["group_geometry"]
        for index, row in enumerate(members):
            bounds = row["group_geometry"].bounds
            combined = (min(first_bounds[0], bounds[0]), min(first_bounds[1], bounds[1]),
                        max(first_bounds[2], bounds[2]), max(first_bounds[3], bounds[3])) if first_bounds else bounds
            # A ≤50 m bounding-box diagonal proves every pair qualifies. This
            # avoids quadratic work for dense coincident short geometries.
            if local_groups and (row["group_geometry"] is first_identical or
                    (combined[2]-combined[0])**2 + (combined[3]-combined[1])**2 <= 2500):
                local_groups[0].append(index)
                assignments[index] = 0
                first_bounds = combined
                if row["group_geometry"] is not first_identical:
                    first_identical = None
                continue
            # The index narrows candidates only; the exact distance remains authoritative.
            candidates = {int(other) for other in tree.query(row["group_geometry"].envelope.buffer(50).envelope)
                          if int(other) < index}
            possible = sorted({assignments[other] for other in candidates})
            target = next((group for group in possible if all(other in candidates and
                related_zones(row, members[other]) for other in local_groups[group])), None)
            if target is None:
                target = len(local_groups)
                local_groups.append([])
            local_groups[target].append(index)
            assignments[index] = target
            if target == 0:
                first_bounds = combined
                if row["group_geometry"] is not first_identical:
                    first_identical = None
        groups.extend([[members[index] for index in group] for group in local_groups])
    return sorted(groups, key=lambda group: group[0]["id"])


def zone_details(db: Session, rows: list[dict[str, Any]], *, brief: bool = False) -> list[FloodAvoidanceZoneResponse]:
    by_id = {zone.id: zone for zone in queue_zone_details(db, [row["id"] for row in rows], brief=brief)}
    zones = [by_id[row["id"]] for row in rows if row["id"] in by_id]
    eligible_ids = active_zone_ids(db, [zone.id for zone in zones])
    bases = brief_zone_response_bases(db, zones, eligible_ids=eligible_ids) if brief else zone_response_bases(zones, eligible_ids=eligible_ids)
    return zone_responses_with_news(db, zones, base_responses=bases)


def paginate(total: int, page: int, page_size: int) -> tuple[int, int, slice]:
    pages = max(1, (total + page_size - 1) // page_size)
    actual = min(page, pages)
    return actual, pages, slice((actual - 1) * page_size, actual * page_size)


def browse_zone_queue(db: Session, *, active_only: bool = True, source: ZoneSource = "all", q: str = "",
        city: str = "", barangay: str = "", severity: str = "", page: int = 1, page_size: int = 20, brief: bool = False) -> ZoneQueuePage:
    groups = current_groups(db, active_only=active_only)
    rows = [row for group in groups for row in group]
    counts = {name: sum(row["source"] == name for row in rows) for name in SOURCES}
    counts["all"] = len(rows)
    source_rows = [row for row in rows if source == "all" or row["source"] == source]
    facets = SpatialReviewFacets(cities=names([location[1] for row in source_rows for location in row["locations"]]),
        barangays=names([location[2] for row in source_rows for location in row["locations"] if not city or locality(location[1]) == locality(city)]))

    def matches(row: dict[str, Any]) -> bool:
        if source != "all" and row["source"] != source:
            return False
        if severity and row["severity"] != severity:
            return False
        if (city or barangay) and not any((not city or locality(location[1]) == locality(city)) and
                (not barangay or normalized(location[2]) == normalized(barangay)) for location in row["locations"]):
            return False
        return all(term in row["searchable"] for term in normalized(q).split())

    groups = [group for group in groups if any(matches(row) for row in group)]
    actual, pages, selected = paginate(len(groups), page, page_size)
    items = [ZoneQueueItem(zone_id=group[0]["id"], member_count=len(group), location=summary([row["location"] for row in group]),
        area_summary=summary([row["area"] for row in group]), sources=names([row["source"] for row in group]),
        severity_levels=[level for level in SEVERITIES if any(row["severity"] == level for row in group)],
        depth_levels=names([row["depth"] for row in group]), evidence=group[0]["evidence"],
        queued_at=max(utc(row["created_at"]) for row in group), group_reason=GROUP_REASON, bounds=camera_bounds(group)) for group in groups[selected]]
    return ZoneQueuePage(items=items, zones=[] if active_only else zone_details(db, [group[0] for group in groups[selected]], brief=brief),
        total=len(groups), item_total=sum(len(group) for group in groups), counts=counts, facets=facets,
        page=actual, pages=pages, page_size=page_size)


def browse_zone_members(db: Session, zone_id: int, *, page: int | None = None, page_size: int = 20, brief: bool = False) -> ZoneMembersPage | None:
    groups = current_groups(db, active_only=True)
    group = next((group for group in groups if any(row["id"] == zone_id for row in group)), None)
    if group is None:
        return None
    if page is None:
        page = next(index for index, row in enumerate(group) if row["id"] == zone_id) // page_size + 1
    actual, pages, selected = paginate(len(group), page, page_size)
    return ZoneMembersPage(zone_total=sum(len(item) for item in groups), zone_id=group[0]["id"], zones=zone_details(db, group[selected], brief=brief), total=len(group),
        page=actual, pages=pages, page_size=page_size, group_reason=GROUP_REASON)
