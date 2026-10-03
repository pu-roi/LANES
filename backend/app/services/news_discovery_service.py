"""Metro Manila flood shortlisting and safe article retrieval; never creates map reports."""

from __future__ import annotations

import re
import hashlib
import json
from typing import TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlsplit

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.news_extraction import NewsArticleExtractorInput, NewsExtractionResult
from app.services.news_feed_service import FeedProbe, NewsEntry, canonical_article_url, probe_feed
from app.services.news_sources import NewsSource

if TYPE_CHECKING:
    from app.models.news import NewsArticle


# Broad discovery terms; body evidence and geographic gates qualify local leads.
FLOOD_TERMS = re.compile(
    r"\b(?:baha|binaha|binabaha|pagbaha|bumaha|bumabaha|floods?|flooded|flooding|"
    r"floodwaters?|inundat(?:ed|ion)|lubog|nalubog|submerged|lagpas\s+tuhod|knee[-\s]deep|ankle[-\s]deep)\b",
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
MAX_ARTICLE_CHARS = 100_000
MIN_ARTICLE_CHARS = 120
MAX_NEWS_AGE = timedelta(days=7)
MAX_LOCATION_BODY_PROBES = 5


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
class DiscoveryNotice:
    source_id: str
    article_url: str
    reason: str


@dataclass(frozen=True)
class DiscoveryRun:
    probes: tuple[FeedProbe, ...]
    candidates: tuple[NewsCandidate, ...]
    notices: tuple[DiscoveryNotice, ...] = ()


@dataclass(frozen=True)
class CandidateExtraction:
    article_url: str
    extraction: NewsExtractionResult | None
    error: str | None = None
    article_id: int | None = None
    input_fingerprint: str | None = None


async def extract_discovery_candidates(run: DiscoveryRun) -> tuple[CandidateExtraction, ...]:
    """Exercise collection-to-extraction without DB writes or external audit calls.

    This diagnostic does not invoke ingestion or turn preview geometry into
    public zones. Missing bodies and individual extraction failures remain visible.
    """
    inputs: list[tuple[NewsArticleExtractorInput, str | None]] = []
    for index, candidate in enumerate(run.candidates, start=1):
        article = NewsArticleExtractorInput(
            article_id=-index, canonical_url=candidate.article_url, publisher=candidate.publisher,
            title=candidate.title, excerpt=candidate.excerpt, article_text=candidate.article_text,
            published_at=candidate.published_at, fetched_at=candidate.fetched_at,
        )
        inputs.append((article, candidate.article_error))
    return await _extract_article_inputs(inputs)


async def extract_saved_news_articles(articles: list[NewsArticle]) -> tuple[CandidateExtraction, ...]:
    """Read saved snapshots with real IDs; never commits or invokes ingestion.

    This prepares the persistent worker handoff. It does not store extraction
    results, change review state, retry network retrieval, or call an auditor.
    """
    def aware(value: datetime | None) -> datetime | None:
        return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value

    inputs = [(NewsArticleExtractorInput(
        article_id=article.id, canonical_url=article.canonical_url, publisher=article.publisher_source_id,
        title=article.title, excerpt=article.excerpt or "", article_text=article.article_text,
        published_at=aware(article.published_at), fetched_at=aware(article.fetched_at),
    ), article.article_error) for article in articles]
    return await _extract_article_inputs(inputs)


async def _extract_article_inputs(
    inputs: list[tuple[NewsArticleExtractorInput, str | None]],
) -> tuple[CandidateExtraction, ...]:
    from app.services.hybrid_extraction_service import HybridExtractionService
    from app.services.news_road_placement_service import get_news_road_placement_provider

    extractor = HybridExtractionService()
    results: list[CandidateExtraction] = []
    for article, body_error in inputs:
        # Fetch time is not evidence content and cannot create a new version.
        _, fingerprint = extraction_input_snapshot(article)
        error = body_error
        if not error and not article.article_text:
            error = "Article body unavailable"
        if not error and len(article.article_text or "") > MAX_ARTICLE_CHARS:
            error = "Article text exceeds processing limit"
        if error:
            results.append(CandidateExtraction(article.canonical_url, None, error, article.article_id, fingerprint))
            continue
        try:
            extraction = await extractor.extract_hybrid(article, mode="rules_only")
            provider = get_news_road_placement_provider()
            for claim in extraction.claims:
                claim.road_placement = provider.resolve(claim)
        except Exception as exc:
            results.append(CandidateExtraction(article.canonical_url, None,
                                               f"Extraction failed: {type(exc).__name__}", article.article_id, fingerprint))
            continue
        results.append(CandidateExtraction(article.canonical_url, extraction, None, article.article_id, fingerprint))
    return tuple(results)


def extraction_input_snapshot(article: NewsArticleExtractorInput) -> tuple[dict, str]:
    """Canonical immutable evidence identity shared by previews and storage."""
    snapshot = article.model_dump(mode="json", exclude={"article_id", "fetched_at"})
    if article.published_at:
        publication = article.published_at
        if publication.tzinfo is None:
            publication = publication.replace(tzinfo=timezone.utc)
        snapshot["published_at"] = publication.astimezone(timezone.utc).isoformat()
    fingerprint = hashlib.sha256(json.dumps(snapshot, ensure_ascii=False, sort_keys=True,
                                             separators=(",", ":")).encode("utf-8")).hexdigest()
    return snapshot, fingerprint


async def extract_captured_news_article(article: NewsArticleExtractorInput) -> CandidateExtraction:
    """Extract one captured snapshot without audit, ingestion, or SQL writes."""
    return (await _extract_article_inputs([(article, None)]))[0]


def likely_pasig_flood(entry: NewsEntry) -> bool:
    """Broad shortlist only; location and flood facts still need NER and review."""
    text = f"{entry.title} {entry.excerpt}"
    return bool(FLOOD_TERMS.search(text) and any(pattern.search(text) for pattern in PLACE_TERMS))


METRO_MANILA_TERMS = re.compile(
    r"\b(?:Metro\s+Manila|National\s+Capital\s+Region|NCR|"
    r"Caloocan|Las\s+Pi(?:ñ|n)as|Makati|Malabon|Mandaluyong|Manila|Marikina|"
    r"Muntinlupa|Navotas|Para(?:ñ|n)aque|Pasay|Pasig|Quezon\s+City|"
    r"San\s+Juan\s+City|Taguig|Valenzuela|Pateros|EDSA)\b",
    re.I,
)


def likely_metro_manila_flood(entry: NewsEntry) -> bool:
    """Shortlist flood entries with a Metro Manila place in RSS metadata.

    Place-free headlines are skipped before article retrieval. This reduces
    collector work but may miss reports whose location appears only in the body.
    """
    text = f"{entry.title} {entry.excerpt}"
    return bool(FLOOD_TERMS.search(text) and METRO_MANILA_TERMS.search(text))


def body_has_metro_manila_flood_claim(entry: NewsEntry, body: str) -> bool:
    """Shortlist body-grounded local claims; this is not event verification."""
    from app.services.taglish_extraction_service import extract_taglish_flood_facts
    from app.services.news_evidence_policy import has_flood_observation, metro_manila_claim

    result = extract_taglish_flood_facts(NewsArticleExtractorInput(
        article_id=-1, canonical_url=entry.article_url, publisher=entry.publisher,
        title=entry.title, excerpt=entry.excerpt, article_text=body, published_at=entry.published_at,
    ))
    return any(
        claim.flood_mentioned and not claim.is_negated and not claim.is_forecast and not claim.is_historical
        and claim.condition in {"active", "rising", "receding", "subsided"}
        and "photo_caption_only" not in claim.uncertainty_reasons
        and metro_manila_claim(claim) and has_flood_observation(claim.evidence_sentence)
        for claim in result.claims
    )


def metadata_names_only_outside_metro_places(entry: NewsEntry) -> bool:
    """Avoid spending location probes on clearly non-local feed headlines."""
    from app.services.taglish_extraction_service import extract_taglish_flood_facts

    result = extract_taglish_flood_facts(NewsArticleExtractorInput(
        article_id=-1, canonical_url=entry.article_url, publisher=entry.publisher,
        title=entry.title, excerpt=entry.excerpt, published_at=entry.published_at,
    ))
    places = [claim for claim in result.claims if claim.psgc_code and claim.place_type in {"city", "province"}]
    return bool(places) and all(not claim.psgc_code.startswith("13") for claim in places)


def previously_verified_article(db: Session, entry: NewsEntry, article: NewsArticle) -> bool:
    """Recognize stored flood evidence before evaluating a correction's headline."""
    from dataclasses import replace
    stored_entry = replace(entry, title=article.title, excerpt=article.excerpt or "",
                           published_at=article.published_at)
    if article.article_text and body_has_metro_manila_flood_claim(stored_entry, article.article_text):
        return True
    # After a denial replaces the current body, its original verified input
    # remains history. Further corrections to that known article are legitimate.
    from app.crud.news_results import result_rows, readable_claim, readable_run
    from app.models.news import NewsArticleVersion
    history, value, _, _ = result_rows(db)
    return db.execute(history.where(NewsArticleVersion.article_id == article.id,
        readable_claim(value), readable_run(db)).limit(1)).first() is not None


class _ArticleParser(HTMLParser):
    def __init__(self, source_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self.source_id = source_id
        self.article_depth = 0
        self.skip_depth = 0
        self.related_div_depth = 0
        self.selected_div_depth = 0
        self.related_heading = False
        self.related_list_pending = False
        self.related_list_depth = 0
        self.parts: list[str] = []
        self.has_continuation = False
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.source_id == "feedspot-03":
            if self.related_list_pending and not self.related_heading and tag != "ul":
                self.related_list_pending = False
            if tag == "h6" and any(name == "id" and value == "h-also-on-rappler" for name, value in attrs):
                self.related_heading = True
                self.related_list_pending = True
                self.skip_depth += 1
            elif tag == "ul" and (self.related_list_pending or self.related_list_depth):
                if not self.related_list_depth:
                    self.related_list_pending = False
                    self.skip_depth += 1
                self.related_list_depth += 1
        if tag == "div":
            attr = dict(attrs)
            classes = set((attr.get("class") or "").split())
            if self.related_div_depth:
                self.related_div_depth += 1
            elif (attr.get("id") in {"mrect_related_content_holder", "related_block", "load_more"} or
                  (self.source_id == "feedspot-01" and bool(classes & {"lower_article", "ivs-placeholder-more-videos"})) or
                  (self.source_id == "feedspot-03" and "related-article" in classes)):
                self.related_div_depth = 1
            selected = (
                (self.source_id == "daily-tribune" and "story-text" in classes) or
                (self.source_id == "feedspot-05" and attr.get("id") == "sports_article_writeup") or
                (self.source_id == "feedspot-03" and "post-single__content" in classes) or
                (self.source_id == "feedspot-07" and "entry-content" in classes)
            )
            if self.selected_div_depth:
                self.selected_div_depth += 1
            elif selected:
                self.selected_div_depth = 1
                self.article_depth += 1
        if tag == "a":
            href = next((value for name, value in attrs if name == "href"), None)
            if href:
                self.links.append(href)
        if tag in {"a", "link"} and (tag == "link" or self.article_depth):
            rel = next((value for name, value in attrs if name == "rel"), None)
            if rel and "next" in rel.casefold().split():
                self.has_continuation = True
        if tag in {"script", "style", "nav", "footer", "aside"}:
            self.skip_depth += 1
        if tag in {"article", "main"} and self.source_id not in {"feedspot-03", "feedspot-07", "daily-tribune"}:
            self.article_depth += 1
        if tag in {"p", "h1", "h2", "h3", "li", "br"} and self.article_depth and not self.skip_depth and not self.related_div_depth:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "h6" and self.related_heading:
            self.related_heading = False
            self.skip_depth -= 1
        if tag == "ul" and self.related_list_depth:
            self.related_list_depth -= 1
            if not self.related_list_depth:
                self.skip_depth -= 1
        if tag in {"p", "h1", "h2", "h3", "li"} and self.article_depth and not self.skip_depth and not self.related_div_depth:
            self.parts.append("\n")
        if tag == "div" and self.related_div_depth:
            self.related_div_depth -= 1
        if tag == "div" and self.selected_div_depth:
            self.selected_div_depth -= 1
            if not self.selected_div_depth:
                self.article_depth -= 1
        if tag in {"article", "main"} and self.article_depth and self.source_id not in {"feedspot-03", "feedspot-07", "daily-tribune"}:
            self.article_depth -= 1
        if tag in {"script", "style", "nav", "footer", "aside"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.article_depth and not self.skip_depth and not self.related_div_depth:
            self.parts.append(data)


def _same_article_continuation(article_url: str, href: str) -> bool:
    """Recognize common page-two URLs without confusing publisher next-story loaders."""
    current = urlsplit(article_url)
    target = urlsplit(urljoin(article_url, href))
    if target.netloc.casefold() != current.netloc.casefold() or target.scheme not in {"http", "https"}:
        return False
    current_path = current.path.rstrip("/")
    target_path = target.path.rstrip("/")
    if current_path == target_path:
        current_query = parse_qs(current.query)
        target_query = parse_qs(target.query)
        for key in ("page", "next"):
            current_pages = current_query.get(key, ["1"])
            target_pages = target_query.get(key, [])
            if (target_pages and target_pages != current_pages and
                    any(page.isdigit() and int(page) > 1 for page in target_pages)):
                return True
        return False
    return bool(re.fullmatch(re.escape(current_path) + r"/(?:page/)?[2-9]\d*", target_path))


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
                    if response.status_code == 403 and response.headers.get("cf-mitigated", "").casefold() == "challenge":
                        return None, "Article access blocked by publisher challenge (HTTP 403)"
                    return None, f"Article HTTP {response.status_code}"
                if "html" not in response.headers.get("content-type", "").lower():
                    return None, "Article response is not HTML"
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_ARTICLE_BYTES:
                        return None, "Article response exceeds size limit"
                # Tribune streams its reporting paragraphs after the enclosing
                # <article> closes. Read only those named body containers, not
                # unrelated stories or embedded JavaScript/JSON summaries.
                publisher_host = (urlsplit(current_url).hostname or "").removeprefix("www.")
                parser = _ArticleParser("daily-tribune" if publisher_host == "tribune.net.ph"
                                        and "/amp/story/" not in urlsplit(current_url).path else source.id)
                parser.feed(body.decode(response.encoding or "utf-8", errors="replace"))
                if parser.has_continuation or any(
                    _same_article_continuation(current_url, href) for href in parser.links
                ):
                    return None, "Article has a continuation page; full body was not extracted"
                # Keep paragraph/list boundaries: flattening a multi-location
                # list into one sentence assigns one road's depth to another.
                lines = (" ".join(line.split()) for line in "".join(parser.parts).splitlines())
                text = "\n".join(line for line in lines if line)
                if len(text) > MAX_ARTICLE_CHARS:
                    return None, "Article text exceeds processing limit; full body was not extracted"
                if len(text) < MIN_ARTICLE_CHARS:
                    return None, "Article text unavailable or too short"
                return text, None
        return None, "Too many article redirects"
    except (httpx.HTTPError, ValueError) as exc:
        return None, str(exc)


def discover_news(sources: tuple[NewsSource, ...], client: httpx.Client, db: Session | None = None,
                  *, actor_id: int | None = None) -> DiscoveryRun:
    """Persist operational attempts for staff and collector; dry runs stay pure."""
    if db is None:
        return _discover_news(sources, client)
    from app.services.news_telemetry_service import begin_discovery, finish_discovery
    id = begin_discovery(db, actor_id)
    try:
        result = _discover_news(sources, client, db, telemetry_id=id)
        finish_discovery(db, id, "feed_partial_failure" if any(probe.error for probe in result.probes) else None)
        return result
    except Exception:
        db.rollback()
        finish_discovery(db, id, "discovery_failed")
        raise


def _discover_news(sources: tuple[NewsSource, ...], client: httpx.Client, db: Session | None = None,
                   *, telemetry_id: int | None = None) -> DiscoveryRun:
    """Run verified feeds; with a session, persist checkpoints and shortlisted evidence."""
    # Local import avoids coupling the read-only probe path to database operations.
    from app.crud import news as news_crud

    probes: list[FeedProbe] = []
    candidates: list[NewsCandidate] = []
    seen_urls: set[str] = set()
    seen_fingerprints: set[tuple[str, str, str]] = set()
    accepted_urls: set[str] = set()
    notices: list[DiscoveryNotice] = []
    body_probes = 0
    for source in sources:
        if not source.enabled or source.verified_at is None:
            continue
        for feed_url in source.feed_urls:
            checked_at = datetime.now(timezone.utc)
            saved_urls: set[str] = set()
            body_errors = 0
            scope_unresolved = 0
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
            # Keep metadata-local leads first; extra body probes cannot consume
            # their retrieval allowance. The five-probe budget covers the run.
            for entry in sorted(entries, key=lambda item: (
                    not likely_metro_manila_flood(item),
                    -(item.published_at.timestamp() if item.published_at else float("-inf")))):
                fingerprint = (
                    source.id,
                    " ".join(re.findall(r"\w+", entry.title.casefold())),
                    " ".join(re.findall(r"\w+", entry.excerpt.casefold())),
                )
                now = datetime.now(timezone.utc)
                if entry.published_at is not None and entry.published_at < now - MAX_NEWS_AGE:
                    continue
                if entry.published_at is not None and entry.published_at > now:
                    notices.append(DiscoveryNotice(source.id, entry.article_url, "Publication time is in the future"))
                    continue
                existing = news_crud.get_article(db, entry.article_url) if db is not None else None
                def utc(value: datetime) -> datetime:
                    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

                if (existing is not None and existing.published_at and entry.published_at
                        and utc(entry.published_at) < utc(existing.published_at)):
                    notices.append(DiscoveryNotice(source.id, entry.article_url, "Older feed revision cannot replace newer stored evidence"))
                    continue
                metadata_local = likely_metro_manila_flood(entry)
                has_flood_metadata = bool(FLOOD_TERMS.search(f"{entry.title} {entry.excerpt}"))
                metadata_outside = not metadata_local and metadata_names_only_outside_metro_places(entry)
                if not has_flood_metadata or metadata_outside:
                    known_evidence = existing is not None and previously_verified_article(db, entry, existing)
                    if not known_evidence:
                        if metadata_outside:
                            notices.append(DiscoveryNotice(source.id, entry.article_url, "Feed metadata names only non-Metro Manila places"))
                        continue
                    metadata_local = True  # A known article correction needs no new location probe.
                normalized = " ".join(re.findall(r"\w+", f"{entry.title} {entry.excerpt}".casefold()))
                digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                duplicate = (entry.article_url in seen_urls or
                             (entry.excerpt and fingerprint in seen_fingerprints))
                seen_urls.add(entry.article_url)
                if duplicate:
                    if db is not None and entry.article_url in accepted_urls:
                        news_crud.save_candidate(db, entry, None)
                        saved_urls.add(entry.article_url)
                    continue
                same_publication = (existing is not None and
                                    (entry.published_at is None or (existing.published_at is not None and
                                     utc(entry.published_at) == utc(existing.published_at))))
                if (existing is not None and existing.content_fingerprint == digest
                        and existing.article_text is not None and existing.article_error is None and same_publication):
                    if body_has_metro_manila_flood_claim(entry, existing.article_text):
                        accepted_urls.add(entry.article_url)
                        if entry.excerpt:
                            seen_fingerprints.add(fingerprint)
                        if db is not None:
                            news_crud.save_candidate(db, entry, None)
                            saved_urls.add(entry.article_url)
                    else:
                        notices.append(DiscoveryNotice(source.id, entry.article_url, "No body-grounded Metro Manila flood claim"))
                    continue
                if not metadata_local:
                    if body_probes >= MAX_LOCATION_BODY_PROBES:
                        scope_unresolved += 1
                        notices.append(DiscoveryNotice(source.id, entry.article_url, "Location body-probe limit reached; scope unresolved"))
                        continue
                    body_probes += 1
                article_text, article_error = fetch_article_text(source, entry.article_url, client)
                if article_error:
                    body_errors += 1
                # A prior publisher denial can be the current body while its
                # original verified flood evidence remains in history. Keep a
                # later retrieval failure visible for that known article too,
                # including when the revised metadata lacks a local place clue.
                if (article_text is None and db is not None and existing is not None
                        and previously_verified_article(db, entry, existing)):
                    failed = NewsCandidate(source_id=entry.source_id, publisher=entry.publisher,
                        feed_id=entry.feed_id, article_url=entry.article_url, title=entry.title,
                        excerpt=entry.excerpt, published_at=entry.published_at,
                        fetched_at=datetime.now(timezone.utc), article_text=None, article_error=article_error)
                    news_crud.save_candidate(db, entry, failed)
                if not metadata_local:
                    if article_text is None:
                        scope_unresolved += 1
                        notices.append(DiscoveryNotice(source.id, entry.article_url,
                                                       f"Location unresolved: {article_error or 'article body unavailable'}"))
                        continue
                # A local headline cannot qualify an unreadable article. Keep
                # failed refresh diagnostics only for previously verified flood
                # evidence, without admitting a new candidate or relabeling it.
                if article_text is None:
                    notices.append(DiscoveryNotice(source.id, entry.article_url,
                        f"Article not collected: body verification unavailable ({article_error or 'no article text'})"))
                    continue
                if article_text is not None and not body_has_metro_manila_flood_claim(entry, article_text):
                    notices.append(DiscoveryNotice(source.id, entry.article_url, "No body-grounded Metro Manila flood claim"))
                    # A successfully retrieved correction must supersede the
                    # current body of an article already admitted on verified
                    # evidence. Otherwise a denial, forecast-only revision or
                    # changed event can leave its earlier flood claim current
                    # indefinitely. New unrelated leads remain excluded.
                    if existing is None or not (existing.article_text or "").strip():
                        continue
                accepted_urls.add(entry.article_url)
                if entry.excerpt:
                    seen_fingerprints.add(fingerprint)
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
                    saved_urls.add(entry.article_url)
            if db is not None:
                news_crud.save_checkpoint(db, probe)
                if telemetry_id is not None:
                    from app.models.news_telemetry import NewsDiscoveryFeedRun
                    db.add(NewsDiscoveryFeedRun(discovery_run_id=telemetry_id, source_id=source.id,
                        feed_url=feed_url, status=probe.status, checked_at=checked_at,
                        error_code="feed_probe_failed" if probe.error else None, entries_seen=len(entries),
                        candidates_saved=len(saved_urls), body_errors=body_errors, scope_unresolved=scope_unresolved))
                db.commit()
    return DiscoveryRun(tuple(probes), tuple(candidates), tuple(notices))
