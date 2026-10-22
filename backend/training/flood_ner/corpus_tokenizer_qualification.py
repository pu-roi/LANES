"""Admitted-corpus boundary qualification; no predictions, export or training."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from .annotation.schema import AnnotationRecord, PLACE_LABELS
from .cohort import _groups, TARGETS
from .contextual_pilot import ContextReview, validate_contextual_pilot
from .evaluation.contract import evaluation_contract
from .export import CANDIDATE_TOKENIZER_NAME
from .model_tokenizer import TOKENIZER_NAME
from .preflight import verify_model, MODEL_REVISION
from .qualification import load_frozen_cohort
from .sources import json_bytes, read_jsonl
from .tokenizer_qualification import load_cases, assess
from .use_bundle import verified_reference, verify_directory

SCOPE = 'private_owner_only_academic_training_evaluation'
CONSTRUCTED_CASES = Path(__file__).with_name('configs') / 'tokenizer_qualification_cases.jsonl'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def bound_manifest(path: Path) -> dict:
    value = read(path)
    require(isinstance(value, dict) and isinstance(value.get('files'), dict) and bool(value['files']), 'nonempty hash-bound manifest required')
    for name, sha in value['files'].items():
        require(isinstance(name, str) and isinstance(sha, str) and re.fullmatch('[a-f0-9]{64}', sha), 'valid manifest file identity required')
        target = (path.parent / name).resolve()
        require(target.is_relative_to(path.parent.resolve()) and target.is_file() and digest(target) == sha, 'manifest file missing, unsafe or hash mismatch: ' + name)
    return value


def bound_member(path: Path, package: dict, package_path: Path):
    path = path.resolve()
    require(path.is_relative_to(package_path.parent.resolve()), 'input outside admission package')
    name = path.relative_to(package_path.parent.resolve()).as_posix()
    require(package['files'].get(name) == digest(path), 'input not bound by admission package')


def membership(records):
    return [{'record_id': r.record_id, 'source_version': r.source.capture_version, 'source_sha256': r.source.text_sha256,
        'start': r.passage_start, 'end': r.passage_end, 'passage_sha256': r.text_sha256,
        'language': r.passage_language, 'split': r.split} for r in sorted(records, key=lambda r: r.record_id)]


def validate_admission(ledger: dict, rows: list[AnnotationRecord], contexts: list[AnnotationRecord], index: dict, root: Path):
    require(ledger.get('schema_version') == 'lanes-private-academic-admission-v1'
        and ledger.get('scope') == SCOPE and ledger.get('admission_applied') is True, 'scoped private academic admission required')
    require(type(ledger.get('training_admitted')) is int and ledger['training_admitted'] == len(rows) == 400
        and type(ledger.get('source_articles')) is int and ledger['source_articles'] == 138
        and type(ledger.get('sample_memberships')) is int and ledger['sample_memberships'] == 400, 'admission totals mismatch')
    require(all(ledger.get(k) is False for k in ('publisher_permission_claimed', 'legal_approval_claimed', 'dataset_license_granted', 'canonical_desktop_v2'))
        and ledger.get('desktop_predecessor_unreconciled') is True, 'unsupported permission/reconciliation claim')
    require(json_bytes(ledger.get('unchanged_nonacademic_outcomes')) == json_bytes(index.get('unchanged_nonacademic_outcomes'))
        and len(ledger['unchanged_nonacademic_outcomes']) == 12, 'nonacademic outcomes changed')
    entries = ledger.get('articles', [])
    require(len(entries) == len({v['source_id'] for v in entries}) == 138, '138 unique article admissions required')
    old = {v['source_id']: v for v in index['articles']}
    selected = {r.source.source_id for r in rows}
    require(selected == {v['source_id'] for v in entries} == set(old), 'admission/source identities differ')
    require(Counter(v['decision'] for v in entries) == Counter(adopt_private_academic_basis=69,
        prior_desktop_reported_adoption=68, prior_local_adoption=1), 'decision provenance differs')
    seen = []
    for entry in entries:
        sid = entry['source_id']
        chosen = [r for r in rows if r.source.source_id == sid]
        require(entry['scope'] == SCOPE and entry['permission_claimed'] is False and entry['admission_applied'] is True, 'article scope/claims mismatch')
        require(entry['decision'] == old[sid]['decision'] and entry['evidence'] == old[sid]['evidence'], 'article decision/evidence changed')
        require(entry['memberships'] == old[sid]['memberships'] == membership(chosen)
            and entry['selection_sha256'] == old[sid]['selection_sha256'] == hashlib.sha256(json_bytes(entry['memberships'])).hexdigest(), 'selected article scope mismatch')
        verified_reference(entry['evidence'], root)
        verified_reference(entry['provenance_reference'], root)
        require(entry['assessor']['kind'] == 'ai' and entry['assessor']['capacity'] == 'acting_under_explicit_researcher_delegation'
            and entry['applied_at'] == ledger['provenance']['applied_at'], 'actual AI admission provenance required')
        require(type(entry['samples']) is int and entry['samples'] == len(chosen), 'article sample count mismatch')
        for row in chosen + [r for r in contexts if r.source.source_id == sid]:
            require(row.source.capture_version == entry['capture_version'] and row.source.text_sha256 == entry['source_sha256']
                and row.source.url == entry['url'], 'admitted capture/source identity mismatch')
            require(row.source.admission_status == entry['admission_status'] == 'training_admitted'
                and row.source.reuse_status == entry['reuse_status'] == 'allowed'
                and row.source.reuse_terms == entry['reuse_terms'] and SCOPE in entry['reuse_terms'], 'source policy metadata mismatch')
            require(row.complete and row.review_status == 'accepted' and row.quality == 'silver', 'accepted complete silver annotations required')
        seen.extend(v['record_id'] for v in entry['memberships'])
    require(len(seen) == len(set(seen)) == 400, '400 distinct article memberships required')
    require({s: dict(Counter(r.passage_language for r in rows if r.split == s)) for s in TARGETS} == TARGETS, 'frozen language/split totals differ')


def inputs(cohort: Path, context: Path, admission_manifest: Path, root: Path):
    package = bound_manifest(admission_manifest)
    require(package.get('schema_version') == 'lanes-private-academic-admission-package-v1', 'private admission package required')
    for path in [cohort / 'partition_manifest.json', context / 'manifest.json']:
        bound_member(path, package, admission_manifest)
    rows, nlp, manifest = load_frozen_cohort(cohort)
    require(manifest.get('tokenizer') == CANDIDATE_TOKENIZER_NAME and manifest.get('source_admission_scope') == SCOPE, 'saved corpus-v3 and scoped admission required')
    context_manifest = verify_directory(context, 'manifest.json')
    require(context_manifest['location_manifest_sha256'] == digest(cohort / 'partition_manifest.json'), 'context/cohort binding mismatch')
    contexts = read_jsonl(context / 'context_annotations.jsonl', AnnotationRecord)
    reviews = [ContextReview.model_validate(v) for v in read(context / 'category_reviews.json')]
    require(validate_contextual_pilot(rows, contexts, reviews, nlp)['complete'], 'context pairing/category validation failed')
    ledger_path = (cohort / manifest['admission_ledger']['path']).resolve()
    bound_member(ledger_path, package, admission_manifest)
    require(digest(ledger_path) == manifest['admission_ledger']['sha256'], 'admission ledger binding mismatch')
    ledger = read(ledger_path)
    for reference in ledger['input_bindings'].values(): verified_reference(reference, root)
    index = read(verified_reference(ledger['input_bindings']['source_use_index'], root))
    validate_admission(ledger, rows, contexts, index, root)
    require(sum(len(r.entities) for r in rows) == 1465 and sum(not r.entities for r in rows) == 48, 'frozen annotation totals differ')
    def ref(path): return {'path': path.resolve().relative_to(root.resolve()).as_posix(), 'sha256': digest(path)}
    bindings = {'cohort': ref(cohort / 'partition_manifest.json'), 'context': ref(context / 'manifest.json'),
        'admission_package': ref(admission_manifest), 'admission_ledger': ref(ledger_path)}
    cases = []
    for kind, records in [('location', rows), ('context', contexts)]:
        cases += [{'case_id': kind + ':' + r.record_id, 'record_id': r.record_id, 'kind': kind,
            'text': r.text, 'text_sha256': r.text_sha256, 'split': r.split, 'language': r.passage_language,
            'entities': [e.model_dump(mode='json') for e in r.entities]} for r in records]
    constructed = load_cases(CONSTRUCTED_CASES)
    cases += [{'case_id': 'constructed:' + c.case_id, 'kind': 'constructed', 'text': c.text,
        'text_sha256': c.text_sha256, 'entities': [e.model_dump(mode='json') for e in c.expected_places]} for c in constructed]
    return cases, constructed, bindings


def verify_tokenizer(manifest_path: Path, model_manifest: Path, model: dict):
    manifest = read(manifest_path)
    require(isinstance(manifest, dict), 'tokenizer manifest must be an object')
    require(manifest.get('schema_version') == 'lanes-calamancy-tokenizer-v1' and manifest.get('name') == TOKENIZER_NAME
        and manifest.get('qualification_state') == 'passed' and manifest.get('model_revision') == MODEL_REVISION
        and manifest.get('model_manifest_sha256') == digest(model_manifest)
        and manifest.get('serialization_excludes') == ['vocab'], 'qualified pinned candidate manifest required')
    name = manifest.get('tokenizer_file')
    require(isinstance(name, str) and Path(name).name == name and '/' not in name and '\\' not in name, 'local candidate tokenizer filename required')
    path = manifest_path.parent / name
    require(path.is_file() and digest(path) == manifest.get('sha256'), 'candidate tokenizer bytes/hash mismatch')
    require(manifest.get('vocabulary_files') == [f for f in model['files'] if f['path'].startswith('vocab/')], 'candidate vocabulary binding mismatch')
    require(manifest.get('cases_sha256') == digest(CONSTRUCTED_CASES), 'constructed qualification cases changed')
    return manifest, path


def validate_tokens(tokens: list, text: str):
    require(isinstance(tokens, list), 'token list required')
    cursor = 0
    for token in tokens:
        require(isinstance(token, dict) and set(token) == {'start', 'end', 'text', 'whitespace'}, 'exact token offset/text/whitespace fields required')
        start, end = token['start'], token['end']
        require(type(start) is int and type(end) is int and start == cursor and start < end <= len(text), 'ordered exact Unicode token offsets required')
        require(isinstance(token['text'], str) and text[start:end] == token['text']
            and isinstance(token['whitespace'], str) and (not token['whitespace'] or token['whitespace'].isspace()), 'token text/whitespace mismatch')
        cursor = end + len(token['whitespace'])
        require(text[end:cursor] == token['whitespace'], 'token whitespace/source mismatch')
    require(cursor == len(text), 'worker omitted source characters')


def alignment(tokens, start, end):
    return any(t['start'] == start for t in tokens) and any(t['end'] == end for t in tokens)


def validate_payload(payload: dict, cases: list, output: Path, tokenizer: dict):
    require(isinstance(payload, dict) and set(payload) == {'schema_version', 'operation', 'python_version',
        'spacy_version', 'pipeline_components_loaded', 'model_predictions_performed', 'model_weights_loaded', 'runs'},
        'exact tokenizer-only worker result object required')
    require(payload.get('schema_version') == 'lanes-corpus-tokenizer-worker-v1' and payload.get('operation') == 'tokenize_only'
        and re.fullmatch(r'3\.11\.\d+', str(payload.get('python_version'))) and payload.get('spacy_version') == '3.7.5', 'isolated worker identity mismatch')
    require(isinstance(payload.get('runs'), dict), 'worker runs must be an object')
    require(payload.get('pipeline_components_loaded') == [] and payload.get('model_predictions_performed') is False
        and payload.get('model_weights_loaded') is False and set(payload.get('runs', {})) == {'native', 'candidate', 'corpus-v3'}, 'tokenizer-only result required')
    expected = {c['case_id']: c for c in cases}
    for mode, run in payload['runs'].items():
        require(isinstance(run, dict) and set(run) == {'roundtrip_identical', 'tokenizer_sha256', 'cases'}, 'exact tokenizer run object required')
        require(run.get('roundtrip_identical') is True and digest(output / (mode + '.tokenizer.bin')) == run.get('tokenizer_sha256'), 'saved/reloaded tokenizer hash mismatch')
        if mode == 'candidate': require(run['tokenizer_sha256'] == tokenizer['sha256'], 'candidate serialization identity changed')
        rows = run.get('cases', [])
        require(isinstance(rows, list) and all(isinstance(r, dict) and isinstance(r.get('case_id'), str) for r in rows), 'worker cases must be identified objects')
        require(len(rows) == len({r['case_id'] for r in rows}) == len(expected)
            and {r['case_id'] for r in rows} == set(expected), 'worker omitted/duplicated corpus cases')
        for row in rows:
            require(set(row) == {'case_id', 'text_sha256', 'tokens', 'reference_alignment'}, 'unexpected worker fields/predictions')
            case = expected[row['case_id']]
            require(row['text_sha256'] == case['text_sha256'], 'worker passage hash mismatch')
            validate_tokens(row['tokens'], case['text'])
            truth = [{'start': e['start'], 'end': e['end'], 'label': e['label'],
                'aligned': alignment(row['tokens'], e['start'], e['end'])} for e in case['entities']]
            require(json_bytes(row['reference_alignment']) == json_bytes(truth), 'false reference alignment claim')


def assess_payload(payload: dict, cases: list, constructed):
    lookup = {c['case_id']: c for c in cases}
    results = {}
    native = payload['runs']['native']['cases']
    def controls_rows(rows):
        return [{'case_id': r['case_id'].removeprefix('constructed:'), 'tokens': [
            {k: t[k] for k in ('start', 'end', 'text')} for t in r['tokens']]} for r in rows if lookup[r['case_id']]['kind'] == 'constructed']
    for mode, run in payload['runs'].items():
        errors, contextual = [], []
        for row in run['cases']:
            case = lookup[row['case_id']]
            for span in row['reference_alignment']:
                if not span['aligned']:
                    issue = {'case_id': row['case_id'], 'start': span['start'], 'end': span['end'], 'label': span['label']}
                    if case['kind'] == 'location': errors.append(issue)
                    elif case['kind'] == 'context': contextual.append(issue)
        constructed_report = assess(controls_rows(run['cases']), constructed, controls_rows(native))
        results[mode] = {'location_alignment_errors': errors, 'location_alignment_error_count': len(errors),
            'contextual_entity_boundary_diagnostics': contextual,
            'contextual_location_alignment_error_count': sum(v['label'] in PLACE_LABELS for v in contextual),
            'constructed_alignment_error_count': len(constructed_report['reference_alignment_errors']),
            'constructed_control_failures': constructed_report['control_failures'],
            'constructed_controls_checked': len(constructed_report['control_results'])}
    return results


def qualify_corpus_tokenizer(python: Path, model_manifest: Path, tokenizer_manifest: Path,
                            cohort: Path, context: Path, admission_manifest: Path, output: Path, root: Path) -> dict:
    root, output = root.resolve(), output.resolve()
    artifacts = root / 'backend/training/flood_ner/artifacts'
    require(output.is_relative_to(artifacts.resolve()) and not output.exists(), 'qualification destination must be new and under ignored artifacts')
    interpreter = python.absolute()
    require(interpreter.is_file() and interpreter.resolve().is_relative_to(artifacts.resolve())
        and interpreter.resolve() != Path(sys.executable).resolve(), 'explicit isolated research interpreter required')
    try:
        cases, constructed, bindings = inputs(cohort, context, admission_manifest, root)
        model, model_dir = verify_model(model_manifest, artifacts)
        tokenizer, candidate_path = verify_tokenizer(tokenizer_manifest, model_manifest, model)
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('malformed corpus qualification input: ' + str(exc)) from exc
    for key, path in [('model_manifest', model_manifest), ('tokenizer_manifest', tokenizer_manifest)]:
        bindings[key] = {'path': path.resolve().relative_to(root).as_posix(), 'sha256': digest(path)}
    report = {'schema_version': 'lanes-corpus-tokenizer-qualification-v1', 'state': 'blocked', 'input_bindings': bindings,
        'records': 400, 'location_spans': 1465, 'negative_passages': 48, 'contextual_pairs': 40,
        'constructed_cases': 48, 'constructed_controls': 56, 'research_interpreter_sha256': digest(interpreter),
        'candidate': tokenizer['name'], 'candidate_sha256': tokenizer['sha256'],
        'spacy_version_required': '3.7.5', 'research_python_required': '3.11', 'model_revision': MODEL_REVISION,
        'model_predictions_performed': False, 'exports': 0, 'training_performed': False,
        'attempts': 1, 'retry_policy': 'One unchanged-environment attempt after the recorded planning error; no automatic retries',
        'implementation_sha256': {name: digest(Path(__file__).with_name(name)) for name in ['corpus_tokenizer_qualification.py', 'corpus_tokenizer_worker.py']}}
    output.mkdir(parents=True)
    request = {'operation': 'tokenize_only', 'vocab_dir': str(model_dir / 'vocab'), 'native_tokenizer': str(model_dir / 'tokenizer'),
        'candidate_tokenizer': str(candidate_path.resolve()), 'corpus_tokenizer': str((cohort / 'tokenizer.bin').resolve()),
        'output': str(output), 'cases': cases}
    request_path = output / 'request.json'
    request_path.write_bytes(json_bytes(request))
    env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH'}}
    env.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
    try:
        proc = subprocess.run([str(interpreter), '-B', '-I', '-X', 'utf8', str(Path(__file__).with_name('corpus_tokenizer_worker.py')), str(request_path)],
            cwd=output, env=env, capture_output=True, timeout=300)
        (output / 'worker.stdout.log').write_bytes(proc.stdout)
        (output / 'worker.stderr.log').write_bytes(proc.stderr)
        if proc.returncode:
            error = proc.stderr.decode('utf-8', errors='replace')
            report.update(failure_stage='worker_subprocess', returncode=proc.returncode,
                error=error, application_control_4551='4551' in error)
        else:
            payload = json.loads(proc.stdout.decode('utf-8'))
            validate_payload(payload, cases, output, tokenizer)
            comparison = assess_payload(payload, cases, constructed)
            (output / 'tokens.json').write_bytes(json_bytes(payload))
            (output / 'comparison.json').write_bytes(json_bytes(comparison))
            candidate = comparison['candidate']
            passed = (not candidate['location_alignment_errors'] and not candidate['contextual_location_alignment_error_count']
                and not candidate['constructed_alignment_error_count'] and not candidate['constructed_control_failures'])
            require(not comparison['corpus-v3']['location_alignment_errors'], 'frozen corpus tokenizer no longer aligns its original labels')
            report.update(state='passed' if passed else 'failed', failure_stage=None if passed else 'boundary_qualification',
                alignment_error_counts={k: v['location_alignment_error_count'] for k, v in comparison.items()},
                candidate_control_failures=len(candidate['constructed_control_failures']),
                candidate_constructed_alignment_errors=candidate['constructed_alignment_error_count'],
                serialization_reload_verified=True)
    except subprocess.TimeoutExpired as exc:
        (output / 'worker.stdout.log').write_bytes(exc.stdout or b'')
        (output / 'worker.stderr.log').write_bytes(exc.stderr or b'')
        report.update(failure_stage='worker_timeout', error='Isolated tokenizer worker exceeded 300 seconds', application_control_4551=False)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        report.update(state='failed', failure_stage='execution_or_result_validation', error=str(exc))
    # Any post-run input mutation invalidates an apparent successful run too.
    try:
        verify_model(model_manifest, artifacts)
        for reference in bindings.values(): verified_reference(reference, root)
        bound_manifest(admission_manifest)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        report.update(state='failed', failure_stage='input_preservation', error=str(exc))
    report_path = output / 'qualification.json'
    report_path.write_bytes(json_bytes(report))
    contract = evaluation_contract(bindings,
        {'name': TOKENIZER_NAME, 'sha256': tokenizer['sha256'], 'vocabulary_binding': bindings['model_manifest'],
         'qualified': report['state'] == 'passed'},
        {'state': report['state'], 'report': {'path': 'qualification.json', 'sha256': digest(report_path)}})
    (output / 'evaluation-contract.json').write_bytes(json_bytes(contract))
    manifest = {'schema_version': 'lanes-corpus-tokenizer-package-v1', 'state': report['state'],
        'files': {p.name: digest(p) for p in sorted(output.iterdir()) if p.is_file()},
        'input_bindings': bindings, 'tokenizer_qualified': report['state'] == 'passed', 'exports': 0, 'training_performed': False}
    (output / 'manifest.json').write_bytes(json_bytes(manifest))
    return report
