"""One explicitly authorized live request; fictional evidence and no SQL writes."""
from __future__ import annotations

import httpx

from app.services.news_ner_durable.adapter import build_native_result, verify_saved_result
from app.services.news_ner_durable.assets import with_resolution_assets
from app.services.news_ner_durable.contracts import RunEvidence, sha
from app.services.news_ner_durable.read_projection import build_read_projection
from app.services.news_ner_durable.resolution import ResolutionError, apply_resolution, targets
from scripts.news_verified_contract import NOW, fixture


async def check_provider(trusted: object, resolver: object, *, transport=None) -> dict:
    text = ('On October 20, 2026 as of 10 AM, Fictional Crescent in Pasig City '
            'was flooded knee-deep.')
    parent_context, raw, parent = fixture(trusted, text)
    derived = with_resolution_assets(trusted, resolver.identity)
    context = RunEvidence.model_validate({**parent_context.model_dump(), 'run_id': 2,
                                         'pipeline_version': derived.pipeline_version})
    baseline = build_native_result(context, raw, derived, extracted_at=NOW)
    if not 1 <= len(targets(baseline)) <= resolver.config.batch_size:
        raise ResolutionError('provider_check_single_request_required')
    receipt = {'status': 'failed', 'database_writes': 0, 'model_inferences': 0,
               'external_provider_requests': 0, 'http_status': None,
               'model': resolver.identity['model'],
               'fixture_kind': 'source_authored_neural_mentions_not_model_predictions'}

    async def request_hook(request):
        if (receipt['external_provider_requests'] or request.method != 'POST'
                or request.url.host != 'generativelanguage.googleapis.com'):
            raise ResolutionError('provider_check_request_limit')
        receipt['external_provider_requests'] += 1

    async def response_hook(response):
        receipt['http_status'] = response.status_code

    try:
        async with httpx.AsyncClient(transport=transport, follow_redirects=False,
                timeout=httpx.Timeout(30, connect=5),
                event_hooks={'request': [request_hook], 'response': [response_hook]}) as client:
            payload = await resolver.resolve(context.source(), baseline, parent_run_id=1,
                parent_result_sha256=sha(parent.model_dump(mode='json', by_alias=True)), client=client)
        result = apply_resolution(context.source(), baseline, payload, derived.catalog, resolver.identity)
        result.read_projection = build_read_projection(context.source(), result, derived.catalog)
        result = verify_saved_result(context, result, derived)
        observations = [c for c in result.claims if c.event_time_resolved
                        and c.event_time_resolved.isoformat() == '2026-10-20T10:00:00+08:00']
        if not observations:
            raise ResolutionError('provider_check_expected_observation_missing')
        receipt.update(status='passed', saved_result_recomputed=True,
                       accepted_observations=len(observations), transport=payload['transport'])
    except ResolutionError as exc:
        receipt.update(error_code=exc.code, retryable=exc.retryable)
        receipt['provider_diagnostic'] = getattr(exc, 'provider_diagnostic', {})
        if getattr(resolver, 'budget', None) is not None:
            resolver.budget.stop(exc.code)
    return receipt
