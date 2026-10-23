"""One manually authorized immutable request replay, no SQL or neural inference."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, '/app')

import httpx

from app.services.news_ner_durable.contracts import sha
from app.services.news_pilot_budget import GCSLedgerStore, MODEL, PilotBudget
from app.services.news_provider_diagnostics import provider_diagnostic


async def diagnose() -> dict:
    packet = json.loads(Path('/diagnostic/request.json').read_text())
    if sha(packet) != os.environ['LANES_DIAGNOSTIC_PACKET_SHA256']:
        raise ValueError('diagnostic_packet_changed')
    payload, context = packet['payload'], packet['context']
    if sha({'request_sha256': sha(payload), 'context': context}) != packet['original_attempt_id']:
        raise ValueError('diagnostic_original_request_changed')
    resume_id = os.environ['LANES_DIAGNOSTIC_RESUME_ID']
    if not resume_id or len(resume_id) > 80:
        raise ValueError('diagnostic_manual_resume_required')
    budget = PilotBudget(GCSLedgerStore('lanes-storage', os.environ['LANES_NEWS_PILOT_BUDGET_OBJECT']),
                         os.environ['LANES_NEWS_PILOT_BUDGET_IDENTITY'])
    attempt = budget.reserve(MODEL, payload, {**context, 'manual_diagnostic_resume': resume_id})
    receipt = {'schema': 'news-gemini-diagnostic-v1', 'original_attempt_id': packet['original_attempt_id'],
        'request_payload_sha256': sha(payload), 'model': MODEL, 'provider_requests': 0,
        'database_writes': 0, 'neural_inferences': 0, 'status': 'failed'}
    diagnostic = {}
    success = False
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30, connect=5), follow_redirects=False,
                transport=httpx.AsyncHTTPTransport(retries=0)) as client:
            receipt['provider_requests'] = 1
            async with client.stream('POST',
                    'https://generativelanguage.googleapis.com/v1beta/models/'+MODEL+':generateContent',
                    headers={'x-goog-api-key': os.environ['GEMINI_API_KEY']}, json=payload) as response:
                receipt['http_status'] = response.status_code
                if response.status_code != 200:
                    diagnostic = await provider_diagnostic(response, secrets=(os.environ['GEMINI_API_KEY'],))
                    receipt['diagnostic'] = diagnostic
                else:
                    raw = bytearray()
                    async for chunk in response.aiter_bytes():
                        raw.extend(chunk)
                        if len(raw) > 65536:
                            raise ValueError('diagnostic_response_too_large')
                    envelope = json.loads(raw)
                    usage = envelope.get('usageMetadata', {})
                    diagnostic = {k: v for k, v in usage.items()
                        if k in ('promptTokenCount', 'candidatesTokenCount', 'thoughtsTokenCount')
                        and type(v) is int and 0 <= v <= 10000000}
                    receipt.update(status='transport_passed_not_article_acceptance', usage=diagnostic)
                    success = True
    except (httpx.TransportError, TimeoutError, ValueError) as exc:
        receipt['error_type'] = type(exc).__name__
    finally:
        budget.finish(attempt, succeeded=success, diagnostic=diagnostic)
        # A diagnostic never opens permission for subsequent seed requests.
        budget.stop('manual_diagnostic_completed_requires_review')
    return receipt


def main() -> int:
    try:
        result = asyncio.run(diagnose())
    except Exception as exc:
        result = {'schema': 'news-gemini-diagnostic-v1', 'status': 'failed',
                  'error_code': getattr(exc, 'code', 'diagnostic_failed'), 'error_type': type(exc).__name__}
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if result['status'] == 'transport_passed_not_article_acceptance' else 1


if __name__ == '__main__':
    raise SystemExit(main())
