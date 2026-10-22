"""Mock transports and constructed receipts only. Never contacts publishers."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner import research_capture as capture
from training.flood_ner.research_review import FileBinding, ReviewError, file_hash

HTML = b'<html><article>Constructed rain in Sample City.</article></html>'


class InterruptedBody(httpx.SyncByteStream):
    def __iter__(self):
        yield b'<article>Constructed partial'
        raise httpx.ReadError('constructed interruption')


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.urls = [f'https://www.gmanetwork.com/news/constructed/{i}/story/' for i in range(8)]
        self.calls = []
        self.auth = dict(schema='lanes-research-capture-grant-v1', network_allowed=True,
                         url_ceiling=30, publisher_ceiling=100, task_request_limit=6, alias_reservation=1,
                         claim_root=str((self.root / 'claims').resolve()))
        receipt = self.write('original-receipt.json', {'constructed_original_urls': self.urls})
        self.proof = dict(schema='lanes-research-capture-preflight-v1',
            implementation_sha256=file_hash(Path(capture.__file__)), accounting_verified=True,
            original_receipts_verified=True, unquantified_exposure=False, interrupted_request=False,
            original_receipts=[self.raw_binding(receipt)], raw_identities=self.urls,
            uncertain_slots=4, publisher_attempts=74)
        journal = self.write('predecessor-journal.json', {'constructed_original_journal': True})
        replay = self.write('predecessor-replay.json', dict(journal_sha256=journal.sha256,
            accounting_verified=True, original_receipts_verified=True, unquantified_exposure=False,
            interrupted_request=False, original_receipt_sha256=[receipt.sha256],
            raw_identity_union_sha256=hashlib.sha256(capture._canonical(sorted(self.urls))).hexdigest(),
            uncertain_slots=4, publisher_attempts=74))
        self.proof.update(predecessor_journal=self.raw_binding(journal), predecessor_replay=self.raw_binding(replay))
        source = FileBinding(Path(__file__), file_hash(Path(__file__)))
        self.test_data = dict(implementation_sha256=self.proof['implementation_sha256'], passed=1, failed=0,
                              test_source=self.raw_binding(source))
        self.rebind()

    def raw_binding(self, binding):
        return dict(path=str(binding.path), sha256=binding.sha256)

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding='utf-8')
        return FileBinding(path, file_hash(path))

    def rebind(self):
        self.proof['test_results'] = self.raw_binding(self.write('test-results.json', self.test_data))
        self.auth['preflight_evidence_sha256'] = hashlib.sha256(capture._canonical(
            {k: v for k, v in self.proof.items() if k != 'authorization_sha256'})).hexdigest()
        self.authorization = self.write('authorization.json', self.auth)
        self.proof['authorization_sha256'] = self.authorization.sha256
        self.preflight = self.write('preflight.json', self.proof)

    def review(self, index=0):
        return self.write(f'source-review-{index}.json', dict(url=self.urls[index], eligible=True,
            evidence=[self.raw_binding(FileBinding(Path(__file__), file_hash(Path(__file__))))]))

    def session(self, handler=None, directory='out'):
        def send(request):
            self.calls.append(request)
            return handler(request) if handler else httpx.Response(200, headers={'content-type': 'text/html'}, content=HTML)
        return capture.ResearchCaptureSession(self.root / directory, self.authorization, self.preflight,
                       claim_root=self.root / 'claims', _test_transport=httpx.MockTransport(send))

    def rows(self, session):
        return capture.read_journal(session.directory / 'journal.jsonl')

    def test_reservation_precedes_dispatch_and_client_headers(self):
        def handler(request):
            self.assertEqual(session.attempts, 75)
            self.assertEqual(session.pending, 5)
            self.assertEqual(self.rows(session)[-1]['kind'], 'publisher_dispatched')
            self.assertEqual(request.headers['user-agent'], 'LANES-NER-Research/1.0')
            self.assertIn('text/html', request.headers['accept'])
            self.assertEqual(request.extensions['timeout']['read'], 30)
            return httpx.Response(200, headers={'content-type': 'text/html', 'set-cookie': 'secret-fixture'}, content=HTML)
        session = self.session(handler)
        self.assertTrue(session.capture(self.urls[0], 'c0', self.review())['success'])
        self.assertEqual(session.pending, 4)
        self.assertEqual(session.attempts, 75)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual((session.directory / 'c0.raw.html').read_bytes(), HTML)
        receipt = json.loads((session.directory / 'c0.headers.json').read_text())
        self.assertNotIn('set-cookie', receipt['headers'])
        session.close()

    def test_missing_stale_or_unverified_preflight_blocks_before_claim(self):
        cases = [{'accounting_verified': False}, {'original_receipts_verified': False},
                 {'unquantified_exposure': True}, {'interrupted_request': True},
                 {'original_receipts': []}, {'authorization_sha256': '0' * 64},
                 {'implementation_sha256': '0' * 64}]
        original_proof = dict(self.proof)
        for i, updates in enumerate(cases):
            self.proof = {**original_proof, **updates}
            self.rebind()
            if 'authorization_sha256' in updates:
                self.proof['authorization_sha256'] = updates['authorization_sha256']
            binding = self.write(f'bad-{i}.json', self.proof)
            with self.subTest(updates=updates), self.assertRaises(ReviewError):
                capture.ResearchCaptureSession(self.root / f'out-{i}', self.authorization, binding,
                    claim_root=self.root / 'claims', _test_transport=httpx.MockTransport(lambda r: self.fail('dispatch')))
            self.assertFalse((self.root / f'out-{i}').exists())
        self.assertFalse((self.root / 'claims').exists())

    def test_review_only_scope_cannot_dispatch(self):
        self.auth['network_allowed'] = False
        self.rebind()
        with self.assertRaises(ReviewError):
            self.session()
        self.assertEqual(self.calls, [])

    def test_matching_successful_test_evidence_required(self):
        original_test_data = dict(self.test_data)
        for i, updates in enumerate(({'passed': 0}, {'failed': 1}, {'failed': False},
                                     {'implementation_sha256': 'b' * 64})):
            self.test_data = {**original_test_data, **updates}
            self.rebind()
            with self.subTest(updates=updates), self.assertRaises(ReviewError):
                self.session(directory=f'out-{i}')

    def test_missing_original_receipt_blocks_even_with_counters(self):
        Path(self.proof['original_receipts'][0]['path']).unlink()
        with self.assertRaises(ReviewError):
            self.session()

    def test_stale_authorization_and_preflight_hashes(self):
        self.authorization.path.write_text('{}')
        with self.assertRaises(ReviewError):
            self.session()
        self.rebind()
        self.preflight.path.write_text('{}')
        with self.assertRaises(ReviewError):
            self.session()

    def test_rebound_preflight_cannot_substitute_unapproved_accounting(self):
        self.proof['publisher_attempts'] = 0
        self.preflight = self.write('preflight.json', self.proof)
        with self.assertRaisesRegex(ReviewError, 'exact preflight'):
            self.session()

    def test_stale_predecessor_journal_or_replay_baseline_rejected(self):
        path = Path(self.proof['predecessor_journal']['path'])
        prior = path.read_bytes()
        path.write_bytes(b'changed after reviewed grant')
        with self.assertRaises(ReviewError):
            self.session()
        path.write_bytes(prior)
        self.proof['publisher_attempts'] = 0
        self.rebind()  # Even a separately bound grant cannot ignore replay mismatch.
        with self.assertRaisesRegex(ReviewError, 'stale replay'):
            self.session()

    def test_repeated_or_concurrent_authorization_rejected(self):
        session = self.session()
        with self.assertRaises(FileExistsError):
            self.session(directory='other')
        session._lock.acquire()
        try:
            with self.assertRaisesRegex(ReviewError, 'concurrent'):
                session.capture(self.urls[0], 'c0', self.review())
        finally:
            session._lock.release()
        session.close()
        with self.assertRaises(FileExistsError):
            self.session(directory='after-close')
        self.assertEqual(self.calls, [])

    def test_claim_location_cannot_bypass_consumed_authorization(self):
        self.session()
        with self.assertRaisesRegex(ReviewError, 'claim location'):
            capture.ResearchCaptureSession(self.root / 'different', self.authorization, self.preflight,
                claim_root=self.root / 'different-claims', _test_transport=httpx.MockTransport(lambda r: self.fail('dispatch')))

    def test_existing_destination_and_receipt_never_overwritten(self):
        destination = self.root / 'out'
        destination.mkdir()
        marker = destination / 'prior.raw'
        marker.write_bytes(b'preserved')
        with self.assertRaises(ReviewError):
            self.session()
        self.assertEqual(marker.read_bytes(), b'preserved')
        session = self.session(directory='new')
        prior = session.directory / 'c0.raw.html'
        prior.write_bytes(b'preserved')
        with self.assertRaises(ReviewError):
            session.capture(self.urls[0], 'c0', self.review())
        self.assertEqual(prior.read_bytes(), b'preserved')
        with self.assertRaises(FileExistsError):
            capture.exclusive_bytes(prior, b'overwrite')
        self.assertEqual(self.calls, [])

    def test_six_request_cap_and_inherited_uncertainty(self):
        session = self.session()
        for i in range(6):
            self.assertTrue(session.capture(self.urls[i], f'c{i}', self.review(i))['success'])
        with self.assertRaisesRegex(ReviewError, 'exhausted'):
            session.capture(self.urls[6], 'c6', self.review(6))
        self.assertEqual((len(self.calls), session.attempts, session.pending), (6, 80, 4))

    def test_reservation_exhaustion_prevents_network(self):
        self.auth['url_ceiling'] = len(self.urls) + 4
        self.rebind()
        session = self.session()
        with self.assertRaisesRegex(ReviewError, 'exhausted'):
            session.capture(self.urls[0], 'c0', self.review())
        self.assertEqual(self.calls, [])

    def test_failed_parser_is_accounted_and_prevents_next_dispatch(self):
        session = self.session()
        def parse(*args):
            raise ValueError('constructed parse failure')
        result = session.capture(self.urls[0], 'c0', self.review(), _parser=parse)
        self.assertTrue(result['halted'])
        self.assertFalse(result['success'])
        self.assertEqual(session.pending, 5)
        self.assertEqual((session.directory / 'c0.raw.html').read_bytes(), HTML)
        self.assertEqual(self.rows(session)[-1]['kind'], 'publisher_accounted')
        self.assertFalse(self.rows(session)[-1]['data']['success'])
        with self.assertRaises(ReviewError):
            session.capture(self.urls[1], 'c1', self.review(1))
        self.assertEqual(len(self.calls), 1)

    def test_interrupted_read_preserves_headers_and_partial_bytes(self):
        session = self.session(lambda r: httpx.Response(200, headers={'content-type': 'text/html'}, stream=InterruptedBody()))
        result = session.capture(self.urls[0], 'c0', self.review())
        self.assertTrue(result['halted'])
        self.assertEqual((session.directory / 'c0.raw.html').read_bytes(), b'<article>Constructed partial')
        self.assertTrue((session.directory / 'c0.headers.json').exists())
        self.assertEqual([r['kind'] for r in self.rows(session)],
                         ['initialized', 'publisher_dispatched', 'headers_received', 'publisher_accounted'])

    def test_malformed_identity_headers_preserved_before_rejection(self):
        urls = 'https://example.org/a https://example.org/b'
        session = self.session(lambda r: httpx.Response(200, headers={'content-type': 'text/html', 'location': urls}, content=HTML))
        result = session.capture(self.urls[0], 'c0', self.review())
        self.assertTrue(result['halted'])
        self.assertTrue({'https://example.org/a', 'https://example.org/b'} <= session.raw)
        self.assertTrue(json.loads((session.directory / 'c0.headers.json').read_text())['malformed'])
        self.assertEqual(len(self.calls), 1)

    def test_malformed_relative_and_credential_identity_headers(self):
        for value in ('', 'javascript:alert(1)', '/bad path', 'https://user:pass@example.org/a', 'https://[invalid/'):
            with self.subTest(value=value):
                self.assertTrue(capture.header_identities(self.urls[0], httpx.Headers({'location': value}))[2])

    def test_duplicate_alias_counted_once_raw_header_retained(self):
        alias = 'https://example.org/alias'
        session = self.session(lambda r: httpx.Response(200, headers=[('content-type', 'text/html'),
                     ('link', f'<{alias}>; rel=canonical'), ('link', f'<{alias}>; rel=alternate')], content=HTML))
        self.assertTrue(session.capture(self.urls[0], 'c0', self.review())['success'])
        self.assertEqual(len(session.raw), len(self.urls) + 1)
        receipt = json.loads((session.directory / 'c0.headers.json').read_text())
        self.assertEqual(len(receipt['identity_headers']['link']), 2)

    def test_alias_overrun_halts_and_keeps_all_received_identities(self):
        session = self.session(lambda r: httpx.Response(200, headers={'content-type': 'text/html',
            'link': '<https://example.org/a>; rel=canonical, <https://example.org/b>; rel=alternate'}, content=HTML))
        self.assertFalse(session.capture(self.urls[0], 'c0', self.review())['success'])
        self.assertEqual(len(session.raw), len(self.urls) + 2)
        self.assertEqual(session.pending, 5)

    def test_body_aliases_checked_before_success(self):
        html = b'<link rel="canonical" href="https://example.org/a"><meta property="og:url" content="https://example.org/b"><article>Constructed.</article>'
        session = self.session(lambda r: httpx.Response(200, headers={'content-type': 'text/html'}, content=html))
        self.assertFalse(session.capture(self.urls[0], 'c0', self.review())['success'])
        self.assertEqual(len(session.raw), len(self.urls) + 2)
        self.assertEqual((session.directory / 'c0.raw.html').read_bytes(), html)

    def test_redirect_never_followed_or_retried(self):
        session = self.session(lambda r: httpx.Response(302, headers={'location': 'https://example.org/redirect'}))
        self.assertFalse(session.capture(self.urls[0], 'c0', self.review())['success'])
        self.assertEqual(len(self.calls), 1)
        self.assertIn('https://example.org/redirect', session.raw)
        self.assertEqual(session.attempts, 75)

    def test_http_failures_and_transport_errors_never_retry(self):
        def failure(request):
            raise httpx.ConnectError('constructed transport failure')
        session = self.session(failure)
        self.assertFalse(session.capture(self.urls[0], 'c0', self.review())['success'])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.rows(session)[-1]['data']['failure_kind'], 'ConnectError')

    def test_nonhtml_response_rejected(self):
        session = self.session(lambda r: httpx.Response(200, headers={'content-type': 'application/json'}, content=b'{}'))
        self.assertFalse(session.capture(self.urls[0], 'c0', self.review())['success'])
        self.assertEqual(session.pending, 5)

    def test_zero_retry_verified_transport_options(self):
        session = self.session()
        session._transport = None
        transport = httpx.MockTransport(lambda r: httpx.Response(503))
        with patch.object(capture.httpx, 'HTTPTransport', return_value=transport) as constructor:
            self.assertFalse(session.capture(self.urls[0], 'c0', self.review())['success'])
        constructor.assert_called_once_with(retries=0, verify=True, trust_env=False)

    def test_live_parser_override_forbidden_before_request(self):
        session = self.session()
        session._transport = None
        with self.assertRaisesRegex(ReviewError, 'test-only'):
            session.capture(self.urls[0], 'c0', self.review(), _parser=lambda *a: None)
        self.assertEqual(self.calls, [])

    def test_interrupted_journal_blocks_further_dispatch(self):
        session = self.session()
        path = session.directory / 'journal.jsonl'
        with path.open('ab') as stream:
            stream.write(b'{"interrupted":')
        before = path.read_bytes()
        with self.assertRaises(ReviewError):
            session.capture(self.urls[0], 'c0', self.review())
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.calls, [])
        with self.assertRaises(ReviewError):
            capture.read_journal(path)

    def test_accounting_append_failure_keeps_reservation_and_halts(self):
        session = self.session()
        original = session._append
        def append(kind, data):
            if kind == 'publisher_accounted':
                raise OSError('constructed disk failure')
            original(kind, data)
        session._append = append
        with self.assertRaises(OSError):
            session.capture(self.urls[0], 'c0', self.review())
        self.assertEqual(session.pending, 5)
        self.assertTrue(session.halted)
        with self.assertRaises(ReviewError):
            session.capture(self.urls[1], 'c1', self.review(1))
        self.assertEqual(len(self.calls), 1)

    def test_changed_authorization_before_dispatch_blocks(self):
        session = self.session()
        self.preflight.path.write_text('{}')
        with self.assertRaises(ReviewError):
            session.capture(self.urls[0], 'c0', self.review())
        self.assertEqual(self.calls, [])

    def test_duplicate_retry_and_unregistered_identity_rejected(self):
        session = self.session()
        session.capture(self.urls[0], 'c0', self.review())
        with self.assertRaises(ReviewError):
            session.capture(self.urls[0], 'new', self.review())
        unregistered = 'https://www.gmanetwork.com/news/constructed/unknown/story/'
        review = self.write('unregistered.json', dict(url=unregistered, eligible=True,
            evidence=[self.raw_binding(FileBinding(Path(__file__), file_hash(Path(__file__))))]))
        with self.assertRaises(ReviewError):
            session.capture(unregistered, 'new', review)
        self.assertEqual(len(self.calls), 1)


if __name__ == '__main__':
    unittest.main()
