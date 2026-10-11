"""Public article metadata for Community Feed Local Updates."""
from datetime import datetime

from pydantic import BaseModel


class LocalNewsArticle(BaseModel):
    id: int
    title: str
    publisher: str
    source_url: str
    published_at: datetime


class LocalNewsUpdates(BaseModel):
    items: list[LocalNewsArticle]
    as_of: datetime
