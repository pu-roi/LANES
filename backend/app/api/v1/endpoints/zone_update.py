"""Public authenticated submissions; private Spatial Operations review reads."""
import logging
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, Response, UploadFile
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.zone_update import ZoneObservationCreate, ZoneObservationReview, ZoneObservationEditorRequest
from app.services import zone_update_service as service
from app.services.flood_followup_service import FollowupError


def private(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(dependencies=[Depends(private)])
logger = logging.getLogger(__name__)


def run(db: Session, action: Callable[[], Any]) -> Any:
    try:
        return action()
    except FollowupError as exc:
        db.rollback()
        raise HTTPException(exc.status_code, exc.detail, headers={"Cache-Control": "no-store"}) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Zone observation storage failed (%s)", type(exc).__name__)
        raise HTTPException(503, "Updates are temporarily unavailable. Please retry.") from exc


@router.post("/zones/{zone_id}/updates")
def submit(zone_id: int = Path(ge=1), body: str = Form(...), media: list[UploadFile] = File(default=[]),
           db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Any:
    try:
        payload = ZoneObservationCreate.model_validate_json(body)
    except ValidationError as exc:
        raise HTTPException(422, "; ".join(error["msg"] for error in exc.errors())) from exc
    return run(db, lambda: service.submit(db, zone_id, user, payload, media))


@router.get("/zones/{zone_id}/update-context")
def update_context(zone_id: int = Path(ge=1), db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)) -> Any:
    return run(db, lambda: service.update_context(db, zone_id, user))


@router.get("/admin/zone-updates/counts")
def counts(zone_ids: list[int] = Query(default=[], max_length=100), db: Session = Depends(get_db),
           user: User = Depends(get_current_user)) -> Any:
    return run(db, lambda: service.counts(db, zone_ids, user))


@router.get("/admin/zones/{zone_id}/updates")
def read(zone_id: int = Path(ge=1), limit: int = Query(default=50, ge=1, le=100),
         before_id: int | None = Query(default=None, ge=1), db: Session = Depends(get_db),
         user: User = Depends(get_current_user)) -> Any:
    return run(db, lambda: service.list_updates(db, zone_id, user, limit, before_id))


@router.post("/admin/zones/{zone_id}/updates/{update_id}/review")
def review(payload: ZoneObservationReview, zone_id: int = Path(ge=1), update_id: int = Path(ge=1),
           db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Any:
    return run(db, lambda: service.review(db, zone_id, update_id, user, payload))


@router.post("/admin/zones/{zone_id}/updates/{update_id}/editor")
def editor(payload: ZoneObservationEditorRequest, zone_id: int = Path(ge=1), update_id: int = Path(ge=1),
           db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Any:
    return run(db, lambda: service.editor_proposal(db, zone_id, update_id, user, payload))
