"""Opt-in, read-only qualification with a persistent shared twelve-POST ceiling.

Fixtures contain frozen article/claim snapshots, their hashes and expected outcomes.
No discovery, database imports, publication, credential logging or automatic retries.
An existing stopped ledger cannot be resumed by rerunning this command.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import replace
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import httpx

from app.schemas.news_audit_batch import AuditCandidate
from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_claim_auditor import (
    AuditorConfig, NewsClaimAuditor, canonical_claim_sha256, canonical_input_sha256,
)
from app.services.news_gemini_schema import GEMINI_SCHEMA_PROFILES, GEMINI_SCHEMA_REVISION

MODELS = ("gemini-3.8-flash", "gemini-3.5-flash-lite")
MAX_POSTS = 12


class BudgetExhausted(httpx.TransportError):
    pass


class QualificationBudget:
    """Reserve before dispatch; interrupted attempts still consume the budget."""
    def __init__(self, path: Path, identity: str) -> None:
        self.path, self.identity = path, identity
        self.lock = path.with_suffix(".lock")
        self.state: dict[str, Any] = {}

    def __enter__(self) -> QualificationBudget:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fd = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            self.state = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {
                "identity": self.identity, "max_posts": MAX_POSTS, "attempts": [], "status": "running"}
            if self.state["identity"] != self.identity or self.state["max_posts"] != MAX_POSTS:
                raise ValueError("qualification_ledger_identity_mismatch")
            if self.state["status"] != "running":
                raise ValueError("qualification_ledger_already_stopped")
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *args: Any) -> None:
        os.close(self.fd)
        self.lock.unlink()

    def save(self) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def reserve(self, context: dict[str, Any]) -> int:
        if self.state["status"] != "running" or len(self.state["attempts"]) >= MAX_POSTS:
            raise BudgetExhausted("qualification_budget_exhausted")
        self.state["attempts"].append(dict(context, dispatched_at=datetime.now(timezone.utc).isoformat()))
        self.save()
        return len(self.state["attempts"]) - 1

    def stop(self, status: str, **details: Any) -> None:
        self.state.update(status=status, **details)
        self.save()


class BudgetTransport(httpx.AsyncBaseTransport):
    def __init__(self, budget: QualificationBudget, context: dict[str, Any], delegate: httpx.AsyncBaseTransport) -> None:
        self.budget, self.context, self.delegate = budget, context, delegate
        self.attempt: int | None = None

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if request.method != "POST" or request.url.host != "generativelanguage.googleapis.com":
            raise ValueError("qualification_request_not_allowed")
        self.attempt = self.budget.reserve(self.context)
        return await self.delegate.handle_async_request(request)

    async def aclose(self) -> None:
        await self.delegate.aclose()


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    for case in cases:
        article = NewsArticleExtractorInput.model_validate(case["article"])
        candidates = tuple(AuditCandidate.model_validate_json(json.dumps(c)) for c in case["candidates"])
        if canonical_input_sha256(article) != case["input_sha256"]:
            raise ValueError("qualification_article_hash_mismatch")
        if [canonical_claim_sha256(c.claim) for c in candidates] != case["claim_sha256"]:
            raise ValueError("qualification_claim_hash_mismatch")
        if set(case["expected"]) != {c.candidate_id for c in candidates}:
            raise ValueError("qualification_expected_ids_mismatch")
        NewsClaimAuditor(AuditorConfig()).batch_document(candidates, article)
        case.update(article=article, candidates=candidates)
    if not cases or not any(len(c["candidates"]) == 8 for c in cases):
        raise ValueError("qualification_eight_claim_case_missing")
    return cases


async def qualify(config: AuditorConfig, cases: list[dict[str, Any]], budget: QualificationBudget) -> None:
    if config.provider != "gemini" or config.error_code():
        raise ValueError("qualification_gemini_configuration_required")
    model_index = 0
    for profile in GEMINI_SCHEMA_PROFILES:
        while model_index < len(MODELS):
            auditor = NewsClaimAuditor(replace(config, model=MODELS[model_index], gemini_schema_profile=profile))
            unavailable = False
            for case in cases:
                context = {"model": auditor.config.model, "profile": profile, "adapter_revision": GEMINI_SCHEMA_REVISION,
                           "case": case["name"], "input_sha256": case["input_sha256"], "claim_sha256": case["claim_sha256"]}
                transport = BudgetTransport(budget, context, httpx.AsyncHTTPTransport(retries=0))
                async with httpx.AsyncClient(transport=transport, follow_redirects=False) as client:
                    results = await auditor.audit_batch(case["candidates"], case["article"], client=client)
                if transport.attempt is None:
                    budget.stop("blocked", reason="budget_exhausted_or_not_dispatched")
                    return
                entry = budget.state["attempts"][transport.attempt]
                entry["results"] = {key: value.model_dump(mode="json") for key, value in results.items()}
                passed = all(r.outcome == case["expected"][key] and r.evidence is not None for key, r in results.items())
                entry["passed"] = passed
                budget.save()
                print(json.dumps(dict(context, attempt=transport.attempt + 1, passed=passed,
                    outcomes={key: {"outcome": r.outcome, "reason": r.reason_code,
                        "http_status": r.provider_http_status} for key, r in results.items()})), flush=True)
                statuses = {r.provider_http_status for r in results.values()}
                if statuses & {401, 402, 403, 429}:
                    delay = max([r.retry_after_seconds or 0 for r in results.values()] + [3600 if 429 not in statuses else 900])
                    budget.stop("blocked", reason="account_error", blocked_until=(datetime.now(timezone.utc) + timedelta(seconds=delay)).isoformat())
                    return
                if statuses & {404, 503} or any(r.transport and r.transport.error_category == "model_unavailable" for r in results.values()):
                    unavailable = True
                    break
                if not passed:
                    # A request error never repeats this profile. Semantic failure
                    # cannot be fixed by loosening provider-side constraints.
                    if 400 not in statuses:
                        budget.stop("blocked", reason="qualification_evidence_failed")
                        return
                    break
            else:
                budget.stop("qualified", model=auditor.config.model, profile=profile)
                return
            if unavailable:
                model_index += 1
                continue
            break
    budget.stop("blocked", reason="no_qualified_profile_or_model")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()
    config = AuditorConfig.from_environment()
    fixture_digest = hashlib.sha256(args.fixtures.read_bytes()).hexdigest()
    identity = hashlib.sha256((fixture_digest + "\0" + config.gemini_api_key + "\0" + GEMINI_SCHEMA_REVISION).encode()).hexdigest()
    cases = load_cases(args.fixtures)
    with QualificationBudget(args.ledger, identity) as budget:
        asyncio.run(qualify(config, cases, budget))
        print(json.dumps({"status": budget.state["status"], "posts": len(budget.state["attempts"]), "limit": MAX_POSTS}))
        if budget.state["status"] != "qualified":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
