"""Deterministic reviewed-corpus serialization, not model training."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import spacy
from spacy.tokens import DocBin
from spacy.util import compile_infix_regex, compile_prefix_regex, compile_suffix_regex

from .annotation.schema import AnnotationRecord, AnnotationProfile, LABELS, PLACE_LABELS, SCHEMA_VERSION
from .annotation.validation import validate_corpus
from .sources import json_bytes, write_jsonl

TOKENIZER_NAME = "lanes.xx.address-v2"
CANDIDATE_TOKENIZER_NAME = "lanes.xx.address-v3"


def corpus_tokenizer(version: str = TOKENIZER_NAME) -> Any:
    if spacy.__version__ != "3.7.5":
        raise ValueError(f"milestone-1 tokenizer requires spaCy 3.7.5; found {spacy.__version__}")
    if version not in {TOKENIZER_NAME, CANDIDATE_TOKENIZER_NAME}:
        raise ValueError('unsupported corpus tokenizer version')
    nlp = spacy.blank("xx")
    # Address-code suffixes such as 25-A. must end before sentence punctuation.
    # This changes token boundaries only; original source characters stay intact.
    nlp.tokenizer.suffix_search = compile_suffix_regex([*nlp.Defaults.suffixes, r"(?<=[A-Za-z0-9])[.\-,:;]"]).search
    nlp.tokenizer.prefix_search = compile_prefix_regex([*nlp.Defaults.prefixes, r'-']).search
    if version == CANDIDATE_TOKENIZER_NAME:
        # Opt-in qualification candidate: a typographic dash after a number
        # can delimit a report (2—baha). Keep ordinary address codes like 25-A.
        nlp.tokenizer.infix_finditer = compile_infix_regex(
            [*nlp.Defaults.infixes, r'(?<=[A-Za-z0-9.!?])[–—](?=\w)',
             r'(?<=\w)\.[–—](?=\w)', r'(?<=\w)/(?=\w)',
             r'(?<=[A-Za-z])-(?=[0-9]+(?:st|nd|rd|th)\b)']).finditer
        nlp.tokenizer.suffix_search = compile_suffix_regex(
            [*nlp.Defaults.suffixes, r'(?<=[A-Za-z0-9])[.\-,:;/–—]']).search
    return nlp


def export_corpus(records: list[AnnotationRecord], output: Path, *, allow_constructed: bool = False,
                  annotation_profile: AnnotationProfile = 'context-rich-v1',
                  tokenizer: str = TOKENIZER_NAME) -> dict[str, Any]:
    if annotation_profile not in {'context-rich-v1', 'location-only-v1'}:
        raise ValueError('unsupported annotation profile')
    nlp = corpus_tokenizer(tokenizer)
    errors = validate_corpus(records, nlp)
    if not records:
        errors.append("no annotations supplied")
    for record in records:
        if record.annotation_profile != annotation_profile:
            errors.append(f'{record.record_id}: record profile must match explicit export profile {annotation_profile}')
        if record.review_status != "accepted" or not record.complete or not record.reviewer:
            errors.append(f"{record.record_id}: export requires complete, accepted, reviewed annotations")
        if record.split is None:
            errors.append(f"{record.record_id}: frozen train/dev/test split required")
        if not record.source.event_group or not record.source.syndication_group:
            errors.append(f"{record.record_id}: reviewed event and syndication groups required (use a unique group for unsyndicated sources)")
        if any(value and value.casefold().startswith(("provisional:", "review-needed:", "unresolved:"))
               for value in (record.source.article_group, record.source.event_group, record.source.syndication_group)):
            errors.append(f"{record.record_id}: provisional/unresolved groups must be reviewed before export")
        if record.source.admission_status != "training_admitted":
            errors.append(f"{record.record_id}: source is research-only")
        if (record.quality == "constructed" or record.source.origin == "constructed_fixture") and not allow_constructed:
            errors.append(f"{record.record_id}: constructed data requires explicit test-only override")
    if errors:
        raise ValueError("\n".join(errors))
    if output.exists() and any(output.iterdir()):
        raise ValueError("export destination must be empty; refuse overwriting a frozen dataset")
    records = sorted(records, key=lambda r: r.record_id)
    tokenizer_bytes = (corpus_tokenizer(tokenizer).tokenizer.to_bytes()
                       if tokenizer == CANDIDATE_TOKENIZER_NAME else nlp.tokenizer.to_bytes())
    files: dict[str, bytes] = {"tokenizer.bin": tokenizer_bytes}
    counts = {}
    for split in ("train", "dev", "test"):
        binary = DocBin(attrs=["ORTH", "SPACY", "ENT_IOB", "ENT_TYPE"], store_user_data=True)
        selected = [r for r in records if r.split == split]
        for record in selected:
            doc = nlp.make_doc(record.text)
            doc.ents = [doc.char_span(e.start, e.end, label=e.label, alignment_mode="strict") for e in sorted(record.entities, key=lambda e: e.start)]
            doc.user_data["record_id"] = record.record_id
            binary.add(doc)
        files[f"{split}.spacy"] = binary.to_bytes()
        counts[split] = len(selected)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "schema_sha256": hashlib.sha256(json_bytes(AnnotationRecord.model_json_schema())).hexdigest(),
        "spacy_version": spacy.__version__, "tokenizer": tokenizer,
        "tokenizer_sha256": hashlib.sha256(tokenizer_bytes).hexdigest(),
        "annotation_profile": annotation_profile,
        "labels": [label for label in LABELS if annotation_profile != 'location-only-v1' or label in PLACE_LABELS],
        "counts": counts, "constructed_test_only": allow_constructed,
        "records": [{"record_id": r.record_id, "split": r.split, "source_sha256": r.source.text_sha256,
                     "passage_sha256": r.text_sha256, "annotation_revision": r.annotation_revision,
                     "quality": r.quality, "annotation_profile": r.annotation_profile,
                     "passage_language": r.passage_language, "article_group": r.source.article_group,
                     "event_group": r.source.event_group, "syndication_group": r.source.syndication_group} for r in records],
    }
    output.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (output / name).write_bytes(data)
    # Full records preserve relationships, geographic identity, evidence and review provenance.
    write_jsonl(output / "relationships.jsonl", records)
    manifest["files"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())}
    (output / "manifest.json").write_bytes(json_bytes(manifest))
    return manifest
