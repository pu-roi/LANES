"""Safe fallback retrieval orchestration; telemetry is handled by its caller."""

import httpx
from dataclasses import dataclass
from datetime import datetime

from app.models.news import NewsArticle
from app.services.news_sources import load_news_sources
from app.services.news_open_search_service import (
    OpenSearchLookup, search_open_article_leads, append_publisher_feed_leads,
    retrieve_open_article_leads, assess_alternate_article_leads,
)


@dataclass(frozen=True)
class FallbackInput:
    canonical_url: str
    title: str
    excerpt: str
    published_at: datetime | None

    @classmethod
    def capture(cls, article: NewsArticle) -> "FallbackInput":
        """Keep lookup inputs stable when the start-record commit expires ORM rows."""
        return cls(article.canonical_url, article.title, article.excerpt, article.published_at)


def lookup_news_leads(article: FallbackInput, retrieve_articles: bool) -> OpenSearchLookup:
    with httpx.Client(timeout=httpx.Timeout(8.0, connect=3.0)) as client:
        result = search_open_article_leads(
            article.canonical_url,
            article.title,
            article.excerpt,
            client,
            published_at=article.published_at,
            include_event_context=retrieve_articles,
        )
        if retrieve_articles:
            sources = load_news_sources()
            result = append_publisher_feed_leads(
                result, article.title, article.excerpt, article.published_at, sources, client,
            )
            result = retrieve_open_article_leads(result, sources, client)
            result = assess_alternate_article_leads(result, article.title, article.excerpt, article.published_at)
    return result
