"""Exercise actual Git checkout conversion for hash-bound NER source files."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('git'), 'Git is required for checkout verification')
class ResearchCheckoutBytesTests(unittest.TestCase):
    def test_checkout_matches_mixed_frozen_source_styles(self) -> None:
        source = 'VALUE = "Peña"\n'.encode('utf-8')
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder) / 'repo'
            checkout = Path(folder) / 'checkout'
            repo.mkdir()

            def git(*args: str) -> subprocess.CompletedProcess:
                return subprocess.run(['git', *args], cwd=repo, check=True,
                                      capture_output=True)

            git('init', '-q')
            git('config', 'core.autocrlf', 'true')
            git('config', 'core.safecrlf', 'false')
            (repo / '.gitattributes').write_bytes((ROOT / '.gitattributes').read_bytes())
            paths = ['backend/training/flood_ner/experiment_worker.py',
                     'backend/training/flood_ner/annotation/schema.py',
                     'backend/training/flood_ner/cli.py',
                     'backend/training/flood_ner/corpus_tokenizer_qualification.py',
                     'backend/training/flood_ner/corpus_tokenizer_worker.py',
                     'backend/training/flood_ner/evaluation/contract.py',
                     'backend/training/flood_ner/regularization_experiment_execution.py',
                     'backend/training/flood_ner/regularization_development_worker.py',
                     'backend/tests/test_flood_ner_regularization_execution.py',
                     'backend/tests/test_flood_ner_corrected_development_languages.py']
            # The evaluation contract now uses literal byte preservation. Only
            # these three historical source paths still request CRLF conversion.
            crlf_paths = set(paths[2:5])
            for name in paths:
                path = repo / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(source)
            git('add', '.gitattributes', *paths)
            for autocrlf in ('true', 'false'):
                git('config', 'core.autocrlf', autocrlf)
                destination = checkout / autocrlf
                git('checkout-index', '--all', '--prefix=' + destination.as_posix() + '/')
                for name in paths:
                    with self.subTest(path=name, autocrlf=autocrlf):
                        expected = source.replace(b'\n', b'\r\n') if name in crlf_paths else source
                        self.assertEqual((destination / name).read_bytes(), expected)


if __name__ == '__main__':
    unittest.main()
