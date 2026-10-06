"""Locked append-only news decisions. Helpers flush; the caller commits."""
from __future__ import annotations

from uuid import UUID
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.news_publication import NewsClaimCase, NewsClaimDecision
from app.schemas.news_publication import NewsDecisionSnapshot


class NewsPublicationError(ValueError):
    def __init__(self, code: str, status_code: int = 422, *, revision: int | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.status_code = status_code
        self.revision = revision


def publication_lock(db: Session, key: str) -> None:
    if db.get_bind().dialect.name != "postgresql":
        raise NewsPublicationError("publication_requires_postgresql", 503)
    # Deterministic server hashes serialize case identity and UUID requests,
    # including when the target doesn't exist yet. No raw publisher SQL.
    lock = int(key[:16], 16)
    if lock >= 2 ** 63:
        lock -= 2 ** 64
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock})


def lock_case(db: Session, case_id: int) -> NewsClaimCase:
    case = db.scalar(select(NewsClaimCase).where(NewsClaimCase.id == case_id).with_for_update())
    if case is None:
        raise NewsPublicationError("claim_not_found", 404)
    return case


def latest_decision(db: Session, case_id: int) -> NewsClaimDecision | None:
    return db.scalar(select(NewsClaimDecision).where(NewsClaimDecision.case_id == case_id)
                     .order_by(NewsClaimDecision.revision.desc()).limit(1))


def existing_request(db: Session, request_id: UUID, request_sha256: str) -> NewsClaimDecision | None:
    decision = db.scalar(select(NewsClaimDecision).where(NewsClaimDecision.request_id == request_id))
    if decision is not None:
        snapshot = NewsDecisionSnapshot.model_validate(decision.snapshot)
        if snapshot.request_sha256 != request_sha256:
            raise NewsPublicationError("request_identity_conflict", 409, revision=decision.revision)
    return decision


def append_decision(db: Session, case: NewsClaimCase, *, request_id: UUID,
                    decision_id: int,
                    actor_kind: str, actor_user_id: int | None, operation: str,
                    public_state: str, review_state: str, reason_code: str,
                    snapshot: NewsDecisionSnapshot, observed_at: datetime | None,
                    expires_at: datetime | None, now: datetime) -> NewsClaimDecision:
    revision = case.revision + 1
    decision = NewsClaimDecision(id=decision_id, case_id=case.id, revision=revision, request_id=request_id,
        actor_kind=actor_kind, actor_user_id=actor_user_id, operation=operation,
        public_state=public_state, review_state=review_state, reason_code=reason_code,
        evaluation_id=snapshot.evaluation_id, snapshot=snapshot.model_dump(mode="json"),
        observed_at=observed_at, expires_at=expires_at, decided_at=now)
    db.add(decision)
    case.revision = revision
    db.flush()
    if snapshot.public is not None:
        # The decision ID is assigned after flush; UPDATE is prohibited by the
        # append-only trigger. The service reserves an ID before insertion.
        if snapshot.public.decision_id != decision.id or snapshot.public.revision != revision:
            raise NewsPublicationError("decision_snapshot_identity_mismatch")
    return decision


def reserve_decision_id(db: Session) -> int:
    return db.scalar(text("SELECT nextval(pg_get_serial_sequence('news_claim_decisions', 'id'))"))
