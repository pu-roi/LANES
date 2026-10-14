"""Explicit editorial decisions over immutable captures; no annotation or admission."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, model_validator

from .annotation.schema import Language, SourceCapture, StrictRecord, text_hash
from .preparation import CandidatePassage, candidate_identity
from .sources import json_bytes


class ReviewRange(StrictRecord):
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    reason: str = Field(min_length=1)


class Selection(ReviewRange):
    language: Language
    language_reason: str = Field(min_length=1)


class Exclusion(ReviewRange):
    kind: Literal['publisher_metadata', 'publisher_interface', 'related_story', 'caption']


class ContextNote(ReviewRange):
    kind: Literal['embedded_reporting', 'caption', 'measurement_role', 'scope_warning', 'language_exception']


class EditorialReview(StrictRecord):
    schema_version: Literal['lanes-flood-ner-editorial-v1'] = 'lanes-flood-ner-editorial-v1'
    candidate_id: str = Field(pattern=r'^candidate-[a-f0-9]{20}$')
    source_id: str = Field(min_length=1)
    capture_version: str = Field(min_length=1)
    source_text_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    reviewer: str = Field(min_length=1)
    review_kind: Literal['ai_assisted', 'human']
    reviewed_at: datetime
    review_revision: str = Field(min_length=1)
    selections: list[Selection] = Field(min_length=1)
    exclusions: list[Exclusion] = Field(default_factory=list)
    context_notes: list[ContextNote] = Field(default_factory=list)
    notes: list[str] = Field(min_length=1)

    @model_validator(mode='after')
    def qualified_metadata(self) -> EditorialReview:
        if self.reviewed_at.utcoffset() is None:
            raise ValueError('editorial review time requires a timezone')
        if (any(not value.strip() for value in [self.reviewer, self.review_revision, *self.notes])
                or any(not r.reason.strip() for r in [*self.selections, *self.exclusions, *self.context_notes])
                or any(not s.language_reason.strip() for s in self.selections)):
            raise ValueError('editorial review reasons and identity cannot be blank')
        return self


def validate_review(candidate: CandidatePassage, review: EditorialReview) -> None:
    """Account for all non-whitespace source text; never concatenate across omissions."""
    CandidatePassage.model_validate(candidate.model_dump())
    EditorialReview.model_validate(review.model_dump())
    source = candidate.source
    if (review.candidate_id != candidate.candidate_id or review.source_id != source.source_id
            or review.capture_version != source.capture_version
            or review.source_text_sha256 != source.text_sha256):
        raise ValueError('editorial review must match the original candidate/source identity')
    for span in [*review.selections, *review.exclusions, *review.context_notes]:
        if (not 0 <= span.start < span.end <= len(source.text)
                or text_hash(source.text[span.start:span.end]) != span.sha256):
            raise ValueError('editorial range must match unchanged source offsets/hash')
    for selection in review.selections:
        if not source.text[selection.start:selection.end].strip():
            raise ValueError('editorial selection cannot contain only whitespace')
    ranges = sorted([*review.selections, *review.exclusions], key=lambda r: (r.start, r.end))
    end = 0
    for span in ranges:
        if span.start < end:
            raise ValueError('editorial selections/exclusions must not overlap')
        if source.text[end:span.start].strip():
            raise ValueError('editorial review must account for every non-whitespace source character')
        end = span.end
    if source.text[end:].strip():
        raise ValueError('editorial review must account for every non-whitespace source character')


def build_editorial_queue(candidates: list[CandidatePassage], reviews: list[EditorialReview],
                         sources: list[SourceCapture], root: Path, output: Path) -> dict[str, Any]:
    """Produce research-only context blocks and metadata, retaining original decisions."""
    if not candidates or len(candidates) != len(reviews):
        raise ValueError('one editorial review is required for each original candidate')
    identities = [c.candidate_id for c in candidates]
    review_ids = [r.candidate_id for r in reviews]
    articles = [c.article_key for c in candidates]
    if (len(set(identities)) != len(identities) or len(set(review_ids)) != len(review_ids)
            or set(identities) != set(review_ids) or len(set(articles)) != len(articles)):
        raise ValueError('editorial candidate/article identities must be unique and reviews complete')
    by_version: dict[str, SourceCapture] = {}
    for source in sources:
        SourceCapture.model_validate(source.model_dump())
        if source.capture_version in by_version and by_version[source.capture_version] != source:
            raise ValueError('conflicting inventoried capture version')
        by_version[source.capture_version] = source
    by_review = {r.candidate_id: r for r in reviews}
    blocks = []
    metadata = []
    restored_cues = []
    for candidate in sorted(candidates, key=lambda c: c.article_key):
        if by_version.get(candidate.source.capture_version) != candidate.source:
            raise ValueError('editorial candidate must match the inventoried immutable capture')
        review = by_review[candidate.candidate_id]
        validate_review(candidate, review)
        selections = sorted(review.selections, key=lambda s: s.start)
        for selection in selections:
            text = candidate.source.text[selection.start:selection.end]
            holds = ['reuse_assessment_pending', 'event_syndication_review_pending', 'annotation_not_started']
            if candidate.source.reuse_status == 'allowed':
                holds.remove('reuse_assessment_pending')
            if review.review_kind != 'human':
                holds.append('research_team_manual_review_pending')
            if selection.language == 'unknown':
                holds.append('unsupported_or_unresolved_language_review_pending')
            elif selection.language == 'tagalog':
                holds.append('outside_paper_english_taglish_scope')
            if candidate.source.raw_sha256 is None or candidate.source.captured_at is None:
                holds.append('legacy_original_html_retrieval_gap')
            if len(selections) > 1:
                holds.append('cross_block_context_review_pending')
            if any(n.kind == 'measurement_role' and n.start < selection.end and n.end > selection.start
                   for n in review.context_notes):
                holds.append('measurement_role_annotation_review_pending')
            block = {'schema_version': 'lanes-flood-ner-editorial-block-v1',
                     'block_id': candidate_identity(candidate.source, selection.start, selection.end),
                     'original_candidate_id': candidate.candidate_id, 'article_key': candidate.article_key,
                     'source': candidate.source.model_dump(mode='json'),
                     'passage_start': selection.start, 'passage_end': selection.end,
                     'text': text, 'text_sha256': selection.sha256,
                     'passage_language': selection.language, 'language_reason': selection.language_reason,
                     'reviewer': review.reviewer, 'review_kind': review.review_kind,
                     'review_revision': review.review_revision, 'reviewed_at': review.reviewed_at.isoformat(),
                     'selection_reason': selection.reason, 'source_review_notes': candidate.source_review_notes,
                     'context_source_sha256': candidate.source.text_sha256,
                     'sibling_block_ids': [candidate_identity(candidate.source, s.start, s.end) for s in selections
                                           if s != selection],
                     'proposed_event_group': candidate.proposed_event_group,
                     'proposed_syndication_group': candidate.proposed_syndication_group,
                     'context_notes': [n.model_dump() for n in review.context_notes
                                       if n.start < selection.end and n.end > selection.start],
                     'admission_status': 'research_only', 'hold_reasons': holds}
            blocks.append(block)
            metadata.append({k: v for k, v in block.items() if k not in {'source', 'text'}} |
                            {'source_id': candidate.source.source_id,
                             'source_version': candidate.source.capture_version,
                             'source_url': candidate.source.url, 'characters': len(text)})
        # Each original cue must be retained or explicitly accounted for as excluded evidence.
        for cue in candidate.case_cues:
            start = candidate.passage_start + cue['start']
            end = candidate.passage_start + cue['end']
            if not any(s.start <= start < end <= s.end for s in selections):
                exclusion = next((e for e in review.exclusions if e.start <= start < end <= e.end), None)
                restored_cues.append({'source_id': candidate.source.source_id, 'role': cue['role'],
                                      'source_version': candidate.source.capture_version,
                                      'start': start, 'end': end, 'sha256': cue['sha256'],
                                      'disposition': 'explicitly_excluded' if exclusion else 'cross_block_review',
                                      'exclusion_kind': exclusion.kind if exclusion else None,
                                      'reason': exclusion.reason if exclusion else 'Cue crosses reviewed context boundaries.'})
    # Validate the complete packet before writing; earlier queues are immutable.
    artifacts = (root / 'backend/training/flood_ner/artifacts').resolve()
    if not output.resolve().is_relative_to(artifacts):
        raise ValueError('editorial bodies must stay under ignored training artifacts')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('editorial destination must be empty; preserve earlier queues')
    counts = Counter(b['passage_language'] for b in blocks)
    report = {'schema_version': 'lanes-flood-ner-editorial-report-v1',
              'source_articles': len(candidates), 'editorial_reviews': len(reviews),
              'context_blocks': len(blocks), 'passage_languages': dict(counts),
              'review_kinds': dict(Counter(r.review_kind for r in reviews)),
              'paper_language_compatible_blocks': counts['english'] + counts['taglish'],
              'paper_dataset_target': {'total': 400, 'train': 280, 'dev': 60, 'test': 60},
              'excluded_ranges': dict(Counter(e.kind for r in reviews for e in r.exclusions)),
              'hold_reasons': dict(Counter(h for b in blocks for h in b['hold_reasons'])),
              'human_reviewed_articles': sum(r.review_kind == 'human' for r in reviews),
              'annotated_passages': 0, 'training_admitted': 0, 'assigned_splits': 0,
              'note': 'Editorial blocks are context for manual annotation, not independent accepted training samples.'}
    output.mkdir(parents=True, exist_ok=True)
    (output / 'context_blocks.jsonl').write_bytes(
        ''.join(json.dumps(b, ensure_ascii=False, sort_keys=True) + '\n' for b in blocks).encode('utf-8'))
    (output / 'block_register.json').write_bytes(json_bytes(metadata))
    (output / 'editorial_reviews.json').write_bytes(json_bytes([r.model_dump(mode='json') for r in reviews]))
    (output / 'cue_dispositions.json').write_bytes(json_bytes(restored_cues))
    (output / 'readiness.json').write_bytes(json_bytes(report))
    return report
