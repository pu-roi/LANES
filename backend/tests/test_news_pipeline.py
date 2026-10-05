"""The explicit pipeline preserves stage boundaries and propagates storage errors."""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.services import news_pipeline_service as pipeline, news_publication_service as publication
from app.services.news_evaluation_service import EvaluationSummary
from app.services.news_processing_service import ProcessingSummary
from app.services.news_publication_service import PublicationSummary


@pytest.mark.asyncio
async def test_pipeline_handoff_uses_committed_stages_and_still_expires_after_provider_failure(monkeypatch):
    order=[]
    factory=lambda: None
    policy=SimpleNamespace(fingerprint="fixture")
    async def process(actual,**kwargs):
        assert actual is factory
        order.append("committed_extraction")
        return ProcessingSummary(completed=1)
    def seed(actual,actual_policy,**kwargs):
        assert actual is factory and actual_policy is policy
        assert order == ["committed_extraction"] and kwargs["after_run_id"] == 7
        order.append("committed_seed")
        return EvaluationSummary(evaluations_created=1,next_after_run_id=8)
    async def evaluate(actual,**kwargs):
        assert kwargs["policy"] is policy
        order.append("completed_provider_failure")
        return EvaluationSummary(failed=1)
    def publish(actual,**kwargs):
        assert kwargs["policy"] is policy
        order.append("publication_and_expiry")
        return PublicationSummary(needs_review=1,expired=1)
    monkeypatch.setattr(pipeline,"process_saved_news",process)
    monkeypatch.setattr(pipeline,"seed_claim_evaluations",seed)
    monkeypatch.setattr(pipeline,"evaluate_news_claims",evaluate)
    monkeypatch.setattr(pipeline,"evaluation_policy",lambda _:policy)
    monkeypatch.setattr(publication,"process_news_publications",publish)
    summary=await pipeline.run_news_pipeline(factory,seed_cursor=7,auditor=object(),clock=lambda:datetime.now(timezone.utc))
    assert summary["next_seed_cursor"] == 8
    assert summary["extraction"]["completed"] == 1
    assert summary["evaluation"]["failed"] == summary["publication"]["expired"] == 1
    assert order == ["committed_extraction","committed_seed","completed_provider_failure","publication_and_expiry"]


@pytest.mark.asyncio
async def test_pipeline_storage_failure_never_reports_publication_success(monkeypatch):
    async def unavailable(*_,**__):
        raise SQLAlchemyError("synthetic storage outage")
    def unexpected(*_,**__):
        raise AssertionError("Publication must not run after a lost extraction commit")
    monkeypatch.setattr(pipeline,"process_saved_news",unavailable)
    monkeypatch.setattr(pipeline,"evaluation_policy",lambda _:object())
    monkeypatch.setattr(publication,"process_news_publications",unexpected)
    with pytest.raises(SQLAlchemyError):
        await pipeline.run_news_pipeline(lambda:None,auditor=object())
