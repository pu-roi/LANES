"""Versioned collection quotas, independent of model accuracy and source admission."""
from collections import Counter
from typing import Literal

from pydantic import Field

from .annotation.schema import AnnotationRecord, PLACE_LABELS, StrictRecord
from .collection import article_key, publisher_for


class Support(StrictRecord):
    spans: int = Field(ge=1)
    passages: int = Field(ge=1)
    articles: int = Field(ge=1)


class CoveragePolicy(StrictRecord):
    schema_version: Literal['lanes-flood-ner-coverage-v1'] = 'lanes-flood-ner-coverage-v1'
    minimum_publishers: int = Field(default=3, ge=1)
    publisher_min_per_language: int = Field(default=25, ge=1)
    publisher_max_total: int = Field(default=160, ge=1)
    publisher_max_per_language: int = Field(default=100, ge=1)
    article_max: int = Field(default=8, ge=1)
    group_max: int = Field(default=80, ge=1)
    groups_min_per_partition: int = Field(default=5, ge=1)
    train: Support = Field(default_factory=lambda: Support(spans=20, passages=10, articles=5))
    holdout: Support = Field(default_factory=lambda: Support(spans=10, passages=5, articles=3))
    road_train: Support = Field(default_factory=lambda: Support(spans=60, passages=30, articles=10))
    road_holdout: Support = Field(default_factory=lambda: Support(spans=20, passages=10, articles=5))

    def support(self, split: str, label: str) -> Support:
        if label == 'ROAD':
            return self.road_train if split == 'train' else self.road_holdout
        return self.train if split == 'train' else self.holdout


def label_support(records: list[AnnotationRecord], label: str) -> dict[str, int]:
    positive = [r for r in records if any(e.label == label for e in r.entities)]
    return {'spans': sum(e.label == label for r in positive for e in r.entities),
            'passages': len(positive), 'articles': len({article_key(r.source.url) for r in positive})}


def policy_report(records: list[AnnotationRecord], groups: list[int], policy: CoveragePolicy,
                  *, pool: bool = False) -> dict:
    """Pool deficits are necessary lower bounds, never a claim of partition feasibility."""
    if len(records) != len(groups):
        raise ValueError('one connected-group identity required per record')
    failures = []
    pubs = sorted({publisher_for(r.source.url) for r in records})
    publisher_languages = {p: dict(Counter(r.passage_language for r in records if publisher_for(r.source.url) == p)) for p in pubs}
    qualified_publishers = sum(all(counts.get(lang, 0) >= policy.publisher_min_per_language
                                   for lang in ('english', 'taglish')) for counts in publisher_languages.values())
    if qualified_publishers < policy.minimum_publishers:
        failures.append({'quota': 'publishers_with_both_languages', 'required': policy.minimum_publishers, 'available': qualified_publishers})
    coverage = {}
    for split in (('pool',) if pool else ('train', 'dev', 'test')):
        coverage[split] = {}
        for language in ('english', 'taglish'):
            rows = [r for r in records if r.passage_language == language and (pool or r.split == split)]
            coverage[split][language] = {}
            for label in sorted(PLACE_LABELS):
                support = label_support(rows, label)
                coverage[split][language][label] = support
                needed = (policy.support(split, label).model_dump() if not pool else
                          {k: policy.support('train', label).model_dump()[k] + 2 * policy.support('dev', label).model_dump()[k]
                           for k in ('spans', 'passages', 'articles')})
                for metric in needed:
                    if support[metric] < needed[metric]:
                        failures.append({'quota': 'label_support', 'partition': split, 'language': language,
                                         'label': label, 'metric': metric, 'required': needed[metric], 'available': support[metric]})
    if not pool:
        for pub, counts in publisher_languages.items():
            for lang in ('english', 'taglish'):
                if not policy.publisher_min_per_language <= counts.get(lang, 0) <= policy.publisher_max_per_language:
                    failures.append({'quota': 'publisher_language', 'publisher': pub, 'language': lang, 'actual': counts.get(lang, 0)})
            if sum(counts.values()) > policy.publisher_max_total:
                failures.append({'quota': 'publisher_total', 'publisher': pub, 'actual': sum(counts.values())})
        for kind, counts, limit in [('article', Counter(article_key(r.source.url) for r in records), policy.article_max),
                                    ('group', Counter(groups), policy.group_max)]:
            failures.extend({'quota': kind + '_cap', 'identity': str(key), 'actual': count, 'maximum': limit}
                            for key, count in sorted(counts.items()) if count > limit)
        for split in ('train', 'dev', 'test'):
            count = len({g for r, g in zip(records, groups) if r.split == split})
            if count < policy.groups_min_per_partition:
                failures.append({'quota': 'partition_groups', 'partition': split, 'actual': count, 'minimum': policy.groups_min_per_partition})
        assignments = {}
        for r, group in zip(records, groups):
            if group in assignments and assignments[group] != r.split:
                failures.append({'quota': 'group_leakage', 'identity': group})
            assignments[group] = r.split
    return {'policy': policy.model_dump(mode='json'), 'mode': 'necessary_pool_checks' if pool else 'selected_cohort',
            'publisher_languages': publisher_languages, 'coverage': coverage, 'failures': failures,
            'passed': not failures, 'model_accuracy_measured': False}
