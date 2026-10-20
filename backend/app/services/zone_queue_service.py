"""Read-only zone attention groups. Publication and routing stay independent."""
from typing import Any

from sqlalchemy.orm import Session

from app.crud.zone_queue import queue_metadata, queue_zone_details, active_zone_ids
from app.schemas.report import FloodAvoidanceZoneResponse
from app.schemas.spatial_review import SpatialReviewFacets
from app.schemas.zone_queue import ZoneSource, ZoneQueueItem, ZoneQueuePage, ZoneMembersPage
from app.services.merge_service import normalize_road_name
from app.services.news_zone_projection_service import zone_responses_with_news
from app.services.spatial_grouping import complete_link_groups, metric_geometry
from app.services.spatial_review_grouping import locality, utc

GROUP_REASON = "Nearby active zone boundaries: up to 500 m on a confirmed matching road and city; otherwise 50 m. Creation time does not limit grouping. Each zone retains its own evidence and actions."
SOURCES = ("user_reports", "news", "official", "other")
SEVERITIES = ("low", "medium", "high", "extreme")


def normalized(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def names(values: list[str | None]) -> list[str]:
    return sorted({normalized(value): value.strip() for value in values if value and value.strip()}.values(), key=str.casefold)


def summary(values: list[str | None]) -> str:
    items = names(values)
    return " · ".join(items[:3]) + (f" · +{len(items) - 3} more" if len(items) > 3 else "")


def zone_facts(row: dict[str, Any], *, projected: bool) -> dict[str, Any]:
    reports = row["reports"]
    news = row["news"]
    locations = [(report["human_readable_location"], report["city"], report["barangay"]) for report in reports]
    locations += [(item["claim"].get("canonical_road"), item["claim"].get("canonical_city"),
                   item["claim"].get("canonical_barangay")) for item in news]
    road_cities = {(normalize_road_name(road), locality(city)) for road, city, _ in locations
                   if normalize_road_name(road) and locality(city)}
    # Incomplete or contradictory evidence cannot establish the wider threshold.
    reliable = len(road_cities) == 1 and all(normalize_road_name(road) and locality(city) for road, city, _ in locations)
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
    return {**row, "metric": metric_geometry(row["geometry"], projected=projected), "locations": locations,
            "road_city": next(iter(road_cities)) if reliable else None, "severity": severity, "depth": depth,
            "source": source, "evidence": evidence, "searchable": normalized(" ".join(str(value or "") for value in searchable)),
            "location": row["name"] or summary([road for road, _, _ in locations]) or public.get("location_label") or f"Zone #{row['id']}",
            "area": summary([", ".join(filter(None, [barangay, city])) for _, city, barangay in locations])}


def related_zones(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if a["metric"] is None or b["metric"] is None:
        return False
    limit = 500.0 if a["road_city"] and a["road_city"] == b["road_city"] else 50.0
    return a["metric"].distance(b["metric"]) <= limit


def current_groups(db: Session, *, active_only: bool) -> list[list[dict[str, Any]]]:
    rows = [zone_facts(row, projected=db.get_bind().dialect.name == "postgresql") for row in queue_metadata(db, active_only=active_only)]
    ordered = sorted(rows, key=lambda row: row["id"])
    groups = complete_link_groups(ordered, related_zones) if active_only else [[row] for row in ordered]
    return sorted(groups, key=lambda group: (-max(utc(row["created_at"]).timestamp() for row in group), group[0]["id"]))


def zone_details(db: Session, rows: list[dict[str, Any]]) -> list[FloodAvoidanceZoneResponse]:
    by_id = {zone.id: zone for zone in queue_zone_details(db, [row["id"] for row in rows])}
    zones = [by_id[row["id"]] for row in rows if row["id"] in by_id]
    eligible_ids = active_zone_ids(db, [zone.id for zone in zones])
    bases = []
    for zone in zones:
        # Avoid ORM properties that perform one news lookup per zone without reports.
        values = {name: getattr(zone, name) for name in FloodAvoidanceZoneResponse.model_fields
                  if name not in {"report_source", "contributors", "news"} and hasattr(type(zone), name)}
        primary = zone.primary_report
        values.update(is_active=zone.id in eligible_ids,
            report_source=(str(getattr(primary.source, "value", primary.source)) if primary else None),
            contributors=zone.contributors if zone.reports else [], original_report_text=primary.raw_text if primary else None,
            location_label=primary.human_readable_location if primary else None,
            is_bidirectional=primary.is_bidirectional if primary else None,
            report_media_urls=list(dict.fromkeys(url for report in zone.reports for url in report.media_urls or [] if url)),
            media_urls=list(zone.media_urls or []), reporter_name=zone.reporter_name if primary else None)
        bases.append(FloodAvoidanceZoneResponse.model_validate(values))
    return zone_responses_with_news(db, zones, base_responses=bases)


def paginate(total: int, page: int, page_size: int) -> tuple[int, int, slice]:
    pages = max(1, (total + page_size - 1) // page_size)
    actual = min(page, pages)
    return actual, pages, slice((actual - 1) * page_size, actual * page_size)


def browse_zone_queue(db: Session, *, active_only: bool = True, source: ZoneSource = "all", q: str = "",
        city: str = "", barangay: str = "", severity: str = "", page: int = 1, page_size: int = 20) -> ZoneQueuePage:
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
        queued_at=max(utc(row["created_at"]) for row in group), group_reason=GROUP_REASON) for group in groups[selected]]
    return ZoneQueuePage(items=items, zones=[] if active_only else zone_details(db, [group[0] for group in groups[selected]]),
        total=len(groups), item_total=sum(len(group) for group in groups), counts=counts, facets=facets,
        page=actual, pages=pages, page_size=page_size)


def browse_zone_members(db: Session, zone_id: int, *, page: int | None = None, page_size: int = 20) -> ZoneMembersPage | None:
    group = next((group for group in current_groups(db, active_only=True) if any(row["id"] == zone_id for row in group)), None)
    if group is None:
        return None
    if page is None:
        page = next(index for index, row in enumerate(group) if row["id"] == zone_id) // page_size + 1
    actual, pages, selected = paginate(len(group), page, page_size)
    return ZoneMembersPage(zone_id=group[0]["id"], zones=zone_details(db, group[selected]), total=len(group),
        page=actual, pages=pages, page_size=page_size, group_reason=GROUP_REASON)
