"""Authenticated research-only duration reads. No publication or zone writes."""
from fastapi import APIRouter, Depends, HTTPException, Response

from app.api.news_publication_deps import require_news_reader
from app.models.user import User
from app.schemas.flood_subsidence import DurationModelStatus, DurationPreviewRequest, DurationPreviewResponse
from app.services.flood_duration_model import DurationModelError
from app.services.flood_subsidence_prediction_service import load_research_model, model_status, preview_subsidence

router = APIRouter()


@router.get("/duration-model", response_model=DurationModelStatus)
def duration_model(response: Response, _staff: User = Depends(require_news_reader)) -> DurationModelStatus:
    response.headers["Cache-Control"] = "no-store"
    try:
        return model_status(*load_research_model())
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise HTTPException(503, "The duration research artifact is unavailable or invalid.") from exc


@router.post("/duration-preview", response_model=DurationPreviewResponse)
def duration_preview(payload: DurationPreviewRequest, response: Response,
                     _staff: User = Depends(require_news_reader)) -> DurationPreviewResponse:
    response.headers["Cache-Control"] = "no-store"
    try:
        return preview_subsidence(payload)
    except (OSError, DurationModelError, ValueError, TypeError, KeyError, OverflowError) as exc:
        raise HTTPException(503, "The duration research estimate could not be calculated.") from exc
