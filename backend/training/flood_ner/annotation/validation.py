"""Validate source-exact spans, semantics and frozen corpus partitions."""
from __future__ import annotations

from collections import defaultdict
from typing import Any
from urllib.parse import urlsplit

from .schema import AnnotationRecord, PLACE_LABELS, SourceCapture, Span, text_hash
from ..collection import article_key

STATUS_VALUES = {"active", "rising", "receding", "subsided", "cleared", "forecast", "negated", "historical", "habitual", "prevention", "unknown"}
ACCESS_VALUES = {"passable_all", "passable_with_caution", "passable_unspecified", "light_vehicle_closed", "impassable_all", "unknown"}


def validate_record(record: AnnotationRecord, nlp: Any) -> list[str]:
    errors: list[str] = []
    source = record.source
    if record.annotation_profile == 'location-only-v1':
        if any(e.label not in PLACE_LABELS for e in record.entities) or record.facts or record.relations:
            errors.append('location-only profile requires place entities only; contextual evidence belongs in a separate record')
    try:
        SourceCapture.model_validate(source.model_dump())
    except ValueError as exc:
        errors.append(f"source integrity: {exc}")
    if source.text[record.passage_start:record.passage_end] != record.text or record.passage_end > len(source.text):
        errors.append("passage offsets do not match unchanged source text")
    if text_hash(record.text) != record.text_sha256:
        errors.append("passage text_sha256 mismatch")
    doc = nlp.make_doc(record.text)

    def check_span(span: Span, context: str, aligned: bool = False) -> None:
        if span.end <= span.start or span.end > len(record.text) or record.text[span.start:span.end] != span.text:
            errors.append(f"{context}: invalid source-exact span")
        elif aligned and doc.char_span(span.start, span.end, alignment_mode="strict") is None:
            errors.append(f"{context}: entity is not token aligned")

    ids: set[str] = set()
    for kind, objects in (("entity", record.entities), ("fact", record.facts), ("relation", record.relations)):
        for item in objects:
            if item.id in ids:
                errors.append(f"{kind} {item.id}: duplicate annotation ID")
            ids.add(item.id)
    entities = {item.id: item for item in record.entities}
    facts = {item.id: item for item in record.facts}
    relations = {item.id: item for item in record.relations}
    previous_end = -1
    for entity in sorted(record.entities, key=lambda e: (e.start, e.end)):
        check_span(entity, f"entity {entity.id}", aligned=True)
        if entity.start < previous_end:
            errors.append(f"entity {entity.id}: overlapping NER entities")
        previous_end = max(previous_end, entity.end)
        if entity.identity:
            identity = entity.identity
            if entity.label not in PLACE_LABELS:
                errors.append(f"entity {entity.id}: geography only applies to places")
            if any(p not in entities or entities[p].label not in PLACE_LABELS or p == entity.id for p in identity.parent_entity_ids):
                errors.append(f"entity {entity.id}: invalid parent entity")
            if (identity.osm_id is None) != (identity.osm_type is None):
                errors.append(f"entity {entity.id}: incomplete OSM identity")
            if identity.state != "resolved" and (identity.psgc_code or identity.osm_id):
                errors.append(f"entity {entity.id}: uncertain identity must not carry definitive feature IDs")
            if identity.state == "resolved" and not identity.reference_url:
                errors.append(f"entity {entity.id}: resolved identity requires reference evidence")
            if identity.state == "resolved" and not (identity.psgc_code or identity.osm_id):
                errors.append(f"entity {entity.id}: resolved identity requires a reviewed feature ID")
            if identity.psgc_code and entity.label not in {"BARANGAY", "CITY", "PROVINCE"}:
                errors.append(f"entity {entity.id}: PSGC identifies administrative places, not this local/road entity")
            if identity.reference_url:
                reference = urlsplit(identity.reference_url)
                if reference.scheme not in {"http", "https"} or not reference.hostname or reference.username or reference.password:
                    errors.append(f"entity {entity.id}: reference must be HTTP(S) without credentials")
    for fact in record.facts:
        for span in fact.evidence:
            check_span(span, f"fact {fact.id}")
        expected = {"depth": "DEPTH", "time": "TIME"}.get(fact.kind)
        if any(e not in entities or (expected and entities[e].label != expected) for e in fact.entity_ids):
            errors.append(f"fact {fact.id}: invalid evidence entity reference")
        if expected and not fact.entity_ids:
            errors.append(f"fact {fact.id}: depth/time needs its entity evidence")
        if expected and fact.value is not None and fact.value not in {entities[e].text for e in fact.entity_ids if e in entities}:
            errors.append(f"fact {fact.id}: depth/time value must be raw entity text or null; no inferred scalar/date")
        if any(e in entities and not any(s.start <= entities[e].start and s.end >= entities[e].end for s in fact.evidence) for e in fact.entity_ids):
            errors.append(f"fact {fact.id}: evidence does not contain referenced entity")
        if fact.kind == "time" and fact.temporal_role is None:
            errors.append(f"fact {fact.id}: time role required")
        if fact.kind != "time" and fact.temporal_role is not None:
            errors.append(f"fact {fact.id}: temporal role on non-time fact")
        if fact.kind == "depth" and fact.depth_scope is None:
            errors.append(f"fact {fact.id}: depth scope required")
        if fact.kind != "depth" and fact.depth_scope is not None:
            errors.append(f"fact {fact.id}: depth scope on non-depth fact")
        if fact.kind == "status" and fact.value not in STATUS_VALUES:
            errors.append(f"fact {fact.id}: unsupported status")
        if fact.kind == "access" and fact.value not in ACCESS_VALUES:
            errors.append(f"fact {fact.id}: unsupported access")
    for relation in record.relations:
        for span in relation.evidence:
            check_span(span, f"relation {relation.id}")
        if relation.fact_id not in facts:
            errors.append(f"relation {relation.id}: missing fact")
        if len(set(relation.target_entity_ids)) != len(relation.target_entity_ids) or any(
            e not in entities or entities[e].label not in PLACE_LABELS for e in relation.target_entity_ids
        ):
            errors.append(f"relation {relation.id}: invalid place targets")
        if relation.scope == "local" and len(relation.target_entity_ids) != 1:
            errors.append(f"relation {relation.id}: local scope needs one target")
        if relation.scope == "shared" and len(relation.target_entity_ids) < 2:
            errors.append(f"relation {relation.id}: shared scope needs multiple targets")
        if relation.scope == "unresolved" and not relation.uncertainty:
            errors.append(f"relation {relation.id}: unresolved scope requires uncertainty")
        if any(e in entities and not any(s.start <= entities[e].start and s.end >= entities[e].end for s in relation.evidence) for e in relation.target_entity_ids):
            errors.append(f"relation {relation.id}: scope evidence does not contain target")
        base = relations.get(relation.overrides_relation_id or "")
        if relation.overrides_relation_id and (
            base is None or base.id == relation.id or not set(relation.target_entity_ids) <= set(base.target_entity_ids)
            or relation.fact_id not in facts or base.fact_id not in facts
            or facts[relation.fact_id].kind != facts[base.fact_id].kind
        ):
            errors.append(f"relation {relation.id}: invalid local override")
    for entity in record.entities:
        pending = list(entity.identity.parent_entity_ids) if entity.identity else []
        seen: set[str] = set()
        while pending:
            parent = pending.pop()
            if parent == entity.id:
                errors.append(f"entity {entity.id}: cyclic parent hierarchy")
                break
            if parent not in seen:
                seen.add(parent)
                ancestor = entities.get(parent)
                if ancestor and ancestor.identity:
                    pending.extend(ancestor.identity.parent_entity_ids)
    for relation in record.relations:
        seen = {relation.id}
        current = relation
        while current.overrides_relation_id in relations:
            if current.overrides_relation_id in seen:
                errors.append(f"relation {relation.id}: cyclic overrides")
                break
            seen.add(current.overrides_relation_id)
            current = relations[current.overrides_relation_id]
    if record.review_status == "accepted" and (not record.reviewer or not record.complete):
        errors.append("accepted annotations require reviewer and complete passage annotation")
    if record.quality == "silver" and record.review_status == "accepted" and not record.teacher:
        errors.append("accepted silver annotations require teacher identity")
    if source.origin == "constructed_fixture" and record.quality != "constructed":
        errors.append("constructed sources must retain constructed quality")
    return errors


def validate_corpus(records: list[AnnotationRecord], nlp: Any) -> list[str]:
    errors: list[str] = []
    record_ids: set[str] = set()
    memberships: dict[tuple[str, str], set[str]] = defaultdict(set)
    for record in records:
        if record.record_id in record_ids:
            errors.append(f"{record.record_id}: duplicate record ID")
        record_ids.add(record.record_id)
        errors.extend(f"{record.record_id}: {error}" for error in validate_record(record, nlp))
        if record.split:
            source = record.source
            for key, value in (
                ("article", source.article_group), ("url", article_key(source.url)), ("event", source.event_group),
                ("syndication", source.syndication_group), ("source_hash", source.text_sha256),
                ("passage_hash", record.text_sha256),
            ):
                if value:
                    memberships[(key, value)].add(record.split)
    errors.extend(f"split leakage: {key} group {value!r}" for (key, value), splits in sorted(memberships.items()) if len(splits) > 1)
    return errors
