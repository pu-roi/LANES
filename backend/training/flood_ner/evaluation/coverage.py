"""Metadata-only report, tracked separately from source article bodies."""
from __future__ import annotations

from collections import Counter
from typing import Any

from ..annotation.schema import SourceCapture


def coverage_report(sources: list[SourceCapture], issues: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "schema_version": "lanes-flood-ner-coverage-v1",
        "source_count": len(sources),
        "language_counts": dict(sorted(Counter(s.language for s in sources).items())),
        "admission_counts": dict(sorted(Counter(s.admission_status for s in sources).items())),
        "annotations_read": 0,
        "limitations": [
            "Source languages are supplied research metadata, not model predictions or passage annotations.",
            "Unknown language/event/syndication/reuse metadata requires review before corpus admission.",
            "Coverage counts are source inventory counts, not extraction accuracy or balanced training support.",
            "This source inventory does not inspect annotation files or evaluate a model.",
        ],
        "issues": issues,
        "sources": [{
            "source_id": s.source_id, "url": s.url, "publisher": s.publisher, "title": s.title,
            "text_sha256": s.text_sha256, "raw_sha256": s.raw_sha256, "capture_version": s.capture_version,
            "characters": len(s.text), "language": s.language, "origin": s.origin,
            "published_at": s.published_at.isoformat() if s.published_at else None,
            "captured_at": s.captured_at.isoformat() if s.captured_at else None,
            "publication_basis": s.publication_basis, "extraction_method": s.extraction_method,
            "reuse_status": s.reuse_status, "reuse_terms": s.reuse_terms, "admission_status": s.admission_status,
            "article_group": s.article_group, "event_group": s.event_group, "syndication_group": s.syndication_group,
        } for s in sorted(sources, key=lambda s: (s.url, s.text_sha256))],
    }
