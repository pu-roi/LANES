"""Explicit, hash-bound annotation corrections without selecting new samples."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

from pydantic import Field, model_validator

from .annotation.schema import AnnotationRecord, Entity, PLACE_LABELS, StrictRecord
from .annotation.validation import validate_corpus
from .cohort import _groups
from .policy import CoveragePolicy, policy_report
from .qualification import _bound_file, load_frozen_cohort
from .sources import json_bytes, write_jsonl


def record_hash(record: AnnotationRecord) -> str:
    return hashlib.sha256(json_bytes(record.model_dump(mode='json'))).hexdigest()


class EntityCorrection(StrictRecord):
    record_id: str = Field(min_length=1)
    original_record_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    passage_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    before_entities: list[Entity]
    after_entities: list[Entity]
    revision: str = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    reviewed_at: datetime
    reason: str = Field(min_length=1)
    context_target_qualifiers: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode='after')
    def reviewed(self) -> EntityCorrection:
        if (any(not value.strip() for value in (self.record_id, self.revision, self.reviewer, self.reason))
                or self.reviewed_at.utcoffset() is None
                or any(not key.strip() or not value.strip() for key, value in self.context_target_qualifiers.items())):
            raise ValueError('corrections require substantive review and a timezone-qualified review date')
        return self


def apply_corrections(records: list[AnnotationRecord], corrections: list[EntityCorrection], nlp: Any) -> list[AnnotationRecord]:
    errors = validate_corpus(records, nlp)
    by_id = {r.record_id: r for r in records}
    if errors or not corrections or len({c.record_id for c in corrections}) != len(corrections):
        raise ValueError('valid corpus and distinct explicit corrections required')
    updated = {key: value.model_copy(deep=True) for key, value in by_id.items()}
    for correction in corrections:
        original = by_id.get(correction.record_id)
        if (original is None or original.annotation_profile != 'location-only-v1'
                or original.quality not in {'silver', 'constructed'} or original.review_status != 'accepted' or not original.complete
                or original.text_sha256 != correction.passage_sha256
                or record_hash(original) != correction.original_record_sha256
                or original.entities != correction.before_entities):
            raise ValueError('correction input hash or expected original annotations differ')
        if (correction.after_entities == correction.before_entities
                or correction.revision == original.annotation_revision
                or not set(correction.context_target_qualifiers) <= {e.id for e in correction.after_entities}):
            raise ValueError('changed entities, new revision and existing qualifier targets required')
        record = updated[correction.record_id]
        record.entities = [e.model_copy(deep=True) for e in correction.after_entities]
        record.annotation_revision = correction.revision
        record.reviewer = correction.reviewer
        record.notes.append(f'AI annotation correction {correction.reviewed_at.isoformat()}: {correction.reason}')
    revised = [updated[r.record_id] for r in records]
    errors = validate_corpus(revised, nlp)
    if errors:
        raise ValueError('corrected annotations fail validation: ' + '; '.join(errors))
    return revised


def revise_contexts(originals: list[AnnotationRecord], revised: list[AnnotationRecord], contexts: list[AnnotationRecord],
                    corrections: list[EntityCorrection], nlp: Any) -> list[AnnotationRecord]:
    """Retain fact/target IDs; a new locality does not acquire a flood assertion."""
    expected = apply_corrections(originals, corrections, nlp)
    if expected != revised or validate_corpus(contexts, nlp):
        raise ValueError('context rebind requires exactly the reviewed location corrections')
    before = {r.record_id: r for r in originals}
    after = {r.record_id: r for r in revised}
    patches = {c.record_id: c for c in corrections}
    results = []
    for record in contexts:
        original = before.get(record.record_id)
        if (original is None or record.split != 'train' or original.split != 'train'
                or record.annotation_profile != 'context-rich-v1'
                or record.source != original.source or record.text != original.text
                or record.text_sha256 != original.text_sha256
                or record.passage_start != original.passage_start or record.passage_end != original.passage_end
                or record.passage_language != original.passage_language
                or [e for e in record.entities if e.label in PLACE_LABELS] != original.entities):
            raise ValueError('original context/location binding differs')
        result = record.model_copy(deep=True)
        if record.record_id in patches:
            patch = patches[record.record_id]
            result.entities = [e.model_copy(deep=True) for e in after[record.record_id].entities] + [
                e.model_copy(deep=True) for e in record.entities if e.label not in PLACE_LABELS]
            result.annotation_revision = patch.revision + '-context-v3'
            result.reviewer = patch.reviewer
            result.notes.append(f'Paired AI silver correction {patch.reviewed_at.isoformat()}: {patch.reason}')
            facts = {f.id: f for f in result.facts}
            for relation in result.relations:
                for target in relation.target_entity_ids:
                    qualifier = patch.context_target_qualifiers.get(target)
                    if qualifier and qualifier not in facts[relation.fact_id].qualifiers:
                        facts[relation.fact_id].qualifiers.append(qualifier)
        results.append(result)
    errors = validate_corpus(results, nlp)
    if errors:
        raise ValueError('corrected contextual annotations fail validation: ' + '; '.join(errors))
    return results


def write_cohort_revision(cohort: Path, corrections: list[EntityCorrection], output: Path, root: Path) -> dict:
    artifacts = (root / 'backend/training/flood_ner/artifacts').resolve()
    output = output.resolve()
    if not output.is_relative_to(artifacts) or output.exists():
        raise ValueError('revision destination must be new and under ignored artifacts')
    records, nlp, parent = load_frozen_cohort(cohort)
    revised = apply_corrections(records, corrections, nlp)
    manifest = {k: v for k, v in parent.items() if k != 'files'}
    if 'coverage_policy' in parent:
        policy = CoveragePolicy.model_validate_json(json.dumps(parent['coverage_policy']))
        checked = policy_report(revised, _groups(revised), policy)
        if not checked['passed']:
            raise ValueError('correction violates frozen coverage quotas')
        manifest['policy_checks'] = checked
    register = json.loads((cohort / 'selection_register.json').read_text(encoding='utf-8'))
    by_id = {r.record_id: r for r in revised}
    if len(register) != len(revised) or {r['record_id'] for r in register} != set(by_id):
        raise ValueError('parent selection identities differ')
    for row in register:
        record = by_id[row['record_id']]
        for key, value in [('entities', len(record.entities)), ('annotation_revision', record.annotation_revision),
                           ('reviewer', record.reviewer)]:
            row[key] = value
    correction_register = {'schema_version': 'lanes-annotation-correction-v1',
        'parent_manifest_sha256': hashlib.sha256((cohort / 'partition_manifest.json').read_bytes()).hexdigest(),
        'corrections': [c.model_dump(mode='json') for c in sorted(corrections, key=lambda c: c.record_id)],
        'records_changed': len(corrections), 'sample_selection_rerun': False, 'partitions_changed': False}
    manifest['annotation_revision_of'] = correction_register['parent_manifest_sha256']
    manifest['correction_register_sha256'] = hashlib.sha256(json_bytes(correction_register)).hexdigest()
    coverage = json.loads((cohort / 'coverage.json').read_text(encoding='utf-8'))
    coverage.update(manifest)
    coverage['entity_labels'] = dict(Counter(e.label for r in revised for e in r.entities))
    coverage['empty_entity_records'] = sum(not r.entities for r in revised)
    # Validate all inputs before creating a new version. Never write the parent.
    files = {name: _bound_file(cohort, name) for name in parent['files']}
    if any(Path(name).name != name or '/' in name or '\\' in name for name in files):
        raise ValueError('revision inputs require local manifest basenames')
    output.mkdir(parents=True)
    for name, path in files.items():
        shutil.copyfile(path, output / name)
    write_jsonl(output / 'grouped_annotations.jsonl', revised)
    (output / 'selection_register.json').write_bytes(json_bytes(register))
    (output / 'coverage.json').write_bytes(json_bytes(coverage))
    (output / 'correction_register.json').write_bytes(json_bytes(correction_register))
    manifest['files'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}
    (output / 'partition_manifest.json').write_bytes(json_bytes(manifest))
    load_frozen_cohort(output)
    return manifest
