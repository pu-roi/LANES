"""Explicit five-request, no-retry original-evidence qualification; never writes to a DB."""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any

import httpx

from app.services.chatgpt_plan_auth import CredentialStore
from app.services.chatgpt_plan_qualification import (
    REVISION, TRANSPORT_REVISION, QualificationError, audit_response, request_body, validate_selection,
)
from app.services.news_claim_auditor import AuditorConfig, NewsClaimAuditor
from scripts.qualify_news_gemini import load_cases

MAX_POSTS = 5


class Budget:
    def __init__(self, path: Path, identity: str, model: str) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.acquire()
        # Never restart a previous experiment, including one interrupted after reserve.
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
        except BaseException:
            self.close()
            raise
        self.state: dict[str, Any] = {"identity": identity, "model": model, "max_posts": MAX_POSTS,
            "status": "running", "revision": REVISION, "attempts": [],
            "preview_only": True, "publication_permitted": False, "may_affect_routing": False}
        self.save()

    def acquire(self) -> None:
        self.lock = self.path.with_suffix(".lock")
        descriptor = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
        self.owns_lock = True

    def close(self) -> None:
        if getattr(self, "owns_lock", False):
            self.lock.unlink()
            self.owns_lock = False

    def save(self) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.path)

    def reserve(self, case: dict[str, Any]) -> dict[str, Any]:
        if self.state["status"] != "running" or len(self.state["attempts"]) >= MAX_POSTS:
            raise QualificationError("budget_exhausted")
        entry = {"case": case["name"], "input_sha256": case["input_sha256"],
            "claim_sha256": case["claim_sha256"], "dispatched_at": datetime.now(timezone.utc).isoformat(),
            "transport_revision": TRANSPORT_REVISION}
        self.state["attempts"].append(entry)
        self.save()
        return entry

    @classmethod
    def resume_transport_repair(cls, path: Path, identity: str, model: str) -> Budget:
        budget = cls.__new__(cls)
        budget.path = path
        budget.acquire()
        try:
            budget.state = json.loads(path.read_text(encoding="utf-8"))
        except BaseException:
            budget.close()
            raise
        if (budget.state["identity"] != identity or budget.state["model"] != model
                or budget.state["max_posts"] != MAX_POSTS or budget.state["status"] != "blocked"
                or budget.state["reason"] != "response_message_invalid"
                or not 1 <= len(budget.state["attempts"]) < MAX_POSTS
                or any(entry.get("http_status") != 200 or entry.get("error_code") != "response_message_invalid"
                       for entry in budget.state["attempts"])):
            budget.close()
            raise QualificationError("transport_resume_not_permitted")
        budget.state.update(status="running", resumed_for_transport_revision=TRANSPORT_REVISION)
        budget.save()
        return budget


async def qualify(account: dict[str, Any], cases: list[dict[str, Any]], budget: Budget) -> None:
    auditor = NewsClaimAuditor(AuditorConfig())
    async with httpx.AsyncClient(timeout=60, follow_redirects=False, trust_env=False,
                                 transport=httpx.AsyncHTTPTransport(retries=0)) as client:
        for case in cases:
            if account["expires_at"] <= time.time() + 60:
                budget.state.update(status="blocked", reason="credential_expiry_needs_reauthorization")
                budget.save()
                return
            payload = request_body(auditor.batch_document(case["candidates"], case["article"]), budget.state["model"])
            entry = budget.reserve(case)
            try:
                trace_path = budget.path.parent / f"chatgpt-stream-{len(budget.state['attempts'])}.sse"
                entry["stream_artifact"] = trace_path.name
                budget.save()
                with trace_path.open("xb") as trace:
                    text, metadata = await audit_response(client, account["access_token"], payload, capture=trace.write)
                entry["transport"] = metadata
                entry["selection"] = json.loads(text)
                results = validate_selection(text, case)
                entry["results"] = results
                passed = all(result["outcome"] == case["expected"][result["candidate_id"]]
                             and result["evidence"] is not None for result in results)
                entry["passed"] = passed
                print(json.dumps({"attempt": len(budget.state["attempts"]), "case": case["name"],
                    "passed": passed, "outcomes": [{"candidate_id": r["candidate_id"], "outcome": r["outcome"],
                                                     "reason": r["reason_code"]} for r in results]}), flush=True)
                if not passed:
                    budget.state.update(status="blocked", reason="evidence_qualification_failed")
                    budget.save()
                    return
                budget.save()
            except QualificationError as error:
                entry.update(passed=False, error_code=error.code, http_status=error.http_status,
                    request_id=error.request_id, error_param=error.error_param)
                if error.provider_response is not None:
                    entry["provider_response"] = error.provider_response
                budget.state.update(status="blocked", reason=error.code)
                budget.save()
                print(json.dumps({"attempt": len(budget.state["attempts"]), "case": case["name"],
                    "passed": False, "http_status": error.http_status, "error_code": error.code,
                    "error_param": error.error_param, "request_id": error.request_id}), flush=True)
                return
            except (ValueError, KeyError, IndexError, TypeError):
                entry.update(passed=False, error_code="selection_validation_failed")
                budget.state.update(status="blocked", reason="selection_validation_failed")
                budget.save()
                return
    all_passed = all(entry.get("passed") is True for entry in budget.state["attempts"])
    budget.state.update(status="qualified" if all_passed else "partial",
                        reason=None if all_passed else "earlier_attempt_not_validated")
    budget.save()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--resume-transport-repair", action="store_true")
    args = parser.parse_args()
    account = CredentialStore(Path(os.environ["LOCALAPPDATA"]) / "LANES" / "ChatGPTPlan").load("account.dpapi")
    if not account or not {"chatgpt.tokens.use.direct", "resource.invoke"}.issubset(account["scopes"]):
        parser.error("Verified local ChatGPT plan authorization is required.")
    cases = load_cases(args.fixtures)
    if len(cases) != 5:
        parser.error("Exactly the five frozen qualification cases are required.")
    identity = hashlib.sha256((hashlib.sha256(args.fixtures.read_bytes()).hexdigest() + "\0" +
        account["client_id"] + "\0" + account["subject"] + "\0" + REVISION).encode()).hexdigest()
    if args.resume_transport_repair:
        budget = Budget.resume_transport_repair(args.ledger, identity, args.model)
        # Do not retry the first case or reset its evidence. Use only remaining
        # authorized cases; the morning claim is also present in the eight-case batch.
        cases = cases[len(budget.state["attempts"]):]
    else:
        budget = Budget(args.ledger, identity, args.model)
    try:
        asyncio.run(qualify(account, cases, budget))
    finally:
        budget.close()
    print(json.dumps({"status": budget.state["status"], "posts": len(budget.state["attempts"]), "max_posts": MAX_POSTS}))
    if budget.state["status"] != "qualified":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
