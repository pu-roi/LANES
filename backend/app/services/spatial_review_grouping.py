"""Read-only attention groups; individual evidence and moderation remain intact."""
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Mapping

from shapely.affinity import scale
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.errors import ShapelyError

from app.services.merge_service import normalize_road_name

MAX_GROUP_DISTANCE_M = 500.0
MAX_GROUP_TIME = timedelta(hours=2)
GROUP_REASON = "Nearby reports within 2 hours: up to 500 m on the same road, or 50 m between different roads. Barangay boundaries do not exclude review. Confirm the flood extent before merging."
Identity = tuple[str, int, int]


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def locality(value: str | None) -> str:
    return " ".join((value or "").casefold().removeprefix("city of ").removesuffix(" city").split())


@dataclass
class ReviewGroup:
    identities: list[Identity]
    queued_at: datetime
    reason: str | None = None

    @property
    def key(self) -> str:
        source, record_id, index = self.identities[0]
        return f"{source}:{record_id}:{index}" if source == "news_claim" else f"{source}:{record_id}"


def group_review_identities(identities: list[Mapping[str, Any]], reports: list[Mapping[str, Any]], *, projected: bool) -> list[ReviewGroup]:
    metadata = {row["id"]: row for row in reports}
    geometry: dict[int, BaseGeometry] = {}
    for row in reports:
        try:
            raw = row["geometry"]
            if raw is None:
                continue
            geom = shape(json.loads(raw) if isinstance(raw, str) else raw)
            if geom.is_empty or not geom.is_valid:
                continue
            # Production metadata is PostGIS UTM 51N in metres. The isolated
            # SQLite test adapter stores WGS84 GeoJSON, with a local projection.
            geometry[row["id"]] = geom if projected else scale(geom,
                xfact=111320 * math.cos(math.radians(14.58)), yfact=110574, origin=(0, 0))
        except (ValueError, TypeError, KeyError, ShapelyError):
            # Missing/invalid geometry cannot establish a related group.
            continue

    def related(first: int, second: int) -> bool:
        a, b = metadata.get(first), metadata.get(second)
        if a is None or b is None or first not in geometry or second not in geometry:
            return False
        road = normalize_road_name(a["human_readable_location"])
        other_road = normalize_road_name(b["human_readable_location"])
        if not road or not other_road:
            return False
        city = locality(a["city"])
        other_city = locality(b["city"])
        if not city or not other_city:
            return False
        if abs(utc(a["created_at"]) - utc(b["created_at"])) > MAX_GROUP_TIME:
            return False
        limit = MAX_GROUP_DISTANCE_M if road == other_road and city == other_city else 50.0
        return geometry[first].distance(geometry[second]) <= limit

    groups: list[ReviewGroup] = []
    # Stable oldest-ID anchors; complete-link checks prevent distant reports
    # joining through a chain of intermediary reports along a long avenue.
    for row in sorted(identities, key=lambda row: (row["source"], row["record_id"], row["claim_index"])):
        identity = (row["source"], row["record_id"], row["claim_index"])
        when = utc(row["queued_at"])
        report = metadata.get(row["record_id"]) if row["source"] == "user_report" else None
        target = next((group for group in groups if report and group.identities[0][0] == "user_report"
            if all(related(row["record_id"], other[1]) for other in group.identities)), None) if report else None
        if target:
            target.identities.append(identity)
            target.queued_at = max(target.queued_at, when)
            target.reason = GROUP_REASON
        else:
            group = ReviewGroup([identity], when)
            groups.append(group)
    return sorted(groups, key=lambda group: (-group.queued_at.timestamp(), group.key))
