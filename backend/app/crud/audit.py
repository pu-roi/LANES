from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.schemas.audit import AuditLogCreate
from app.crud.flood_followup import OBSERVATION_ACTION, REVIEW_ACTION
from app.crud.zone_update import OBSERVATION_ACTION as ZONE_OBSERVATION, REVIEW_ACTION as ZONE_REVIEW


def create_audit_log(db: Session, audit_in: AuditLogCreate, commit: bool = True) -> AuditLog:
    """
    Creates a new audit log record.
    """
    db_audit = AuditLog(
        admin_id=audit_in.admin_id,
        action_type=audit_in.action_type,
        target_table=audit_in.target_table,
        target_id=audit_in.target_id,
        metadata_json=audit_in.metadata_json,
        ip_address=audit_in.ip_address,
    )
    db.add(db_audit)
    if commit:
        db.commit()
        db.refresh(db_audit)
    else:
        db.flush()
    return db_audit


def get_audit_logs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    action_type: Optional[str] = None,
    admin_id: Optional[int] = None,
) -> Tuple[List[AuditLog], int]:
    """
    Retrieves a paginated list of audit logs and the total matching count.
    """
    # Private observation/review evidence is readable only through the
    # ownership/capability-checked follow-up endpoints, never this general feed.
    query = select(AuditLog).where(or_(AuditLog.action_type.is_(None),
        AuditLog.action_type.not_in((OBSERVATION_ACTION, REVIEW_ACTION, ZONE_OBSERVATION, ZONE_REVIEW))))
    
    if action_type:
        query = query.where(AuditLog.action_type == action_type)
    if admin_id is not None:
        query = query.where(AuditLog.admin_id == admin_id)
        
    # Get total matching count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0
    
    # Get paginated logs ordered by most recent first
    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    logs = db.scalars(query).all()
    
    return list(logs), total
