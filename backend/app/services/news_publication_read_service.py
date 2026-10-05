"""Safe current-time projections of immutable news publication decisions."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.news_publication_read import (
    list_decision_history, list_public_decisions, read_latest_decision, source_input_for_decision,
)
from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimEvaluation, NewsClaimSource
from app.schemas.news_extraction import NewsArticleExtractorInput
from app.schemas.news_publication import (
    NewsClaimDetail, NewsDecisionSnapshot, NewsDecisionSummary, NewsEvaluationOption, PublicNewsAlert, PublicNewsAlertPage,
)
from app.schemas.news_publication_reads import StaffNewsDecision, StaffNewsDecisionPage
from app.services.news_evaluation_service import source_is_approved
from app.services.news_sources import NewsSource, load_news_sources


def publication_read_clock() -> datetime:
    return datetime.now(timezone.utc)


def decision_summary(decision: NewsClaimDecision) -> NewsDecisionSummary:
    return NewsDecisionSummary(**{field: getattr(decision, field) for field in NewsDecisionSummary.model_fields})


def _approved_public_source(db: Session, decision: NewsClaimDecision, sources: tuple[NewsSource, ...]) -> bool:
    snapshot = source_input_for_decision(db, decision)
    if snapshot is None:
        return False
    frozen = NewsArticleExtractorInput.model_validate(snapshot)
    public = NewsDecisionSnapshot.model_validate(decision.snapshot).public
    return bool(public is not None and public.source_url == frozen.canonical_url
                and source_is_approved(frozen, sources))


def browse_public_news_alerts(db: Session, *, page: int, page_size: int,
                             now: datetime | None = None, sources: tuple[NewsSource, ...] | None = None) -> PublicNewsAlertPage:
    from app.services.news_publication_service import public_projection
    now = now or publication_read_clock()
    sources = sources if sources is not None else load_news_sources()
    rows, total, actual_page = list_public_decisions(db, now=now, page=page, page_size=page_size,
        approved_source_ids=tuple(source.id for source in sources if source.enabled and source.verified_at is not None))
    items = []
    for decision in rows:
        NewsDecisionSnapshot.model_validate(decision.snapshot)
        if not _approved_public_source(db, decision, sources):
            # A source-domain policy change must not expose stale unsafe links.
            # Raise a safe feed error instead of returning an inconsistent page.
            raise ValueError("Published source is no longer approved")
        item = public_projection(decision, now)
        if item is None:
            raise ValueError("Published projection is inconsistent with current feed")
        items.append(item)
    return PublicNewsAlertPage(items=items, total=total, page=actual_page, page_size=page_size,
                               pages=max(1, (total + page_size - 1) // page_size), as_of=now)


def read_public_news_alert(db: Session, case_id: int, *, now: datetime | None = None,
                          sources: tuple[NewsSource, ...] | None = None) -> PublicNewsAlert | None:
    from app.services.news_publication_service import public_projection
    decision = read_latest_decision(db, case_id)
    if decision is None:
        return None
    NewsDecisionSnapshot.model_validate(decision.snapshot)
    sources = sources if sources is not None else load_news_sources()
    if not _approved_public_source(db, decision, sources):
        return None
    return public_projection(decision, now or publication_read_clock(), include_retained=True)


def _evaluation_options(db: Session, case_id: int) -> list[NewsEvaluationOption]:
    article_ids = select(NewsArticleVersion.article_id).join(
        NewsExtractionRun, NewsExtractionRun.article_version_id == NewsArticleVersion.id).join(
        NewsClaimSource, NewsClaimSource.extraction_run_id == NewsExtractionRun.id).where(NewsClaimSource.case_id == case_id)
    rows = db.execute(select(NewsClaimEvaluation, NewsClaimSource, NewsExtractionRun).join(
        NewsClaimSource, NewsClaimSource.id == NewsClaimEvaluation.claim_source_id).join(
        NewsExtractionRun, NewsExtractionRun.id == NewsClaimSource.extraction_run_id).join(
        NewsArticleVersion, NewsArticleVersion.id == NewsExtractionRun.article_version_id).where(
        NewsArticleVersion.article_id.in_(article_ids), NewsClaimEvaluation.status == "completed")
        .order_by(NewsClaimEvaluation.id.desc()).limit(100)).all()
    options = []
    for evaluation, source, run in rows:
        claim = run.result["claims"][source.claim_ordinal]
        audit = (evaluation.result or {}).get("audit") or {}
        if audit.get("outcome") != "verified":
            continue
        # These are evidence choices, not authorization. Preview and final
        # transaction independently recheck policy, quotes, identity and time.
        if source.case_id == case_id or claim.get("condition") == "subsided":
            options.append(NewsEvaluationOption(evaluation_id=evaluation.id, source_id=source.id, run_id=run.id,
                claim_ordinal=source.claim_ordinal, condition=claim["condition"], observed_at=claim.get("event_time_resolved"),
                outcome=audit["outcome"], reason_code=audit.get("reason_code", "independently_verified")))
    return options


def allowed_news_actions(case: NewsClaimCase, current: NewsClaimDecision | None, *, can_write: bool,
                         options: list[NewsEvaluationOption]) -> list[str]:
    if not can_write:
        return []
    if current is None:
        return ["defer", "reject"]
    actions = ["defer", "reject"]
    if any(option.condition in ("active", "rising") for option in options):
        actions.insert(0, "correct")
    if current.public_state in ("active_alert", "active_zone", "expired") and any(option.condition == "subsided" for option in options):
        actions.append("clear")
    if current.public_state in ("withdrawn", "unpublished"):
        actions.append("reopen")
    return actions


def read_news_claim_detail(db: Session, case_id: int, *, can_write: bool = False,
                           now: datetime | None = None) -> NewsClaimDetail | None:
    from app.services.news_publication_service import public_projection
    case = db.get(NewsClaimCase, case_id)
    if case is None:
        return None
    now = now or publication_read_clock()
    current = read_latest_decision(db, case_id)
    options = _evaluation_options(db, case_id) if can_write else []
    rows, _, _ = list_decision_history(db, case_id, page=1, page_size=20)
    return NewsClaimDetail(case_id=case_id, revision=case.revision,
        allowed_actions=allowed_news_actions(case, current, can_write=can_write, options=options),
        current=decision_summary(current) if current else None,
        public=public_projection(current, now, include_retained=True) if current else None,
        decisions=[decision_summary(row) for row in rows], evaluation_options=options)


def browse_news_claim_history(db: Session, case_id: int, *, page: int, page_size: int,
                              now: datetime | None = None) -> StaffNewsDecisionPage | None:
    if db.get(NewsClaimCase, case_id) is None:
        return None
    rows, total, actual_page = list_decision_history(db, case_id, page=page, page_size=page_size)
    items = []
    for row in rows:
        snapshot = NewsDecisionSnapshot.model_validate(row.snapshot)
        items.append(StaffNewsDecision(**decision_summary(row).model_dump(), request_id=row.request_id,
            actor_kind=row.actor_kind, actor_user_id=row.actor_user_id, evaluation_id=row.evaluation_id,
            private_reason=snapshot.private_reason,
            public_correction=snapshot.public.correction_note if snapshot.public else None))
    return StaffNewsDecisionPage(items=items, total=total, page=actual_page, page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size), as_of=now or publication_read_clock())
