"""Bounded automatic activation from operator-owned exact current footprints.

Catalog lookup selects candidates; the publication service rechecks every
approval/evidence/revision gate inside the atomic activation transaction.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from pydantic import ValidationError
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.crud.news_evaluation import require_utc
from app.crud.news_processing import utc_now
from app.crud.news_publication import NewsPublicationError
from app.models.news_publication import NewsClaimCase, NewsClaimDecision
from app.schemas.news_publication import NewsDecisionSnapshot
from app.services.news_evaluation_service import EvaluationPolicy
from app.services.news_publication_service import activate_operational_footprint, activate_estimated_road, require_geometry_review
from app.services.news_sources import NewsSource
from app.services.news_estimated_road_service import estimated_road_asset_revision
from app.services.operational_footprint_evidence_service import get_incident_footprint_provider


@dataclass
class FootprintWorkerSummary:
    catalog_status: str = "not_configured"
    considered: int = 0
    activated: int = 0
    estimated_considered: int = 0
    estimated_activated: int = 0
    unresolved: list[dict] = field(default_factory=list)
    next_after_case_id: int = 0
    outcomes: list[dict] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)


def process_news_footprints(session_factory: Callable[[], Session], *, policy: EvaluationPolicy,
        limit: int = 50, after_case_id: int = 0, clock: Callable[[], datetime] = utc_now,
        sources: tuple[NewsSource, ...] | None = None) -> FootprintWorkerSummary:
    if not 1 <= limit <= 200 or after_case_id < 0:
        raise ValueError("Invalid footprint worker batch")
    now = require_utc(clock())
    assets = get_incident_footprint_provider()
    summary = FootprintWorkerSummary()
    if assets.error:
        if assets.error != "operational_footprint_catalog_not_configured":
            summary.catalog_status = "invalid"
            summary.skipped.append({"reason_code": assets.error})
            return summary
    else:
        summary.catalog_status = "ready"
    # No guessed perimeter, source label or ranked asset enters this stage.
    # Filter by approved exact input/claim identity before batching so alerts
    # without footprints cannot starve eligible cases behind them. Scan the
    # bounded catalog even after failures; limit caps successful activations,
    # so permanently rejected early records cannot starve later cases when a
    # scheduled process restarts with cursor zero.
    identities = [and_(NewsClaimDecision.snapshot["article_id"].as_integer() == record.article_id,
        NewsClaimDecision.snapshot["input_sha256"].astext == record.input_sha256,
        NewsClaimDecision.snapshot["claim_sha256"].astext == record.claim_sha256,
        NewsClaimDecision.snapshot["incident_identity"].astext == record.incident_identity,
        NewsClaimDecision.observed_at == record.observed_at) for record in assets.records.values()]
    with session_factory() as db:
        ids = list(db.scalars(select(NewsClaimDecision.id).join(NewsClaimCase,
            NewsClaimCase.id == NewsClaimDecision.case_id).where(
            NewsClaimCase.id > after_case_id, NewsClaimDecision.revision == NewsClaimCase.revision,
            NewsClaimDecision.public_state == "active_alert", NewsClaimDecision.actor_kind == "automatic",
            NewsClaimDecision.operation == "evaluate", NewsClaimDecision.expires_at > now,
            NewsClaimDecision.snapshot["policy_fingerprint"].astext == policy.fingerprint,
            or_(*identities) if identities else False).order_by(NewsClaimCase.id).limit(500)))
    attempted_cases = set()
    for decision_id in ids:
        if summary.activated >= limit:
            break
        case_id = None
        try:
            with session_factory() as db, db.begin():
                decision = db.get(NewsClaimDecision, decision_id)
                case_id = decision.case_id
                attempted_cases.add(case_id)
                summary.considered += 1
                summary.next_after_case_id = case_id
                snapshot = NewsDecisionSnapshot.model_validate(decision.snapshot)
                public = snapshot.public
                matches = [record for record in assets.records.values() if public is not None
                    and record.article_id == snapshot.article_id and record.input_sha256 == snapshot.input_sha256
                    and record.claim_sha256 == snapshot.claim_sha256 and record.incident_identity == snapshot.incident_identity
                    and record.observed_at == public.observed_at]
                if len(matches) != 1:
                    raise NewsPublicationError("ambiguous_operational_footprint_records")
                record = matches[0]
                result = activate_operational_footprint(db, case_id, record.geometry,
                    expected_revision=decision.revision, geometry_srid=record.srid,
                    evidence_record_id=record.record_id, provenance_source=record.source_id,
                    provenance_checksum=record.source_sha256, policy=policy, now=clock(), sources=sources)
                outcome = {"case_id": case_id, "decision_id": result.id, "status": result.public_state}
            summary.activated += 1
            summary.outcomes.append(outcome)
        except NewsPublicationError as exc:
            summary.skipped.append({"case_id": case_id, "reason_code": exc.code})
        except (ValidationError, ValueError, TypeError, KeyError):
            summary.skipped.append({"case_id": case_id, "reason_code": "invalid_decision_snapshot"})
        except SQLAlchemyError:
            # An individual transaction rolls back; report only a safe code.
            # A later claim can still activate, and the next sweep retries it.
            summary.skipped.append({"case_id": case_id, "reason_code": "footprint_storage_unavailable"})
    # Catalog-backed current extents take priority. Otherwise estimate only
    # from server-owned article-scoped OSM/NOAH assets. Bound scanning as well
    # as activations, and never override staff decisions or active zones.
    if summary.activated < limit:
        asset_revision = estimated_road_asset_revision()
        with session_factory() as db:
            candidates = list(db.execute(select(NewsClaimDecision.id, NewsClaimCase.id, NewsClaimDecision.revision)
                .join(NewsClaimCase, NewsClaimCase.id == NewsClaimDecision.case_id).where(
                    NewsClaimCase.id > after_case_id, NewsClaimDecision.revision == NewsClaimCase.revision,
                    NewsClaimDecision.public_state == "active_alert", NewsClaimDecision.actor_kind == "automatic",
                    NewsClaimDecision.operation == "evaluate", NewsClaimDecision.expires_at > now,
                    NewsClaimDecision.snapshot["policy_fingerprint"].astext == policy.fingerprint,
                    or_(NewsClaimDecision.snapshot["estimated_road_review_revision"].astext.is_(None),
                        NewsClaimDecision.snapshot["estimated_road_review_revision"].astext != asset_revision),
                    NewsClaimCase.id.not_in(attempted_cases)).order_by(NewsClaimCase.id).limit(500)))
        for _, case_id, revision in candidates:
            if summary.activated >= limit:
                break
            summary.estimated_considered += 1
            summary.next_after_case_id = case_id
            try:
                with session_factory() as db, db.begin():
                    decision = activate_estimated_road(db, case_id, expected_revision=revision,
                        policy=policy, now=clock(), sources=sources)
                    outcome = {"case_id": case_id, "decision_id": decision.id, "status": decision.public_state}
                summary.activated += 1
                summary.estimated_activated += 1
                summary.outcomes.append(outcome)
            except NewsPublicationError as exc:
                if exc.code == "stale_case_revision":
                    continue
                try:
                    with session_factory() as db, db.begin():
                        require_geometry_review(db, case_id, expected_revision=revision, reason=exc.code, now=now,
                                                asset_revision=asset_revision)
                except SQLAlchemyError:
                    summary.skipped.append({"case_id": case_id, "reason_code": "footprint_storage_unavailable"})
                    continue
                summary.unresolved.append({"case_id": case_id, "reason_code": exc.code})
            except (ValidationError, ValueError, TypeError, KeyError):
                summary.skipped.append({"case_id": case_id, "reason_code": "invalid_estimated_road_evidence"})
            except SQLAlchemyError:
                summary.skipped.append({"case_id": case_id, "reason_code": "footprint_storage_unavailable"})
    if summary.activated < limit and (not ids or len(ids) < 500) and (summary.estimated_considered < 500):
        summary.next_after_case_id = 0  # wrap to admit newly provisioned old alerts
    return summary
