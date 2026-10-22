"""Constructed validation-only metrics/inference tests; no real predictions."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from training.flood_ner.validation_comparison import score_spans, coarse, checked_predictions, selected_run, compare_validation
from training.flood_ner.validation_worker import infer_raw
from training.flood_ner.evaluation.contract import score_exact_spans


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.truth = {'a': [(0, 5, 'CITY')], 'b': [(1, 3, 'ROAD')], 'negative': []}
        self.pred = {'a': [(0, 5, 'CITY')], 'b': [(1, 3, 'LANDMARK')], 'negative': [(0, 1, 'ROAD')]}
        self.lang = {'a': 'english', 'b': 'taglish', 'negative': 'english'}

    def test_six_class_matches_original_frozen_scorer(self):
        result = score_spans(self.truth, self.pred, self.lang)
        self.assertEqual(result, score_exact_spans(self.truth, self.pred, self.lang))
        self.assertEqual((result['overall']['TP'], result['overall']['FP'], result['overall']['FN']), (1, 2, 1))
        self.assertIsNone(result['labels']['PROVINCE']['f1'])
        self.assertEqual(result['negative_passages']['overall']['rate'], 1)
        self.assertIsNone(result['negative_passages']['taglish']['rate'])

    def test_coarse_matching_separates_class_errors_and_preserves_adjacent_spans(self):
        result = score_spans(coarse(self.truth), coarse(self.pred), self.lang, frozenset({'LOC'}))
        self.assertEqual(result['overall']['TP'], 2)
        self.assertEqual(set(result['labels']), {'LOC'})
        self.assertEqual(coarse({'x': [(0, 2, 'ROAD'), (2, 4, 'CITY'), (0, 2, 'CITY')]}),
                         {'x': [(0, 2, 'LOC'), (2, 4, 'LOC')]})

    def test_duplicate_missing_moved_and_unsupported_spans_refused(self):
        for predictions in [dict(self.pred, a=[(0,5,'CITY')]*2), {'a': []},
                            dict(self.pred, a=[(False,5,'CITY')]), dict(self.pred, a=[(0,5,'LOC')])]:
            with self.subTest(predictions=predictions), self.assertRaises(ValueError):
                score_spans(self.truth, predictions, self.lang)

    def test_unicode_offsets_and_changed_text_bounds(self):
        rows = [{'record_id':'a', 'text':'Biñan'}]
        self.assertEqual(checked_predictions(rows, {'a':[(0,5,'CITY')]}, frozenset({'CITY'})), {'a':[(0,5,'CITY')]})
        for p in [{'a':[(0,6,'CITY')]}, {'a':[(0,5,'LOC')]}, {'other':[]}]:
            with self.assertRaises(ValueError): checked_predictions(rows, p, frozenset({'CITY'}))

    def test_raw_strings_only_and_native_loc_filter(self):
        seen = []
        def pipe(texts, batch_size):
            self.assertTrue(all(isinstance(t, str) for t in texts))
            seen.extend(texts)
            return [SimpleNamespace(text=t, ents=[SimpleNamespace(start_char=0,end_char=5,label_='LOC'),
                                                  SimpleNamespace(start_char=0,end_char=2,label_='ORG')]) for t in texts]
        out, diag = infer_raw(SimpleNamespace(pipe=pipe), [{'record_id':'a','text':'Biñan','entities':['must not enter inference']}], True)
        self.assertEqual(seen, ['Biñan'])
        self.assertEqual(out, {'a':[(0,5,'LOC')]})
        self.assertEqual(diag, {'ORG':1})

    def test_inference_omission_and_text_rewrite_fail(self):
        rows=[{'record_id':'a','text':'Biñan'}]
        for docs in [[],[SimpleNamespace(text='Binan',ents=[])]]:
            with self.assertRaises(ValueError): infer_raw(SimpleNamespace(pipe=lambda *a,**k:docs), rows, False)

    def test_failed_or_mismatched_selected_run_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/'run-status.json').write_text(json.dumps({'state':'failed'}))
            with self.assertRaises(ValueError): selected_run(p, 0)
            selection={'partition':'dev','tie_break':'earlier checkpoint step','score':0.5,'step':35}
            status={'state':'completed','training_completed':True,'exit_code':0,'seed':0,'test_predictions_performed':False,'selection':selection}
            (p/'run-status.json').write_text(json.dumps(status))
            (p/'selected-checkpoint/model').mkdir(parents=True)
            (p/'selected-checkpoint/model/meta.json').write_text('{}')
            (p/'selected-checkpoint/selection.json').write_text(json.dumps(selection))
            self.assertEqual(selected_run(p,0)['selection']['step'],35)
            with self.assertRaises(ValueError): selected_run(p,1)

    def test_comparison_refuses_existing_destination_before_input_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            out=root/'backend/training/flood_ner/artifacts/existing'
            out.mkdir(parents=True)
            with self.assertRaisesRegex(ValueError,'destination must be new'):
                compare_validation(root/'python',root/'prep',root/'runs',out,root)


if __name__ == '__main__': unittest.main()
