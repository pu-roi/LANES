"""Public, read-only article list for Community Feed Local Updates."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.local_news import LocalNewsUpdates
from app.services.local_news_service import browse_local_news

router = APIRouter()


@router.get("/local-updates", response_model=LocalNewsUpdates)
def local_updates(response: Response, limit: int = Query(5, ge=1, le=10),
                  db: Session = Depends(get_db)) -> LocalNewsUpdates:
    response.headers["Cache-Control"] = "no-store"
    try:
        return browse_local_news(db, limit=limit)
    except (SQLAlchemyError, ValueError) as exc:
        raise HTTPException(503, "Local news is temporarily unavailable. Please retry.") from exc
