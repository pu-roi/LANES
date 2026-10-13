"""Backend-owned immutable bundles and side-effect-free evidence previews."""
import hashlib
import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.mcp_review_config import MCP_REVIEW_REVISION
from app.crud.mcp_review import saved_run, saved_runs
from app.schemas.mcp_review import MCPAuditProposal
from app.schemas.news_audit import CompactBatchSelection
from app.schemas.news_audit_batch import AuditCandidate
from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput
from app.services.news_claim_auditor import (
    AuditorConfig, NewsClaimAuditor, MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES,
    SYSTEM_INSTRUCTIONS, RESPONSE_VERSION, PROMPT_VERSION,
    canonical_claim_sha256, canonical_input_sha256,
    _provider_evidence, _validate_evidence, _classify,
)


class MCPReviewError(ValueError):
    def __init__(self, code: str, status: int = 422) -> None:
        self.code = code
        self.status = status
        super().__init__(code)


def _encoded(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False).encode("utf-8")


def list_news(db: Session, page: int, page_size: int) -> dict[str, Any]:
    rows, total = saved_runs(db, page, page_size)
    names = ("run_id", "pipeline_version", "completed_at", "article_version_id",
             "article_id", "input_sha256", "title", "publisher", "published_at", "claim_count")
    return {"items": [dict(zip(names, row)) for row in rows], "page": page,
            "page_size": page_size, "total": total, "collection": "completed_extraction_runs"}


def _load(db: Session, run_id: int, indexes: tuple[int, ...]):
    if (not 1 <= len(indexes) <= 8 or any(type(i) is not int or i < 0 for i in indexes)
            or len(set(indexes)) != len(indexes)):
        raise MCPReviewError("mcp_claim_indexes_invalid")
    record = saved_run(db, run_id)
    if record is None:
        raise MCPReviewError("mcp_saved_run_not_found", 404)
    run, version = record
    if not isinstance(run.result, dict) or not isinstance(run.result.get("claims"), list):
        raise MCPReviewError("mcp_saved_run_invalid")
    if max(indexes) >= len(run.result["claims"]):
        raise MCPReviewError("mcp_claim_not_found", 404)
    source = NewsArticleExtractorInput.model_validate(version.input_snapshot)
    if canonical_input_sha256(source) != version.input_fingerprint:
        raise MCPReviewError("mcp_source_identity_mismatch", 409)
    candidates = tuple(AuditCandidate(candidate_id=f"run_{run_id}_claim_{i}",
        claim=ExtractedClaim.model_validate(run.result["claims"][i])) for i in indexes)
    return run, version, source, candidates


def _bundle(db: Session, run_id: int, indexes: tuple[int, ...]):
    run, version, source, candidates = _load(db, run_id, indexes)
    auditor = NewsClaimAuditor(AuditorConfig())  # No credentials/configuration or dispatch.
    try:
        document = json.loads(auditor.batch_document(candidates, source))
    except ValueError as exc:
        raise MCPReviewError(str(exc)) from exc
    identity = {"run_id": run_id, "claim_indexes": list(indexes),
        "article_version_id": version.id, "input_sha256": version.input_fingerprint,
        "pipeline_version": run.pipeline_version, "validation_revision": MCP_REVIEW_REVISION,
        "prompt_version": PROMPT_VERSION, "response_version": RESPONSE_VERSION,
        "selection_schema_sha256": hashlib.sha256(_encoded(CompactBatchSelection.model_json_schema())).hexdigest(),
        "claim_sha256": [canonical_claim_sha256(c.claim) for c in candidates]}
    bundle = {"reference": {"run_id": run_id, "claim_indexes": list(indexes),
        "bundle_sha256": hashlib.sha256(_encoded(identity)).hexdigest()}, "identity": identity,
        "instructions": SYSTEM_INSTRUCTIONS, "document": document,
        "original_claims": [c.claim.model_dump(mode="json") for c in candidates],
        "selection_schema": CompactBatchSelection.model_json_schema(),
        "evidence_complete": True, "preview_only": True,
        "publication_permitted": False, "may_affect_routing": False}
    if len(_encoded(bundle)) > MAX_REQUEST_BYTES:
        raise MCPReviewError("mcp_bundle_oversized", 413)
    return bundle, candidates, source, auditor


def get_bundle(db: Session, run_id: int, indexes: tuple[int, ...]) -> dict[str, Any]:
    return _bundle(db, run_id, indexes)[0]


def get_claim(db: Session, run_id: int, claim_index: int) -> dict[str, Any]:
    return get_bundle(db, run_id, (claim_index,))


def preview(db: Session, proposal: MCPAuditProposal) -> dict[str, Any]:
    if len(proposal.model_dump_json().encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise MCPReviewError("mcp_proposal_oversized", 413)
    ref = proposal.bundle
    bundle, candidates, source, auditor = _bundle(db, ref.run_id, ref.claim_indexes)
    if ref.bundle_sha256 != bundle["reference"]["bundle_sha256"]:
        raise MCPReviewError("mcp_bundle_identity_mismatch", 409)
    wanted = {c.candidate_id: c for c in candidates}
    ids = [row.candidate_id for row in proposal.results]
    if len(set(ids)) != len(ids) or set(ids) != set(wanted):
        raise MCPReviewError("mcp_result_identity_invalid")
    options = auditor._batch_options(candidates, (source.article_text or "").strip())
    results = []
    for selection in proposal.results:
        candidate = wanted[selection.candidate_id]
        selected = selection.model_dump(mode="json", exclude={"candidate_id"})
        selected["claim_sha256"] = canonical_claim_sha256(candidate.claim)
        try:
            audit = _provider_evidence(json.dumps(selected, ensure_ascii=False), options)
            reason = _validate_evidence(audit, candidate.claim, source, selected["claim_sha256"])
            outcome, reason = ("invalid", reason) if reason else _classify(audit, candidate.claim)
        except (ValueError, KeyError, IndexError, TypeError):
            audit, outcome, reason = None, "invalid", "auditor_response_invalid"
        results.append({"candidate_id": selection.candidate_id, "outcome": outcome,
            "reason_code": reason, "evidence": audit.model_dump(mode="json")
                if audit is not None and outcome != "invalid" else None})
    return {"bundle": bundle["reference"], "validation_revision": MCP_REVIEW_REVISION,
        "results": results, "preview_only": True, "publication_permitted": False,
        "may_affect_routing": False, "provider": "chatgpt_interactive_review", "model": None}
