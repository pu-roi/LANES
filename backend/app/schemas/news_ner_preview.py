"""Dedicated transient extraction contract, independent of legacy flood claims."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, JsonValue


class PreviewModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Evidence(PreviewModel):
    start: int
    end: int
    text: str


class Mention(Evidence):
    id: str
    label: Literal['ROAD', 'LANDMARK', 'LOCAL_AREA', 'CITY', 'BARANGAY', 'PROVINCE']
    provenance_sha256: str


class Expression(Evidence):
    id: str
    label: Literal['DEPTH', 'TIME']


class Fact(PreviewModel):
    id: str
    kind: Literal['depth', 'time', 'status', 'access']
    entity_ids: list[str]
    value: str | None
    temporal_role: Literal['onset', 'observation', 'report', 'publication', 'recession', 'clearance', 'unspecified'] | None
    depth_scope: Literal['point', 'range', 'collective', 'maximum', 'unspecified'] | None
    qualifiers: list[str]
    uncertainty: list[str]
    evidence: list[Evidence]


class Relation(PreviewModel):
    id: str
    fact_id: str
    target_entity_ids: list[str]
    scope: Literal['local', 'shared', 'collective', 'unresolved']
    evidence: list[Evidence]
    uncertainty: list[str]
    overrides_relation_id: str | None
    reason: str


class Unassigned(PreviewModel):
    fact_id: str
    reason: str


class ContextGraph(PreviewModel):
    schema_id: str = Field(alias='schema')
    record_id: str
    text_sha256: str
    mentions: list[Mention]
    expressions: list[Expression]
    facts: list[Fact]
    relations: list[Relation]
    unassigned: list[Unassigned]
    diagnostics: list[str]
    absolute_instants: list[JsonValue]
    numeric_depths: list[JsonValue]


class FieldGroup(PreviewModel):
    target_entity_ids: list[str]
    scope: Literal['local', 'shared', 'collective', 'unresolved']
    evidence: list[Evidence]
    relation_ids: list[str]
    depth: list[Fact]
    time: list[Fact]
    status: list[Fact]
    access: list[Fact]


class PreviewSource(PreviewModel):
    article_id: int
    canonical_url: str
    text_field: Literal['article_text'] = 'article_text'
    text_sha256: str
    input_sha256: str
    published_at: str | None
    publication_timezone_known: bool


class RuntimeMeasurements(PreviewModel):
    cold_seconds: float
    extraction_seconds: float
    peak_worker_rss_bytes: int


class NerPreview(PreviewModel):
    schema_version: Literal['lanes-ner-preview-v1'] = 'lanes-ner-preview-v1'
    source: PreviewSource
    provenance: dict[str, str]
    measurements: RuntimeMeasurements
    neural_mentions: list[Mention]
    effective_mentions: list[Mention]
    proposals: list[dict[str, JsonValue]]
    abstentions: list[dict[str, JsonValue]]
    groups: list[FieldGroup]
    unassigned: list[Unassigned]
    graph: ContextGraph
    limitations: list[str]
