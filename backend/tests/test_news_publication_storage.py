"""Publication storage checks on a fresh, explicitly disposable local PostGIS DB.

Set TEST_NEWS_PUBLICATION_DATABASE_URL to a loopback database whose name starts
with lanes_publication_test_. Never point this suite at LANES or cloud data.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from geoalchemy2 import WKTElement
from sqlalchemy import CheckConstraint, create_engine, delete, func, inspect, select, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, configure_mappers

from app.models import (
    FloodAvoidanceZone, NewsArticle, NewsArticleVersion, NewsExtractionRun,
    NewsClaimCase, NewsClaimSource, NewsClaimEvaluation, NewsClaimDecision, NewsClaimZoneLink,
    Role, User,
)

PREVIOUS = "c5a7e9d2104f"
REVISION = "d7e4b9a21c60"
NOW = datetime(2026, 10, 5, tzinfo=timezone.utc)
MODELS = (NewsClaimCase, NewsClaimSource, NewsClaimEvaluation, NewsClaimDecision, NewsClaimZoneLink)
TABLES = {model.__tablename__ for model in MODELS}
PRIOR_TABLES = ("news_articles", "news_article_versions", "news_extraction_runs", "flood_avoidance_zones")


def migration_config() -> Config:
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    return config


def test_publication_migration_extends_one_head_and_registers_relationships() -> None:
    scripts = ScriptDirectory.from_config(migration_config())
    assert scripts.get_heads() == [REVISION]
    assert scripts.get_revision(REVISION).down_revision == PREVIOUS
    configure_mappers()
    assert NewsClaimSource.extraction_run.property.mapper.class_ is NewsExtractionRun
    assert NewsClaimZoneLink.zone.property.mapper.class_ is FloodAvoidanceZone
    assert NewsClaimDecision.actor.property.mapper.class_ is User


@pytest.fixture(scope="module")
def publication_database():
    database_url = os.environ.get("TEST_NEWS_PUBLICATION_DATABASE_URL")
    if not database_url:
        pytest.skip("Fresh disposable local PostGIS URL required")
    parsed = make_url(database_url)
    assert parsed.host in ("localhost", "127.0.0.1", "::1"), "Refusing a non-local database"
    assert (parsed.database or "").startswith("lanes_publication_test_"), "Refusing a non-test database"
    from app.core.config import settings

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(settings, "DATABASE_URL", database_url)
    engine = create_engine(database_url)
    config = migration_config()
    try:
        assert not (set(inspect(engine).get_table_names()) & {"users", "news_articles", *TABLES}), "Expected fresh DB"
        command.upgrade(config, PREVIOUS)
        with Session(engine) as db, db.begin():
            article = NewsArticle(canonical_url="https://example.org/preserved-publication-evidence",
                publisher_source_id="fixture", title="Preserved source", excerpt="",
                article_text="Original wet evidence", content_fingerprint="a" * 64)
            db.add(article)
            db.flush()
            version = NewsArticleVersion(article_id=article.id, input_fingerprint="b" * 64,
                                         input_snapshot={"article_text": "Original wet evidence"})
            db.add(version)
            db.flush()
            run = NewsExtractionRun(article_version_id=version.id, pipeline_version="fixture-v1",
                status="completed", completed_at=NOW, result={"claims": [{"raw_place_name": "Fixture Road"}]})
            zone = FloodAvoidanceZone(geometry=WKTElement("POLYGON((121 14,121.001 14,121.001 14.001,121 14))", srid=4326),
                                      is_active=True, expires_at=NOW + timedelta(hours=2))
            db.add_all([run, zone])
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT postgis_version()"))
            prior_rows = {table: connection.execute(text(f"SELECT row_to_json(t)::text FROM {table} t ORDER BY id")).scalars().all()
                          for table in PRIOR_TABLES}
        prior_tables = set(inspect(engine).get_table_names())
        command.upgrade(config, "head")
        command.upgrade(config, "head")
        yield engine, config, prior_rows, prior_tables
    finally:
        engine.dispose()
        monkeypatch.undo()


def assert_prior_evidence(engine, prior_rows: dict) -> None:
    with engine.connect() as connection:
        for table, rows in prior_rows.items():
            assert connection.execute(text(f"SELECT row_to_json(t)::text FROM {table} t ORDER BY id")).scalars().all() == rows


def test_upgrade_repeat_downgrade_reupgrade_preserves_evidence(publication_database) -> None:
    engine, config, prior_rows, prior_tables = publication_database
    assert set(inspect(engine).get_table_names()) == prior_tables | TABLES
    assert_prior_evidence(engine, prior_rows)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == REVISION
        for table in TABLES:
            assert connection.scalar(text(f"SELECT count(*) FROM {table}")) == 0
    command.downgrade(config, PREVIOUS)
    assert set(inspect(engine).get_table_names()) == prior_tables
    with engine.connect() as connection:
        for function in ("reject_news_publication_change", "check_news_automatic_evaluation", "check_news_zone_link_decision"):
            assert connection.scalar(text("SELECT to_regprocedure(:signature)"), {"signature": function + "()"}) is None
    assert_prior_evidence(engine, prior_rows)
    command.upgrade(config, "head")
    assert_prior_evidence(engine, prior_rows)


def test_migrated_schema_matches_models_and_restricts_all_foreign_keys(publication_database) -> None:
    engine = publication_database[0]
    inspector = inspect(engine)
    for model in MODELS:
        table = model.__table__
        columns = {column["name"]: column for column in inspector.get_columns(table.name)}
        assert set(columns) == set(table.columns.keys())
        for column in table.columns:
            reflected = columns[column.name]
            assert reflected["nullable"] == column.nullable
            assert str(reflected["type"].compile(dialect=engine.dialect)) == str(column.type.compile(dialect=engine.dialect))
            if column.server_default:
                assert reflected["default"] is not None
        assert {check["name"] for check in inspector.get_check_constraints(table.name)} == {
            constraint.name for constraint in table.constraints if isinstance(constraint, CheckConstraint)}
        assert {index["name"] for index in inspector.get_indexes(table.name)} >= {index.name for index in table.indexes}
        assert all(fk["options"]["ondelete"] == "RESTRICT" for fk in inspector.get_foreign_keys(table.name))
    ownership = next(index for index in inspector.get_indexes("news_claim_zone_links")
                     if index["name"] == "uq_news_claim_zone_creation_owner")
    assert ownership["unique"] and "created" in str(ownership["dialect_options"]["postgresql_where"])


@pytest.fixture
def publication_session(publication_database):
    engine = publication_database[0]
    with engine.connect() as connection:
        transaction = connection.begin()
        db = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield db
        finally:
            db.close()
            transaction.rollback()


@pytest.fixture
def claim_records(publication_session):
    db = publication_session
    case = NewsClaimCase()
    db.add(case)
    db.flush()
    source = NewsClaimSource(case_id=case.id, extraction_run_id=db.scalar(select(NewsExtractionRun.id)),
                             claim_ordinal=0, claim_sha256="c" * 64)
    db.add(source)
    db.flush()
    evaluation = NewsClaimEvaluation(claim_source_id=source.id, policy_fingerprint="d" * 64)
    db.add(evaluation)
    db.flush()
    return case, source, evaluation


def complete_audit(db: Session, evaluation: NewsClaimEvaluation) -> None:
    evaluation.status, evaluation.result, evaluation.completed_at = "completed", {"audit": "fixture"}, NOW
    db.flush()


def decision(case: NewsClaimCase, **overrides) -> NewsClaimDecision:
    fields = dict(case_id=case.id, revision=1, request_id=uuid4(), actor_kind="maintenance", operation="expire",
                  public_state="expired", review_state="resolved", reason_code="evidence_stale",
                  snapshot={"schema_version": 1}, observed_at=NOW, expires_at=NOW + timedelta(hours=2))
    return NewsClaimDecision(**(fields | overrides))


@pytest.mark.parametrize("changes", [
    {"attempt_count": -1}, {"attempt_count": 6}, {"policy_fingerprint": "D" * 64},
    {"status": "processing"}, {"lease_token": uuid4()}, {"status": "completed"},
    {"status": "completed", "completed_at": NOW, "result": None},
    {"status": "completed", "completed_at": NOW, "result": []},
    {"status": "failed"}, {"status": "retry_wait"}, {"error_code": "raw provider error / token"},
])
def test_invalid_evaluation_states_are_rejected(publication_session, claim_records, changes) -> None:
    db = publication_session
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(update(NewsClaimEvaluation).where(NewsClaimEvaluation.id == claim_records[2].id).values(**changes))


def test_evaluation_lease_retry_completion_and_finalization(publication_session, claim_records) -> None:
    db = publication_session
    evaluation = claim_records[2]
    evaluation.status, evaluation.lease_token = "processing", uuid4()
    evaluation.lease_expires_at, evaluation.started_at, evaluation.attempt_count = NOW + timedelta(minutes=5), NOW, 1
    db.flush()
    evaluation.status, evaluation.lease_token, evaluation.lease_expires_at = "retry_wait", None, None
    evaluation.error_code, evaluation.next_attempt_at = "provider_timeout", NOW + timedelta(minutes=1)
    db.flush()
    complete_audit(db, evaluation)
    for statement in (update(NewsClaimEvaluation).where(NewsClaimEvaluation.id == evaluation.id).values(result={"replaced": True}),
                      delete(NewsClaimEvaluation).where(NewsClaimEvaluation.id == evaluation.id)):
        with pytest.raises(IntegrityError, match="immutable"), db.begin_nested():
            db.execute(statement)


def test_failed_evaluation_is_also_finalized(publication_session, claim_records) -> None:
    db = publication_session
    evaluation = claim_records[2]
    evaluation.status, evaluation.completed_at, evaluation.error_code = "failed", NOW, "audit_exhausted"
    db.flush()
    for statement in (update(NewsClaimEvaluation).where(NewsClaimEvaluation.id == evaluation.id).values(status="pending"),
                      delete(NewsClaimEvaluation).where(NewsClaimEvaluation.id == evaluation.id)):
        with pytest.raises(IntegrityError, match="immutable"), db.begin_nested():
            db.execute(statement)


@pytest.mark.parametrize("changes", [
    {"revision": 0}, {"actor_kind": "staff"}, {"actor_kind": "automatic", "actor_user_id": 999},
    {"actor_kind": "automatic", "operation": "evaluate"}, {"public_state": "active_alert", "expires_at": None},
    {"operation": "correct", "public_state": "active_alert", "observed_at": None},
    {"operation": "correct", "public_state": "active_zone", "expires_at": NOW},
    {"operation": "clear", "public_state": "active_zone"}, {"operation": "reject", "public_state": "active_alert"},
    {"snapshot": []}, {"snapshot": {"text": "x" * 65536}}, {"reason_code": "private raw error / details"},
])
def test_invalid_decisions_are_rejected(publication_session, claim_records, changes) -> None:
    db = publication_session
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(decision(claim_records[0], **changes))
        db.flush()


def test_automatic_decision_requires_completed_evaluation(publication_session, claim_records) -> None:
    db = publication_session
    case, _, evaluation = claim_records
    fields = dict(actor_kind="automatic", operation="evaluate", public_state="active_alert", evaluation_id=evaluation.id)
    with pytest.raises(IntegrityError, match="completed audit"), db.begin_nested():
        db.add(decision(case, **fields))
        db.flush()
    complete_audit(db, evaluation)
    saved = decision(case, **fields)
    db.add(saved)
    db.flush()
    assert saved.actor_user_id is None and saved.evaluation.source.case.id == case.id


def test_decision_revision_request_uniqueness_and_history(publication_session, claim_records) -> None:
    db = publication_session
    saved = decision(claim_records[0])
    db.add(saved)
    db.flush()
    other_case = NewsClaimCase()
    db.add(other_case)
    db.flush()
    for row in (decision(claim_records[0]), decision(other_case, request_id=saved.request_id)):
        with pytest.raises(IntegrityError), db.begin_nested():
            db.add(row)
            db.flush()
    for statement in (update(NewsClaimDecision).where(NewsClaimDecision.id == saved.id).values(reason_code="changed"),
                      delete(NewsClaimDecision).where(NewsClaimDecision.id == saved.id)):
        with pytest.raises(IntegrityError, match="immutable"), db.begin_nested():
            db.execute(statement)


def test_source_identity_hash_immutability_and_parent_preservation(publication_session, claim_records) -> None:
    db = publication_session
    case, source, _ = claim_records
    for fields in ({}, {"claim_ordinal": -1}, {"claim_ordinal": 1, "claim_sha256": "C" * 64}):
        with pytest.raises(IntegrityError), db.begin_nested():
            db.add(NewsClaimSource(**(dict(case_id=case.id, extraction_run_id=source.extraction_run_id,
                                         claim_ordinal=0, claim_sha256="c" * 64) | fields)))
            db.flush()
    for statement in (update(NewsClaimSource).where(NewsClaimSource.id == source.id).values(claim_ordinal=2),
                      delete(NewsClaimSource).where(NewsClaimSource.id == source.id)):
        with pytest.raises(IntegrityError, match="immutable"), db.begin_nested():
            db.execute(statement)
    for statement in (delete(NewsClaimCase).where(NewsClaimCase.id == case.id),
                      delete(NewsExtractionRun).where(NewsExtractionRun.id == source.extraction_run_id)):
        with pytest.raises(IntegrityError), db.begin_nested():
            db.execute(statement)


def test_zone_creation_owner_multiple_support_and_alert_isolation(publication_session, claim_records) -> None:
    db = publication_session
    case = claim_records[0]
    zone_id = db.scalar(select(FloodAvoidanceZone.id))
    active = decision(case, operation="correct", public_state="active_zone")
    later = decision(case, revision=2, operation="correct", public_state="active_zone")
    alert = decision(case, revision=3, operation="correct", public_state="active_alert")
    db.add_all([active, later, alert])
    db.flush()
    original = NewsClaimZoneLink(decision_id=active.id, zone_id=zone_id, relation="created")
    db.add(original)
    db.flush()
    for row in (NewsClaimZoneLink(decision_id=later.id, zone_id=zone_id, relation="created"),
                NewsClaimZoneLink(decision_id=active.id, zone_id=zone_id, relation="supported"),
                NewsClaimZoneLink(decision_id=alert.id, zone_id=zone_id, relation="supported")):
        with pytest.raises(IntegrityError), db.begin_nested():
            db.add(row)
            db.flush()
    db.add(NewsClaimZoneLink(decision_id=later.id, zone_id=zone_id, relation="supported"))
    db.flush()
    assert db.scalar(select(func.count()).select_from(NewsClaimZoneLink)) == 2
    for statement in (update(NewsClaimZoneLink).where(NewsClaimZoneLink.id == original.id).values(relation="supported"),
                      delete(NewsClaimZoneLink).where(NewsClaimZoneLink.id == original.id),
                      delete(FloodAvoidanceZone).where(FloodAvoidanceZone.id == zone_id)):
        with pytest.raises(IntegrityError), db.begin_nested():
            db.execute(statement)


@pytest.mark.parametrize("table", sorted(TABLES - {"news_claim_cases"}))
def test_history_cannot_be_truncated(publication_session, table) -> None:
    with pytest.raises(IntegrityError, match="immutable"), publication_session.begin_nested():
        publication_session.execute(text(f"TRUNCATE {table} CASCADE"))


def test_staff_actor_and_external_clearance_evidence(publication_session, claim_records) -> None:
    db = publication_session
    role = Role(name="publication-test-admin")
    db.add(role)
    db.flush()
    actor = User(username="publication-test", email="publication-test@example.org", hashed_password="not-a-live-password", role_id=role.id)
    clearance_case = NewsClaimCase()
    db.add_all([actor, clearance_case])
    db.flush()
    clearance_source = NewsClaimSource(case_id=clearance_case.id, extraction_run_id=claim_records[1].extraction_run_id,
                                       claim_ordinal=1, claim_sha256="e" * 64)
    db.add(clearance_source)
    db.flush()
    evaluation = NewsClaimEvaluation(claim_source_id=clearance_source.id, policy_fingerprint="f" * 64,
                                     status="completed", completed_at=NOW, result={"status": "subsided"})
    db.add(evaluation)
    db.flush()
    cleared = decision(claim_records[0], actor_kind="staff", actor_user_id=actor.id, operation="clear",
                       public_state="withdrawn", evaluation_id=evaluation.id, reason_code="matched_clearance")
    db.add(cleared)
    db.flush()
    assert cleared.evaluation.source.case_id != cleared.case_id
    assert cleared.actor.username == "publication-test"
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(delete(User).where(User.id == actor.id))
