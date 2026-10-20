"""Prepare/build/execute/verify one C3a local attempt. No cloud operations."""
from __future__ import annotations

import argparse
from datetime import datetime
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2];BACKEND=ROOT/'backend';ART=BACKEND/'training/flood_ner/artifacts'
QUALIFIED=ART/'rss-ner-runtime-phase-b-3g-20261020-v1'
QUALIFIED_SHA='8b079765472409592b99e4d2f380c95b3846ad799aa5ef437b6db46857c7d488'
sys.path.insert(0,str(BACKEND))
from app.services.news_ner.bundle import digest
from app.services.news_ner.contract import object_sha


def read(path: Path) -> object:return json.loads(path.read_text(encoding='utf-8'))
def write(path: Path,value: object) -> None:
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,allow_nan=False,indent=2)
def command(task: Path,name: str,args: list[str],timeout: int=180) -> int:
    with (task/(name+'-stdout.bin')).open('xb') as out,(task/(name+'-stderr.bin')).open('xb') as err:
        result=subprocess.run(args,stdout=out,stderr=err,timeout=timeout)
    write(task/(name+'-exit.json'),{'exit_code':result.returncode});return result.returncode


def prepare(task: Path) -> dict:
    assert digest(QUALIFIED/'final-package-manifest.json')==QUALIFIED_SHA
    old=read(QUALIFIED/'final-package-manifest.json')['files']
    for name in ('image.id','input/workload.json','input/request.json','output/responses.jsonl'):
        assert digest(QUALIFIED/name)==old[name]
    image=(QUALIFIED/'image.id').read_text().strip()
    inspected=json.loads(subprocess.run(['docker','image','inspect',image],capture_output=True,text=True,check=True).stdout)[0]
    assert inspected['Id']==image and inspected['Os']=='linux' and inspected['Architecture']=='amd64'
    for name in ('app.services.news_ner_durable.processing','app.services.news_ner_durable.capture',
                 'app.services.news_ner_durable.source_check','app.services.news_saved_run_service'):
        importlib.import_module(name)
    from app.services.news_ner_durable.assets import normalizer_bindings
    from app.services.news_ner_runtime.protocol import code_bindings
    app_files=set()
    for module in tuple(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.is_relative_to(BACKEND/'app') and path.suffix=='.py':app_files.add(path)
    for name in normalizer_bindings():app_files.add(BACKEND/'app'/name)
    for name in code_bindings(BACKEND/'app/services'):app_files.add(BACKEND/'app/services'/name)
    for path in tuple(app_files):
        for parent in path.parents:
            if not parent.is_relative_to(BACKEND/'app'):break
            if (parent/'__init__.py').exists():app_files.add(parent/'__init__.py')
    context=task/'context';context.mkdir();bindings={}
    for path in sorted(app_files):
        target=context/path.relative_to(BACKEND);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
        bindings[path.relative_to(ROOT).as_posix()]=digest(path)
    for name in ('run_news_ner_processing.py','news_ner_c3a_acceptance.py','news_ner_runtime_faults.py'):
        path=BACKEND/'scripts'/name;target=context/'scripts'/name;target.parent.mkdir(exist_ok=True);shutil.copyfile(path,target)
        bindings[path.relative_to(ROOT).as_posix()]=digest(path)
    shutil.copyfile(BACKEND/'app/news_sources.json',context/'app/news_sources.json')
    (context/'data').mkdir()
    for name in ('philippines_psgc_reference.csv','pasig_barangay_reference.csv'):
        shutil.copyfile(ROOT/'data'/name,context/'data'/name);bindings['data/'+name]=digest(ROOT/'data'/name)
    bindings['backend/app/news_sources.json']=digest(BACKEND/'app/news_sources.json')
    tag='lanes-c3a-qualified-base:'+read(task/'private-postgis-state.json')['owner'][:10]
    existing=subprocess.run(['docker','image','inspect',tag],capture_output=True,text=True)
    if existing.returncode==0:assert json.loads(existing.stdout)[0]['Id']==image
    subprocess.run(['docker','image','tag',image,tag],capture_output=True,check=True)
    (context/'Dockerfile').write_text('FROM '+tag+'\nCOPY app/ /app/app/\nCOPY scripts/ /app/scripts/\nCOPY data/ /data/\n',encoding='utf-8')
    original=read(QUALIFIED/'input/request.json');assert code_bindings(BACKEND/'app/services')==original['code']
    inputs=task/'input';inputs.mkdir()
    write(inputs/'request.json',{'bundle_sha256':original['bundle_sha256'],'worker_code_sha256':object_sha(original['code']),
                               'normalizer_bindings':normalizer_bindings()})
    rows=read(QUALIFIED/'input/workload.json')['rows'];responses=[json.loads(s) for s in (QUALIFIED/'output/responses.jsonl').read_text(encoding='utf-8').splitlines()]
    selected=[i for i,row in enumerate(rows) if row['kind'] in ('article','stress','reviewed')]
    assert len(selected)==10
    write(inputs/'workload.json',{'rows':[rows[i] for i in selected]})
    write(task/'expected-private.json',{'rows':[responses[i] for i in selected]})
    for name in ('qualify_news_ner_c3a.py','run_news_ner_processing.py','news_ner_c3a_acceptance.py'):
        path=BACKEND/'scripts'/name;bindings[path.relative_to(ROOT).as_posix()]=digest(path)
    for name in ('test_news_ner_processing.py','test_news_ner_method_boundary.py','test_news_ner_method_postgres.py'):
        path=BACKEND/'tests'/name;bindings[path.relative_to(ROOT).as_posix()]=digest(path)
    for name in bindings:
        target=task/'source-snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    write(task/'freeze.json',{'schema':'lanes-c3a-acceptance-v1','qualified_manifest_sha256':QUALIFIED_SHA,
        'base_image':image,'base_tag':tag,'bindings':bindings,'context':{p.relative_to(context).as_posix():digest(p) for p in context.rglob('*') if p.is_file()},
        'inputs':{p.name:digest(p) for p in inputs.iterdir()},'expected_private_sha256':digest(task/'expected-private.json'),
        'limits':{'cpus':1,'memory':3*1024**3,'memory_swap':3*1024**3,'headroom':2688*1024**2,'job_seconds':450,'article_seconds':125},
        'counts':{'article':6,'reviewed':1,'stress':3},'neural_attempts_allowed':1,'expected_predictions_mounted':False})
    return {'status':'prepared','freeze_sha256':digest(task/'freeze.json'),'source_files':len(bindings)}


def check(task: Path) -> dict:
    frozen=read(task/'freeze.json')
    for name,expected in frozen['bindings'].items():assert digest(ROOT/name)==expected,name
    for name,expected in frozen['context'].items():assert digest(task/'context'/name)==expected,name
    for name,expected in frozen['inputs'].items():assert digest(task/'input'/name)==expected,name
    assert digest(task/'expected-private.json')==frozen['expected_private_sha256']
    return frozen


def create(task: Path,suffix: str,image: str,operation: str) -> str:
    state=read(task/'private-postgis-state.json');name='lanes-c3a-'+state['owner'][:10]+'-'+suffix
    output=task/('output-'+suffix);output.mkdir()
    args=['docker','create','--name',name,'--init','--label','lanes.c3a.owner='+state['owner'],'--network',state['network'],
          '--cpus','1','--memory','3g','--memory-swap','3g','--pids-limit','128','--read-only','--cap-drop','ALL',
          '--security-opt','no-new-privileges','--tmpfs','/tmp:rw,noexec,nosuid,size=67108864','--workdir','/tmp',
          '--env-file',str(task/'private-worker.env'),'--mount',f'type=bind,src={task / "input"},dst=/input,readonly',
          '--mount',f'type=bind,src={output},dst=/output',image,'python','-I','-B',
          '/app/scripts/news_ner_runtime_faults.py' if operation=='faults' else '/app/scripts/news_ner_c3a_acceptance.py']
    if operation!='faults':args.append(operation)
    assert command(task,suffix+'-create',args)==0
    return name


def build(task: Path) -> dict:
    frozen=check(task)
    assert json.loads(subprocess.run(['docker','image','inspect',frozen['base_tag']],capture_output=True,text=True,check=True).stdout)[0]['Id']==frozen['base_image']
    assert command(task,'build',['docker','build','--pull=false','--network=none','--iidfile',str(task/'image.id'),str(task/'context')],300)==0
    image=(task/'image.id').read_text().strip();state=read(task/'private-postgis-state.json')
    (task/'private-worker.env').write_text('ENVIRONMENT=test\nLANES_NEWS_AUDITOR_BATCH_SIZE=8\nDATABASE_URL='+state['internal_database_url']+'\n',encoding='utf-8')
    for suffix,operation in (('preflight','preflight'),('faults','faults')):
        name=create(task,suffix,image,operation)
        assert command(task,suffix+'-run',['docker','start','-a',name],120)==0
        assert command(task,suffix+'-inspect',['docker','inspect',name])==0
    write(task/'build-ready.json',{'image':image,'freeze_sha256':digest(task/'freeze.json'),'preflight':read(task/'output-preflight/preflight.json')})
    return {'status':'built_preflight_and_fictional_faults_passed'}


def execute(task: Path) -> dict:
    check(task);ready=read(task/'build-ready.json');assert ready['freeze_sha256']==digest(task/'freeze.json')
    tests=ET.parse(task/'checks3.xml').getroot();assert not any(e.tag in ('failure','error','skipped') for e in tests.iter())
    assert read(task/'checks3-exit.json')['exit_code']==0
    state=read(task/'private-postgis-state.json');db=json.loads(subprocess.run(['docker','inspect',state['container_id']],capture_output=True,text=True,check=True).stdout)[0]
    assert db['Config']['Labels']['lanes.c3a.owner']==state['owner']
    assert command(task,'db-detach-bridge',['docker','network','disconnect','bridge',state['container_id']])==0
    write(ART/'rss-ner-c3a-integration.claim.json',{'attempts':1,'freeze_sha256':digest(task/'freeze.json'),'destination':task.name})
    write(task/'attempt.json',{'attempts':1,'freeze_sha256':digest(task/'freeze.json'),'image':ready['image'],'tests_sha256':digest(task/'checks3.xml')})
    name=create(task,'integration',ready['image'],'execute')
    try:code=command(task,'integration-run',['docker','start','-a',name],480)
    except subprocess.TimeoutExpired:
        command(task,'integration-guard-kill',['docker','kill',name]);code=2
        write(task/'guard-failure.json',{'code':'integration_deadline','retry':False})
    command(task,'integration-inspect',['docker','inspect',name])
    return {'status':'integration_completed_verification_required' if code==0 else 'integration_failed','retry':False}


def verify(task: Path) -> dict:
    check(task)
    from types import SimpleNamespace
    from app.services.news_ner_durable.assets import load_trusted_assets
    from app.services.news_ner_durable.contracts import RunEvidence
    from app.services.news_ner_durable.adapter import verify_saved_result
    request=read(task/'input/request.json');trusted=load_trusted_assets(ART/'ner-preview-bundle-20261019-v1',request['bundle_sha256'],expected_worker_code_sha256=request['worker_code_sha256'])
    output=task/'output-integration';summary=read(output/'summary.json');history=read(output/'saved-history.json');expected=read(task/'expected-private.json')['rows']
    assert read(task/'integration-run-exit.json')['exit_code']==0 and len(history)==len(expected)==10
    predictions=0
    for saved,oracle in zip(history,expected):
        run=SimpleNamespace(**saved['run']);version=SimpleNamespace(**saved['version']);result=verify_saved_result(RunEvidence.from_records(run,version),run.result,trusted)
        actual=[[m.start,m.end,m.label] for m in result.native.neural_mentions]
        wanted=[[m['start'],m['end'],m['label']] for m in oracle['result']['proposal']['neural_mentions']]
        assert actual==wanted;predictions+=len(actual)
        # Original saved predictions supply the independent pure-adapter oracle.
        from copy import deepcopy
        from app.services.news_ner.location_pipeline import from_neural_mentions
        from app.services.news_ner_durable.adapter import build_native_result
        context=RunEvidence.from_records(run,version);raw=context.source().runtime_request(context.input_fingerprint)
        pure=from_neural_mentions({**raw,'mentions':deepcopy(oracle['result']['proposal']['neural_mentions'])})
        projected=build_native_result(context,{**pure,'provenance':oracle['result']['provenance'],'measurements':result.measurements},trusted,extracted_at=result.extracted_at)
        assert projected.model_dump(mode='json',by_alias=True)==run.result
    processing=read(output/'processing.json');metrics=read(output/'metrics-complete.json')
    assert metrics['model_starts']==metrics['model_reaps']==1 and metrics['neural_requests']==10
    assert metrics['isolation']['raw_socket_denied'] and metrics['isolation']['parent_death_signal']
    assert metrics['worker_seconds']<=450 and metrics['cgroup_memory_peak_bytes']<2688*1024**2
    assert max(r['operation_seconds'] for r in processing['runs'])<=125 and metrics['cleanup_seconds']<=5 and metrics['cold_seconds']<=60
    assert max(r['seconds'] for r in metrics['requests'])<=60
    result={**summary,'predictions_matched':predictions,'reviewed_predictions_matched':len(history[-1]['run']['result']['native']['neural_mentions']),
        'memory_peak_bytes':metrics['cgroup_memory_peak_bytes'],'worker_seconds':metrics['worker_seconds'],
        'maximum_operation_seconds':max(r['operation_seconds'] for r in processing['runs']),
        'cleanup_seconds':metrics['cleanup_seconds'],'prediction_and_graph_projection_parity':True,'independent_verification_neural_requests':0}
    assert result['reviewed_predictions_matched']==53
    write(task/'integration-verification.json',result);return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=['prepare','build','execute','verify']);parser.add_argument('--task',type=Path,required=True);args=parser.parse_args()
    task=args.task.resolve();assert task.parent==ART.resolve()
    # Scoped import configuration; never read the development/shared database.
    from sqlalchemy.engine import URL
    os.environ['ENVIRONMENT']='test';os.environ['LANES_NEWS_AUDITOR_BATCH_SIZE']='8'
    os.environ['DATABASE_URL']=URL.create('postgresql+psycopg',host='127.0.0.1',port=1,database='lanes_p3_verify_import_only').render_as_string(hide_password=False)
    try:print(json.dumps(globals()[args.operation](task)))
    except Exception:
        import traceback
        write(task/(args.operation+'-private-failure.json'),{'code':'c3a_'+args.operation+'_failed','trace':traceback.format_exc()})
        print(json.dumps({'status':'failed','operation':args.operation,'retry':False}));sys.exit(2)
