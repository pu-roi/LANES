"""Staff history and read contracts kept separate from public alert output."""
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.news_publication import NewsDecisionSummary, NewsPublicationModel


class StaffNewsDecision(NewsDecisionSummary):
    request_id: UUID
    actor_kind: str
    actor_user_id: int | None = None
    evaluation_id: int | None = None
    private_reason: str | None = None
    public_correction: str | None = None


class StaffNewsDecisionPage(NewsPublicationModel):
    items: list[StaffNewsDecision]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    pages: int = Field(ge=1)
    as_of: datetime
