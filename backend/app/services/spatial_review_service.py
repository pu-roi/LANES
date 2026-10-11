"""Read current exceptions while keeping original evidence and source actions distinct."""
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy.orm import Session

from app.crud.report import get_flood_report
from app.crud.spatial_review import is_current_review, list_review_identities, list_report_group_metadata, read_review_members
from app.schemas.report import FloodReportResponse
from app.schemas.spatial_review import ReviewSource, SpatialReviewDetail, SpatialReviewItem, SpatialReviewMember, SpatialReviewPage, SpatialReviewMembersPage, SpatialReviewFacets
from app.services.news_results_service import read_news_result
from app.services.spatial_review_grouping import ReviewGroup, group_review_identities, locality


def review_clock() -> datetime:
    return datetime.now(timezone.utc)


def _current_groups(db: Session, now: datetime) -> tuple[list[ReviewGroup], dict[str, int], list[Mapping[str, Any]]]:
    identities = list_review_identities(db, now)
    counts = {"user_reports": sum(row["source"] == "user_report" for row in identities),
        "news_claims": sum(row["source"] == "news_claim" for row in identities), "all": len(identities)}
    reports = list_report_group_metadata(db) if counts["user_reports"] else []
    return group_review_identities(identities, reports, projected=db.get_bind().dialect.name == "postgresql"), counts, identities


def _member(row: Mapping[str, Any]) -> SpatialReviewMember:
    news = row["source"] == "news_claim"
    key = f"news_claim:{row['record_id']}:{row['claim_index']}" if news else f"user_report:{row['record_id']}"
    return SpatialReviewMember(**{name: row[name] for name in (
        "source", "title", "location", "evidence", "review_reason", "queued_at", "severity", "depth", "city", "barangay")}, key=key,
        report_id=None if news else row["record_id"], run_id=row["record_id"] if news else None,
        claim_index=row["claim_index"] if news else None)


def _normalized(value: str | None) -> str:
    return " ".join((value or "").casefold().split())


def _names(values: list[str | None]) -> list[str]:
    unique = {_normalized(value): value.strip() for value in reversed(values) if value and value.strip()}
    return sorted(unique.values(), key=str.casefold)


def _summary(values: list[str | None]) -> str:
    names = _names(values)
    return " · ".join(names[:3]) + (f" · +{len(names) - 3} more" if len(names) > 3 else "")


def browse_spatial_review(db: Session, *, source: ReviewSource, page: int, page_size: int,
                         q: str = "", city: str = "", barangay: str = "", severity: str = "") -> SpatialReviewPage:
    now = review_clock()
    groups, counts, rows = _current_groups(db, now)
    facts = {(row["source"], row["record_id"], row["claim_index"]): row for row in rows}
    if source != "all":
        groups = [group for group in groups if group.identities[0][0] == ("user_report" if source == "user_reports" else "news_claim")]
    source_rows = [facts[identity] for group in groups for identity in group.identities]
    # Facets remain available on zero-result searches. Barangays are scoped to
    # the selected city, using the same evidence row rather than a group's union.
    cities = {locality(row["city"]): row["city"].strip() for row in reversed(source_rows) if row["city"] and locality(row["city"])}
    facets = SpatialReviewFacets(cities=sorted(cities.values(), key=str.casefold),
        barangays=_names([row["barangay"] for row in source_rows if not city or locality(row["city"]) == locality(city)]))

    def matches(row: Mapping[str, Any]) -> bool:
        if city and locality(row["city"]) != locality(city):
            return False
        if barangay and _normalized(row["barangay"]) != _normalized(barangay):
            return False
        if severity and _normalized(row["severity"] or "unknown") != severity:
            return False
        searchable = " ".join(str(row[name] or "") for name in (
            "title", "location", "city", "barangay", "evidence", "review_reason"))
        return all(term in _normalized(searchable) for term in _normalized(q).split())

    # Match any member, keep the entire group and its canonical key. Filtering
    # must not silently change related-report membership or moderation targets.
    groups = [group for group in groups if any(matches(facts[identity]) for identity in group.identities)]
    total = len(groups)
    pages = max(1, (total + page_size - 1) // page_size)
    actual_page = min(page, pages)
    selected = groups[(actual_page - 1) * page_size:actual_page * page_size]
    # At most three evidence previews per card; large groups have a separately
    # paginated read. Grouping never splits at an individual-row page boundary.
    items = []
    for group in selected:
        evidence = [facts[identity] for identity in group.identities]
        preview = [_member(row) for row in evidence[:3]]
        levels = {str(row["severity"]).lower() for row in evidence if row["severity"]}
        items.append(SpatialReviewItem(**{**preview[0].model_dump(), "queued_at": group.queued_at},
            member_count=len(group.identities), members=preview if len(group.identities) > 1 else [], group_reason=group.reason,
            location_summary=_summary([row["location"] for row in evidence]),
            area_summary=_summary([", ".join(filter(None, [row["barangay"], row["city"]])) for row in evidence]),
            severity_levels=[level for level in ("low", "medium", "high", "extreme") if level in levels],
            depth_levels=_names([row["depth"] for row in evidence])))
    return SpatialReviewPage(items=items, counts=counts, total=total, item_total=sum(len(group.identities) for group in groups), page=actual_page,
        page_size=page_size, pages=pages, facets=facets)


def browse_review_members(db: Session, key: str, *, page: int, page_size: int) -> SpatialReviewMembersPage | None:
    """Resolve current membership from any selected identity, including map picks."""
    now = review_clock()
    groups, _, _ = _current_groups(db, now)
    parts = key.split(":")
    identity = (parts[0], int(parts[1]), int(parts[2]) if parts[0] == "news_claim" else -1)
    group = next((group for group in groups if identity in group.identities), None)
    if group is None:
        return None
    total = len(group.identities)
    pages = max(1, (total + page_size - 1) // page_size)
    actual_page = min(page, pages)
    selected = group.identities[(actual_page - 1) * page_size:actual_page * page_size]
    rows = read_review_members(db, selected, now)
    members = {(row["source"], row["record_id"], row["claim_index"]): _member(row) for row in rows}
    return SpatialReviewMembersPage(key=group.key, items=[members[identity] for identity in selected if identity in members],
        total=total, page=actual_page, page_size=page_size, pages=pages, group_reason=group.reason)


def read_spatial_review(db: Session, key: str, *, can_write_news: bool = False) -> SpatialReviewDetail | None:
    parts = key.split(":")
    source, record_id = parts[0], int(parts[1])
    index = int(parts[2]) if source == "news_claim" else -1
    current = is_current_review(db, source, record_id, index, review_clock())
    if source == "news_claim":
        news = read_news_result(db, record_id, index)
        if news is None:
            return None
        case = None
        if db.get_bind().dialect.name == "postgresql":
            from app.crud.news_publication_read import source_for_claim
            from app.services.news_publication_read_service import read_news_claim_detail
            binding = source_for_claim(db, record_id, index)
            if binding is not None:
                case = read_news_claim_detail(db, binding.case_id, can_write=can_write_news)
        return SpatialReviewDetail(key=key, source=source, is_current_review=current, news=news,
            news_case=case, news_actions_available=bool(case and case.allowed_actions))
    report = get_flood_report(db, record_id)
    return SpatialReviewDetail(key=key, source=source, is_current_review=current,
        report=FloodReportResponse.model_validate(report)) if report else None
