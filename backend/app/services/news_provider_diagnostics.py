"""Bounded, redacted provider errors, without credentials or arbitrary details."""
from __future__ import annotations

import json
import re
from collections.abc import Iterable

import httpx

STATUSES = {'INVALID_ARGUMENT', 'UNAUTHENTICATED', 'PERMISSION_DENIED',
            'RESOURCE_EXHAUSTED', 'NOT_FOUND', 'FAILED_PRECONDITION', 'UNAVAILABLE', 'INTERNAL'}


def redact_message(value: object, secrets: Iterable[str] = ()) -> str:
    if not isinstance(value, str):
        return ''
    text = value[:16384]
    for secret in secrets:
        if secret:
            text = text.replace(secret, '[redacted]')
    text = re.sub(r'https?://\S+|\bBearer\s+\S+', '[redacted]', text, flags=re.I)
    text = re.sub(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', '[redacted-email]', text, flags=re.I)
    text = re.sub(r'(?:AIza|AQ\.)[A-Za-z0-9_.-]+|[A-Za-z0-9_-]{24,}', '[redacted-token]', text)
    return ' '.join(text.split())[:1200]


async def provider_diagnostic(response: httpx.Response, *, secrets: Iterable[str] = ()) -> dict:
    result = {'http_status': response.status_code, 'category': 'provider_request_failed'}
    raw = bytearray()
    async for chunk in response.aiter_bytes():
        raw.extend(chunk[:max(0, 16384-len(raw))])
        if len(raw) >= 16384:
            break
    try:
        error = json.loads(raw).get('error', {})
        if not isinstance(error, dict):
            return result
        status = error.get('status')
        if status in STATUSES:
            result['provider_status'] = status
        message = redact_message(error.get('message'), secrets)
        if message:
            result['message'] = message
        details = error.get('details', [])
        reasons, fields = [], []
        for detail in details[:8] if isinstance(details, list) else []:
            if not isinstance(detail, dict):
                continue
            if detail.get('@type') == 'type.googleapis.com/google.rpc.ErrorInfo':
                reason = detail.get('reason')
                if isinstance(reason, str) and re.fullmatch(r'[A-Z][A-Z_]{0,79}', reason) and reason not in secrets:
                    reasons.append(reason)
            if detail.get('@type') == 'type.googleapis.com/google.rpc.BadRequest':
                violations = detail.get('fieldViolations', [])
                for violation in violations[:8] if isinstance(violations, list) else []:
                    field = violation.get('field') if isinstance(violation, dict) else None
                    if isinstance(field, str) and re.fullmatch(r'[A-Za-z0-9_.\[\]]{1,160}', field):
                        fields.append({'field': field, 'description': redact_message(violation.get('description'), secrets)})
        if reasons:
            result['reasons'] = sorted(set(reasons))
        if fields:
            result['field_violations'] = fields
        lower = message.casefold()
        for needle, category in (('api key', 'key_configuration_rejected'),
                ('billing', 'billing_required'), ('quota', 'quota_exhausted'),
                ('schema', 'schema_request_rejected'), ('too many states', 'schema_request_rejected'),
                ('not found', 'model_or_resource_unavailable')):
            if needle in lower:
                result['category'] = category
                break
    except (ValueError, TypeError, AttributeError):
        pass
    return result
