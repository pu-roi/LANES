"""Offline preparation integrity; constructed fixtures are never training truth."""
from __future__ import annotations

import json
import hashlib
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError
from spacy.tokens import DocBin

from training.flood_ner.annotation.schema import AnnotationRecord, SourceCapture, text_hash
from training.flood_ner.annotation.validation import validate_corpus, validate_record
from training.flood_ner.cli import main
from training.flood_ner.export import corpus_tokenizer, export_corpus
from training.flood_ner.sources import capture_source, inventory_sources, read_jsonl, write_jsonl


@pytest.fixture(scope="module")
def nlp():
    return corpus_tokenizer()


def record(text: str = "As of 2 PM, Main Road and Side Road had 10 inches of flooding.",
           record_id: str = "one", split: str = "train") -> AnnotationRecord:
    def span(value: str) -> dict:
        start = text.index(value)
        return {"start": start, "end": start + len(value), "text": value}
    entities = [{"id": "road1", "label": "ROAD", **span("Main Road")},
                {"id": "road2", "label": "ROAD", **span("Side Road")},
                {"id": "clock", "label": "TIME", **span(re.search(r"\d+ PM", text).group())},
                {"id": "depth", "label": "DEPTH", **span("10 inches")}]
    evidence = [{"start": 0, "end": len(text), "text": text}]
    return AnnotationRecord.model_validate({
        "record_id": record_id, "source": {
            "source_id": record_id, "url": f"https://example.org/{record_id}", "publisher": "Constructed test",
            "text": text, "text_sha256": text_hash(text), "capture_version": text_hash(text),
            "article_group": record_id, "event_group": record_id, "syndication_group": record_id,
            "origin": "constructed_fixture", "reuse_status": "allowed", "reuse_terms": "original test fixture",
            "admission_status": "training_admitted", "extraction_method": "constructed",
        }, "passage_start": 0, "passage_end": len(text), "text": text, "text_sha256": text_hash(text),
        "entities": entities, "facts": [
            {"id": "time-fact", "kind": "time", "entity_ids": ["clock"], "temporal_role": "observation", "evidence": evidence},
            {"id": "depth-fact", "kind": "depth", "entity_ids": ["depth"], "depth_scope": "point", "evidence": evidence},
        ], "relations": [
            {"id": "time-shared", "fact_id": "time-fact", "target_entity_ids": ["road1", "road2"], "scope": "shared", "evidence": evidence},
            {"id": "depth-shared", "fact_id": "depth-fact", "target_entity_ids": ["road1", "road2"], "scope": "shared", "evidence": evidence},
        ], "annotation_revision": "test-v1", "quality": "constructed", "reviewer": "test-author",
        "review_status": "accepted", "complete": True, "split": split,
    })


def test_shared_facts_preserve_single_occurrence_and_unknown_values(nlp):
    item = record()
    assert validate_record(item, nlp) == []
    assert len(item.facts) == 2 and len(item.entities) == 4
    assert item.facts[0].value is None  # No invented calendar date.
    assert item.entities[0].identity is None  # No invented map identity.


def test_context_jsonl_round_trips_multiline_unicode_and_unreviewed_cues(tmp_path):
    from training.flood_ner.context import write_context_jsonl

    text = 'As of 2 PM, Main Road and Side Road had 10 inches of flooding.\r\nParañaque — hindi passable.\n"Humupa" remains a cue.'
    items = [record(text, record_id='first'), record(text, record_id='second')]
    path = tmp_path / 'context.jsonl'
    views = write_context_jsonl(path, items)
    original = path.read_bytes()
    restored = [json.loads(line) for line in original.decode('utf-8').splitlines()]
    assert len(restored) == len(items) == 2 and restored == views
    for view, item in zip(restored, items):
        assert view['text'] == item.text and view['text_sha256'] == text_hash(item.text)
        assert view['source_sha256'] == item.source.text_sha256 and view['review_status'] == 'draft'
        assert 'facts' not in view and 'relations' not in view
        for cue in view['candidate_cues']:
            assert item.text[cue['start']:cue['end']] == cue['text']
            assert text_hash(cue['text']) == cue['sha256'] and cue['review_status'] == 'unreviewed'
    second = tmp_path / 'second.jsonl'
    write_context_jsonl(second, items)
    assert second.read_bytes() == original
    with pytest.raises(ValueError, match='preserve earlier artifacts'):
        write_context_jsonl(path, [])
    assert path.read_bytes() == original


@pytest.mark.parametrize('text,name', [('CAUAYAN CITY- Floods','CAUAYAN CITY'),
                                    ('along -Bonifacio Drive','Bonifacio Drive'),
                                    ('V. Mapa- RMB','V. Mapa'), ('Lot 25-A.','Lot 25-A')])
def test_address_v2_delimiters_align_without_changing_source_or_internal_codes(nlp,text,name):
    doc=nlp.make_doc(text)
    start=text.index(name)
    assert doc.text==text
    assert doc.char_span(start,start+len(name),alignment_mode='strict').text==name
    if '25-A' in text: assert any(t.text=='25-A' for t in doc)


def location_record() -> AnnotationRecord:
    data=record().model_dump()
    data.update(annotation_profile='location-only-v1',
                entities=[e for e in data['entities'] if e['label']=='ROAD'],facts=[],relations=[])
    return AnnotationRecord.model_validate(data)


def test_location_profile_is_explicit_and_rich_records_remain_compatible(nlp):
    assert record().annotation_profile=='context-rich-v1'
    assert validate_record(location_record(),nlp)==[]
    data=record().model_dump();data['annotation_profile']='location-only-v1'
    assert any('place entities only' in error for error in validate_record(AnnotationRecord.model_validate(data),nlp))


def test_location_profile_docbin_contains_places_and_manifest_scope(tmp_path,nlp):
    item=location_record()
    manifest=export_corpus([item],tmp_path/'out',allow_constructed=True,annotation_profile='location-only-v1')
    assert manifest['annotation_profile']=='location-only-v1'
    from training.flood_ner.sources import json_bytes
    assert manifest['schema_sha256']==hashlib.sha256(json_bytes(AnnotationRecord.model_json_schema())).hexdigest()
    assert manifest['labels']==['ROAD','LANDMARK','LOCAL_AREA','BARANGAY','CITY','PROVINCE']
    docs=list(DocBin().from_disk(tmp_path/'out/train.spacy').get_docs(nlp.vocab))
    assert [[(e.text,e.label_) for e in d.ents] for d in docs]==[[('Main Road','ROAD'),('Side Road','ROAD')]]
    assert docs[0].text==item.text and manifest['constructed_test_only']


def test_export_refuses_implicit_or_mixed_annotation_profiles(tmp_path):
    with pytest.raises(ValueError,match='explicit export profile'):
        export_corpus([location_record()],tmp_path/'implicit',allow_constructed=True)
    with pytest.raises(ValueError,match='explicit export profile'):
        export_corpus([record()],tmp_path/'wrong',allow_constructed=True,annotation_profile='location-only-v1')
    with pytest.raises(ValueError,match='unsupported annotation profile'):
        export_corpus([record()],tmp_path/'unknown',allow_constructed=True,annotation_profile='invalid')
    assert not any(tmp_path.iterdir())


def test_location_profile_does_not_admit_research_sources(tmp_path):
    item=location_record()
    item.source.admission_status='research_only'
    with pytest.raises(ValueError,match='research-only'):
        export_corpus([item],tmp_path/'out',allow_constructed=True,annotation_profile='location-only-v1')
    assert not (tmp_path/'out').exists()


@pytest.mark.parametrize("mutation,expected", [
    (lambda d: d.update(text_sha256="0" * 64), "passage text_sha256"),
    (lambda d: d.update(passage_start=1), "passage offsets"),
    (lambda d: d["entities"][0].update(text="Wrong Road"), "source-exact"),
    (lambda d: d["entities"][0].update(start=d["entities"][0]["start"] + 1, text="ain Road"), "token aligned"),
    (lambda d: d["entities"].append({**d["entities"][0], "id": "duplicate-span"}), "overlapping"),
    (lambda d: d["relations"][0].update(target_entity_ids=["clock"]), "place targets"),
    (lambda d: d["relations"][0].update(fact_id="missing"), "missing fact"),
    (lambda d: d["facts"][0].update(temporal_role=None), "time role"),
    (lambda d: d["facts"][1].update(depth_scope=None), "depth scope"),
    (lambda d: d.update(reviewer=None), "reviewer"),
    (lambda d: d.update(complete=False), "complete"),
    (lambda d: d["entities"][0].update(identity={"state": "unresolved", "psgc_code": "1380600000"}), "uncertain identity"),
    (lambda d: d["relations"][0].update(overrides_relation_id="time-shared"), "invalid local override"),
])
def test_invalid_annotations_are_actionable(nlp, mutation, expected):
    data = record().model_dump()
    mutation(data)
    assert any(expected in message for message in validate_record(AnnotationRecord.model_validate(data), nlp))


def test_source_integrity_and_timezone_are_required():
    data = record().source.model_dump()
    with pytest.raises(ValidationError, match="text_sha256 mismatch"):
        SourceCapture.model_validate({**data, "text_sha256": "0" * 64})
    with pytest.raises(ValidationError, match="timezone"):
        SourceCapture.model_validate({**data, "captured_at": datetime(2026, 10, 14)})
    with pytest.raises(ValidationError, match="allowed reuse"):
        SourceCapture.model_validate({**data, "reuse_status": "unknown"})


@pytest.mark.parametrize("group", ["article_group", "event_group", "syndication_group"])
def test_related_groups_cannot_cross_splits(nlp, group):
    first = record()
    second = record("As of 3 PM, Main Road and Side Road had 10 inches of flooding.", "two", "test")
    setattr(second.source, group, getattr(first.source, group))
    assert any("split leakage" in e for e in validate_corpus([first, second], nlp))


def test_copied_text_cannot_cross_splits_even_with_different_groups(nlp):
    assert any("source_hash" in e for e in validate_corpus([record(), record(record_id="two", split="test")], nlp))


@pytest.mark.parametrize("second_url", [
    "https://gmanetwork.com/news/topstories/nation/123456/changed-slug/story/amp/?utm_source=feed",
    "http://www.gmanetwork.com/news/balitambayan/balita/123456/translated/story/",
])
def test_same_article_url_aliases_cannot_cross_splits(nlp, second_url):
    first=record()
    second=record("As of 3 PM, Main Road and Side Road had 10 inches of flooding.","two","test")
    first.source.url="https://www.gmanetwork.com/news/topstories/metro/123456/original/story/"
    second.source.url=second_url
    assert any("split leakage: url" in e for e in validate_corpus([first,second],nlp))


@pytest.mark.parametrize("field,value", [
    ("article_group","review-needed:article"),
    ("event_group","provisional:2024-storm"),
    ("syndication_group","unresolved:publisher-story"),
])
def test_export_rejects_explicitly_unreviewed_groups(tmp_path, field, value):
    item=record();setattr(item.source,field,value)
    with pytest.raises(ValueError,match="groups must be reviewed"):
        export_corpus([item],tmp_path/"out",allow_constructed=True)
    assert not (tmp_path/"out").exists()


def test_ranges_collective_evidence_and_road_specific_override(nlp):
    item = record()
    item.facts[1].depth_scope = "range"
    item.facts[1].value = None
    item.facts[1].qualifiers = ["collective range; no exact per-road measurement"]
    item.relations[1].scope = "collective"
    data = item.model_dump()
    data["facts"].append({**data["facts"][1], "id": "local-depth", "depth_scope": "unspecified", "uncertainty": ["depth unknown"]})
    data["relations"].append({**data["relations"][1], "id": "local-exception", "fact_id": "local-depth",
                              "scope": "local", "target_entity_ids": ["road1"], "overrides_relation_id": "depth-shared"})
    assert validate_record(AnnotationRecord.model_validate(data), nlp) == []


@pytest.mark.parametrize("status", ["forecast", "negated", "historical", "receding", "cleared", "unknown"])
def test_status_is_distinct_from_ner_spans(nlp, status):
    data = record().model_dump()
    evidence = data["facts"][0]["evidence"]
    data["facts"].append({"id": "state", "kind": "status", "value": status, "evidence": evidence})
    assert validate_record(AnnotationRecord.model_validate(data), nlp) == []


def test_export_is_deterministic_and_round_trips_relationships(tmp_path, nlp):
    items = [record(), record("As of 3 PM, Main Road and Side Road had 10 inches of flooding.", "two", "dev")]
    first = export_corpus(items, tmp_path / "first", allow_constructed=True)
    second = export_corpus(list(reversed(items)), tmp_path / "second", allow_constructed=True)
    assert first == second
    assert first["constructed_test_only"] is True
    docs = list(DocBin().from_disk(tmp_path / "first" / "train.spacy").get_docs(nlp.vocab))
    assert docs[0].text == items[0].text
    assert [(e.text, e.label_) for e in docs[0].ents] == [("2 PM", "TIME"), ("Main Road", "ROAD"), ("Side Road", "ROAD"), ("10 inches", "DEPTH")]
    restored = read_jsonl(tmp_path / "first" / "relationships.jsonl", AnnotationRecord)
    assert restored[0].relations == items[0].relations
    assert (tmp_path / "first" / "tokenizer.bin").exists()
    with pytest.raises(ValueError, match="empty"):
        export_corpus(items, tmp_path / "first", allow_constructed=True)


@pytest.mark.parametrize("field,value,expected", [
    ("review_status", "draft", "accepted"), ("split", None, "frozen"),
    ("event_group", None, "event and syndication"), ("admission_status", "research_only", "research-only"),
])
def test_export_refuses_unqualified_records_without_writes(tmp_path, field, value, expected):
    item = record()
    target = item.source if field in {"event_group", "admission_status"} else item
    setattr(target, field, value)
    with pytest.raises(ValueError, match=expected):
        export_corpus([item], tmp_path / "out", allow_constructed=True)
    assert not (tmp_path / "out").exists()


def test_constructed_data_cannot_silently_become_a_training_corpus(tmp_path):
    with pytest.raises(ValueError, match="constructed"):
        export_corpus([record()], tmp_path / "out")


@pytest.mark.parametrize("name", ["Purok labing-isa", "Purok 25-A", "Block treinta y dos", "Blk. 12", "Prk. Singko", "Lot 158-B", "Phase II", "Area A3", "Unit IV", "7th Street", "Purok Maligaya"])
def test_export_preserves_diverse_identifiers_without_forcing_map_identity(tmp_path, name):
    item = record()
    item.text = item.source.text = f"Flooding at {name}."
    item.text_sha256 = item.source.text_sha256 = text_hash(item.text)
    item.passage_end = len(item.text)
    data = item.model_dump()
    data.update(entities=[{"id": "local", "label": "LOCAL_AREA", "text": name, "start": 12, "end": 12 + len(name)}], facts=[], relations=[])
    item = AnnotationRecord.model_validate(data)
    export_corpus([item], tmp_path / "out", allow_constructed=True)
    docs = list(DocBin().from_disk(tmp_path / "out" / "train.spacy").get_docs(corpus_tokenizer().vocab))
    assert docs[0].ents[0].text == name
    assert item.entities[0].identity is None


def test_inferred_dates_and_exact_depths_are_rejected(nlp):
    item = record()
    item.facts[0].value = "2026-10-14T14:00:00+08:00"
    item.facts[1].value = "0.254"
    assert sum("no inferred scalar/date" in e for e in validate_record(item, nlp)) == 2


def test_scope_evidence_must_cover_targets_and_overrides_cannot_cycle(nlp):
    item = record()
    item.relations[0].evidence = [item.entities[2].model_copy()]
    assert any("does not contain target" in e for e in validate_record(item, nlp))
    item = record()
    item.relations[0].overrides_relation_id = "depth-shared"
    item.relations[1].overrides_relation_id = "time-shared"
    assert any("cyclic overrides" in e for e in validate_record(item, nlp))


def test_cli_export_has_visible_failure_and_success(tmp_path, capsys):
    path = tmp_path / "input.jsonl"
    write_jsonl(path, [record()])
    assert main(["export", str(path), "--output", str(tmp_path / "bad")]) == 1
    assert "constructed" in capsys.readouterr().err
    assert main(["export", str(path), "--output", str(tmp_path / "good"), "--allow-constructed"]) == 0
    assert '"train": 1' in capsys.readouterr().out


def test_capture_is_bounded_source_exact_and_separate_from_operational_data(tmp_path):
    html = '<script type="application/ld+json">{"@type":"NewsArticle","headline":"Test","datePublished":"2026-10-14T01:00:00+08:00"}</script><nav>Noise</nav><article><p>Flooding on <b>Main Road</b>.</p><p>As of 2 PM.</p><aside>Related news</aside></article>'
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, text=html, headers={"content-type": "text/html"}))) as client:
        source = capture_source("https://example.org/news", "test-source", "Fixture", "english", "event", client, tmp_path)
    assert source.text == "Flooding on Main Road.\nAs of 2 PM."
    assert source.admission_status == "research_only" and source.reuse_status == "unknown"
    assert source.published_at.utcoffset().total_seconds() == 28800
    assert (tmp_path / f"{source.capture_version}.html").read_bytes() == html.encode()


def test_repeated_capture_is_immutable_and_identical_bodies_keep_distinct_sources(tmp_path):
    html = "<article><p>Flooding on Main Road.</p></article>"
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, text=html, headers={"content-type": "text/html"}))) as client:
        first = capture_source("https://example.org/one", "one", "Fixture", "english", "event", client, tmp_path)
        repeated = capture_source("https://example.org/one", "one", "Fixture", "english", "event", client, tmp_path)
        other = capture_source("https://example.org/two", "two", "Fixture", "english", "event", client, tmp_path)
    assert first == repeated and first.capture_version != other.capture_version
    assert len(list(tmp_path.glob("*.json"))) == 2


def test_corrupt_repeated_capture_is_not_reported_as_success(tmp_path):
    html = "<article><p>Flooding on Main Road.</p></article>"
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, text=html, headers={"content-type": "text/html"}))) as client:
        source = capture_source("https://example.org/news", "one", "Fixture", "english", "event", client, tmp_path)
        (tmp_path / f"{source.capture_version}.txt").write_bytes(b"changed")
        with pytest.raises(ValueError, match="frozen-text capture hash mismatch"):
            capture_source("https://example.org/news", "one", "Fixture", "english", "event", client, tmp_path)


def test_parent_cycles_are_not_geographic_identity(nlp):
    data = record().model_dump()
    data["entities"][0]["identity"] = {"parent_entity_ids": ["road2"]}
    data["entities"][1]["identity"] = {"parent_entity_ids": ["road1"]}
    assert any("cyclic parent" in e for e in validate_record(AnnotationRecord.model_validate(data), nlp))


@pytest.mark.parametrize("body,headers,error", [
    ("<p>No article container</p>", {"content-type": "text/html"}, "no article"),
    ("pdf", {"content-type": "application/pdf"}, "requires HTML"),
    ("x" * (4 * 1024 * 1024 + 1), {"content-type": "text/html"}, "4 MiB"),
], ids=["no-container", "non-html", "too-large"])
def test_capture_failure_does_not_write_a_success_record(tmp_path, body, headers, error):
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, text=body, headers=headers))) as client:
        with pytest.raises(ValueError, match=error):
            capture_source("https://example.org/news", "id", "Publisher", "unknown", "event", client, tmp_path / "capture")
    assert not (tmp_path / "capture").exists()


def test_inventory_preserves_newlines_checks_hash_and_reports_missing_files(tmp_path):
    folder = tmp_path / "docs" / "evaluations" / "sources"
    folder.mkdir(parents=True)
    text = "Purok 11\r\nUnknown depth\r\n"
    (folder / "source.txt").write_bytes(text.encode())
    rows = [{"source_id": "one", "url": "https://example.org/news", "text_path": "source.txt", "text_sha256": text_hash(text)}]
    rows.append({**rows[0], "source_id": "missing", "text_path": "missing.txt"})
    (folder / "source_manifest.json").write_text(json.dumps(rows), encoding="utf-8")
    sources, issues = inventory_sources(tmp_path)
    assert sources[0].text == text
    assert sources[0].published_at is None and sources[0].language == "unknown"
    assert len(issues) == 1 and issues[0]["source_id"] == "missing"


def test_cli_surfaces_bad_jsonl_and_validates_without_application_configuration(tmp_path, capsys):
    path = tmp_path / "input.jsonl"
    path.write_text('{"invalid": true}\n', encoding="utf-8")
    assert main(["validate", str(path)]) == 1
    assert "line 1" in capsys.readouterr().err
    write_jsonl(path, [record()])
    assert main(["validate", str(path)]) == 0
    assert '"valid": true' in capsys.readouterr().out
    backend = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, "-c", "import sys; from training.flood_ner.cli import main; assert 'app.core.database' not in sys.modules; assert 'app.core.config' not in sys.modules; main(['--help'])"], cwd=backend, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_location_inspection_reuses_existing_parent_scoped_osm_identity():
    from training.flood_ner.locations import inspect_place
    result = inspect_place("Sitio Seis", "Malabon", "Malabon")
    assert result["comparison_key"] == "sitio 6"
    assert result["osm_locality_candidates"][0]["osm_id"] == 11155381066
    assert result["osm_locality_candidates"][0]["quarter"] == "Catmon"
    assert not inspect_place("Sitio Seis", "Pasig", "Pasig")["osm_locality_candidates"]
