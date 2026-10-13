"""MCP previews accept selections, never host-supplied articles or actors."""
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.news_audit import CompactClaimSelection


class BundleReference(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    run_id: int = Field(ge=1)
    claim_indexes: tuple[int, ...] = Field(min_length=1, max_length=8)
    bundle_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class MCPAuditProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    bundle: BundleReference
    results: tuple[CompactClaimSelection, ...] = Field(min_length=1, max_length=8)
