"""Opt-in export of the admitted cohort with its qualified model tokenizer."""
from __future__ import annotations

from collections import Counter
import os
from pathlib import Path
import re
import subprocess
import sys

from . import corpus_tokenizer_qualification as q
from .annotation.schema import AnnotationRecord, PLACE_LABELS
from .evaluation.contract import evaluation_contract
from .qualified_export_worker import signature
from .sources import json_bytes, read_jsonl

SCHEMA = 'lanes-qualified-location-export-v1'
PAYLOAD_FILES = frozenset({'train.spacy', 'dev.spacy', 'test.spacy', 'tokenizer.bin'})


def new_output(root: Path, output: Path) -> Path:
    absolute = output.absolute()
    artifacts = (root / 'backend/training/flood_ner/artifacts').resolve()
    q.require(absolute.resolve().is_relative_to(artifacts) and not absolute.exists(),
              'export destination must be new and under ignored artifacts')
    for path in (absolute, *absolute.parents):
        q.require(not path.is_symlink() and not getattr(path, 'is_junction', lambda: False)(),
                  'symlink/junction export destination refused')
        if path == artifacts:
            break
    ignored = subprocess.run(['git', 'check-ignore', '-q', '--', str(absolute)],
                             cwd=root, capture_output=True)
    q.require(ignored.returncode == 0, 'export destination must be ignored by Git')
    return absolute.resolve()


def passed_package(qualification: Path, root: Path):
    package = q.bound_manifest(qualification / 'manifest.json')
    q.require(package.get('schema_version') == 'lanes-corpus-tokenizer-package-v1'
              and package.get('state') == 'passed' and package.get('tokenizer_qualified') is True
              and package.get('exports') == 0 and package.get('training_performed') is False,
              'passing tokenizer-only qualification package required')
    required = {'qualification.json', 'evaluation-contract.json', 'comparison.json', 'tokens.json',
                'candidate.tokenizer.bin', 'native.tokenizer.bin', 'corpus-v3.tokenizer.bin'}
    q.require(required <= package['files'].keys(), 'incomplete qualification package')
    report = q.read(qualification / 'qualification.json')
    bindings = report.get('input_bindings', {})
    q.require(set(bindings) == {'cohort', 'context', 'admission_package', 'admission_ledger',
                               'model_manifest', 'tokenizer_manifest'}
              and package.get('input_bindings') == bindings, 'qualification input bindings differ')
    paths = {name: q.verified_reference(value, root) for name, value in bindings.items()}
    q.require(report.get('schema_version') == 'lanes-corpus-tokenizer-qualification-v1'
              and report.get('state') == 'passed' and report.get('candidate') == q.TOKENIZER_NAME
              and report.get('serialization_reload_verified') is True
              and report.get('model_predictions_performed') is False
              and report.get('training_performed') is False and report.get('exports') == 0
              and report.get('records') == 400 and report.get('contextual_pairs') == 40
              and report.get('location_spans') == 1465 and report.get('negative_passages') == 48
              and report.get('constructed_cases') == 48 and report.get('constructed_controls') == 56,
              'complete passing corpus qualification required')
    for name, sha in report.get('implementation_sha256', {}).items():
        q.require(name in {'corpus_tokenizer_qualification.py', 'corpus_tokenizer_worker.py'}
                  and q.digest(Path(__file__).with_name(name)) == sha, 'qualification implementation changed')
    q.require(set(report.get('implementation_sha256', {})) ==
              {'corpus_tokenizer_qualification.py', 'corpus_tokenizer_worker.py'},
              'qualification implementation identities required')
    expected_contract = evaluation_contract(bindings,
        {'name': q.TOKENIZER_NAME, 'sha256': report['candidate_sha256'],
         'vocabulary_binding': bindings['model_manifest'], 'qualified': True},
        {'state': 'passed', 'report': {'path': 'qualification.json',
                                     'sha256': q.digest(qualification / 'qualification.json')}})
    q.require(json_bytes(q.read(qualification / 'evaluation-contract.json')) == json_bytes(expected_contract),
              'frozen evaluation contract differs from qualified inputs/protocol')
    return report, paths


def export_records(records, candidate_cases, frozen_cases):
    """Validate export policy and build passage-only requests plus metadata."""
    q.require(records and len(records) == len({r.record_id for r in records}), 'duplicate/empty export membership')
    expected = {r['case_id'].removeprefix('location:'): r for r in candidate_cases
                if r['case_id'].startswith('location:')}
    frozen = {r['record_id']: r for r in frozen_cases if r['kind'] == 'location'}
    q.require(len(expected) == len(records) and set(expected) == set(frozen) == {r.record_id for r in records},
              'qualified location memberships differ')
    rows, metadata = [], []
    for r in sorted(records, key=lambda r: r.record_id):
        q.require(r.annotation_profile == 'location-only-v1' and not r.facts and not r.relations
                  and r.complete and r.review_status == 'accepted' and r.reviewer and r.reviewer.strip()
                  and r.teacher and r.teacher.strip() and r.quality == 'silver',
                  'complete accepted silver location profile required')
        s = r.source
        q.require(s.origin == 'captured_original' and s.admission_status == 'training_admitted'
                  and s.reuse_status == 'allowed' and q.SCOPE in s.reuse_terms,
                  'scoped private academic admission required')
        q.require(r.split in q.TARGETS and r.passage_language in q.TARGETS[r.split]
                  and s.event_group and s.syndication_group
                  and not any(v.casefold().startswith(('provisional:', 'review-needed:', 'unresolved:'))
                              for v in (s.article_group, s.event_group, s.syndication_group)),
                  'frozen reviewed groups/partition required')
        q.require(r.split == frozen[r.record_id]['split']
                  and r.passage_language == frozen[r.record_id]['language'],
                  'frozen partition/language membership changed')
        entities = [{'start': e.start, 'end': e.end, 'label': e.label} for e in r.entities]
        q.require(all(e['label'] in PLACE_LABELS for e in entities), 'out-of-profile export label')
        qualified = expected[r.record_id]
        truth = [{'start': e['start'], 'end': e['end'], 'label': e['label'], 'aligned': True}
                 for e in entities]
        q.require(r.text_sha256 == qualified['text_sha256']
                  and json_bytes(qualified['reference_alignment']) == json_bytes(truth),
                  'qualified text/entity identities differ')
        q.validate_tokens(qualified['tokens'], r.text)
        rows.append({'record_id': r.record_id, 'split': r.split, 'language': r.passage_language,
                     'text': r.text, 'text_sha256': r.text_sha256,
                     'entities': entities, 'tokens': qualified['tokens']})
        metadata.append({'record_id': r.record_id, 'split': r.split, 'language': r.passage_language,
                         'source_id': s.source_id, 'capture_version': s.capture_version,
                         'source_sha256': s.text_sha256, 'passage_sha256': r.text_sha256,
                         'passage_start': r.passage_start, 'passage_end': r.passage_end,
                         'article_group': s.article_group, 'event_group': s.event_group,
                         'syndication_group': s.syndication_group,
                         'annotation_revision': r.annotation_revision, 'quality': r.quality,
                         'annotation_profile': r.annotation_profile, 'teacher': r.teacher,
                         'reviewer': r.reviewer, 'review_status': r.review_status,
                         'entity_count': len(entities)})
    return rows, metadata


def validate_worker(result, rows, output):
    q.require(result.get('schema_version') == 'lanes-qualified-export-worker-v1'
              and result.get('operation') == 'export_qualified_location_corpus'
              and re.fullmatch(r'3\.11\.\d+', str(result.get('python_version')))
              and result.get('spacy_version') == '3.7.5'
              and result.get('pipeline_components_loaded') == []
              and result.get('model_weights_loaded') is False
              and result.get('model_predictions_performed') is False
              and result.get('training_performed') is False
              and result.get('serialization_reload_verified') is True, 'invalid isolated serialization result')
    q.require(result.get('request_records_sha256') == signature(rows)
              and result.get('records') == 400 and result.get('location_spans') == 1465
              and result.get('negative_passages') == 48
              and result.get('counts') == {'train': 280, 'dev': 60, 'test': 60}
              and result.get('languages') == {'english': 200, 'taglish': 200},
              'serialized cohort counts/memberships differ')
    q.require(set(result.get('files', {})) == PAYLOAD_FILES, 'exact training payload required')
    for name, sha in result['files'].items():
        q.require(q.digest(output / name) == sha, 'serialized file hash differs')


def export_qualified_corpus(python: Path, qualification: Path, output: Path, root: Path):
    root = root.resolve()
    output = new_output(root, output)
    qualification = qualification.resolve()
    artifacts = root / 'backend/training/flood_ner/artifacts'
    q.require(qualification.is_relative_to(artifacts) and qualification.is_dir(),
              'existing ignored qualification directory required')
    interpreter = python.resolve()
    q.require(interpreter.is_file() and interpreter.is_relative_to(artifacts)
              and interpreter != Path(sys.executable).resolve(), 'existing isolated research interpreter required')
    try:
        report, paths = passed_package(qualification, root)
        q.require(q.digest(interpreter) == report['research_interpreter_sha256'],
                  'research interpreter differs from qualification')
        cases, constructed, bindings = q.inputs(paths['cohort'].parent, paths['context'].parent,
                                                paths['admission_package'], root)
        q.require(bindings == {k: report['input_bindings'][k] for k in bindings}, 'current admission differs')
        model, model_dir = q.verify_model(paths['model_manifest'], artifacts)
        tokenizer, candidate = q.verify_tokenizer(paths['tokenizer_manifest'], paths['model_manifest'], model)
        q.require(tokenizer['sha256'] == report['candidate_sha256']
                  == q.digest(qualification / 'candidate.tokenizer.bin'), 'qualified candidate bytes differ')
        payload = q.read(qualification / 'tokens.json')
        q.validate_payload(payload, cases, qualification, tokenizer)
        comparison = q.assess_payload(payload, cases, constructed)
        q.require(json_bytes(comparison) == json_bytes(q.read(qualification / 'comparison.json')),
                  'qualification comparison differs')
        chosen = comparison['candidate']
        q.require(not chosen['location_alignment_errors']
                  and not chosen['contextual_location_alignment_error_count']
                  and not chosen['constructed_alignment_error_count']
                  and not chosen['constructed_control_failures']
                  and chosen['constructed_controls_checked'] == 56, 'candidate qualification did not pass')
        records = read_jsonl(paths['cohort'].parent / 'grouped_annotations.jsonl', AnnotationRecord)
        rows, metadata = export_records(records, payload['runs']['candidate']['cases'], cases)
        q.require({s: dict(Counter(r['language'] for r in rows if r['split'] == s))
                   for s in q.TARGETS} == q.TARGETS, 'frozen language/partition quotas differ')
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('malformed qualified export inputs: ' + str(exc)) from exc
    qualification_sha = q.digest(qualification / 'manifest.json')
    output.mkdir(parents=True)
    status = {'schema_version': SCHEMA, 'state': 'failed', 'training_performed': False,
              'model_predictions_performed': False}
    try:
        request = {'operation': 'export_qualified_location_corpus', 'vocab_dir': str(model_dir / 'vocab'),
                   'candidate_tokenizer': str(candidate), 'candidate_sha256': tokenizer['sha256'],
                   'output': str(output), 'records': rows}
        request_path = output / 'request.json'
        request_path.write_bytes(json_bytes(request))
        env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH'}}
        env.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
                   OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
        worker = Path(__file__).with_name('qualified_export_worker.py')
        proc = subprocess.run([str(interpreter), '-B', '-I', '-X', 'utf8', str(worker), str(request_path)],
                              cwd=output, env=env, capture_output=True, timeout=300)
        (output / 'worker.stdout.log').write_bytes(proc.stdout)
        (output / 'worker.stderr.log').write_bytes(proc.stderr)
        q.require(proc.returncode == 0, 'isolated export worker failed; see retained worker.stderr.log')
        import json
        result = json.loads(proc.stdout.decode('utf-8'))
        validate_worker(result, rows, output)
        q.require(q.digest(output / 'tokenizer.bin') == tokenizer['sha256'], 'export tokenizer differs')
        # Revalidate mutable inputs/evidence after the subprocess as well.
        q.require(q.digest(qualification / 'manifest.json') == qualification_sha, 'qualification package changed')
        passed_package(qualification, root)
        q.inputs(paths['cohort'].parent, paths['context'].parent, paths['admission_package'], root)
        q.verify_model(paths['model_manifest'], artifacts)
        q.require(q.digest(candidate) == tokenizer['sha256']
                  and q.digest(interpreter) == report['research_interpreter_sha256'], 'export input changed')
        (output / 'provenance.json').write_bytes(json_bytes(metadata))
        status.update(state='passed', records=400, source_articles=138, contextual_pairs_referenced=40,
                      contextual_pairs_exported_as_samples=0, location_spans=1465, negative_passages=48,
                      counts=result['counts'], languages=result['languages'],
                      annotation_profile='location-only-v1', labels=sorted(PLACE_LABELS),
                      source_use_scope=q.SCOPE, independently_verified_gold=False,
                      tokenizer=q.TOKENIZER_NAME, tokenizer_sha256=tokenizer['sha256'],
                      serialization_excludes=['vocab'], vocabulary_binding=report['input_bindings']['model_manifest'],
                      input_bindings=report['input_bindings'],
                      qualification={'path': (qualification / 'manifest.json').relative_to(root).as_posix(),
                                     'sha256': qualification_sha},
                      evaluation_contract={'path': (qualification / 'evaluation-contract.json').relative_to(root).as_posix(),
                                           'sha256': q.digest(qualification / 'evaluation-contract.json')},
                      serialization_reload_verified=True, payload_files=result['files'],
                      research_interpreter_sha256=report['research_interpreter_sha256'],
                      implementation_sha256={p.name: q.digest(p) for p in [Path(__file__), worker]})
        status['files'] = {p.name: q.digest(p) for p in sorted(output.iterdir()) if p.is_file()}
        (output / 'manifest.json').write_bytes(json_bytes(status))
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as exc:
        if isinstance(exc, subprocess.TimeoutExpired):
            (output / 'worker.stdout.log').write_bytes(exc.stdout or b'')
            (output / 'worker.stderr.log').write_bytes(exc.stderr or b'')
        status.update(state='failed', error=str(exc))
        (output / 'failure.json').write_bytes(json_bytes(status))
        raise ValueError('qualified export failed; diagnostics retained in ' + str(output)) from exc
    return status
