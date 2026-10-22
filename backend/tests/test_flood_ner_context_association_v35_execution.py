"""Constructed control/scoring failure cases; no real workers or corpus."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.flood_ner import context_association_run_v35 as runner
from training.flood_ner import context_association_scoring_v35 as score
from training.flood_ner import context_association_worker_v35 as worker
from training.flood_ner import context_association_v35 as engine
from training.flood_ner.context_association_cases_v35 import core_cases
from test_flood_ner_context_association_v35 import raw_case


def test_stale_grant_rejected_before_predecessor_or_dispatch(tmp_path,monkeypatch):
    path=tmp_path/'grant.json';path.write_text('{}',encoding='utf-8')
    monkeypatch.setattr(runner.previous,'preflight',lambda *a:pytest.fail('predecessor must not run'))
    with pytest.raises(ValueError,match='stale'):runner.preflight(tmp_path,path,'0'*64)


def test_wrong_scope_or_absent_binding_rejected_before_dispatch(tmp_path):
    path=tmp_path/'grant.json';path.write_text('{}',encoding='utf-8')
    with pytest.raises(ValueError,match='exact successor'):runner.preflight(tmp_path,path,runner.digest(path))


@pytest.mark.parametrize('damage',['returncode','incomplete','count','scope','stale'])
def test_fixture_qualification_requires_authentic_complete_binding(tmp_path,damage):
    script=tmp_path/'qualify_fixtures.py';script.write_text('# constructed',encoding='utf-8')
    data={'returncode':0,'output_complete':True,'args':[str(script),'a'*64],
        'stdout':json.dumps({'status':'qualified_fictional_fixtures','cases':64,
            'tokenizer_reconstruction_verified':True,'neural_inference':False,'training_started':False})}
    if damage=='returncode':data['returncode']=1
    if damage=='incomplete':data['output_complete']=False
    if damage in {'count','scope'}:
        result=json.loads(data['stdout']);result['cases'if damage=='count'else'status']=40 if damage=='count'else'forged_ready'
        data['stdout']=json.dumps(result)
    receipt=tmp_path/'receipt.json';receipt.write_text(json.dumps(data),encoding='utf-8')
    protocol={'fixture_qualification':{'path':receipt.name,'sha256':runner.digest(receipt)},
        'fixture_qualification_script':{'path':script.name,'sha256':runner.digest(script)}}
    if damage=='stale':receipt.write_text('{}',encoding='utf-8')
    with pytest.raises(ValueError):runner.verify_fixture_qualification(tmp_path,protocol,'a'*64)


def test_worker_mount_closure_excludes_oracles_and_model_code():
    assert not any(any(w in name for w in ('scoring','cases_v35','model','prediction'))for name in runner.WORKER_FILES)
    assert 'training/flood_ner/context_association_worker_v35.py'in runner.WORKER_FILES


def test_occupied_destination_blocks_all_commands(tmp_path,monkeypatch):
    art=tmp_path/'training/flood_ner/artifacts';art.mkdir(parents=True)
    monkeypatch.setattr(runner,'__file__',str(art.parent/'context_association_run_v35.py'))
    monkeypatch.setattr(runner,'preflight',lambda *a:({}, {}, {'image_id':'sha256:'+'a'*64}))
    monkeypatch.setattr(runner.q,'command',lambda *a,**kw:pytest.fail('no dispatch'))
    dest=art/'occupied';dest.mkdir()
    with pytest.raises(ValueError,match='new direct'):runner.execute(tmp_path,'docker',tmp_path/'grant','a'*64,dest)


def test_concurrent_lease_and_consumed_claim_are_exclusive(tmp_path):
    lock=tmp_path/'lease'
    with runner.q.exclusive(lock,{'owner':'first'}):
        with pytest.raises(FileExistsError):
            with runner.q.exclusive(lock,{'owner':'second'}):pytest.fail('second owner entered')
        assert json.loads(lock.read_text(encoding='utf-8'))['owner']=='first'
    claim=tmp_path/'consumed.json';runner.q.write_new(claim,{'attempt':1})
    with pytest.raises(FileExistsError):runner.q.write_new(claim,{'attempt':2})


def test_failed_dispatch_preserves_claim_and_blocks_second_launch(tmp_path,monkeypatch):
    art=tmp_path/'training/flood_ner/artifacts';art.mkdir(parents=True)
    monkeypatch.setattr(runner,'__file__',str(art.parent/'context_association_run_v35.py'))
    monkeypatch.setattr(runner,'preflight',lambda *a:({}, {}, {'image_id':'sha256:'+'a'*64}))
    calls=[]
    def failed(args,*a,**kw):calls.append(args);return {'returncode':1,'stdout':'','stderr':'constructed failure'}
    monkeypatch.setattr(runner.q,'command',failed)
    with pytest.raises(ValueError,match='command failed'):
        runner.execute(tmp_path,'docker',tmp_path/'grant','a'*64,art/'first')
    assert len(calls)==1 and (art/'first/failure.json').exists()
    assert (art/'context-association-v35-active.lock').exists()
    assert (art/'context-association-v35-claims'/('a'*64+'.json')).exists()
    with pytest.raises(FileExistsError):runner.execute(tmp_path,'docker',tmp_path/'grant','a'*64,art/'second')
    assert len(calls)==1 and not(art/'second').exists()


def test_actual_worker_guards_block_model_network_and_database_imports(tmp_path):
    backend=Path(__file__).resolve().parents[1]
    code="""import sys,socket
sys.path.insert(0,sys.argv[1])
from training.flood_ner.context_association_worker_v35 import NoNeural,install_guards
sys.meta_path.insert(0,NoNeural());install_guards()
from training.flood_ner.context_association_v35 import extract
for name in ['spacy','torch','sqlite3','psycopg']:
 try:__import__(name)
 except (RuntimeError,ImportError):pass
 else:raise AssertionError('forbidden import '+name)
try:socket.create_connection(('127.0.0.1',1))
except RuntimeError:pass
else:raise AssertionError('network dispatch allowed')
print('guards_verified')
"""
    result=subprocess.run([sys.executable,'-I','-B','-c',code,str(backend)],cwd=tmp_path,
        capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()=='guards_verified'


def test_timeout_stops_first_constructed_input_preserving_partial_evidence(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'install_guards',lambda:None)
    # Windows parent has no SIGALRM; exercise the same handler wiring with an
    # injected extractor timeout, without changing or waiting on a real clock.
    monkeypatch.setattr(worker.signal,'SIGALRM',14,raising=False)
    monkeypatch.setattr(worker.signal,'ITIMER_REAL',0,raising=False)
    monkeypatch.setattr(worker.signal,'signal',lambda *a:None)
    monkeypatch.setattr(worker.signal,'setitimer',lambda *a:None,raising=False)
    calls=[]
    def failed(row):calls.append(row['record_id']);raise TimeoutError('constructed timeout')
    monkeypatch.setattr(engine,'extract',failed)
    rows=[{'record_id':f'constructed-{i}','text':'','text_sha256':runner.q.text_hash(''),
        'publication':None,'mentions':[]}for i in range(88)]
    prior=list(sys.meta_path)
    try:
        with pytest.raises(TimeoutError):worker.run({'schema':'lanes-context-association-worker-v35','rows':rows,'implementation':{}},tmp_path)
    finally:sys.meta_path[:]=prior
    assert calls==['constructed-0'] and (tmp_path/'results.jsonl').read_bytes()==b''
    assert json.loads((tmp_path/'heartbeat.json').read_text(encoding='utf-8'))['index']==0


def test_strict_scoring_keeps_reference_versions_and_correct_links_separate():
    case=core_cases()[0];raw=raw_case(case);out=engine.extract(raw)
    baseline={**deepcopy(out),'unscored':[]}
    result=score.compare(case['record'],raw,baseline,out,out)
    assert not result['transitions']['introduced_incorrect'] and not result['transitions']['lost_correct']
    assert all(r['baseline']==r['v34']==r['candidate']for r in result['metrics'].values())
    mapping=score.map_previous_correct(case['record'],case['record'],baseline,out,None)
    assert mapping and all(e['disposition']=='retained'for e in mapping)
    changed=deepcopy(case['record']);changed['relations']=[]
    with pytest.raises(ValueError,match='without independent'):score.map_previous_correct(case['record'],changed,baseline,out,None)


def test_qualifier_loss_remains_a_scoring_failure():
    case=next(c for c in core_cases()if c['family']=='collective_ranges' and c['contrast']=='supported')
    out=engine.extract(raw_case(case))
    assert score.qualifier_errors(out)==[]
    next(f for f in out['facts']if f['kind']=='depth')['qualifiers']=[]
    assert 'range_qualifier_lost'in score.qualifier_errors(out)


@pytest.mark.parametrize('damage',['fixture','reference','lost','introduced','qualifier'])
def test_acceptance_is_derived_from_actual_evidence(damage):
    case=core_cases()[0];raw=raw_case(case);out=engine.extract(raw)
    baseline={**deepcopy(out),'unscored':[]}
    template=score.compare(case['record'],raw,baseline,out,out)
    reviews=[]
    for i in range(24):
        row=deepcopy(template);row['record_id']=f'constructed-{i}'
        row['transitions']['gained_correct']=[('constructed-targeted-correction',)]
        reviews.append(row)
    fixtures=[{'case_id':f'fictional-{i}','passed':True}for i in range(64)]
    mapping=[]
    if damage=='fixture':fixtures[0]['passed']=False
    if damage=='reference':mapping=[{'associations':[{'disposition':'unresolved'}]}]
    if damage=='lost':reviews[0]['transitions']['lost_correct']=[('lost',)]
    if damage=='introduced':reviews[0]['transitions']['introduced_incorrect']=[('incorrect',)]
    if damage=='qualifier':reviews[0]['qualifier_errors']=['lost']
    result=score.summarize(reviews,fixtures,mapping,{r['record_id']for r in reviews},set())
    assert result['status']=='not_qualified' and result['blockers']


def test_held_or_missing_records_cannot_be_negatives():
    with pytest.raises(ValueError,match='accounting'):score.summarize([],[],[],{'missing'},set())
