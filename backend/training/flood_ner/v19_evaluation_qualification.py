"""Exact, local qualification of the received v19 research implementation.

Newline equivalence is narrowly scoped to the twelve recorded transport
differences. It never changes files or replaces raw-byte bindings elsewhere.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
from pathlib import Path

from training.flood_ner.development_error_audit import bound, digest, read, require, safe_path

NEWLINE_PATHS = frozenset({
    'backend/app/core/config.py', 'backend/app/models/news_publication.py',
    'backend/app/models/report.py', 'backend/app/schemas/news_extraction.py',
    'backend/app/schemas/news_locality.py', 'backend/app/schemas/news_placement.py',
    'backend/app/services/flood_depth.py', 'backend/app/services/locality_number_service.py',
    'backend/app/services/news_evidence_policy.py', 'backend/app/services/pasig_historical_service.py',
    'data/flooded_areas_pasig_clean.csv', 'data/pasig_barangay_reference.csv',
})
ORIGINAL_HANDOFF = 'b3dd00e73d59aa11fdcdbf4a1c97c7e58abd7b30540521f2215e9c7435887367'


def canonical_ast(value):
    """Version-neutral syntax, excluding positions and empty 3.12 type_params.

    Nonempty type parameters remain substantive; Python 3.11 cannot parse that
    syntax. No literal, operator, identifier or executable statement is dropped.
    """
    if isinstance(value, ast.AST):
        return [type(value).__name__, [[key, canonical_ast(item)] for key, item in ast.iter_fields(value)
                if not (key == 'type_params' and item == [])]]
    if isinstance(value, list):
        return [canonical_ast(item) for item in value]
    if value is Ellipsis:
        return ['literal_ellipsis']
    if isinstance(value, bytes):
        return ['literal_bytes', value.hex()]
    if isinstance(value, complex):
        return ['literal_complex', repr(value)]
    return value


def newline_equivalence(name: str, original: bytes, actual: bytes) -> dict:
    require(name in NEWLINE_PATHS, 'newline exception is not allowlisted')
    normalize = lambda value: value.replace(b'\r\n', b'\n')
    require(original != actual and normalize(original) == normalize(actual),
            'substantive difference is not a newline exception')
    if name.endswith('.py'):
        parsed = [canonical_ast(ast.parse(b.decode('utf-8'))) for b in (original, actual)]
        method = 'python_ast_without_positions_runtime_neutral_v2'
    else:
        parsed = [list(csv.reader(io.StringIO(b.decode('utf-8'), newline=None))) for b in (original, actual)]
        method = 'csv_parsed_rows_universal_newlines'
    require(parsed[0] == parsed[1], 'parsed content differs')
    return {'path': name, 'original_sha256': hashlib.sha256(original).hexdigest(),
            'actual_sha256': hashlib.sha256(actual).hexdigest(), 'method': method,
            'equivalence_sha256': hashlib.sha256(json.dumps(parsed[0], ensure_ascii=False).encode()).hexdigest()}


def verify_receipt(root: Path, path: Path, expected_sha: str) -> dict:
    require(digest(path) == expected_sha, 'stale qualification receipt')
    receipt = read(path)
    require(set(receipt) == {'schema', 'original_handoff_sha256', 'scoped_manifest',
            'development_exclusions', 'partition_manifest', 'neural_runtime', 'rules_runtime',
            'implementation', 'newline_equivalence', 'rules_specification', 'protocol_sha256',
            'constructed_evidence', 'verified'}, 'qualification fields differ')
    require(receipt['schema'] == 'lanes-v19-evaluation-qualification-v1' and receipt['verified'] is True
            and receipt['original_handoff_sha256'] == ORIGINAL_HANDOFF, 'wrong qualification scope')
    for name in ('scoped_manifest', 'development_exclusions', 'partition_manifest', 'constructed_evidence'):
        bound(root, receipt[name])
    evidence = read(bound(root, receipt['constructed_evidence']))
    require(evidence.get('schema') == 'lanes-v19-constructed-qualification-v1'
            and evidence.get('state') == 'passed' and type(evidence.get('tests_passed')) is int
            and evidence['tests_passed'] > 0 and evidence.get('tests_failed') == 0
            and evidence.get('private_content_in_fixtures') is False,
            'passing constructed qualification evidence required')
    require(receipt['partition_manifest']['sha256'] ==
            '4be5213e0b4106d358505027af936bedd7f80b8151345e62362127fcb2a5f20e', 'partition lineage differs')
    for name, version in (('neural_runtime', '3.11.17'), ('rules_runtime', '3.12.14')):
        runtime = receipt[name]
        require(runtime['version'] == version and digest(Path(runtime['python'])) == runtime['sha256'],
                'qualified interpreter identity differs')
    require(receipt['neural_runtime']['spacy'] == '3.7.5', 'wrong neural runtime')
    require(receipt['implementation'], 'implementation evidence missing')
    for name, sha in receipt['implementation'].items():
        require(digest(safe_path(root, name)) == sha, 'qualified implementation changed')
    proofs = receipt['newline_equivalence']
    require(len(proofs) == 12 and {p['path'] for p in proofs} == NEWLINE_PATHS, 'twelve newline proofs required')
    for proof in proofs:
        actual = safe_path(root, proof['path']).read_bytes()
        # The authentic desktop hash must match this exact newline-only candidate.
        original = actual.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
        require(newline_equivalence(proof['path'], original, actual) == proof, 'newline proof changed')
        require(receipt['implementation'][proof['path']] == proof['actual_sha256'], 'unbound newline exception')
    from training.flood_ner.rules_baseline import specification
    require(specification(root) == receipt['rules_specification'], 'rules assets or transitive imports changed')
    return receipt
