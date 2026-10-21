"""Attach safe current news details to existing zone responses, without schema writes."""
from collections import defaultdict

from sqlalchemy import select, func, case
from sqlalchemy.orm import Session

from app.crud.news_processing import utc_now
from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimZoneLink
from app.schemas.report import FloodAvoidanceZoneResponse
from app.services.news_publication_service import public_projection
from app.services.configuration_service import read_configuration


def zone_response_bases(zones: list, *, eligible_ids: set[int] | None = None,
        schema: type[FloodAvoidanceZoneResponse] = FloodAvoidanceZoneResponse) -> list[FloodAvoidanceZoneResponse]:
    """Serialize eager-loaded evidence without database-backed news properties."""
    responses = []
    for zone in zones:
        values = {name: getattr(zone, name) for name in FloodAvoidanceZoneResponse.model_fields
                  if name not in {"report_source", "contributors", "news"} and hasattr(type(zone), name)}
        primary = zone.primary_report
        values.update(report_source=str(getattr(primary.source, "value", primary.source)) if primary else None,
            contributors=zone.contributors if zone.reports else [], original_report_text=primary.raw_text if primary else None,
            location_label=primary.human_readable_location if primary else None,
            is_bidirectional=primary.is_bidirectional if primary else None,
            report_media_urls=list(dict.fromkeys(url for report in zone.reports for url in report.media_urls or [] if url)),
            media_urls=list(zone.media_urls or []), reporter_name=zone.reporter_name if primary else None)
        if eligible_ids is not None:
            values["is_active"] = zone.id in eligible_ids
        responses.append(schema.model_validate(values))
    return responses


def brief_zone_response_bases(db: Session, zones: list, *, eligible_ids: set[int] | None = None,
        schema: type[FloodAvoidanceZoneResponse] = FloodAvoidanceZoneResponse) -> list[FloodAvoidanceZoneResponse]:
    """Keep complete counts/severity when only the first evidence page is loaded."""
    from app.models.report import FloodReport
    bases = zone_response_bases(zones, eligible_ids=eligible_ids, schema=schema)
    if not zones:
        return bases
    levels = ("low", "medium", "high", "extreme")
    counts = {item[0]: item[1:] for item in db.query(FloodReport.zone_id, func.count(FloodReport.id),
        func.max(case(*[(FloodReport.severity == name, index) for index, name in enumerate(levels)], else_=1)))
        .filter(FloodReport.zone_id.in_([zone.id for zone in zones])).group_by(FloodReport.zone_id)}
    for index, zone in enumerate(zones):
        count, level = counts.get(zone.id, (0, 1))
        bases[index] = bases[index].model_copy(update={"contributor_count": count,
            "severity": str(getattr(zone.severity_override, "value", zone.severity_override)) if zone.severity_override else levels[level]})
    return bases


def zone_responses_with_news(db: Session, zones: list, *,
        base_responses: list[FloodAvoidanceZoneResponse] | None = None) -> list[FloodAvoidanceZoneResponse]:
    if not zones:
        return []
    if base_responses is None:
        base_responses = zone_response_bases(zones)
    by_zone = defaultdict(list)
    from app.crud.news_publication_read import operational_deadline_expression
    rows = db.execute(select(NewsClaimZoneLink.zone_id, NewsClaimDecision, operational_deadline_expression())
        .select_from(NewsClaimZoneLink)
        .join(NewsClaimDecision, NewsClaimDecision.id == NewsClaimZoneLink.decision_id)
        .join(NewsClaimCase, NewsClaimCase.id == NewsClaimDecision.case_id)
        .where(NewsClaimZoneLink.zone_id.in_([zone.id for zone in zones]),
               NewsClaimDecision.revision == NewsClaimCase.revision,
               NewsClaimDecision.public_state == "active_zone"))
    now = utc_now()
    automatic_expiry_enabled = read_configuration(db).automatic_expiry_enabled
    for zone_id, decision, deadline in rows:
        public = public_projection(decision, now, automatic_expiry_enabled=automatic_expiry_enabled,
            expiry_override=deadline)
        if public and public.status == "Active" and public.affects_routing:
            by_zone[zone_id].append(public)
    responses = []
    for index, zone in enumerate(zones):
        response = base_responses[index]
        news = sorted(by_zone[zone.id], key=lambda alert: (alert.observed_at, alert.case_id), reverse=True)
        updates = {"news": news}
        if news and not zone.report_id:
            updates.update(reporter_name=news[0].source_publisher, reporter_role="News report",
                reporter_trust_score=None, report_text=news[0].evidence_excerpt,
                report_source="news", contributors=[])
        responses.append(response.model_copy(update=updates))
    return responses
