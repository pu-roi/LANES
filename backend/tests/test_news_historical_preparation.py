"""E0 uses fictional source bindings; no SQL connection, model or publisher access."""
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace

import pytest
from sqlalchemy.engine import Engine

from app.crud.news_historical_preparation import read_preparation_inventory
from app.services.news_historical_preparation import (SourceSpec, PreparationError, authenticate_source,
    build_preparation, save_private_package, text_sha)
from app.services.news_ner_durable.contracts import NativeInput, sha
from app.services.news_processing_identity import native_pipeline_version


@pytest.fixture(autouse=True)
def no_external_execution(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("E0 software tests attempted external SQL or neural execution")
    monkeypatch.setattr(Engine, "connect", forbidden)
    from app.services.news_ner_runtime.supervisor import Session
    monkeypatch.setattr(Session, "start", forbidden)


@pytest.fixture
def preparation():
    body = "\n  On September 9, 2026, fictional Straße Avenue was flooded 8 inches.\r\n"
    sources, specs, history, candidates = [], [], [], []
    for index in range(2):
        article_id, version_id, zone_id = 101 + index, 201 + index, 301 + index
        snapshot = {"title": "Fictional flood report", "excerpt": "Original excerpt",
            "publisher": "fictional-source", "canonical_url": f"https://example.org/{index}",
            "published_at": "2026-09-09T01:00:00+00:00", "article_text": body}
        specs.append(SourceSpec(article_id, version_id, sha(snapshot), text_sha(body), snapshot["canonical_url"],
            snapshot["publisher"], snapshot["published_at"]))
        sources.append({"article_id": article_id, "version_id": version_id,
                        "input_fingerprint": sha(snapshot), "input_snapshot": snapshot})
        claim = {"canonical_road": "Straße Avenue", "canonical_city": "Fictional City",
                 "evidence_sentence": body.strip(), "condition": "active", "depth_raw": "8 inches",
                 "event_time_resolved": "2026-09-09T08:55:00+08:00"}
        history.append({"article_id": article_id, "run_id": 401 + index, "claim_ordinal": 0,
            "zone_id": zone_id, "event_id": 501 + index, "mode": "rules_only", "is_active": False,
            "event_status": "ended", "geometry_valid": True, "geometry_srid": 4326,
            "geometry_sha256": "5" * 64, "claim": claim})
        candidates.append((article_id, 401 + index, 0, zone_id,
            "primary" if index == 0 else "historical", "active_demo" if index == 0 else "historical_archive",
            "Straße Avenue", "Fictional City"))
    manifest = {key: {"version": "fictional"} for key in
        ("model", "tokenizer", "runtime", "location_rules", "context_rules", "projection", "source_check", "geography")}
    assets = {"manifest": manifest, "manifest_sha256": sha(manifest),
              "pipeline_version": native_pipeline_version(manifest), "preparation_code_sha256": "4" * 64}
    inventory = {"read_only": True, "database_identity_sha256": "3" * 64,
                 "sources": sources, "feeds": [], "history": history}
    return inventory, assets, tuple(specs), tuple(candidates)


def build(values, **kwargs):
    inventory, assets, specs, candidates = values
    return build_preparation(inventory, assets, specs=specs, candidates=candidates, **kwargs)


def test_exact_unicode_whitespace_and_originals_preserved(preparation):
    original = deepcopy(preparation)
    documents = build(preparation)
    for spec in preparation[2]:
        capture = documents[f"native-{spec.article_id}.json"]
        native = NativeInput.model_validate_json(json.dumps(capture["input_snapshot"]), strict=True)
        assert native.article_text == preparation[0]["sources"][0]["input_snapshot"]["article_text"]
        assert capture["runtime_request"]["text_sha256"] == spec.body_sha256
        assert sha(capture["input_snapshot"]) == capture["native_input_fingerprint"]
        assert capture["source_input_fingerprint"] != capture["native_input_fingerprint"]
    assert preparation == original


def test_unknown_publication_cannot_be_promoted_from_saved_timestamp(preparation):
    preparation[0]["feeds"] = [{"article_id": 101, "source_id": "fictional-source",
                               "raw_metadata": {"published_at": "2026-09-09T01:00:00+00:00"}}]
    documents = build(preparation)
    assert documents["native-101.json"]["runtime_request"]["publication"] is None
    assert documents["manifest.json"]["inputs"][0]["publication_evidence"] == {
        "raw": None, "timezone_known": False, "basis": "legacy_unknown"}


def test_exact_bound_feed_proof_is_retained(preparation):
    snapshot = preparation[0]["sources"][0]["input_snapshot"]
    binding = {key: snapshot[key] for key in ("title", "excerpt", "published_at", "publisher")}
    binding["body_sha256"] = text_sha(snapshot["article_text"])
    preparation[0]["feeds"] = [{"source_id": "fictional-source", "raw_metadata": {"captured_input": {
        "binding": binding, "publication_evidence": {"basis": "publisher_feed",
        "raw": "Wed, 09 Sep 2026 09:00:00 +0800", "timezone_known": True}}}}]
    publication = build(preparation)["native-101.json"]["runtime_request"]["publication"]
    assert publication == {"value": "2026-09-09T01:00:00+00:00", "basis": "publisher_feed"}


def test_body_hash_is_independently_pinned_even_if_snapshot_hash_is_replaced(preparation):
    inventory, _, specs, _ = preparation
    row = deepcopy(inventory["sources"][0])
    row["input_snapshot"]["article_text"] += " "
    row["input_fingerprint"] = sha(row["input_snapshot"])
    with pytest.raises(PreparationError, match="source_body_mismatch"):
        authenticate_source(row, replace(specs[0], fingerprint=row["input_fingerprint"]))


@pytest.mark.parametrize("field,value", [("article_id", 999), ("version_id", 999),
                                         ("input_fingerprint", "0" * 64)])
def test_source_identity_tampering_is_rejected(preparation, field, value):
    preparation[0]["sources"][0][field] = value
    with pytest.raises(PreparationError):
        build(preparation)


def test_snapshot_mutation_without_pin_change_is_rejected(preparation):
    preparation[0]["sources"][0]["input_snapshot"]["excerpt"] = "Changed"
    with pytest.raises(PreparationError, match="source_snapshot_tampered"):
        build(preparation)


@pytest.mark.parametrize("field,value", [("is_active", True), ("event_status", "active"),
    ("geometry_valid", False), ("geometry_srid", 3857), ("mode", "ner_rules_v1"), ("run_id", 999)])
def test_wrong_or_changed_history_cannot_be_silently_reused(preparation, field, value):
    preparation[0]["history"][0][field] = value
    with pytest.raises(PreparationError):
        build(preparation)


def test_missing_or_duplicate_source_and_history_sets_rejected(preparation):
    for key in ("sources", "history"):
        changed = deepcopy(preparation)
        changed[0][key][1] = changed[0][key][0]
        with pytest.raises(PreparationError):
            build(changed)


def test_legacy_evidence_not_a_substring_is_rejected(preparation):
    preparation[0]["history"][0]["claim"]["evidence_sentence"] = "Invented source claim"
    with pytest.raises(PreparationError, match="legacy_evidence_not_in_saved_body"):
        build(preparation)


def test_session_and_documents_are_stable_with_both_output_intents(preparation):
    first = build(preparation)
    assert first == build(preparation)
    manifest = first["manifest.json"]
    assert {s["intended_disposition"] for s in manifest["candidates"]} == {"active_demo", "historical_archive"}
    assert all(s["neural_source_geometry_eligibility"] == "not_evaluated" for s in manifest["candidates"])
    assert first["receipt.json"]["inference_calls"] == first["receipt.json"]["database_writes"] == 0
    assert manifest["policy"]["visibility_target"] == ["public_map", "spatial_operations"]


def test_json_round_trip_and_retained_match_do_not_change_capture(preparation):
    documents = build(preparation, retained_text_hashes={preparation[2][0].body_sha256})
    assert json.loads(json.dumps(documents, ensure_ascii=False)) == documents
    assert all(row["retained_exact_text_match"] for row in documents["manifest.json"]["inputs"])
    assert documents["native-101.json"] == build(preparation)["native-101.json"]


@pytest.mark.parametrize("field,value", [("pipeline_version", "ner-v1:" + "0" * 64),
                                         ("manifest_sha256", "0" * 64)])
def test_asset_identity_mismatch_is_rejected(preparation, field, value):
    preparation[1][field] = value
    with pytest.raises(PreparationError, match="asset_identity_invalid"):
        build(preparation)


def test_read_only_inventory_required(preparation):
    preparation[0]["read_only"] = False
    with pytest.raises(PreparationError, match="read_only_inventory_required"):
        build(preparation)


def test_package_rerun_verifies_without_overwriting_and_tamper_is_refused(preparation, tmp_path):
    documents = build(preparation)
    output = tmp_path / "private"
    assert save_private_package(output, documents) is True
    before = {p.name: p.stat().st_mtime_ns for p in output.iterdir()}
    assert save_private_package(output, documents) is False
    assert before == {p.name: p.stat().st_mtime_ns for p in output.iterdir()}
    (output / "native-101.json").write_text("{}", encoding="utf-8")
    with pytest.raises(PreparationError, match="existing_package_changed"):
        save_private_package(output, documents)
    assert (output / "native-101.json").read_text() == "{}"


def test_partial_package_is_preserved_and_path_escape_refused(preparation, tmp_path):
    output = tmp_path / "partial"
    output.mkdir()
    (output / "partial.txt").write_text("Retain failure")
    with pytest.raises(PreparationError, match="existing_package_incomplete_or_changed"):
        save_private_package(output, build(preparation))
    with pytest.raises(PreparationError, match="package_name_invalid"):
        save_private_package(tmp_path / "escape", {"../escape.json": {}})


def test_wrong_database_refused_before_connecting():
    engine = SimpleNamespace(url=SimpleNamespace(database="unconfirmed"))
    with pytest.raises(PreparationError, match="database_confirmation_mismatch"):
        read_preparation_inventory(engine, "confirmed")


@pytest.mark.parametrize("reported_database,read_only", [("lanes", "on"), ("other", "on"), ("lanes", "off")])
def test_inventory_transaction_enforces_read_only_before_reading(reported_database, read_only):
    statements = []

    class Connection:
        rolled_back = False

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def execution_options(self, **kwargs):
            assert kwargs == {"isolation_level": "REPEATABLE READ"}
            return self

        def execute(self, statement, _parameters=None):
            sql = str(statement).strip()
            statements.append(sql)
            value = reported_database if sql == "SELECT current_database()" else read_only
            return SimpleNamespace(scalar_one=lambda: value, mappings=lambda: [])

        def rollback(self):
            self.rolled_back = True

    connection = Connection()
    engine = SimpleNamespace(url=SimpleNamespace(database="lanes", drivername="postgresql",
        host="example.invalid", port=5432), connect=lambda: connection)
    if reported_database == "lanes" and read_only == "on":
        inventory = read_preparation_inventory(engine, "lanes")
        assert inventory["read_only"] is True and connection.rolled_back
        assert inventory["sources"] == inventory["history"] == []
    else:
        with pytest.raises(PreparationError, match="read_only_database_mismatch"):
            read_preparation_inventory(engine, "lanes")
        assert not any("FROM news_article_versions" in sql for sql in statements)
    assert statements[0] == "SET TRANSACTION READ ONLY"
    assert all(sql.startswith(("SET", "SELECT", "SHOW")) for sql in statements)
