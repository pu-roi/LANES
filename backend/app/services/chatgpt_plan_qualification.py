"""Bounded Responses transport and strict evidence preview. No DB or worker integration."""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Callable

import httpx

from app.schemas.news_audit import CompactBatchSelection
from app.services.news_claim_auditor import (
    AUDIT_TIMEOUT_SECONDS, MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES, SYSTEM_INSTRUCTIONS,
    AuditorConfig, NewsClaimAuditor, canonical_claim_sha256,
    _classify, _provider_evidence, _unique_json_object, _validate_evidence,
)

REVISION = "chatgpt-plan-qualification-v1"
TRANSPORT_REVISION = "responses-streamed-items-v3"
MAX_STREAM_BYTES = 2_097_152
MAX_EVENT_BYTES = 262_144


class QualificationError(Exception):
    def __init__(self, code: str, *, http_status: int | None = None,
                 request_id: str | None = None, error_param: str | None = None) -> None:
        super().__init__(code)
        self.code, self.http_status, self.request_id, self.error_param = code, http_status, request_id, error_param
        self.provider_response: dict[str, Any] | None = None


def safe_code(value: Any) -> str | None:
    return value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,200}", value) else None


def request_body(document: str, model: str) -> dict[str, Any]:
    payload = {"model": model, "instructions": SYSTEM_INSTRUCTIONS,
        "input": [{"role": "user", "content": document}], "store": False, "stream": True,
        "text": {"format": {"type": "json_schema", "name": "lanes_flood_audit",
            "strict": True, "schema": CompactBatchSelection.model_json_schema()}}}
    if len(json.dumps(payload, ensure_ascii=False).encode()) > MAX_REQUEST_BYTES:
        raise QualificationError("request_oversized")
    return payload


def completed_text(response: dict[str, Any]) -> str:
    if response.get("status") != "completed" or response.get("error"):
        raise QualificationError("response_not_completed")
    output = response.get("output")
    if not isinstance(output, list) or any(not isinstance(item, dict) for item in output):
        raise QualificationError("response_output_invalid")
    messages = []
    for item in output:
        if item.get("type") == "reasoning":
            continue
        if item.get("type") != "message" or item.get("role") != "assistant":
            raise QualificationError("response_output_invalid")
        if item.get("phase") == "commentary":
            continue
        if item.get("phase") not in {None, "final_answer"}:
            raise QualificationError("response_phase_invalid")
        messages.append(item)
    if len(messages) != 1 or messages[0].get("role") != "assistant" or messages[0].get("status") != "completed":
        raise QualificationError("response_message_invalid")
    content = messages[0].get("content")
    if (not isinstance(content, list) or not content or
            any(not isinstance(part, dict) or part.get("type") != "output_text"
                or not isinstance(part.get("text"), str) for part in content)):
        raise QualificationError("response_refused_or_invalid")
    text = "".join(part["text"] for part in content)
    if len(text.encode()) > MAX_RESPONSE_BYTES:
        raise QualificationError("response_oversized")
    return text


async def audit_response(client: httpx.AsyncClient, token: str, payload: dict[str, Any],
                         capture: Callable[[bytes], Any] | None = None) -> tuple[str, dict[str, Any]]:
    """Consume through completion; HTTP 200 and text deltas alone are insufficient."""
    request_id = None
    status = None
    try:
        async with asyncio.timeout(AUDIT_TIMEOUT_SECONDS):
            async with client.stream("POST", "https://api.openai.com/v1/responses",
                    headers={"Authorization": "Bearer " + token}, json=payload) as response:
                status = response.status_code
                request_id = safe_code(response.headers.get("x-request-id"))
                if status != 200:
                    body = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        body.extend(chunk)
                        if len(body) > MAX_RESPONSE_BYTES:
                            raise QualificationError("error_body_oversized")
                    try:
                        data = json.loads(body)
                        error = data.get("error") if isinstance(data, dict) else None
                        error = error if isinstance(error, dict) else {}
                    except ValueError:
                        error = {}
                    raise QualificationError(safe_code(error.get("code")) or "responses_http_error",
                        error_param=safe_code(error.get("param")))
                buffer = bytearray()
                received = 0
                completed: dict[str, Any] | None = None
                items: dict[int, dict[str, Any]] = {}

                def event(block: bytes) -> None:
                    nonlocal completed
                    lines = [line[5:].lstrip(b" ") for line in block.splitlines() if line.startswith(b"data:")]
                    if not lines:
                        return
                    value = b"\n".join(lines)
                    if value == b"[DONE]":
                        return
                    data = json.loads(value, object_pairs_hook=_unique_json_object)
                    if not isinstance(data, dict):
                        raise QualificationError("stream_event_invalid")
                    kind = data.get("type")
                    if kind == "response.output_item.done":
                        index = data.get("output_index")
                        if (type(index) is not int or not 0 <= index < 16 or index in items
                                or not isinstance(data.get("item"), dict)):
                            raise QualificationError("stream_item_invalid")
                        items[index] = data["item"]
                    if kind in {"response.failed", "response.incomplete", "error"}:
                        container = data.get("response") or data
                        error = container.get("error") if isinstance(container, dict) else None
                        error = error if isinstance(error, dict) else {}
                        raise QualificationError(safe_code(error.get("code")) or str(kind).replace(".", "_"),
                            error_param=safe_code(error.get("param")))
                    if kind == "response.completed":
                        if completed is not None or not isinstance(data.get("response"), dict):
                            raise QualificationError("stream_completion_invalid")
                        completed = data["response"]

                async for chunk in response.aiter_bytes(chunk_size=8192):
                    received += len(chunk)
                    if received > MAX_STREAM_BYTES:
                        raise QualificationError("stream_oversized")
                    if capture is not None:
                        capture(chunk)
                    # Normalize CRLF safely even when the boundary splits across chunks.
                    buffer.extend(chunk)
                    while True:
                        boundary = re.search(br"\r?\n\r?\n", buffer)
                        if not boundary:
                            break
                        if boundary.start() > MAX_EVENT_BYTES:
                            raise QualificationError("stream_event_oversized")
                        block = bytes(buffer[:boundary.start()])
                        del buffer[:boundary.end()]
                        event(block)
                    if len(buffer) > MAX_EVENT_BYTES:
                        raise QualificationError("stream_event_oversized")
                if buffer.strip():
                    event(bytes(buffer))
                if completed is None:
                    raise QualificationError("stream_completion_missing")
                assembled = dict(completed)
                # SIWC can emit a thin completed envelope; finalized output-item
                # events carry its answer. Deltas alone never establish success.
                if assembled.get("output") == [] and items:
                    assembled["output"] = [items[index] for index in sorted(items)]
                try:
                    text = completed_text(assembled)
                except QualificationError as error:
                    # Preserve the bounded model envelope for offline diagnosis; it
                    # contains no OAuth credentials or request Authorization header.
                    error.provider_response = assembled
                    raise
                usage = completed.get("usage")
                usage = usage if isinstance(usage, dict) else {}
                metadata = {"http_status": status, "request_id": request_id,
                    "response_id": safe_code(completed.get("id")), "actual_model": safe_code(completed.get("model")),
                    "stream_bytes": received, "response_status": "completed",
                    "transport_revision": TRANSPORT_REVISION,
                    "input_tokens": usage.get("input_tokens") if type(usage.get("input_tokens")) is int else None,
                    "output_tokens": usage.get("output_tokens") if type(usage.get("output_tokens")) is int else None}
                return text, metadata
    except QualificationError as error:
        error.http_status, error.request_id = status, request_id
        raise
    except (httpx.TimeoutException, TimeoutError):
        raise QualificationError("response_timeout", http_status=status, request_id=request_id) from None
    except httpx.TransportError:
        raise QualificationError("response_transport_error", http_status=status, request_id=request_id) from None
    except (ValueError, TypeError, KeyError):
        raise QualificationError("response_malformed", http_status=status, request_id=request_id) from None


def validate_selection(text: str, case: dict[str, Any]) -> list[dict[str, Any]]:
    if len(text.encode()) > MAX_RESPONSE_BYTES:
        raise QualificationError("response_oversized")
    # Also reject duplicate JSON keys; Pydantic alone does not preserve that distinction.
    json.loads(text, object_pairs_hook=_unique_json_object)
    selection = CompactBatchSelection.model_validate_json(text)
    candidates, article = case["candidates"], case["article"]
    wanted = {candidate.candidate_id: candidate for candidate in candidates}
    ids = [row.candidate_id for row in selection.results]
    if len(ids) != len(set(ids)) or set(ids) != set(wanted):
        raise QualificationError("result_set_identity_invalid")
    auditor = NewsClaimAuditor(AuditorConfig())
    options = auditor._batch_options(candidates, (article.article_text or "").strip())
    results = []
    for row in selection.results:
        candidate = wanted[row.candidate_id]
        selected = row.model_dump(mode="json", exclude={"candidate_id"})
        digest = canonical_claim_sha256(candidate.claim)
        selected["claim_sha256"] = digest
        evidence = _provider_evidence(json.dumps(selected, ensure_ascii=False), options)
        reason = _validate_evidence(evidence, candidate.claim, article, digest)
        outcome, reason = ("invalid", reason) if reason else _classify(evidence, candidate.claim)
        results.append({"candidate_id": row.candidate_id, "claim_sha256": digest,
            "outcome": outcome, "reason_code": reason,
            "evidence": evidence.model_dump(mode="json") if outcome != "invalid" else None})
    return results
