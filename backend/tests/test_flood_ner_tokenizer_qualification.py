"""Boundary qualification guards and unchanged-source regressions."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
import spacy
from spacy.tokenizer import Tokenizer

from training.flood_ner import tokenizer_qualification as q
from training.flood_ner.model_tokenizer import apply_candidate, extend_pattern
from training.flood_ner.export import corpus_tokenizer, CANDIDATE_TOKENIZER_NAME
from test_flood_ner_preflight import fixture

CASES = Path(__file__).resolve().parents[1] / 'training/flood_ner/configs/tokenizer_qualification_cases.jsonl'


@pytest.mark.parametrize('text,expected', [
    ('CITY—-Purok 31-A', ['CITY', '—-', 'Purok', '31-A']),
    ('CITY–--Purok 003-B', ['CITY', '–--', 'Purok', '003-B']),
    ('CITY- and -Bonifacio', ['CITY', '-', 'and', '-', 'Bonifacio']),
    ('--Rizal', ['-', '-', 'Rizal']),
    ('Unit 101-B', ['Unit', '101-B']),
    ('Biñan—-Purok', ['Biñan', '—-', 'Purok']),
])
def test_candidate_delimiters_preserve_internal_identifiers_and_text(text, expected):
    nlp = corpus_tokenizer(CANDIDATE_TOKENIZER_NAME); apply_candidate(nlp.tokenizer)
    doc = nlp(text)
    assert [t.text for t in doc] == expected
    assert doc.text == text


def test_candidate_keeps_exceptions_token_matching_flags_and_serialized_roundtrip():
    import re
    nlp = spacy.blank('xx')
    nlp.tokenizer.add_special_case('DO-NOT-SPLIT', [{'ORTH': 'DO-NOT-SPLIT'}])
    nlp.tokenizer.token_match = re.compile(r'^ABC-\d+$', re.I).match
    nlp.tokenizer.prefix_search = re.compile(nlp.tokenizer.prefix_search.__self__.pattern, re.I).search
    apply_candidate(nlp.tokenizer)
    assert nlp.tokenizer.prefix_search.__self__.flags & re.I
    data = nlp.tokenizer.to_bytes(exclude=['vocab'])
    restored = Tokenizer(nlp.vocab).from_bytes(data, exclude=['vocab'])
    text = 'DO-NOT-SPLIT ABC-12 CITY—-Purok 31-A'
    assert [(t.idx,t.text,t.whitespace_) for t in restored(text)] == [(t.idx,t.text,t.whitespace_) for t in nlp(text)]
    assert 'DO-NOT-SPLIT' in [t.text for t in restored(text)]
    assert 'ABC-12' in [t.text for t in restored(text)]
    with pytest.raises(ValueError): extend_pattern(lambda s: None, '-')


def test_qualification_cases_preserve_originals_and_expanded_controls():
    cases = q.load_cases(CASES)
    assert len(cases) == 48 and sum(c.language == 'english' for c in cases) == 24
    assert cases[19].text == q.preflight.load_cases(q.ORIGINAL_CASES)[19].text
    assert any(not c.expected_places for c in cases[24:])
    assert q.REQUIRED_TAGS <= {t for c in cases[24:] for t in c.tags}


@pytest.mark.parametrize('mutation', ['count','origin','quality','news_field','hash','original','duplicate_text',
                                     'language','control_offset','no_controls','no_tags','overlap'])
def test_constructed_gate_rejects_unqualified_cases(tmp_path, mutation):
    rows = [json.loads(l) for l in CASES.read_text(encoding='utf-8').split('\n') if l.strip()]
    row = rows[24]
    if mutation == 'count': rows.pop()
    elif mutation == 'origin': row['origin'] = 'captured_original'
    elif mutation == 'quality': row['quality'] = 'silver'
    elif mutation == 'news_field': row['source_url'] = 'https://example.org/news'
    elif mutation == 'hash': row['text_sha256'] = '0'*64
    elif mutation == 'original': rows[0]['tags'].append('changed')
    elif mutation == 'duplicate_text': row['text'] = rows[25]['text']
    elif mutation == 'language': row['language'] = 'taglish'
    elif mutation == 'control_offset': row['token_controls'][0]['end'] += 1
    elif mutation == 'no_controls': row['token_controls'] = []
    elif mutation == 'no_tags':
        for r in rows[24:]: r['tags'] = ['unrelated']
    else: row['expected_places'].append(deepcopy(row['expected_places'][0]))
    path = tmp_path/'cases.jsonl'; path.write_text('\n'.join(json.dumps(r) for r in rows), encoding='utf-8')
    with pytest.raises(ValueError): q.load_cases(path)


def payload(cases, mode='candidate'):
    nlp = corpus_tokenizer(CANDIDATE_TOKENIZER_NAME); apply_candidate(nlp.tokenizer)
    rows = []
    for case in cases:
        doc = nlp(case.text)
        rows.append({'case_id': case.case_id, 'text_sha256': case.text_sha256,
                     'tokens': [{'start':t.idx,'end':t.idx+len(t.text),'text':t.text} for t in doc], 'entities': [],
                     'reference_alignment': [{'start':s.start,'end':s.end,'label':s.label,
                                              'aligned':doc.char_span(s.start,s.end) is not None} for s in case.expected_places]})
    return {'schema_version':'lanes-model-preflight-result-v1','python_version':'3.11.17','spacy_version':'3.7.5',
            'model_revision':q.preflight.MODEL_REVISION,'model_version':'0.1.0','cpu_only':True,
            'pipeline':['tok2vec','ner'],'repeated_predictions_identical':True,'roundtrip_identical':True,
            'tokenizer_mode':mode,'tokenizer_name':'calamancy-native' if mode=='native' else q.TOKENIZER_NAME,
            'tokenizer_sha256':hashlib.sha256(b'fixture bytes').hexdigest(),'cases':rows,
            'resources':{'load_ms':1.0,'p50_ms':1.0,'p95_ms':2.0,'peak_working_set_bytes':1000,
                         'warmup_passes':1,'measured_passes':10,'measured_calls':480,'batch_size':1,'threads':2}}


@pytest.mark.parametrize('mutation',['false_alignment','integer_alignment','omitted_token','mode','roundtrip','hash','calls','pipeline'])
def test_worker_claims_are_recomputed_and_bound_to_saved_bytes(tmp_path, mutation):
    cases = q.load_cases(CASES); r = payload(cases)
    (tmp_path/'candidate.tokenizer.bin').write_bytes(b'fixture bytes')
    if mutation == 'false_alignment': r['cases'][0]['reference_alignment'][0]['aligned'] = False
    elif mutation == 'integer_alignment': r['cases'][0]['reference_alignment'][0]['aligned'] = 1
    elif mutation == 'omitted_token': r['cases'][0]['tokens'].pop(0)
    elif mutation == 'mode': r['tokenizer_mode'] = 'native'
    elif mutation == 'roundtrip': r['roundtrip_identical'] = False
    elif mutation == 'hash': r['tokenizer_sha256'] = '0'*64
    elif mutation == 'calls': r['resources']['measured_calls'] = 24
    else: r['pipeline'] = ['ner']
    with pytest.raises(ValueError): q.validate_payload(r,cases,'candidate',tmp_path)


def test_controls_distinguish_alignment_from_identifier_preservation():
    cases = q.load_cases(CASES); rows = payload(cases)['cases']
    assert not q.assess(rows,cases,rows)['control_failures']
    target = next(c for c in cases[24:] if '31-A' in c.text)
    row = next(r for r in rows if r['case_id']==target.case_id)
    token = next(t for t in row['tokens'] if t['text']=='31-A')
    a=token['start'];i=row['tokens'].index(token)
    row['tokens'][i:i+1]=[{'start':a,'end':a+2,'text':'31'},{'start':a+2,'end':a+3,'text':'-'},{'start':a+3,'end':a+4,'text':'A'}]
    assessed = q.assess(rows,cases,rows)
    assert not assessed['reference_alignment_errors']
    assert assessed['control_failures']


def test_command_runs_modes_separately_and_records_deterministic_artifacts(tmp_path,monkeypatch):
    artifacts,path,exe,_ = fixture(tmp_path,monkeypatch); calls=[]
    def run(args,**kwargs):
        request=json.loads(Path(args[-1]).read_text()); mode=request['mode'];calls.append(mode)
        assert args[:4]==[str(exe),'-I','-X','utf8'] and kwargs['env']['HF_HUB_OFFLINE']=='1'
        assert 'GEMINI_API_KEY' not in kwargs['env']
        Path(request['tokenizer_file']).write_bytes(b'fixture bytes')
        return subprocess.CompletedProcess(args,0,json.dumps(payload(q.load_cases(CASES),mode)).encode(),b'')
    monkeypatch.setattr(q.subprocess,'run',run)
    report=q.qualify_tokenizer(exe,path,CASES,artifacts/'result',tmp_path)
    assert report['state']=='passed' and calls==['native','candidate']
    assert report['news_samples_processed']==0 and report['training_admitted']==0
    assert (artifacts/'result/tokenizer_manifest.json').exists()
    with pytest.raises(ValueError):q.qualify_tokenizer(exe,path,CASES,artifacts/'result',tmp_path)
    with pytest.raises(ValueError):q.qualify_tokenizer(Path(sys.executable),path,CASES,artifacts/'main',tmp_path)
    with pytest.raises(ValueError):q.qualify_tokenizer(exe,path,CASES,tmp_path/'outside',tmp_path)


@pytest.mark.parametrize('failure',['nonzero','timeout','encoding','oserror'])
def test_failed_worker_preserves_evidence_without_a_success_result(tmp_path,monkeypatch,failure):
    artifacts,path,exe,_=fixture(tmp_path,monkeypatch)
    def run(args,**kwargs):
        if failure=='timeout':raise subprocess.TimeoutExpired(args,600)
        if failure=='oserror':raise PermissionError('blocked')
        return subprocess.CompletedProcess(args,1 if failure=='nonzero' else 0,b'\xff',b'failed')
    monkeypatch.setattr(q.subprocess,'run',run)
    report=q.qualify_tokenizer(exe,path,CASES,artifacts/'failed',tmp_path)
    assert report['state']=='failed' and report['error'] and not report['runs']
    assert not (artifacts/'failed/tokenizer_manifest.json').exists()


def test_unicode_jsonl_uses_physical_lines(tmp_path):
    text=CASES.read_text(encoding='utf-8').replace('Malabon City\\n', 'Malabon City\\u2028')
    # Decoded alternate separators are source characters, never JSONL record boundaries.
    rows=[json.loads(l) for l in text.split('\n') if l.strip()]
    for row in rows:row['text_sha256']=hashlib.sha256(row['text'].encode()).hexdigest()
    # New whitespace variant changes lengths by zero, so offsets still bind.
    p=tmp_path/'cases.jsonl';p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    assert len(q.load_cases(p))==48


def test_original_constructed_checkpoint_is_hash_bound(tmp_path,monkeypatch):
    p=tmp_path/'original.jsonl';p.write_bytes(q.ORIGINAL_CASES.read_bytes()+b'\n')
    monkeypatch.setattr(q,'ORIGINAL_CASES',p)
    with pytest.raises(ValueError,match='checkpoint hash'):q.load_cases(CASES)


@pytest.mark.parametrize('state,expected',[('passed',0),('failed',2)])
def test_cli_returns_qualification_outcome_without_changing_preflight(state,expected,tmp_path,monkeypatch,capsys):
    from training.flood_ner.cli import main
    monkeypatch.setattr(q,'qualify_tokenizer',lambda *args: {'state':state})
    assert main(['qualify-model-tokenizer','--python',str(tmp_path/'python.exe'),'--model-manifest',str(tmp_path/'model.json'),
                 '--cases',str(CASES),'--output',str(tmp_path/'out')])==expected
    assert json.loads(capsys.readouterr().out)['state']==state


def test_post_inference_artifact_failure_revokes_success(tmp_path,monkeypatch):
    artifacts,path,exe,_=fixture(tmp_path,monkeypatch)
    def run(args,**kwargs):
        request=json.loads(Path(args[-1]).read_text())
        Path(request['tokenizer_file']).write_bytes(b'fixture bytes')
        return subprocess.CompletedProcess(args,0,json.dumps(payload(q.load_cases(CASES),request['mode'])).encode(),b'')
    monkeypatch.setattr(q.subprocess,'run',run)
    original=Path.write_bytes
    def write(path,data):
        if path.name=='tokenizer_manifest.json':raise OSError('constructed artifact write failure')
        return original(path,data)
    monkeypatch.setattr(Path,'write_bytes',write)
    report=q.qualify_tokenizer(exe,path,CASES,artifacts/'failed_manifest',tmp_path)
    assert report['state']=='failed' and 'artifact write failure' in report['error']
    assert (artifacts/'failed_manifest/report.json').exists()
