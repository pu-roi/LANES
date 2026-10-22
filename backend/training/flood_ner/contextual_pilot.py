"""Validate paired contextual reviews against a frozen location training cohort."""
from collections import Counter
import hashlib
from pathlib import Path
from typing import Literal

from pydantic import Field

from .annotation.schema import AnnotationRecord, PLACE_LABELS, Span, StrictRecord
from .annotation.validation import validate_corpus
from .annotation.context_review import contextual_semantic_errors
from .collection import article_key
from .qualification import load_frozen_cohort
from .sources import json_bytes, write_jsonl

CATEGORIES = ('shared_observations', 'local_exceptions', 'collective_ranges', 'temporal_transitions', 'negative_unknown_time')


class CategoryEvidence(StrictRecord):
    category: Literal['shared_observations', 'local_exceptions', 'collective_ranges', 'temporal_transitions', 'negative_unknown_time']
    evidence: list[Span] = Field(min_length=1)
    rationale: str = Field(min_length=1)


class ContextReview(StrictRecord):
    schema_version: Literal['lanes-context-pilot-review-v1'] = 'lanes-context-pilot-review-v1'
    record_id: str = Field(min_length=1)
    passage_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    reviewer: str = Field(min_length=1)
    categories: list[CategoryEvidence] = Field(default_factory=list)


def validate_contextual_pilot(locations: list[AnnotationRecord], contexts: list[AnnotationRecord],
                              reviews: list[ContextReview], nlp) -> dict:
    errors = validate_corpus(contexts, nlp)
    by_id = {r.record_id: r for r in locations}
    by_review = {r.record_id: r for r in reviews}
    if len(by_review) != len(reviews) or set(by_review) != {r.record_id for r in contexts}:
        errors.append('one source-bound category review required per contextual record')
    for record in contexts:
        for fact in record.facts:
            errors.extend(f'{record.record_id}: {error}' for error in contextual_semantic_errors(fact))
        original = by_id.get(record.record_id)
        if original is None or original.split != 'train' or record.split != 'train':
            errors.append(f'{record.record_id}: contextual pilot requires frozen training passages')
            continue
        if (original.source != record.source or original.text != record.text or original.text_sha256 != record.text_sha256
                or original.passage_start != record.passage_start or original.passage_end != record.passage_end
                or original.passage_language != record.passage_language
                or [e for e in record.entities if e.label in PLACE_LABELS] != original.entities):
            errors.append(f'{record.record_id}: paired locations, passage and source must remain identical')
        if record.annotation_profile != 'context-rich-v1' or record.review_status != 'accepted' or not record.complete:
            errors.append(f'{record.record_id}: complete accepted context-rich review required')
        review = by_review.get(record.record_id)
        if review is None:
            continue
        if review.passage_sha256 != record.text_sha256 or not review.reviewer.strip():
            errors.append(f'{record.record_id}: category review identity/hash mismatch')
        if len({c.category for c in review.categories}) != len(review.categories):
            errors.append(f'{record.record_id}: duplicate categories cannot inflate support')
        for category in review.categories:
            if not category.rationale.strip() or any(not 0 <= s.start < s.end <= len(record.text) or record.text[s.start:s.end] != s.text for s in category.evidence):
                errors.append(f'{record.record_id}: category rationale and unchanged evidence required')
            if category.category == 'shared_observations' and not any(r.scope == 'shared' for r in record.relations):
                errors.append(f'{record.record_id}: shared category requires a reviewed shared relationship')
            if category.category == 'local_exceptions' and not any(r.overrides_relation_id for r in record.relations):
                errors.append(f'{record.record_id}: exception category requires a reviewed override')
            if category.category == 'collective_ranges' and not any(f.kind == 'depth' and f.depth_scope in {'range', 'collective'} for f in record.facts):
                errors.append(f'{record.record_id}: collective/range category requires reviewed depth scope')
            if category.category == 'temporal_transitions' and not (any(f.kind == 'status' and f.value in {'receding','subsided','cleared','rising'} for f in record.facts)
                                                                      or len({f.temporal_role for f in record.facts if f.kind == 'time'}) > 1):
                errors.append(f'{record.record_id}: transition category requires source-supported transition facts')
            if category.category == 'negative_unknown_time' and not (any(f.kind == 'status' and f.value in {'negated','historical','habitual','prevention','forecast','unknown'} for f in record.facts)
                                                                       or not any(f.kind == 'time' and f.temporal_role == 'observation' for f in record.facts)):
                errors.append(f'{record.record_id}: negative/unknown-time category requires supporting annotations')
    counts = Counter(r.passage_language for r in contexts)
    if counts != Counter({'english': 20, 'taglish': 20}):
        errors.append('contextual pilot requires exactly 20 English and 20 Taglish training passages')
    articles = {lang: len({article_key(r.source.url) for r in contexts if r.passage_language == lang}) for lang in ('english','taglish')}
    if any(n < 5 for n in articles.values()):
        errors.append('contextual pilot requires five articles per language')
    support = {category: dict(Counter(r.passage_language for r in contexts if r.record_id in by_review
                                     and any(c.category == category for c in by_review[r.record_id].categories))) for category in CATEGORIES}
    for category, languages in support.items():
        if sum(languages.values()) < 4 or any(languages.get(lang, 0) < 1 for lang in ('english','taglish')):
            errors.append(f'{category}: four examples including both languages required')
    return {'schema_version': 'lanes-context-pilot-v1', 'records': len(contexts), 'languages': dict(counts),
            'source_articles_by_language': articles, 'category_support': support, 'errors': errors,
            'complete': not errors, 'additional_location_samples': 0,
            'scope_is_project_choice_not_optimal_sample_size': True}


def write_contextual_pilot(folder: Path, contexts: list[AnnotationRecord], reviews: list[ContextReview],
                           root: Path, output: Path) -> dict:
    if not output.resolve().is_relative_to((root / 'backend/training/flood_ner/artifacts').resolve()) or output.exists():
        raise ValueError('context pilot destination must be new and under ignored artifacts')
    locations, nlp, _ = load_frozen_cohort(folder)
    report = validate_contextual_pilot(locations, contexts, reviews, nlp)
    if report['errors']:
        raise ValueError('\n'.join(report['errors']))
    output.mkdir(parents=True)
    write_jsonl(output / 'context_annotations.jsonl', contexts)
    (output / 'category_reviews.json').write_bytes(json_bytes([r.model_dump(mode='json') for r in reviews]))
    report['location_manifest_sha256'] = hashlib.sha256((folder / 'partition_manifest.json').read_bytes()).hexdigest()
    report['files'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())}
    (output / 'manifest.json').write_bytes(json_bytes(report))
    return report
