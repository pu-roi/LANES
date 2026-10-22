"""Portable history handoff boundaries; runs with unittest, no app or database."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location('history_inventory',
    Path(__file__).resolve().parents[1] / 'training/flood_ner/history_inventory.py')
h = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(h)


class HistoryInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'checkout'
        self.root.mkdir()
        (self.root / 'DESIGN.md').write_text('constructed checkout', encoding='utf-8')
        self.output = self.base / 'new-report'

    def put(self, name, text='do not export these contents'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def read_result(self):
        return json.loads((self.output / 'inventory.json').read_text())

    def test_hashes_without_body_annotation_or_archive_execution(self):
        source = self.put('captures/body.txt', 'private captured text')
        self.put('annotations.json', '{"entities":["private annotation"]}')
        self.put('backup.zip', 'not even a valid archive')
        self.put('RESTORE.py', 'raise RuntimeError("never execute")')
        summary = h.inventory(self.root, [], self.output)
        result = self.read_result()
        self.assertEqual(summary['files_hashed'], 5)
        self.assertNotIn('private captured text', json.dumps(result))
        self.assertNotIn('private annotation', json.dumps(result))
        row = next(r for r in result['files'] if r['path'] == 'captures/body.txt')
        self.assertEqual(row['sha256'], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertFalse(result['external_history_complete'])
        self.assertFalse(result['fresh_test_sealed'])
        manifest = json.loads((self.output / 'manifest.json').read_text())
        self.assertEqual(manifest['files']['inventory.json'], h.digest(self.output / 'inventory.json'))

    def test_excluded_files_never_opened(self):
        names = ['.env', '.env.production', 'credentials.json', 'id_rsa', 'server.pem',
                 'models/encoder/config.json', 'venv/pyvenv.cfg', 'research-env-v1/test',
                 'node_modules/x.js', 'weights.safetensors', 'weights.bin',
                 'heldout-targeted-collection-v1/candidates.jsonl',
                 'additional-heldout-curation-v1/sources.jsonl', 'fresh_test.jsonl']
        for name in names:
            self.put(name)
        original = h.digest
        def guarded(path):
            if path.is_relative_to(self.root):
                self.assertIsNone(h.excluded_reason(path.relative_to(self.root)))
            return original(path)
        with patch.object(h, 'digest', guarded):
            h.inventory(self.root, [], self.output)
        self.assertEqual(len(self.read_result()['files']), 1)

    def test_existing_output_and_overlapping_roots_rejected_without_writes(self):
        self.output.mkdir()
        sentinel = self.output / 'sentinel'
        sentinel.write_bytes(b'unchanged')
        with self.assertRaises(ValueError):
            h.inventory(self.root, [], self.output)
        self.assertEqual(sentinel.read_bytes(), b'unchanged')
        with self.assertRaises(ValueError):
            h.inventory(self.root, [self.root], self.base / 'other')
        with self.assertRaises(ValueError):
            h.inventory(self.root, [], self.base)

    def test_output_inside_scan_is_skipped_and_inputs_unchanged(self):
        self.output = self.root / 'reports/new'
        before = {p: h.digest(p) for p in self.root.rglob('*') if p.is_file()}
        h.inventory(self.root, [], self.output)
        self.assertEqual(len(self.read_result()['files']), 1)
        self.assertEqual(self.read_result()['excluded_entry_counts']['output'], 1)
        for path, digest in before.items():
            self.assertEqual(h.digest(path), digest)

    def test_extra_root_and_explicit_exclusion(self):
        extra = self.base / 'old-collection'
        extra.mkdir()
        (extra / 'captured.txt').write_text('source text')
        secret = self.put('unrecognized-private-test/records.jsonl')
        h.inventory(self.root, [extra], self.output, [secret.parent])
        result = self.read_result()
        self.assertEqual(len(result['files']), 2)
        self.assertEqual(len(result['roots']), 2)
        self.assertEqual(result['files'][-1]['root_index'], 1)
        self.assertFalse(result['external_history_complete'])

    def test_symlinks_not_followed_or_allowed_as_output(self):
        target = self.base / 'external.txt'
        target.write_text('outside secret')
        link = self.root / 'linked.txt'
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest('symlink creation unavailable')
        h.inventory(self.root, [], self.output)
        self.assertEqual(len(self.read_result()['files']), 1)
        alias = self.base / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            h.inventory(self.root, [], alias / 'output')

    def test_opt_in_projection_strips_text_labels_query_and_nested_outputs(self):
        body = 'source-exact unicode: baha sa kalsada é'
        source = self.put('sources.jsonl', json.dumps({
            'source_id': 'captured-01', 'url': 'https://example.org/article?token=secret#private',
            'text': body, 'text_sha256': hashlib.sha256(body.encode()).hexdigest(),
            'title': 'never export title', 'entities': [{'text': 'never export label'}],
            'outputs': {'source_id': 'not-source', 'url': 'https://example.org/forbidden'},
            'captured_at': '2026-10-17T00:00:00Z', 'event_group': 'storm-year-01'}))
        h.inventory(self.root, [], self.output, metadata_files=[source])
        result = self.read_result()
        encoded = json.dumps(result)
        for secret in [body, 'never export', '?token', '#private', '/forbidden']:
            self.assertNotIn(secret, encoded)
        row = result['source_metadata'][0]['source']
        self.assertTrue(row['recorded_text_hash_matches'])
        self.assertEqual(row['url_without_query_fragment'], 'https://example.org/article')
        self.assertEqual(row['event_group'], 'storm-year-01')

    def test_no_source_decoding_without_explicit_opt_in(self):
        self.put('sources.jsonl', 'not valid JSON')
        with patch.object(h, 'metadata_records', side_effect=AssertionError('must not decode')):
            result = h.inventory(self.root, [], self.output)
        self.assertEqual(result['source_metadata_records'], 0)
        self.assertEqual(result['errors'], 0)

    def test_forbidden_source_metadata_rejected_before_output(self):
        path = self.put('heldout-selection-v1/sources.jsonl', '{}')
        with self.assertRaises(ValueError):
            h.inventory(self.root, [], self.output, metadata_files=[path])
        self.assertFalse(self.output.exists())

    def test_bad_metadata_and_unreadable_input_report_incomplete(self):
        source = self.put('sources.jsonl', 'invalid JSON')
        result = h.inventory(self.root, [], self.output, metadata_files=[source])
        self.assertGreater(result['errors'], 0)
        self.assertFalse(result['complete_for_named_readable_scope'])
        self.assertFalse(self.read_result()['external_history_complete'])

    def test_file_mutation_is_not_a_success(self):
        source = self.put('body.txt', 'before')
        original = h.digest
        def mutate(path):
            value = original(path)
            if path == source:
                path.write_text('after is longer')
            return value
        with patch.object(h, 'digest', mutate):
            result = h.inventory(self.root, [], self.output)
        self.assertFalse(result['complete_for_named_readable_scope'])
        self.assertEqual(result['errors'], 1)

    def test_url_credentials_and_non_scalar_group_are_not_exported(self):
        self.assertIsNone(h.safe_source_metadata({'source_id': 's', 'url': 'https://u:p@example.org/'}))
        row = h.safe_source_metadata({'source_id': 's', 'url': 'https://example.org/',
            'event_group': ['unexpected'], 'published_at': 'arbitrary secret', 'text_sha256': 'wrong'})
        self.assertEqual(set(row), {'source_id', 'url_without_query_fragment'})

    def test_windows_reparse_directory_is_pruned_without_reading(self):
        self.put('junction/contents.json', 'do not read')
        original = h.is_link
        with patch.object(h, 'is_link', lambda p: p.name == 'junction' or original(p)):
            h.inventory(self.root, [], self.output)
        result = self.read_result()
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['excluded_entry_counts']['link_or_reparse'], 1)

    def test_unreadable_file_is_explicit_and_incomplete(self):
        source = self.put('unreadable.txt')
        original = h.digest
        def deny(path):
            if path == source:
                raise PermissionError('never print contents')
            return original(path)
        with patch.object(h, 'digest', deny):
            result = h.inventory(self.root, [], self.output)
        self.assertEqual(result['errors'], 1)
        self.assertFalse(result['complete_for_named_readable_scope'])
        self.assertNotIn('never print contents', json.dumps(self.read_result()))


if __name__ == '__main__':
    unittest.main()
