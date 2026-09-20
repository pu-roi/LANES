import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session

from app import models, crud
from app.core.database import SessionLocal

logger = logging.getLogger("lanes.retention")


def purge_expired_archived_records(db: Session, retention_days: int = 30) -> Dict[str, Any]:
    """
    Permanently deletes records that have been soft-deleted or archived
    for longer than `retention_days` (default 30 days).
    """
    threshold = datetime.utcnow() - timedelta(days=retention_days)
    purged_counts = {
        "users": 0,
        "posts": 0,
        "reports": 0,
        "zones": 0,
        "total": 0,
    }

    try:
        # 1. Purge Archived Users
        expired_users = db.query(models.User).filter(
            models.User.deleted_at.is_not(None),
            models.User.deleted_at <= threshold
        ).all()
        for user in expired_users:
            if crud.hard_delete_user(db, user.id):
                purged_counts["users"] += 1

        # 2. Purge Archived Community Posts
        expired_posts = db.query(models.CommunityPost).filter(
            models.CommunityPost.deleted_at.is_not(None),
            models.CommunityPost.deleted_at <= threshold
        ).all()
        for post in expired_posts:
            if crud.hard_delete_post(db, post.id):
                purged_counts["posts"] += 1

        # 3. Purge Rejected Flood Reports
        expired_reports = db.query(models.FloodReport).filter(
            models.FloodReport.status == "rejected",
            models.FloodReport.updated_at <= threshold
        ).all()
        for report in expired_reports:
            if crud.hard_delete_flood_report(db, report.id):
                purged_counts["reports"] += 1

        # 4. Purge Deactivated Flood Avoidance Zones
        expired_zones = db.query(models.FloodAvoidanceZone).filter(
            models.FloodAvoidanceZone.is_active.is_(False),
            (
                (models.FloodAvoidanceZone.expires_at <= threshold) |
                (models.FloodAvoidanceZone.created_at <= threshold)
            )
        ).all()
        for zone in expired_zones:
            if crud.hard_delete_flood_avoidance_zone(db, zone.id):
                purged_counts["zones"] += 1

        purged_counts["total"] = (
            purged_counts["users"] +
            purged_counts["posts"] +
            purged_counts["reports"] +
            purged_counts["zones"]
        )

        if purged_counts["total"] > 0:
            logger.info(f"Auto-purge executed: Purged {purged_counts['total']} expired records ({purged_counts})")

    except Exception as e:
        logger.error(f"Error executing auto-purge of archived records: {e}", exc_info=True)
        db.rollback()

    return purged_counts


async def run_periodic_retention_purge(interval_seconds: int = 86400, retention_days: int = 30):
    """
    Background worker that runs daily to purge expired archived records.
    """
    logger.info(f"Retention background worker started. Running every {interval_seconds}s with {retention_days}-day window.")
    while True:
        try:
            db = SessionLocal()
            try:
                purge_expired_archived_records(db=db, retention_days=retention_days)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Retention worker encountered an error: {e}", exc_info=True)

        await asyncio.sleep(interval_seconds)
