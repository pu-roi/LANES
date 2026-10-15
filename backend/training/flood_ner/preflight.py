"""Constructed-only model preflight through an isolated research interpreter."""
from __future__ import annotations

import hashlib
import json
import os
import math
from pathlib import Path, PurePosixPath
import subprocess
import sys
from typing import Literal

from pydantic import Field

from .annotation.schema import PLACE_LABELS, Span, StrictRecord, text_hash
from .sources import json_bytes

MODEL_REVISION = '51a40433059d8a2c25b98a48eca854f8789a491a'
PINNED_METADATA_HASHES = {
    'meta.json':'283a173d2dbf698a81c1832a1134b9ec5c6c872c74733df62937a6b89e20d1cd',
    'config.cfg':'e77d26602a84eb8e170e404a9f207f93be8fefd233760426a3d90ec6638e2f67',
    'README.md':'624959769997ae04286a21666ea9c274044064821e2ce66450af7fc0549683b5',
}


class ExpectedPlace(Span):
    label: Literal['ROAD', 'LANDMARK', 'LOCAL_AREA', 'BARANGAY', 'CITY', 'PROVINCE']


class ConstructedCase(StrictRecord):
    case_id: str = Field(min_length=1)
    origin: Literal['constructed_fixture']
    quality: Literal['constructed']
    language: Literal['english', 'taglish']
    text: str = Field(min_length=1)
    text_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    expected_places: list[ExpectedPlace] = Field(default_factory=list)
    tags: list[str] = Field(min_length=1)


def load_cases(path: Path) -> list[ConstructedCase]:
    cases = [ConstructedCase.model_validate_json(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(cases) != 24 or len({c.case_id for c in cases}) != 24 or any(sum(c.language == lang for c in cases) != 12 for lang in ('english','taglish')):
        raise ValueError('preflight requires 24 unique constructed cases, 12 English and 12 Taglish')
    for case in cases:
        if text_hash(case.text) != case.text_sha256:
            raise ValueError('constructed case text hash mismatch')
        end = 0
        for span in sorted(case.expected_places, key=lambda s: s.start):
            if not end <= span.start < span.end <= len(case.text) or case.text[span.start:span.end] != span.text:
                raise ValueError('malformed or overlapping constructed place reference')
            end = span.end
    if {p.label for c in cases for p in c.expected_places} != PLACE_LABELS:
        raise ValueError('constructed cases must exercise all six place classes')
    return cases


def verify_model(manifest_path: Path, artifacts: Path) -> tuple[dict, Path]:
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if (manifest.get('schema_version') != 'lanes-model-artifact-v1' or manifest.get('model') != 'tl_calamancy_md'
            or manifest.get('version') != '0.1.0' or manifest.get('revision') != MODEL_REVISION
            or manifest.get('license') != 'MIT' or manifest.get('download_complete') is not True):
        raise ValueError('complete approved pinned model manifest required')
    directory = Path(manifest['model_dir']).resolve()
    if not directory.is_relative_to(artifacts.resolve()) or not directory.is_dir():
        raise ValueError('model must remain inside ignored research artifacts')
    files = manifest.get('files')
    if not isinstance(files,list) or any(not isinstance(f,dict) for f in files):
        raise ValueError('model file hashes required')
    names = [f.get('path') for f in files]
    required = {'config.cfg','meta.json','tokenizer','ner/model','ner/moves','tok2vec/model','vocab/vectors','vocab/vectors.cfg','vocab/strings.json','README.md'}
    if any(not isinstance(n,str) for n in names) or len(set(names)) != len(names) or not required <= set(names):
        raise ValueError('model artifact file inventory incomplete or duplicated')
    for entry in files:
        name = PurePosixPath(entry['path'])
        target = (directory / str(name)).resolve()
        if name.is_absolute() or '..' in name.parts or not target.is_relative_to(directory) or not target.is_file():
            raise ValueError('unsafe/missing model artifact path')
        if hashlib.sha256(target.read_bytes()).hexdigest() != entry.get('sha256') or target.stat().st_size != entry.get('bytes'):
            raise ValueError('model artifact hash/size mismatch')
        if entry['path'] in PINNED_METADATA_HASHES and entry['sha256'] != PINNED_METADATA_HASHES[entry['path']]:
            raise ValueError('model metadata hash differs from pinned research evidence')
    if {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()} != set(names):
        raise ValueError('unmanifested model artifact files')
    meta = json.loads((directory/'meta.json').read_text(encoding='utf-8'))
    if meta.get('version') != '0.1.0' or meta.get('license') != 'MIT' or set(meta.get('labels',{}).get('ner',[])) != {'LOC','ORG','PER'}:
        raise ValueError('model metadata differs from approved identity')
    return manifest, directory


def validate_result(result: dict, cases: list[ConstructedCase]) -> None:
    if not isinstance(result,dict) or result.get('schema_version') != 'lanes-model-preflight-result-v1':
        raise ValueError('malformed worker output')
    if (not str(result.get('python_version','')).startswith('3.11.') or result.get('spacy_version') != '3.7.5'
            or result.get('model_revision') != MODEL_REVISION or result.get('model_version') != '0.1.0'
            or result.get('cpu_only') is not True or result.get('repeated_predictions_identical') is not True):
        raise ValueError('worker runtime/model/CPU identity mismatch')
    rows = result.get('cases')
    if not isinstance(rows,list) or any(not isinstance(r,dict) for r in rows) or len(rows) != 24 or len({r.get('case_id') for r in rows}) != 24:
        raise ValueError('worker case identity/count mismatch')
    by_id = {c.case_id:c for c in cases}
    for row in rows:
        case = by_id.get(row.get('case_id'))
        if case is None or row.get('text_sha256') != case.text_sha256:
            raise ValueError('worker case/source hash mismatch')
        tokens = row.get('tokens'); entities = row.get('entities'); alignment = row.get('reference_alignment')
        if (not isinstance(tokens,list) or any(not isinstance(t,dict) for t in tokens)
                or not isinstance(entities,list) or any(not isinstance(e,dict) for e in entities)
                or not isinstance(alignment,list) or len(alignment) != len(case.expected_places)):
            raise ValueError('worker token/entity/alignment arrays required')
        boundaries=set();end=0
        for token in tokens:
            a,z=token.get('start'),token.get('end')
            if type(a) is not int or type(z) is not int or not end <= a < z <= len(case.text) or token.get('text') != case.text[a:z]:
                raise ValueError('malformed worker token span')
            boundaries.add((a,z));end=z
        end=0
        for entity in entities:
            a,z=entity.get('start'),entity.get('end')
            if (type(a) is not int or type(z) is not int or not end <= a < z <= len(case.text)
                    or entity.get('text') != case.text[a:z] or entity.get('label') not in {'LOC','ORG','PER'}
                    or not any(t[0]==a for t in boundaries) or not any(t[1]==z for t in boundaries)):
                raise ValueError('malformed or unaligned worker entity span')
            end=z
        for expected, actual in zip(case.expected_places,alignment):
            supported=any(t[0]==expected.start for t in boundaries) and any(t[1]==expected.end for t in boundaries)
            if actual != {'start':expected.start,'end':expected.end,'label':expected.label,'aligned':supported}:
                raise ValueError('worker reference alignment mismatch')
    resources=result.get('resources',{})
    if not isinstance(resources,dict):raise ValueError('worker resource measurements missing or invalid')
    if (type(resources.get('load_ms')) not in (int,float) or resources['load_ms'] < 0
            or type(resources.get('peak_working_set_bytes')) is not int or resources['peak_working_set_bytes'] <= 0
            or resources.get('warmup_passes') != 1 or resources.get('measured_passes') != 10
            or type(resources.get('p50_ms')) not in (int,float) or type(resources.get('p95_ms')) not in (int,float)
            or not all(math.isfinite(resources[k]) for k in ('load_ms','p50_ms','p95_ms'))
            or not 0 <= resources['p50_ms'] <= resources['p95_ms']):
        raise ValueError('worker resource measurements missing or invalid')


def run_preflight(python: Path, model_manifest: Path, case_file: Path, output: Path, root: Path) -> dict:
    artifacts = root / 'backend/training/flood_ner/artifacts'
    if not output.resolve().is_relative_to(artifacts.resolve()) or output.exists():
        raise ValueError('preflight destination must be new and under ignored artifacts')
    output = output.resolve()
    interpreter = python.absolute()
    if (not interpreter.resolve().is_relative_to(artifacts.resolve()) or interpreter.resolve() == Path(sys.executable).resolve()
            or not interpreter.is_file()):
        raise ValueError('explicit isolated research interpreter required; main environment forbidden')
    cases = load_cases(case_file)
    manifest,directory = verify_model(model_manifest,artifacts)
    output.mkdir(parents=True)
    request={'model_dir':str(directory),'model_revision':manifest['revision'],'cases':[c.model_dump(mode='json') for c in cases]}
    (output/'request.json').write_bytes(json_bytes(request))
    env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','TEMP','TMP','PATH'}}
    env.update({'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false','OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2'})
    report={'schema_version':'lanes-model-preflight-v1','state':'failed','research_interpreter':str(interpreter),
            'model_manifest_sha256':hashlib.sha256(model_manifest.read_bytes()).hexdigest(),
            'cases_sha256':hashlib.sha256(case_file.read_bytes()).hexdigest(),'model_revision':manifest['revision'],
            'case_count':24,'constructed_only':True,'news_samples_processed':0,'model_training_performed':False,
            'resources':None,'production_runtime_qualified':False,'six_class_accuracy_measured':False}
    try:
        result = subprocess.run([str(interpreter),'-I','-X','utf8',str(Path(__file__).with_name('preflight_worker.py')),str(output/'request.json')],
                                cwd=output,env=env,capture_output=True,timeout=600)
        (output/'stdout.log').write_bytes(result.stdout);(output/'stderr.log').write_bytes(result.stderr)
        stdout = result.stdout.decode('utf-8')
        stderr = result.stderr.decode('utf-8',errors='replace')
        if result.returncode:
            report.update({'failure_stage':'worker_execution','returncode':result.returncode,'error':stderr or stdout or 'worker failed without output'})
        else:
            payload=json.loads(stdout);validate_result(payload,cases)
            (output/'predictions.json').write_bytes(json_bytes(payload))
            report.update({'state':'passed','resources':payload['resources'],'model_weights_loaded':True,
                           'constructed_predictions_recorded':24,'reference_alignment_errors':sum(not s['aligned'] for r in payload['cases'] for s in r['reference_alignment'])})
    except (OSError,subprocess.TimeoutExpired,ValueError,TypeError,KeyError) as exc:
        report.update({'failure_stage':'subprocess_start' if isinstance(exc,OSError) else 'worker_timeout' if isinstance(exc,subprocess.TimeoutExpired) else 'worker_output_validation',
                       'error':str(exc),'os_error':getattr(exc,'winerror',None) or getattr(exc,'errno',None)})
    report['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}
    (output/'report.json').write_bytes(json_bytes(report))
    return report
