"""Constructed-only held-out guards and scoring; no real model inference."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from training.flood_ner import heldout_test as h
from training.flood_ner.heldout_test_worker import validate_request
from training.flood_ner.validation_worker import infer_raw
from types import SimpleNamespace


def rows():
    return [{'record_id': f'r{i:02}', 'kind': 'location', 'split': 'test',
             'language': 'english' if i < 30 else 'taglish', 'text': 'Biñan',
             'text_sha256': hashlib.sha256('Biñan'.encode()).hexdigest(),
             'entities': [] if i == 59 else [{'start': 0, 'end': 5, 'label': 'CITY'}]} for i in range(60)]


def roster():
    return [{'family': f, 'seed': s, 'recipe': 'recovery' if f == 'original' and s == 2 else f}
            for f, s in h.ROSTER]


def guesses(cases):
    trained = {r['record_id']: [(e['start'], e['end'], e['label']) for e in r['entities']] for r in cases}
    return {**{f'{f}-seed-{s}': deepcopy(trained) for f, s in h.ROSTER},
            'rules': deepcopy(trained), 'native': h.coarse(trained)}


class HeldoutTests(unittest.TestCase):
    def test_fixed_roles_recovery_and_excluding_B(self):
        records = list(reversed(roster())) + [{'family': 'B', 'seed': 0, 'recipe': 'B'}]
        self.assertEqual([(v['family'], v['seed']) for v in h.fixed_roster(records)], list(h.ROSTER))
        for bad in [roster()[:-1], roster() + [roster()[0]],
                    [dict(v, seed=False) if v['seed'] == 0 else v for v in roster()],
                    [dict(v, recipe='original') if v['seed'] == 2 else v for v in roster()]]:
            with self.assertRaises(ValueError): h.fixed_roster(bad)

    def test_test_rows_exclude_training_validation_and_contexts(self):
        cases = rows()
        self.assertEqual(h.test_rows(cases + [{'record_id': 'train', 'kind': 'location', 'split': 'train'},
                                             {'record_id': 'dev', 'kind': 'location', 'split': 'dev'},
                                             {'record_id': 'ctx', 'kind': 'context', 'split': 'train'}]), cases)
        for extra in [dict(cases[0], split='train'), dict(cases[0], kind='context', split='train')]:
            with self.assertRaises(ValueError): h.test_rows(cases + [extra])

    def test_duplicate_moved_language_or_changed_unicode_inputs_refused(self):
        for field, value in [('record_id', 'r01'), ('split', 'dev'), ('kind', 'context'),
                             ('language', 'taglish'), ('text', 'Binan')]:
            cases = rows();cases[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): h.validate_rows(cases)

    def test_constructed_controls_have_no_record_id_and_are_not_memberships(self):
        controls = [{'kind': 'constructed', 'case_id': 'constructed:unicode-control', 'text': 'Biñan'}]
        self.assertEqual(h.test_rows(rows() + controls), rows())

    def test_invalid_label_offsets_and_duplicates_refused(self):
        for entities in [[{'start': 0, 'end': 6, 'label': 'CITY'}], [{'start': 0, 'end': 5, 'label': 'LOC'}],
                         [{'start': False, 'end': 5, 'label': 'CITY'}], rows()[0]['entities'] * 2]:
            cases = rows();cases[0]['entities'] = entities
            with self.assertRaises(ValueError): h.validate_rows(cases)

    def test_exact_coarse_errors_and_negative_false_positives(self):
        cases = rows();pred = guesses(cases)
        pred['original-seed-0']['r00'] = [(0, 5, 'ROAD')]
        pred['original-seed-0']['r59'] = [(0, 5, 'CITY')]
        metrics, errors = h.scored_results(cases, pred)
        strict = metrics['original-seed-0']['six_class']
        self.assertEqual((strict['overall']['TP'], strict['overall']['FP'], strict['overall']['FN']), (58, 2, 1))
        self.assertEqual(metrics['original-seed-0']['coarse_loc']['overall']['TP'], 59)
        self.assertEqual(strict['negative_passages']['overall']['false_positive_passages'], 1)
        self.assertIsNone(strict['negative_passages']['english']['rate'])
        self.assertEqual(errors['original-seed-0']['r00']['false_positives'], [(0, 5, 'ROAD')])
        self.assertEqual(metrics['rules']['unavailable_labels'], ['LOCAL_AREA'])
        self.assertNotIn('six_class', metrics['native'])
        self.assertNotIn('text', json.dumps(errors))

    def test_incomplete_systems_or_record_predictions_refused(self):
        for mutation in ('system', 'record', 'duplicate', 'native_duplicate'):
            cases = rows();pred = guesses(cases)
            if mutation == 'system': del pred['A-seed-2']
            elif mutation == 'record': del pred['original-seed-0']['r00']
            elif mutation == 'duplicate': pred['original-seed-0']['r00'] *= 2
            else: pred['native']['r00'] *= 2
            with self.assertRaises(ValueError): h.scored_results(cases, pred)

    def test_undefined_metrics_and_statistics_stay_null(self):
        cases = rows()
        for r in cases: r['entities'] = []
        metrics, _ = h.scored_results(cases, guesses(cases))
        self.assertIsNone(metrics['original-seed-0']['six_class']['overall']['f1'])
        self.assertIsNone(h.family_statistics(metrics)['A']['six_class']['mean'])

    def test_test_inference_receives_unicode_strings_not_reference_entities(self):
        seen = []
        def pipe(texts, batch_size):
            seen.extend(texts)
            self.assertTrue(all(type(v) is str for v in texts))
            return [SimpleNamespace(text=v, ents=[]) for v in texts]
        infer_raw(SimpleNamespace(pipe=pipe), rows(), False)
        self.assertEqual(seen, ['Biñan'] * 60)

    def test_exclusive_marker_refuses_repeat_even_with_different_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp);(p / 'manifest.json').write_text('{}')
            h.claim_attempt(p, p / 'one')
            before = (p / 'attempt.json').read_bytes()
            with self.assertRaises(FileExistsError): h.claim_attempt(p, p / 'two')
            self.assertEqual((p / 'attempt.json').read_bytes(), before)

    def test_existing_destination_refused_before_any_input_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = Path(tmp);out = r / 'backend/training/flood_ner/artifacts/existing';out.mkdir(parents=True)
            with patch.object(h, 'load_inputs') as load, self.assertRaisesRegex(ValueError, 'destination must be new'):
                h.freeze_test_experiment(r / 'prep', r / 'report', out, r)
            load.assert_not_called()
            with patch.object(h, 'verify_freeze') as load, self.assertRaisesRegex(ValueError, 'destination must be new'):
                h.evaluate_test(r / 'freeze', r / 'python', out, r)
            load.assert_not_called()

    def test_model_hash_or_file_set_changes_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp);(p / 'meta.json').write_text('{}')
            files = {'meta.json': h.digest(p / 'meta.json')};h.check_model(p, files)
            (p / 'meta.json').write_text('{"changed":true}')
            with self.assertRaises(ValueError): h.check_model(p, files)
            (p / 'meta.json').write_text('{}');(p / 'extra').write_text('extra')
            with self.assertRaises(ValueError): h.check_model(p, files)

    def test_changed_freeze_seal_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp);h.write(p / 'manifest.json', {'state': 'changed'})
            h.write(p / 'seal.json', {'manifest_sha256': '0' * 64})
            with patch.object(h, 'private_existing', return_value=p), self.assertRaisesRegex(ValueError, 'manifest changed'):
                h.verify_freeze(p, p)

    def test_worker_rejects_non_test_operation_before_gpu_imports(self):
        with self.assertRaisesRegex(ValueError, 'operation'): validate_request({'operation': 'validation_only'})

    def test_worker_binds_roster_rows_docbin_and_code_before_gpu_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp);(p / 'test.spacy').write_bytes(b'constructed');(p / 'registry.py').write_text('')
            (p / 'helper.py').write_text('constructed helper')
            cases = rows()
            state = {'runs': [], 'native_model': str(p), 'native_model_files': {},
                     'candidate_tokenizer_sha256': 'candidate', 'native_tokenizer_sha256': 'native',
                     'test_memberships': h.memberships(cases), 'evaluator_code': {str(p / 'helper.py'): h.digest(p / 'helper.py')},
                     'bindings': {'test_docbin': {'sha256': h.digest(p / 'test.spacy')}}}
            h.write(p / 'manifest.json', state)
            request = {k: state[k] for k in ('runs', 'native_model', 'native_model_files', 'candidate_tokenizer_sha256', 'native_tokenizer_sha256')}
            request.update(operation='heldout_test', rows=cases, freeze=str(p / 'manifest.json'),
                           freeze_sha256=h.digest(p / 'manifest.json'), test_docbin=str(p / 'test.spacy'),
                           test_docbin_sha256=h.digest(p / 'test.spacy'), registry=str(p / 'registry.py'), registry_sha256=h.digest(p / 'registry.py'))
            validate_request(request)
            for key, value in [('freeze_sha256', 'changed'), ('runs', [{'name': 'B'}]),
                               ('test_docbin_sha256', 'changed')]:
                bad = deepcopy(request);bad[key] = value
                with self.subTest(key=key), self.assertRaises(ValueError): validate_request(bad)
            bad = deepcopy(request);bad['rows'][0]['record_id'] = 'moved'
            with self.assertRaises(ValueError): validate_request(bad)
            bad = deepcopy(request);bad['rows'][0]['split'] = 'dev'
            with self.assertRaises(ValueError): validate_request(bad)
            (p / 'helper.py').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'evaluator bytes changed'): validate_request(request)

    def test_evaluation_failure_preserves_marker_logs_and_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = Path(tmp);freeze = r / 'freeze';freeze.mkdir()
            (freeze / 'manifest.json').write_text('{}')
            out = r / 'output';python = r / 'python'
            state = {'python': str(python), 'bindings': {'rules': {'path': 'rules.json'}}, 'runs': [],
                     'native_model': 'native', 'native_model_files': {}, 'native_tokenizer_sha256': 'native',
                     'candidate_tokenizer_sha256': 'candidate'}
            h.write(r / 'rules.json', {'frozen': 'rules'})
            inputs = {'rows': rows(), 'export': r, 'prep': {'implementation_sha256': {'experiment_registry.py': 'registry'}}}
            (r / 'test.spacy').write_bytes(b'constructed')
            result = SimpleNamespace(returncode=1, stdout=b'failed worker', stderr=b'constructed error')
            with patch('training.flood_ner.qualified_export.new_output', return_value=out), \
                 patch.object(h, 'verify_freeze', return_value=(state, inputs)), \
                 patch('training.flood_ner.rules_baseline.specification', return_value={'frozen': 'rules'}), \
                 patch('training.flood_ner.rules_baseline.predict_mentions', return_value={'spans': [], 'diagnostics': []}), \
                 patch.object(h.subprocess, 'run', return_value=result):
                with self.assertRaisesRegex(ValueError, 'do not retry automatically'):
                    h.evaluate_test(freeze, python, out, r)
            self.assertTrue((freeze / 'attempt.json').exists())
            self.assertEqual((out / 'worker.stderr.log').read_bytes(), b'constructed error')
            self.assertEqual(h.read(out / 'failure.json')['state'], 'failed')
            self.assertFalse((out / 'manifest.json').exists())


if __name__ == '__main__':
    unittest.main()
