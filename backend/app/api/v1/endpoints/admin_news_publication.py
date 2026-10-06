"""Authenticated, revision-guarded news exception decisions and history."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.news_publication_deps import may_write_news_claims, require_news_reader, require_news_writer
from app.core.database import get_db
from app.core.sse import manager
from app.crud.news_publication import NewsPublicationError
from app.models.user import User
from app.schemas.news_publication import NewsClaimDetail, NewsDecisionEffect, NewsDecisionSummary, NewsStaffDecisionRequest
from app.schemas.news_publication_reads import StaffNewsDecisionPage
from app.services.news_claim_auditor import NewsClaimAuditor
from app.services.news_evaluation_service import EvaluationPolicy, evaluation_policy
from app.services.news_publication_read_service import browse_news_claim_history, publication_read_clock, read_news_claim_detail

router = APIRouter()


def publication_policy() -> EvaluationPolicy:
    return evaluation_policy(NewsClaimAuditor())


@router.get("/claims/{case_id}", response_model=NewsClaimDetail)
def claim_detail(response: Response, case_id: int = Path(gt=0), db: Session = Depends(get_db),
                 staff: User = Depends(require_news_reader)) -> NewsClaimDetail:
    response.headers["Cache-Control"] = "no-store"
    try:
        result = read_news_claim_detail(db, case_id, can_write=may_write_news_claims(staff))
    except (SQLAlchemyError, ValueError) as exc:
        raise HTTPException(503, "News decision storage is unavailable.") from exc
    if result is None:
        raise HTTPException(404, "News claim was not found.")
    return result


@router.get("/claims/{case_id}/history", response_model=StaffNewsDecisionPage)
def claim_history(response: Response, case_id: int = Path(gt=0), page: int = Query(1, ge=1),
                  page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db),
                  _staff: User = Depends(require_news_reader)) -> StaffNewsDecisionPage:
    response.headers["Cache-Control"] = "no-store"
    try:
        result = browse_news_claim_history(db, case_id, page=page, page_size=page_size)
    except (SQLAlchemyError, ValueError) as exc:
        raise HTTPException(503, "News decision history is unavailable.") from exc
    if result is None:
        raise HTTPException(404, "News claim was not found.")
    return result


@router.post("/claims/{case_id}/decisions", response_model=NewsDecisionSummary)
def decide_claim(payload: NewsStaffDecisionRequest, background: BackgroundTasks, response: Response,
                 case_id: int = Path(gt=0), db: Session = Depends(get_db),
                 staff: User = Depends(require_news_writer),
                 policy: EvaluationPolicy = Depends(publication_policy)) -> NewsDecisionSummary:
    from app.services.news_publication_service import apply_staff_decision
    response.headers["Cache-Control"] = "no-store"
    try:
        decision = apply_staff_decision(db, case_id, payload, actor_user_id=staff.id,
                                        policy=policy, now=publication_read_clock())
        result = NewsDecisionSummary(**{key: getattr(decision, key) for key in NewsDecisionSummary.model_fields})
        db.commit()
    except NewsPublicationError as exc:
        db.rollback()
        raise HTTPException(exc.status_code, {"code": exc.code, "current_revision": exc.revision}) from exc
    except (SQLAlchemyError, ValueError) as exc:
        db.rollback()
        raise HTTPException(503, "The news decision could not be saved. Keep the same request ID when retrying.") from exc
    # Invalidation carries no private notes/body and occurs only after commit.
    background.add_task(manager.broadcast, {"type": "news_updated", "case_id": case_id})
    return result


@router.post("/claims/{case_id}/decision-preview", response_model=NewsDecisionEffect)
def preview_decision(payload: NewsStaffDecisionRequest, response: Response, case_id: int = Path(gt=0),
                     db: Session = Depends(get_db), staff: User = Depends(require_news_writer),
                     policy: EvaluationPolicy = Depends(publication_policy)) -> NewsDecisionEffect:
    from app.services.news_publication_service import preview_staff_decision
    response.headers["Cache-Control"] = "no-store"
    try:
        return preview_staff_decision(db, case_id, payload, actor_user_id=staff.id,
                                      policy=policy, now=publication_read_clock())
    except NewsPublicationError as exc:
        raise HTTPException(exc.status_code, {"code": exc.code, "current_revision": exc.revision}) from exc
    except (SQLAlchemyError, ValueError) as exc:
        raise HTTPException(503, "This decision could not be previewed. Nothing was saved.") from exc
