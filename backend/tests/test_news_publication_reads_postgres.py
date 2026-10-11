"""Native read-time expiry, privacy, permissions and per-claim queue behavior."""
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, event, inspect, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.api import deps
from app.core.database import get_db
from app.crud.news_evaluation import bind_completed_run
from app.crud.news_publication import append_decision, reserve_decision_id
from app.crud.news_publication_read import read_latest_decision, source_input_for_decision
from app.main import app
from app.models.news_publication import NewsClaimCase, NewsClaimSource
from app.schemas.news_publication import NewsDecisionSnapshot
from app.services import news_publication_read_service as reads
from app.services.spatial_review_service import browse_spatial_review
from test_news_evaluation_postgres import NOW, POLICY, SOURCES, seed
from test_news_publication_api import alert


@pytest.fixture(scope="module")
def read_factory():
    url = os.environ.get("LANES_NEWS_EVALUATION_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Disposable loopback publication database required")
    parsed = make_url(url)
    assert parsed.host in ("localhost", "127.0.0.1", "::1")
    assert (parsed.database or "").startswith("lanes_evaluation_test_")
    from app.core.config import settings
    patch = pytest.MonkeyPatch()
    patch.setattr(settings, "DATABASE_URL", url)
    engine = create_engine(url)
    # The isolated runner may have upgraded this same disposable DB for the
    # publication service tests; never drop or truncate existing test history.
    if not inspect(engine).get_table_names():
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
        command.upgrade(config, "head")
    try:
        yield sessionmaker(bind=engine)
    finally:
        engine.dispose()
        patch.undo()


def source_case(factory, **claim_changes):
    run_id, _ = seed(factory, **claim_changes)
    with factory() as db, db.begin():
        bind_completed_run(db, run_id, POLICY.fingerprint, NOW)
        source = db.scalar(select(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run_id))
        return source.case_id, source.id, run_id


def decision(factory, case_id, source_id, *, state="active_alert", operation="evaluate", when=NOW,
             observed=NOW, expires=None, private="Internal sensitive notes", deferred=None, source_url=None):
    with factory() as db, db.begin():
        case = db.get(NewsClaimCase, case_id)
        identity = reserve_decision_id(db)
        frozen = source_input_for_decision(db, SimpleNamespace(snapshot={"claim_source_id": source_id}))
        public = alert().model_copy(update={"case_id":case_id,"decision_id":identity,"revision":case.revision+1,
            "source_url": source_url or frozen["canonical_url"],
            "observed_at":observed,"expires_at":expires or NOW+timedelta(hours=2),"updated_at":when,
            "status":"Cleared" if operation == "clear" else "Active",
            "cleared_at":observed if operation == "clear" else None})
        snapshot = NewsDecisionSnapshot(request_sha256="1"*64,policy_fingerprint=POLICY.fingerprint,
            claim_source_id=source_id,input_sha256="2"*64,claim_sha256="3"*64,incident_identity="4"*64,
            article_id=1,public=public if state != "unpublished" else None,private_reason=private,deferred_until=deferred)
        row = append_decision(db,case,request_id=uuid4(),decision_id=identity,actor_kind="maintenance",actor_user_id=None,
            operation=operation,public_state=state,review_state="resolved" if state != "unpublished" else "needs_review",
            reason_code="read_fixture",snapshot=snapshot,observed_at=observed,
            expires_at=expires or NOW+timedelta(hours=2),now=when)
        return row.id


def test_public_read_expires_without_worker_and_retention_anchors_to_observation(read_factory):
    case_id,source_id,_=source_case(read_factory)
    decision(read_factory,case_id,source_id)
    with read_factory() as db:
        active=reads.read_public_news_alert(db,case_id,now=NOW+timedelta(hours=1),sources=SOURCES)
        expired=reads.read_public_news_alert(db,case_id,now=NOW+timedelta(hours=2),sources=SOURCES)
        assert active.status == "Active" and expired.status == "Unconfirmed"
        assert expired.cleared_at is None and expired.current_status_unknown
        page=reads.browse_public_news_alerts(db,page=1,page_size=100,now=NOW+timedelta(hours=26),sources=SOURCES)
        assert case_id not in [item.case_id for item in page.items]
        archive=reads.read_public_news_alert(db,case_id,now=NOW+timedelta(hours=40),sources=SOURCES)
        assert archive.status == "Unconfirmed"
        assert read_latest_decision(db,case_id).revision == 1


def test_latest_withdrawal_hides_old_active_and_source_disable_hides_public(read_factory):
    case_id,source_id,_=source_case(read_factory)
    decision(read_factory,case_id,source_id)
    decision(read_factory,case_id,source_id,state="withdrawn",operation="reject")
    with read_factory() as db:
        assert reads.read_public_news_alert(db,case_id,now=NOW,sources=SOURCES) is None
        assert case_id not in [item.case_id for item in reads.browse_public_news_alerts(db,page=1,page_size=100,now=NOW,sources=SOURCES).items]
        assert reads.browse_public_news_alerts(db,page=1,page_size=100,now=NOW,sources=()).items == []


def test_clearance_current_feed_uses_clearance_clock_and_private_fields_never_project(read_factory):
    case_id,source_id,_=source_case(read_factory)
    cleared=NOW+timedelta(hours=1)
    decision(read_factory,case_id,source_id,state="withdrawn",operation="clear",observed=cleared)
    with read_factory() as db:
        page=reads.browse_public_news_alerts(db,page=1,page_size=100,now=NOW+timedelta(hours=24),sources=SOURCES)
        item=next(row for row in page.items if row.case_id == case_id)
        assert item.status == "Cleared" and item.cleared_at == cleared
        assert "Internal sensitive notes" not in item.model_dump_json()
        assert reads.read_public_news_alert(db,case_id,now=NOW+timedelta(days=3),sources=SOURCES).status == "Cleared"


def test_public_reads_are_bounded_and_create_no_decisions(read_factory):
    statements=[]
    with read_factory() as db:
        connection=db.connection()
        def record(_conn,_cursor,statement,*_):
            statements.append(statement)
        event.listen(connection,"before_cursor_execute",record)
        reads.browse_public_news_alerts(db,page=1,page_size=2,now=NOW,sources=SOURCES)
        event.remove(connection,"before_cursor_execute",record)
    assert any("LIMIT" in sql and "OFFSET" in sql for sql in statements)
    assert not any(sql.lstrip().split()[0].upper() in ("INSERT","UPDATE","DELETE") for sql in statements)


def test_public_link_must_match_immutable_article_url(read_factory):
    case_id, source_id, _ = source_case(read_factory)
    decision(read_factory, case_id, source_id, source_url="https://example.org/different-article")
    with read_factory() as db:
        assert reads.read_public_news_alert(db, case_id, now=NOW, sources=SOURCES) is None
        with pytest.raises(ValueError, match="no longer approved"):
            reads.browse_public_news_alerts(db, page=1, page_size=100, now=NOW, sources=SOURCES)


@pytest.mark.asyncio
async def test_native_jwt_roles_preview_and_committed_retry(read_factory, monkeypatch):
    from jose import jwt
    from app.core.config import settings
    from app.models.role import Role
    from app.models.user import User
    from app.api.v1.endpoints import admin_news_publication
    from app.services import news_publication_service
    case_id, source_id, _ = source_case(read_factory)
    decision(read_factory, case_id, source_id)
    role_headers = {}
    with read_factory() as db, db.begin():
        for permission in ("none", "view", "full"):
            suffix = uuid4().hex
            role = Role(name=f"Publication {permission} {suffix}", permissions={"reports": permission})
            db.add(role)
            db.flush()
            user = User(username=suffix, email=f"{suffix}@example.org", hashed_password="test-only",
                        role_id=role.id, is_active=True)
            db.add(user)
            db.flush()
            token = jwt.encode({"sub": str(user.id), "exp": datetime.now(timezone.utc) + timedelta(minutes=10)},
                               settings.SECRET_KEY, algorithm=settings.ALGORITHM)
            role_headers[permission] = {"Authorization": f"Bearer {token}"}
    def database():
        with read_factory() as db:
            yield db
    old_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = database
    app.dependency_overrides[admin_news_publication.publication_policy] = lambda: POLICY
    monkeypatch.setattr(admin_news_publication, "publication_read_clock", lambda: NOW)
    # Local transaction behavior; no paid external audit or SSE network call.
    monkeypatch.setattr(news_publication_service, "load_news_sources", lambda: SOURCES)
    broadcast = []
    async def sent(message):
        with read_factory() as db:
            assert read_latest_decision(db, case_id).revision == 2
        broadcast.append(message)
    monkeypatch.setattr(admin_news_publication.manager, "broadcast", sent)
    path = f"/api/v1/admin/news/claims/{case_id}"
    payload = dict(request_id=str(uuid4()), expected_revision=1, operation="reject", reason="Staff-only fixture reason")
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            assert (await client.get(path)).status_code == 401
            assert (await client.get(path, headers={"Authorization": "Bearer invalid"})).status_code == 401
            assert (await client.get(path, headers=role_headers["none"])).status_code == 403
            assert (await client.get(path, headers=role_headers["view"])).status_code == 200
            assert (await client.post(path + "/decisions", headers=role_headers["view"], json=payload)).status_code == 403
            preview = await client.post(path + "/decision-preview", headers=role_headers["full"], json=payload)
            assert preview.status_code == 200 and preview.json()["public_state"] == "withdrawn"
            with read_factory() as db:
                assert read_latest_decision(db, case_id).revision == 1
            saved = await client.post(path + "/decisions", headers=role_headers["full"], json=payload)
            assert saved.status_code == 200, saved.text
            assert "Staff-only fixture reason" not in saved.text
            retry = await client.post(path + "/decisions", headers=role_headers["full"], json=payload)
            assert retry.status_code == 200 and retry.json() == saved.json()
            assert len(broadcast) == 2
            history = await client.get(path + "/history", headers=role_headers["view"])
            assert history.status_code == 200
            assert history.json()["items"][0]["private_reason"] == payload["reason"]
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(old_overrides)


def test_resolving_one_claim_keeps_another_claim_in_same_run_reviewable(read_factory,monkeypatch):
    from copy import deepcopy
    from app.models.news import NewsExtractionRun
    from app.services import spatial_review_service
    run_id,_=seed(read_factory)
    with read_factory() as db,db.begin():
        run=db.get(NewsExtractionRun,run_id)
        result=deepcopy(run.result)
        original=result["claims"][0]
        original.update(action_type="flagged_review",action_rationale="Uncertain affected footprint")
        result["claims"]=[original,{**original,"raw_place_name":"Pasig City","canonical_road":None,"place_char_start":6,"place_char_end":16}]
        run.result=result
        db.flush()
        bind_completed_run(db,run_id,POLICY.fingerprint,NOW)
        source=db.scalar(select(NewsClaimSource).where(NewsClaimSource.extraction_run_id==run_id,NewsClaimSource.claim_ordinal==0))
        case_id,source_id=source.case_id,source.id
    decision(read_factory,case_id,source_id)
    monkeypatch.setattr(spatial_review_service,"review_clock",lambda:NOW)
    with read_factory() as db:
        page=browse_spatial_review(db,source="news_claims",page=1,page_size=100)
        keys={row.key for row in page.items}
        assert f"news_claim:{run_id}:0" not in keys
        assert f"news_claim:{run_id}:1" in keys
