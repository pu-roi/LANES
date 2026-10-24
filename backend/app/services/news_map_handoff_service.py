"""Resolve saved news identity to an active zone; never recompute placement."""
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.report import FloodAvoidanceZone
from app.schemas.news_results import NewsMapTarget
from app.services.news_browsing_service import publisher_labels
from app.services.news_history_evidence import evidence_refs
from app.services.news_results_service import read_news_result
from app.services.news_ner_durable.readers import read_native_group


def linked_active_zone_ids(db: Session, run_id: int, claim_index: int | None,
                           group_id: str | None) -> list[int]:
    from app.crud.report import get_active_avoidance_zone_query
    refs = evidence_refs()
    identities = []
    if claim_index is not None:
        identities.append(refs.c.claim_index == claim_index)
    if group_id is not None:
        identities.append(refs.c.group_id == group_id)
    if not identities:
        return []
    # Legacy publication links own a particular zone. Native imports retain
    # their exact run/group lineage on the event, including reviewed placements.
    query = get_active_avoidance_zone_query(db).join(refs, or_(
        FloodAvoidanceZone.id == refs.c.zone_id,
        and_(refs.c.zone_id.is_(None), FloodAvoidanceZone.event_id == refs.c.event_id)))
    return [row[0] for row in query.with_entities(FloodAvoidanceZone.id).filter(
        refs.c.run_id == run_id, or_(*identities)).distinct().order_by(FloodAvoidanceZone.id)]


def resolve_map_target(db: Session, run_id: int, claim_index: int | None,
                       group_id: str | None) -> NewsMapTarget | None:
    detail = (read_native_group(db, run_id, group_id, publisher_labels()) if group_id is not None
              else read_news_result(db, run_id, claim_index))
    if detail is None:
        return None
    item = detail.item
    ids = linked_active_zone_ids(db, run_id, item.claim_index, getattr(item, "group_id", None))
    return NewsMapTarget(zone_id=ids[0] if ids else None, claim_index=item.claim_index)
