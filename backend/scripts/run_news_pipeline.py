"""Explicit saved-article processing, independent audit, publication and expiry.

This command writes to the configured database and can incur configured AI
provider fees. It never discovers new publishers or activates ranked geometry.
"""
import argparse
import asyncio
import json
import sys

from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.services.news_pipeline_service import pipeline_has_failures, run_news_pipeline


async def worker(limit: int, cursor: int, interval: int | None, footprint_cursor: int = 0) -> int:
    while True:
        try:
            result = await run_news_pipeline(SessionLocal, limit=limit, seed_cursor=cursor,
                                             footprint_cursor=footprint_cursor, unbound_only=True)
        except SQLAlchemyError:
            print("news_pipeline_storage_unavailable", file=sys.stderr)
            return 1
        except ValueError:
            print("news_pipeline_configuration_invalid", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False), flush=True)
        cursor = result["next_seed_cursor"]
        footprint_cursor = result["next_footprint_cursor"]
        if interval is None:
            return int(pipeline_has_failures(result))
        await asyncio.sleep(interval)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=50, help="Per-stage batch size, 1–200")
    parser.add_argument("--after-run-id", type=int, default=0, help="Seed cursor from a previous batch")
    parser.add_argument("--after-case-id", type=int, default=0, help="Footprint sweep cursor from a previous batch")
    parser.add_argument("--interval", type=int, help="Repeat every 30–3600 seconds; otherwise run once")
    args = parser.parse_args()
    if not 1 <= args.limit <= 200 or args.after_run_id < 0 or args.after_case_id < 0 or (args.interval is not None and not 30 <= args.interval <= 3600):
        parser.error("Invalid batch, cursor or interval")
    try:
        return asyncio.run(worker(args.limit, args.after_run_id, args.interval, args.after_case_id))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
