from typing import Optional

from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
import datetime

from app.core.database import get_db
from app.models.report import FloodReport, ReportStatus
from app.core.limiter import limiter
from app import models, schemas
from app.services.email_service import send_contact_email_async
from app.services.visitor_analytics_service import get_visitor_summary, record_visitor_activity
from app.api import deps

router = APIRouter()

@router.get("/stats")
def get_public_stats(db: Session = Depends(get_db)) -> schemas.PublicStatsResponse:
    """
    Retrieve public statistics for the landing page.
    Includes daily verified flood reports and deduplicated first-party visitors.
    """
    # 1. Daily Verified Reports
    today = datetime.datetime.utcnow().date()
    daily_verified_reports = db.query(FloodReport).filter(
        FloodReport.status == ReportStatus.APPROVED,
        func.date(FloodReport.created_at) == today
    ).count()
    
    visitor_summary = get_visitor_summary(db)
    return {
        "daily_verified_reports": daily_verified_reports,
        "total_visitors": visitor_summary["total_unique_visitors"],
    }


@router.post("/visits", response_model=schemas.VisitorActivityResponse)
@limiter.limit("30/minute")
def record_public_visit(
    request: Request,
    payload: schemas.VisitorActivityRequest,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_user_optional),
) -> schemas.VisitorActivityResponse:
    """Record a visible first-party visit without IP or fingerprint-based identity."""
    recorded = record_visitor_activity(
        db,
        visitor_id=payload.visitor_id,
        user_id=current_user.id if current_user else None,
        user_agent=request.headers.get("user-agent"),
    )
    visitor_summary = get_visitor_summary(db)
    today = datetime.datetime.utcnow().date()
    daily_verified_reports = db.query(FloodReport).filter(
        FloodReport.status == ReportStatus.APPROVED,
        func.date(FloodReport.created_at) == today,
    ).count()
    return schemas.VisitorActivityResponse(
        daily_verified_reports=daily_verified_reports,
        total_visitors=visitor_summary["total_unique_visitors"],
        recorded=recorded,
    )


@router.post("/contact", response_model=schemas.ContactMessageResponse)
@limiter.limit("5/minute")
async def send_contact_message(
    request: Request,
    payload: schemas.ContactMessageCreate
):
    """
    Send a direct message/inquiry to lanes@navlanes.live and navlanes.live@gmail.com using Resend.
    """
    success, err_msg = await send_contact_email_async(
        name=payload.name,
        sender_email=payload.email,
        subject=payload.subject,
        message=payload.message
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deliver message: {err_msg}"
        )
    return {
        "success": True,
        "message": "Your message has been sent successfully. We will get back to you soon!"
    }

