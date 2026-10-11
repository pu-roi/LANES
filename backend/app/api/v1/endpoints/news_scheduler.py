"""Machine-only tick. Staff/browser status reads never dispatch workers."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, sessionmaker
from app.core.database import get_db
from app.core.news_scheduler_auth import require_news_scheduler
from app.services.news_weather_controller_service import run_weather_tick

router = APIRouter()


@router.post("/tick")
def news_weather_tick(db: Session = Depends(get_db), _identity: dict = Depends(require_news_scheduler)) -> dict:
    try:
        result = run_weather_tick(sessionmaker(bind=db.get_bind(), expire_on_commit=False))
    except Exception as exc:
        raise HTTPException(503, "News scheduling check is unavailable") from exc
    if result.get("outcome") == "requires_attention":
        raise HTTPException(503, "News worker dispatch requires attention; see automation status")
    return result
