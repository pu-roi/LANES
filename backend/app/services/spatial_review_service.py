"""Read current exceptions while keeping original evidence and source actions distinct."""
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy.orm import Session

from app.crud.report import get_flood_report
from app.crud.spatial_review import is_current_review, list_review_identities, list_report_group_metadata, read_review_members
from app.schemas.report import FloodReportResponse
from app.schemas.spatial_review import ReviewSource, SpatialReviewDetail, SpatialReviewItem, SpatialReviewMember, SpatialReviewPage, SpatialReviewMembersPage
from app.services.news_results_service import read_news_result
from app.services.spatial_review_grouping import ReviewGroup, group_review_identities


def review_clock() -> datetime:
    return datetime.now(timezone.utc)


def _current_groups(db: Session, now: datetime) -> tuple[list[ReviewGroup], dict[str, int]]:
    identities = list_review_identities(db, now)
    counts = {"user_reports": sum(row["source"] == "user_report" for row in identities),
        "news_claims": sum(row["source"] == "news_claim" for row in identities), "all": len(identities)}
    reports = list_report_group_metadata(db) if counts["user_reports"] else []
    return group_review_identities(identities, reports, projected=db.get_bind().dialect.name == "postgresql"), counts


def _member(row: Mapping[str, Any]) -> SpatialReviewMember:
    news = row["source"] == "news_claim"
    key = f"news_claim:{row['record_id']}:{row['claim_index']}" if news else f"user_report:{row['record_id']}"
    return SpatialReviewMember(**{name: row[name] for name in (
        "source", "title", "location", "evidence", "review_reason", "queued_at", "severity", "depth")}, key=key,
        report_id=None if news else row["record_id"], run_id=row["record_id"] if news else None,
        claim_index=row["claim_index"] if news else None)


def browse_spatial_review(db: Session, *, source: ReviewSource, page: int, page_size: int) -> SpatialReviewPage:
    now = review_clock()
    groups, counts = _current_groups(db, now)
    if source != "all":
        groups = [group for group in groups if group.identities[0][0] == ("user_report" if source == "user_reports" else "news_claim")]
    total = len(groups)
    pages = max(1, (total + page_size - 1) // page_size)
    actual_page = min(page, pages)
    selected = groups[(actual_page - 1) * page_size:actual_page * page_size]
    # At most three evidence previews per card; large groups have a separately
    # paginated read. Grouping never splits at an individual-row page boundary.
    rows = read_review_members(db, [identity for group in selected for identity in group.identities[:3]], now)
    members = {(row["source"], row["record_id"], row["claim_index"]): _member(row) for row in rows}
    items = []
    for group in selected:
        preview = [members[identity] for identity in group.identities[:3] if identity in members]
        if not preview:
            continue
        items.append(SpatialReviewItem(**{**preview[0].model_dump(), "queued_at": group.queued_at},
            member_count=len(group.identities), members=preview if len(group.identities) > 1 else [], group_reason=group.reason))
    return SpatialReviewPage(items=items, counts=counts, total=total, item_total=counts[source], page=actual_page,
        page_size=page_size, pages=pages)


def browse_review_members(db: Session, key: str, *, page: int, page_size: int) -> SpatialReviewMembersPage | None:
    """Resolve current membership from any selected identity, including map picks."""
    now = review_clock()
    groups, _ = _current_groups(db, now)
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


def read_spatial_review(db: Session, key: str) -> SpatialReviewDetail | None:
    parts = key.split(":")
    source, record_id = parts[0], int(parts[1])
    index = int(parts[2]) if source == "news_claim" else -1
    current = is_current_review(db, source, record_id, index, review_clock())
    if source == "news_claim":
        news = read_news_result(db, record_id, index)
        return SpatialReviewDetail(key=key, source=source, is_current_review=current, news=news) if news else None
    report = get_flood_report(db, record_id)
    return SpatialReviewDetail(key=key, source=source, is_current_review=current,
        report=FloodReportResponse.model_validate(report)) if report else None
