"""Saved native extraction shape; inspection does not grant publication eligibility.

This is separate from both the transient preview and legacy extraction schemas.
Projection/source-consistency validation belongs to the native processing adapter,
not to serialization or an admin GET.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_serializer

from app.schemas.news_extraction import ExtractedClaim, NewsExtractionResult, FloodCondition
from app.schemas.news_ner_preview import ContextGraph, FieldGroup, Mention

ProcessingMode = Literal["rules_only", "ner_rules_v1"]
NATIVE_SCHEMA = "lanes-news-ner-result-v1"
MAX_NATIVE_RESULT_BYTES = 8 * 1024 * 1024


class NativeSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    article_version_id: int = Field(gt=0)
    input_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    canonical_url: str
    text_field: Literal["article_text"]
    text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    published_at: str | None
    publication_timezone_known: bool


class NativeExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    neural_mentions: list[Mention]
    effective_mentions: list[Mention]
    proposals: list[dict[str, JsonValue]]
    abstentions: list[dict[str, JsonValue]]
    graph: ContextGraph
    groups: list[FieldGroup]

    @model_serializer(mode="wrap")
    def preserve_graph_schema_key(self, handler: Callable[[NativeExtraction], dict]) -> dict:
        payload = handler(self)
        # Legacy callers often omit by_alias=True. Do not change the native
        # graph's schema discriminator/hash during that ordinary JSON dump.
        if "schema_id" in payload["graph"]:
            payload["graph"]["schema"] = payload["graph"].pop("schema_id")
        return payload


class NerProjectedClaim(ExtractedClaim):
    """Unknown model confidence is distinct from a calibrated probability."""

    model_config = ConfigDict(extra="forbid")
    confidence_score: float | None = None


class NativeReadDisplay(BaseModel):
    model_config = ConfigDict(extra='forbid')
    raw_place_name: str = Field(min_length=1, max_length=500)
    canonical_city: str
    condition: FloodCondition
    depth_raw: str | None = Field(default=None, max_length=500)
    event_time_resolved: datetime | None = None
    event_time_kind: Literal['observation', 'report', 'unspecified']
    road_passability: str
    evidence_span: tuple[int, int]
    uncertainty_reasons: list[str]


class NativeReadGroup(BaseModel):
    model_config = ConfigDict(extra='forbid')
    group_id: str
    claim_index: int | None
    display: NativeReadDisplay | None = None


class NativeReadProjection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    version: Literal['ner-result-read-v1'] = 'ner-result-read-v1'
    groups: list[NativeReadGroup]
    omitted_counts: dict[str, int]


class NewsNerResult(NewsExtractionResult):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["lanes-news-ner-result-v1"]
    processing_method: Literal["ner_rules_v1"]
    is_metadata_only: Literal[False]
    claims: list[NerProjectedClaim] = Field(default_factory=list)
    source: NativeSource
    provenance: dict[str, JsonValue]
    native: NativeExtraction
    projection: dict[str, JsonValue]
    measurements: dict[str, JsonValue]
    limitations: list[str]
    read_projection: NativeReadProjection | None = None

    @model_serializer(mode='wrap')
    def preserve_historical_shape(self, handler: Callable) -> dict:
        payload = handler(self)
        if self.read_projection is None:
            payload.pop('read_projection', None)
        return payload


def parse_saved_result(mode: str, value: object) -> NewsExtractionResult | NewsNerResult | None:
    """Dispatch using the persisted method; never reinterpret unknown native data."""
    if mode not in ("rules_only", "ner_rules_v1"):
        raise ValueError("extraction_mode_unsupported")
    if value is None:
        return None
    if isinstance(value, NewsExtractionResult):
        value = value.model_dump(mode="json", by_alias=True)
    if not isinstance(value, dict):
        raise ValueError("extraction_result_invalid")
    if mode == "rules_only":
        if any(key in value for key in ("schema_version", "processing_method", "native")):
            raise ValueError("extraction_result_method_mismatch")
        return NewsExtractionResult.model_validate(value)
    if value.get("schema_version") != NATIVE_SCHEMA:
        raise ValueError("ner_result_version_unsupported")
    if value.get("processing_method") != mode:
        raise ValueError("extraction_result_method_mismatch")
    encoded = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(encoded) > MAX_NATIVE_RESULT_BYTES:
        raise ValueError("ner_result_too_large")
    # JSON-mode strict validation accepts ISO instants/JSON arrays while refusing
    # coercion of source offsets, lengths, flags or unknown confidence values.
    return NewsNerResult.model_validate_json(encoded, strict=True)
