"""Evidence-only academic-use review checks; no source admission operations."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from .annotation.schema import AnnotationRecord, text_hash
from .collection import publisher_for
from .sources import json_bytes
from .use_bundle import verified_reference

ACADEMIC_SCOPE = 'academic_training_evaluation'


def clause_pointer(path: Path, root: Path, start: int, end: int) -> dict[str, Any]:
    """Bind an exact clause without redistributing its wording in the report."""
    path = path.resolve(); root = root.resolve()
    if not path.is_relative_to(root):
        raise ValueError('clause evidence must stay inside the repository')
    text = path.read_bytes().decode('utf-8')
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
        raise ValueError('clause needs valid Unicode character offsets')
    return {'reference': {'path': path.relative_to(root).as_posix(),
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest()},
            'start': start, 'end': end, 'span_sha256': text_hash(text[start:end])}


def verify_pointer(pointer: dict[str, Any], root: Path) -> None:
    path = verified_reference(pointer.get('reference'), root)
    actual = clause_pointer(path, root, pointer.get('start'), pointer.get('end'))
    if actual != pointer:
        raise ValueError('clause evidence hash or offsets differ')


def validate_academic_review(report: dict[str, Any], original_packet: dict[str, Any],
                             records: list[AnnotationRecord], root: Path) -> None:
    """Check report scope/provenance, never infer rights from a completed form."""
    if (report.get('schema_version') != 'lanes-academic-use-review-v1'
            or report.get('scope') != ACADEMIC_SCOPE
            or report.get('training_admitted') != 0 or report.get('docbin_exported') != 0
            or report.get('distribution_ready') is not False or report.get('automatic_admission') is not False):
        raise ValueError('academic review must preserve admission and distribution holds')
    if (len(records) != 400 or len({r.record_id for r in records}) != 400
            or len({r.source.source_id for r in records}) != 139
            or any(r.source.admission_status != 'research_only' or r.source.reuse_status != 'unknown' for r in records)):
        raise ValueError('unchanged research-only 400-record/139-source cohort required')
    bindings = report.get('bindings', {})
    if set(bindings) != {'cohort_manifest', 'context_manifest', 'review_packet'}:
        raise ValueError('corrected cohort/context/review bindings required')
    for value in bindings.values(): verified_reference(value, root)
    if (bindings['cohort_manifest']['sha256'] != original_packet.get('dataset_manifest_sha256')
            or bindings['context_manifest']['sha256'] != original_packet.get('context_manifest_sha256')
            or json.loads(verified_reference(bindings['review_packet'], root).read_text(encoding='utf-8')) != original_packet):
        raise ValueError('review bindings must identify the corrected packet and its cohort/context manifests')
    prior = [r for r in original_packet['assessments'] if r['scope'] != ACADEMIC_SCOPE]
    if (len(prior) != 12 or report.get('unchanged_nonacademic_outcomes') != prior
            or report.get('nonacademic_outcomes_sha256') != hashlib.sha256(json_bytes(prior)).hexdigest()):
        raise ValueError('all twelve nonacademic outcomes must remain unchanged')
    pubs = Counter(publisher_for(r.source.url) for r in {r.source.source_id: r for r in records}.values())
    reviews = report.get('assessments', [])
    if len(reviews) != 3 or len({a['publisher'] for a in reviews}) != 3 or {a['publisher'] for a in reviews} != set(pubs):
        raise ValueError('one academic conclusion per publisher required')
    rows = report.get('article_reviews', [])
    sources = {r.source.source_id: r.source for r in records}
    if len(rows) != 139 or len({r['source_id'] for r in rows}) != 139 or {r['source_id'] for r in rows} != set(sources):
        raise ValueError('every selected article needs a distinct review')
    for row in rows:
        source = sources[row['source_id']]
        if (row.get('capture_version') != source.capture_version or row.get('text_sha256') != source.text_sha256
                or row.get('publisher') != publisher_for(source.url) or row.get('admission_decision') != 'unresolved'):
            raise ValueError('article review source binding or admission mismatch')
        for pointer in row.get('evidence_pointers', []): verify_pointer(pointer, root)
    clause_ids = set()
    for item in report.get('clauses', []):
        if not item.get('clause_id') or item['clause_id'] in clause_ids:
            raise ValueError('unique clause identities required')
        clause_ids.add(item['clause_id']); verify_pointer(item['pointer'], root)
    if not clause_ids: raise ValueError('bound policy/statutory clauses required')
    for review in reviews:
        expected = {r.source.source_id for r in records if publisher_for(r.source.url) == review['publisher']}
        assessor = review.get('assessor', {})
        try:
            reviewed_at = datetime.fromisoformat(assessor.get('reviewed_at', ''))
        except (TypeError, ValueError) as exc:
            raise ValueError('actual dated AI assessor required') from exc
        if (review.get('scope') != ACADEMIC_SCOPE or set(review.get('source_ids', [])) != expected
                or review.get('admission_decision') != 'unresolved' or review.get('review_state') != 'complete'
                or assessor.get('kind') != 'ai' or not assessor.get('name') or reviewed_at.utcoffset() is None
                or set(review.get('fair_use_factors', {})) != {'purpose', 'nature', 'amount', 'market_effect'}
                or any(not isinstance(v, str) or not v.strip() for v in review['fair_use_factors'].values())
                or not review.get('next_actions') or not review.get('clause_ids')
                or not set(review['clause_ids']) <= clause_ids):
            raise ValueError('publisher conclusion needs factors, provenance, bound clauses and actions; no admission inferred')
        for action in review['next_actions']:
            if action.get('owner_type') not in {'researcher', 'school_guidance', 'rights_holder'} or not action.get('action'):
                raise ValueError('next action needs a specific owner and action')
