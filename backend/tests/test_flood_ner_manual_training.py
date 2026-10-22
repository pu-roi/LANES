"""Launcher safety tests. Never invoke real training or a GPU worker."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from training.flood_ner import manual_training as launcher


class LauncherTests(unittest.TestCase):
    def test_redirected_parent_streams_a_real_unicode_subprocess_without_training(self):
        real_popen = subprocess.Popen
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'backend').mkdir()
            env = root / 'backend/.env'
            env.write_text('CONSTRUCTED_TEST_FIXTURE=1\n', encoding='utf-8')
            output = root / 'seed-2'
            plan = {'seed': 2, 'output': str(output), 'python': sys.executable}
            # This child emits console symbols and synthetic checkpoint metadata.
            # It imports only the standard library; no spaCy/GPU code is run.
            code = ("from pathlib import Path; import json; "
                    "print('\\u2139 constructed worker', flush=True); "
                    "p=Path('selected-checkpoint'); (p/'model').mkdir(parents=True); "
                    "(p/'model/meta.json').write_text('{}'); "
                    "(p/'selection.json').write_text(json.dumps({'partition':'dev','score':0.5,'step':35}))")
            def constructed_child(args, **kwargs):
                return real_popen([sys.executable, '-B', '-I', '-X', 'utf8', '-c', code], **kwargs)
            buffer = io.BytesIO()
            stream = io.TextIOWrapper(buffer, encoding='cp1252')
            with patch.object(launcher, 'ROOT', root), patch.object(launcher, 'validate_inputs', return_value=plan), \
                    patch.object(launcher.subprocess, 'Popen', side_effect=constructed_child), patch('sys.stdout', stream):
                # Recovery/trial runners call launch directly, bypassing main.
                self.assertEqual(launcher.launch(plan, validator=lambda: None), 0)
                stream.flush()
                captured = buffer.getvalue().decode('utf-8')
            self.assertIn('\u2139 constructed worker', captured)
            self.assertIn('\u2139 constructed worker', (output/'training.log').read_text(encoding='utf-8'))
            self.assertEqual(json.loads((output/'run-status.json').read_text())['state'], 'completed')
            self.assertEqual(env.read_text(encoding='utf-8'), 'CONSTRUCTED_TEST_FIXTURE=1\n')

    def test_worker_console_symbols_survive_a_legacy_redirected_stdout(self):
        buffer = io.BytesIO()
        stream = io.TextIOWrapper(buffer, encoding='cp1252')
        with patch('sys.stdout', stream), patch.object(launcher, 'worker', side_effect=lambda path: print('\u2139 GPU ready')):
            self.assertEqual(launcher.main(['--worker', 'constructed-request.json']), 0)
            stream.flush()
            data = buffer.getvalue()
        self.assertIn('\u2139 GPU ready', data.decode('utf-8'))

    def test_robustness_seed_checks_do_not_launch(self):
        for seed in (1, 2):
            with self.subTest(seed=seed), patch.object(launcher, 'validate_inputs', return_value={}) as validate, \
                    patch.object(launcher, 'launch') as launch:
                self.assertEqual(launcher.main(['--seed', str(seed)]), 0)
                validate.assert_called_once_with(seed=seed)
                launch.assert_not_called()

    def test_explicit_robustness_start_passes_the_selected_seed(self):
        for seed in (1, 2):
            plan = {'operation': 'train_seed_' + str(seed), 'seed': seed}
            with self.subTest(seed=seed), patch.object(launcher, 'validate_inputs', return_value=plan), \
                    patch.object(launcher, 'launch', return_value=0) as launch:
                self.assertEqual(launcher.main(['--seed', str(seed), '--start-training']), 0)
                launch.assert_called_once_with(plan)

    def test_nonfrozen_seed_refused(self):
        for seed in (True, -1, 3):
            with self.subTest(seed=seed), self.assertRaisesRegex(ValueError, 'frozen seed'):
                launcher.validate_inputs(seed=seed)

    def test_default_checks_without_launching(self):
        with patch.object(launcher, 'validate_inputs', return_value={}) as validate, \
                patch.object(launcher, 'launch') as launch:
            self.assertEqual(launcher.main([]), 0)
            validate.assert_called_once_with()
            launch.assert_not_called()

    def test_explicit_start_is_required(self):
        plan = {'operation': 'train_seed_0'}
        with patch.object(launcher, 'validate_inputs', return_value=plan), \
                patch.object(launcher, 'launch', return_value=0) as launch:
            self.assertEqual(launcher.main(['--start-training']), 0)
            launch.assert_called_once_with(plan)

    def test_validation_failure_never_starts_training(self):
        with patch.object(launcher, 'validate_inputs', side_effect=ValueError('changed input')), \
                patch.object(launcher, 'launch') as launch:
            self.assertEqual(launcher.main(['--start-training']), 1)
            launch.assert_not_called()

    def fixture(self, root: Path) -> Path:
        prep = root / 'preparation'
        prep.mkdir()
        (prep / 'train-seed-0.cfg').write_text('frozen', encoding='utf-8')
        manifest = {'schema_version': 'lanes-experiment-preparation-v1', 'state': 'passed',
                    'initialization_only': True, 'primary_seed': 0, 'robustness_seeds': [1, 2],
                    'files': {'train-seed-0.cfg': launcher.digest(prep / 'train-seed-0.cfg')},
                    'implementation_sha256': {'experiment_registry.py': '0' * 64}}
        (prep / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        report = root / 'docs/evaluations/flood-ner-experiment-preparation-20261016/verification.json'
        report.parent.mkdir(parents=True)
        report.write_text(json.dumps({'manifest_sha256': launcher.digest(prep / 'manifest.json')}), encoding='utf-8')
        return prep

    def test_changed_preparation_identity_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prep = self.fixture(root)
            with (prep / 'manifest.json').open('a') as stream:
                stream.write(' ')
            with self.assertRaisesRegex(ValueError, 'preparation identity changed'):
                launcher.validate_inputs(root, prep)

    def test_changed_config_or_implementation_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prep = self.fixture(root)
            with self.assertRaisesRegex(ValueError, 'prepared implementation changed'):
                launcher.validate_inputs(root, prep)
            (prep / 'train-seed-0.cfg').write_text('modified', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                launcher.validate_inputs(root, prep)


if __name__ == '__main__':
    unittest.main()
