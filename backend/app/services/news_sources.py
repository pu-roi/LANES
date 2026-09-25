"""Reviewed RSS source configuration; catalog entries are disabled by default."""

from __future__ import annotations

import json
import ipaddress
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


DEFAULT_SOURCE_FILE = Path(__file__).resolve().parents[1] / "news_sources.json"


@dataclass(frozen=True)
class NewsSource:
    id: str
    publisher: str
    article_domains: tuple[str, ...]
    feed_urls: tuple[str, ...]
    verified_at: date | None
    enabled: bool

    def accepts_article_host(self, hostname: str | None) -> bool:
        if not hostname:
            return False
        host = hostname.lower().removeprefix("www.")
        return any(
            host == domain.removeprefix("www.") or host.endswith("." + domain.removeprefix("www."))
            for domain in self.article_domains
        )


def _public_host(hostname: str | None) -> bool:
    if not hostname:
        return False
    host = hostname.lower()
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    return "." in host and host != "localhost" and not host.endswith(".localhost") and all(
        part and part.replace("-", "").isalnum() for part in host.split(".")
    )


def load_news_sources(path: Path = DEFAULT_SOURCE_FILE) -> tuple[NewsSource, ...]:
    """Load candidates. An enabled source needs a dated human verification."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources: list[NewsSource] = []
    seen_ids: set[str] = set()
    for item in payload["sources"]:
        source_id = str(item["id"])
        if source_id in seen_ids:
            raise ValueError(f"Duplicate news source: {source_id}")
        seen_ids.add(source_id)
        domains = tuple(str(host).lower() for host in item["article_domains"])
        urls = tuple(str(url) for url in item["feed_urls"])
        if not domains or any(not _public_host(host) for host in domains):
            raise ValueError(f"Invalid article domain for {source_id}")
        for url in urls:
            parts = urlsplit(url)
            if (parts.scheme != "https" or not _public_host(parts.hostname) or parts.username or
                    parts.password or parts.port not in (None, 443)):
                raise ValueError(f"Invalid feed URL for {source_id}")
        verified_at = date.fromisoformat(item["verified_at"]) if item["verified_at"] else None
        enabled = item["enabled"]
        if not isinstance(enabled, bool):
            raise ValueError(f"Invalid enabled flag for {source_id}")
        if enabled and (not urls or verified_at is None):
            raise ValueError(f"Enabled source requires a verified feed and date: {source_id}")
        sources.append(NewsSource(
            id=source_id,
            publisher=str(item["publisher"]),
            article_domains=domains,
            feed_urls=urls,
            verified_at=verified_at,
            enabled=enabled,
        ))
    return tuple(sources)
