"""Corpus contracts independent of database and production configuration."""
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "lanes-flood-ner-v1"
LABELS = ("ROAD", "LANDMARK", "LOCAL_AREA", "BARANGAY", "CITY", "PROVINCE", "DEPTH", "TIME")
PLACE_LABELS = frozenset(LABELS[:6])
EntityLabel = Literal["ROAD", "LANDMARK", "LOCAL_AREA", "BARANGAY", "CITY", "PROVINCE", "DEPTH", "TIME"]
Language = Literal["english", "tagalog", "taglish", "unknown"]
AnnotationProfile = Literal['context-rich-v1', 'location-only-v1']


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class StrictRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class SourceCapture(StrictRecord):
    schema_version: Literal["lanes-flood-ner-v1"] = SCHEMA_VERSION
    source_id: str = Field(min_length=1)
    url: str
    publisher: str = Field(min_length=1)
    title: str = ""
    language: Language = "unknown"
    origin: Literal["captured_original", "constructed_fixture"] = "captured_original"
    text: str = Field(min_length=1)
    text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    capture_version: str = Field(min_length=1)
    published_at: datetime | None = None
    captured_at: datetime | None = None
    publication_basis: str | None = None
    article_group: str = Field(min_length=1)
    event_group: str | None = None
    syndication_group: str | None = None
    reuse_status: Literal["unknown", "allowed", "restricted"] = "unknown"
    reuse_terms: str = Field(min_length=1)
    admission_status: Literal["research_only", "training_admitted"] = "research_only"
    extraction_method: str = Field(min_length=1)
    raw_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def source_integrity(self) -> SourceCapture:
        parts = urlsplit(self.url)
        if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
            raise ValueError("source URL must be HTTP(S) without credentials")
        if text_hash(self.text) != self.text_sha256:
            raise ValueError("source text_sha256 mismatch")
        for value in (self.published_at, self.captured_at):
            if value is not None and value.utcoffset() is None:
                raise ValueError("source timestamps require a timezone; unknown dates stay null")
        if self.admission_status == "training_admitted" and self.reuse_status != "allowed":
            raise ValueError("training admission requires explicit allowed reuse status")
        return self


class Span(StrictRecord):
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str = Field(min_length=1)


class GeographicIdentity(StrictRecord):
    """Optional reviewed identity; NER labels never manufacture coordinates."""
    state: Literal["unresolved", "ambiguous", "resolved"] = "unresolved"
    parent_entity_ids: list[str] = Field(default_factory=list)
    psgc_code: str | None = Field(default=None, pattern=r"^\d{10}$")
    osm_type: Literal["node", "way", "relation"] | None = None
    osm_id: int | None = Field(default=None, gt=0)
    reference_url: str | None = None


class Entity(Span):
    id: str = Field(min_length=1)
    label: EntityLabel
    comparison_key: str | None = None
    identity: GeographicIdentity | None = None


class Fact(StrictRecord):
    id: str = Field(min_length=1)
    kind: Literal["depth", "time", "status", "access"]
    evidence: list[Span] = Field(min_length=1)
    entity_ids: list[str] = Field(default_factory=list)
    value: str | None = None
    temporal_role: Literal["onset", "observation", "report", "publication", "recession", "clearance", "unspecified"] | None = None
    depth_scope: Literal["point", "range", "collective", "maximum", "unspecified"] | None = None
    qualifiers: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)


class Relation(StrictRecord):
    id: str = Field(min_length=1)
    fact_id: str
    target_entity_ids: list[str] = Field(min_length=1)
    scope: Literal["local", "shared", "collective", "unresolved"]
    evidence: list[Span] = Field(min_length=1)
    overrides_relation_id: str | None = None
    uncertainty: list[str] = Field(default_factory=list)


class AnnotationRecord(StrictRecord):
    schema_version: Literal["lanes-flood-ner-v1"] = SCHEMA_VERSION
    annotation_profile: AnnotationProfile = 'context-rich-v1'
    passage_language: Language = 'unknown'
    record_id: str = Field(min_length=1)
    source: SourceCapture
    passage_start: int = Field(ge=0)
    passage_end: int = Field(gt=0)
    text: str = Field(min_length=1)
    text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    entities: list[Entity] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    annotation_revision: str = Field(min_length=1)
    quality: Literal["silver", "gold", "constructed"] = "silver"
    teacher: str | None = None
    reviewer: str | None = None
    review_status: Literal["draft", "accepted", "rejected", "unresolved"] = "draft"
    complete: bool = False
    split: Literal["train", "dev", "test"] | None = None
    notes: list[str] = Field(default_factory=list)
