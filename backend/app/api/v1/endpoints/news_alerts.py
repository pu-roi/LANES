"""Safe public news reads; no extraction, private audit or lifecycle writes."""
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.news_publication import PublicNewsAlert, PublicNewsAlertPage
from app.services.news_publication_read_service import browse_public_news_alerts, read_public_news_alert

router = APIRouter()


@router.get("/alerts", response_model=PublicNewsAlertPage)
def public_alerts(response: Response, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                  db: Session = Depends(get_db)) -> PublicNewsAlertPage:
    response.headers["Cache-Control"] = "no-store"
    try:
        return browse_public_news_alerts(db, page=page, page_size=page_size)
    except (SQLAlchemyError, ValueError) as exc:
        raise HTTPException(503, "News alerts are temporarily unavailable. Please retry.") from exc


@router.get("/alerts/{case_id}", response_model=PublicNewsAlert)
def public_alert_detail(response: Response, case_id: int = Path(gt=0),
                        db: Session = Depends(get_db)) -> PublicNewsAlert:
    response.headers["Cache-Control"] = "no-store"
    try:
        result = read_public_news_alert(db, case_id)
    except (SQLAlchemyError, ValueError) as exc:
        raise HTTPException(503, "This news alert could not be loaded. Please retry.") from exc
    if result is None:
        raise HTTPException(404, "This news alert is not publicly available.")
    return result
