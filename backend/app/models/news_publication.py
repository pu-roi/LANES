"""Approved durable news claim identity, evaluation and append-only decisions.

These records store publication evidence; inserting a row does not publish a
claim or authorize geometry. Services must enforce the write-boundary gates.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, Uuid, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.news import utc_now

if TYPE_CHECKING:
    from app.models.news import NewsExtractionRun
    from app.models.report import FloodAvoidanceZone
    from app.models.user import User


class NewsClaimCase(Base):
    __tablename__ = "news_claim_cases"
    __table_args__ = (CheckConstraint("revision >= 0", name="nonnegative_revision"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    sources: Mapped[list[NewsClaimSource]] = relationship(back_populates="case", passive_deletes="all")
    decisions: Mapped[list[NewsClaimDecision]] = relationship(back_populates="case", passive_deletes="all")


class NewsClaimSource(Base):
    __tablename__ = "news_claim_sources"
    __table_args__ = (
        UniqueConstraint("extraction_run_id", "claim_ordinal", name="uq_news_claim_source_identity"),
        CheckConstraint("claim_ordinal >= 0", name="nonnegative_ordinal"),
        CheckConstraint("claim_sha256 ~ '^[0-9a-f]{64}$'", name="claim_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("news_claim_cases.id", ondelete="RESTRICT"), index=True)
    extraction_run_id: Mapped[int] = mapped_column(ForeignKey("news_extraction_runs.id", ondelete="RESTRICT"), index=True)
    claim_ordinal: Mapped[int] = mapped_column(Integer)
    claim_sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    case: Mapped[NewsClaimCase] = relationship(back_populates="sources")
    extraction_run: Mapped[NewsExtractionRun] = relationship("NewsExtractionRun")
    evaluations: Mapped[list[NewsClaimEvaluation]] = relationship(back_populates="source", passive_deletes="all")


class NewsClaimEvaluation(Base):
    __tablename__ = "news_claim_evaluations"
    __table_args__ = (
        UniqueConstraint("claim_source_id", "policy_fingerprint", name="uq_news_claim_evaluation_identity"),
        CheckConstraint("policy_fingerprint ~ '^[0-9a-f]{64}$'", name="policy_hash"),
        CheckConstraint("status IN ('pending','processing','completed','retry_wait','failed')", name="evaluation_status"),
        CheckConstraint("attempt_count BETWEEN 0 AND 5", name="bounded_attempts"),
        CheckConstraint("(status = 'processing' AND lease_token IS NOT NULL AND lease_expires_at IS NOT NULL) OR "
                        "(status <> 'processing' AND lease_token IS NULL AND lease_expires_at IS NULL)", name="lease_state"),
        CheckConstraint("status <> 'completed' OR (result IS NOT NULL AND completed_at IS NOT NULL)", name="completed_result"),
        CheckConstraint("status <> 'failed' OR (error_code IS NOT NULL AND completed_at IS NOT NULL)", name="failed_result"),
        CheckConstraint("status <> 'retry_wait' OR (next_attempt_at IS NOT NULL AND error_code IS NOT NULL)", name="retry_state"),
        CheckConstraint("error_code IS NULL OR error_code ~ '^[a-z][a-z0-9_]{0,99}$'", name="safe_error_code"),
        CheckConstraint("result IS NULL OR jsonb_typeof(result) = 'object'", name="result_object"),
        Index("ix_news_claim_evaluation_due", "status", "next_attempt_at", "lease_expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    claim_source_id: Mapped[int] = mapped_column(ForeignKey("news_claim_sources.id", ondelete="RESTRICT"), index=True)
    policy_fingerprint: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30), default="pending", server_default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_token: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(100))
    result: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    source: Mapped[NewsClaimSource] = relationship(back_populates="evaluations")


class NewsClaimDecision(Base):
    __tablename__ = "news_claim_decisions"
    __table_args__ = (
        UniqueConstraint("case_id", "revision", name="uq_news_claim_decision_revision"),
        UniqueConstraint("request_id", name="uq_news_claim_decision_request"),
        CheckConstraint("revision > 0", name="positive_revision"),
        CheckConstraint("actor_kind IN ('automatic','staff','maintenance')", name="actor_kind"),
        CheckConstraint("(actor_kind = 'staff' AND actor_user_id IS NOT NULL) OR "
                        "(actor_kind IN ('automatic','maintenance') AND actor_user_id IS NULL)", name="actor_identity"),
        CheckConstraint("operation IN ('evaluate','correct','defer','reject','reopen','clear','expire')", name="operation"),
        CheckConstraint("public_state IN ('unpublished','active_alert','active_zone','withdrawn','expired')", name="public_state"),
        CheckConstraint("review_state IN ('needs_review','deferred','resolved')", name="review_state"),
        CheckConstraint("reason_code ~ '^[a-z][a-z0-9_]{0,99}$'", name="safe_reason_code"),
        CheckConstraint("jsonb_typeof(snapshot) = 'object' AND octet_length(snapshot::text) <= 65536", name="bounded_snapshot"),
        CheckConstraint("public_state NOT IN ('active_alert','active_zone') OR "
                        "(observed_at IS NOT NULL AND expires_at IS NOT NULL AND expires_at > observed_at)", name="active_expiry"),
        CheckConstraint("actor_kind <> 'automatic' OR operation <> 'evaluate' OR evaluation_id IS NOT NULL", name="automatic_evaluation"),
        CheckConstraint("operation NOT IN ('reject','clear','expire') OR public_state NOT IN ('active_alert','active_zone')", name="inactive_operation"),
        Index("ix_news_claim_decision_public_expiry", "public_state", "expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("news_claim_cases.id", ondelete="RESTRICT"), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    request_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True))
    evaluation_id: Mapped[int | None] = mapped_column(ForeignKey("news_claim_evaluations.id", ondelete="RESTRICT"))
    actor_kind: Mapped[str] = mapped_column(String(20))
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    operation: Mapped[str] = mapped_column(String(20))
    public_state: Mapped[str] = mapped_column(String(20))
    review_state: Mapped[str] = mapped_column(String(20))
    reason_code: Mapped[str] = mapped_column(String(100))
    snapshot: Mapped[dict] = mapped_column(JSONB)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    case: Mapped[NewsClaimCase] = relationship(back_populates="decisions")
    evaluation: Mapped[NewsClaimEvaluation | None] = relationship()
    actor: Mapped[User | None] = relationship("User")
    zone_links: Mapped[list[NewsClaimZoneLink]] = relationship(back_populates="decision", passive_deletes="all")


class NewsClaimZoneLink(Base):
    __tablename__ = "news_claim_zone_links"
    __table_args__ = (
        UniqueConstraint("decision_id", "zone_id", name="uq_news_claim_zone_link"),
        CheckConstraint("relation IN ('created','supported')", name="link_relation"),
        Index("uq_news_claim_zone_creation_owner", "zone_id", unique=True, postgresql_where=text("relation = 'created'")),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("news_claim_decisions.id", ondelete="RESTRICT"), index=True)
    zone_id: Mapped[int] = mapped_column(ForeignKey("flood_avoidance_zones.id", ondelete="RESTRICT"), index=True)
    relation: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    decision: Mapped[NewsClaimDecision] = relationship(back_populates="zone_links")
    zone: Mapped[FloodAvoidanceZone] = relationship("FloodAvoidanceZone")
