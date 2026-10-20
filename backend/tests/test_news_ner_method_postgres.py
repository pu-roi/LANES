"""Real PostgreSQL method isolation using the existing opt-in owned queue fixture."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from sqlalchemy import func, select

from app.crud.news_processing import claim_due_run, enqueue_article, finish_owned_run
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.schemas.news_ner_result import NewsNerResult
from app.services.news_saved_run_service import saved_run_summary
from test_news_ner_method_boundary import PIPELINE, native_fixture
from test_news_processing_postgres import NOW, postgres_queue, seed


def test_concurrent_native_enqueue_and_mode_specific_skip_locked(postgres_queue):
    seed(postgres_queue)
    barrier = Barrier(2)
    def enqueue() -> int:
        with postgres_queue() as db, db.begin():
            row = db.scalar(select(NewsArticle))
            barrier.wait(timeout=10)
            return enqueue_article(db, row, mode="ner_rules_v1", pipeline_version=PIPELINE)
    with ThreadPoolExecutor(max_workers=2) as workers:
        a, b = workers.submit(enqueue), workers.submit(enqueue)
        assert a.result(timeout=30) == b.result(timeout=30)
    with postgres_queue() as db:
        assert db.scalar(select(func.count()).select_from(NewsArticleVersion)) == 2
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun)) == 2
    with postgres_queue() as first, first.begin():
        native = claim_due_run(first, NOW, mode="ner_rules_v1", pipeline_version=PIPELINE)
        with postgres_queue() as second, second.begin():
            legacy = claim_due_run(second, NOW)
            assert native.mode == "ner_rules_v1" and legacy.mode == "rules_only"
            assert native.run_id != legacy.run_id
            assert claim_due_run(second, NOW, mode="ner_rules_v1", pipeline_version=PIPELINE) is None


def test_native_retry_reclaim_completion_and_persisted_history(postgres_queue):
    seed(postgres_queue)
    with postgres_queue() as db, db.begin():
        native_id = enqueue_article(db, db.scalar(select(NewsArticle)), mode="ner_rules_v1", pipeline_version=PIPELINE)
        first = claim_due_run(db, NOW, mode="ner_rules_v1", pipeline_version=PIPELINE)
        assert finish_owned_run(db, first, NOW, error_code="ner_runtime_timeout", retryable=True)
    with postgres_queue() as db, db.begin():
        assert claim_due_run(db, NOW, mode="ner_rules_v1", pipeline_version=PIPELINE) is None
        second = claim_due_run(db, NOW + timedelta(minutes=1), mode="ner_rules_v1", pipeline_version=PIPELINE)
        assert second.attempt_count == 2
    late = NOW + timedelta(minutes=7)
    with postgres_queue() as db, db.begin():
        third = claim_due_run(db, late, mode="ner_rules_v1", pipeline_version=PIPELINE)
        result = native_fixture(db.get(NewsArticleVersion, third.article_version_id))
        assert not finish_owned_run(db, second, late, result=result)
        assert finish_owned_run(db, third, late, result=result)
    with postgres_queue() as db:
        stored = db.get(NewsExtractionRun, native_id)
        parsed = saved_run_summary(stored)
        assert isinstance(parsed.result, NewsNerResult)
        assert parsed.result.model_dump(mode="json", by_alias=True) == result
        assert stored.attempt_count == 3
        assert db.scalar(select(func.count()).select_from(NewsArticleVersion)) == 2


@pytest.mark.parametrize("mode", ["rules_only", "ner_rules_v1"])
def test_database_rows_with_colliding_pipeline_cannot_cross_worker_methods(postgres_queue, mode):
    seed(postgres_queue)
    from app.crud.news_processing import current_pipeline_version
    with postgres_queue() as db, db.begin():
        legacy = db.scalar(select(NewsExtractionRun))
        if mode == "rules_only":
            legacy.mode = "ner_rules_v1"
            worker_pipeline = current_pipeline_version()
        else:
            legacy.pipeline_version = PIPELINE
            worker_pipeline = PIPELINE
        db.flush()
        assert claim_due_run(db, NOW, mode=mode, pipeline_version=worker_pipeline) is None
        assert legacy.attempt_count == 0 and legacy.status == "pending"


def test_native_payload_cannot_be_finished_under_legacy_mode(postgres_queue):
    seed(postgres_queue)
    with postgres_queue() as db, db.begin():
        claim = claim_due_run(db, NOW)
        result = native_fixture(db.get(NewsArticleVersion, claim.article_version_id))
        with pytest.raises(ValueError, match="method_mismatch"):
            finish_owned_run(db, claim, NOW, result=result)
        assert db.get(NewsExtractionRun, claim.run_id).status == "processing"


@pytest.mark.parametrize("key", ["schema_version", "processing_method", "native"])
def test_postgres_legacy_reader_rejects_native_keys_even_when_json_null(postgres_queue, key):
    from app.crud.news_results import readable_run
    seed(postgres_queue)
    with postgres_queue() as db, db.begin():
        run = db.scalar(select(NewsExtractionRun))
        run.status, run.completed_at = "completed", NOW
        run.result = {"claims": [], "is_metadata_only": False, "errors": []}
        db.flush()
        assert db.scalar(select(readable_run(db)).where(NewsExtractionRun.id == run.id))
        run.result = {**run.result, key: None}
        db.flush()
        assert not db.scalar(select(readable_run(db)).where(NewsExtractionRun.id == run.id))
