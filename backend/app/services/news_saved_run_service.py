"""Method-aware saved-run inspection, never inference or operational validation."""
from __future__ import annotations

from app.schemas.news_candidate import NewsExtractionRunSummary


class SavedRunReadError(ValueError):
    """Bounded public failure; no Pydantic/source text leaks into API errors."""


def saved_run_summary(run: object) -> NewsExtractionRunSummary:
    try:
        return NewsExtractionRunSummary.model_validate(run)
    except (ValueError, TypeError) as exc:
        raise SavedRunReadError("news_saved_result_unsupported_or_invalid") from exc
