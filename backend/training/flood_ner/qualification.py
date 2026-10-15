"""Read-only qualification diagnostics for frozen research corpora; no training."""
from __future__ import annotations

from collections import Counter
import hashlib
from importlib.metadata import PackageNotFoundError, version as package_version
import json
from pathlib import Path
import re
from typing import Any

import spacy
from spacy.util import is_compatible_version

from .annotation.schema import AnnotationRecord, PLACE_LABELS
from .annotation.validation import validate_corpus
from .collection import article_key, publisher_for, validate_reviewed, verify_capture_files
from .export import CANDIDATE_TOKENIZER_NAME, TOKENIZER_NAME, corpus_tokenizer
from .sources import inventory_sources, json_bytes, read_jsonl
from .window import LEGACY_WINDOW, PublicationWindow
from .policy import CoveragePolicy, policy_report


def _read_objects(path: Path, description: str) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(description + ' must be a JSON array of objects')
    return value


def _bound_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError('qualification evidence path must be a nonblank string')
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('qualification evidence file is missing or outside its root')
    return path


def load_frozen_cohort(folder: Path) -> tuple[list[AnnotationRecord], Any, dict[str, Any]]:
    manifest = json.loads((folder / 'partition_manifest.json').read_text(encoding='utf-8'))
    files = manifest.get('files') if isinstance(manifest, dict) else None
    required = {'grouped_annotations.jsonl', 'annotation_schema.json', 'tokenizer.bin', 'selection_register.json'}
    if not isinstance(files, dict) or not required <= files.keys():
        raise ValueError('frozen manifest must bind annotations, schema, tokenizer and selection')
    for name, digest in files.items():
        if (not isinstance(name, str) or not isinstance(digest, str)
                or not re.fullmatch(r'[a-f0-9]{64}', digest)
                or hashlib.sha256(_bound_file(folder, name).read_bytes()).hexdigest() != digest):
            raise ValueError('frozen cohort file hash mismatch')
    if manifest.get('tokenizer_sha256') != files['tokenizer.bin'] or manifest.get('annotation_schema_sha256') != files['annotation_schema.json']:
        raise ValueError('frozen schema/tokenizer identities mismatch')
    records = read_jsonl(folder / 'grouped_annotations.jsonl', AnnotationRecord)
    nlp = corpus_tokenizer(manifest.get('tokenizer', TOKENIZER_NAME))
    nlp.tokenizer.from_bytes((folder / 'tokenizer.bin').read_bytes())
    errors = validate_corpus(records, nlp)
    counts = {split: dict(Counter(r.passage_language for r in records if r.split == split))
              for split in ('train', 'dev', 'test')}
    if errors or manifest.get('total') != len(records) or manifest.get('counts') != counts:
        raise ValueError('frozen annotations, totals or split identities fail validation: ' + '; '.join(errors))
    if 'coverage_policy' in manifest:
        from .cohort import _groups
        policy = CoveragePolicy.model_validate_json(json.dumps(manifest['coverage_policy']))
        if not policy_report(records, _groups(records), policy)['passed']:
            raise ValueError('frozen cohort fails its declared coverage policy')
    return records, nlp, manifest


def model_compatibility(rows: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
    results = []
    for row in rows:
        required = {'files', 'model', 'revision', 'version', 'spacy_requirement', 'ner_labels', 'license'}
        if (not required <= row.keys() or not isinstance(row['files'], dict)
                or 'meta.json' not in row['files']):
            raise ValueError('model register needs versioned, captured metadata evidence')
        for evidence in row['files'].values():
            if not isinstance(evidence, dict) or not {'raw_path', 'sha256'} <= evidence.keys():
                raise ValueError('model metadata evidence needs path and hash')
            path = _bound_file(root, evidence['raw_path'])
            if hashlib.sha256(path.read_bytes()).hexdigest() != evidence['sha256']:
                raise ValueError('model metadata evidence hash mismatch')
        meta = json.loads(_bound_file(root, row['files']['meta.json']['raw_path']).read_text(encoding='utf-8'))
        if (not isinstance(meta, dict) or not {'version', 'spacy_version', 'labels', 'license'} <= meta.keys()
                or not isinstance(meta['labels'], dict) or not isinstance(meta['labels'].get('ner'), list)
                or not isinstance(meta.get('requirements', []), list)):
            raise ValueError('model metadata must declare its version, license, labels and dependencies')
        if (meta['version'] != row['version'] or meta['spacy_version'] != row['spacy_requirement']
                or meta.get('labels', {}).get('ner') != row['ner_labels'] or meta.get('license') != row['license']):
            raise ValueError('model register does not match frozen metadata')
        compatible = is_compatible_version(spacy.__version__, meta['spacy_version'])
        dependencies = []
        for requirement in meta.get('requirements', []):
            if not isinstance(requirement, str):
                raise ValueError('model dependency declaration must be a string')
            match = re.fullmatch(r'([A-Za-z0-9_.-]+)(.*)', requirement)
            if match is None:
                raise ValueError('unsupported model dependency declaration')
            package, specifier = match.groups()
            try:
                installed = package_version(package)
            except PackageNotFoundError:
                installed = None
            dependencies.append({'requirement': requirement, 'installed_version': installed,
                                 'satisfied': installed is not None and (not specifier or is_compatible_version(installed, specifier))})
        results.append({
            'model': row['model'], 'version': meta['version'], 'revision': row['revision'],
            'spacy_requirement': meta['spacy_version'], 'installed_spacy': spacy.__version__,
            'declared_spacy_compatibility': compatible,
            'ner_labels': meta.get('labels', {}).get('ner', []), 'model_license': meta.get('license'),
            'fine_grained_lanes_labels_available': PLACE_LABELS <= set(meta.get('labels', {}).get('ner', [])),
            'metadata_evidence': row['files'], 'weights_loaded': False,
            'declared_dependency_checks': dependencies,
            'inference_accuracy_measured': False, 'runtime_tokenizer_qualified': False,
            'state': 'metadata_compatible_only' if compatible else 'metadata_spacy_version_conflict',
        })
    return results


def qualification_report(records: list[AnnotationRecord], nlp: Any) -> dict[str, Any]:
    errors = validate_corpus(records, nlp)
    if errors or not records or any(r.annotation_profile != 'location-only-v1' or r.split is None for r in records):
        raise ValueError('qualification requires valid, split-assigned location-only records: ' + '; '.join(errors))
    labels = sorted(PLACE_LABELS)
    slices = []
    for split in ('train', 'dev', 'test'):
        for language in ('english', 'taglish'):
            selected = [r for r in records if r.split == split and r.passage_language == language]
            spans = Counter(e.label for r in selected for e in r.entities)
            slices.append({
                'split': split, 'language': language, 'samples': len(selected),
                'articles': len({article_key(r.source.url) for r in selected}),
                'reporting_groups': len({r.source.event_group for r in selected}),
                'empty_place_records': sum(not r.entities for r in selected),
                'entity_spans': {label: spans[label] for label in labels},
                'samples_with_label': {label: sum(any(e.label == label for e in r.entities) for r in selected) for label in labels},
            })
    publishers = sorted({publisher_for(r.source.url) or r.source.publisher for r in records})
    publisher_languages = {p: dict(Counter(r.passage_language for r in records
                            if (publisher_for(r.source.url) or r.source.publisher) == p)) for p in publishers}
    source_articles = Counter(article_key(r.source.url) for r in records)
    groups = Counter(r.source.event_group for r in records)
    ready = [r for r in records if r.review_status == 'accepted' and r.complete and r.reviewer and r.reviewer.strip()
             and r.source.admission_status == 'training_admitted' and r.source.reuse_status == 'allowed'
             and r.source.origin == 'captured_original' and r.quality != 'constructed'
             and (r.quality != 'silver' or (r.teacher and r.teacher.strip()))
             and all(value and not value.casefold().startswith(('provisional:', 'review-needed:', 'unresolved:'))
                     for value in (r.source.article_group, r.source.event_group, r.source.syndication_group))]
    candidate = corpus_tokenizer(CANDIDATE_TOKENIZER_NAME)
    candidate_tokenizer_sha256 = hashlib.sha256(candidate.tokenizer.to_bytes()).hexdigest()
    candidate_errors = validate_corpus(records, candidate)
    return {
        'schema_version': 'lanes-flood-ner-qualification-v1',
        'technical_annotation_validation': 'pass', 'samples': len(records),
        'accepted_annotations': sum(r.review_status == 'accepted' and r.complete for r in records),
        'source_articles': len(source_articles), 'entity_spans': sum(len(r.entities) for r in records),
        'slices': slices, 'publisher_languages': publisher_languages,
        'publisher_majority_language_fraction': sum(max(v.values()) for v in publisher_languages.values()) / len(records),
        'publisher_majority_language_fraction_is_not_ner_accuracy': True,
        'largest_article_samples': max(source_articles.values()),
        'largest_reporting_group_samples': max(groups.values()),
        'reporting_group_count': len(groups),
        'small_holdout_slices': [{'split': s['split'], 'language': s['language'], 'label': label, 'spans': count}
                                 for s in slices if s['split'] != 'train' for label, count in s['entity_spans'].items() if count <= 5],
        'small_slice_threshold': 'descriptive flag: <=5 spans; not an accuracy acceptance threshold',
        'training_admitted': sum(r.source.admission_status == 'training_admitted' for r in records),
        'export_ready_records': len(ready),
        'declared_gold_records': sum(r.quality == 'gold' for r in records),
        'independent_review_verified_by_this_tool': False,
        'actual_model_inference_performed': False, 'training_performed': False,
        'candidate_tokenizer': {'name': CANDIDATE_TOKENIZER_NAME,
                               'sha256': candidate_tokenizer_sha256,
                               'corpus_alignment_errors': candidate_errors, 'promoted': False},
        'qualification_open_items': ['source_use_assessment', 'independent_language_label_review',
                                     'publisher_language_confounding', 'exact_incident_membership_review',
                                     'missing_real_source_address_coverage', 'complete_context_severity_references',
                                     'actual_model_tokenizer_and_resource_qualification', 'frozen_evaluation_contract'],
        'notes': ['Empty entities mean no supported six-profile place labels, not absence of flooding.',
                  'Metadata checks and alignment are not model inference or accuracy measurements.',
                  'Reporting groups express conservative split dependencies, not exact physical incidents.'],
    }


def write_qualification(folder: Path, news_register: Path, root: Path, output: Path, *,
                        model_register: Path | None = None, reuse_register: Path | None = None,
                        window: PublicationWindow | None = None) -> dict[str, Any]:
    artifacts = (root / 'backend/training/flood_ner/artifacts').resolve()
    if not output.resolve().is_relative_to(artifacts) or output.exists():
        raise ValueError('qualification output must be new and under ignored training artifacts')
    records, nlp, manifest = load_frozen_cohort(folder)
    declared_window = PublicationWindow.parse(manifest.get('publication_window', LEGACY_WINDOW.as_list()))
    if window is not None and window != declared_window:
        raise ValueError('qualification publication window must match frozen manifest')
    sources, issues = inventory_sources(root)
    entries = _read_objects(news_register, 'news register')
    by_version = {s.capture_version: s for s in sources}
    errors = validate_reviewed(entries, by_version, window=declared_window) + verify_capture_files(entries, root)
    accepted = {e['capture_version'] for e in entries if e.get('status') == 'accepted'}
    for record in records:
        original = by_version.get(record.source.capture_version)
        if original is None or record.source.capture_version not in accepted:
            errors.append('every record requires inventoried reviewed source evidence')
            continue
        before, after = original.model_dump(), record.source.model_dump()
        for key in ('article_group', 'event_group', 'syndication_group'):
            before.pop(key); after.pop(key)
        if before != after:
            errors.append('immutable capture metadata changed beyond reviewed grouping overlay')
    if issues or errors:
        raise ValueError('qualification source binding failed: ' + '; '.join(errors))
    report = qualification_report(records, nlp)
    report['frozen_manifest_sha256'] = hashlib.sha256((folder / 'partition_manifest.json').read_bytes()).hexdigest()
    report['frozen_tokenizer'] = manifest['tokenizer']
    report['verified_selected_sources'] = len({r.source.capture_version for r in records})
    report['models'] = model_compatibility(_read_objects(model_register, 'model register'), root) if model_register else []
    policies = _read_objects(reuse_register, 'reuse register') if reuse_register else []
    if any(not {'publisher', 'policy_evidence'} <= p.keys() or not isinstance(p['policy_evidence'], list) for p in policies):
        raise ValueError('reuse register needs publisher identity and captured policy evidence')
    report['source_use_inventory'] = []
    for publisher in report['publisher_languages']:
        policy = next((p for p in policies if p['publisher'] == publisher), None)
        evidence = policy['policy_evidence'] if policy else []
        for entry in evidence:
            if not isinstance(entry, dict) or not {'raw_path', 'raw_sha256'} <= entry.keys():
                raise ValueError('publisher policy evidence needs path and hash')
            if hashlib.sha256(_bound_file(root, entry['raw_path']).read_bytes()).hexdigest() != entry['raw_sha256']:
                raise ValueError('publisher policy evidence hash mismatch')
        report['source_use_inventory'].append({'publisher': publisher, 'selected_samples': sum(report['publisher_languages'][publisher].values()),
            'selected_articles': len({article_key(r.source.url) for r in records if publisher_for(r.source.url) == publisher}),
            'policy_evidence': evidence, 'assessment': 'evidence inventory only; no admission or legal determination'})
    output.mkdir(parents=True)
    (output / 'qualification.json').write_bytes(json_bytes(report))
    (output / 'candidate_tokenizer.bin').write_bytes(corpus_tokenizer(CANDIDATE_TOKENIZER_NAME).tokenizer.to_bytes())
    return report
