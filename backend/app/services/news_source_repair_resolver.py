"""Canonical request serialization for the manually scoped source correction.

JSONB reads and reconstructed Pydantic values can have different object key
orders. Canonicalize the embedded document, preserving array and passage order,
so counting, authorization and execution bind the identical provider payload.
"""
from __future__ import annotations

import json

from app.services.news_ner_durable.gemini_resolution import GeminiResolver


class SourceRepairResolver(GeminiResolver):
    @property
    def identity(self) -> dict:
        value = {**super().identity, 'request_serialization': 'canonical-document-v1'}
        from app.services.news_tribune_replay import SHARED_TIME_VERSION, SHARED_TIME_REVIEW
        if getattr(self.batch_plan, 'manifest', {}).get('schema_version') == SHARED_TIME_VERSION:
            value['shared_time_review'] = SHARED_TIME_REVIEW.copy()
        return value

    def request_packets(self, source: object, baseline: object, *, parent_run_id: int,
                        parent_result_sha256: str) -> list[dict]:
        packets = super().request_packets(source, baseline, parent_run_id=parent_run_id,
            parent_result_sha256=parent_result_sha256)
        for packet in packets:
            part = packet['payload']['contents'][0]['parts'][0]
            part['text'] = json.dumps(json.loads(part['text']), ensure_ascii=False,
                allow_nan=False, sort_keys=True, separators=(',', ':'))
        return packets
