"""Constructed v19 qualification checks; no private corpus/model inputs."""
from pathlib import Path
import ast
import hashlib
import json
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner import v19_evaluation_qualification as q
from training.flood_ner import v19_development_diagnosis as d


@pytest.mark.parametrize('name', sorted(q.NEWLINE_PATHS))
def test_twelve_transport_paths_require_semantic_equivalence(name):
    lf = b'value = "fixture"\n' if name.endswith('.py') else b'a,b\n1,2\n'
    crlf = lf.replace(b'\n', b'\r\n')
    proof = q.newline_equivalence(name, crlf, lf)
    assert proof['original_sha256'] == hashlib.sha256(crlf).hexdigest()
    assert proof['actual_sha256'] == hashlib.sha256(lf).hexdigest()
    assert proof['method'].startswith('python_ast' if name.endswith('.py') else 'csv_parsed')
    with pytest.raises(ValueError, match='substantive'):
        q.newline_equivalence(name, crlf, lf.replace(b'fixture', b'changed') if name.endswith('.py') else b'a,b\n1,3\n')


def test_arbitrary_newline_exception_and_identical_bytes_rejected():
    with pytest.raises(ValueError, match='allowlisted'):
        q.newline_equivalence('unknown.py', b'x=1\r\n', b'x=1\n')
    with pytest.raises(ValueError, match='substantive'):
        q.newline_equivalence('backend/app/core/config.py', b'x=1\n', b'x=1\n')


def test_csv_quoted_embedded_newlines_are_compared_as_rows():
    proof = q.newline_equivalence('data/pasig_barangay_reference.csv', b'a,b\r\n"one\r\ntwo",3\r\n',
                                  b'a,b\n"one\ntwo",3\n')
    assert proof['method'] == 'csv_parsed_rows_universal_newlines'


def test_stale_receipt_rejected_before_any_import_or_corpus_read(tmp_path):
    path = tmp_path / 'receipt.json'; path.write_text('{}')
    with pytest.raises(ValueError, match='stale'):
        q.verify_receipt(tmp_path, path, '0' * 64)


def test_no_holdout_or_training_request_capability(tmp_path):
    with pytest.raises(ValueError, match='development-only'):
        d.verify_request(tmp_path, {'schema': 'holdout', 'development': '', 'handoff': '',
            'handoff_sha256': '', 'resources': '', 'bindings': [], 'implementation': []})
    with pytest.raises(ValueError, match='unexpected'):
        d.verify_request(tmp_path, {'start_training': True})


def test_stale_diagnosis_request_does_not_create_output(tmp_path):
    request = tmp_path / 'request.json'; request.write_text('{}')
    output = tmp_path / 'output'
    with pytest.raises(ValueError, match='stale'):
        d.run(tmp_path, request, '0' * 64, output)
    assert not output.exists()


def test_missing_source_bindings_rejected(tmp_path):
    with pytest.raises(ValueError, match='implementation'):
        d.verify_request(tmp_path, {'schema': 'lanes-v19-development-diagnosis-v1', 'development': '',
            'handoff': '', 'handoff_sha256': '', 'resources': '', 'bindings': [], 'implementation': []})


def test_empty_type_parameter_metadata_only_is_neutral():
    first = ast.parse('def probe(x):\n    return x + 1\n')
    second = ast.parse('def probe(x):\n    return x + 1\n')
    # Simulate the additional Python 3.12 field when this test runs on 3.11.
    second.body[0]._fields = (*[f for f in second.body[0]._fields if f != 'type_params'], 'type_params')
    second.body[0].type_params = []
    assert q.canonical_ast(first) == q.canonical_ast(second)
    second.body[0].type_params = [ast.Name(id='T', ctx=ast.Load())]
    assert q.canonical_ast(first) != q.canonical_ast(second)
    literal_tree = q.canonical_ast(ast.parse('x = (..., b"raw", 1j)'))
    assert json.loads(json.dumps(literal_tree)) == literal_tree


def test_real_python_311_312_proof_bytes_match():
    root = Path(__file__).resolve().parents[2]
    code = """import sys,json
sys.path.insert(0, 'backend')
from training.flood_ner.v19_evaluation_qualification import newline_equivalence
print(json.dumps(newline_equivalence('backend/app/core/config.py', b'def p(x):\\r\\n return x+1\\r\\n', b'def p(x):\\n return x+1\\n'),sort_keys=True))
"""
    outputs = []
    for interpreter in (root / 'backend/.venv/Scripts/python.exe', root /
                        'backend/training/flood_ner/artifacts/preflight-use-20261015/research-env/Scripts/python.exe'):
        result = subprocess.run([str(interpreter), '-I', '-B', '-c', code], cwd=root, capture_output=True, check=True)
        outputs.append(json.loads(result.stdout))
    assert outputs[0] == outputs[1]
