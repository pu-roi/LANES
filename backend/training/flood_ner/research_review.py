"""Source-bound silver-reference review. Never admits, seals, exports or trains.

Only aggregate models below may cross the isolated curator boundary. Captures,
references, evidence paths, exclusions and correction histories remain private.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import hashlib
import itertools
import json
from pathlib import Path
import re
from typing import Annotated, Any, Callable, Iterable, Literal, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .annotation.schema import AnnotationRecord, Entity, PLACE_LABELS, SourceCapture, text_hash
from .annotation.validation import validate_record
from .collection import article_key

REQUIRED_GATES = frozenset({'source_use', 'publication', 'language', 'history', 'exposure', 'grouping'})
TARGET = (27, 3, 27, 3)
_GUARD_EXECUTION = object()


class ReviewError(ValueError):
    """Private diagnostics must not be forwarded as coordinator output."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReviewError(message)


def file_hash(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


@dataclass(frozen=True)
class FileBinding:
    path: Path
    sha256: str

    def verify(self) -> None:
        require(bool(re.fullmatch(r'[a-f0-9]{64}', self.sha256)), 'invalid evidence digest')
        require(self.path.is_file() and file_hash(self.path) == self.sha256, 'missing or stale evidence')


def validate_reference(proposal: Mapping[str, Any], source: SourceCapture, nlp: Any, *,
                       ignored_occurrences: Sequence[Mapping[str, Any]] = ()) -> AnnotationRecord:
    """Convert explicit, complete source occurrences; never infer an empty reference.

    An omission is a separately reviewed non-entity occurrence, with an exact
    span and reason. A longer annotated entity can cover a shorter literal.
    Matching spellings never automatically acquire the same geographic type.
    """
    require(proposal.get('annotation_reference_complete') is True, 'incomplete reference')
    raw = proposal.get('expected_entities')
    require(isinstance(raw, list), 'unknown reference is not a negative')
    negative = proposal.get('candidate_negative', proposal.get('is_negative'))
    require(type(negative) is bool and negative == (not raw), 'contradictory or absent negative flag')
    if 'is_negative' in proposal:
        require(type(proposal['is_negative']) is bool and proposal['is_negative'] == negative,
                'contradictory negative flags')
    require(bool(proposal.get('annotator')) and bool(proposal.get('reviewer')), 'review identities required')
    text = proposal.get('text')
    require(isinstance(text, str) and bool(text), 'passage text required')
    require(proposal.get('text_sha256') == text_hash(text), 'passage hash mismatch')
    require(proposal.get('source_text_sha256') == source.text_sha256, 'source text binding mismatch')
    require(isinstance(source.raw_sha256, str) and bool(re.fullmatch(r'[a-f0-9]{64}', source.raw_sha256)),
            'captured source raw hash required')
    require(proposal.get('source_raw_sha256') == source.raw_sha256, 'source raw binding mismatch')
    entities = []
    for i, e in enumerate(raw):
        require(isinstance(e, dict) and set(e) == {'start', 'end', 'label', 'text'}, 'explicit entity spans required')
        require(e['label'] in PLACE_LABELS, 'unsupported place type')
        entities.append(Entity(id=f'e{i + 1}', **e))
    omissions = []
    for occurrence in ignored_occurrences:
        start, end = occurrence.get('start'), occurrence.get('end')
        require(type(start) is int and type(end) is int and 0 <= start < end <= len(text), 'invalid omission span')
        require(text[start:end] == occurrence.get('text') and bool(occurrence.get('reason')), 'unreviewed omission')
        require(occurrence.get('decision') == 'not_an_entity' and bool(occurrence.get('evidence')),
                'ambiguous occurrence remains held')
        for binding in occurrence['evidence']:
            require(isinstance(binding, FileBinding), 'bound omission evidence required')
            binding.verify()
        require(not any(start < e.end and e.start < end for e in entities), 'omission overlaps an entity')
        omissions.append((start, end, occurrence['text']))
    for literal in {e.text for e in entities}:
        for match in re.finditer(re.escape(literal), text):
            start, end = match.span()
            covered = any(e.start <= start and end <= e.end for e in entities)
            require(covered or (start, end, literal) in omissions, 'unreviewed repeated occurrence')
    record = AnnotationRecord(
        annotation_profile='location-only-v1', record_id=proposal['record_id'], source=source,
        passage_language=proposal['language'], passage_start=proposal['passage_start'],
        passage_end=proposal['passage_end'], text=text, text_sha256=proposal['text_sha256'],
        entities=entities, annotation_revision=proposal.get('annotation_revision', 'v8-source-review'),
        quality='silver', teacher=proposal['annotator'], reviewer=proposal['reviewer'],
        review_status='draft', complete=True, split=None,
    )
    errors = validate_record(record, nlp)
    require(not errors, 'source/schema/tokenizer checks failed: ' + '; '.join(errors))
    return record


def group_keys(record: AnnotationRecord) -> frozenset[str]:
    source = record.source
    return frozenset(f'{kind}:{value}' for kind, value in (
        ('article', source.article_group), ('url', article_key(source.url)),
        ('event', source.event_group), ('syndication', source.syndication_group),
        ('source_hash', source.text_sha256), ('passage_hash', record.text_sha256),
    ) if value)


@dataclass(frozen=True)
class ReviewCandidate:
    record: AnnotationRecord
    eligibility: Mapping[str, bool]
    evidence: Mapping[str, tuple[FileBinding, ...]]
    alternatives: frozenset[str] = frozenset()
    holds: tuple[str, ...] = ()
    occurrence_exclusions: tuple[Mapping[str, Any], ...] = ()


def validate_candidate(candidate: ReviewCandidate, nlp: Any, excluded_groups: frozenset[str]) -> None:
    record, source = candidate.record, candidate.record.source
    require('entities' in record.model_fields_set, 'missing reference cannot use schema empty-list default')
    require(record.complete and record.annotation_profile == 'location-only-v1', 'incomplete location reference')
    require(record.quality == 'silver' and bool(record.teacher) and bool(record.reviewer), 'review identities required')
    require(record.split is None and source.admission_status == 'research_only', 'review must not alter admission or splits')
    require(record.passage_language in {'english', 'taglish'}, 'target language not established')
    require(not validate_record(record, nlp), 'reference mechanics invalid')
    validate_reference(dict(record_id=record.record_id, language=record.passage_language,
        passage_start=record.passage_start, passage_end=record.passage_end, text=record.text,
        text_sha256=record.text_sha256, source_text_sha256=source.text_sha256,
        source_raw_sha256=source.raw_sha256, expected_entities=[dict(start=e.start, end=e.end,
            text=e.text, label=e.label) for e in record.entities], annotation_reference_complete=True,
        candidate_negative=not record.entities, annotator=record.teacher, reviewer=record.reviewer),
        source, nlp, ignored_occurrences=candidate.occurrence_exclusions)
    require(not candidate.holds, 'candidate is held')
    require(set(candidate.eligibility) == REQUIRED_GATES and
            all(type(v) is bool and v for v in candidate.eligibility.values()), 'eligibility not established')
    require(set(candidate.evidence) == REQUIRED_GATES, 'eligibility evidence absent')
    for bindings in candidate.evidence.values():
        require(bool(bindings), 'eligibility evidence absent')
        for binding in bindings:
            binding.verify()
    require(source.published_at is not None and '2017-01-01' <= source.published_at.date().isoformat() <= '2026-10-14',
            'publication window not supported')
    require(bool(source.event_group) and bool(source.syndication_group), 'reviewed groups required')
    require(not any(str(value).lower().startswith(('pending', 'provisional', 'unresolved', 'review-needed'))
                    for value in (source.article_group, source.event_group, source.syndication_group)), 'unresolved grouping')
    require(not group_keys(record) & excluded_groups, 'historical or exposure group exclusion')


def counts(rows: Iterable[ReviewCandidate]) -> tuple[int, int, int, int]:
    result = [0, 0, 0, 0]
    for row in rows:
        require(row.record.passage_language in {'english', 'taglish'}, 'unknown language')
        result[(0 if row.record.passage_language == 'english' else 2) + int(not row.record.entities)] += 1
    return tuple(result)


def compatible(rows: Sequence[ReviewCandidate]) -> None:
    ids = [r.record.record_id for r in rows]
    require(len(ids) == len(set(ids)), 'duplicate record identity')
    require(not any(r.alternatives & set(ids) for r in rows), 'mutually exclusive alternatives')
    require(len({r.record.text_sha256 for r in rows}) == len(rows), 'duplicate passage')
    articles: Counter[str] = Counter()
    for row in rows:
        for key in group_keys(row.record):
            if key.startswith(('article:', 'url:', 'source_hash:')):
                articles[key] += 1
    require(all(n <= 3 for n in articles.values()), 'article passage cap exceeded')
    for a, b in itertools.combinations(rows, 2):
        if (article_key(a.record.source.url) == article_key(b.record.source.url) or
                a.record.source.article_group == b.record.source.article_group):
            require(a.record.source.text_sha256 == b.record.source.text_sha256,
                    'different article versions require reconciled source offsets')
        if a.record.source.text_sha256 == b.record.source.text_sha256:
            require(a.record.passage_end <= b.record.passage_start or b.record.passage_end <= a.record.passage_start,
                    'overlapping source passages')
    require(all(n <= limit for n, limit in zip(counts(rows), TARGET)), 'language/polarity quota exceeded')


@dataclass(frozen=True)
class SelectionResult:
    selected: tuple[ReviewCandidate, ...]
    rejected: Mapping[str, str]
    baseline_removed: Mapping[str, str]
    states_checked: int
    _validation_sha256: str | None = field(default=None, init=False, repr=False, compare=False)

    @property
    def counts(self) -> tuple[int, int, int, int]:
        return counts(self.selected)

    @property
    def coverage_complete(self) -> bool:
        return self.counts == TARGET


def select_joint(candidates: Sequence[ReviewCandidate], baseline_ids: Iterable[str], nlp: Any, *,
                 excluded_groups: frozenset[str] = frozenset(), state_limit: int = 100_000) -> SelectionResult:
    """Find one jointly feasible proposal; never combine independent maxima.

    No lossy one-witness-per-count pruning: alternatives can constrain future
    groups differently. Exceeding the explicit search limit fails, not certifies.
    """
    indexed = {c.record.record_id: c for c in candidates}
    require(len(indexed) == len(candidates), 'duplicate candidate identity')
    baseline = frozenset(baseline_ids)
    require(baseline <= indexed.keys(), 'baseline candidate missing')
    rejected: dict[str, str] = {}
    eligible = {}
    for rid, c in indexed.items():
        try:
            validate_candidate(c, nlp, excluded_groups)
        except (ValueError, OSError) as exc:
            rejected[rid] = str(exc)
        else:
            eligible[rid] = c
    fixed = tuple(eligible[rid] for rid in sorted(baseline & eligible.keys()))
    compatible(fixed)
    byarticle: dict[str, list[ReviewCandidate]] = defaultdict(list)
    for rid, c in eligible.items():
        if rid not in baseline:
            byarticle[article_key(c.record.source.url)].append(c)
    options = []
    for rows in byarticle.values():
        groups = []
        for size in range(min(3, len(rows)) + 1):
            for group in itertools.combinations(rows, size):
                try:
                    compatible(fixed + group)
                except ReviewError:
                    continue
                groups.append(group)
        options.append(groups)
    best, visited = fixed, 0

    def visit(index: int, chosen: tuple[ReviewCandidate, ...]) -> None:
        nonlocal best, visited
        visited += 1
        require(visited <= state_limit, 'selection search limit exceeded; no feasibility certificate')
        if (len(chosen), counts(chosen)) > (len(best), counts(best)):
            best = chosen
        if index == len(options) or counts(chosen) == TARGET:
            return
        for group in options[index]:
            combined = chosen + group
            try:
                compatible(combined)
            except ReviewError:
                continue
            visit(index + 1, combined)

    visit(0, fixed)
    result = SelectionResult(best, rejected, {rid: rejected[rid] for rid in sorted(baseline & rejected.keys())}, visited)
    object.__setattr__(result, '_validation_sha256', _selection_digest(result))
    return result


def _selection_digest(result: SelectionResult) -> str:
    # Detect mutation of nested Pydantic records/mappings after actual gate execution.
    payload = dict(selected=[dict(record=c.record.model_dump(mode='json'), eligibility=dict(c.eligibility),
        evidence={k: [(str(b.path), b.sha256) for b in bindings] for k, bindings in c.evidence.items()},
        alternatives=sorted(c.alternatives), holds=c.holds,
        omissions=[{**o, 'evidence': [(str(b.path), b.sha256) for b in o.get('evidence', ())]}
                   for o in c.occurrence_exclusions]) for c in result.selected],
        rejected=dict(result.rejected), baseline_removed=dict(result.baseline_removed), states=result.states_checked)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class GuardResults:
    passed: int
    failed: int
    _execution: object = field(default=None, init=False, repr=False, compare=False)


def run_guards(checks: Mapping[str, Callable[[], None]]) -> GuardResults:
    require(bool(checks), 'fresh guard evidence absent')
    passed = failed = 0
    for check in checks.values():
        try:
            require(check() in (None, True), 'guard returned an unsuccessful result')
        except Exception:
            failed += 1
        else:
            passed += 1
    result = GuardResults(passed, failed)
    object.__setattr__(result, '_execution', _GUARD_EXECUTION)
    return result


class SafeReviewStatus(BaseModel):
    """No free-form strings/paths/IDs; invalid extra fields are an error."""
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    schema_version: Literal['lanes-repaired-research-review-v1'] = 'lanes-repaired-research-review-v1'
    english_positive: int = Field(ge=0, le=27)
    english_genuine_negative: int = Field(ge=0, le=3)
    taglish_positive: int = Field(ge=0, le=27)
    taglish_genuine_negative: int = Field(ge=0, le=3)
    conditional_test: int = Field(ge=0, le=60)
    missing_english_positive: int = Field(ge=0, le=27)
    missing_taglish_positive: int = Field(ge=0, le=27)
    missing_english_negative: int = Field(ge=0, le=3)
    missing_taglish_negative: int = Field(ge=0, le=3)
    complete_references_checked: int = Field(ge=0)
    entity_spans_checked: int = Field(ge=0)
    guard_checks_passed: int = Field(ge=0)
    guard_checks_failed: int = Field(ge=0)
    baseline_members_removed: int = Field(ge=0)
    coverage_complete: bool
    accounting_verified: bool
    history_verified: bool
    ready_for_admission: bool
    ready_for_training: Literal[False] = False
    test_sealed: Literal[False] = False
    admission_performed: Literal[False] = False
    export_performed: Literal[False] = False
    new_network_operations: Literal[0] = 0
    blocker_codes: list[Literal['coverage', 'accounting', 'history', 'guards']]

    @model_validator(mode='after')
    def reconcile(self) -> SafeReviewStatus:
        count = (self.english_positive, self.english_genuine_negative,
                 self.taglish_positive, self.taglish_genuine_negative)
        if self.conditional_test != sum(count) or self.coverage_complete != (count == TARGET):
            raise ValueError('selection totals or coverage do not reconcile')
        if (self.missing_english_positive != 27 - count[0] or
                self.missing_taglish_positive != 27 - count[2] or
                self.missing_english_negative != 3 - count[1] or self.missing_taglish_negative != 3 - count[3]):
            raise ValueError('positive shortages do not reconcile')
        expected = ([] if self.coverage_complete else ['coverage'])
        if not self.accounting_verified:
            expected.append('accounting')
        if not self.history_verified:
            expected.append('history')
        if self.guard_checks_failed:
            expected.append('guards')
        if (self.blocker_codes != expected or self.ready_for_admission != (not expected) or
                self.complete_references_checked < self.conditional_test or
                self.guard_checks_passed + self.guard_checks_failed == 0):
            raise ValueError('readiness or verification evidence does not reconcile')
        return self


Digest = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
Count = Annotated[int, Field(ge=0)]


class SafeVerificationManifest(BaseModel):
    """Companion verification is allowlisted too; private manifests never cross."""
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    schema_version: Literal['lanes-repaired-research-verification-v1']
    safe_for_parent: Literal[True]
    aggregate_status_sha256: Digest
    private_output_manifest_sha256: Digest
    authorization_sha256: Digest
    review_module_sha256: Digest
    frozen_tokenizer_sha256: Digest
    exposure_snapshot_bindings_verified: Count
    new_capture_groups_reviewed: Count
    new_windows_corrected_and_mechanically_validated: Count
    new_windows_held: Count
    prior_quarantined_baseline_members_retained: Count
    historical_baseline: Count
    conditional_test: Count
    baseline_members_removed: Count
    complete_references_checked: Count
    unknown_reference_holds: Count
    mechanical_errors: Count
    guard_checks_passed: Count
    guard_checks_failed: Count
    predecessor_files_unchanged: Count
    predecessor_hash_failures: Count
    original_v5_tool_receipts_verified: bool
    additional_unknown_exposure_count: None
    inherited_uncertain_slots_preserved: Count
    new_network_operations: Literal[0]
    accounting_verified: bool
    history_verified: bool
    test_sealed: Literal[False]
    admission_performed: Literal[False]
    export_performed: Literal[False]
    inference_performed: Literal[False]
    training_performed: Literal[False]
    upload_performed: Literal[False]
    push_performed: Literal[False]
    training_ready: Literal[False]
    human_gold: Literal[False]
    contains_source_text_urls_titles_entities_or_individual_labels: Literal[False]
    completed: Literal[True]


def validate_safe_pair(status_bytes: bytes, verification_bytes: bytes, *,
                       authorization_sha256: str, frozen_tokenizer_sha256: str) -> tuple[SafeReviewStatus, SafeVerificationManifest]:
    status = SafeReviewStatus.model_validate_json(status_bytes)
    proof = SafeVerificationManifest.model_validate_json(verification_bytes)
    require(proof.aggregate_status_sha256 == hashlib.sha256(status_bytes).hexdigest(), 'safe status hash mismatch')
    require(proof.authorization_sha256 == authorization_sha256 and
            proof.review_module_sha256 == file_hash(Path(__file__)) and
            proof.frozen_tokenizer_sha256 == frozen_tokenizer_sha256, 'safe verification binding mismatch')
    for key in ('conditional_test', 'baseline_members_removed', 'complete_references_checked',
                'guard_checks_passed', 'guard_checks_failed', 'accounting_verified', 'history_verified'):
        require(getattr(status, key) == getattr(proof, key), 'safe verification totals mismatch')
    require(proof.conditional_test + proof.baseline_members_removed >= proof.historical_baseline,
            'historical baseline reductions unaccounted')
    require(proof.predecessor_hash_failures == 0 and proof.mechanical_errors == 0, 'verification failed')
    return status, proof


def build_status(selection: SelectionResult, *, guards: GuardResults, accounting_verified: bool,
                 history_verified: bool, validated_records: Sequence[AnnotationRecord]) -> SafeReviewStatus:
    require(type(accounting_verified) is bool and type(history_verified) is bool, 'explicit gate decisions required')
    require(guards._execution is _GUARD_EXECUTION and guards.passed + guards.failed > 0, 'executed guard evidence absent')
    require(selection._validation_sha256 == _selection_digest(selection), 'executed selection evidence absent or changed')
    for candidate in selection.selected:
        for bindings in candidate.evidence.values():
            for binding in bindings:
                binding.verify()
    require(all(r.complete for r in validated_records), 'incomplete references in validation totals')
    compatible(selection.selected)
    known = {r.record_id: r for r in validated_records}
    require(len(known) == len(validated_records), 'duplicate mechanical validation rows')
    require(all(c.record.record_id in known and c.record == known[c.record.record_id] for c in selection.selected),
            'selection is not bound to mechanically validated references')
    count = selection.counts
    blockers = []
    if not selection.coverage_complete:
        blockers.append('coverage')
    if not accounting_verified:
        blockers.append('accounting')
    if not history_verified:
        blockers.append('history')
    if guards.failed:
        blockers.append('guards')
    return SafeReviewStatus(
        english_positive=count[0], english_genuine_negative=count[1], taglish_positive=count[2],
        taglish_genuine_negative=count[3], conditional_test=sum(count), missing_english_positive=27-count[0],
        missing_taglish_positive=27-count[2], complete_references_checked=len(validated_records),
        missing_english_negative=3-count[1], missing_taglish_negative=3-count[3],
        entity_spans_checked=sum(len(r.entities) for r in validated_records), guard_checks_passed=guards.passed,
        guard_checks_failed=guards.failed, baseline_members_removed=len(selection.baseline_removed),
        coverage_complete=selection.coverage_complete, accounting_verified=accounting_verified,
        history_verified=history_verified, ready_for_admission=not blockers, blocker_codes=blockers,
    )


def export_review(*args: Any, **kwargs: Any) -> None:
    raise ReviewError('Review-only scope: separate admission, split freeze and model-tokenizer-qualified export required')
