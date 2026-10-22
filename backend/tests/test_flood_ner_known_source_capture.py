"""Constructed fixtures only: no publisher traffic, news text or model loading."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner.known_source_capture import (
    CaptureBoundaryError, SixLeadSession, file_hash, verify_journal,
)

HTML = b'<html><article>Constructed flood fixture at Sample City.</article></html>'


class InterruptedBody(httpx.SyncByteStream):
    def __iter__(self):
        yield b'<article>Constructed partial fixture'
        raise httpx.ReadError('Synthetic interruption')


class KnownSourceCaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.previous = self.base / 'previous.json'
        self.previous.write_text(json.dumps({'cumulative_actual_exposed_urls': 296,
                                            'legacy_uncertain_url_slots': 4,
                                            'cumulative_capture_attempts': 74,
                                            'ready': False, 'sealed': False}))
        self.evidence = self.base / 'input.json'
        self.urls = [f'https://www.gmanetwork.com/news/fixture/{i}/story/' for i in range(296)]
        self.data = {'schema': 'lanes-six-known-leads-input-v1', 'baseline_urls': self.urls,
                     'leads': [{'url': u, 'eligible': True, 'reason_code': 'supported'} for u in self.urls[:6]],
                     'predecessor_aggregate': {'path': str(self.previous), 'sha256': file_hash(self.previous)},
                     'bindings': [{'path': str(self.previous), 'sha256': file_hash(self.previous)}]}
        self.save()
        self.calls = []

    def save(self):
        self.evidence.write_text(json.dumps(self.data))

    def session(self, handler=None, output='out'):
        def send(request):
            self.calls.append(request)
            return handler(request) if handler else httpx.Response(200, headers={'content-type': 'text/html'}, content=HTML)
        s = SixLeadSession.create(self.base / output, self.evidence,
                                  expected_sha256=file_hash(self.evidence),
                                  _test_transport=httpx.MockTransport(send),
                                  _test_claim_root=self.base / 'claims')
        self.addCleanup(s.close)
        return s

    def test_frozen_capture_and_reservation_precedes_dispatch(self):
        def handler(request):
            self.assertEqual(s.requests, 1)
            self.assertEqual(s.status()['new_uncertain_slots'], 1)
            self.assertEqual(s.status()['cumulative_attempts'], 75)
            self.assertEqual(request.headers['user-agent'], 'LANES-NER-Research/1.0')
            self.assertEqual(request.headers['accept'], 'text/html')
            return httpx.Response(200, headers={'content-type': 'text/html'}, content=HTML)
        s = self.session(handler)
        result = s.capture(0)
        self.assertEqual(result.status, 'captured_pending_review')
        self.assertIn('Constructed', result.capture.text)
        self.assertEqual(s.status()['possible_exposure'], 300)
        self.assertEqual(len(self.calls), 1)
        self.assertGreater(verify_journal(s.directory / 'journal.jsonl')['events'], 1)

    def test_all_six_request_cap_and_no_repeat(self):
        s = self.session()
        for i in range(6):
            s.capture(i)
        for i in [0, 6, -1, True]:
            with self.assertRaises(CaptureBoundaryError): s.capture(i)
        self.assertEqual(len(self.calls), 6)
        self.assertEqual(s.status()['cumulative_attempts'], 80)

    def test_preflight_holds_never_dispatch(self):
        for lead in self.data['leads']: lead['eligible'] = False
        self.save()
        s = self.session()
        for i in range(6): self.assertEqual(s.capture(i).status, 'skipped_preflight_hold')
        self.assertEqual(self.calls, [])
        self.assertEqual(s.status()['cumulative_attempts'], 74)
        self.assertEqual(s.status()['legacy_uncertain_slots'], 4)

    def test_unregistered_substitution_rejected(self):
        self.data['leads'][0]['url'] = 'https://www.gmanetwork.com/news/fixture/new/story/'
        self.save()
        with self.assertRaises(CaptureBoundaryError): self.session()

    def test_wrong_origin_and_duplicate_lead_rejected(self):
        self.data['leads'][1] = self.data['leads'][0].copy()
        self.save()
        with self.assertRaises(CaptureBoundaryError): self.session()

    def test_foreign_origin_rejected_even_if_preexposed(self):
        self.data['baseline_urls'][0] = self.data['leads'][0]['url'] = 'https://example.org/news/fixture/'
        self.save()
        with self.assertRaises(CaptureBoundaryError): self.session()

    def test_stale_input_hash_rejected(self):
        with self.assertRaises(CaptureBoundaryError):
            SixLeadSession.create(self.base / 'out', self.evidence, expected_sha256='0' * 64)

    def test_stale_predecessor_hash_rejected(self):
        self.previous.write_text('{}')
        with self.assertRaises(CaptureBoundaryError): self.session()

    def test_stale_counters_rejected_even_if_binding_updated(self):
        previous = json.loads(self.previous.read_text())
        previous['cumulative_capture_attempts'] = 73
        self.previous.write_text(json.dumps(previous))
        for binding in [self.data['predecessor_aggregate'], *self.data['bindings']]:
            binding['sha256'] = file_hash(self.previous)
        self.save()
        with self.assertRaises(CaptureBoundaryError): self.session()

    def test_evidence_change_after_creation_rejected(self):
        s = self.session()
        self.evidence.write_text('{}')
        with self.assertRaises(CaptureBoundaryError): s.capture(0)
        self.assertEqual(self.calls, [])

    def test_concurrent_and_repeated_launch_rejected(self):
        s = self.session()
        with self.assertRaises(CaptureBoundaryError): self.session(output='second')
        s.close()
        with self.assertRaises(CaptureBoundaryError): self.session(output='third')

    def test_concurrent_capture_writer_rejected(self):
        def handler(request):
            with self.assertRaises(CaptureBoundaryError): s.capture(1)
            return httpx.Response(200, headers={'content-type': 'text/html'}, content=HTML)
        s = self.session(handler)
        s.capture(0)
        self.assertEqual(len(self.calls), 1)

    def test_redirect_followup_blocked_before_second_get(self):
        s = self.session(lambda request: httpx.Response(302, headers={'location': self.urls[1]}))
        self.assertEqual(s.capture(0).status, 'held_capture_failure')
        self.assertEqual(len(self.calls), 1)
        self.assertFalse(s.halted)
        self.assertEqual(s.status()['actual_url_identities'], 296)

    def test_one_new_alias_debited_raw_relative_retained(self):
        s = self.session(lambda request: httpx.Response(302, headers={'location': '/news/fixture/new/story/'}))
        s.capture(0)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(s.status()['actual_url_identities'], 297)
        aliases = json.loads((s.directory / 'request-01.aliases.json').read_text())
        self.assertEqual(aliases['raw_aliases'][0]['raw'], '/news/fixture/new/story/')
        self.assertEqual(s.status()['new_uncertain_slots'], 0)

    def test_six_new_aliases_use_exact_headroom(self):
        s = self.session(lambda request: httpx.Response(302, headers={'location': str(request.url) + 'new'}))
        for i in range(6): s.capture(i)
        self.assertEqual(s.status()['possible_exposure'], 306)
        self.assertEqual(s.status()['remaining_url_slots'], 0)
        self.assertEqual(len(self.calls), 6)

    def test_alias_overreturn_retained_and_batch_held(self):
        s = self.session(lambda request: httpx.Response(302, headers=[('location', self.urls[0] + 'new-a'), ('location', self.urls[0] + 'new-b')]))
        s.capture(0)
        self.assertTrue(s.batch_held)
        self.assertTrue(s.halted)
        self.assertEqual(s.status()['actual_url_identities'], 298)
        self.assertEqual(len(json.loads((s.directory / 'request-01.aliases.json').read_text())['raw_aliases']), 2)
        with self.assertRaises(CaptureBoundaryError): s.capture(1)
        self.assertEqual(len(self.calls), 1)

    def test_multiple_url_tokens_in_single_location_all_debited(self):
        s = self.session(lambda request: httpx.Response(302, headers={'location': self.urls[0] + 'new-a ' + self.urls[0] + 'new-b'}))
        s.capture(0)
        self.assertTrue(s.batch_held)
        self.assertEqual(s.status()['actual_url_identities'], 298)
        self.assertEqual(len(self.calls), 1)

    def test_comma_separated_redirect_targets_debited_before_rejection(self):
        s = self.session(lambda request: httpx.Response(302, headers={'location': self.urls[0] + 'new-a,' + self.urls[0] + 'new-b'}))
        s.capture(0)
        self.assertTrue(s.batch_held)
        self.assertEqual(s.status()['actual_url_identities'], 298)

    def test_duplicate_raw_redirect_aliases_preserved_without_double_debit(self):
        target = self.urls[0] + 'new'
        s = self.session(lambda request: httpx.Response(302, headers=[('location', target), ('location', target)]))
        s.capture(0)
        self.assertEqual(s.status()['actual_url_identities'], 297)
        self.assertFalse(s.batch_held)
        aliases = json.loads((s.directory / 'request-01.aliases.json').read_text())
        self.assertEqual(len(aliases['raw_aliases']), 2)

    def test_invalid_alias_still_preserves_header_receipt(self):
        s = self.session(lambda request: httpx.Response(302, headers={'location': 'https://[invalid'}))
        s.capture(0)
        self.assertTrue(s.batch_held)
        self.assertTrue((s.directory / 'request-01.headers.json').is_file())
        self.assertEqual(len(self.calls), 1)

    def test_interrupted_body_keeps_headers_partial_and_uncertainty(self):
        s = self.session(lambda request: httpx.Response(200, headers={'content-type': 'text/html'}, stream=InterruptedBody()))
        s.capture(0)
        self.assertTrue(s.halted)
        self.assertTrue((s.directory / 'request-01.headers.json').exists())
        self.assertIn(b'Constructed', (s.directory / 'request-01.partial.body').read_bytes())
        self.assertEqual(s.status()['new_uncertain_slots'], 1)
        self.assertEqual(s.status()['cumulative_attempts'], 75)
        with self.assertRaises(CaptureBoundaryError): s.capture(0)

    def test_headers_exist_before_body_iteration(self):
        outer = self
        class InspectedBody(httpx.SyncByteStream):
            def __iter__(self):
                outer.assertTrue((s.directory / 'request-01.headers.json').is_file())
                yield HTML
        s = self.session(lambda request: httpx.Response(200, headers={'content-type': 'text/html'}, stream=InspectedBody()))
        self.assertEqual(s.capture(0).status, 'captured_pending_review')

    def test_oversized_body_preserved_as_partial_and_stops(self):
        s = self.session(lambda request: httpx.Response(200, headers={'content-type': 'text/html'}, content=b'x' * (4 * 1024 * 1024 + 1)))
        s.capture(0)
        self.assertTrue(s.halted)
        self.assertGreater((s.directory / 'request-01.partial.body').stat().st_size, 4 * 1024 * 1024)
        self.assertFalse((s.directory / 'request-01.body').exists())
        self.assertEqual(s.status()['new_uncertain_slots'], 1)

    def test_network_failure_has_no_hidden_retry(self):
        def fail(request): raise httpx.ConnectError('Constructed connect failure')
        s = self.session(fail)
        s.capture(0)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(s.status()['new_uncertain_slots'], 1)
        self.assertTrue(s.halted)

    def test_rate_limit_receipt_stops_batch_without_wait_retry(self):
        s = self.session(lambda request: httpx.Response(429, headers={'retry-after': '120', 'set-cookie': 'secret=fixture'}))
        s.capture(0)
        receipt = json.loads((s.directory / 'request-01.headers.json').read_text())
        self.assertEqual(receipt['headers']['retry-after'], ['120'])
        self.assertNotIn('set-cookie', receipt['headers'])
        with self.assertRaises(CaptureBoundaryError): s.capture(1)
        self.assertEqual(len(self.calls), 1)

    def test_journal_tampering_rejected_before_dispatch(self):
        s = self.session()
        path = s.directory / 'journal.jsonl'
        path.write_bytes(path.read_bytes().replace(b'initialize', b'initializE'))
        with self.assertRaises(CaptureBoundaryError): s.capture(0)
        self.assertEqual(self.calls, [])

    def test_truncated_journal_rejected(self):
        s = self.session()
        path = s.directory / 'journal.jsonl'
        path.write_bytes(path.read_bytes()[:-1])
        with self.assertRaises(CaptureBoundaryError): verify_journal(path)

    def test_owned_transport_configuration(self):
        with patch('training.flood_ner.known_source_capture.httpx.HTTPTransport') as transport:
            transport.return_value = httpx.MockTransport(lambda request: httpx.Response(200))
            s = SixLeadSession.create(self.base / 'owned', self.evidence, expected_sha256=file_hash(self.evidence), _test_claim_root=self.base / 'claims')
            self.addCleanup(s.close)
            transport.assert_called_once_with(verify=True, retries=0, trust_env=False)
            self.assertFalse(s._client.follow_redirects)
            self.assertEqual(s._client.timeout.read, 30)


if __name__ == '__main__':
    unittest.main()
