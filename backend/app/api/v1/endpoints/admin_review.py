"""Staff-only combined inspection; no news lifecycle or publication writes."""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api import deps
from app.core.database import get_db
from app.schemas.spatial_review import ReviewSource, SpatialReviewDetail, SpatialReviewPage, SpatialReviewMembersPage
from app.services.spatial_review_service import browse_spatial_review, read_spatial_review, browse_review_members

router = APIRouter()


@router.get("/groups/{key}/members", response_model=SpatialReviewMembersPage)
def review_members(key: str = Path(pattern=r"^(user_report:[1-9][0-9]*|news_claim:[1-9][0-9]*:[0-9]+)$", max_length=100),
                   page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                   db: Session = Depends(get_db), _staff: object = Depends(deps.get_current_active_admin)) -> SpatialReviewMembersPage:
    try:
        result = browse_review_members(db, key, page=page, page_size=page_size)
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Related reports could not be loaded.") from exc
    if result is None:
        raise HTTPException(404, "This review group is no longer available. Refresh the queue.")
    return result


@router.get("/items", response_model=SpatialReviewPage)
def review_items(source: ReviewSource = "all", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                 db: Session = Depends(get_db), _staff: object = Depends(deps.get_current_active_admin)) -> SpatialReviewPage:
    try:
        return browse_spatial_review(db, source=source, page=page, page_size=page_size)
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Review queue storage is unavailable.") from exc


@router.get("/items/{key}", response_model=SpatialReviewDetail)
def review_detail(key: str = Path(pattern=r"^(user_report:[1-9][0-9]*|news_claim:[1-9][0-9]*:[0-9]+)$", max_length=100),
                  db: Session = Depends(get_db), _staff: object = Depends(deps.get_current_active_admin)) -> SpatialReviewDetail:
    try:
        detail = read_spatial_review(db, key)
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Review evidence storage is unavailable.") from exc
    if detail is None:
        raise HTTPException(404, "Review evidence was not found.")
    return detail
