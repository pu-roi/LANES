"""Reviewed research cohort selection with source-bound grouping; no training."""
from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
from typing import Any, Literal

import numpy as np
from pydantic import Field, model_validator
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from .annotation.schema import AnnotationRecord, LABELS, PLACE_LABELS, SourceCapture, StrictRecord, text_hash
from .annotation.validation import validate_corpus
from .collection import article_key, body_fingerprint, publication_date, publisher_for, shingles, validate_reviewed, verify_capture_files
from .export import TOKENIZER_NAME, corpus_tokenizer
from .policy import CoveragePolicy, policy_report
from .sources import json_bytes, write_jsonl
from .window import LEGACY_WINDOW, PublicationWindow

TARGETS = {'train': {'english': 140, 'taglish': 140},
           'dev': {'english': 30, 'taglish': 30}, 'test': {'english': 30, 'taglish': 30}}


class GroupEvidence(StrictRecord):
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    reason: str = Field(min_length=1)


class GroupReview(StrictRecord):
    schema_version: Literal['lanes-flood-ner-group-review-v1'] = 'lanes-flood-ner-group-review-v1'
    source_id: str = Field(min_length=1)
    capture_version: str = Field(min_length=1)
    text_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    publication_date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    article_group: str = Field(min_length=1)
    event_group: str = Field(min_length=1)
    syndication_group: str = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    review_revision: str = Field(min_length=1)
    evidence: list[GroupEvidence] = Field(min_length=1)
    notes: list[str] = Field(min_length=1)

    @model_validator(mode='after')
    def substantive_review(self) -> GroupReview:
        values = [self.source_id, self.capture_version, self.article_group, self.event_group,
                  self.syndication_group, self.reviewer, self.review_revision, *self.notes,
                  *(e.reason for e in self.evidence)]
        if any(not value.strip() for value in values):
            raise ValueError('review identity, grouping and rationale must not be blank')
        return self


def _groups(records: list[AnnotationRecord]) -> list[int]:
    parents = list(range(len(records)))

    def find(i: int) -> int:
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    seen: dict[tuple[str, str], int] = {}
    for i, record in enumerate(records):
        source = record.source
        keys = [('article', article_key(source.url)), ('body', source.text_sha256),
                ('reviewed_article', source.article_group), ('event', source.event_group),
                ('syndication', source.syndication_group)]
        for key, value in keys:
            if value:
                token = (key, value)
                if token in seen:
                    parents[find(i)] = find(seen[token])
                seen[token] = i
    roots = [find(i) for i in range(len(records))]
    ordered = {root: i for i, root in enumerate(sorted(set(roots)))}
    return [ordered[root] for root in roots]


def _assign(records: list[AnnotationRecord], groups: list[int], pilot_ids: set[str],
            targets: dict[str, dict[str, int]], publisher_cap: int, minimum_publishers: int,
            policy: CoveragePolicy | None = None, *, selection_time_limit: int = 60) -> dict[str, str]:
    """Select samples and assign each connected group to at most one split."""
    if type(selection_time_limit) is not int or not 1 <= selection_time_limit <= 3600:
        raise ValueError('selection time limit must be an integer between 1 and 3600 seconds')
    splits = tuple(targets)
    publishers = sorted({publisher_for(r.source.url) for r in records})
    n, g, p = len(records), len(set(groups)), len(publishers)
    size = n * len(splits) + g * len(splits) + p
    # Article-support indicators exist only for source articles containing the label.
    article_bits = {}
    if policy:
        for s in range(len(splits)):
            for language in ('english', 'taglish'):
                for label in sorted(PLACE_LABELS):
                    articles = sorted({article_key(r.source.url) for r in records
                                       if r.passage_language == language and any(e.label == label for e in r.entities)})
                    for article in articles:
                        article_bits[s, language, label, article] = size
                        size += 1
    rows: list[dict[int, float]] = []
    lower: list[float] = []
    upper: list[float] = []

    def constrain(values: dict[int, float], lo: float, hi: float) -> None:
        rows.append(values)
        lower.append(lo)
        upper.append(hi)

    def x(i: int, s: int) -> int:
        return i * len(splits) + s

    def y(group: int, s: int) -> int:
        return n * len(splits) + group * len(splits) + s

    for i in range(n):
        constrain({x(i, s): 1 for s in range(len(splits))}, 0, 1)
        for s in range(len(splits)):
            constrain({x(i, s): 1, y(groups[i], s): -1}, -np.inf, 0)
        if records[i].record_id in pilot_ids:
            constrain({x(i, splits.index('train')): 1}, 1, 1)
    for group in range(g):
        constrain({y(group, s): 1 for s in range(len(splits))}, 0, 1)
        if policy:
            values = {x(i, s): 1 for i in range(n) if groups[i] == group for s in range(len(splits))}
            constrain(values, 0, policy.group_max)
            for s in range(len(splits)):
                # No empty group may inflate the per-partition group minimum.
                constrain({y(group, s): 1} | {x(i, s): -1 for i in range(n) if groups[i] == group}, -np.inf, 0)
    for s, split in enumerate(splits):
        for language, count in targets[split].items():
            constrain({x(i, s): 1 for i, r in enumerate(records) if r.passage_language == language}, count, count)
    for j, publisher in enumerate(publishers):
        values = {x(i, s): 1 for i, r in enumerate(records) if publisher_for(r.source.url) == publisher
                  for s in range(len(splits))}
        bit = n * len(splits) + g * len(splits) + j
        constrain(values, 0, policy.publisher_max_total if policy else publisher_cap)
        # A publisher presence bit may be one only when at least one sample is selected.
        constrain(values | {bit: -1}, 0, np.inf)
        if policy:
            # Every selected publisher activates its minimum in BOTH languages.
            constrain(values | {bit: -policy.publisher_max_total}, -np.inf, 0)
            for language in ('english', 'taglish'):
                per_language = {x(i, s): 1 for i, r in enumerate(records)
                                if publisher_for(r.source.url) == publisher and r.passage_language == language
                                for s in range(len(splits))}
                constrain(per_language, 0, policy.publisher_max_per_language)
                constrain(per_language | {bit: -policy.publisher_min_per_language}, 0, np.inf)
    constrain({n * len(splits) + g * len(splits) + j: 1 for j in range(p)},
              policy.minimum_publishers if policy else minimum_publishers, np.inf)
    if policy:
        for article in sorted({article_key(r.source.url) for r in records}):
            constrain({x(i, s): 1 for i, r in enumerate(records) if article_key(r.source.url) == article
                       for s in range(len(splits))}, 0, policy.article_max)
        for s, split in enumerate(splits):
            constrain({y(group, s): 1 for group in range(g)}, policy.groups_min_per_partition, np.inf)
            for language in ('english', 'taglish'):
                for label in sorted(PLACE_LABELS):
                    support = policy.support(split, label)
                    indices = [i for i, r in enumerate(records) if r.passage_language == language
                               and any(e.label == label for e in r.entities)]
                    constrain({x(i, s): sum(e.label == label for e in records[i].entities) for i in indices}, support.spans, np.inf)
                    constrain({x(i, s): 1 for i in indices}, support.passages, np.inf)
                    bits = {article: bit for (ss, lang, lab, article), bit in article_bits.items()
                            if (ss, lang, lab) == (s, language, label)}
                    constrain({bit: 1 for bit in bits.values()}, support.articles, np.inf)
                    for article, bit in bits.items():
                        constrain({bit: 1} | {x(i, s): -1 for i in indices if article_key(records[i].source.url) == article}, -np.inf, 0)
    matrix = lil_matrix((len(rows), size), dtype=float)
    for i, row in enumerate(rows):
        for j, value in row.items():
            matrix[i, j] = value
    # Stable source/record order and explicit objective; no random passage splitting.
    objective = np.zeros(size)
    for i in range(n):
        for s in range(len(splits)):
            objective[x(i, s)] = (1 if records[i].entities else 3) + (i + 1) / (n + 1) + ((i + 1) * (s + 1)) / (n + 1) ** 3
    result = milp(objective, integrality=np.ones(size), bounds=Bounds(0, 1),
                  constraints=LinearConstraint(matrix.tocsc(), lower, upper),
                  options={'time_limit': selection_time_limit, 'mip_rel_gap': 0})
    if not result.success or result.x is None:
        if result.status == 2:
            raise ValueError('exact grouped cohort is infeasible under the reviewed inputs and hard constraints; solver status 2: ' + str(result.message))
        raise ValueError('exact grouped selection remains unresolved; solver status ' + str(result.status) + ': ' + str(result.message))
    return {record.record_id: splits[s] for i, record in enumerate(records)
            for s in range(len(splits)) if result.x[x(i, s)] > .5}


def build_cohort(records: list[AnnotationRecord], reviews: list[GroupReview], sources: list[SourceCapture],
                 root: Path, output: Path, *, pilot_ids: set[str] | None = None,
                 targets: dict[str, dict[str, int]] | None = None, publisher_cap: int = 200,
                 minimum_publishers: int = 3, window: PublicationWindow = LEGACY_WINDOW,
                 tokenizer: str = TOKENIZER_NAME, policy: CoveragePolicy | None = None,
                 news_entries: list[dict[str, Any]] | None = None,
                 report_infeasible: bool = False,
                 collection_budget_metadata: dict[str, Any] | None = None,
                 selection_time_limit: int = 60) -> dict[str, Any]:
    if type(selection_time_limit) is not int or not 1 <= selection_time_limit <= 3600:
        raise ValueError('selection time limit must be an integer between 1 and 3600 seconds')
    targets = TARGETS if targets is None else targets
    pilot_ids = set() if pilot_ids is None else pilot_ids
    if (set(targets) != {'train', 'dev', 'test'} or any(set(v) != {'english', 'taglish'} for v in targets.values())
            or any(type(n) is not int or n < 1 for v in targets.values() for n in v.values())
            or type(publisher_cap) is not int or publisher_cap < 1
            or type(minimum_publishers) is not int or minimum_publishers < 1):
        raise ValueError('positive exact English/Taglish targets and publisher limits required')
    artifacts = (root / 'backend/training/flood_ner/artifacts').resolve()
    if not output.resolve().is_relative_to(artifacts):
        raise ValueError('full cohort data must stay under ignored training artifacts')
    if output.exists() and any(output.iterdir()):
        raise ValueError('cohort destination must be empty; preserve frozen selections')
    nlp = corpus_tokenizer(tokenizer)
    tokenizer_bytes = nlp.tokenizer.to_bytes()
    errors = validate_corpus(records, nlp)
    by_version = {s.capture_version: s for s in sources}
    verified_days = {}
    if news_entries is not None:
        errors += validate_reviewed(news_entries, by_version, window=window) + verify_capture_files(news_entries, root)
        verified_days = {e['capture_version']: publication_date(e['publication_date'])
                         for e in news_entries if e.get('status') == 'accepted'}
    group_reviews: dict[str, GroupReview] = {}
    for review in reviews:
        source = by_version.get(review.capture_version)
        if (source is None or source.source_id != review.source_id or source.text_sha256 != review.text_sha256
                or review.capture_version in group_reviews):
            errors.append('group review must bind uniquely to inventoried source identity/hash')
            continue
        if any(value.casefold().startswith(('provisional:', 'review-needed:', 'unresolved:'))
               for value in (review.article_group, review.event_group, review.syndication_group)):
            errors.append('group review may not retain provisional identities')
        reviewed_day = publication_date(review.publication_date)
        captured_day = (publication_date(source.published_at.isoformat()) if source.published_at else
                        verified_days.get(source.capture_version))
        if not window.contains(reviewed_day) or captured_day != reviewed_day:
            errors.append('cohort needs a corroborated publication date in the historical window; legacy unknown dates stay excluded')
        for evidence in review.evidence:
            if not 0 <= evidence.start < evidence.end <= len(source.text) or text_hash(source.text[evidence.start:evidence.end]) != evidence.sha256:
                errors.append('group evidence must match frozen source offsets/hash')
        group_reviews[review.capture_version] = review
    for record in records:
        source = by_version.get(record.source.capture_version)
        if source is None or source.model_dump() != record.source.model_dump():
            errors.append(f'{record.record_id}: annotation source must match immutable inventory')
        if news_entries is not None and record.source.capture_version not in verified_days:
            errors.append(f'{record.record_id}: annotation needs accepted capture/publication evidence')
    if errors:
        raise ValueError('\n'.join(errors))
    eligible: list[AnnotationRecord] = []
    exclusions: list[dict[str, str]] = []
    comparisons: list[tuple[str, int, int, str, set[tuple[str, ...]]]] = []
    for record in sorted(records, key=lambda r: (r.record_id not in pilot_ids, -len(r.text), r.record_id)):
        reasons = []
        if record.annotation_profile != 'location-only-v1': reasons.append('wrong_profile')
        if record.quality != 'silver' or record.source.origin != 'captured_original': reasons.append('not_source_backed_silver')
        if record.review_status != 'accepted' or not record.complete: reasons.append('incomplete_or_unresolved_annotation')
        if record.passage_language not in {'english', 'taglish'}: reasons.append('outside_language_scope')
        if publisher_for(record.source.url) is None: reasons.append('publisher_identity_unconfirmed')
        review = group_reviews.get(record.source.capture_version)
        if review is None: reasons.append('group_review_missing')
        key = article_key(record.source.url)
        fingerprint, tokens = body_fingerprint(record.text), shingles(record.text)
        for previous_key, start, end, previous_fingerprint, previous_tokens in comparisons:
            if (previous_key == key
                    and max(start, record.passage_start) < min(end, record.passage_end)):
                reasons.append('overlapping_article_passage')
                break
            intersection = len(tokens & previous_tokens)
            union = len(tokens) + len(previous_tokens) - intersection
            if (fingerprint == previous_fingerprint
                    or (tokens and previous_tokens and intersection / union >= .85)):
                reasons.append('duplicate_or_near_copy_passage')
                break
        if reasons:
            exclusions.append({'record_id': record.record_id, 'reason': ','.join(reasons)})
            continue
        assert review is not None
        # Derived annotation overlay; original captures and input records stay unchanged.
        derived = record.model_copy(deep=True)
        derived.source = record.source.model_copy(update={k: getattr(review, k)
                    for k in ('article_group', 'event_group', 'syndication_group')})
        derived.notes = [*record.notes, f'Grouping overlay: {review.review_revision}; original capture metadata retained separately.']
        eligible.append(derived)
        comparisons.append((key, record.passage_start, record.passage_end, fingerprint, tokens))
    eligible.sort(key=lambda r: r.record_id)
    if not pilot_ids <= {r.record_id for r in eligible}:
        raise ValueError('retained pilot IDs must be eligible, reviewed input records')
    groups = _groups(eligible)
    available = Counter(r.passage_language for r in eligible)
    pool_report = policy_report(eligible, groups, policy, pool=True) if policy else None
    try:
        if any(available[language] < sum(v[language] for v in targets.values()) for language in ('english','taglish')):
            raise ValueError(f'exact cohort infeasible: insufficient reviewed language coverage {dict(available)}')
        if pool_report and not pool_report['passed']:
            raise ValueError('exact cohort infeasible: necessary pool coverage quotas fail')
        assignments = _assign(eligible, groups, pilot_ids, targets, publisher_cap, minimum_publishers, policy,
                              selection_time_limit=selection_time_limit)
    except ValueError as exc:
        if not report_infeasible:
            raise
        report = {'schema_version': 'lanes-flood-ner-infeasibility-v1', 'revision_complete': False,
                  'reason': str(exc), 'reviewed_pool': len(eligible), 'languages': dict(available),
                  'targets': targets, 'publication_window': window.as_list(), 'tokenizer': tokenizer,
                  'coverage': pool_report, 'partitions_frozen': False, 'annotation_accepted': len(eligible),
                  'selected_samples': 0, 'training_admitted': 0, 'exported_samples': 0}
        if collection_budget_metadata:
            report['collection_budget'] = collection_budget_metadata
        if selection_time_limit != 60:
            report['selection_time_limit_seconds'] = selection_time_limit
        output.mkdir(parents=True, exist_ok=True)
        write_jsonl(output / 'reviewed_pool.jsonl', eligible)
        (output / 'tokenizer.bin').write_bytes(tokenizer_bytes)
        (output / 'infeasibility.json').write_bytes(json_bytes(report))
        (output / 'exclusion_register.json').write_bytes(json_bytes(exclusions))
        return report
    selected = [r.model_copy(update={'split': assignments[r.record_id]}) for r in eligible if r.record_id in assignments]
    errors = validate_corpus(selected, nlp)
    counts = {split: dict(Counter(r.passage_language for r in selected if r.split == split)) for split in targets}
    publisher_counts = dict(Counter(publisher_for(r.source.url) for r in selected))
    selected_policy = policy_report(selected, _groups(selected), policy) if policy else None
    effective_minimum = policy.minimum_publishers if policy else minimum_publishers
    effective_cap = policy.publisher_max_total if policy else publisher_cap
    if (errors or counts != targets or len(publisher_counts) < effective_minimum or max(publisher_counts.values()) > effective_cap
            or (selected_policy and not selected_policy['passed'])):
        raise ValueError('selected cohort failed exact counts, publisher constraints or group leakage validation')
    exclusions += [{'record_id': r.record_id, 'reason': 'eligible_reserve_not_selected'}
                   for r in eligible if r.record_id not in assignments]
    register = [{'record_id': r.record_id, 'source_id': r.source.source_id,
                 'source_version': r.source.capture_version, 'source_sha256': r.source.text_sha256,
                 'passage_start': r.passage_start, 'passage_end': r.passage_end, 'passage_sha256': r.text_sha256,
                 'publisher': publisher_for(r.source.url), 'language': r.passage_language, 'split': r.split,
                 'quality': r.quality, 'teacher': r.teacher, 'reviewer': r.reviewer,
                 'annotation_revision': r.annotation_revision, 'entities': len(r.entities),
                 'article_group': r.source.article_group, 'event_group': r.source.event_group,
                 'syndication_group': r.source.syndication_group} for r in selected]
    manifest = {'schema_version': 'lanes-flood-ner-cohort-v1', 'profile': 'location-only-v1',
                'labels': [label for label in LABELS if label in PLACE_LABELS],
                'selection': 'stable source/record order; prefer entity-bearing records then solve exact grouped constraints',
                'annotation_schema_sha256': hashlib.sha256(json_bytes(AnnotationRecord.model_json_schema())).hexdigest(),
                'tokenizer': tokenizer,
                'tokenizer_sha256': hashlib.sha256(tokenizer_bytes).hexdigest(),
                'counts': counts, 'total': len(selected), 'publishers': publisher_counts,
                'eligible_connected_groups': len(set(groups)),
                'selected_connected_groups': len({groups[i] for i,r in enumerate(eligible) if r.record_id in assignments}),
                'retained_pilot_ids': sorted(pilot_ids),
                'training_admitted': sum(r.source.admission_status == 'training_admitted' for r in selected),
                'export_holds': sorted({reason for r in selected for reason in
                    (['source_reuse_unresolved'] if r.source.reuse_status != 'allowed' else []) +
                    (['source_not_training_admitted'] if r.source.admission_status != 'training_admitted' else [])}),
                'group_overlay_preserves_original_captures': True,
                'independently_verified_gold': 0, 'model_trained': False}
    if window != LEGACY_WINDOW or policy is not None:
        manifest['publication_window'] = window.as_list()
    if selection_time_limit != 60:
        manifest['selection_time_limit_seconds'] = selection_time_limit
    if policy:
        manifest['coverage_policy'] = policy.model_dump(mode='json')
        manifest['policy_checks'] = selected_policy
    if collection_budget_metadata:
        manifest['collection_budget'] = collection_budget_metadata
    output.mkdir(parents=True, exist_ok=True)
    (output / 'annotation_schema.json').write_bytes(json_bytes(AnnotationRecord.model_json_schema()))
    (output / 'tokenizer.bin').write_bytes(tokenizer_bytes)
    if collection_budget_metadata:
        (output / 'collection_budget.json').write_bytes(json_bytes(collection_budget_metadata))
    write_jsonl(output / 'grouped_annotations.jsonl', selected)
    for name, value in [('selection_register.json', register), ('exclusion_register.json', exclusions),
                        ('group_reviews.json', [r.model_dump(mode='json') for r in sorted(reviews, key=lambda r: r.capture_version)]),
                        ('partition_manifest.json', manifest)]:
        (output / name).write_bytes(json_bytes(value))
    (output / 'coverage.json').write_bytes(json_bytes(manifest | {
        'distinct_articles': len({article_key(r.source.url) for r in selected}),
        'entity_labels': dict(Counter(e.label for r in selected for e in r.entities)),
        'empty_entity_records': sum(not r.entities for r in selected),
        'publisher_languages': {p: dict(Counter(r.passage_language for r in selected if publisher_for(r.source.url)==p))
                               for p in sorted(publisher_counts)},
        'empty_entities_mean_only_no_supported_place_labels': True,
        'annotation_accepted': len(selected), 'exported_samples': 0}))
    manifest['files'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())
                         if p.name != 'partition_manifest.json'}
    (output / 'partition_manifest.json').write_bytes(json_bytes(manifest))
    return manifest
