"""Constructed prototype/scoring/controller regressions; no private passages."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.flood_ner import context_association as engine
from training.flood_ner import context_association_scoring as score
from training.flood_ner import context_association_run as run
from training.flood_ner.context_acceptance import exact_occurrence
from training.flood_ner.context_acceptance_cases import make_case,entity,depth,time,status


def raw(text, specs, id='constructed-input'):
    return {'record_id':id,'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'publication':None,
        'mentions':[{'id':f'p{i}','label':label,'provenance_sha256':'a'*64,**exact_occurrence(text,name,n)}
                    for i,(name,label,n)in enumerate(specs)]}


def links(out,kind):
    facts={f['id']:f for f in out['facts']}
    return [(facts[r['fact_id']]['value'],r['target_entity_ids'],r['scope'])for r in out['relations']if facts[r['fact_id']]['kind']==kind]


def test_unicode_repeated_rows_preserve_distinct_occurrences_and_input():
    text='🌧 Flood report\nLily Lane: 12 cm.\nLily Lane: 28 cm.'
    x=raw(text,[('Lily Lane','ROAD',0),('Lily Lane','ROAD',1)]);before=deepcopy(x);y=engine.extract(x)
    assert x==before and y['mentions']==x['mentions']
    assert links(y,'depth')==[('12 cm',['p0'],'local'),('28 cm',['p1'],'local')]
    assert engine.extract(x)==y


def test_units_on_a_following_explicit_row_line_and_local_area():
    x=raw('Lily Court\nWater Level: 12.7cm (5 inches)\nDahlia Lane\nWater Level: 20 cm',
          [('Lily Court','LOCAL_AREA',0),('Dahlia Lane','ROAD',0)])
    y=engine.extract(x)
    assert links(y,'depth')==[('12.7cm (5 inches)',['p0'],'local'),('20 cm',['p1'],'local')]
    assert y['mentions'][0]['label']=='LOCAL_AREA'


def test_range_and_upper_bound_remain_raw_not_converted_to_scalars():
    x=raw('Lily Lane had up to 35 cm of floodwater. Dahlia Lane had 12 to 23 cm of floodwater.',
          [('Lily Lane','ROAD',0),('Dahlia Lane','ROAD',0)])
    y=engine.extract(x);assert not y['numeric_depths']
    assert [(f['value'],f['depth_scope'])for f in y['facts']if f['kind']=='depth']==[('up to 35 cm','maximum'),('12 to 23 cm','range')]


def test_no_unmarked_shared_depth_or_nearest_antecedent_guess():
    x=raw('Lily Lane and Dahlia Lane were mentioned. Nearby water was knee-deep; the site was not identified.',
          [('Lily Lane','ROAD',0),('Dahlia Lane','ROAD',0)])
    y=engine.extract(x);assert not links(y,'depth')
    assert any(f['value']=='knee-deep'for f in y['facts'])and y['unassigned']


def test_explicit_shared_clock_does_not_share_different_depths():
    x=raw('As of 4 PM, Lily Lane had ankle-deep flooding and Dahlia Lane had chest-deep flooding.',
          [('Lily Lane','ROAD',0),('Dahlia Lane','ROAD',0)])
    y=engine.extract(x)
    assert links(y,'depth')==[('ankle-deep',['p0'],'local'),('chest-deep',['p1'],'local')]
    assert links(y,'time')==[('4 PM',['p0','p1'],'shared')]


def test_qualified_depth_survives_and_locality_parents_do_not_inherit():
    x=raw('Almost waist-deep flooding affected Lily Lane in Coral City, Verde Province.',
          [('Lily Lane','ROAD',0),('Coral City','CITY',0),('Verde Province','PROVINCE',0)])
    y=engine.extract(x);assert links(y,'depth')==[('Almost waist-deep',['p0'],'local')]
    assert any('approximate'in f['qualifiers']for f in y['facts']if f['kind']=='depth')


def test_forecast_and_negation_are_clause_local():
    x=raw('Forecasters warn Lily Lane may have knee-deep flooding tomorrow. Dahlia Lane is not flooded now.',
          [('Lily Lane','ROAD',0),('Dahlia Lane','ROAD',0)])
    y=engine.extract(x)
    assert ('forecast',['p0'],'local')in links(y,'status')
    assert ('negated',['p1'],'local')in links(y,'status')
    assert ('active',['p0'],'local')not in links(y,'status')


def test_observation_is_not_automatically_onset_and_rain_is_not_flood_onset():
    x=raw('Flooding on Lily Lane was observed at 4 PM. Rain started at 3 PM.',[('Lily Lane','ROAD',0)])
    y=engine.extract(x)
    roles=[(f['value'],f['temporal_role'])for f in y['facts']if f['kind']=='time']
    assert ('4 PM','observation')in roles and ('3 PM','unspecified')in roles
    assert not any(role=='onset'for _,role in roles)
    assert all(v!='3 PM'for v,_,_ in links(y,'time'))


def test_recession_then_explicit_clearance_keep_separate_clock_roles():
    x=raw('At 3 PM floodwater on Lily Lane was receding. At 4 PM the road was dry and cleared of floodwater.',[('Lily Lane','ROAD',0)])
    y=engine.extract(x)
    assert [(f['value'],f['temporal_role'])for f in y['facts']if f['kind']=='time']==[('3 PM','recession'),('4 PM','clearance')]
    assert ('receding',['p0'],'local')in links(y,'status')and('cleared',['p0'],'local')in links(y,'status')


def test_location_names_do_not_become_time_expressions():
    x=raw('Monday Street had knee-deep flooding.',[('Monday Street','ROAD',0)])
    y=engine.extract(x);assert not any(e['label']=='TIME'for e in y['expressions'])


@pytest.mark.parametrize('text,expected',[('The flood-control project on Lily Lane was approved.','prevention'),
    ('Lily Lane is flood-prone.','habitual')])
def test_non_observation_context_is_not_active_flooding(text,expected):
    y=engine.extract(raw(text,[('Lily Lane','ROAD',0)]))
    assert (expected,['p0'],'local')in links(y,'status')
    assert ('active',['p0'],'local')not in links(y,'status')


def test_non_depth_measurement_does_not_become_a_road_flood_depth():
    y=engine.extract(raw('Lily Lane was widened to 12 meters.',[('Lily Lane','ROAD',0)]))
    assert not links(y,'depth')and not any(e['label']=='DEPTH'for e in y['expressions'])


@pytest.mark.parametrize('label',sorted(engine.validate_raw_input.__globals__['PLACE_LABELS']))
def test_all_six_input_labels_are_preserved(label):
    x=raw('Lily Site had knee-deep flooding.',[('Lily Site',label,0)])
    assert engine.extract(x)['mentions']==x['mentions']


@pytest.mark.parametrize('damage',['reference','hash','offset','type','overlap','label','publication','missing_provenance'])
def test_input_rejects_leakage_and_malformed_spans(damage):
    x=raw('Lily Lane had knee-deep flooding.',[('Lily Lane','ROAD',0)])
    if damage=='reference':x['references']=[]
    elif damage=='hash':x['text_sha256']='0'*64
    elif damage=='offset':x['mentions'][0]['start']+=1
    elif damage=='type':x['mentions'][0]['start']=False
    elif damage=='overlap':x['mentions'].append(deepcopy(x['mentions'][0]))
    elif damage=='label':x['mentions'][0]['label']='DEPTH'
    elif damage=='publication':x['publication']={'value':'2026-10-19T04:00:00','basis':'source'}
    elif damage=='missing_provenance':x['mentions'][0]['provenance_sha256']=''
    with pytest.raises(ValueError):engine.extract(x)


def test_empty_text_and_missing_locations_do_not_trigger_fallback():
    y=engine.extract(raw('',[]));assert not y['facts']and not y['relations']
    y=engine.extract(raw('Knee-deep floodwater was observed.',[]))
    assert not y['relations']and y['unassigned']


@pytest.mark.parametrize('damage',['instant','scalar','location','expression','value','relation_target','scope','unassigned'])
def test_output_cannot_invent_values_or_escape_original_mentions(damage):
    x=raw('Lily Lane had knee-deep flooding.',[('Lily Lane','ROAD',0)]);y=engine.extract(x)
    if damage=='instant':y['absolute_instants']=['2026-10-19T04:00:00+08:00']
    elif damage=='scalar':y['numeric_depths']=[0.48]
    elif damage=='location':y['mentions'][0]['label']='CITY'
    elif damage=='expression':y['expressions'][0]['text']='waist-deep'
    elif damage=='value':y['facts'][0]['value']='invented'
    elif damage=='relation_target':y['relations'][0]['target_entity_ids']=['absent']
    elif damage=='scope':y['relations'][0]['scope']='shared'
    elif damage=='unassigned':y['unassigned']=[{'fact_id':y['facts'][0]['id'],'reason':'wrong'}]
    with pytest.raises(ValueError):engine.validate_output(x,y)


def case_record():
    text='Lily Lane had knee-deep flooding at 4 PM.'
    return make_case('separate_depth_shared_time','english','supported',text,
        [entity('p','Lily Lane'),entity('d','knee-deep','DEPTH'),entity('t','4 PM','TIME')],
        [depth('f','d'),time('ft','t','observation'),status('s','active')],
        [('f',['p'],'local'),('ft',['p'],'local'),('s',['p'],'local')],['No onset inference.'],'Constructed scoring oracle.')


def test_strict_scoring_rejects_wrong_boundary_role_and_scope():
    c=case_record();x=raw(c['record']['text'],[('Lily Lane','ROAD',0)]);y=engine.extract(x)
    r=score.reference_keys(c['record']);p=score.output_keys(y)
    assert score.strict_counts(r['links'],p['links'])['fp']==0
    bad=deepcopy(y);next(f for f in bad['facts']if f['kind']=='time')['temporal_role']='onset'
    assert score.strict_counts(r['links'],score.output_keys(bad)['links'])['fp']==1
    bad=deepcopy(y);bad['relations'][0]['scope']='collective'
    assert score.strict_counts(r['links'],score.output_keys(bad)['links'])['fp']==1
    bad=deepcopy(y);bad['expressions'][0]['end']-=1
    assert score.strict_counts(r['DEPTH'],score.output_keys(bad)['DEPTH'])['fp']==1


def test_missing_references_and_zero_support_are_not_negatives_or_perfect_scores():
    r=case_record()['record'];r['complete']=False
    with pytest.raises(ValueError):score.reference_keys(r)
    result=score.strict_counts(set(),{(1,2,'ROAD')})
    assert result['fp']==1 and result['f1']is None and result['recall']is None and not result['measured']


def baseline_raw(x,ambiguous=False):
    return {'record_id':x['record_id'],'text_sha256':x['text_sha256'],'claims':[{
        'place_type':'street','place_char_start':0,'place_char_end':9,'raw_place_name':'Lily Lane',
        'evidence_sentence_offset':[0,len(x['text'])],'evidence_sentence':x['text'],
        'place_source_exact':True,'sentence_source_exact':True,'uncertainty_reasons':[],
        'depth_raw':'knee-deep','depth_span_candidates':[[14,23],[14,23]]if ambiguous else[[14,23]],
        'event_time_raw':None,'time_span_candidates':[],'event_time_kind':'unspecified',
        'condition':'active','is_forecast':False,'is_negated':False,'is_historical':False,'road_passability':'unknown'}]}


def test_baseline_missing_provenance_remains_unscored_and_not_relocated():
    x=raw('Lily Lane had knee-deep flooding.',[('Lily Lane','ROAD',0)])
    normal=score.baseline_projection(baseline_raw(x),x)
    assert len([f for f in normal['facts']if f['kind']=='depth'])==1
    held=score.baseline_projection(baseline_raw(x,True),x)
    assert not any(f['kind']=='depth'for f in held['facts'])
    assert held['unscored'][0]['reason']=='depth_evidence_missing_or_ambiguous'


def test_scoring_and_fixture_pass_depend_on_actual_outputs_not_readiness_flags():
    c=case_record();x=raw(c['record']['text'],[('Lily Lane','ROAD',0)]);y=engine.extract(x)
    assert score.fixture_result(c,x,y)['passed']
    bad=deepcopy(y);bad['relations']=[];bad['unassigned']=[{'fact_id':f['id'],'reason':'abstain'}for f in bad['facts']]
    assert not score.fixture_result(c,x,bad)['passed']


def test_baseline_correct_target_missing_from_neural_mentions_remains_a_failure():
    c=case_record();x=raw(c['record']['text'],[('Lily Lane','ROAD',0)])
    b=score.baseline_projection(baseline_raw(x),x)
    empty=deepcopy(x);empty['mentions']=[];y=engine.extract(empty)
    reviewed=score.compare_record(c['record'],empty,b,y)
    assert reviewed['transitions']['lost_correct']
    assert reviewed['transitions']['lost_correct']==reviewed['transitions']['lost_due_to_missing_neural_target']


@pytest.mark.parametrize('damage',['missing','duplicate','hash','unexpected'])
def test_exact_output_joins_reject_incomplete_or_mismatched_results(damage):
    x=raw('Lily Lane had knee-deep flooding.',[('Lily Lane','ROAD',0)]);o=engine.extract(x);rows=[o]
    if damage=='missing':rows=[]
    elif damage=='duplicate':rows.append(deepcopy(o))
    elif damage=='hash':o['text_sha256']='0'*64
    elif damage=='unexpected':o['record_id']='other'
    with pytest.raises(ValueError):score.join_outputs([x],rows)


def test_aggregate_requires_full_counts_and_derives_failures():
    with pytest.raises(ValueError):score.aggregate([],[])
    metrics={'links':{'baseline':score.strict_counts(set(),set()),'candidate':score.strict_counts(set(),set())}}
    rows=[{'record_id':str(i),'metrics':metrics,'transitions':{'gained_correct':[],'lost_correct':[],'introduced_incorrect':[],'lost_due_to_missing_neural_target':[]},'baseline_unscored':[]}for i in range(24)]
    fixtures=[{'case_id':str(i),'passed':True}for i in range(40)]
    result=score.aggregate(rows,fixtures)
    assert result['status']=='not_qualified'and'no_demonstrated_targeted_correction'in result['blockers']
    fixtures[0]['passed']=False;rows[0]['transitions']['introduced_incorrect']=[('bad',)]
    result=score.aggregate(rows,fixtures)
    assert result['fictional_failed']==1 and result['introduced_incorrect_links']==1


def test_mounts_and_frozen_preflight_reject_stale_bindings(tmp_path):
    file=tmp_path/'grant.json';file.write_text('{}')
    with pytest.raises(ValueError):run.preflight(tmp_path,file,'0'*64)
    with pytest.raises(ValueError):run.preflight(tmp_path,file,run.digest(file))
    mounts={target:(tmp_path,target!='/output')for target in{'/input','/output',*('/code/'+n for n in run.CANDIDATE_FILES)}}
    args=run.container_args('docker','sha256:'+'a'*64,'lanes-context-candidate-'+'b'*16,mounts,'training/flood_ner/context_association_worker.py','c'*64,run.CANDIDATE_FILES)
    assert '--read-only'in args and args[args.index('--network')+1]=='none'
    assert not any('/model'in a or '/references'in a for a in args)
    mounts['/references']=(tmp_path,True)
    with pytest.raises(ValueError):run.container_args('docker','sha256:'+'a'*64,'lanes-context-candidate-'+'b'*16,mounts,'x','c'*64,run.CANDIDATE_FILES)


def test_concurrent_or_occupied_evidence_is_rejected_without_overwrite(tmp_path):
    file=tmp_path/'receipt.json';run.q.write_new(file,{'original':True})
    with pytest.raises(FileExistsError):run.q.write_new(file,{'changed':True})
    with run.q.exclusive(tmp_path/'lock',{'owner':1}):
        with pytest.raises(FileExistsError):
            with run.q.exclusive(tmp_path/'lock',{'owner':2}):pass
    assert json.loads(file.read_text())=={'original':True}


def test_candidate_import_guard_blocks_models_network_database_and_processes(tmp_path):
    backend=Path(__file__).resolve().parents[1]
    code='''import sys,socket,subprocess
sys.path[:0]=[sys.argv[1]]
from training.flood_ner.context_gap_worker import NoNeural
from training.flood_ner.corrected_rules_worker import install_guards
sys.meta_path.insert(0,NoNeural());install_guards()
from training.flood_ner.context_association import extract
for operation in [lambda:__import__('spacy'),lambda:__import__('torch'),lambda:__import__('psycopg'),lambda:socket.getaddrinfo('example.invalid',443),lambda:subprocess.run(['fictional'])]:
 try:operation()
 except RuntimeError:pass
 else:raise AssertionError('forbidden action permitted')
print('guarded prototype imported without neural libraries')
'''
    r=subprocess.run([sys.executable,'-I','-B','-c',code,str(backend)],cwd=tmp_path,capture_output=True,text=True,timeout=30)
    assert r.returncode==0,r.stderr


@pytest.fixture
def grant(tmp_path,monkeypatch):
    def binding(name,value):
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value),encoding='utf-8')
        return {'path':p.relative_to(tmp_path).as_posix(),'sha256':run.digest(p)}
    for n in run.CODE+run.TESTS:
        p=tmp_path/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('constructed binding',encoding='utf-8')
    implementation={n:run.digest(tmp_path/n)for n in run.CODE};tests={n:run.digest(tmp_path/n)for n in run.TESTS}
    raw_receipt=binding('passing-tests.json',{'returncode':0,'output_complete':True,'args':list(run.TESTS)})
    test_receipt=binding('test-binding.json',{'implementation':implementation,'tests':tests,'raw_receipt':raw_receipt})
    parent_name='backend/training/flood_ner/artifacts/context-acceptance-20261019-v33/'
    parent=[];eligible=[];base_rows=[];candidate_rows=[];uses=[]
    for i in range(26):
        id=f'constructed-{i}';opaque='train-'+hashlib.sha256(id.encode()).hexdigest()[:20]
        text='Lily Lane: 12 cm.';h=hashlib.sha256(text.encode()).hexdigest()
        source={'text_sha256':h};current={'record_id':id,'split':'train','text':text,'text_sha256':h,'source':source,'passage_start':0,'passage_end':len(text)}
        parent.append({'current':current,'review':{'disposition':'hold'if i>=24 else'retain_proposed'}})
        uses.append({'record_id':id,'verified':True,'scope':'private_owner_only_academic_training_evaluation','text_sha256':h,'source_sha256':h,'start':0,'end':len(text)})
        if i>=24:continue
        row=raw(text,[('Lily Lane','ROAD',0)],opaque);candidate_rows.append(row)
        base_rows.append({k:row[k]for k in('record_id','text','text_sha256')}|{'published_at':None})
        eligible.append({'record_id':opaque,'partition':'train','source_use_supported':True,'reference_disposition':'retain_proposed','text_sha256':h})
    for i in range(40):candidate_rows.append(raw('Fictional text.',[],f'fictional-{i}'))
    reference_bindings=[binding(parent_name+n,value)for n,value in [('references.json',parent),('fixtures.json',[]),('source-use.json',uses),('freeze.json',{})]]
    pred=binding(parent_name+'private-manifest.json',{})
    image='sha256:'+'a'*64;qualification=binding('image-qualified.json',{'status':'offline_comparison_completed','image_id':image})
    files={'runtime_data/constructed.csv':'b'*64};monkeypatch.setattr(run.old,'rules_files',lambda root:files)
    base={'schema':'lanes-context-gap-worker-v32','rows':base_rows,'implementation':{n:implementation['backend/'+n]for n in run.BASE_FILES},'files':files}
    candidate={'schema':'lanes-context-association-worker-v34','rows':candidate_rows,'implementation':{n:implementation['backend/'+n]for n in run.CANDIDATE_FILES}}
    protocol={'schema':'lanes-context-association-protocol-v34','candidate_experiments':1,
        'fictional_input_bindings':{r['record_id']:{'text_sha256':r['text_sha256'],'mentions_sha256':hashlib.sha256(json.dumps(r['mentions'],sort_keys=True,ensure_ascii=False).encode()).hexdigest()}for r in candidate_rows[24:]},
        'training_input_bindings':{r['record_id']:hashlib.sha256(json.dumps(r['mentions'],sort_keys=True,ensure_ascii=False).encode()).hexdigest()for r in candidate_rows[:24]}}
    value={'schema':'lanes-context-association-grant-v34','implementation':implementation,'tests':tests,'test_receipt':test_receipt,
        'image_id':image,'qualification':qualification,'baseline_request':binding('base.json',base),'candidate_request':binding('candidate.json',candidate),
        'eligibility':binding('eligible.json',eligible),'reference_bindings':reference_bindings,'predecessor_manifest':pred,
        'comparison_protocol':binding('protocol.json',protocol)}
    g=binding('grant.json',value)
    return tmp_path,tmp_path/'grant.json',value


def test_preflight_is_read_only_and_dispatch_free(grant,monkeypatch):
    root,path,g=grant;before={p.relative_to(root).as_posix()for p in root.rglob('*')}
    monkeypatch.setattr(run.q,'command',lambda *args:pytest.fail('unexpected process'))
    assert len(run.preflight(root,path,run.digest(path))[1]['rows'])==24
    assert before=={p.relative_to(root).as_posix()for p in root.rglob('*')}


@pytest.mark.parametrize('damage',['stale_test','wrong_image','missing_code','failed_tests','held','validation','source_use','source_hash','predictions','fixture','raw_reference'])
def test_preflight_rejects_tampering_leakage_and_stale_evidence(grant,damage):
    root,path,g=grant
    def change(binding,modify):
        p=root/binding['path'];value=json.loads(p.read_text(encoding='utf-8'));modify(value);p.write_text(json.dumps(value),encoding='utf-8');binding['sha256']=run.digest(p)
    if damage=='stale_test':(root/run.TESTS[0]).write_text('changed')
    elif damage=='wrong_image':g['image_id']='sha256:'+'0'*64
    elif damage=='missing_code':g['implementation'].pop(next(iter(g['implementation'])))
    elif damage=='failed_tests':
        b=g['test_receipt'];tb=json.loads((root/b['path']).read_text());change(tb['raw_receipt'],lambda x:x.update(returncode=1));(root/b['path']).write_text(json.dumps(tb));b['sha256']=run.digest(root/b['path'])
    elif damage in{'held','validation','source_use'}:
        field,val=('reference_disposition','hold')if damage=='held'else('partition','dev')if damage=='validation'else('source_use_supported',False)
        change(g['eligibility'],lambda x:x[0].update({field:val}))
    elif damage=='source_hash':
        b=next(b for b in g['reference_bindings']if b['path'].endswith('source-use.json'));change(b,lambda x:x[0].update(source_sha256='0'*64))
    elif damage in{'predictions','fixture','raw_reference'}:
        def mutate(v):
            if damage=='raw_reference':v['rows'][0]['reference']=[]
            elif damage=='predictions':v['rows'][0]['mentions']=[]
            else:v['rows'][24]['text']='Other.';v['rows'][24]['text_sha256']=hashlib.sha256(b'Other.').hexdigest()
        change(g['candidate_request'],mutate)
    path.write_text(json.dumps(g))
    with pytest.raises(ValueError):run.preflight(root,path,run.digest(path))
