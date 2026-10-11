"""September 9 replay through real RSS discovery, durable processing and readers.

RSS snapshots are reconstructed from verified article metadata, not archived
historical feeds. Publisher HTML is captured privately and parsed by the normal
article fetcher. Writes are restricted to the dedicated loopback test database.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import ExitStack, contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timezone
from email.utils import format_datetime
import hashlib
import json
from pathlib import Path
from typing import Iterator
from unittest.mock import patch
from xml.etree import ElementTree as ET

import httpx

from scripts.seed_local_news_replay import require_local_test_database

CAPTURE_DIR = Path(__file__).resolve().parents[2] / "data/news-replay/september9"
REPLAY_AT = datetime.fromisoformat("2026-09-09T23:00:00+08:00")
TEST_LABEL = "local historical test"


@dataclass(frozen=True)
class ArticleSpec:
    number: int
    source_id: str
    url: str
    title: str
    published_at: datetime
    updated_at: datetime | None = None


ARTICLES = (
    ArticleSpec(1, "feedspot-05", "https://www.philstar.com/nation/2026/09/09/2555106/list-flooded-metro-manila-areas-september-9/amp/",
                "LIST: Flooded Metro Manila areas on September 9", datetime.fromisoformat("2026-09-09T17:03:00+08:00")),
    ArticleSpec(2, "feedspot-01", "https://www.gmanetwork.com/news/topstories/metro/1001693/list-flooded-roads-in-metro-manila-wednesday-sept-9-2026/story/",
                "FLOOD ALERT: Flooded roads in Metro Manila on Wednesday, September 9, 2026",
                datetime.fromisoformat("2026-09-09T09:19:06+08:00"), datetime.fromisoformat("2026-09-09T15:09:00+08:00")),
    ArticleSpec(3, "feedspot-01", "https://www.gmanetwork.com/news/weather/content/1001808/several-metro-manila-areas-flood-due-to-habagat/story/",
                "Several Metro Manila areas flood due to Habagat", datetime.fromisoformat("2026-09-09T21:24:42+08:00")),
)


def source_timing() -> list[dict]:
    return [{"url": spec.url, "published_at": spec.published_at.isoformat(),
             "updated_at": spec.updated_at.isoformat() if spec.updated_at else None,
             "snapshot_available_no_earlier_than": (spec.updated_at or spec.published_at).isoformat()}
            for spec in ARTICLES]


def reconstructed_feed(specs: tuple[ArticleSpec, ...]) -> bytes:
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "Reconstructed September 9 local historical test"
    for spec in specs:
        item = ET.SubElement(channel, "item")
        for tag, value in (("title", spec.title), ("link", spec.url), ("guid", spec.url),
                           ("description", "Historical September 9 Metro Manila flood report; not a current alert."),
                           ("pubDate", format_datetime(spec.published_at))):
            ET.SubElement(item, tag).text = value
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def replay_sources() -> tuple:
    from app.services.news_sources import load_news_sources
    sources = {source.id: source for source in load_news_sources()}
    return tuple(replace(sources[source_id], enabled=True, verified_at=date(2026, 9, 9),
        feed_urls=(sources[source_id].feed_urls[0] + "?lanes_historical_test=2026-09-09",))
        for source_id in dict.fromkeys(spec.source_id for spec in ARTICLES))


class ReplayClock(datetime):
    @classmethod
    def now(cls, tz=None) -> datetime:
        return REPLAY_AT.astimezone(tz) if tz is not None else REPLAY_AT.replace(tzinfo=None)


@contextmanager
def replay_clock() -> Iterator[None]:
    # Only this one-shot process is patched. Runtime source configuration and
    # extraction's historical activation guards remain unchanged.
    from app.crud import news, news_processing
    from app.services import news_discovery_service, news_telemetry_service, taglish_extraction_service
    with ExitStack() as stack:
        for module in (news, news_discovery_service, news_telemetry_service, taglish_extraction_service):
            stack.enter_context(patch.object(module, "datetime", ReplayClock))
        stack.enter_context(patch.object(news_processing, "utc_now", lambda: REPLAY_AT))
        yield


def fixture_client(capture_dir: Path, request_log: list[str]) -> httpx.Client:
    feeds = {source.feed_urls[0]: reconstructed_feed(tuple(spec for spec in ARTICLES if spec.source_id == source.id))
             for source in replay_sources()}
    articles = {spec.url: capture_dir / f"article-{spec.number}.html" for spec in ARTICLES}

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        request_log.append(url)
        if url in feeds:
            return httpx.Response(200, content=feeds[url], headers={"content-type": "application/rss+xml"})
        if url in articles:
            return httpx.Response(200, content=articles[url].read_bytes(), headers={"content-type": "text/html; charset=utf-8"})
        raise RuntimeError("Replay attempted an unrecorded network resource")

    return httpx.Client(transport=httpx.MockTransport(handler))


def capture_articles(capture_dir: Path) -> list[dict]:
    from app.services.news_discovery_service import fetch_article_text
    sources = {source.id: source for source in replay_sources()}
    capture_dir.mkdir(parents=True, exist_ok=True)
    metadata = []
    captured_responses: list[tuple[int, bytes]] = []

    class RecordingStream(httpx.SyncByteStream):
        def __init__(self, response: httpx.Response) -> None:
            self.response, self.parts = response, bytearray()

        def __iter__(self) -> Iterator[bytes]:
            # Consumption remains driven by fetch_article_text's byte limit;
            # recording must not eagerly read an unbounded publisher response.
            for chunk in self.response.iter_bytes():
                self.parts.extend(chunk)
                yield chunk

        def close(self) -> None:
            captured_responses.append((self.response.status_code, bytes(self.parts)))
            self.response.close()

    class RecordingTransport(httpx.BaseTransport):
        def __init__(self) -> None:
            self.transport = httpx.HTTPTransport(trust_env=False)

        def handle_request(self, request: httpx.Request) -> httpx.Response:
            response = self.transport.handle_request(request)
            headers = dict(response.headers)
            # The inner stream supplies decoded HTML. Prevent the outer
            # fetcher's httpx response from decompressing the same bytes twice.
            headers.pop("content-encoding", None)
            headers.pop("content-length", None)
            return httpx.Response(response.status_code, headers=headers, request=request,
                stream=RecordingStream(response), extensions=response.extensions)

        def close(self) -> None:
            self.transport.close()

    with httpx.Client(timeout=45, trust_env=False, transport=RecordingTransport()) as client:
        for spec in ARTICLES:
            captured_responses.clear()
            body, error = fetch_article_text(sources[spec.source_id], spec.url, client)
            if error or not body:
                raise RuntimeError(f"Article {spec.number} retrieval failed: {error}")
            status, raw_html = captured_responses[-1]
            if status != 200:
                raise RuntimeError("Successful capture did not finish at a publisher HTTP-200 response")
            (capture_dir / f"article-{spec.number}.html").write_bytes(raw_html)
            (capture_dir / f"article-{spec.number}-body.txt").write_text(body, encoding="utf-8")
            facts = {"number": spec.number, "url": spec.url, "source_id": spec.source_id,
                     "published_at": spec.published_at.isoformat(),
                     "updated_at": spec.updated_at.isoformat() if spec.updated_at else None,
                     "body_characters": len(body), "body_sha256": hashlib.sha256(body.encode()).hexdigest(),
                     "captured_at": datetime.now(timezone.utc).isoformat(),
                     "publication_evidence": "visible publisher time element; Philstar JSON-LD incorrectly reports 1970" if spec.number == 1 else "publisher time element and JSON-LD"}
            (capture_dir / f"article-{spec.number}-metadata.json").write_text(json.dumps(facts, indent=2), encoding="utf-8")
            metadata.append(facts)
    return metadata


async def preview(capture_dir: Path) -> dict:
    from app.services.news_discovery_service import discover_news, extract_discovery_candidates
    requests: list[str] = []
    with replay_clock(), fixture_client(capture_dir, requests) as client:
        discovery = discover_news(replay_sources(), client)
        extraction = await extract_discovery_candidates(discovery)
    return {"mode": "read_only", "feed_origin": "reconstructed RSS; not authentic archived feeds",
        "source_registry_origin": "current verified sources enabled under a reconstructed September 9 registry; historical source availability unverified",
        "simulated_at": REPLAY_AT.isoformat(), "production_writes": False,
        "source_timing": source_timing(),
        "requests": requests, "probes": [asdict(item) for item in discovery.probes],
        "notices": [asdict(item) for item in discovery.notices],
        "candidates": [{"url": item.article_url, "error": item.error,
                        "extraction": item.extraction.model_dump(mode="json") if item.extraction else None}
                       for item in extraction]}


async def persist(capture_dir: Path) -> dict:
    from app.core.config import settings
    require_local_test_database(settings.DATABASE_URL)  # Before sessions or writes.
    from app.core.database import SessionLocal
    require_local_test_database(str(SessionLocal.kw["bind"].url))
    from app.crud import news
    from app.models import FloodAvoidanceZone, FloodReport
    from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun, NewsArticleFeedEntry
    from app.services.news_discovery_service import discover_news
    from app.services.news_processing_service import process_saved_news
    from app.services.news_results_service import browse_news_results, read_news_result
    from app.services.news_collection_service import browse_news_collection
    from sqlalchemy import func, select

    urls = [spec.url for spec in ARTICLES]
    original_save = news.save_candidate
    def historical_save(db, entry, candidate):
        # Keep actual parser source IDs during retrieval; mark saved provenance
        # visibly as local test without touching global publisher registration.
        label = f"{entry.publisher} ({TEST_LABEL})"
        return original_save(db, replace(entry, source_id=label),
                             replace(candidate, source_id=label) if candidate is not None else None)

    def counts(db) -> dict:
        ids = select(NewsArticle.id).where(NewsArticle.canonical_url.in_(urls))
        versions = select(NewsArticleVersion.id).where(NewsArticleVersion.article_id.in_(ids))
        return {"articles": db.scalar(select(func.count()).select_from(NewsArticle).where(NewsArticle.id.in_(ids))),
                "versions": db.scalar(select(func.count()).select_from(NewsArticleVersion).where(NewsArticleVersion.id.in_(versions))),
                "runs": db.scalar(select(func.count()).select_from(NewsExtractionRun).where(NewsExtractionRun.article_version_id.in_(versions))),
                "feed_entries": db.scalar(select(func.count()).select_from(NewsArticleFeedEntry).where(NewsArticleFeedEntry.article_id.in_(ids))),
                "zones": db.scalar(select(func.count()).select_from(FloodAvoidanceZone)),
                "reports": db.scalar(select(func.count()).select_from(FloodReport))}

    with SessionLocal() as db:
        before = counts(db)
    cycles = []
    for _ in range(2):
        requests: list[str] = []
        with replay_clock(), patch.object(news, "save_candidate", historical_save), fixture_client(capture_dir, requests) as client:
            with SessionLocal() as db:
                discovery = discover_news(replay_sources(), client, db)
                ids = list(db.scalars(select(NewsArticle.id).where(NewsArticle.canonical_url.in_(urls))))
            if len(ids) != len(ARTICLES):
                raise RuntimeError("Discovery did not collect all three historical reports")
            processed = [asdict(await process_saved_news(SessionLocal, article_id=id_, clock=lambda: REPLAY_AT)) for id_ in ids]
        if any(result[key] for result in processed for key in ("failed", "retry_wait", "lease_lost")):
            raise RuntimeError("Replay durable processing failed")
        with SessionLocal() as db:
            cycle_counts = counts(db)
        cycles.append({"candidates": len(discovery.candidates), "probes": [asdict(probe) for probe in discovery.probes],
                       "notices": [asdict(notice) for notice in discovery.notices], "processing": processed,
                       "requests": requests, "counts": cycle_counts})
    if cycles[0]["counts"] != cycles[1]["counts"]:
        raise RuntimeError("Repeat collection created duplicate evidence or changed public flood state")
    if any(before[key] != cycles[-1]["counts"][key] for key in ("zones", "reports")):
        raise RuntimeError("Replay changed flood reports or avoidance zones")
    with SessionLocal() as db:
        all_items = []
        page_number = 1
        while True:
            page = browse_news_results(db, page=page_number, page_size=100, search="", publisher=None,
                condition=None, placement=None, order="publication_newest")
            all_items.extend(item for item in page.items if item.article_id in ids)
            if page_number >= page.pages:
                break
            page_number += 1
        result_details = [read_news_result(db, item.run_id, item.claim_index) for item in all_items]
        details = [detail.model_dump(mode="json") for detail in result_details]
        if any(detail.claim.action_type == "auto_approved" or detail.claim.road_placement.may_affect_routing for detail in result_details):
            raise RuntimeError("Historical evidence qualified for automatic routing")
        collection = browse_news_collection(db, page=1, page_size=100, search="September 9", publisher=None, status="all")
    return {"mode": "dedicated_local_database", "database": "lanes_news_test",
        "feed_origin": "reconstructed RSS; not authentic archived feeds", "simulated_at": REPLAY_AT.isoformat(),
        "source_registry_origin": "current verified sources enabled under a reconstructed September 9 registry; historical source availability unverified",
        "source_timing": source_timing(),
        "production_writes": False, "zones_and_reports_unchanged": True, "before": before,
        "repeat_idempotent": True, "cycles": cycles, "readable_locations": len(details),
        "details": details, "collection": collection.model_dump(mode="json")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="Fetch original public HTML and body into ignored files")
    parser.add_argument("--persist", action="store_true", help="Write only to the dedicated local historical test database")
    parser.add_argument("--capture-dir", type=Path, default=CAPTURE_DIR)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.persist:
        from app.core.config import settings
        require_local_test_database(settings.DATABASE_URL)
    if args.capture:
        capture_articles(args.capture_dir)
    result = asyncio.run(persist(args.capture_dir) if args.persist else preview(args.capture_dir))
    rendered = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key not in {"details", "candidates", "collection"}},
                     ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
