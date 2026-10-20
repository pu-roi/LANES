"""Staff-only read endpoints for spatially grouped active zones."""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api import deps
from app.core.database import get_db
from app.schemas.zone_queue import ZoneSource, ZoneQueuePage, ZoneMembersPage
from app.services.zone_queue_service import browse_zone_queue, browse_zone_members

router = APIRouter()


@router.get("/queue", response_model=ZoneQueuePage)
def zone_queue(active_only: bool = True, source: ZoneSource = "all", q: str = Query("", max_length=120),
        city: str = Query("", max_length=100), barangay: str = Query("", max_length=100),
        severity: str = Query("", pattern=r"^(|low|medium|high|extreme|unknown)$"),
        page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db), _staff: object = Depends(deps.get_current_active_admin)) -> ZoneQueuePage:
    try:
        return browse_zone_queue(db, active_only=active_only, source=source, q=q, city=city,
            barangay=barangay, severity=severity, page=page, page_size=page_size)
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Zone queue could not be loaded.") from exc


@router.get("/groups/{zone_id}/members", response_model=ZoneMembersPage)
def zone_group_members(zone_id: int = Path(ge=1), page: int | None = Query(None, ge=1),
        page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db),
        _staff: object = Depends(deps.get_current_active_admin)) -> ZoneMembersPage:
    try:
        result = browse_zone_members(db, zone_id, page=page, page_size=page_size)
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Zone group could not be loaded.") from exc
    if result is None:
        raise HTTPException(404, "This group is no longer active. Return to the queue to see current zones.")
    return result
