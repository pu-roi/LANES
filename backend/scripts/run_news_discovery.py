"""Probe candidate feeds or run verified-source discovery once.

Examples (from backend/):
    python -m scripts.run_news_discovery --probe --source feedspot-01
    python -m scripts.run_news_discovery --probe --all-leads
    python -m scripts.run_news_discovery --discover
"""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import json
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import httpx
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.services.news_discovery_service import discover_news, extract_discovery_candidates, extract_saved_news_articles
from app.crud.news import list_pending_articles
from app.services.news_feed_service import canonical_article_url, probe_feed
from app.services.news_open_search_service import append_publisher_feed_leads, assess_alternate_article_leads, retrieve_open_article_leads, search_open_article_leads
from app.services.news_sources import DEFAULT_SOURCE_FILE, NewsSource, load_news_sources
from app.services.news_pipeline_service import pipeline_has_failures, run_news_pipeline


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
    mode.add_argument("--open-leads", action="store_true", help="Read-only index/feed fallback diagnostic")
    mode.add_argument("--extract-saved", action="store_true", help="Preview rules extraction of saved pending articles; requires --dry-run")
    mode.add_argument("--process-saved", action="store_true", help="Persist rules extraction of captured pending inputs and due retries")
    parser.add_argument("--scheduled", action="store_true", help="Apply database cadence, switches and worker overlap protection; requires --discover --pipeline")
    parser.add_argument("--process", action="store_true", help="Process saved/due work after --discover, including unchanged feeds")
    parser.add_argument("--pipeline", action="store_true", help="Run saved extraction, independent audit, publication, expiry and verified footprints; may incur configured AI fees")
    parser.add_argument("--limit", type=int, help="Saved preview/processing batch size, 1-200 (default 50)")
    parser.add_argument("--source", action="append", default=[], help="Source ID; repeat for multiple sources")
    parser.add_argument("--all-leads", action="store_true", help="Probe every configured feed lead")
    parser.add_argument("--sources-file", type=Path, default=DEFAULT_SOURCE_FILE)
    parser.add_argument("--output", type=Path, help="Optional JSON result file")
    parser.add_argument("--ignore-proxy", action="store_true", help="Ignore broken local proxy environment settings")
    parser.add_argument("--dry-run", action="store_true", help="Preview discovery or saved extraction without database writes")
    parser.add_argument("--extract", action="store_true", help="Read-only rules extraction; requires --discover --dry-run")
    parser.add_argument("--article-url", help="Original approved publisher article URL for --open-leads")
    parser.add_argument("--title", help="Original article title for --open-leads")
    parser.add_argument("--excerpt", default="", help="Original RSS excerpt for --open-leads")
    parser.add_argument("--published-at", type=datetime.fromisoformat, help="Original publication ISO timestamp for --open-leads")
    parser.add_argument("--retrieve-articles", action="store_true", help="Retrieve approved alternates for --open-leads")
    parser.add_argument("--trace-network", action="store_true", help="Summarize TCP/TLS events without headers or credentials")
    args = parser.parse_args()
    if args.all_leads and not args.probe:
        parser.error("--all-leads is only valid with --probe")
    if args.dry_run and not (args.discover or args.extract_saved):
        parser.error("--dry-run is only valid with --discover or --extract-saved")
    if args.extract_saved and not args.dry_run:
        parser.error("--extract-saved requires --dry-run; durable processing is not enabled")
    if args.process and (not args.discover or args.dry_run):
        parser.error("--process requires --discover without --dry-run")
    if args.pipeline and (args.dry_run or not (args.discover or args.process_saved) or args.process):
        parser.error("--pipeline requires --discover or --process-saved without --dry-run/--process")
    if args.limit is not None and (not (args.extract_saved or args.process_saved or args.process or args.pipeline) or not 1 <= args.limit <= 200):
        parser.error("--limit requires saved preview/processing and must be between 1 and 200")
    if args.process_saved and args.source:
        parser.error("Saved processing does not accept feed selection options")
    if args.extract_saved and (args.source or args.all_leads):
        parser.error("Saved preview does not accept feed selection options")
    if args.extract and not (args.discover and args.dry_run):
        parser.error("--extract requires --discover --dry-run; production ingestion is not enabled")
    if args.probe and not args.all_leads and not args.source:
        parser.error("--probe requires --source or --all-leads")
    if args.open_leads and (not args.article_url or not args.title):
        parser.error("--open-leads requires --article-url and --title")
    if not args.open_leads and (args.article_url or args.title or args.excerpt or args.published_at or args.retrieve_articles or args.trace_network):
        parser.error("Article lookup and trace options require --open-leads")

    if args.scheduled:
        if not args.discover or not args.pipeline or args.dry_run or args.source:
            parser.error("--scheduled requires --discover --pipeline without --dry-run/--source")
        from app.services.news_scheduler_service import run_scheduled_news_tick
        try:
            result = asyncio.run(run_scheduled_news_tick(SessionLocal, limit=args.limit or 50, sources=load_news_sources(args.sources_file)))
        except Exception:
            print("scheduled_news_worker_failed", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False, default=str))
        return int(result.get("outcome") == "requires_attention")

    if args.process_saved:
        if args.pipeline:
            try:
                result = asyncio.run(run_news_pipeline(SessionLocal, limit=args.limit or 50,
                    unbound_only=True, sources=load_news_sources(args.sources_file)))
            except (SQLAlchemyError, ValueError) as exc:
                print("news_pipeline_storage_unavailable" if isinstance(exc, SQLAlchemyError)
                      else "news_pipeline_configuration_invalid", file=sys.stderr)
                return 1
            output = json.dumps({"mode":"process-saved-pipeline", **result},ensure_ascii=False,indent=2)
            if args.output: args.output.write_text(output + "\n",encoding="utf-8")
            else: print(output)
            return int(pipeline_has_failures(result))
        from app.services.news_processing_service import process_saved_news
        try:
            processed = asyncio.run(process_saved_news(SessionLocal, limit=args.limit or 50))
        except SQLAlchemyError as exc:
            print(f"News processing storage unavailable: {exc.__class__.__name__}", file=sys.stderr)
            return 1
        payload = {"mode": "process-saved", "extraction_mode": "rules_only", **asdict(processed)}
        output = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
        return 1 if processed.failed or processed.retry_wait or processed.lease_lost else 0

    if args.extract_saved:
        try:
            with SessionLocal() as db:
                results = asyncio.run(extract_saved_news_articles(list_pending_articles(db, args.limit or 50)))
        except SQLAlchemyError as exc:
            print(f"Saved article storage unavailable: {exc.__class__.__name__}", file=sys.stderr)
            return 1
        payload = {"mode": "extract-saved", "read_only": True, "extraction_mode": "rules_only",
                   "outcome": "no_candidates" if not results else "extraction_errors" if any(item.error for item in results)
                   else "claims_extracted" if any(item.extraction and item.extraction.claims for item in results) else "no_flood_claims",
                   "extractions": [{**asdict(item), "extraction": item.extraction.model_dump(mode="json")
                                    if item.extraction else None} for item in results]}
        output = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
        if args.output:
            args.output.write_text(output + "\n", encoding="utf-8")
            print(f"Wrote {args.output}")
        else:
            print(output)
        return 1 if any(item.error for item in results) else 0

    all_sources = load_news_sources(args.sources_file)
    sources = _selected_sources(all_sources, args.source)
    if args.open_leads and not any(source.enabled and source.verified_at and canonical_article_url(args.article_url, source) for source in all_sources):
        parser.error("--article-url must belong to an enabled, verified publisher")
    timeout = httpx.Timeout(12.0, connect=5.0)
    transport_events: list[dict] = []
    started = time.monotonic()

    def trace(name: str, info: dict) -> None:
        if name.endswith(("connect_tcp.started", "connect_tcp.complete", "start_tls.started", "start_tls.complete", "receive_response_headers.complete", "failed")):
            event = {"event": name, "elapsed_seconds": round(time.monotonic() - started, 2)}
            if name.endswith("failed"):
                event["error_type"] = type(info.get("exception")).__name__
            transport_events.append(event)

    def attach_trace(request: httpx.Request) -> None:
        request.extensions["trace"] = trace

    def trace_response(response: httpx.Response) -> None:
        transport_events.append({"event": "http.response", "host": response.url.host,
                                 "status": response.status_code,
                                 "elapsed_seconds": round(time.monotonic() - started, 2)})

    hooks = {"request": [attach_trace], "response": [trace_response]} if args.trace_network else None
    with httpx.Client(timeout=timeout, trust_env=not args.ignore_proxy, event_hooks=hooks) as client:
        if args.open_leads:
            result = search_open_article_leads(args.article_url, args.title, args.excerpt, client,
                                             published_at=args.published_at, include_event_context=args.retrieve_articles)
            if args.retrieve_articles:
                result = append_publisher_feed_leads(result, args.title, args.excerpt, args.published_at, sources, client)
                result = retrieve_open_article_leads(result, sources, client)
                result = assess_alternate_article_leads(result, args.title, args.excerpt, args.published_at)
            summary = asdict(result)
            for hit in summary["results"]:
                hit["article_text_chars"] = len(hit["article_text"] or "")
                del hit["article_text"]
            available = any(hit.article_text for hit in result.results)
            outcome = "article_available_for_review" if available else "no_alternate_body" if args.retrieve_articles else "index_links_only" if result.results else "no_leads"
            payload = {"mode": "open-leads", "read_only": True, "outcome": outcome, "lookup": summary}
            if args.trace_network:
                payload["transport_events"] = transport_events
            success = available if args.retrieve_articles else bool(result.results)
        elif args.probe:
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
                       "notices": [asdict(item) for item in run.notices],
                       "candidates": candidate_summaries}
            success = any(probe.status in {"parsed", "empty", "unchanged"} for probe in run.probes)
            if args.extract:
                extracted = asyncio.run(extract_discovery_candidates(run))
                payload["read_only"] = True
                payload["extraction_mode"] = "rules_only"
                payload["extractions"] = [
                    {"article_url": item.article_url, "error": item.error,
                     "metadata_only": item.extraction.is_metadata_only if item.extraction else None,
                     "claim_count": len(item.extraction.claims) if item.extraction else 0,
                     "actions": dict(Counter(claim.action_type for claim in item.extraction.claims)) if item.extraction else {},
                     "claims": [
                         {"place": claim.raw_place_name, "city": claim.canonical_city,
                          "barangay": claim.canonical_barangay,
                          "depth": claim.depth_canonical, "condition": claim.condition,
                          "observation_time": claim.event_time_resolved,
                          "action": claim.action_type, "rationale": claim.action_rationale,
                          "geometry_provenance": claim.ranked_location.geometry_provenance if claim.ranked_location else None,
                          "road_placement": claim.road_placement.model_dump(mode="json") if claim.road_placement else None}
                         for claim in item.extraction.claims
                     ] if item.extraction else []}
                    for item in extracted
                ]
                payload["outcome"] = ("no_candidates" if not extracted else "extraction_errors"
                                      if any(item.error for item in extracted) else "claims_extracted"
                                      if any(item.extraction and item.extraction.claims for item in extracted)
                                      else "no_flood_claims")
                success = success and not any(item.error for item in extracted)

    if args.process:
        from app.services.news_processing_service import process_saved_news
        try:
            processed = asyncio.run(process_saved_news(SessionLocal, limit=args.limit or 50))
        except SQLAlchemyError as exc:
            print(f"News processing storage unavailable: {exc.__class__.__name__}", file=sys.stderr)
            return 1
        payload["processing"] = asdict(processed)
        success = success and not (processed.failed or processed.retry_wait or processed.lease_lost)
    if args.pipeline:
        try:
            result = asyncio.run(run_news_pipeline(SessionLocal, limit=args.limit or 50,
                unbound_only=True, sources=all_sources))
        except (SQLAlchemyError, ValueError) as exc:
            print("news_pipeline_storage_unavailable" if isinstance(exc, SQLAlchemyError)
                  else "news_pipeline_configuration_invalid", file=sys.stderr)
            return 1
        payload["pipeline"] = result
        success = success and not pipeline_has_failures(result)
    output = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(output)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
