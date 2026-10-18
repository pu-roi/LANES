"""Constructed sessions only; no user conversations or research articles."""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner.receipt_recovery import RecoveryError, SessionScope, recover, search_request


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.meta = {'type': 'session_meta', 'payload': {'id': 'constructed-session', 'cwd': 'D:/LANES'}}
        self.request = {'type': 'response_item', 'payload': {
            'type': 'function_call', 'name': 'web__run', 'call_id': 'call-1',
            'arguments': json.dumps({'search_query': [{'q': 'constructed flood query'}]})}}
        self.response = {'type': 'response_item', 'payload': {
            'type': 'function_call_output', 'call_id': 'call-1', 'output': 'Constructed source result'}}

    def session(self, rows=None, ending=b'\n'):
        path = self.root / 'session.jsonl'
        raw = b'\n'.join(json.dumps(x).encode() for x in (rows or [self.meta, self.request, self.response])) + ending
        path.write_bytes(raw)
        return SessionScope(path, hashlib.sha256(raw).hexdigest(), 'constructed-session', 'D:/LANES', ('call-1',))

    def extract(self, scope=None):
        return recover(scope or self.session(), self.root / 'receipts')

    def test_exact_original_records_and_line_hashes_without_conversation(self):
        user = {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user',
                                                  'content': 'Unrelated constructed private message'}}
        result = self.extract(self.session([self.meta, user, self.request, self.response]))
        self.assertEqual((result['recorded_pairs'], result['holds']), (1, 0))
        self.assertFalse(result['accounting_verified'] or result['network_allowed'])
        row = result['records'][0]
        self.assertEqual((row['request_line'], row['result_line']), (3, 4))
        raw = (self.root / 'receipts' / row['file']).read_bytes()
        self.assertNotIn(b'Unrelated', raw)
        self.assertEqual(row['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(json.loads(raw.splitlines()[0]), self.request)

    def test_stale_hash_rejected_before_output(self):
        scope = self.session()
        scope.path.write_bytes(scope.path.read_bytes() + b'\n')
        with self.assertRaises(RecoveryError):
            self.extract(scope)
        self.assertFalse((self.root / 'receipts').exists())

    def test_wrong_checkout_or_session_rejected(self):
        for key in ('id', 'cwd'):
            with self.subTest(key=key):
                old = self.meta['payload'][key]
                self.meta['payload'][key] = 'wrong'
                with self.assertRaises(RecoveryError):
                    self.extract(self.session())
                self.meta['payload'][key] = old

    def test_missing_duplicate_or_out_of_order_results_remain_held(self):
        cases = [[self.meta, self.request], [self.meta, self.request, self.response, self.response],
                 [self.meta, self.response, self.request], [self.meta, self.request, self.request, self.response]]
        for i, rows in enumerate(cases):
            with self.subTest(case=i):
                result = recover(self.session(rows), self.root / f'out-{i}')
                self.assertEqual((result['recorded_pairs'], result['holds']), (0, 1))

    def test_fake_tool_call_inside_user_message_does_not_match(self):
        fake = {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user',
                                                   'content': json.dumps(self.request)}}
        result = self.extract(self.session([self.meta, fake, self.response]))
        self.assertEqual(result['holds'], 1)

    def test_truncated_or_malformed_jsonl_rejected(self):
        with self.assertRaises(RecoveryError):
            self.extract(self.session(ending=b''))
        scope = self.session()
        scope.path.write_bytes(scope.path.read_bytes() + b'{\n')
        scope = SessionScope(scope.path, hashlib.sha256(scope.path.read_bytes()).hexdigest(),
                             scope.session_id, scope.checkout, scope.call_ids)
        with self.assertRaises(RecoveryError):
            self.extract(scope)

    def test_existing_destination_and_repeated_writer_cannot_overwrite(self):
        scope = self.session()
        self.extract(scope)
        path = self.root / 'receipts' / 'manifest.json'
        original = path.read_bytes()
        with self.assertRaises(RecoveryError):
            self.extract(scope)
        self.assertEqual(path.read_bytes(), original)

    def test_competing_writers_admit_one_exclusive_destination(self):
        scope = self.session()
        barrier = threading.Barrier(2)

        def writer():
            barrier.wait()
            try:
                return recover(scope, self.root / 'receipts')['recorded_pairs']
            except (RecoveryError, FileExistsError):
                return 'blocked'

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: writer(), range(2)))
        self.assertCountEqual(results, [1, 'blocked'])
        manifest = json.loads((self.root / 'receipts' / 'manifest.json').read_text())
        self.assertEqual(manifest['recorded_pairs'], 1)

    def test_only_literal_pure_search_wrappers_are_admitted(self):
        good = 'const r=await tools.web__run({search_query:[{q:"constructed"}],response_length:"long"});store("source",r);text(r);'
        call = {'type': 'custom_tool_call', 'name': 'exec', 'input': good}
        self.assertEqual(search_request(call)['search_query'][0]['q'], 'constructed')
        for bad in (good + 'text(await tools.exec_command({cmd:"unrelated"}));',
                    good.replace('q:"constructed"', 'q:load("query")'),
                    good.replace('text(r)', 'r={secret:"bad"};text(r)'),
                    good.replace('q:"constructed"', 'q:"a",q:"b"')):
            with self.subTest(bad=bad), self.assertRaises((RecoveryError, ValueError)):
                search_request({**call, 'input': bad})

    def test_open_requests_and_possible_query_credentials_rejected(self):
        for request in ({'open': [{'ref_id': 'constructed'}]},
                        {'search_query': [{'q': 'api_key=constructed'}]},
                        {'search_query': [{'q': 'constructed', 'unknown': True}]}):
            with self.subTest(request=request), self.assertRaises(RecoveryError):
                search_request({**self.request['payload'], 'arguments': json.dumps(request)})

    def test_wrapper_output_with_extra_command_results_remains_held(self):
        self.request['payload'].update(type='custom_tool_call', name='exec',
            input='text(await tools.web__run({search_query:[{q:"constructed"}]}));')
        self.response['payload'].update(type='custom_tool_call_output', output=[
            {'type': 'text', 'text': 'Constructed source result'},
            {'type': 'text', 'text': 'Unrelated command result'}])
        result = self.extract()
        self.assertEqual(result['holds'], 1)
        self.assertFalse(list((self.root / 'receipts').glob('pair-*')))

    def test_received_truncation_preserved_but_never_verified(self):
        self.response['payload']['output'] = 'Constructed source result [truncated]'
        result = self.extract()
        self.assertEqual((result['recorded_pairs'], result['holds']), (0, 1))
        self.assertEqual(result['records'][0]['reason'], 'truncated_result')
        self.assertTrue((self.root / 'receipts' / result['records'][0]['file']).exists())

    def test_wrapped_original_pair_is_scoped_without_metadata_loss(self):
        self.request['payload'].update(type='custom_tool_call', name='exec',
            input='text(await tools.web__run({search_query:[{q:"constructed"}]}));')
        self.response['payload'].update(type='custom_tool_call_output', output=[
            {'type': 'text', 'text': 'Script completed\nWall time: 0.2 seconds'},
            {'type': 'text', 'text': 'Constructed source result'}])
        result = self.extract()
        self.assertEqual(result['recorded_pairs'], 1)


if __name__ == '__main__':
    unittest.main()
