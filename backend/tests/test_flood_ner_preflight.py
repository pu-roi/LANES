"""Preflight preserves provenance and refuses unsafe/malformed execution inputs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import pytest

from training.flood_ner import preflight as p

CASES=Path(__file__).resolve().parents[1]/'training/flood_ner/configs/preflight_constructed_cases.jsonl'


def fixture(tmp_path,monkeypatch):
    artifacts=tmp_path/'backend/training/flood_ner/artifacts';model=artifacts/'model';model.mkdir(parents=True)
    names=['config.cfg','meta.json','tokenizer','ner/model','ner/moves','tok2vec/model','vocab/vectors','vocab/vectors.cfg','vocab/strings.json','README.md']
    meta={'version':'0.1.0','license':'MIT','labels':{'ner':['LOC','ORG','PER']}}
    entries=[]
    for name in names:
        target=model/name;target.parent.mkdir(exist_ok=True,parents=True)
        target.write_bytes(json.dumps(meta).encode() if name=='meta.json' else name.encode())
        entries.append({'path':name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size})
    monkeypatch.setattr(p,'PINNED_METADATA_HASHES',{f['path']:f['sha256'] for f in entries if f['path'] in p.PINNED_METADATA_HASHES})
    manifest={'schema_version':'lanes-model-artifact-v1','model':'tl_calamancy_md','version':'0.1.0','revision':p.MODEL_REVISION,'license':'MIT','download_complete':True,'model_dir':str(model),'files':entries}
    path=artifacts/'model_manifest.json';path.write_text(json.dumps(manifest))
    exe=artifacts/'research/python.exe';exe.parent.mkdir();exe.write_bytes(b'constructed executable fixture; never run')
    return artifacts,path,exe,manifest


def payload():
    cases=p.load_cases(CASES);rows=[]
    for case in cases:
        tokens=[{'start':m.start(),'end':m.end(),'text':m.group()} for m in re.finditer(r'\w+|[^\w\s]',case.text)]
        a={t['start'] for t in tokens};z={t['end'] for t in tokens}
        rows.append({'case_id':case.case_id,'text_sha256':case.text_sha256,'tokens':tokens,'entities':[],
                     'reference_alignment':[{'start':e.start,'end':e.end,'label':e.label,'aligned':e.start in a and e.end in z} for e in case.expected_places]})
    return {'schema_version':'lanes-model-preflight-result-v1','python_version':'3.11.17','spacy_version':'3.7.5','model_revision':p.MODEL_REVISION,
            'model_version':'0.1.0','cpu_only':True,'repeated_predictions_identical':True,'cases':rows,
            'resources':{'load_ms':10.0,'peak_working_set_bytes':1000,'p50_ms':1.0,'p95_ms':2.0,'warmup_passes':1,'measured_passes':10}}


def test_constructed_cases_cover_both_languages_and_six_labels():
    cases=p.load_cases(CASES)
    assert len(cases)==24 and sum(c.language=='english' for c in cases)==12
    assert {e.label for c in cases for e in c.expected_places}==p.PLACE_LABELS
    assert any(not c.expected_places for c in cases)


@pytest.mark.parametrize('mutation',['news_origin','silver','source_url','hash','offset','overlap','language_balance','duplicate_id','count'])
def test_case_gate_rejects_nonconstructed_or_malformed_inputs(tmp_path,mutation):
    rows=[json.loads(l) for l in CASES.read_text(encoding='utf8').splitlines()]
    if mutation=='news_origin':rows[0]['origin']='captured_original'
    elif mutation=='silver':rows[0]['quality']='silver'
    elif mutation=='source_url':rows[0]['source_url']='https://publisher.example/news'
    elif mutation=='hash':rows[0]['text_sha256']='0'*64
    elif mutation=='offset':rows[0]['expected_places'][0]['end']+=1
    elif mutation=='overlap':rows[0]['expected_places'].append(deepcopy(rows[0]['expected_places'][0]))
    elif mutation=='language_balance':rows[0]['language']='taglish'
    elif mutation=='duplicate_id':rows[0]['case_id']=rows[1]['case_id']
    else:rows.pop()
    path=tmp_path/'cases.jsonl';path.write_text('\n'.join(json.dumps(x) for x in rows))
    with pytest.raises(ValueError):p.load_cases(path)


@pytest.mark.parametrize('mutation',['wrong_revision','incomplete','duplicate_file','path_escape','hash','missing','unmanifested','pinned_metadata'])
def test_artifact_binding_rejects_identity_hash_and_inventory_defects(tmp_path,monkeypatch,mutation):
    artifacts,path,exe,manifest=fixture(tmp_path,monkeypatch)
    if mutation=='wrong_revision':manifest['revision']='main'
    elif mutation=='incomplete':manifest['download_complete']=False
    elif mutation=='duplicate_file':manifest['files'].append(manifest['files'][0])
    elif mutation=='path_escape':manifest['files'][0]['path']='../config.cfg'
    elif mutation=='hash':manifest['files'][0]['sha256']='0'*64
    elif mutation=='missing':(Path(manifest['model_dir'])/'ner/model').unlink()
    elif mutation=='unmanifested':(Path(manifest['model_dir'])/'extra').write_text('unbound')
    else:p.PINNED_METADATA_HASHES['config.cfg']='0'*64
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):p.verify_model(path,artifacts)


@pytest.mark.parametrize('mutation',['python','spacy','gpu','unstable','case_id','case_hash','entity','label','alignment','nonfinite','missing_resources','bad_tokens','bad_row'])
def test_worker_output_is_revalidated_before_success(mutation):
    r=payload()
    if mutation=='python':r['python_version']='3.12.14'
    elif mutation=='spacy':r['spacy_version']='3.8.3'
    elif mutation=='gpu':r['cpu_only']=False
    elif mutation=='unstable':r['repeated_predictions_identical']=False
    elif mutation=='case_id':r['cases'][0]['case_id']='foreign'
    elif mutation=='case_hash':r['cases'][0]['text_sha256']='0'*64
    elif mutation in {'entity','label'}:r['cases'][0]['entities']=[{'start':0,'end':1,'text':'F','label':'ROAD' if mutation=='label' else 'LOC'}]
    elif mutation=='alignment':r['cases'][0]['reference_alignment'][0]['aligned']=not r['cases'][0]['reference_alignment'][0]['aligned']
    elif mutation=='nonfinite':r['resources']['load_ms']=float('nan')
    elif mutation=='missing_resources':r['resources']=None
    elif mutation=='bad_tokens':r['cases'][0]['tokens']=[None]
    else:r['cases'][0]=None
    with pytest.raises(ValueError):p.validate_result(r,p.load_cases(CASES))


@pytest.mark.parametrize('relative',[False,True])
def test_success_records_real_worker_payload_and_isolation(tmp_path,monkeypatch,relative):
    artifacts,path,exe,_=fixture(tmp_path,monkeypatch);out=artifacts/'result'
    def run(args,**kwargs):
        assert args[0]==str(exe) and args[1]=='-I'
        assert kwargs['env']['HF_HUB_OFFLINE']=='1' and kwargs['env']['TRANSFORMERS_OFFLINE']=='1'
        assert 'GEMINI_API_KEY' not in kwargs['env']
        assert len(json.loads(Path(args[-1]).read_text())['cases'])==24
        assert args[2:4]==['-X','utf8']
        return subprocess.CompletedProcess(args,0,json.dumps(payload(),ensure_ascii=False).encode('utf8'),b'')
    monkeypatch.setattr(p.subprocess,'run',run)
    if relative:monkeypatch.chdir(tmp_path)
    result=p.run_preflight(exe,path,CASES,out.relative_to(tmp_path) if relative else out,tmp_path)
    assert result['state']=='passed' and result['news_samples_processed']==0
    assert (out/'predictions.json').exists() and result['constructed_predictions_recorded']==24
    with pytest.raises(ValueError):p.run_preflight(exe,path,CASES,out,tmp_path)


@pytest.mark.parametrize('failure',['os_policy','nonzero','bad_json','bad_encoding','timeout'])
def test_failed_subprocess_never_becomes_predictions_or_measurements(tmp_path,monkeypatch,failure):
    artifacts,path,exe,_=fixture(tmp_path,monkeypatch);out=artifacts/'failed'
    def run(args,**kwargs):
        if failure=='os_policy':raise PermissionError(4551,'Application Control policy blocked execution')
        if failure=='timeout':raise subprocess.TimeoutExpired(args,600)
        return subprocess.CompletedProcess(args,1 if failure=='nonzero' else 0,b'\xf1' if failure=='bad_encoding' else b'not json',b'dependency failure' if failure=='nonzero' else b'')
    monkeypatch.setattr(p.subprocess,'run',run)
    result=p.run_preflight(exe,path,CASES,out,tmp_path)
    assert result['state']=='failed' and result['resources'] is None and result['error']
    assert not(out/'predictions.json').exists() and (out/'report.json').exists()


def test_main_interpreter_and_outside_output_are_rejected_before_execution(tmp_path,monkeypatch):
    artifacts,path,exe,_=fixture(tmp_path,monkeypatch)
    def run(*args,**kwargs):raise AssertionError('must never start worker')
    monkeypatch.setattr(p.subprocess,'run',run)
    with pytest.raises(ValueError,match='isolated'):p.run_preflight(Path(sys.executable),path,CASES,artifacts/'result',tmp_path)
    with pytest.raises(ValueError,match='ignored'):p.run_preflight(exe,path,CASES,tmp_path/'outside',tmp_path)


def test_real_subprocess_unicode_wire_preserves_filipino_characters():
    result=subprocess.run([sys.executable,'-I','-X','utf8','-c',
                           'import json;print(json.dumps({"place":"Biñan—Pag-asa"},ensure_ascii=False))'],capture_output=True,check=True)
    assert json.loads(result.stdout.decode('utf8'))=={'place':'Biñan—Pag-asa'}
