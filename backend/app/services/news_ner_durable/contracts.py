"""Native input and projection contracts; independent of legacy normalization."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from email.utils import parsedate_to_datetime
import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.schemas.news_ner_preview import Evidence

PROJECTION_VERSION = "ner-claim-projection-v1"
SOURCE_VERSION = "source-ner-v1"
MAX_CLAIMS = 500
MAX_QUOTE = 4000


class NerEvidenceError(ValueError):
    def __init__(self, code: str) -> None:
        assert code in {"ner_input_binding_invalid", "ner_result_contract_invalid",
                        "ner_assets_unavailable", "ner_configuration_invalid"}
        self.code = code
        super().__init__(code)


def sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PublicationEvidence(StrictModel):
    raw: str | None = None
    timezone_known: bool = False
    basis: Literal["publisher_feed", "legacy_unknown"] = "legacy_unknown"

    @model_validator(mode="after")
    def unknown_is_explicit(self) -> PublicationEvidence:
        if self.basis == "legacy_unknown" and (self.raw is not None or self.timezone_known):
            raise ValueError("invalid_publication_provenance")
        if self.timezone_known and not self.raw:
            raise ValueError("missing_publisher_clock")
        return self


class NativeInput(StrictModel):
    capture_schema: Literal["lanes-news-ner-input-v1"] = "lanes-news-ner-input-v1"
    canonical_url: str
    publisher: str
    title: str
    excerpt: str = ""
    article_text: str = Field(min_length=1, max_length=100000)
    published_at: datetime | None
    publication_evidence: PublicationEvidence

    @model_validator(mode="after")
    def bind_publication(self) -> NativeInput:
        if not self.article_text.strip():
            raise ValueError("missing_body")
        if self.publication_evidence.timezone_known:
            raw = self.publication_evidence.raw or ""
            try:
                try:
                    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00").replace(" PHT", "+08:00"))
                except ValueError:
                    parsed = parsedate_to_datetime(raw.replace(" PHT", " +0800"))
                if (parsed.utcoffset() is None or self.published_at is None
                        or self.published_at.utcoffset() is None or parsed != self.published_at):
                    raise ValueError("publication_identity_mismatch")
            except (ValueError, TypeError, AttributeError, OverflowError) as exc:
                raise ValueError("publication_provenance_invalid") from exc
        return self

    def runtime_request(self, fingerprint: str) -> dict:
        return {"record_id": "ner-" + fingerprint, "text": self.article_text,
                "text_sha256": hashlib.sha256(self.article_text.encode("utf-8")).hexdigest(),
                "publication": {"value": self.published_at.isoformat(), "basis": "publisher_feed"}
                if self.publication_evidence.timezone_known and self.published_at else None}


def capture_native_input(article: NewsArticleExtractorInput, *,
                         publication_evidence: PublicationEvidence | None = None) -> tuple[dict, str]:
    """Pure capture helper, not connected to RSS or the queue in C2."""
    try:
        value = NativeInput.model_validate({**article.model_dump(exclude={"article_id", "fetched_at"}),
            "publication_evidence": publication_evidence or PublicationEvidence()})
        snapshot = value.model_dump(mode="json")
        return snapshot, sha(snapshot)
    except (ValueError, TypeError) as exc:
        raise NerEvidenceError("ner_input_binding_invalid") from exc


class RunEvidence(StrictModel):
    run_id: int = Field(gt=0)
    article_id: int = Field(gt=0)
    article_version_id: int = Field(gt=0)
    mode: Literal["ner_rules_v1"]
    pipeline_version: str = Field(pattern=r"^ner-v1:[a-f0-9]{64}$")
    input_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_snapshot: dict[str, JsonValue]

    @classmethod
    def from_records(cls, run: object, version: object) -> RunEvidence:
        try:
            if run.article_version_id != version.id:
                raise ValueError("version_mismatch")
            return cls(run_id=run.id, article_id=version.article_id, article_version_id=version.id,
                       mode=run.mode, pipeline_version=run.pipeline_version,
                       input_fingerprint=version.input_fingerprint, input_snapshot=deepcopy(version.input_snapshot))
        except (ValueError, TypeError, AttributeError) as exc:
            raise NerEvidenceError("ner_input_binding_invalid") from exc

    def source(self) -> NativeInput:
        try:
            if self.input_snapshot.get("capture_schema") != "lanes-news-ner-input-v1" or sha(self.input_snapshot) != self.input_fingerprint:
                raise ValueError("fingerprint_mismatch")
            return NativeInput.model_validate_json(json.dumps(self.input_snapshot), strict=True)
        except (ValueError, TypeError) as exc:
            raise NerEvidenceError("ner_input_binding_invalid") from exc


class Observation(StrictModel):
    group_id: str
    target_entity_ids: list[str]
    relation_ids: list[str]
    fact_ids: list[str]
    scope: Literal["local", "shared", "collective", "unresolved"]
    evidence: list[Evidence]
    evidence_storage: Literal["inline", "native_graph"] = "inline"
    disposition: Literal["projected", "native_only", "context_only"]
    reasons: list[str]
    claim_index: int | None
    normalizations: dict[str, JsonValue]


class FactAccounting(StrictModel):
    fact_id: str
    group_ids: list[str]
    disposition: Literal["projected", "native_only", "context_only", "unassigned"]
    reasons: list[str]


class Projection(StrictModel):
    version: Literal["ner-claim-projection-v1"] = PROJECTION_VERSION
    disposition: Literal["projected", "native_only", "no_eligible_observations"]
    groups: list[Observation]
    fact_accounting: list[FactAccounting]
    mentions_without_observation: list[str]
