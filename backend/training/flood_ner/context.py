"""Preserve raw contextual cues without claiming reviewed flood facts."""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .annotation.schema import AnnotationRecord, text_hash
from .sources import write_jsonl


CUE_PATTERNS = {
    'measurement_role_unknown': r'\b(?:\d+(?:\.\d+)?\s*(?:inches|cm|feet|meters?|ft)|(?:knee|waist|chest|gutter|tire|ankle)[- ]deep)\b',
    'time_role_unknown': r'\b\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?|\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
    'status_polarity_unknown': r'\b(?:subsided|receded|receding|humupa|flooded|binaha|pagbaha|baha)\b',
    'vehicle_scope_unknown': r'\b(?:not passable|passable|impassable|light vehicles|motorcycles|PATV|NPLV|NPATV|evacuation)\b',
}


def write_context_jsonl(path: Path, records: list[AnnotationRecord]) -> list[dict[str, Any]]:
    """Write one JSON object per physical line, preserving every source character."""
    if path.exists():
        raise ValueError('context destination must be new; preserve earlier artifacts')
    views: list[dict[str, Any]] = []
    for record in records:
        cues = [
            {'candidate_kind': kind, 'start': match.start(), 'end': match.end(),
             'text': match.group(), 'sha256': text_hash(match.group()), 'review_status': 'unreviewed'}
            for kind, pattern in CUE_PATTERNS.items()
            for match in re.finditer(pattern, record.text, re.I)
        ]
        views.append({
            'schema_version': 'lanes-flood-ner-context-preservation-v1',
            'record_id': record.record_id, 'source_id': record.source.source_id,
            'source_version': record.source.capture_version, 'source_sha256': record.source.text_sha256,
            'passage_start': record.passage_start, 'passage_end': record.passage_end,
            'text': record.text, 'text_sha256': record.text_sha256,
            'review_status': 'draft', 'candidate_cues': cues,
            'notes': ['Raw contextual evidence preserved; cue discovery is not accepted fact interpretation.',
                      'No observed calendar date, scalar depth, status polarity or target association inferred.'],
        })
    write_jsonl(path, views)
    return views
