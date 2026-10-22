"""Fictional source-bound context records and mocked worker contracts."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.flood_ner import context_gap_audit as a
from training.flood_ner import context_gap_runner as r
from training.flood_ner.annotation.schema import AnnotationRecord


@pytest.fixture
def tokenizer():
    from spacy.tokenizer import Tokenizer
    from spacy.vocab import Vocab
    return SimpleNamespace(make_doc=Tokenizer(Vocab()))


def records():
    text='Aster Road had knee-deep flooding at 2 PM.'
    def entity(name,label,id):
        start=text.index(name);return {'id':id,'start':start,'end':start+len(name),'text':name,'label':label}
    loc=entity('Aster Road','ROAD','road');depth=entity('knee-deep','DEPTH','depth');time=entity('2 PM','TIME','clock')
    def span(e):return {k:e[k]for k in ('start','end','text')}
    source={'source_id':'fictional-source','url':'https://example.invalid/fictional','publisher':'Fixture',
            'text':text,'text_sha256':a.text_hash(text),'capture_version':'fixture','article_group':'fixture',
            'reuse_terms':'private_owner_only_academic_training_evaluation','reuse_status':'allowed',
            'admission_status':'training_admitted','extraction_method':'fictional fixture'}
    base={'record_id':'fixture-1','source':source,'passage_start':0,'passage_end':len(text),'text':text,'text_sha256':a.text_hash(text),
          'passage_language':'english','entities':[loc],'facts':[],'relations':[],'annotation_revision':'fictional',
          'review_status':'accepted','complete':True,'split':'train','annotation_profile':'location-only-v1',
          'teacher':'fictional teacher','reviewer':'fictional reviewer'}
    loc_record=AnnotationRecord.model_validate_json(json.dumps(base)).model_dump(mode='json')
    rich=deepcopy(base);rich.update(annotation_profile='context-rich-v1',entities=[loc,depth,time],
        facts=[{'id':'d','kind':'depth','value':'knee-deep','depth_scope':'point','entity_ids':['depth'],'evidence':[span(depth)]},
               {'id':'t','kind':'time','value':'2 PM','temporal_role':'observation','entity_ids':['clock'],'evidence':[span(time)]}],
        relations=[{'id':'rd','fact_id':'d','target_entity_ids':['road'],'scope':'local','evidence':[{'start':0,'end':len(text),'text':text}]},
                   {'id':'rt','fact_id':'t','target_entity_ids':['road'],'scope':'local','evidence':[{'start':0,'end':len(text),'text':text}]}])
    return loc_record,AnnotationRecord.model_validate_json(json.dumps(rich)).model_dump(mode='json')


def test_complete_reference_and_missing_are_separate(tokenizer):
    loc,ref=records();result,unmatched=a.inventory([loc],[ref],tokenizer)
    assert result[0]['context']['scorable'] and result[0]['context']['context_entities']=={'DEPTH':1,'TIME':1}
    assert result[0]['context_negative']is False and not unmatched
    result,_=a.inventory([loc],[],tokenizer)
    assert result[0]['context']['state']=='missing_context_reference' and not result[0]['context_negative']


@pytest.mark.parametrize('damage',['hash','source','offset','language','partition','complete','null','span','relation','location_drift','role'])
def test_bad_context_never_becomes_complete_negative(tokenizer,damage):
    loc,ref=records()
    if damage=='hash':ref['text_sha256']='0'*64
    elif damage=='source':ref['source']['capture_version']='other'
    elif damage=='offset':ref['passage_start']=1
    elif damage=='language':ref['passage_language']='taglish'
    elif damage=='partition':ref['split']='test'
    elif damage=='complete':ref['complete']=False
    elif damage=='null':ref['facts']=None
    elif damage=='span':ref['entities'][1]['text']='wrong'
    elif damage=='relation':ref['relations'][0]['target_entity_ids']=['nonexistent']
    elif damage=='location_drift':loc['entities'][0]['end']-=5;loc['entities'][0]['text']='Aster'
    elif damage=='role':ref['facts'][1]['temporal_role']='onset';ref['facts'][1]['qualifiers']=['not a flood onset']
    state=a.contextual_state(ref,loc,tokenizer)
    assert state['scorable']is False


def test_duplicate_active_context_and_outside_membership(tokenizer):
    loc,ref=records()
    with pytest.raises(ValueError):a.inventory([loc],[ref,ref],tokenizer)
    ref['record_id']='outside';result,unmatched=a.inventory([loc],[ref],tokenizer)
    assert len(unmatched)==1 and result[0]['context']['state']=='missing_context_reference'


@pytest.mark.parametrize('damage',['reference','prediction','hash','duplicate','naive_time','oversize','type'])
def test_raw_worker_input_rejects_unbound_or_reference_data(damage):
    row={'record_id':'fictional-1','text':'🌧 Piña Road','text_sha256':a.text_hash('🌧 Piña Road'),'published_at':None}
    rows=[row]
    if damage in('reference','prediction'):row[damage]=[]
    elif damage=='hash':row['text_sha256']='0'*64
    elif damage=='duplicate':rows.append(deepcopy(row))
    elif damage=='naive_time':row['published_at']='2026-10-01T02:00:00'
    elif damage=='oversize':row['text']='x'*100001;row['text_sha256']=a.text_hash(row['text'])
    elif damage=='type':row['text']=42
    with pytest.raises(ValueError):a.validate_raw(rows)


def test_only_supported_publication_time_reaches_projection():
    loc,_=records();loc['source']['published_at']='2026-10-01T02:00:00+08:00'
    use={loc['record_id']:{'supported':True}}
    assert a.raw_projection([loc],use)[0]['published_at']is None
    loc['source']['publication_basis']='source timestamp'
    assert a.raw_projection([loc],use)[0]['published_at']==loc['source']['published_at']


@pytest.mark.parametrize('supported',[True,False])
def test_exact_source_use_binding(supported):
    loc,_=records();member={'record':deepcopy(loc),'eligibility':{'source_use':True}}
    assert a.source_use(loc,member,supported)['supported']is supported
    member['record']['passage_end']-=1
    assert not a.source_use(loc,member,True)['supported']


def test_stale_capture_terms_need_exact_qualified_scope_not_blanket_inheritance():
    loc,_=records();loc['source']['reuse_terms']='not verified';member={'record':deepcopy(loc),'eligibility':{'source_use':True}}
    assert not a.source_use(loc,member,True)['supported']
    proof={'scope':'private_owner_only_academic_training_evaluation','record_id':loc['record_id'],
           'source_sha256':loc['source']['text_sha256'],'text_sha256':loc['text_sha256'],
           'start':loc['passage_start'],'end':loc['passage_end'],'verified':True}
    assert a.source_use(loc,member,True,proof)['supported']
    proof['end']-=1
    assert not a.source_use(loc,member,True,proof)['supported']


def test_repeated_unicode_mentions_are_not_first_occurrence_relocated():
    text='🌧 knee-deep. knee-deep.'
    assert a.phrase_candidates(text,'knee-deep',[0,len(text)])==[[2,11],[13,22]]
    assert a.phrase_candidates(text,'knee-deep',[13,len(text)])==[[13,22]]
    assert a.phrase_candidates(text,'2 PM',[13,len(text)])==[]


@pytest.mark.parametrize('role',['observation','onset','clearance','recession','unspecified'])
def test_time_roles_and_collective_depth_preserved(role):
    _,ref=records();ref['facts'][1]['temporal_role']=role;ref['facts'][0]['depth_scope']='range'
    tags=a.reference_phenomena(ref)
    assert 'time_'+role in tags and 'depth_range'in tags


def test_shared_time_does_not_automatically_prove_shared_depth():
    _,ref=records();ref['relations'][1]['scope']='shared';ref['relations'][1]['target_entity_ids'].append('another-road')
    assert 'shared_time'in a.reference_phenomena(ref)and 'shared_depth'not in a.reference_phenomena(ref)


@pytest.mark.parametrize('status',['forecast','negated','historical','subsided','receding'])
def test_status_categories_not_collapsed(status):
    _,ref=records();ref['facts'].append({'id':'s','kind':'status','value':status})
    assert 'status_'+status in a.reference_phenomena(ref)


def test_missing_or_incomplete_reference_cannot_be_scored():
    _,ref=records()
    with pytest.raises(ValueError):a.compare_context(ref,{'claims':[]},{'supported':False})
    result=a.compare_context(ref,{'claims':[]},{'supported':True})
    assert result['DEPTH']['reference_spans']==1 and result['relationships_scored']is False
    assert 'precision'not in result['DEPTH']and 'recall'not in result['DEPTH']


def test_worker_import_guard_blocks_neural_network_and_database(tmp_path):
    backend=Path(__file__).resolve().parents[1]
    code='''import sys,socket,json
sys.path.insert(0,sys.argv[1])
from training.flood_ner.context_gap_worker import NoNeural
from training.flood_ner.corrected_rules_worker import install_guards
sys.meta_path.insert(0,NoNeural());install_guards()
for module in ['spacy','torch','psycopg']:
 try:__import__(module)
 except RuntimeError:pass
 else:raise AssertionError('forbidden import')
try:socket.getaddrinfo('example.invalid',443)
except RuntimeError:pass
else:raise AssertionError('network permitted')
from app.core.database import engine
try:engine.connect()
except RuntimeError:pass
else:raise AssertionError('database permitted')
print(json.dumps({'guards':'passed'}))
'''
    result=subprocess.run([sys.executable,'-I','-B','-c',code,str(backend)],cwd=tmp_path,capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_no_model_or_reference_mounts(tmp_path):
    mounts={target:(tmp_path,target!='/output')for target in{'/input','/output',*('/code/'+n for n in r.WORKER_FILES)}}
    args=r.container_args('docker','sha256:'+'a'*64,'lanes-context-gap-'+'b'*16,mounts,'c'*64)
    assert '--read-only'in args and args[args.index('--network')+1]=='none'
    assert not any('/assets'in x or '/model'in x for x in args)
    mounts['/references']=(tmp_path,True)
    with pytest.raises(ValueError):r.container_args('docker','sha256:'+'a'*64,'lanes-context-gap-'+'b'*16,mounts,'c'*64)


def test_stale_grant_and_existing_destination_rejected(tmp_path):
    path=tmp_path/'grant.json';path.write_text('{}')
    with pytest.raises(ValueError):r.preflight(tmp_path,path,'0'*64)
    with pytest.raises(ValueError):r.preflight(tmp_path,path,a.digest(path))
    with pytest.raises(ValueError):r.q.private_destination(tmp_path,tmp_path)


@pytest.fixture
def grant(tmp_path,monkeypatch):
    def bound(name,value):
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value),encoding='utf-8')
        return {'path':name,'sha256':a.digest(p)}
    for name in r.IMPLEMENTATION:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture',encoding='utf-8')
    test='backend/tests/test_flood_ner_context_gap_audit.py';p=tmp_path/test;p.parent.mkdir(parents=True);p.write_text('fixture')
    implementation={n:a.digest(tmp_path/n)for n in r.IMPLEMENTATION};tests={test:a.digest(p)}
    raw_receipt=bound('tests.json',{'returncode':0,'output_complete':True,'args':[test]})
    test_binding=bound('test-binding.json',{'implementation':implementation,'tests':tests,'raw_receipt':raw_receipt})
    row={'record_id':'fictional','text':'Aster Road','text_sha256':a.text_hash('Aster Road'),'published_at':None}
    image='sha256:'+'a'*64
    request={'schema':'lanes-context-gap-worker-v32','rows':[row],
      'implementation':{n:implementation['backend/'+n]for n in r.WORKER_FILES},'files':{'runtime_data/fictional.csv':'b'*64}}
    monkeypatch.setattr(r,'rules_files',lambda root:request['files'])
    value={'schema':'lanes-context-gap-grant-v32','implementation':implementation,'tests':tests,'test_receipt':test_binding,
           'request':bound('request.json',request),'eligibility':bound('eligibility.json',[{'record_id':'fictional','text_sha256':row['text_sha256'],'supported':True}]),
           'image_id':image,'qualification':bound('qualification.json',{'image_id':image,'status':'offline_comparison_completed'})}
    b=bound('grant.json',value)
    return tmp_path,tmp_path/'grant.json',value


def test_bound_preflight_is_read_only(grant,monkeypatch):
    root,path,g=grant;before={p.relative_to(root).as_posix()for p in root.rglob('*')}
    monkeypatch.setattr(r.q,'command',lambda *args:pytest.fail('process dispatch'))
    assert r.preflight(root,path,a.digest(path))[1]['rows'][0]['text']=='Aster Road'
    assert before=={p.relative_to(root).as_posix()for p in root.rglob('*')}


@pytest.mark.parametrize('damage',['missing_code','stale_test','test_failure','source_use','source_text','neural_fields','wrong_image'])
def test_preflight_rejects_tampering_and_unqualified_inputs(grant,damage):
    root,path,g=grant
    if damage=='missing_code':g['implementation'].pop(next(iter(g['implementation'])))
    elif damage=='stale_test':(root/'backend/tests/test_flood_ner_context_gap_audit.py').write_text('changed')
    elif damage=='wrong_image':g['image_id']='sha256:'+'0'*64
    elif damage=='test_failure':
        p=root/'tests.json';v=json.loads(p.read_text());v['returncode']=1;p.write_text(json.dumps(v))
        b=root/'test-binding.json';v=json.loads(b.read_text());v['raw_receipt']['sha256']=a.digest(p);b.write_text(json.dumps(v));g['test_receipt']['sha256']=a.digest(b)
    elif damage in('source_use','source_text'):
        p=root/'eligibility.json';v=json.loads(p.read_text())
        if damage=='source_use':v[0]['supported']=False
        else:v[0]['text_sha256']='0'*64
        p.write_text(json.dumps(v));g['eligibility']['sha256']=a.digest(p)
    else:
        p=root/'request.json';v=json.loads(p.read_text());v['rows'][0]['prediction']=[];p.write_text(json.dumps(v));g['request']['sha256']=a.digest(p)
    path.write_text(json.dumps(g))
    with pytest.raises(ValueError):r.preflight(root,path,a.digest(path))
