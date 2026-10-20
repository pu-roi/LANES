"""Consumer/queue foundation only; fictional native data is not neural inference."""
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
import hashlib
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import event, func, select

from app.api import deps
from app.core.database import get_db
from app.crud.news_evaluation import validate_run
from app.crud.news_processing import claim_due_run, enqueue_article, finish_owned_run
from app.main import app
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.schemas.news_candidate import NewsExtractionRunSummary
from app.schemas.news_ner_result import NewsNerResult, parse_saved_result
from app.services.news_ner.contract import object_sha
from app.services.news_ner.location_pipeline import from_neural_mentions
from app.services.news_ner.projection import project
from app.services.news_processing_identity import NATIVE_MANIFEST_KEYS, native_pipeline_version
from app.services.news_processing_service import process_saved_news
from test_news_processing import article, queue_db, NOW  # Owned SQLite fixtures only.


MANIFEST = {key: "fictional-" + key for key in NATIVE_MANIFEST_KEYS}
PIPELINE = native_pipeline_version(MANIFEST)


def native_fixture(version: NewsArticleVersion) -> dict:
    """Source-authored mentions and unchanged pure rules, never a model prediction."""
    body = version.input_snapshot["article_text"]
    raw = dict(record_id="ner-" + version.input_fingerprint, text=body,
               text_sha256=hashlib.sha256(body.encode("utf-8")).hexdigest(),
               publication=None, mentions=[])
    for label, name in (("BARANGAY", "Maybunga"), ("CITY", "Pasig City")):
        start = body.index(name)
        raw["mentions"].append(dict(id=f"m{len(raw['mentions'])}", start=start, end=start + len(name),
                                    text=name, label=label, provenance_sha256="0" * 64))
    output = from_neural_mentions(raw)
    proposal = output["proposal"]
    return dict(schema_version="lanes-news-ner-result-v1", processing_method="ner_rules_v1",
        article_id=version.article_id, canonical_url=version.input_snapshot["canonical_url"],
        is_metadata_only=False, processed_text_length=len(body), claims=[], errors=[],
        extracted_at=NOW.isoformat().replace("+00:00", "Z"), extractor_version="fictional-schema-fixture",
        source=dict(article_version_id=version.id, input_fingerprint=version.input_fingerprint,
                    canonical_url=version.input_snapshot["canonical_url"], text_field="article_text",
                    text_sha256=raw["text_sha256"], published_at=version.input_snapshot.get("published_at"),
                    publication_timezone_known=True),
        provenance={"fixture": "source_authored_not_inference", "manifest": MANIFEST},
        native=dict(neural_mentions=proposal["neural_mentions"], effective_mentions=proposal["effective_mentions"],
                    proposals=proposal["proposals"], abstentions=proposal["abstentions"], graph=output["graph"],
                    groups=project({**raw, "mentions": proposal["effective_mentions"]}, output["graph"])),
        projection={"version": "ner-claim-projection-v1", "disposition": "native_only",
                    "reason": "fictional_boundary_fixture_not_qualified_projection"},
        measurements={"inference_runs": 0}, limitations=["fictional_fixture_not_operational"])


def seed_native(factory, *, legacy=True) -> tuple[int, int]:
    with factory() as db, db.begin():
        row = article(article_text="  🌧️ " + article().article_text + "  ")
        db.add(row)
        if legacy:
            enqueue_article(db, row)
        run_id = enqueue_article(db, row, mode="ner_rules_v1", pipeline_version=PIPELINE)
        version_id = db.get(NewsExtractionRun, run_id).article_version_id
    return run_id, version_id


@pytest.mark.parametrize("key", sorted(NATIVE_MANIFEST_KEYS))
def test_every_manifest_family_changes_identity(key):
    assert len(PIPELINE) == 71
    assert native_pipeline_version(dict(reversed(list(MANIFEST.items())))) == PIPELINE
    assert native_pipeline_version({**MANIFEST, key: "changed"}) != PIPELINE
    with pytest.raises(ValueError, match="manifest_incomplete"):
        native_pipeline_version({k: v for k, v in MANIFEST.items() if k != key})


@pytest.mark.parametrize("mode,pipeline", [("unknown", "test"), ("ner_rules_v1", None),
    ("ner_rules_v1", "legacy"), ("rules_only", PIPELINE), ("ner_rules_v1", "ner-v1:" + "z" * 64)])
def test_invalid_identity_refuses_before_any_write(queue_db, mode, pipeline):
    with queue_db() as db, db.begin():
        db.add(article())
        with pytest.raises(ValueError):
            enqueue_article(db, db.get(NewsArticle, 1), mode=mode, pipeline_version=pipeline)
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun)) == 0


def test_modes_keep_distinct_inputs_and_idempotent_runs(queue_db):
    run_id, version_id = seed_native(queue_db)
    with queue_db() as db, db.begin():
        row = db.get(NewsArticle, 1)
        # SQLite discards tzinfo; restore the original source clock for this
        # exact-input check. Actual timezone round-trips are covered in PostGIS.
        row.published_at = article().published_at
        assert enqueue_article(db, row, mode="ner_rules_v1", pipeline_version=PIPELINE) == run_id
        assert db.scalar(select(func.count()).select_from(NewsArticleVersion)) == 2
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun)) == 2
        native = claim_due_run(db, NOW, mode="ner_rules_v1", pipeline_version=PIPELINE)
        assert native.run_id == run_id and native.article_version_id == version_id
        assert native.mode == "ner_rules_v1" and native.pipeline_version == PIPELINE
        legacy = claim_due_run(db, NOW)
        assert legacy.run_id != run_id and legacy.mode == "rules_only"
        assert claim_due_run(db, NOW, mode="ner_rules_v1", pipeline_version=PIPELINE) is None


@pytest.mark.parametrize("state", ["pending", "retry_wait", "processing"])
def test_legacy_worker_cannot_claim_native_even_with_colliding_pipeline(queue_db, state):
    run_id, _ = seed_native(queue_db, legacy=False)
    from app.crud.news_processing import current_pipeline_version
    with queue_db() as db, db.begin():
        row = db.get(NewsExtractionRun, run_id)
        row.pipeline_version = current_pipeline_version()  # Deliberate inconsistent stored fixture.
        row.status = state
        if state == "retry_wait":
            row.next_attempt_at = NOW - timedelta(minutes=1)
        if state == "processing":
            from uuid import uuid4
            row.lease_token, row.lease_expires_at = uuid4(), NOW - timedelta(minutes=1)
        db.flush()
        assert claim_due_run(db, NOW) is None
        assert row.status == state and row.attempt_count == 0


def test_native_worker_cannot_claim_legacy_with_colliding_identity(queue_db):
    seed_native(queue_db)
    with queue_db() as db, db.begin():
        rows = db.scalars(select(NewsExtractionRun)).all()
        next(row for row in rows if row.mode == "rules_only").pipeline_version = PIPELINE
        next(row for row in rows if row.mode == "ner_rules_v1").pipeline_version = "ner-v1:" + "f" * 64
        db.flush()
        assert claim_due_run(db, NOW, mode="ner_rules_v1", pipeline_version=PIPELINE) is None


def test_native_completion_rejects_method_or_input_substitution_and_keeps_lease(queue_db):
    run_id, version_id = seed_native(queue_db)
    with queue_db() as db, db.begin():
        claim = claim_due_run(db, NOW, mode="ner_rules_v1", pipeline_version=PIPELINE)
        result = native_fixture(db.get(NewsArticleVersion, version_id))
        with pytest.raises(ValueError, match="version_unsupported"):
            finish_owned_run(db, claim, NOW, result={"claims": []})
        for field, changed in [("input_fingerprint", "f" * 64), ("article_version_id", version_id + 1),
                               ("canonical_url", "https://example.org/other"), ("text_sha256", "f" * 64)]:
            bad = deepcopy(result)
            bad["source"][field] = changed
            with pytest.raises(ValueError, match="input_binding_invalid"):
                finish_owned_run(db, claim, NOW, result=bad)
        assert not finish_owned_run(db, replace(claim, mode="rules_only"), NOW, result={"claims": []})
        assert not finish_owned_run(db, replace(claim, pipeline_version="different"), NOW, result=result)
        assert finish_owned_run(db, claim, NOW, result=result)
    with queue_db() as db:
        assert db.get(NewsExtractionRun, run_id).result == result
        # Storage/inspection compatibility does not authorize the old evaluator.
        with pytest.raises(ValueError, match="extraction_not_completed"):
            validate_run(db.get(NewsExtractionRun, run_id), db.get(NewsArticleVersion, version_id))


@pytest.mark.asyncio
async def test_default_processor_does_not_execute_native_jobs(queue_db):
    native_id, _ = seed_native(queue_db)
    summary = await process_saved_news(queue_db, clock=lambda: NOW)
    assert summary.completed == 1 and len(summary.runs) == 1
    assert summary.runs[0]["run_id"] != native_id
    with queue_db() as db:
        assert db.get(NewsExtractionRun, native_id).status == "pending"


@pytest.mark.parametrize("mode,change", [("rules_only", {}), ("ner_rules_v1", {"schema_version": "future"}),
    ("ner_rules_v1", {"processing_method": "rules_only"}), ("future", {})])
def test_discriminator_mismatch_never_coerces_to_legacy(queue_db, mode, change):
    _, version_id = seed_native(queue_db)
    with queue_db() as db:
        raw = {**native_fixture(db.get(NewsArticleVersion, version_id)), **change}
    with pytest.raises(ValueError):
        parse_saved_result(mode, raw)


@pytest.mark.parametrize("role", ["onset", "observation", "report", "publication", "recession", "clearance", "unspecified"])
def test_inspection_preserves_each_native_time_role_without_absolute_completion(queue_db, role):
    _, version_id = seed_native(queue_db)
    with queue_db() as db:
        raw = native_fixture(db.get(NewsArticleVersion, version_id))
    times = [fact for fact in raw["native"]["graph"]["facts"] if fact["kind"] == "time"]
    assert times
    times[0]["temporal_role"] = role  # Constructed serialization case, not extraction output.
    parsed = parse_saved_result("ner_rules_v1", raw)
    assert parsed.native.graph.facts[[f["id"] for f in raw["native"]["graph"]["facts"]].index(times[0]["id"])].temporal_role == role
    assert parsed.native.graph.absolute_instants == []


def test_unknown_native_fields_and_cross_version_summary_are_visible_errors(queue_db):
    run_id, version_id = seed_native(queue_db)
    with queue_db() as db:
        raw = native_fixture(db.get(NewsArticleVersion, version_id))
        with pytest.raises(ValueError):
            parse_saved_result("ner_rules_v1", {**raw, "future_unhandled_field": "preserve-or-reject"})
        run = db.get(NewsExtractionRun, run_id)
        raw["source"]["article_version_id"] += 1
        run.result = raw
        with pytest.raises(ValueError, match="source_version_mismatch"):
            NewsExtractionRunSummary.model_validate(run)


@pytest.mark.parametrize("field", ["processed_text_length", "mention_offset"])
def test_native_offsets_and_lengths_are_not_coerced_from_strings(queue_db, field):
    _, version_id = seed_native(queue_db)
    with queue_db() as db:
        raw = native_fixture(db.get(NewsArticleVersion, version_id))
    if field == "processed_text_length":
        raw[field] = str(raw[field])
    else:
        raw["native"]["neural_mentions"][0]["start"] = str(raw["native"]["neural_mentions"][0]["start"])
    with pytest.raises(ValueError):
        parse_saved_result("ner_rules_v1", raw)


def test_roundtrip_preserves_unicode_repair_evidence_graph_and_unknown_confidence(queue_db):
    run_id, version_id = seed_native(queue_db)
    with queue_db() as db:
        version = db.get(NewsArticleVersion, version_id)
        raw = native_fixture(version)
        # Inspect a projected shape without calling it a qualified projection.
        from app.schemas.news_ner_result import NerProjectedClaim
        mention = raw["native"]["effective_mentions"][0]
        raw["claims"] = [NerProjectedClaim(raw_place_name=mention["text"], place_char_start=mention["start"],
            place_char_end=mention["end"], evidence_sentence=version.input_snapshot["article_text"],
            evidence_sentence_offset=(0, raw["processed_text_length"]), confidence_score=None).model_dump(mode="json")]
        run = db.get(NewsExtractionRun, run_id)
        run.result = raw
        parsed = NewsExtractionRunSummary.model_validate(run)
        encoded = parsed.model_dump(mode="json", by_alias=True)["result"]
        assert isinstance(parsed.result, NewsNerResult)
        assert encoded == raw and parsed.result.claims[0].confidence_score is None
        assert parsed.result.model_dump(mode="json")["native"] == raw["native"]
        assert object_sha(encoded["native"]) == object_sha(raw["native"])
        assert raw["native"]["neural_mentions"][0]["start"] > 4


@pytest.mark.asyncio
async def test_saved_native_history_is_admin_only_readonly_and_keeps_full_graph(queue_db, monkeypatch):
    run_id, version_id = seed_native(queue_db)
    with queue_db() as db, db.begin():
        claim = claim_due_run(db, NOW, mode="ner_rules_v1", pipeline_version=PIPELINE)
        raw = native_fixture(db.get(NewsArticleVersion, version_id))
        from app.schemas.news_ner_result import NerProjectedClaim
        mention = raw["native"]["effective_mentions"][0]
        raw["claims"] = [NerProjectedClaim(raw_place_name=mention["text"], place_char_start=mention["start"],
            place_char_end=mention["end"], evidence_sentence=claim.input_snapshot["article_text"],
            evidence_sentence_offset=(0, raw["processed_text_length"])).model_dump(mode="json")]
        assert finish_owned_run(db, claim, NOW, result=raw)
    from app.services.news_ner_runtime.supervisor import Session as RuntimeSession
    async def forbidden(*_args, **_kwargs):
        pytest.fail("Saved-read path launched inference")
    monkeypatch.setattr(RuntimeSession, "start", forbidden)
    writes = []
    def record(_c, _u, statement, _p, _x, _m):
        if statement.lstrip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE"}:
            writes.append(statement)
    event.listen(queue_db.kw["bind"], "before_cursor_execute", record)
    def database():
        with queue_db() as db:
            yield db
    app.dependency_overrides[get_db] = database
    paths = ["/api/v1/admin/news/articles/1", "/api/v1/admin/news/candidates/1/processing"]
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            for path in paths:
                assert (await client.get(path)).status_code == 401
            app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Commuter"))
            for path in paths:
                assert (await client.get(path)).status_code == 403
            app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Admin"))
            history = await client.get(paths[0])
            assert history.status_code == 200, history.text[:150]
            native = next(run for run in history.json()["runs"] if run["id"] == run_id)
            assert native["mode"] == "ner_rules_v1" and native["result"] == raw
            runs = await client.get(paths[1])
            assert runs.status_code == 200 and next(r for r in runs.json() if r["id"] == run_id)["result"] == raw
            assert (await client.get("/api/v1/admin/news/results")).json()["total"] == 0
            attention = await client.get("/api/v1/admin/news/collection")
            assert attention.status_code == 200 and attention.json()["total"] == 1
            assert attention.json()["items"][0]["collection_status"] == "needs_checking"
            for suffix in ("", "/placement"):
                response = await client.get(f"/api/v1/admin/news/results/{run_id}/0{suffix}")
                assert response.status_code == 409
                assert response.json() == {"detail": "news_native_result_consumer_not_ready"}
            # Invalid saved versions are a visible bounded error, not dropped native fields.
            with queue_db() as db, db.begin():
                run = db.get(NewsExtractionRun, run_id)
                run.result = {**raw, "schema_version": "future-private-text"}
            writes.clear()
            for path in paths:
                response = await client.get(path)
                assert response.status_code == 409
                assert response.json() == {"detail": "news_saved_result_unsupported_or_invalid"}
            assert not writes
            # A mislabeled native payload must also fail closed in SQL readers.
            with queue_db() as db, db.begin():
                run = db.get(NewsExtractionRun, run_id)
                run.mode, run.result = "rules_only", raw
            writes.clear()
            assert (await client.get("/api/v1/admin/news/results")).json()["total"] == 0
            assert (await client.get(paths[0])).status_code == 409
            assert not writes
    finally:
        event.remove(queue_db.kw["bind"], "before_cursor_execute", record)
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(deps.get_current_user, None)
