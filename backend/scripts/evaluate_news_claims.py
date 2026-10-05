"""Explicit bounded evaluator; extraction and public activation remain separate.

From backend/: python -m scripts.evaluate_news_claims --seed --after-run-id 0
Then: python -m scripts.evaluate_news_claims --evaluate --limit 50
Seeding writes unpublished bindings; --evaluate can incur configured AI calls.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
import json
import sys

from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.crud.news_processing import utc_now
from app.services.news_claim_auditor import NewsClaimAuditor
from app.services.news_evaluation_service import evaluate_news_claims, evaluation_policy, seed_claim_evaluations


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit immutable news claims without publishing alerts or zones")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--seed", action="store_true", help="Bind current completed extraction runs; no AI calls")
    modes.add_argument("--evaluate", action="store_true", help="Audit due work through the explicitly configured provider")
    parser.add_argument("--limit", type=int, default=50, help="Bounded batch size, 1-200")
    parser.add_argument("--run-id", type=int, help="Restrict work to one completed extraction run")
    parser.add_argument("--after-run-id", type=int, default=0, help="Seed cursor; reuse next_after_run_id in the next batch")
    args = parser.parse_args()
    if not 1 <= args.limit <= 200 or args.after_run_id < 0 or (args.run_id is not None and args.run_id <= 0):
        parser.error("Invalid batch limit or run ID")
    if args.after_run_id and (not args.seed or args.run_id is not None):
        parser.error("--after-run-id requires --seed without --run-id")
    try:
        auditor = NewsClaimAuditor()
        policy = evaluation_policy(auditor)
        summary = (seed_claim_evaluations(SessionLocal, policy, now=utc_now(), limit=args.limit,
                                         run_id=args.run_id, after_run_id=args.after_run_id) if args.seed else
                   asyncio.run(evaluate_news_claims(SessionLocal, limit=args.limit, run_id=args.run_id,
                                                    auditor=auditor, policy=policy)))
    except SQLAlchemyError:
        print("news_evaluation_storage_unavailable", file=sys.stderr)
        return 1
    except ValueError:
        print("news_evaluation_configuration_invalid", file=sys.stderr)
        return 1
    print(json.dumps({"mode": "seed" if args.seed else "evaluate", "public_writes": False,
                      "policy_fingerprint": policy.fingerprint, **asdict(summary)}, indent=2))
    return int(bool(summary.failed or summary.retry_wait or summary.lease_lost or summary.skipped))


if __name__ == "__main__":
    raise SystemExit(main())
