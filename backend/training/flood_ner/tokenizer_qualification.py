"""Constructed-only comparison of native, adapted and corpus tokenizers."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Literal

from pydantic import Field

from .annotation.schema import Span, text_hash
from . import preflight
from .export import CANDIDATE_TOKENIZER_NAME, corpus_tokenizer
from .model_tokenizer import TOKENIZER_NAME, INFIX, PREFIX, SUFFIX
from .sources import json_bytes

ORIGINAL_CASES = Path(__file__).with_name('configs') / 'preflight_constructed_cases.jsonl'
ORIGINAL_CASES_SHA256 = '62f317b78101dd8abacf5c60155c05948b990cef79be803e71ecb4e1fc5ea1b9'
REQUIRED_TAGS = {'dash_combination', 'dateline', 'list_delimiter', 'unicode', 'whitespace',
                 'address_identifier', 'compound_address', 'clock_date_count', 'hyphenated_word'}


class TokenControl(Span):
    kind: Literal['token', 'boundaries', 'native_equivalent']


class BoundaryCase(preflight.ConstructedCase):
    token_controls: list[TokenControl] = Field(default_factory=list)


def load_cases(path: Path) -> list[BoundaryCase]:
    if hashlib.sha256(ORIGINAL_CASES.read_bytes()).hexdigest() != ORIGINAL_CASES_SHA256:
        raise ValueError('original constructed-case checkpoint hash mismatch')
    cases = [BoundaryCase.model_validate_json(line) for line in path.read_text(encoding='utf-8').split('\n') if line.strip()]
    if (len(cases) != 48 or len({c.case_id for c in cases}) != 48
            or len({c.text for c in cases}) != 48
            or any(sum(c.language == lang for c in cases) != 24 for lang in ('english', 'taglish'))):
        raise ValueError('qualification requires 48 distinct constructed cases, 24 per language')
    originals = preflight.load_cases(ORIGINAL_CASES)
    for original, current in zip(originals, cases[:24]):
        if current.model_dump(exclude={'token_controls'}) != original.model_dump() or current.token_controls:
            raise ValueError('original 24 constructed cases must be preserved unchanged and ordered')
    if not REQUIRED_TAGS <= {t for c in cases[24:] for t in c.tags}:
        raise ValueError('expanded boundary/control coverage missing')
    for case in cases:
        if case.text_sha256 != text_hash(case.text):
            raise ValueError('constructed text hash mismatch')
        end = 0
        for span in sorted(case.expected_places, key=lambda s: s.start):
            if not end <= span.start < span.end <= len(case.text) or case.text[span.start:span.end] != span.text:
                raise ValueError('malformed or overlapping place references')
            end = span.end
        for control in case.token_controls:
            if not 0 <= control.start < control.end <= len(case.text) or case.text[control.start:control.end] != control.text:
                raise ValueError('malformed token control')
        if case in cases[24:] and not case.token_controls:
            raise ValueError('each new constructed case needs explicit token controls')
    return cases


def aligned(tokens: list[dict], start: int, end: int) -> bool:
    return any(t['start'] == start for t in tokens) and any(t['end'] == end for t in tokens)


def validate_payload(payload: dict, cases: list[BoundaryCase], mode: str, output: Path) -> None:
    preflight.validate_result(payload, cases, case_count=48)
    resources = payload['resources']
    if (resources.get('measured_calls') != 480 or resources.get('batch_size') != 1 or resources.get('threads') != 2
            or payload.get('pipeline') != ['tok2vec', 'ner'] or payload.get('tokenizer_mode') != mode
            or payload.get('tokenizer_name') != ('calamancy-native' if mode == 'native' else TOKENIZER_NAME)
            or payload.get('roundtrip_identical') is not True):
        raise ValueError('worker measurement/tokenizer identity mismatch')
    tokenizer_file = output / f'{mode}.tokenizer.bin'
    if not tokenizer_file.is_file() or hashlib.sha256(tokenizer_file.read_bytes()).hexdigest() != payload.get('tokenizer_sha256'):
        raise ValueError('saved tokenizer hash mismatch')
    by_id = {c.case_id: c for c in cases}
    for row in payload['cases']:
        case = by_id[row['case_id']]
        cursor = 0
        for token in row['tokens']:
            if case.text[cursor:token['start']].strip():
                raise ValueError('worker omitted source characters between tokens')
            cursor = token['end']
        if case.text[cursor:].strip():
            raise ValueError('worker omitted source characters after tokens')
        for expected, actual in zip(case.expected_places, row['reference_alignment']):
            if type(actual.get('aligned')) is not bool or actual['aligned'] != aligned(row['tokens'], expected.start, expected.end):
                raise ValueError('false reference alignment claim')


def assess(rows: list[dict], cases: list[BoundaryCase], native_rows: list[dict]) -> dict:
    by_id = {r['case_id']: r for r in rows}
    native = {r['case_id']: r for r in native_rows}
    gaps = []; controls = []
    for case in cases:
        tokens = by_id[case.case_id]['tokens']
        for ref in case.expected_places:
            if not aligned(tokens, ref.start, ref.end):
                gaps.append({'case_id': case.case_id, 'start': ref.start, 'end': ref.end, 'label': ref.label})
        for control in case.token_controls:
            inside = [t for t in tokens if t['start'] < control.end and t['end'] > control.start]
            if control.kind == 'token':
                passed = len(inside) == 1 and inside[0]['start'] == control.start and inside[0]['end'] == control.end
            elif control.kind == 'boundaries':
                passed = aligned(tokens, control.start, control.end)
            else:
                before = [t for t in native[case.case_id]['tokens'] if t['start'] < control.end and t['end'] > control.start]
                passed = inside == before
            controls.append({'case_id': case.case_id, 'start': control.start, 'end': control.end, 'kind': control.kind, 'passed': passed})
    return {'reference_alignment_errors': gaps, 'control_results': controls,
            'control_failures': [c for c in controls if not c['passed']]}


def qualify_tokenizer(python: Path, model_manifest: Path, case_file: Path, output: Path, root: Path) -> dict:
    artifacts = (root / 'backend/training/flood_ner/artifacts').resolve()
    output = output.resolve(); interpreter = python.absolute()
    if not output.is_relative_to(artifacts) or output.exists():
        raise ValueError('qualification destination must be new and under ignored artifacts')
    if (not interpreter.resolve().is_relative_to(artifacts) or not interpreter.is_file()
            or interpreter.resolve() == Path(sys.executable).resolve()):
        raise ValueError('explicit isolated research interpreter required')
    cases = load_cases(case_file)
    manifest, directory = preflight.verify_model(model_manifest, artifacts)
    case_hash = hashlib.sha256(case_file.read_bytes()).hexdigest()
    manifest_hash = hashlib.sha256(model_manifest.read_bytes()).hexdigest()
    output.mkdir(parents=True)
    report = {'schema_version': 'lanes-tokenizer-qualification-v1', 'state': 'failed',
              'research_interpreter': str(interpreter), 'research_interpreter_sha256': hashlib.sha256(interpreter.read_bytes()).hexdigest(),
              'implementation_files': {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                       for name in ('model_tokenizer.py', 'tokenizer_worker.py', 'tokenizer_qualification.py', 'preflight.py')},
              'model_revision': manifest['revision'], 'model_manifest_sha256': manifest_hash,
              'cases_sha256': case_hash, 'candidate': TOKENIZER_NAME,
              'constructed_only': True, 'case_count': 48, 'languages': {'english': 24, 'taglish': 24},
              'news_samples_processed': 0, 'training_performed': False, 'training_admitted': 0,
              'production_qualified': False, 'six_class_accuracy_measured': False, 'runs': {}}
    env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH'}}
    env.update({'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'TOKENIZERS_PARALLELISM': 'false',
                'OMP_NUM_THREADS': '2', 'MKL_NUM_THREADS': '2'})
    payloads = {}
    try:
        for mode in ('native', 'candidate'):
            request = {'model_dir': str(directory), 'model_revision': manifest['revision'], 'mode': mode,
                       'tokenizer_file': str(output / f'{mode}.tokenizer.bin'),
                       'cases': [c.model_dump(mode='json') for c in cases]}
            request_path = output / f'{mode}.request.json'; request_path.write_bytes(json_bytes(request))
            proc = subprocess.run([str(interpreter), '-I', '-X', 'utf8', str(Path(__file__).with_name('tokenizer_worker.py')), str(request_path)],
                                  cwd=output, env=env, capture_output=True, timeout=600)
            (output / f'{mode}.stdout.log').write_bytes(proc.stdout)
            (output / f'{mode}.stderr.log').write_bytes(proc.stderr)
            if proc.returncode:
                raise ValueError(f'{mode} worker failed ({proc.returncode}): {proc.stderr.decode("utf-8", errors="replace")}')
            payload = json.loads(proc.stdout.decode('utf-8'))
            validate_payload(payload, cases, mode, output)
            payloads[mode] = payload
            (output / f'{mode}.predictions.json').write_bytes(json_bytes(payload))
            report['runs'][mode] = {'resources': payload['resources'], 'tokenizer_sha256': payload['tokenizer_sha256'],
                                     'roundtrip_identical': True, 'repeated_predictions_identical': True}
        # Blank corpus tokenizer comparison uses no model and never touches news text.
        nlp = corpus_tokenizer(CANDIDATE_TOKENIZER_NAME)
        rows = []
        for case in cases:
            doc = nlp.make_doc(case.text)
            if doc.text != case.text: raise ValueError('corpus tokenizer changed text')
            rows.append({'case_id': case.case_id, 'tokens': [{'start': t.idx, 'end': t.idx + len(t.text), 'text': t.text} for t in doc]})
        (output / 'corpus-v3.tokens.json').write_bytes(json_bytes(rows))
        comparison = {mode: assess(payloads[mode]['cases'], cases, payloads['native']['cases']) for mode in payloads}
        comparison[CANDIDATE_TOKENIZER_NAME] = assess(rows, cases, payloads['native']['cases'])
        native = {r['case_id']: r for r in payloads['native']['cases']}
        differences = [{'case_id': r['case_id'], 'tokens_changed': r['tokens'] != native[r['case_id']]['tokens'],
                        'entities_changed': r['entities'] != native[r['case_id']]['entities'],
                        'native_entities': native[r['case_id']]['entities'], 'candidate_entities': r['entities']}
                       for r in payloads['candidate']['cases']]
        (output / 'comparison.json').write_bytes(json_bytes({'tokenizers': comparison, 'prediction_differences': differences}))
        candidate = comparison['candidate']
        preflight.verify_model(model_manifest, artifacts)
        if (hashlib.sha256(case_file.read_bytes()).hexdigest() != case_hash
                or hashlib.sha256(model_manifest.read_bytes()).hexdigest() != manifest_hash):
            raise ValueError('case or model manifest changed during qualification')
        report.update({'state': 'passed' if not candidate['reference_alignment_errors'] and not candidate['control_failures'] else 'failed',
                       'reference_alignment_errors': {m: len(v['reference_alignment_errors']) for m, v in comparison.items()},
                       'candidate_control_failures': len(candidate['control_failures']),
                       'prediction_changes': sum(d['entities_changed'] for d in differences),
                       'tokenization_changes': sum(d['tokens_changed'] for d in differences)})
        tokenizer_manifest = {'schema_version': 'lanes-calamancy-tokenizer-v1', 'name': TOKENIZER_NAME,
                              'model_revision': manifest['revision'], 'model_manifest_sha256': hashlib.sha256(model_manifest.read_bytes()).hexdigest(),
                              'tokenizer_file': 'candidate.tokenizer.bin', 'sha256': payloads['candidate']['tokenizer_sha256'],
                              'serialization_excludes': ['vocab'], 'vocabulary_files': [f for f in manifest['files'] if f['path'].startswith('vocab/')],
                              'rules': {'infix': INFIX, 'prefix': PREFIX, 'suffix': SUFFIX},
                              'original_cases_sha256': hashlib.sha256(ORIGINAL_CASES.read_bytes()).hexdigest(),
                              'cases_sha256': report['cases_sha256'], 'research_candidate_only': True,
                              'qualification_state': report['state']}
        (output / 'tokenizer_manifest.json').write_bytes(json_bytes(tokenizer_manifest))
    except (OSError, subprocess.TimeoutExpired, ValueError, TypeError, KeyError) as exc:
        report['state'] = 'failed'
        report['error'] = str(exc)
        report['failure_stage'] = 'worker_timeout' if isinstance(exc, subprocess.TimeoutExpired) else 'execution_or_validation'
    report['files'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}
    (output / 'report.json').write_bytes(json_bytes(report))
    return report
