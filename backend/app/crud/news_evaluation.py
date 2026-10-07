"""Bounded unpublished claim bindings and owned evaluation leases; never commit."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
from uuid import UUID, uuid4

from sqlalchemy import or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimCase, NewsClaimEvaluation, NewsClaimSource
from app.schemas.news_extraction import NewsArticleExtractorInput, NewsExtractionResult
from app.services.news_claim_auditor import canonical_claim_sha256
from app.services.news_discovery_service import MAX_ARTICLE_CHARS, extraction_input_snapshot

MAX_ATTEMPTS = 5
LEASE_SECONDS = 120


def canonical_sha256(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require_utc(now: datetime) -> datetime:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Evaluation clock requires a timezone")
    return now.astimezone(timezone.utc)


def validate_run(run: NewsExtractionRun, version: NewsArticleVersion) -> tuple[NewsArticleExtractorInput, NewsExtractionResult]:
    if run.status != "completed" or run.completed_at is None or run.mode != "rules_only":
        raise ValueError("extraction_not_completed")
    article = NewsArticleExtractorInput.model_validate({**version.input_snapshot, "article_id": version.article_id})
    if extraction_input_snapshot(article)[1] != version.input_fingerprint:
        raise ValueError("input_fingerprint_mismatch")
    text = (article.article_text or "").strip()
    if not text or len(article.article_text or "") > MAX_ARTICLE_CHARS:
        raise ValueError("invalid_article_body")
    result = NewsExtractionResult.model_validate(run.result)
    if (result.article_id != version.article_id or result.canonical_url != article.canonical_url
            or result.is_metadata_only or result.errors or result.processed_text_length != len(text)
            or len(result.claims) > 500):
        raise ValueError("invalid_extraction_result")
    for claim in result.claims:
        start, end = claim.evidence_sentence_offset
        if not (0 <= start < end <= len(text)) or text[start:end].strip() != claim.evidence_sentence.strip():
            raise ValueError("invalid_evidence_offsets")
        if (not (start <= claim.place_char_start < claim.place_char_end <= end)
                or text[claim.place_char_start:claim.place_char_end] != claim.raw_place_name):
            raise ValueError("invalid_place_offsets")
        # Reject coercible nonfinite values before any binding or JSON write.
        canonical_claim_sha256(claim)
    return article, result


def bind_completed_run(db: Session, run_id: int, policy_fingerprint: str, now: datetime) -> tuple[int, int]:
    """Serialize a run's bindings; retries reuse sources and policy evaluations.

    New runs get separate unpublished cases. Cross-run continuity is intentionally
    not inferred from ordinal, road name, title or proximity.
    """
    now = require_utc(now)
    if not re.fullmatch(r"[0-9a-f]{64}", policy_fingerprint):
        raise ValueError("invalid_policy_fingerprint")
    if db.get_bind().dialect.name != "postgresql":
        raise ValueError("Claim evaluation requires PostgreSQL")
    run = db.scalar(select(NewsExtractionRun).where(NewsExtractionRun.id == run_id).with_for_update())
    if run is None:
        raise ValueError("extraction_not_found")
    version = db.get(NewsArticleVersion, run.article_version_id)
    _, result = validate_run(run, version)
    # Validate every existing immutable binding before creating any new rows.
    existing = {row.claim_ordinal: row for row in db.scalars(select(NewsClaimSource).where(
        NewsClaimSource.extraction_run_id == run_id)).all()}
    hashes = [canonical_claim_sha256(claim) for claim in result.claims]
    if any(ordinal >= len(hashes) or source.claim_sha256 != hashes[ordinal]
           for ordinal, source in existing.items()):
        raise ValueError("claim_fingerprint_mismatch")
    sources_created = evaluations_created = 0
    for ordinal, digest in enumerate(hashes):
        source = existing.get(ordinal)
        if source is None:
            case = NewsClaimCase(created_at=now)
            db.add(case)
            db.flush()
            source = NewsClaimSource(case_id=case.id, extraction_run_id=run_id,
                                     claim_ordinal=ordinal, claim_sha256=digest, created_at=now)
            db.add(source)
            db.flush()
            sources_created += 1
        created = db.scalar(insert(NewsClaimEvaluation).values(
            claim_source_id=source.id, policy_fingerprint=policy_fingerprint, status="pending",
            attempt_count=0, created_at=now, updated_at=now,
        ).on_conflict_do_nothing(index_elements=["claim_source_id", "policy_fingerprint"])
            .returning(NewsClaimEvaluation.id))
        evaluations_created += int(created is not None)
    return sources_created, evaluations_created


@dataclass(frozen=True)
class ClaimedEvaluation:
    evaluation_id: int
    source_id: int
    case_id: int
    run_id: int
    claim_ordinal: int
    claim_sha256: str
    input_fingerprint: str
    policy_fingerprint: str
    lease_token: UUID | None
    attempt_count: int
    input_snapshot: dict
    extraction_result: dict
    exhausted: bool = False


def claim_due_evaluation(db: Session, now: datetime, *, policy_fingerprint: str,
                         run_id: int | None = None,
                         exclude_evaluation_ids: tuple[int, ...] = (), source_ids: tuple[str, ...] | None = None) -> ClaimedEvaluation | None:
    now = require_utc(now)
    row_type = NewsClaimEvaluation
    due = or_(row_type.status == "pending",
              (row_type.status == "retry_wait") & (row_type.next_attempt_at <= now),
              (row_type.status == "processing") & (row_type.lease_expires_at <= now))
    query = select(row_type).join(NewsClaimSource).where(due, row_type.policy_fingerprint == policy_fingerprint)
    if source_ids is not None:
        query = query.join(NewsExtractionRun, NewsExtractionRun.id == NewsClaimSource.extraction_run_id).join(
            NewsArticleVersion, NewsArticleVersion.id == NewsExtractionRun.article_version_id).where(
                NewsArticleVersion.input_snapshot["publisher"].as_string().in_(source_ids))
    if exclude_evaluation_ids:
        query = query.where(row_type.id.not_in(exclude_evaluation_ids))
    if run_id is not None:
        query = query.where(NewsClaimSource.extraction_run_id == run_id)
    row = db.scalar(query.order_by(row_type.created_at, row_type.id)
                    .with_for_update(of=row_type, skip_locked=True).limit(1))
    if row is None:
        return None
    source = db.get(NewsClaimSource, row.claim_source_id)
    run = db.get(NewsExtractionRun, source.extraction_run_id)
    version = db.get(NewsArticleVersion, run.article_version_id)
    exhausted = row.attempt_count >= MAX_ATTEMPTS
    if exhausted:
        row.status, row.error_code = "failed", "lease_expired_exhausted"
        row.lease_token = row.lease_expires_at = row.next_attempt_at = None
        row.completed_at = row.updated_at = now
    else:
        row.status = "processing"
        row.attempt_count += 1
        row.lease_token = uuid4()
        row.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
        row.started_at = row.updated_at = now
        row.error_code = row.next_attempt_at = row.completed_at = None
        row.result = None
    db.flush()
    return ClaimedEvaluation(row.id, source.id, source.case_id, run.id, source.claim_ordinal,
                             source.claim_sha256, version.input_fingerprint, row.policy_fingerprint,
                             row.lease_token, row.attempt_count,
                             {**deepcopy(version.input_snapshot), "article_id": version.article_id},
                             deepcopy(run.result), exhausted)


def finish_owned_evaluation(db: Session, claim: ClaimedEvaluation, now: datetime, *,
                            result: dict | None = None, error_code: str | None = None,
                            retryable: bool = False) -> bool:
    """Terminal results are append-only; a lost lease cannot overwrite evidence."""
    now = require_utc(now)
    if error_code is not None and not re.fullmatch(r"[a-z][a-z0-9_]{0,99}", error_code):
        raise ValueError("Invalid safe evaluation error code")
    values: dict = {"lease_token": None, "lease_expires_at": None, "updated_at": now}
    if error_code:
        retry = retryable and claim.attempt_count < MAX_ATTEMPTS
        values.update(status="retry_wait" if retry else "failed", error_code=error_code, result=None,
                      next_attempt_at=now + timedelta(seconds=min(900, 60 * 2 ** (claim.attempt_count - 1))) if retry else None,
                      completed_at=None if retry else now)
    else:
        if not isinstance(result, dict) or len(json.dumps(result, ensure_ascii=False, allow_nan=False).encode()) > 65536:
            raise ValueError("Completed evaluation requires a bounded result object")
        values.update(status="completed", result=result, error_code=None, next_attempt_at=None, completed_at=now)
    changed = db.execute(update(NewsClaimEvaluation).where(
        NewsClaimEvaluation.id == claim.evaluation_id, NewsClaimEvaluation.status == "processing",
        NewsClaimEvaluation.lease_token == claim.lease_token, NewsClaimEvaluation.lease_expires_at > now,
        NewsClaimEvaluation.policy_fingerprint == claim.policy_fingerprint,
    ).values(**values).execution_options(synchronize_session=False))
    return changed.rowcount == 1
