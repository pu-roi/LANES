"""Only saved evidence reads and validation previews are exposed to MCP."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.mcp_review_deps import get_mcp_reader, review_db
from app.core.mcp_review_config import MCP_REVIEW_REVISION
from app.models.user import User
from app.schemas.mcp_review import MCPAuditProposal
from app.services import mcp_review_service as service
from app.services.news_claim_auditor import MAX_RESPONSE_BYTES

router = APIRouter()


def invoke(function, *args):
    try:
        return jsonable_encoder(function(*args))
    except service.MCPReviewError as exc:
        raise HTTPException(exc.status, exc.code) from None
    except ValidationError:
        raise HTTPException(422, "mcp_saved_evidence_invalid") from None


@router.get("/connection")
def connection(actor: User = Depends(get_mcp_reader)) -> dict:
    return {"account_id": actor.id, "capabilities": ["saved_news_read", "audit_preview"],
            "revision": MCP_REVIEW_REVISION, "preview_only": True,
            "publication_permitted": False, "may_affect_routing": False}


@router.get("/saved-news")
def list_saved_news(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50),
        actor: User = Depends(get_mcp_reader), db: Session = Depends(review_db)) -> dict:
    return invoke(service.list_news, db, page, page_size)


@router.get("/claim")
def get_claim_evidence(run_id: int = Query(..., ge=1), claim_index: int = Query(..., ge=0),
        actor: User = Depends(get_mcp_reader), db: Session = Depends(review_db)) -> dict:
    return invoke(service.get_claim, db, run_id, claim_index)


@router.get("/bundle")
def get_audit_bundle(run_id: int = Query(..., ge=1),
        claim_indexes: list[int] = Query(..., min_length=1, max_length=8),
        actor: User = Depends(get_mcp_reader), db: Session = Depends(review_db)) -> dict:
    return invoke(service.get_bundle, db, run_id, tuple(claim_indexes))


@router.post("/preview")
async def preview_audit_proposal(request: Request, actor: User = Depends(get_mcp_reader),
        db: Session = Depends(review_db)) -> dict:
    body = await request.body()
    if len(body) > MAX_RESPONSE_BYTES:
        raise HTTPException(413, "mcp_proposal_oversized")
    try:
        # JSON validation keeps strict integer/boolean types and accepts JSON arrays
        # for the existing immutable tuple schemas without Python coercion.
        from app.services.news_claim_auditor import _unique_json_object
        import json
        json.loads(body, object_pairs_hook=_unique_json_object)
        proposal = MCPAuditProposal.model_validate_json(body)
    except (ValueError, TypeError):
        raise HTTPException(422, "mcp_proposal_invalid") from None
    return invoke(service.preview, db, proposal)
