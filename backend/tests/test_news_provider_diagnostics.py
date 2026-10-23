import json

import httpx
import pytest

from app.services.news_provider_diagnostics import provider_diagnostic, redact_message


@pytest.mark.asyncio
async def test_nested_reason_and_field_violation_survive_generic_message():
    secret = 'a-very-sensitive-key-value-12345'
    response = httpx.Response(400, json={'error': {'status': 'INVALID_ARGUMENT',
        'message': 'Request contains an invalid argument.', 'details': [
            {'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID',
             'metadata': {'key': secret}},
            {'@type': 'type.googleapis.com/google.rpc.BadRequest', 'fieldViolations': [
                {'field': 'generationConfig.responseJsonSchema', 'description': 'Invalid schema '+secret}]}]}})
    result = await provider_diagnostic(response, secrets=(secret,))
    assert result['reasons'] == ['API_KEY_INVALID']
    assert result['field_violations'][0]['field'] == 'generationConfig.responseJsonSchema'
    assert secret not in json.dumps(result) and 'metadata' not in json.dumps(result)


def test_redaction_removes_credentials_urls_and_email_with_bounded_output():
    text = redact_message('API key AQ.fake-sensitive-value here Bearer abc123 https://example.org/key?q=secret user@example.org '+'x'*5000)
    assert len(text) <= 1200
    assert all(value not in text for value in ('AQ.fake', 'abc123', 'example.org', 'user@'))


@pytest.mark.asyncio
async def test_schema_message_and_malformed_body_are_visible_and_safe():
    result = await provider_diagnostic(httpx.Response(400, json={'error': {
        'status': 'INVALID_ARGUMENT', 'message': 'Schema constraint has too many states for serving.'}}))
    assert result['category'] == 'schema_request_rejected'
    assert 'too many states' in result['message']
    result = await provider_diagnostic(httpx.Response(400, text='<not-json>'))
    assert result == {'http_status': 400, 'category': 'provider_request_failed'}
