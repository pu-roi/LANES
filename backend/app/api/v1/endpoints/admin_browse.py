"""Authenticated, bounded staff reads, independent of legacy response contracts."""
import logging
from datetime import datetime
from typing import Any, Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api import deps
from app.core.database import get_db
from app.crud.report import avoidance_zones_query
from app.schemas.spatial_browse import HistoryRecordsPage, HistoryInspection, MapPage, ZoneCount, InspectionPage
from app.services.spatial_browse_service import history_cards, map_read, history_overview, history_collection, zone_contributors

router = APIRouter(dependencies=[Depends(deps.get_current_active_admin)])
logger = logging.getLogger(__name__)


def filters(status_filter: str = "all", severity: str | None = None, date_from: datetime | None = None,
        date_to: datetime | None = None, barangay: str | None = None, road: str | None = None,
        search: str | None = None, multiple_places: bool = False) -> dict[str, Any]:
    return dict(status_filter=status_filter, severity=severity, date_from=date_from, date_to=date_to,
        barangay=barangay, road=road, search=search, multiple_places=multiple_places)


def read(call: Any) -> Any:
    try:
        return call()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except SQLAlchemyError as exc:
        logger.exception("Staff browsing read failed")
        raise HTTPException(503, "Flood data is temporarily unavailable. Please try again.") from exc


@router.get("/zones/count", response_model=ZoneCount)
def zone_count(db: Session = Depends(get_db)) -> ZoneCount:
    return read(lambda: ZoneCount(total=avoidance_zones_query(db, active_only=True).count()))


@router.get("/zones/map", response_model=MapPage)
def zones_map(bbox: str | None = None, cursor: int = Query(0, ge=0), summary_only: bool = False,
        db: Session = Depends(get_db)) -> MapPage:
    return read(lambda: map_read(db, filters=None, bbox=bbox, zoom=15, cursor=cursor, summary_only=summary_only))


@router.get("/flood-events/records", response_model=HistoryRecordsPage)
def records(page: int = Query(1, ge=1), focus_event_id: int | None = Query(None, ge=1),
        selected: dict[str, Any] = Depends(filters), db: Session = Depends(get_db)) -> HistoryRecordsPage:
    return read(lambda: history_cards(db, selected, page=page, focus_event_id=focus_event_id))


@router.get("/flood-events/map", response_model=MapPage)
def historical_map(bbox: str | None = None, zoom: float = Query(12, ge=0, le=24),
        cursor: int = Query(0, ge=0), summary_only: bool = False,
        event_id: int | None = Query(None, ge=1),
        selected: dict[str, Any] = Depends(filters), db: Session = Depends(get_db)) -> MapPage:
    return read(lambda: map_read(db, filters={**selected, "event_id": event_id}, bbox=bbox, zoom=zoom, cursor=cursor, summary_only=summary_only))


@router.get("/flood-events/{event_id}/inspection", response_model=HistoryInspection)
def overview(event_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    return read(lambda: history_overview(db, event_id))


@router.get("/flood-events/{event_id}/inspection/{collection}", response_model=InspectionPage)
def collection_page(event_id: int, collection: Literal["zones", "reports", "timeline", "locations"], page: int = Query(1, ge=1),
        db: Session = Depends(get_db)) -> InspectionPage:
    return read(lambda: history_collection(db, event_id, collection, page))


@router.get("/zones/{zone_id}/contributors", response_model=InspectionPage)
def contributors(zone_id: int, page: int = Query(1, ge=1), focus_report_id: int | None = Query(None, ge=1),
        db: Session = Depends(get_db)) -> InspectionPage:
    return read(lambda: zone_contributors(db, zone_id, page, focus_report_id))
