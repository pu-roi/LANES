"""Synthetic mapping/configuration/checkpoint-policy tests; no real training."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import spacy

from training.flood_ner.rules_baseline import adapt_mentions, TYPE_TO_LABEL, specification
from training.flood_ner.experiment_worker import build_config, parameter_devices, POLICY
from training.flood_ner import experiment_registry as registry


class MappingTests(unittest.TestCase):
    def test_all_emitted_types_map_without_reference_labels(self):
        text = 'Biñan'
        for kind, label in TYPE_TO_LABEL.items():
            with self.subTest(kind=kind):
                result = adapt_mentions(text, [{'raw_place_name': text, 'char_start': 0, 'char_end': 5,
                                                'place_type': kind}])
                self.assertEqual(result, {'spans': [{'start': 0, 'end': 5, 'label': label}], 'diagnostics': []})
        result = adapt_mentions('Purok Singko', [{'raw_place_name': 'Purok Singko', 'char_start': 0,
                                                 'char_end': 12, 'place_type': 'landmark'}])
        self.assertEqual(result['spans'][0]['label'], 'LANDMARK')
        self.assertNotIn('LOCAL_AREA', TYPE_TO_LABEL.values())

    def test_invalid_raw_offsets_unknown_types_and_bool_are_diagnostic(self):
        for item in [
            {'char_start': False, 'char_end': 5, 'raw_place_name': 'Biñan', 'place_type': 'city'},
            {'char_start': 0, 'char_end': 5, 'raw_place_name': 'Binan', 'place_type': 'city'},
            {'char_start': 0, 'char_end': 5, 'raw_place_name': 'Biñan', 'place_type': 'unknown'},
            {'char_start': 0, 'char_end': 6, 'raw_place_name': 'Biñan', 'place_type': 'city'},
        ]:
            with self.subTest(item=item):
                result = adapt_mentions('Biñan', [item])
                self.assertFalse(result['spans'])
                self.assertEqual(len(result['diagnostics']), 1)

    def test_duplicate_and_overlapping_emissions_preserved_without_reference_resolution(self):
        mention = {'char_start': 0, 'char_end': 5, 'raw_place_name': 'Biñan', 'place_type': 'city'}
        other = {**mention, 'place_type': 'province'}
        result = adapt_mentions('Biñan', [mention, mention, other])
        self.assertEqual(len(result['spans']), 2)

    def test_rule_code_and_assets_are_hash_bound(self):
        root = Path(__file__).resolve().parents[2]
        value = specification(root)
        self.assertEqual(value['unavailable_output_labels'], ['LOCAL_AREA'])
        self.assertIn('backend/app/services/taglish_extraction_service.py', value['files'])
        self.assertIn('data/philippines_psgc_reference.csv', value['files'])
        self.assertTrue(all(len(h) == 64 for h in value['files'].values()))


class ConfigTests(unittest.TestCase):
    def test_pinned_cpu_upper_allowed_but_cpu_encoder_refused(self):
        class GPU: pass
        class CPU: pass
        class Node:
            param_names = ['W']
            def __init__(self, value): self.value = value
            def has_param(self, name): return True
            def get_param(self, name): return self.value
            def walk(self): return [self]
        encoder, upper = Node(GPU()), Node(CPU())
        model = SimpleNamespace(get_ref=lambda name: upper, walk=lambda: [encoder, upper])
        self.assertEqual(parameter_devices(model, GPU, CPU), {'gpu': 1, 'cpu_upper': 1})
        encoder.value = CPU()
        with self.assertRaises(ValueError): parameter_devices(model, GPU, CPU)
        encoder.value, upper.value = GPU(), GPU()
        with self.assertRaises(ValueError): parameter_devices(model, GPU, CPU)

    def test_seeds_callbacks_training_budget_and_test_exclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nlp = spacy.blank('tl')
            nlp.add_pipe('ner')
            nlp.config.to_disk(root / 'config.cfg')
            request = {'model_dir': str(root), 'model_manifest': str(root / 'model.json'),
                       'model_manifest_sha256': '0' * 64, 'export': str(root / 'export'),
                       'tokenizer_sha256': '1' * 64, 'future_training_root': str(root / 'future')}
            for seed in (0, 1, 2):
                with self.subTest(seed=seed):
                    cfg = build_config(request, seed)
                    self.assertEqual(cfg['system']['seed'], seed)
                    self.assertEqual(cfg['nlp']['pipeline'], ['ner'])
                    self.assertNotIn('test.spacy', cfg.to_str())
                    self.assertEqual(cfg['training']['score_weights']['ents_f'], 1.0)
                    self.assertEqual(cfg['training']['max_steps'], 1000)
                    self.assertEqual(cfg['training']['batcher']['size'], 8)
                    self.assertEqual(cfg['initialize']['after_init']['@callbacks'], 'lanes.restore_ner_encoder.v1')
                    self.assertEqual(cfg['training']['before_to_disk']['@callbacks'],
                                     'lanes.select_earliest_dev_checkpoint.v1')
            for bad in (True, -1, 3):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    build_config(request, bad)
        self.assertEqual(POLICY['eval_frequency'], 35)

    def test_before_initialize_registers_exactly_six_new_labels(self):
        nlp = spacy.blank('tl')
        nlp.add_pipe('ner')
        registry.location_labels()(nlp)
        self.assertEqual(set(nlp.get_pipe('ner').labels), set(registry.LABELS))
        nlp.get_pipe('ner').add_label('LOC')
        with self.assertRaises(ValueError):
            registry.location_labels()(nlp)


class SelectionTests(unittest.TestCase):
    def test_strict_dev_improvement_and_earliest_tie(self):
        self.assertTrue(registry.better_checkpoint(0.5, 0, float('-inf'), None))
        self.assertTrue(registry.better_checkpoint(0.6, 70, 0.5, 35))
        self.assertFalse(registry.better_checkpoint(0.5, 70, 0.5, 35))
        self.assertTrue(registry.better_checkpoint(0.5, 35, 0.5, 70))
        self.assertFalse(registry.better_checkpoint(0.4, 105, 0.5, 35))
        for score, step in [(float('nan'), 0), (True, 0), (1.1, 0), (0.5, -1)]:
            with self.subTest(score=score, step=step), self.assertRaises(ValueError):
                registry.better_checkpoint(score, step, 0, None)

    def test_selector_saves_improvements_only_and_refuses_existing_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = Path(tmp) / 'artifacts'
            target = artifacts / 'selected'
            saved = []
            def save(path):
                path.mkdir(parents=True, exist_ok=True)
                saved.append((nlp.meta['performance']['ents_f'], nlp.meta['lanes_training_step']))
            nlp = SimpleNamespace(meta={'performance': {'ents_f': 0.5}, 'lanes_training_step': 35},
                                  to_disk=save)
            with patch.object(registry, 'ARTIFACTS', artifacts):
                callback = registry.select_checkpoint(str(target))
                callback(nlp)
                nlp.meta['lanes_training_step'] = 70
                callback(nlp)
                nlp.meta['performance']['ents_f'] = 0.6
                nlp.meta['lanes_training_step'] = 105
                callback(nlp)
                self.assertEqual(saved, [(0.5, 35), (0.6, 105)])
                with self.assertRaises(ValueError):
                    registry.select_checkpoint(str(target))


if __name__ == '__main__':
    unittest.main()
