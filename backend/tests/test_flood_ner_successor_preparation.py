"""Constructed admission/export/launcher controls. No private examples or network."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner import successor_preparation as prep
from training.flood_ner import successor_training as trainer
from training.flood_ner import successor_export_worker as worker
from training.flood_ner.annotation.schema import AnnotationRecord
from training.flood_ner.export import corpus_tokenizer


def metadata(key='a', partition='train', **changes):
    row = dict(record_id=key, partition=partition, group_keys=['article:' + key],
        passage_sha256=hashlib.sha256(key.encode()).hexdigest(), source_sha256=key,
        passage_start=0, passage_end=10, fitted_component=False, article_group=key,
        alternatives=[])
    row.update(changes)
    return row


@pytest.mark.parametrize('mutation,match', [
    ('fit', 'fitted'), ('same_group', 'fragmented'), ('duplicate', 'duplicate passage'),
    ('window', 'overlapping'), ('alternative', 'exclusive'), ('held', 'reuse'), ('test', 'capability')])
def test_partition_rejects_leakage_and_incompatible_members(mutation, match):
    rows = [metadata(), metadata('b', 'dev')]
    excluded = set()
    if mutation == 'fit': rows[1]['fitted_component'] = True
    if mutation == 'same_group': rows[1]['group_keys'] = rows[0]['group_keys']
    if mutation == 'duplicate': rows[1]['passage_sha256'] = rows[0]['passage_sha256']
    if mutation == 'window': rows[1]['source_sha256'] = rows[0]['source_sha256']
    if mutation == 'alternative': rows[1]['alternatives'] = ['a']
    if mutation == 'held': excluded.add('b')
    if mutation == 'test': rows[1]['partition'] = 'research_holdout'
    with pytest.raises(ValueError, match=match):
        prep.validate_partition_rows(rows, capability='development', excluded_ids=excluded)


def test_preserved_fitted_anchor_blocks_excluded_original_group():
    row = metadata(partition='dev')
    with pytest.raises(ValueError, match='fitted'):
        prep.validate_partition_rows([row], capability='development', fitted_keys={'article:a'})


def test_holdout_cap_and_development_cap_are_distinct():
    rows = [metadata(str(i), 'research_holdout', article_group='same') for i in range(4)]
    with pytest.raises(ValueError, match='cap'):
        prep.validate_partition_rows(rows, capability='research_holdout')
    for row in rows: row['partition'] = 'train'
    prep.validate_partition_rows(rows, capability='development')


def test_cross_join_groups_duplicates_overlap_and_privacy():
    a,b = metadata(),metadata('b','research_holdout')
    assert prep.cross_partition_check([a],[b])['records'] == 2
    for key,value in [('group_keys',a['group_keys']),('passage_sha256',a['passage_sha256']),
                      ('source_sha256',a['source_sha256']),('group_keys',['url:https://example.org/private'])]:
        row = {**b,key:value}
        with pytest.raises(ValueError): prep.cross_partition_check([a],[row])


def test_group_keys_hash_url_values_in_article_keys():
    result = prep.safe_group_keys(['article:https://example.org/a','url:https://example.org/a','event:a'])
    assert not any('://' in k for k in result)
    assert 'event:a' in result


def test_binding_traversal_and_stale_hash(tmp_path):
    path = tmp_path/'evidence.json'
    path.write_text('{}',encoding='utf-8')
    value = prep.binding(tmp_path,path)
    assert prep.verify_binding(tmp_path,value) == path
    path.write_text('{"changed":true}',encoding='utf-8')
    with pytest.raises(ValueError,match='stale'): prep.verify_binding(tmp_path,value)
    for path in ['../elsewhere','C:/outside']:
        with pytest.raises(ValueError): prep.inside(tmp_path,path)


@pytest.fixture
def normalized(tmp_path):
    text = 'Élan City flooded.'
    raw = tmp_path/'raw.html'; raw.write_bytes(b'constructed html')
    review = tmp_path/'review.json'; review.write_text('{"reviewed":true}',encoding='utf-8')
    h = lambda x:hashlib.sha256(x.encode()).hexdigest()
    record = dict(record_id='constructed-a',annotation_profile='location-only-v1',
        source=dict(source_id='constructed-source',url='https://example.org/constructed',
            publisher='Constructed test publisher',text=text,text_sha256=h(text),capture_version='test',
            article_group='a',event_group='event-a',syndication_group='syndication-a',
            published_at='2025-01-01T00:00:00Z',reuse_terms='Constructed test only',
            extraction_method='test',raw_sha256=prep.digest(raw)),
        passage_language='english',passage_start=0,passage_end=len(text),text=text,text_sha256=h(text),
        entities=[dict(id='e1',start=0,end=9,text='Élan City',label='CITY')],
        annotation_revision='test',quality='silver',teacher='test',reviewer='test',complete=True)
    return {'schema':'lanes-successor-input-v1','capability':'development',
        'historical_anchor_count':280,
        'members':[dict(record=record,partition='train',pool_kind='reviewed_additional',
            eligibility={k:True for k in prep.GATES},
            evidence={k:[prep.binding(tmp_path,review)] for k in prep.GATES},
            raw_binding=prep.binding(tmp_path,raw),fitted_component=False)],
        'historical_fitted_group_keys':[],'historical_nontraining_record_ids':[],'excluded_record_ids':[]}


def test_normalize_preserves_source_unicode_and_scoped_admission(tmp_path,normalized):
    original = deepcopy(normalized)
    records,*_ = prep.normalize(tmp_path,normalized,corpus_tokenizer())
    record = records[0][0]
    assert record.source.admission_status == 'training_admitted'
    assert record.source.reuse_status == 'allowed' and record.split == 'train'
    assert record.entities[0].text == 'Élan City'
    assert normalized == original


@pytest.mark.parametrize('mutation',['missing','incomplete','source_use','historical','raw','span','unknown_pool','repeated'])
def test_normalize_rejects_substantive_failure(tmp_path,normalized,mutation):
    bundle = deepcopy(normalized); member=bundle['members'][0]; record=member['record']
    if mutation=='missing': record.pop('entities')
    if mutation=='incomplete': record['complete']=False
    if mutation=='source_use': member['eligibility']['source_use']=False
    if mutation=='historical': bundle['historical_nontraining_record_ids']=[record['record_id']]
    if mutation=='raw': member['raw_binding']['sha256']='0'*64
    if mutation=='span': record['entities'][0]['end']=8
    if mutation=='unknown_pool': member['pool_kind']='historical_validation'
    if mutation=='repeated':
        record['text'] += ' Élan City recovered.'
        record['text_sha256']=hashlib.sha256(record['text'].encode()).hexdigest()
        record['passage_end']=len(record['text'])
        record['source']['text']=record['text'];record['source']['text_sha256']=record['text_sha256']
    with pytest.raises(ValueError): prep.normalize(tmp_path,bundle,corpus_tokenizer())


def test_worker_roundtrip_and_capability(tmp_path,normalized):
    nlp = corpus_tokenizer()
    records,*_ = prep.normalize(tmp_path,normalized,nlp)
    # Serializer receives only the partitions its capability is allowed to export.
    with pytest.raises(ValueError,match='forbidden'):
        worker.serialize(records,nlp.tokenizer,nlp.tokenizer.to_bytes(exclude=['vocab']),tmp_path,'research_holdout')
    record=records[0][0]
    from spacy.tokens import DocBin
    out=tmp_path/'out';out.mkdir()
    copied=record.model_copy(update={'record_id':'constructed-b','split':'dev'})
    files=worker.serialize(records+[(copied,'dev')],nlp.tokenizer,nlp.tokenizer.to_bytes(exclude=['vocab']),out,'development')
    assert set(files)=={'train.spacy','dev.spacy','tokenizer.bin','admitted-records.jsonl'}
    assert len(list(DocBin().from_disk(out/'train.spacy').get_docs(nlp.vocab)))==1
    assert not (out/'research-holdout.spacy').exists()
    with pytest.raises(FileExistsError):
        worker.serialize(records+[(copied,'dev')],nlp.tokenizer,nlp.tokenizer.to_bytes(exclude=['vocab']),out,'development')


def test_failed_tokenizer_reload_before_output(tmp_path,normalized):
    nlp=corpus_tokenizer();records,*_=prep.normalize(tmp_path,normalized,nlp)
    with pytest.raises(ValueError,match='reload'):
        worker.serialize(records,nlp.tokenizer,b'wrong',tmp_path,'development')
    assert not (tmp_path/'tokenizer.bin').exists()


def test_privacy_rejects_even_plausible_extra_fields():
    for field in ('url','title','candidate_ids','text','entities','record_id'):
        with pytest.raises(ValueError,match='unsafe'):
            prep.safe_status({field:'private'})


def test_launcher_readonly_no_process_training_or_output(tmp_path,monkeypatch):
    called=[]
    monkeypatch.setattr(trainer,'verify_package',lambda *a:{'counts':{'train':345,'dev':60}})
    monkeypatch.setattr(trainer,'probe',lambda *a,**k:called.append(k) or {'python_version':'3.11.17','spacy_version':'3.7.5'})
    monkeypatch.setattr(trainer,'validate_runtime_configs',lambda *a:{'state':'configuration_schema_verified'})
    before=list(tmp_path.rglob('*'))
    status=trainer.launch(tmp_path,tmp_path,tmp_path/'python.exe',tmp_path)
    assert status['training_started'] is False and called==[{'gpu':False}]
    assert list(tmp_path.rglob('*'))==before
    with pytest.raises(ValueError): trainer.launch(tmp_path,tmp_path,tmp_path/'py',tmp_path,seed=0)


def test_launcher_missing_gpu_never_creates_run(tmp_path,monkeypatch):
    monkeypatch.setattr(trainer,'verify_package',lambda *a:{'counts':{'train':345,'dev':60}})
    monkeypatch.setattr(trainer,'probe',lambda *a,**k: (_ for _ in ()).throw(ValueError('missing GPU')))
    output=tmp_path/'backend/training/flood_ner/artifacts/new-run'
    with pytest.raises(ValueError,match='GPU'):
        trainer.launch(tmp_path,tmp_path,tmp_path/'python',tmp_path,start=True,seed=0,output=output)
    assert not output.exists()


def test_probe_has_zero_training_or_pipeline_calls_and_disables_isolation_leaks(tmp_path,monkeypatch):
    calls=[]
    def fake_run(args,**kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=0,stdout='{"python_version":"3.11.17","spacy_version":"3.7.5"}')
    monkeypatch.setattr(trainer.subprocess,'run',fake_run)
    trainer.probe(tmp_path/'python')
    assert calls[0][1:4]==['-I','-B','-c']
    assert not any(word in calls[0][-1] for word in ('spacy.load','nlp(','cli.train'))


def test_render_portable_paths_without_shell_or_unresolved_tokens():
    template='\n'.join('"@@'+k+'@@"' for k in trainer.TOKENS)
    rendered=trainer.render_config(template,{k:'D:\\Folder With Spaces\\a' for k in trainer.TOKENS})
    assert '@@' not in rendered and 'D:\\\\Folder With Spaces\\\\a' in rendered


def test_wrong_gpu_qualification_and_runtime(tmp_path):
    prep.write_new(tmp_path/'gpu-qualification.json',{'state':'passed','gpu_environment_qualified':True,
        'model_revision':'51a40433059d8a2c25b98a48eca854f8789a491a'})
    prep.write_new(tmp_path/'gpu-runtime.json',{'gpu_name':'Fixture GPU'})
    with pytest.raises(ValueError,match='differs'): trainer.verify_gpu(tmp_path,{'gpu_name':'Different GPU'})


def test_stale_grant_cannot_start_worker(tmp_path,monkeypatch):
    path=tmp_path/'grant.json';prep.write_new(path,{'schema':'review-only'})
    monkeypatch.setattr(prep.subprocess,'run',lambda *a,**k:pytest.fail('must not dispatch'))
    with pytest.raises(ValueError,match='grant'): prep.prepare(tmp_path,path,tmp_path/'py',tmp_path/'new')
    assert not (tmp_path/'new').exists()


@pytest.fixture
def grant(tmp_path,monkeypatch):
    def put(name,value):
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True)
        prep.write_new(path,value)
        return prep.binding(tmp_path,path)
    protocol=put('protocol.json',{'documented_limitations':True})
    auth=put('task.json',dict(schema='lanes-successor-task-authorization-v1',scope=prep.SCOPE,
        network_allowed=False,training_allowed=False,inference_allowed=False,upload_allowed=False,
        commit_allowed=False,push_allowed=False,original_protocol=protocol,
        expected_counts={'train':345,'dev':60,'research_holdout':60},
        authorized_actions=['admit_in_new_package','freeze_grouped_partitions','serialize_and_reload']))
    implementation=[put('backend/training/flood_ner/'+name,{'constructed':name}) for name in prep.IMPLEMENTATIONS]
    test_source=put('backend/tests/test_constructed.py',{'constructed':'test'})
    tests=put('tests.json',{'implementation':implementation,'failures':0,'passed':2,'constructed_only':True,
                          'test_files':[test_source]})
    tokenizer=put('tokenizer.bin',{'constructed':'tokenizer'})
    monkeypatch.setattr(prep,'FROZEN_TOKENIZER',tokenizer['sha256'])
    model_files=[]
    for i in range(23):
        item=put('model/'+str(i),{'constructed':i})
        model_files.append({'path':str(i),'sha256':item['sha256']})
    model=put('model-manifest.json',{'revision':'51a40433059d8a2c25b98a48eca854f8789a491a','files':model_files})
    bundle=put('bundle.json',{'constructed':True})
    other=put('other-bundle.json',{'constructed':'other'})
    joined=put('join.json',{'schema':'lanes-successor-cross-partition-preflight-v1','records':465,
        'partitions':{'train':345,'dev':60,'research_holdout':60},'group_separation_verified':True,
        'input_bundles':[bundle,other]})
    return dict(schema='lanes-successor-preparation-grant-v1',scope=prep.SCOPE,capability='development',
        task_authorization=auth,protocol=protocol,implementation=implementation,test_evidence=tests,
        global_history_verified=False,accounting_verified=False,certified_fresh=False,
        bundle=bundle,cross_partition_evidence=joined,tokenizer=tokenizer,
        protected_input_manifest=put('protected.json',{}),model_manifest=model,model_directory='model',
        expected_counts={'train':345,'dev':60},historical_anchor_count=280)


@pytest.mark.parametrize('failure',['protocol','implementation','tests','test_source','tokenizer','model','bundle','counts','anchors','limits'])
def test_hash_bound_grant_rejects_stale_or_wrong_bindings(tmp_path,grant,failure):
    assert prep.verify_grant(tmp_path,grant)==tmp_path/'model'
    if failure=='protocol': grant['protocol']={**grant['protocol'],'sha256':'0'*64}
    if failure=='implementation': (tmp_path/grant['implementation'][0]['path']).write_text('changed',encoding='utf-8')
    if failure=='tests': grant['test_evidence']['sha256']='0'*64
    if failure=='test_source':(tmp_path/'backend/tests/test_constructed.py').write_text('changed',encoding='utf-8')
    if failure=='tokenizer': grant['tokenizer']['sha256']='0'*64
    if failure=='model': (tmp_path/'model/0').write_text('wrong',encoding='utf-8')
    if failure=='bundle': grant['bundle']['sha256']='0'*64
    if failure=='counts': grant['expected_counts']['train']=344
    if failure=='anchors': grant['historical_anchor_count']=279
    if failure=='limits': grant['global_history_verified']=True
    with pytest.raises(ValueError): prep.verify_grant(tmp_path,grant)


def test_existing_destination_and_consumed_grant_block_before_dispatch(tmp_path,grant,monkeypatch):
    gp=tmp_path/'grant.json';prep.write_new(gp,grant)
    existing=tmp_path/'backend/training/flood_ner/artifacts/existing';existing.mkdir(parents=True)
    monkeypatch.setattr(prep.subprocess,'run',lambda *a,**k:pytest.fail('must not dispatch'))
    with pytest.raises(ValueError,match='new output'): prep.prepare(tmp_path,gp,tmp_path/'py',existing)
    claims=tmp_path/'backend/training/flood_ner/artifacts/successor-claims';claims.mkdir(parents=True)
    (claims/(prep.digest(gp)+'.claim')).write_text('existing writer',encoding='utf-8')
    with pytest.raises(FileExistsError): prep.prepare(tmp_path,gp,tmp_path/'py',claims.parent/'new')
    assert not (claims.parent/'new').exists()


def test_failed_worker_keeps_consumed_claim(tmp_path,grant,monkeypatch):
    gp=tmp_path/'grant.json';prep.write_new(gp,grant)
    artifacts=tmp_path/'backend/training/flood_ner/artifacts';artifacts.mkdir(parents=True)
    monkeypatch.setattr(prep.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=1))
    with pytest.raises(ValueError,match='failed'): prep.prepare(tmp_path,gp,tmp_path/'py',artifacts/'new')
    with pytest.raises(FileExistsError): prep.prepare(tmp_path,gp,tmp_path/'py',artifacts/'new2')


def test_runtime_mismatch_blocks_without_cpu_fallback(tmp_path,monkeypatch):
    monkeypatch.setattr(trainer.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,
        stdout='{"python_version":"3.12.1","spacy_version":"3.8.0"}'))
    with pytest.raises(ValueError,match='3.11'):trainer.probe(tmp_path/'python',gpu=True)


def test_calendar_date_projection_requires_exact_saved_basis():
    printed='July 16, 2025 | 12:00am'
    assert prep.publication_day_projection(printed,'Header '+printed+' Body')=='2025-07-16T00:00:00+00:00'
    with pytest.raises(ValueError):prep.publication_day_projection(printed,'No date')
    with pytest.raises(ValueError):prep.publication_day_projection('maybe 2025','maybe 2025')


def test_capability_rejects_foreign_references_before_reading_them(tmp_path,normalized):
    normalized['members']=[{'partition':'research_holdout','record':'must never parse'}]
    with pytest.raises(ValueError,match='capability'):prep.normalize(tmp_path,normalized,corpus_tokenizer())


@pytest.fixture
def trainer_payload(tmp_path,monkeypatch):
    payload=tmp_path/'payload';payload.mkdir();model=tmp_path/'model';model.mkdir()
    rows=[]
    for i in range(23):
        path=model/str(i);path.write_bytes(('constructed '+str(i)).encode())
        rows.append({'path':str(i),'bytes':path.stat().st_size,'sha256':prep.digest(path)})
    for name in trainer.PAYLOAD_FILES:
        (payload/name).write_text('{}',encoding='utf-8')
    (payload/'model-contract.json').write_text(json.dumps({'revision':'51a40433059d8a2c25b98a48eca854f8789a491a',
        'version':'0.1.0','files':rows}),encoding='utf-8')
    q={'capability':'development','counts':{'train':345,'dev':60},'serialization_reload_verified':True,
       'files':{name:prep.digest(payload/name) for name in ['train.spacy','dev.spacy','tokenizer.bin']}}
    (payload/'qualification.json').write_text(json.dumps(q),encoding='utf-8')
    (payload/'evaluation-contract.json').write_text(json.dumps({'scope':prep.SCOPE,'certified_fresh':False,
        'human_gold':False}),encoding='utf-8')
    prep.write_new(payload/'handoff-manifest.json',{'schema':'lanes-successor-training-handoff-v1',
        'counts':q['counts'],'training_started':False,'implementation':_constructed_implementations(tmp_path),
        'files':{name:prep.digest(payload/name) for name in trainer.PAYLOAD_FILES}})
    monkeypatch.setattr(trainer,'verify_template',lambda *a:None)
    return tmp_path,payload,model


def _constructed_implementations(root):
    bindings=[]
    for name in (*prep.IMPLEMENTATIONS,'experiment_registry.py'):
        path=root/'backend/training/flood_ner'/name
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text('constructed fixture',encoding='utf-8')
        bindings.append(prep.binding(root,path))
    return bindings


@pytest.mark.parametrize('failure',['payload','model','extra_model','corpus_capability','qualification','limits','extra_payload'])
def test_trainer_package_rejects_changed_inputs(trainer_payload,failure):
    root,payload,model=trainer_payload
    assert trainer.verify_package(root,payload,model)['counts']=={'train':345,'dev':60}
    if failure=='payload':(payload/'train.spacy').write_bytes(b'changed')
    if failure=='model':(model/'0').write_bytes(b'changed')
    if failure=='extra_model':(model/'extra').write_bytes(b'unmanifested')
    if failure=='extra_payload':(payload/'research-holdout.spacy').write_bytes(b'must not receive this')
    if failure in ('corpus_capability','qualification','limits'):
        m=prep.read(payload/'handoff-manifest.json')
        if failure=='corpus_capability':m['files']['research-holdout.spacy']='a'*64
        if failure=='qualification':
            q=prep.read(payload/'qualification.json');q['capability']='research_holdout'
            (payload/'qualification.json').write_text(json.dumps(q),encoding='utf-8')
            m['files']['qualification.json']=prep.digest(payload/'qualification.json')
        if failure=='limits':
            q=prep.read(payload/'evaluation-contract.json');q['certified_fresh']=True
            (payload/'evaluation-contract.json').write_text(json.dumps(q),encoding='utf-8')
            m['files']['evaluation-contract.json']=prep.digest(payload/'evaluation-contract.json')
        (payload/'handoff-manifest.json').write_text(json.dumps(m),encoding='utf-8')
    with pytest.raises(ValueError):trainer.verify_package(root,payload,model)


def test_concurrent_training_rejected_before_new_output(trainer_payload,monkeypatch):
    root,payload,model=trainer_payload
    monkeypatch.setattr(trainer,'probe',lambda *a,**k:{})
    monkeypatch.setattr(trainer,'validate_runtime_configs',lambda *a:{'state':'configuration_schema_verified'})
    monkeypatch.setattr(trainer,'verify_gpu',lambda *a:None)
    artifacts=root/'backend/training/flood_ner/artifacts';artifacts.mkdir(parents=True)
    (artifacts/'successor-training-active.lock').write_text('other active writer',encoding='utf-8')
    with pytest.raises(FileExistsError):
        trainer.launch(root,payload,root/'python',model,start=True,seed=0,output=artifacts/'new')
    assert not (artifacts/'new').exists()


def test_safe_status_rejects_content_nested_in_allowed_aggregate_fields():
    value=dict(schema='lanes-successor-qualified-export-v1',scope=prep.SCOPE,capability='research_holdout',
        counts={'research_holdout':60},languages={'research_holdout':{'english':30,'taglish':30}},
        polarities={'research_holdout':{'english_positive':27,'english_negative':3,
                    'taglish_positive':27,'taglish_negative':3}},labels={'research_holdout':{'CITY':2}},
        serialization_reload_verified=True,python_version='3.11.17',spacy_version='3.7.5',
        files={n:'a'*64 for n in ['admission-ledger.json','admitted-records.jsonl','coverage.json','partitions.json',
            'source-only-join-metadata.json','tokenizer.bin','research-holdout.spacy']},
        global_history_verified=False,accounting_verified=False,certified_fresh=False,
        training_performed=False,model_predictions_performed=False,model_weights_loaded=False,
        pipeline_components_loaded=[])
    assert prep.safe_status(value)==value
    for change in ({'python_version':'https://example.org/private'},
                   {'labels':{'research_holdout':{'candidate-private':1}}},
                   {'files':{'candidate-private':'a'*64}},
                   {'languages':{'research_holdout':{'english':'private text'}}}):
        with pytest.raises(ValueError):prep.safe_status({**value,**change})


def test_coverage_is_actual_and_disallows_content(tmp_path,normalized):
    records,rows,*_=prep.normalize(tmp_path,normalized,corpus_tokenizer())
    result=prep.coverage(normalized,records,rows)
    assert result['partitions']['train']['languages']['english']['labels']['CITY']==1
    assert result['partitions']['train']['languages']['taglish']['labels']['CITY']==0
    assert result['partitions']['dev']['articles']==0
    result['partitions']['train']['themes']['candidate-private']=1
    with pytest.raises(ValueError,match='category'):prep.safe_coverage(result)


def constructed_template():
    return '''[paths]
train = "@@TRAIN@@"
dev = "@@DEV@@"
vectors = null
init_tok2vec = null
[system]
seed = 0
[nlp.tokenizer]
model_manifest = "@@MODEL_MANIFEST@@"
manifest_sha256 = "@@MODEL_MANIFEST_SHA256@@"
tokenizer_file = "@@TOKENIZER@@"
[components.ner.model]
nO = null
[corpora.train]
path = ${paths.train}
[corpora.dev]
path = ${paths.dev}
[training]
max_steps = 1000
max_epochs = 30
eval_frequency = 35
[training.batcher]
size = 8
[training.optimizer]
@optimizers = "Adam.v1"
L2 = 0.01
L2_is_weight_decay = true
[training.before_to_disk]
output = "@@CHECKPOINT@@"
[initialize.after_init]
model_manifest = "@@MODEL_MANIFEST@@"
manifest_sha256 = "@@MODEL_MANIFEST_SHA256@@"
'''


def test_full_portable_template_including_sha256_token():
    template=constructed_template()
    trainer.verify_template(template,0)
    for bad in [template.replace('@@MODEL_MANIFEST_SHA256@@','@@UNEXPECTED@@'),
                template.replace('@@DEV@@','research-holdout.spacy'),
                template.replace('seed = 0','seed = 1')]:
        with pytest.raises(ValueError):trainer.verify_template(bad,0)


@pytest.mark.parametrize('key,bad',[('L2','l2'),('L2_is_weight_decay','l2_is_weight_decay'),('nO','no')])
def test_lowercased_spacy_arguments_rejected(key,bad):
    template=constructed_template().replace(key+' =',bad+' =')
    with pytest.raises(ValueError,match='case-sensitive'):trainer.verify_template(template,0)


@pytest.mark.parametrize('seed',[0,1,2])
def test_portable_generator_preserves_case_and_recipe(seed):
    recipe=constructed_template()
    rendered=trainer.portable_template(recipe,seed)
    parsed=trainer.case_sensitive_parser(rendered)
    assert parsed['training.optimizer']['L2']=='0.01'
    assert parsed['training.optimizer']['L2_is_weight_decay']=='true'
    assert parsed['components.ner.model']['nO']=='null'
    assert parsed['system']['seed']==str(seed)
    assert 'l2' not in parsed['training.optimizer'] and 'no' not in parsed['components.ner.model']


def test_runtime_schema_failure_blocks_training_before_output(tmp_path,monkeypatch):
    monkeypatch.setattr(trainer,'verify_package',lambda *a:{'counts':{'train':345,'dev':60}})
    monkeypatch.setattr(trainer,'probe',lambda *a,**k:{'spacy_version':'3.7.5'})
    monkeypatch.setattr(trainer,'validate_runtime_configs',lambda *a:(_ for _ in ()).throw(ValueError('schema invalid')))
    monkeypatch.setattr(trainer.subprocess,'run',lambda *a,**k:pytest.fail('must not invoke training'))
    destination=tmp_path/'backend/training/flood_ner/artifacts/new-run'
    with pytest.raises(ValueError,match='schema invalid'):
        trainer.launch(tmp_path,tmp_path,tmp_path/'python',tmp_path,start=True,seed=0,output=destination)
    assert not destination.exists()


def test_runtime_config_validator_uses_pinned_process_and_surfaces_errors(tmp_path,monkeypatch):
    calls=[]
    def failed(args,**kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=1,stdout='',stderr='training.optimizer.l2: extra field')
    monkeypatch.setattr(trainer.subprocess,'run',failed)
    with pytest.raises(ValueError,match='extra field'):trainer.validate_runtime_configs(tmp_path/'python',tmp_path)
    assert calls[0][1:3]==['-I','-B'] and '--internal-config-validation' in calls[0]
    assert '--internal-training' not in calls[0]
