"""Constructed authorization, isolation and stop-on-failure regressions."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.flood_ner import context_run_v36 as runner
from training.flood_ner import context_association_worker_v36 as worker
from training.flood_ner import context_association_v36 as engine
from training.flood_ner import context_scoring_v36 as scoring
from training.flood_ner import context_review_v36 as review
from training.flood_ner.context_cases_v36 import core_cases
from test_flood_ner_context_association_v36 import raw_case


def test_stale_grant_stops_before_predecessor(tmp_path,monkeypatch):
    path=tmp_path/'grant.json';path.write_text('{}',encoding='utf-8')
    monkeypatch.setattr(runner.predecessor,'preflight',lambda *a:pytest.fail('must not inspect predecessor'))
    with pytest.raises(ValueError,match='stale'):runner.preflight(tmp_path,path,'0'*64)


def test_wrong_scope_and_incomplete_binding_stop_before_dispatch(tmp_path):
    path=tmp_path/'grant.json';path.write_text('{}',encoding='utf-8')
    with pytest.raises(ValueError,match='exact review'):runner.preflight(tmp_path,path,runner.digest(path))


def test_worker_closure_excludes_references_oracles_and_models():
    assert not any(any(w in n for w in ('cases','scoring','review_v36','predictions','model'))for n in runner.WORKER_FILES)
    assert 'training/flood_ner/context_association_worker_v36.py'in runner.WORKER_FILES


def test_occupied_destination_blocks_all_commands(tmp_path,monkeypatch):
    art=tmp_path/'training/flood_ner/artifacts';art.mkdir(parents=True)
    monkeypatch.setattr(runner,'__file__',str(art.parent/'context_run_v36.py'))
    monkeypatch.setattr(runner,'preflight',lambda *a:({}, {}, {'image_id':'sha256:'+'a'*64}))
    monkeypatch.setattr(runner.q,'command',lambda *a,**kw:pytest.fail('no dispatch'))
    dest=art/'occupied';dest.mkdir()
    with pytest.raises(ValueError,match='new direct'):runner.execute(tmp_path,'docker',tmp_path/'grant','a'*64,dest)


def test_competing_writers_and_consumed_claims(tmp_path):
    lock=tmp_path/'lease'
    with runner.q.exclusive(lock,{'owner':'first'}):
        with pytest.raises(FileExistsError):
            with runner.q.exclusive(lock,{'owner':'second'}):pytest.fail('second writer')
    claim=tmp_path/'claim';runner.q.write_new(claim,{'attempt':1})
    with pytest.raises(FileExistsError):runner.q.write_new(claim,{'attempt':2})


def test_failed_attempt_preserves_claim_lock_and_partial_evidence(tmp_path,monkeypatch):
    art=tmp_path/'training/flood_ner/artifacts';art.mkdir(parents=True)
    monkeypatch.setattr(runner,'__file__',str(art.parent/'context_run_v36.py'))
    monkeypatch.setattr(runner,'preflight',lambda *a:({}, {}, {'image_id':'sha256:'+'a'*64}))
    calls=[]
    def failed(args,*a,**kw):calls.append(args);return {'returncode':1,'stdout':'','stderr':'constructed failure'}
    monkeypatch.setattr(runner.q,'command',failed)
    with pytest.raises(ValueError):runner.execute(tmp_path,'docker',tmp_path/'grant','a'*64,art/'first')
    assert len(calls)==1 and(art/'first/failure.json').exists()
    assert(art/'context-association-v36-active.lock').exists()
    assert(art/'context-association-v36-claims'/('a'*64+'.json')).exists()
    with pytest.raises(FileExistsError):runner.execute(tmp_path,'docker',tmp_path/'grant','a'*64,art/'second')
    assert len(calls)==1 and not(art/'second').exists()


def test_actual_worker_import_network_and_database_guards(tmp_path):
    backend=Path(__file__).resolve().parents[1]
    code="""import sys,socket
sys.path.insert(0,sys.argv[1])
from training.flood_ner.context_association_worker_v36 import NoNeural,install_guards
sys.meta_path.insert(0,NoNeural());install_guards()
from training.flood_ner.context_association_v36 import extract
for name in ['spacy','torch','sqlite3','psycopg']:
 try:__import__(name)
 except (RuntimeError,ImportError):pass
 else:raise AssertionError('forbidden import '+name)
try:socket.create_connection(('127.0.0.1',1))
except RuntimeError:pass
else:raise AssertionError('network allowed')
print('guards_verified')
"""
    result=subprocess.run([sys.executable,'-I','-B','-c',code,str(backend)],cwd=tmp_path,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()=='guards_verified'


def test_timeout_stops_before_second_input_and_preserves_partial_stream(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'install_guards',lambda:None)
    monkeypatch.setattr(worker.signal,'SIGALRM',14,raising=False);monkeypatch.setattr(worker.signal,'ITIMER_REAL',0,raising=False)
    monkeypatch.setattr(worker.signal,'signal',lambda *a:None);monkeypatch.setattr(worker.signal,'setitimer',lambda *a:None,raising=False)
    calls=[]
    def failed(row):calls.append(row['record_id']);raise TimeoutError('constructed')
    monkeypatch.setattr(engine,'extract',failed)
    rows=[{'record_id':f'constructed-{i}','text':'','text_sha256':runner.q.text_hash(''),
        'publication':None,'mentions':[]}for i in range(184)]
    prior=list(sys.meta_path)
    try:
        with pytest.raises(TimeoutError):worker.run({'schema':'lanes-context-association-worker-v36','rows':rows,'implementation':{}},tmp_path)
    finally:sys.meta_path[:]=prior
    assert len(calls)==1 and(tmp_path/'results.jsonl').read_bytes()==b''
    assert json.loads((tmp_path/'heartbeat.json').read_text())['index']==0


def test_extra_unspecified_status_cannot_hide_in_new_exhaustive_fixtures():
    case=core_cases()[1];raw=raw_case(case);output=engine.extract(raw)
    output['facts'].append({'id':'bad','kind':'status','entity_ids':[],'value':'active','temporal_role':None,
        'depth_scope':None,'qualifiers':[],'uncertainty':[],'evidence':[{'start':0,'end':len(raw['text']),'text':raw['text']}]})
    output['relations'].append({'id':'bad-r','fact_id':'bad','target_entity_ids':[raw['mentions'][0]['id']],
        'scope':'local','evidence':[{'start':0,'end':len(raw['text']),'text':raw['text']}],'uncertainty':[],
        'overrides_relation_id':None,'reason':'constructed forged assertion'})
    assert not review.fixture_result(case,raw,output,exhaustive=True)['passed']


@pytest.mark.parametrize('field',['record_id','url','title','text','predictions','annotations'])
def test_aggregate_rejects_source_bearing_fields(field):
    with pytest.raises(ValueError):scoring.public_aggregate({field:'forbidden'})
