"""Self-contained synthetic export safeguards; no private research data needed."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import spacy
from spacy.tokens import DocBin

from training.flood_ner.annotation.schema import AnnotationRecord, text_hash
from training.flood_ner.evaluation.contract import evaluation_contract
from training.flood_ner.export import export_corpus, TOKENIZER_NAME
from training.flood_ner import qualified_export as e
from training.flood_ner import qualified_export_worker as w


def synthetic_record():
    # Policy fixture only; it is never passed to the full 400-record exporter.
    text = 'Biñan\u2028has flooding.\nNo inferred location.'
    return AnnotationRecord.model_validate({
        'record_id': 'synthetic', 'annotation_profile': 'location-only-v1',
        'passage_language': 'english', 'source': {
            'source_id': 'synthetic', 'url': 'https://example.org/synthetic',
            'publisher': 'Synthetic test fixture', 'text': text, 'text_sha256': text_hash(text),
            'capture_version': 'synthetic-v1', 'article_group': 'synthetic-article',
            'event_group': 'synthetic-event', 'syndication_group': 'synthetic-syndication',
            'reuse_status': 'allowed', 'admission_status': 'training_admitted',
            'reuse_terms': e.q.SCOPE, 'extraction_method': 'synthetic unit test'},
        'text': text, 'text_sha256': text_hash(text), 'passage_start': 0, 'passage_end': len(text),
        'entities': [{'id': 'place', 'start': 0, 'end': 5, 'text': 'Biñan', 'label': 'CITY'}],
        'annotation_revision': 'synthetic-v1', 'quality': 'silver', 'teacher': 'synthetic teacher',
        'reviewer': 'synthetic reviewer', 'review_status': 'accepted', 'complete': True, 'split': 'train'})


class RecordPolicyTests(unittest.TestCase):
    def setUp(self):
        self.record = synthetic_record()
        nlp = spacy.blank('xx')
        self.cases = [{'case_id': 'location:synthetic', 'text_sha256': self.record.text_sha256,
                       'tokens': w.tokens(nlp(self.record.text)),
                       'reference_alignment': [{'start': 0, 'end': 5, 'label': 'CITY', 'aligned': True}]}]
        self.frozen = [{'record_id': 'synthetic', 'kind': 'location', 'split': 'train', 'language': 'english'}]

    def test_passage_only_request_and_metadata_without_article_body(self):
        rows, metadata = e.export_records([self.record], self.cases, self.frozen)
        self.assertEqual(rows[0]['text'], self.record.text)
        self.assertNotIn('source', rows[0])
        self.assertNotIn('text', metadata[0])
        self.assertEqual(metadata[0]['teacher'], 'synthetic teacher')
        self.assertEqual(metadata[0]['source_sha256'], self.record.source.text_sha256)

    def test_policy_refuses_unadmitted_unreviewed_or_wrong_profile(self):
        mutations = [
            lambda r: setattr(r.source, 'admission_status', 'research_only'),
            lambda r: setattr(r.source, 'reuse_status', 'unknown'),
            lambda r: setattr(r.source, 'reuse_terms', 'different use'),
            lambda r: setattr(r.source, 'origin', 'constructed_fixture'),
            lambda r: setattr(r.source, 'event_group', 'unresolved:storm'),
            lambda r: setattr(r, 'annotation_profile', 'context-rich-v1'),
            lambda r: setattr(r, 'teacher', None),
            lambda r: setattr(r, 'review_status', 'draft'),
            lambda r: setattr(r, 'complete', False),
            lambda r: setattr(r.entities[0], 'label', 'TIME'),
        ]
        for change in mutations:
            with self.subTest(change=change):
                record = self.record.model_copy(deep=True)
                change(record)
                with self.assertRaises(ValueError):
                    e.export_records([record], self.cases, self.frozen)

    def test_duplicate_missing_or_moved_memberships_refused(self):
        with self.assertRaises(ValueError):
            e.export_records([self.record, self.record], self.cases, self.frozen)
        with self.assertRaises(ValueError):
            e.export_records([self.record], [], self.frozen)
        for attr, value in [('split', 'test'), ('passage_language', 'taglish')]:
            with self.subTest(attr=attr):
                record = self.record.model_copy(deep=True)
                setattr(record, attr, value)
                with self.assertRaises(ValueError):
                    e.export_records([record], self.cases, self.frozen)

    def test_qualified_span_and_token_changes_refused(self):
        for field in ['span', 'tokens', 'hash']:
            cases = deepcopy(self.cases)
            if field == 'span':
                cases[0]['reference_alignment'][0]['end'] = 4
            elif field == 'tokens':
                cases[0]['tokens'][0]['text'] = 'changed'
            else:
                cases[0]['text_sha256'] = '0' * 64
            with self.subTest(field=field), self.assertRaises(ValueError):
                e.export_records([self.record], cases, self.frozen)

    def test_legacy_export_default_and_research_only_refusal_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'legacy'
            result = export_corpus([self.record], out, annotation_profile='location-only-v1')
            self.assertEqual(result['tokenizer'], TOKENIZER_NAME)
            self.assertEqual(result['counts'], {'train': 1, 'dev': 0, 'test': 0})
            self.record.source.admission_status = 'research_only'
            with self.assertRaises(ValueError):
                export_corpus([self.record], Path(tmp) / 'forbidden', annotation_profile='location-only-v1')


class SerializationTests(unittest.TestCase):
    def setUp(self):
        self.nlp = spacy.blank('xx')
        self.data = self.nlp.tokenizer.to_bytes(exclude=['vocab'])
        self.rows = []
        for split, text, entities in [
            ('train', 'Biñan\u2028CITY—-Purok\r\n', [{'start': 0, 'end': 5, 'label': 'CITY'}]),
            ('dev', 'Main Road floods.', [{'start': 0, 'end': 9, 'label': 'ROAD'}]),
            ('test', 'No named location here.', []),
        ]:
            self.rows.append({'record_id': split, 'split': split, 'language': 'english',
                              'text': text, 'text_sha256': text_hash(text),
                              'entities': entities, 'tokens': w.tokens(self.nlp(text))})

    def test_docbin_reload_unicode_negatives_and_deterministic_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / 'first', Path(tmp) / 'second'
            first.mkdir()
            second.mkdir()
            result = w.write_docbins(self.rows, self.nlp.tokenizer, self.data, first)
            replay = w.write_docbins(list(reversed(self.rows)), self.nlp.tokenizer, self.data, second)
            self.assertEqual(result['files'], replay['files'])
            self.assertTrue(result['serialization_reload_verified'])
            self.assertEqual(result['negative_passages'], 1)
            self.assertEqual(result['counts'], {'train': 1, 'dev': 1, 'test': 1})
            for row in self.rows:
                docs = list(DocBin().from_disk(first / (row['split'] + '.spacy')).get_docs(self.nlp.vocab))
                self.assertEqual(docs[0].text, row['text'])
                self.assertEqual(docs[0].user_data['record_id'], row['record_id'])
                self.assertEqual([(x.start_char, x.end_char, x.label_) for x in docs[0].ents],
                                 [(x['start'], x['end'], x['label']) for x in row['entities']])
            with self.assertRaises(ValueError):
                w.write_docbins(self.rows, self.nlp.tokenizer, self.data, first)

    def test_invalid_offsets_labels_or_tokens_never_write_payload(self):
        for mutation in ['offset', 'bool', 'label', 'token', 'hash', 'duplicate']:
            rows = deepcopy(self.rows)
            if mutation == 'offset':
                rows[0]['entities'][0]['end'] = 4
            elif mutation == 'bool':
                rows[0]['entities'][0]['start'] = False
            elif mutation == 'label':
                rows[0]['entities'][0]['label'] = 'DEPTH'
            elif mutation == 'token':
                rows[0]['tokens'][0]['text'] = 'changed'
            elif mutation == 'hash':
                rows[0]['text_sha256'] = '0' * 64
            else:
                rows.append(rows[0])
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(ValueError):
                    w.write_docbins(rows, self.nlp.tokenizer, self.data, Path(tmp))
                self.assertFalse(list(Path(tmp).iterdir()))


class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / 'qualification'
        self.folder.mkdir()
        names = ['cohort', 'context', 'admission_package', 'admission_ledger', 'model_manifest', 'tokenizer_manifest']
        bindings = {}
        for name in names:
            p = self.root / (name + '.json')
            p.write_bytes(b'{}')
            bindings[name] = {'path': p.name, 'sha256': e.q.digest(p)}
        report = {'schema_version': 'lanes-corpus-tokenizer-qualification-v1', 'state': 'passed',
                  'input_bindings': bindings, 'candidate': e.q.TOKENIZER_NAME,
                  'candidate_sha256': hashlib.sha256(b'fixture').hexdigest(),
                  'records': 400, 'contextual_pairs': 40, 'location_spans': 1465, 'negative_passages': 48,
                  'constructed_cases': 48, 'constructed_controls': 56, 'serialization_reload_verified': True,
                  'model_predictions_performed': False, 'training_performed': False, 'exports': 0,
                  'implementation_sha256': {n: e.q.digest(Path(e.q.__file__).with_name(n))
                      for n in ['corpus_tokenizer_qualification.py', 'corpus_tokenizer_worker.py']}}
        (self.folder / 'qualification.json').write_bytes(e.q.json_bytes(report))
        contract = evaluation_contract(bindings,
            {'name': e.q.TOKENIZER_NAME, 'sha256': report['candidate_sha256'],
             'vocabulary_binding': bindings['model_manifest'], 'qualified': True},
            {'state': 'passed', 'report': {'path': 'qualification.json',
                                         'sha256': e.q.digest(self.folder / 'qualification.json')}})
        (self.folder / 'evaluation-contract.json').write_bytes(e.q.json_bytes(contract))
        for name in ['tokens.json', 'comparison.json', 'candidate.tokenizer.bin',
                     'native.tokenizer.bin', 'corpus-v3.tokenizer.bin']:
            (self.folder / name).write_bytes(b'fixture')
        self.package = {'schema_version': 'lanes-corpus-tokenizer-package-v1', 'state': 'passed',
                        'tokenizer_qualified': True, 'input_bindings': bindings,
                        'exports': 0, 'training_performed': False}
        self.rebind()

    def rebind(self):
        self.package['files'] = {p.name: e.q.digest(p) for p in self.folder.iterdir()
                                 if p.name != 'manifest.json'}
        (self.folder / 'manifest.json').write_bytes(e.q.json_bytes(self.package))

    def test_bound_passing_package_and_failed_or_stale_package(self):
        report, paths = e.passed_package(self.folder, self.root)
        self.assertEqual(report['state'], 'passed')
        self.assertEqual(len(paths), 6)
        self.package['state'] = 'failed'
        self.rebind()
        with self.assertRaises(ValueError):
            e.passed_package(self.folder, self.root)
        self.package['state'] = 'passed'
        self.rebind()
        (self.root / 'cohort.json').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            e.passed_package(self.folder, self.root)

    def test_corrupted_member_missing_member_or_changed_contract(self):
        p = self.folder / 'tokens.json'
        p.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            e.passed_package(self.folder, self.root)
        p.unlink()
        self.rebind()
        with self.assertRaises(ValueError):
            e.passed_package(self.folder, self.root)
        p.write_bytes(b'fixture')
        contract = e.q.read(self.folder / 'evaluation-contract.json')
        contract['model_selection']['partition'] = 'test'
        (self.folder / 'evaluation-contract.json').write_bytes(e.q.json_bytes(contract))
        self.rebind()
        with self.assertRaises(ValueError):
            e.passed_package(self.folder, self.root)

    def test_claimed_pass_with_prediction_or_incomplete_report_refused(self):
        report = e.q.read(self.folder / 'qualification.json')
        report['model_predictions_performed'] = True
        (self.folder / 'qualification.json').write_bytes(e.q.json_bytes(report))
        self.rebind()
        with self.assertRaises(ValueError):
            e.passed_package(self.folder, self.root)

    def test_new_output_refuses_existing_external_or_unignored_path(self):
        artifacts = self.root / 'backend/training/flood_ner/artifacts'
        artifacts.mkdir(parents=True)
        existing = artifacts / 'existing'
        existing.mkdir()
        with self.assertRaises(ValueError):
            e.new_output(self.root, existing)
        with self.assertRaises(ValueError):
            e.new_output(self.root, self.root / 'outside')
        with patch.object(e.subprocess, 'run', return_value=SimpleNamespace(returncode=1)):
            with self.assertRaises(ValueError):
                e.new_output(self.root, artifacts / 'not-ignored')
        with patch.object(e.subprocess, 'run', return_value=SimpleNamespace(returncode=0)):
            self.assertEqual(e.new_output(self.root, artifacts / 'new'), artifacts / 'new')


class CliTests(unittest.TestCase):
    def test_new_command_and_legacy_tokenizer_choices(self):
        backend = Path(__file__).resolve().parents[1]
        for command, required in [
            (['export-qualified-corpus', '--help'], ['--qualification', '--python', '--output']),
            (['export', '--help'], ['lanes.xx.address-v2', 'lanes.xx.address-v3', '--profile']),
        ]:
            with self.subTest(command=command):
                p = subprocess.run([sys.executable, '-B', '-m', 'training.flood_ner', *command],
                                   cwd=backend, capture_output=True, text=True)
                self.assertEqual(p.returncode, 0, p.stderr)
                for value in required:
                    self.assertIn(value, p.stdout)


if __name__ == '__main__':
    unittest.main()
