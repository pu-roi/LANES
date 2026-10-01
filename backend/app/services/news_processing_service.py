"""Bounded durable rules extraction; never audits, publishes, or changes moderation."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.crud.news_processing import MAX_ATTEMPTS, capture_pending_inputs, claim_due_run, finish_owned_run, utc_now
from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_discovery_service import extract_captured_news_article, extraction_input_snapshot


@dataclass
class ProcessingSummary:
    captured: int = 0
    completed: int = 0
    retry_wait: int = 0
    failed: int = 0
    lease_lost: int = 0
    runs: list[dict] = field(default_factory=list)


async def process_saved_news(session_factory: Callable[[], Session], *, limit: int = 50,
                             article_id: int | None = None,
                             clock: Callable[[], datetime] = utc_now) -> ProcessingSummary:
    if not 1 <= limit <= 200:
        raise ValueError("Processing limit must be between 1 and 200")
    summary = ProcessingSummary()
    if article_id is None:
        with session_factory() as db, db.begin():
            summary.captured = capture_pending_inputs(db, limit)
    for _ in range(limit):
        with session_factory() as db, db.begin():
            claim = claim_due_run(db, clock(), article_id=article_id)
        if claim is None:
            break
        if claim.exhausted:
            summary.failed += 1
            summary.runs.append({"run_id": claim.run_id, "article_id": claim.article_id,
                                 "status": "failed", "error_code": "lease_expired_exhausted"})
            continue
        error_code, retryable, result = None, False, None
        try:
            source = NewsArticleExtractorInput.model_validate({**claim.input_snapshot, "article_id": claim.article_id})
            if extraction_input_snapshot(source)[1] != claim.input_fingerprint:
                error_code = "input_fingerprint_mismatch"
            else:
                extracted = await extract_captured_news_article(source)
                if extracted.error:
                    retryable = extracted.error.startswith("Extraction failed:")
                    error_code = "extraction_exception" if retryable else "invalid_article_body"
                elif extracted.extraction is None or extracted.extraction.errors:
                    error_code, retryable = "extraction_result_errors", True
                else:
                    result = extracted.extraction.model_dump(mode="json")
        except ValidationError:
            error_code = "invalid_input_snapshot"
        except Exception:
            error_code, retryable = "extraction_exception", True
        # Storage failures deliberately propagate; never report durable success
        # if the completion transaction failed. Lease expiry recovers lost work.
        now = clock()
        with session_factory() as db, db.begin():
            owned = finish_owned_run(db, claim, now, result=result, error_code=error_code, retryable=retryable)
        status = ("lease_lost" if not owned else "retry_wait" if error_code and retryable and claim.attempt_count < MAX_ATTEMPTS
                  else "failed" if error_code else "completed")
        setattr(summary, status, getattr(summary, status) + 1)
        summary.runs.append({"run_id": claim.run_id, "article_id": claim.article_id,
                             "status": status, "error_code": error_code})
    return summary
