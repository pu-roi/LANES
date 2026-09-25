"""Pasig flood shortlisting and safe article retrieval; never creates map reports."""

from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.news_feed_service import FeedProbe, NewsEntry, canonical_article_url, probe_feed
from app.services.news_sources import NewsSource


# Broad discovery terms; NER and staff review decide whether a real flood occurred.
FLOOD_TERMS = re.compile(
    r"\b(?:baha|binaha|binabaha|pagbaha|bumaha|bumabaha|flood|flooded|flooding|"
    r"inundat(?:ed|ion)|lubog|nalubog|submerged|lagpas\s+tuhod|knee[-\s]deep|ankle[-\s]deep)\b",
    re.I,
)
# Snapshot of data/pasig_barangay_reference.csv (30 PSGC-backed Pasig barangays).
PASIG_BARANGAYS = (
    "Bagong Ilog", "Bagong Katipunan", "Bambang", "Buting", "Caniogan", "Dela Paz", "Kalawaan",
    "Kapasigan", "Kapitolyo", "Malinao", "Manggahan", "Maybunga", "Oranbo",
    "Palatiw", "Pinagbuhatan", "Pineda", "Rosario", "Sagad", "San Antonio",
    "San Joaquin", "San Jose", "San Miguel", "San Nicolas", "Santa Cruz", "Santa Rosa",
    "Santo Tomas", "Santolan", "Sumilang", "Ugong", "Santa Lucia",
)
PLACE_TERMS = tuple(re.compile(r"(?<!\w)" + re.escape(name) + r"(?!\w)", re.I) for name in ("Pasig", *PASIG_BARANGAYS))
MAX_ARTICLE_BYTES = 1_000_000
MIN_ARTICLE_CHARS = 120
MAX_NEWS_AGE = timedelta(days=7)


@dataclass(frozen=True)
class NewsCandidate:
    source_id: str
    publisher: str
    feed_id: str
    article_url: str
    title: str
    excerpt: str
    published_at: datetime | None
    fetched_at: datetime
    article_text: str | None
    article_error: str | None


@dataclass(frozen=True)
class DiscoveryRun:
    probes: tuple[FeedProbe, ...]
    candidates: tuple[NewsCandidate, ...]


def likely_pasig_flood(entry: NewsEntry) -> bool:
    """Broad shortlist only; location and flood facts still need NER and review."""
    text = f"{entry.title} {entry.excerpt}"
    return bool(FLOOD_TERMS.search(text) and any(pattern.search(text) for pattern in PLACE_TERMS))


def likely_philippine_flood(entry: NewsEntry) -> bool:
    """Broad nationwide flood detection across Luzon, Visayas, and Mindanao."""
    text = f"{entry.title} {entry.excerpt}"
    if not FLOOD_TERMS.search(text):
        return False
    if likely_pasig_flood(entry):
        return True
    from app.services.philippine_location_service import get_philippine_location_service
    loc_service = get_philippine_location_service()
    lower_text = text.lower()
    for prov in loc_service.provinces:
        if len(prov) >= 4 and re.search(rf"\b{re.escape(prov)}\b", lower_text):
            return True
    for city in loc_service.cities:
        if len(city) >= 4 and re.search(rf"\b{re.escape(city)}\b", lower_text):
            return True
    return False


class _ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.article_depth = 0
        self.skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "nav", "footer", "aside"}:
            self.skip_depth += 1
        if tag in {"article", "main"}:
            self.article_depth += 1
        if tag in {"p", "h1", "h2", "h3", "br"} and self.article_depth and not self.skip_depth:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"article", "main"} and self.article_depth:
            self.article_depth -= 1
        if tag in {"script", "style", "nav", "footer", "aside"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.article_depth and not self.skip_depth:
            self.parts.append(data)


def fetch_article_text(source: NewsSource, article_url: str, client: httpx.Client) -> tuple[str | None, str | None]:
    """Fetch a public article from an approved publisher domain with strict bounds."""
    if canonical_article_url(article_url, source) is None:
        return None, "Article URL is outside the publisher domains"
    current_url = article_url
    try:
        for _ in range(4):
            with client.stream("GET", current_url, follow_redirects=False,
                               headers={"User-Agent": "LANES-NewsDiscovery/0.1 (+https://github.com/pu-roi/LANES)"}) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    target = urljoin(current_url, response.headers.get("location", ""))
                    if canonical_article_url(target, source) is None:
                        return None, "Article redirect left the publisher domains"
                    current_url = target
                    continue
                if response.status_code != 200:
                    return None, f"Article HTTP {response.status_code}"
                if "html" not in response.headers.get("content-type", "").lower():
                    return None, "Article response is not HTML"
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_ARTICLE_BYTES:
                        return None, "Article response exceeds size limit"
                parser = _ArticleParser()
                parser.feed(body.decode(response.encoding or "utf-8", errors="replace"))
                text = " ".join(" ".join(parser.parts).split())[:30_000]
                if len(text) < MIN_ARTICLE_CHARS:
                    return None, "Article text unavailable or too short"
                return text, None
        return None, "Too many article redirects"
    except (httpx.HTTPError, ValueError) as exc:
        return None, str(exc)


def discover_news(sources: tuple[NewsSource, ...], client: httpx.Client, db: Session | None = None) -> DiscoveryRun:
    """Run verified feeds; with a session, persist checkpoints and shortlisted evidence."""
    # Local import avoids coupling the read-only probe path to database operations.
    from app.crud import news as news_crud

    probes: list[FeedProbe] = []
    candidates: list[NewsCandidate] = []
    seen_urls: set[str] = set()
    seen_fingerprints: set[tuple[str, str, str]] = set()
    for source in sources:
        if not source.enabled or source.verified_at is None:
            continue
        for feed_url in source.feed_urls:
            if db is not None and db.get_bind().dialect.name == "postgresql":
                # Cloud Scheduler may retry a job while the earlier run is active.
                db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:feed_url))"), {"feed_url": feed_url})
            checkpoint = news_crud.get_checkpoint(db, feed_url) if db is not None else None
            probe, entries = probe_feed(
                source, feed_url, client,
                etag=checkpoint.etag if checkpoint else None,
                last_modified=checkpoint.last_modified if checkpoint else None,
            )
            probes.append(probe)
            for entry in entries:
                fingerprint = (
                    source.id,
                    " ".join(re.findall(r"\w+", entry.title.casefold())),
                    " ".join(re.findall(r"\w+", entry.excerpt.casefold())),
                )
                if ((entry.published_at is not None and
                         entry.published_at < datetime.now(timezone.utc) - MAX_NEWS_AGE) or
                        not likely_philippine_flood(entry)):
                    continue
                existing = news_crud.get_article(db, entry.article_url) if db is not None else None
                normalized = " ".join(re.findall(r"\w+", f"{entry.title} {entry.excerpt}".casefold()))
                digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                duplicate = (entry.article_url in seen_urls or
                             (entry.excerpt and fingerprint in seen_fingerprints))
                seen_urls.add(entry.article_url)
                if entry.excerpt:
                    seen_fingerprints.add(fingerprint)
                if duplicate or (existing is not None and existing.content_fingerprint == digest
                                 and existing.article_text is not None):
                    if db is not None:
                        news_crud.save_candidate(db, entry, None)
                    continue
                article_text, article_error = fetch_article_text(source, entry.article_url, client)
                candidate = NewsCandidate(
                    source_id=entry.source_id,
                    publisher=entry.publisher,
                    feed_id=entry.feed_id,
                    article_url=entry.article_url,
                    title=entry.title,
                    excerpt=entry.excerpt,
                    published_at=entry.published_at,
                    fetched_at=datetime.now(timezone.utc),
                    article_text=article_text,
                    article_error=article_error,
                )
                candidates.append(candidate)
                if db is not None:
                    news_crud.save_candidate(db, entry, candidate)
            if db is not None:
                news_crud.save_checkpoint(db, probe)
                db.commit()
    return DiscoveryRun(tuple(probes), tuple(candidates))
