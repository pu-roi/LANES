"""Bounded RSS/Atom retrieval and parsing for publisher feed probes."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit
from xml.etree import ElementTree

import httpx

from app.services.news_sources import NewsSource


MAX_FEED_BYTES = 2_000_000
MAX_REDIRECTS = 3
MAX_ARTICLE_URL_BYTES = 1500
MAX_GUID_BYTES = 512


@dataclass(frozen=True)
class NewsEntry:
    source_id: str
    publisher: str
    feed_url: str
    feed_id: str
    title: str
    excerpt: str
    article_url: str
    published_at: datetime | None


@dataclass(frozen=True)
class FeedProbe:
    source_id: str
    publisher: str
    feed_url: str
    status: str
    http_status: int | None
    entry_count: int
    publisher_link_count: int
    newest_published_at: datetime | None
    etag: str | None = None
    last_modified: str | None = None
    error: str | None = None


class _TextOnly(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _plain_text(value: str | None) -> str:
    parser = _TextOnly()
    parser.feed(value or "")
    return " ".join(" ".join(parser.parts).split())


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(node: ElementTree.Element, *names: str) -> str | None:
    for name in names:
        for child in node:
            if _local_name(child.tag) == name:
                value = "".join(child.itertext()).strip()
                if value:
                    return value
    return None


def _entry_link(node: ElementTree.Element, atom: bool) -> str | None:
    if not atom:
        return _child_text(node, "link")
    for child in node:
        if _local_name(child.tag) == "link" and child.get("rel", "alternate") == "alternate":
            return child.get("href")
    return None


def _published(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        result = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)


def canonical_article_url(url: str, source: NewsSource) -> str | None:
    try:
        parsed = urlsplit(url.strip())
        if (parsed.scheme != "https" or not source.accepts_article_host(parsed.hostname) or
                parsed.username or parsed.password or parsed.port not in (None, 443)):
            return None
    except ValueError:
        return None
    canonical = urlunsplit(("https", parsed.hostname.lower(), parsed.path or "/", parsed.query, ""))
    return canonical if len(canonical.encode("utf-8")) <= MAX_ARTICLE_URL_BYTES else None


def parse_feed(content: bytes, source: NewsSource, feed_url: str) -> tuple[NewsEntry, ...]:
    """Parse bounded RSS 2.0 or Atom bytes; reject DTD/entity declarations."""
    if (len(content) > MAX_FEED_BYTES or b"\x00" in content[:200] or
            b"<!doctype" in content.lower() or b"<!entity" in content.lower()):
        raise ValueError("Feed exceeds size limit or contains an XML declaration not allowed here")
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise ValueError("Invalid feed XML") from exc
    kind = _local_name(root.tag)
    if kind == "rss":
        channel = next((child for child in root if _local_name(child.tag) == "channel"), None)
        if channel is None:
            raise ValueError("RSS channel is missing")
        nodes = [child for child in channel if _local_name(child.tag) == "item"]
        atom = False
    elif kind == "feed":
        nodes = [child for child in root if _local_name(child.tag) == "entry"]
        atom = True
    else:
        raise ValueError("Expected an RSS or Atom feed")

    entries: list[NewsEntry] = []
    for node in nodes:
        raw_link = _entry_link(node, atom)
        if not raw_link:
            continue
        article_url = canonical_article_url(urljoin(feed_url, raw_link), source)
        if not article_url:
            continue
        title = _plain_text(_child_text(node, "title"))[:500]
        if not title:
            continue
        excerpt = _plain_text(_child_text(node, "description", "summary", "content", "encoded"))[:5000]
        published_at = _published(_child_text(node, "pubdate", "published", "updated", "date"))
        feed_id = _child_text(node, "guid", "id") or article_url
        if len(feed_id.encode("utf-8")) > MAX_GUID_BYTES:
            feed_id = "sha256:" + hashlib.sha256(feed_id.encode("utf-8")).hexdigest()
        entries.append(NewsEntry(source.id, source.publisher, feed_url, feed_id, title, excerpt, article_url, published_at))
    return tuple(entries)


def _read_bounded_feed(client: httpx.Client, url: str, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
    original_host = urlsplit(url).hostname
    current_url = url
    for _ in range(MAX_REDIRECTS + 1):
        with client.stream("GET", current_url, headers=headers, follow_redirects=False) as response:
            if response.status_code in (301, 302, 303, 307, 308):
                target = urljoin(current_url, response.headers.get("location", ""))
                target_parts = urlsplit(target)
                original_base = (original_host or "").removeprefix("www.")
                target_base = (target_parts.hostname or "").removeprefix("www.")
                if (target_parts.scheme != "https" or target_base != original_base or
                        target_parts.username or target_parts.password or target_parts.port not in (None, 443)):
                    raise ValueError("Feed redirect left the configured HTTPS host")
                current_url = target
                continue
            body = bytearray()
            if response.status_code == 200:
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_FEED_BYTES:
                        raise ValueError("Feed response exceeds size limit")
            return response.status_code, dict(response.headers), bytes(body)
    raise ValueError("Too many feed redirects")


def probe_feed(
    source: NewsSource,
    feed_url: str,
    client: httpx.Client,
    *,
    etag: str | None = None,
    last_modified: str | None = None,
) -> tuple[FeedProbe, tuple[NewsEntry, ...]]:
    """Probe one configured candidate feed. Network and parse failures are explicit results."""
    if feed_url not in source.feed_urls:
        raise ValueError("Feed URL is not configured for this source")
    headers = {"User-Agent": "LANES-NewsDiscovery/0.1 (+https://github.com/pu-roi/LANES)"}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    try:
        status, response_headers, content = _read_bounded_feed(client, feed_url, headers)
        if status == 304:
            return FeedProbe(source.id, source.publisher, feed_url, "unchanged", status, 0, 0, None, etag, last_modified), ()
        if status != 200:
            return FeedProbe(source.id, source.publisher, feed_url, "http_error", status, 0, 0, None, error=f"HTTP {status}"), ()
        entries = parse_feed(content, source, feed_url)
        newest = max((entry.published_at for entry in entries if entry.published_at), default=None)
        last_modified = response_headers.get("last-modified")
        # Some publishers return a stale Last-Modified header for an actively updating feed.
        if newest and last_modified and (_published(last_modified) or datetime.min.replace(tzinfo=timezone.utc)) < newest:
            last_modified = None
        probe = FeedProbe(source.id, source.publisher, feed_url, "parsed" if entries else "empty", status,
                          len(entries), len(entries), newest,
                          response_headers.get("etag"), last_modified)
        return probe, entries
    except (httpx.HTTPError, ValueError) as exc:
        return FeedProbe(source.id, source.publisher, feed_url, "failed", None, 0, 0, None, error=str(exc)), ()
