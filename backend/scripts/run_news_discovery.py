"""Probe candidate feeds or run verified-source discovery once.

Examples (from backend/):
    python -m scripts.run_news_discovery --probe --source feedspot-01
    python -m scripts.run_news_discovery --probe --all-leads
    python -m scripts.run_news_discovery --discover
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

import httpx
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.services.news_discovery_service import discover_news
from app.services.news_feed_service import probe_feed
from app.services.news_sources import DEFAULT_SOURCE_FILE, NewsSource, load_news_sources


def _selected_sources(all_sources: tuple[NewsSource, ...], ids: list[str]) -> tuple[NewsSource, ...]:
    known = {source.id: source for source in all_sources}
    unknown = set(ids) - set(known)
    if unknown:
        raise ValueError(f"Unknown source IDs: {', '.join(sorted(unknown))}")
    return tuple(known[id_] for id_ in ids) if ids else all_sources


def main() -> int:
    parser = argparse.ArgumentParser(description="LANES RSS candidate feed probe and discovery")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--probe", action="store_true", help="Check feed leads without article retrieval")
    mode.add_argument("--discover", action="store_true", help="Collect from verified, enabled feeds only")
    parser.add_argument("--source", action="append", default=[], help="Source ID; repeat for multiple sources")
    parser.add_argument("--all-leads", action="store_true", help="Probe every configured feed lead")
    parser.add_argument("--sources-file", type=Path, default=DEFAULT_SOURCE_FILE)
    parser.add_argument("--output", type=Path, help="Optional JSON result file")
    parser.add_argument("--ignore-proxy", action="store_true", help="Ignore broken local proxy environment settings")
    parser.add_argument("--dry-run", action="store_true", help="Discover without database writes or checkpoints")
    args = parser.parse_args()
    if args.all_leads and not args.probe:
        parser.error("--all-leads is only valid with --probe")
    if args.dry_run and not args.discover:
        parser.error("--dry-run is only valid with --discover")
    if args.probe and not args.all_leads and not args.source:
        parser.error("--probe requires --source or --all-leads")

    sources = _selected_sources(load_news_sources(args.sources_file), args.source)
    timeout = httpx.Timeout(12.0, connect=5.0)
    with httpx.Client(timeout=timeout, trust_env=not args.ignore_proxy) as client:
        if args.probe:
            results: list[dict] = []
            for source in sources:
                if not source.feed_urls:
                    results.append({"source_id": source.id, "publisher": source.publisher,
                                    "status": "no_feed_lead"})
                for feed_url in source.feed_urls:
                    probe, _ = probe_feed(source, feed_url, client)
                    results.append(asdict(probe))
                    time.sleep(0.5)
            payload = {"mode": "probe", "sources_checked": len(sources), "results": results}
            success = any(result["status"] == "parsed" and result.get("entry_count", 0) for result in results)
        else:
            active = tuple(source for source in sources if source.enabled)
            if not active:
                print("No verified, enabled RSS sources. Run --probe and complete source review first.", file=sys.stderr)
                return 2
            try:
                if args.dry_run:
                    run = discover_news(active, client)
                else:
                    with SessionLocal() as db:
                        run = discover_news(active, client, db)
            except SQLAlchemyError as exc:
                print(f"RSS discovery storage failed: {exc.__class__.__name__}", file=sys.stderr)
                return 1
            candidate_summaries = []
            for item in run.candidates:
                summary = asdict(item)
                summary["article_text_chars"] = len(item.article_text or "")
                summary["article_text_available"] = item.article_text is not None
                del summary["article_text"]
                candidate_summaries.append(summary)
            payload = {"mode": "discover", "dry_run": args.dry_run,
                       "probes": [asdict(item) for item in run.probes],
                       "candidates": candidate_summaries}
            success = any(probe.status in {"parsed", "unchanged"} for probe in run.probes)

    output = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(output)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
