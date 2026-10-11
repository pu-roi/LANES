"""Authenticated owner submissions and capability-checked staff evidence review."""
import logging
from collections.abc import Callable
from typing import Literal, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.flood_followup import (
    FloodFollowupCreate, FloodFollowupResponse, FloodFollowupReviewCreate, FloodFollowupsExportResponse,
    OwnerFloodFollowupsResponse, StaffFloodFollowupsResponse,
)
from app.services import flood_followup_service as service

def _private_response(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(dependencies=[Depends(_private_response)])
logger = logging.getLogger(__name__)
Result = TypeVar("Result")


def _run(db: Session, operation: Callable[[], Result]) -> Result:
    try:
        return operation()
    except service.FollowupError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.detail,
            headers={"Cache-Control": "no-store"}) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        # Do not log exception SQL/parameters containing private citizen evidence.
        logger.error("Flood follow-up persistence failed (%s).", type(exc).__name__)
        raise HTTPException(status_code=503,
            detail="Follow-up storage is temporarily unavailable. Please try again.",
            headers={"Cache-Control": "no-store"}) from exc


@router.get("/reports/{report_id}/follow-ups", response_model=OwnerFloodFollowupsResponse)
def get_owner_followups(report_id: int = Path(ge=1), db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)) -> OwnerFloodFollowupsResponse:
    with db.no_autoflush:
        return _run(db, lambda: service.list_owner_followups(db, report_id, user))


@router.post("/reports/{report_id}/follow-ups", response_model=FloodFollowupResponse)
def create_followup(payload: FloodFollowupCreate, report_id: int = Path(ge=1),
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> FloodFollowupResponse:
    return _run(db, lambda: service.submit_followup(db, report_id, user, payload))


@router.get("/admin/flood-follow-ups", response_model=StaffFloodFollowupsResponse)
def get_staff_followups(review_state: Literal["pending", "accepted", "rejected", "all"] = "pending",
                        limit: int = Query(default=50, ge=1, le=100),
                        before_id: int | None = Query(default=None, ge=1),
                        db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> StaffFloodFollowupsResponse:
    with db.no_autoflush:
        return _run(db, lambda: service.list_staff_followups(db, user,
            review_state=review_state, limit=limit, before_id=before_id))


@router.post("/admin/flood-follow-ups/{followup_id}/review", response_model=FloodFollowupResponse)
def create_followup_review(payload: FloodFollowupReviewCreate, followup_id: int = Path(ge=1),
                           db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> FloodFollowupResponse:
    return _run(db, lambda: service.review_followup(db, followup_id, user, payload))


@router.get("/admin/flood-follow-ups/export", response_model=FloodFollowupsExportResponse)
def export_followups(review_state: Literal["pending", "accepted", "rejected", "all"] = "all",
                     limit: int = Query(default=100, ge=1, le=100),
                     before_id: int | None = Query(default=None, ge=1),
                     db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> FloodFollowupsExportResponse:
    with db.no_autoflush:
        return _run(db, lambda: service.export_staff_followups(db, user,
            review_state=review_state, limit=limit, before_id=before_id))
