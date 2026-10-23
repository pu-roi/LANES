"""E0 source authentication and native capture preparation. Never infer or publish."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_ner_durable.contracts import NativeInput, PublicationEvidence, capture_native_input, sha
from app.services.news_processing_identity import native_pipeline_version

DATASET_ID = "capstone-september-2026-v1"


class PreparationError(ValueError):
    """Bounded operator diagnostic; never contains source text or connection data."""


@dataclass(frozen=True)
class SourceSpec:
    article_id: int
    version_id: int
    fingerprint: str
    body_sha256: str
    url: str
    publisher: str
    published_at: str


SOURCES = (
    SourceSpec(25, 66, "0e1e1ba1f6b90200ac6188e544d62ec0f4c65a56024bee68676f9972cebec940",
        "dc4773d602277a22fb0660705e21eb45f64125f4bd8167cd55ad21ec3350bc0f",
        "https://tribune.net.ph/2026/09/24/minor-flooding-hits-some-metro-areas",
        "daily-tribune", "2026-09-24T20:41:00+00:00"),
    SourceSpec(47, 137, "b7dc414b045b1f203a385867169a74b8af5d18553f86a07b51d1a2921055c131",
        "a7b92b1ec22db882779dcc2d3f0d3dc153d834f325a00432a551d04357b57708",
        "https://www.gmanetwork.com/news/topstories/metro/1001693/list-flooded-roads-in-metro-manila-wednesday-sept-9-2026/story/",
        "feedspot-01", "2026-09-09T01:19:06+00:00"),
)

# These are selection references to old claims, not a neural or geometry oracle.
CANDIDATES = (
    (25, 134, 4, 59, "primary", "active_demo", "Quirino Avenue", "City of Manila"),
    (25, 134, 5, 60, "backup", "active_demo", "Gov. Pascual Avenue", "City of Malabon"),
    (47, 137, 7, 61, "historical", "historical_archive", "NS Amoranto", "Quezon City"),
    (47, 137, 11, 62, "historical", "historical_archive", "Don Jose St", "Quezon City"),
    (47, 137, 12, 63, "historical", "historical_archive", "NS Amoranto", "Quezon City"),
)


def text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise PreparationError(code)


def authenticate_source(row: dict, spec: SourceSpec) -> tuple[dict, str]:
    """Bind to the approved immutable legacy version, including every whitespace byte."""
    _require(row.get("article_id") == spec.article_id and row.get("version_id") == spec.version_id,
             "source_identity_mismatch")
    snapshot = row.get("input_snapshot")
    _require(isinstance(snapshot, dict) and row.get("input_fingerprint") == spec.fingerprint,
             "source_fingerprint_mismatch")
    _require(sha(snapshot) == spec.fingerprint, "source_snapshot_tampered")
    body = snapshot.get("article_text")
    _require(isinstance(body, str) and text_sha(body) == spec.body_sha256, "source_body_mismatch")
    _require(snapshot.get("canonical_url") == spec.url and snapshot.get("publisher") == spec.publisher,
             "source_publisher_mismatch")
    _require(snapshot.get("published_at") == spec.published_at, "source_publication_mismatch")
    return snapshot, body


def bound_publication(snapshot: dict, metadata: list[dict]) -> PublicationEvidence:
    """Accept only feed proof already bound to this exact saved input; never synthesize it."""
    if snapshot.get('capture_schema') == 'lanes-news-ner-input-v1':
        return NativeInput.model_validate(snapshot).publication_evidence
    binding = {key: snapshot[key] for key in ("title", "excerpt", "published_at", "publisher")}
    binding["body_sha256"] = text_sha(snapshot["article_text"])
    values = []
    for entry in metadata:
        if entry.get("source_id") != snapshot["publisher"]:
            continue
        captured = (entry.get("raw_metadata") or {}).get("captured_input", {})
        if captured.get("binding") == binding:
            try:
                values.append(PublicationEvidence.model_validate(captured["publication_evidence"]))
            except (ValueError, KeyError, TypeError) as exc:
                raise PreparationError("bound_publication_invalid") from exc
    known = [v for v in values if v.timezone_known]
    if known:
        # Different RFC/ISO spellings of one instant are accepted by NativeInput.
        for value in known:
            NativeInput.model_validate({**snapshot, "publication_evidence": value})
        return known[0]
    return values[0] if values else PublicationEvidence()


def build_preparation(inventory: dict, assets: dict, *, specs: tuple[SourceSpec, ...] = SOURCES,
                      candidates: tuple = CANDIDATES, retained_text_hashes: set[str] | None = None, dataset_id: str = DATASET_ID) -> dict[str, dict]:
    """Produce deterministic private JSON documents without inference, SQL or file writes."""
    import re
    _require(bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{0,99}", dataset_id)), "historical_dataset_invalid")
    _require(bool(specs), "historical_input_set_invalid")
    _require(inventory.get("read_only") is True, "read_only_inventory_required")
    rows = inventory.get("sources", [])
    _require(len(rows) == len(specs) and len({r["version_id"] for r in rows}) == len(specs),
             "source_set_mismatch")
    _require(set(assets) == {"manifest", "manifest_sha256", "pipeline_version", "preparation_code_sha256"}
             and sha(assets["manifest"]) == assets["manifest_sha256"]
             and native_pipeline_version(assets["manifest"]) == assets["pipeline_version"], "asset_identity_invalid")
    captures, inputs = {}, []
    by_version = {r["version_id"]: r for r in rows}
    bodies = {}
    for spec in specs:
        _require(spec.version_id in by_version, "source_set_mismatch")
        snapshot, body = authenticate_source(by_version[spec.version_id], spec)
        bodies[spec.article_id] = body
        evidence = bound_publication(snapshot, inventory.get("feeds", []))
        article = NewsArticleExtractorInput(article_id=spec.article_id, **snapshot)
        native, fingerprint = capture_native_input(article, publication_evidence=evidence)
        _require(native["article_text"] == body, "native_body_changed")
        request = NativeInput.model_validate(native).runtime_request(fingerprint)
        name = f"native-{spec.article_id}.json"
        captures[name] = {"article_id": spec.article_id, "source_version_id": spec.version_id,
            "source_input_fingerprint": spec.fingerprint, "native_input_fingerprint": fingerprint,
            "input_snapshot": native, "runtime_request": request}
        inputs.append({"article_id": spec.article_id, "source_version_id": spec.version_id,
            "source_input_fingerprint": spec.fingerprint, "source_text_sha256": spec.body_sha256,
            "characters": len(body), "native_capture_file": name,
            "native_input_fingerprint": fingerprint, "publication_evidence": evidence.model_dump(),
            "publication_limit": None if evidence.timezone_known else "original_feed_wording_not_bound_unknown_preserved",
            "retained_exact_text_match": None if retained_text_hashes is None else spec.body_sha256 in retained_text_hashes})
    history = inventory.get("history", [])
    _require(len(history) == len(candidates) and len({r["zone_id"] for r in history}) == len(candidates),
             "history_set_mismatch")
    by_zone = {r["zone_id"]: r for r in history}
    selections = []
    for article_id, run_id, ordinal, zone_id, role, disposition, road, city in candidates:
        _require(zone_id in by_zone, "history_set_mismatch")
        row = by_zone[zone_id]
        claim = row["claim"]
        _require((row["article_id"], row["run_id"], row["claim_ordinal"]) == (article_id, run_id, ordinal)
                 and row["mode"] == "rules_only", "history_source_mismatch")
        _require(row["is_active"] is False and row["event_status"] == "ended"
                 and row["geometry_valid"] is True and row["geometry_srid"] == 4326,
                 "history_state_mismatch")
        _require(claim.get("canonical_road") == road and claim.get("canonical_city") == city,
                 "history_place_mismatch")
        quote = claim.get("evidence_sentence", "")
        start = bodies[article_id].find(quote) if quote else -1
        _require(start >= 0, "legacy_evidence_not_in_saved_body")
        selections.append({"candidate_id": f"article-{article_id}:legacy-run-{run_id}:claim-{ordinal}",
            "article_id": article_id, "legacy_run_id": run_id, "legacy_claim_ordinal": ordinal,
            "existing_event_id": row["event_id"], "existing_zone_id": zone_id,
            "role": role, "intended_disposition": disposition,
            "selection_only_not_activation_authorization": True,
            "neural_source_geometry_eligibility": "not_evaluated",
            "target": {"road": road, "city": city, "section": claim.get("road_segment_raw")},
            "legacy_evidence_reference": {"start": start, "end": start + len(quote), "text_sha256": text_sha(quote)},
            "legacy_claim_sha256": sha(claim), "existing_geometry_sha256": row["geometry_sha256"],
            "legacy_facts_not_new_neural_results": {key: claim.get(key) for key in
                ("depth_raw", "condition", "road_passability", "event_time_resolved")}})
    identity = {"dataset_id": dataset_id, "source_inputs": [i["source_input_fingerprint"] for i in inputs],
                "candidates": [(s["candidate_id"], s["role"], s["intended_disposition"]) for s in selections]}
    session = str(uuid5(NAMESPACE_URL, "lanes:historical-demo:" + sha(identity)))
    manifest = {"schema": "lanes-historical-e0-manifest-v1", "dataset_id": dataset_id,
        "demonstration_session_id": session, "phase": "E0_prepared_not_processed",
        "database_identity_sha256": inventory["database_identity_sha256"], "assets": assets,
        "inputs": inputs, "candidates": selections,
        "policy": {"primary": "Quirino/Guazon", "backup": "Gov. Pascual",
            "backup_requires_explicit_selection_after_primary_qualification": True,
            "visibility_target": ["public_map", "spatial_operations"],
            "display_label": "Historical demonstration — September 2026",
            "reuse_existing_articles_and_history": True, "inference_performed": False,
            "database_writes_performed": False, "activation_performed": False,
            "publication_time_not_observation_time": True}}
    if not any(c['intended_disposition'] == 'active_demo' for c in selections):
        manifest['policy'] = {'archive_only': True, 'visibility_target': ['flood_history'],
            'reuse_existing_articles_and_history': True, 'inference_performed': False,
            'database_writes_performed': False, 'activation_performed': False,
            'publication_time_not_observation_time': True}
    documents = {"inventory.json": inventory, **captures, "manifest.json": manifest}
    documents["receipt.json"] = {"schema": "lanes-historical-e0-receipt-v1",
        "manifest_sha256": sha(manifest), "demonstration_session_id": session,
        "document_sha256": {name: sha(value) for name, value in documents.items()},
        "inputs": len(inputs), "candidates": len(selections), "native_captures": len(captures),
        "neural_eligibility": "pending_E1_E2", "inference_calls": 0, "database_writes": 0}
    return documents


def save_private_package(directory: Path, documents: dict[str, dict]) -> bool:
    """Create once, or verify an exact prior package without overwriting any evidence."""
    _require(all(Path(name).name == name and name not in {".", ".."} for name in documents),
             "package_name_invalid")
    if directory.exists():
        _require(directory.is_dir() and not directory.is_symlink(), "output_not_private_directory")
        _require({p.name for p in directory.iterdir()} == set(documents), "existing_package_incomplete_or_changed")
        for name, value in documents.items():
            path = directory / name
            _require(not path.is_symlink() and json.loads(path.read_text(encoding="utf-8")) == value,
                     "existing_package_changed")
        return False
    directory.mkdir(parents=True, exist_ok=False)
    # Receipt is last: an interruption preserves a visibly incomplete package.
    for name, value in documents.items():
        with (directory / name).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n")
    return True
