"""Typed batch inputs; kept separate from extraction's audit-result dependency."""
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput
from app.schemas.news_audit import AuditEvidenceSpan


class AuditCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    candidate_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    claim: ExtractedClaim


class AuditRequestCandidate(AuditCandidate):
    claim_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class AuditBatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    article: NewsArticleExtractorInput
    evidence_text: str
    evidence_options: tuple[AuditEvidenceSpan, ...] = Field(max_length=256)
    candidates: tuple[AuditRequestCandidate, ...] = Field(min_length=1, max_length=8)
