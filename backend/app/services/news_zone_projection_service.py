"""Attach safe current news details to existing zone responses, without schema writes."""
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.news_processing import utc_now
from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimZoneLink
from app.schemas.report import FloodAvoidanceZoneResponse
from app.services.news_publication_service import public_projection


def zone_responses_with_news(db: Session, zones: list) -> list[FloodAvoidanceZoneResponse]:
    if not zones:
        return []
    by_zone = defaultdict(list)
    rows = db.execute(select(NewsClaimZoneLink.zone_id, NewsClaimDecision)
        .join(NewsClaimDecision, NewsClaimDecision.id == NewsClaimZoneLink.decision_id)
        .join(NewsClaimCase, NewsClaimCase.id == NewsClaimDecision.case_id)
        .where(NewsClaimZoneLink.zone_id.in_([zone.id for zone in zones]),
               NewsClaimDecision.revision == NewsClaimCase.revision,
               NewsClaimDecision.public_state == "active_zone"))
    now = utc_now()
    for zone_id, decision in rows:
        public = public_projection(decision, now)
        if public and public.status == "Active" and public.affects_routing:
            by_zone[zone_id].append(public)
    responses = []
    for zone in zones:
        response = FloodAvoidanceZoneResponse.model_validate(zone)
        news = sorted(by_zone[zone.id], key=lambda alert: (alert.observed_at, alert.case_id), reverse=True)
        updates = {"news": news}
        if news and not zone.report_id:
            updates.update(reporter_name=news[0].source_publisher, reporter_role="News report",
                reporter_trust_score=None, report_text=news[0].evidence_excerpt,
                report_source="news", contributors=[])
        responses.append(response.model_copy(update=updates))
    return responses
