"""Private capability-checked case suggestions and a bounded review queue."""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from shapely.errors import ShapelyError

from app.api.deps import get_current_user
from app.api.v1.endpoints.flood_followup import _private_response, _run
from app.core.database import get_db
from app.models.user import User
from app.schemas.flood_review_suggestion import CaseReviewSuggestion, ReviewSuggestionCreate, ReviewSuggestionQueue
from app.services import flood_review_suggestion_service as service
from app.schemas.zone_prediction import ZonePrediction
from app.services import zone_prediction_service
from app.schemas.cross_location_prediction import CrossLocationPrediction
from app.services import cross_location_prediction_service
from app.schemas.zone_expiry import ZoneExpiryPolicy

router = APIRouter(dependencies=[Depends(_private_response)])


@router.get("/admin/zones/{zone_id}/expiry-policy", response_model=ZoneExpiryPolicy)
def zone_expiry_policy(zone_id: int = Path(ge=1), db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)) -> ZoneExpiryPolicy:
    from app.services.pasig_ml_expiry_service import expiry_status
    def read() -> ZoneExpiryPolicy:
        zone_prediction_service.require_staff_permission(user, write=False)
        zone_prediction_service.require_zone_reader(user, write=False)
        return ZoneExpiryPolicy(**expiry_status(db, zone_id))
    return _run(db, read)


@router.get("/admin/zones/{zone_id}/cross-location-prediction", response_model=CrossLocationPrediction)
def cross_location_prediction(zone_id: int = Path(ge=1), db: Session = Depends(get_db),
                              user: User = Depends(get_current_user)) -> CrossLocationPrediction:
    try:
        return _run(db, lambda: cross_location_prediction_service.compare_zone(db, zone_id, user))
    except (OSError, ValueError, TypeError, KeyError, OverflowError, ShapelyError) as exc:
        db.rollback()
        raise HTTPException(503, "The cross-location comparison could not be calculated. Please retry.",
                            headers={"Cache-Control": "no-store"}) from exc


@router.get("/admin/zones/{zone_id}/prediction-features")
def zone_features(zone_id: int = Path(ge=1), db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)) -> dict:
    try:
        return _run(db,lambda:zone_prediction_service.feature_context(db,zone_id,user))
    except (OSError,ValueError,TypeError,KeyError,ShapelyError) as exc:
        raise HTTPException(503,"Model input context is unavailable. Please retry.",headers={"Cache-Control":"no-store"}) from exc


@router.get("/admin/zones/{zone_id}/subsidence-prediction", response_model=ZonePrediction)
def zone_prediction(zone_id: int = Path(ge=1), db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)) -> ZonePrediction:
    try:
        return _run(db, lambda: zone_prediction_service.predict_zone(db, zone_id, user))
    except (OSError, ValueError, TypeError, KeyError, OverflowError, ShapelyError) as exc:
        db.rollback()
        raise HTTPException(503, "The zone prediction could not be calculated. Please retry.",
            headers={"Cache-Control": "no-store"}) from exc


@router.get("/admin/flood-review-suggestions", response_model=ReviewSuggestionQueue)
def queue(limit: int = Query(default=25, ge=1, le=50), before_id: int | None = Query(default=None, ge=1),
          actionable_only: bool = True, db: Session = Depends(get_db),
          user: User = Depends(get_current_user)) -> ReviewSuggestionQueue:
    return _run(db, lambda: service.review_queue(db, user, limit=limit, before_id=before_id,
        actionable_only=actionable_only))


@router.get("/admin/reports/{report_id}/review-suggestion", response_model=CaseReviewSuggestion)
def get_suggestion(report_id: int = Path(ge=1), db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)) -> CaseReviewSuggestion:
    return _run(db, lambda: service.get_case(db, report_id, user))


@router.post("/admin/reports/{report_id}/review-suggestion", response_model=CaseReviewSuggestion)
def create_suggestion(payload: ReviewSuggestionCreate, report_id: int = Path(ge=1),
                      db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CaseReviewSuggestion:
    try:
        return _run(db, lambda: service.issue_suggestion(db, report_id, user, payload))
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        db.rollback()
        raise HTTPException(503, "The experimental model could not calculate a suggestion. Please try again.",
            headers={"Cache-Control": "no-store"}) from exc
