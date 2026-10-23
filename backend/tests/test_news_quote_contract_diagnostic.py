"""V2 cannot reuse v1 authority, change the reviewed request or send twice."""
from copy import deepcopy
import json
from types import SimpleNamespace

import httpx
import pytest

from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.gemini_resolution import INSTRUCTIONS, response_schema, GeminiResolver
from app.services.news_ner_durable.resolution import ResolutionError
from scripts import verify_news_gemini_quote_contract as script
from test_news_gemini_receipts import CONFIG, Receipts, envelope
from test_news_native_resolution import answer
from test_news_pilot_budget import Store


@pytest.fixture
def selection(monkeypatch):
    targets = [{'id': 'n'+str(i), 'label': 'CITY'} for i in range(4)]
    document = {'targets': targets, 'evidence_text': 'Fictional source only.',
        'quote_options': [{'option_index': 0, 'quote': 'Fictional source only.'}]}
    payload = {'systemInstruction': {'parts': [{'text': INSTRUCTIONS}]},
        'contents': [{'parts': [{'text': json.dumps(document)}]}],
        'generationConfig': {'temperature': 0, 'maxOutputTokens': 8192, 'responseMimeType': 'application/json',
            'responseJsonSchema': response_schema(targets, 'compact', 1)}}
    size = len(json.dumps(payload, ensure_ascii=False, allow_nan=False).encode())
    reservation = (2*size+16384)*300+8192*2500
    monkeypatch.setattr(script, 'REQUEST_PIN', sha(payload))
    monkeypatch.setattr(script, 'RESERVATION', reservation)
    monkeypatch.setenv('LANES_NEWS_RECEIPTS_PREFIX', 'private-prefix')
    release = {'application_files': {}, 'database_identity_sha256': 'target', 'resolver': GeminiResolver(CONFIG).identity}
    packet = {'schema_version': 'news-quote-contract-diagnostic-input-v2', 'article_id': 47, 'version_id': 574,
        'context': {'parent_run_id': 375, 'targets_sha256': sha(targets)}, 'batch_index': 0, 'model': CONFIG.model,
        'payload': payload, 'expected_reservation_nanodollars': reservation,
        'original_release_sha256': script.PARENT_RELEASE, 'resolver_identity': release['resolver']}
    authority = {'schema_version': 'news-evidence-diagnostic-authority-v2', 'release_sha256': sha(release),
        'application_sha256': sha({}), 'database_identity_sha256': 'target',
        'allowed_operation': 'verify-quote-contract-one-batch', 'provider_requests': 1, 'database_writes': False,
        'batch_index': 0, 'expected_reservation_nanodollars': reservation, 'request_sha256': sha(payload),
        'parent_pipeline_version': script.PARENT_PIPELINE, 'original_release_sha256': script.PARENT_RELEASE,
        'receipts_prefix': 'private-prefix', 'session_id': 'quote-contract-20261022-v1', 'input_sha256': sha(packet)}
    return release, authority, packet, document


def test_exact_v2_packet_is_admitted_without_rewriting_input(selection):
    release, authority, packet, document = selection
    before = deepcopy(packet)
    assert script.validate_packet(release, authority, packet, sha(authority)) == document
    assert packet == before


@pytest.mark.parametrize('field,value', [('schema_version', 'news-evidence-diagnostic-authority-v1'),
    ('provider_requests', 2), ('database_writes', True), ('request_sha256', 'changed'),
    ('expected_reservation_nanodollars', 1), ('session_id', 'another'),
    ('parent_pipeline_version', 'new-parent'), ('database_identity_sha256', 'another-database')])
def test_old_or_expanded_authority_is_rejected_even_with_new_pin(selection, field, value):
    release, authority, packet, _ = selection
    authority[field] = value
    with pytest.raises(ResolutionError, match='quote_diagnostic_authority_invalid'):
        script.validate_packet(release, authority, packet, sha(authority))


def test_changed_payload_cannot_be_admitted_by_repinning_packet(selection):
    release, authority, packet, _ = selection
    packet['payload']['generationConfig']['temperature'] = 1
    authority['input_sha256'] = sha(packet)
    with pytest.raises(ResolutionError, match='quote_diagnostic_input_changed'):
        script.validate_packet(release, authority, packet, sha(authority))


@pytest.mark.asyncio
async def test_v2_default_preflight_has_no_budget_or_provider_access(selection, monkeypatch):
    release, authority, packet, _ = selection
    monkeypatch.setattr(script, 'verified_input', lambda _: (release, authority, packet, {'counts': {}}))
    monkeypatch.setattr(script, 'GCSLedgerStore', lambda *_: pytest.fail('Preflight tried to access spending ledger'))
    result = await script.execute(SimpleNamespace(allow_one_request=False))
    assert result['status'] == 'preflight_passed' and result['provider_requests'] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('valid', [True, False])
async def test_one_request_stops_after_success_or_failure_and_reinvocation_cannot_resend(selection, monkeypatch, valid):
    release, authority, packet, document = selection
    authority.update(budget_object='fixed-ledger', budget_identity='selection')
    ledger = Store(); receipts = Receipts(); sent = []
    monkeypatch.setattr(script, 'verified_input', lambda _: (release, authority, packet, {}))
    monkeypatch.setattr(script, 'GCSLedgerStore', lambda *_: ledger)
    monkeypatch.setattr(script, 'GCSReceiptStore', lambda *_: receipts)
    monkeypatch.setattr(script.AuditorConfig, 'from_environment', lambda: CONFIG)
    monkeypatch.setenv('LANES_NEWS_PILOT_BUDGET_OBJECT', 'fixed-ledger')
    monkeypatch.setenv('LANES_NEWS_PILOT_BUDGET_IDENTITY', 'selection')
    def respond(request):
        sent.append(1)
        rows = [answer(t) for t in document['targets']]
        if not valid: rows[0]['place_evidence'] = [327]
        return httpx.Response(200, json=envelope(rows))
    monkeypatch.setattr(script.httpx, 'AsyncHTTPTransport', lambda **_: httpx.MockTransport(respond))
    first = await script.execute(SimpleNamespace(allow_one_request=True))
    assert first['status'] == ('one_batch_evidence_references_passed' if valid else 'failed')
    assert first['article_acceptance'] == 'not_evaluated' and first['database_writes'] == 0
    second = await script.execute(SimpleNamespace(allow_one_request=True))
    assert second['status'] == 'failed' and second['provider_requests'] == 0
    assert sent == [1] and ledger.state['status'] == 'stopped'
    assert any(k.endswith('/response.json') for k in receipts.items)
