"""Freeze/build/run/verify the one authorized local C3b integration attempt."""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
from email.utils import format_datetime
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2];BACKEND=ROOT/'backend'
ART=BACKEND/'training/flood_ner/artifacts'
sys.path.insert(0,str(BACKEND))
QUALIFIED=ART/'rss-ner-runtime-phase-b-3g-20261020-v1'
QUALIFIED_SHA='8b079765472409592b99e4d2f380c95b3846ad799aa5ef437b6db46857c7d488'


def read(path: Path):return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path,value: object) -> None:
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,allow_nan=False,indent=2)


def digest(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_sha(value: object) -> str:
    from app.services.news_ner.contract import object_sha as implementation
    return implementation(value)


def command(task: Path,name: str,args: list[str],timeout: int=180) -> int:
    with (task/(name+'-stdout.bin')).open('xb') as out,(task/(name+'-stderr.bin')).open('xb') as err:
        result=subprocess.run(args,stdout=out,stderr=err,timeout=timeout)
    write(task/(name+'-exit.json'),{'exit_code':result.returncode})
    return result.returncode


def prepare(task: Path) -> dict:
    assert not (ART/'rss-ner-c3b-integration.claim.json').exists()
    assert digest(QUALIFIED/'final-package-manifest.json')==QUALIFIED_SHA
    predecessor=read(QUALIFIED/'final-package-manifest.json')['files']
    for name in ('image.id','input/workload.json','input/request.json','output/responses.jsonl'):
        assert digest(QUALIFIED/name)==predecessor[name]
    image=(QUALIFIED/'image.id').read_text().strip()
    info=json.loads(subprocess.run(['docker','image','inspect',image],capture_output=True,text=True,check=True).stdout)[0]
    assert info['Id']==image and info['Os']=='linux' and info['Architecture']=='amd64'
    for module in ('app.services.news_ner_durable.pipeline','app.services.news_ner_durable.readers',
        'app.services.news_results_service','app.services.news_browsing_service','app.services.news_collection_service',
        'app.services.news_saved_run_service','app.crud.news_ner_results'):
        importlib.import_module(module)
    from app.services.news_ner_durable.assets import load_trusted_assets,with_placement_assets,normalizer_bindings
    from app.services.news_ner_runtime.protocol import code_bindings
    original=read(QUALIFIED/'input/request.json')
    assert code_bindings(BACKEND/'app/services')==original['code']
    trusted=with_placement_assets(load_trusted_assets(ART/'ner-preview-bundle-20261019-v1',original['bundle_sha256'],
        expected_worker_code_sha256=object_sha(original['code'])))
    files=set()
    for module in tuple(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.is_relative_to(BACKEND/'app') and path.suffix=='.py':files.add(path)
    files.update(BACKEND/'app'/name for name in normalizer_bindings())
    files.update(BACKEND/'app/services'/name for name in original['code'])
    for path in tuple(files):
        for parent in path.parents:
            if not parent.is_relative_to(BACKEND/'app'):break
            if (parent/'__init__.py').exists():files.add(parent/'__init__.py')
    context=task/'context';context.mkdir()
    bindings={}
    def copy(path: Path,relative: Path) -> None:
        dest=context/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
        bindings[path.relative_to(ROOT).as_posix()]=digest(path)
    for path in sorted(files):copy(path,path.relative_to(BACKEND))
    for name in ('news_ner_c3b_acceptance.py','run_news_ner_pipeline.py','news_ner_runtime_faults.py'):
        copy(BACKEND/'scripts'/name,Path('scripts')/name)
    copy(BACKEND/'app/news_sources.json',Path('app/news_sources.json'))
    for folder in ('osm','noah-placement','barangay-ncr'):
        for path in (BACKEND/'runtime_data'/folder).rglob('*'):
            if path.is_file() and path.suffix!='.md':copy(path,path.relative_to(BACKEND))
    for name in ('philippines_psgc_reference.csv','pasig_barangay_reference.csv','flooded_areas_pasig_clean.csv'):
        copy(ROOT/'data'/name,Path('data')/name)
    state=read(task/'private-postgis-state.json');tag='lanes-c3b-qualified-base:'+state['owner'][:10]
    subprocess.run(['docker','image','tag',image,tag],check=True,capture_output=True)
    (context/'Dockerfile').write_text('FROM '+tag+'\nCOPY app/ /app/app/\nCOPY scripts/ /app/scripts/\nCOPY runtime_data/ /app/runtime_data/\nCOPY data/ /data/\n',encoding='utf-8')
    inputs=task/'input';inputs.mkdir()
    write(inputs/'request.json',{'bundle_sha256':original['bundle_sha256'],'worker_code_sha256':object_sha(original['code']),
        'manifest':trusted.manifest,'normalizer_bindings':normalizer_bindings(),
        'publication_raw':format_datetime(datetime.now(timezone.utc))})
    rows=read(QUALIFIED/'input/workload.json')['rows']
    responses=[json.loads(line) for line in (QUALIFIED/'output/responses.jsonl').read_text(encoding='utf-8').splitlines()]
    selected=[i for i,row in enumerate(rows) if row['kind'] in ('article','reviewed','stress')]
    assert len(selected)==10
    write(inputs/'workload.json',{'rows':[rows[i] for i in selected]})
    write(task/'expected-private.json',{'rows':[responses[i] for i in selected]})
    for name in ('qualify_news_ner_c3b.py',):bindings['backend/scripts/'+name]=digest(BACKEND/'scripts'/name)
    for path in BACKEND.glob('tests/test_news_ner_*.py'):bindings[path.relative_to(ROOT).as_posix()]=digest(path)
    for name in bindings:
        target=task/'source-snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    write(task/'freeze.json',{'schema':'lanes-c3b-acceptance-v1','qualified_manifest_sha256':QUALIFIED_SHA,
        'base_image':image,'base_tag':tag,'bindings':bindings,
        'context':{p.relative_to(context).as_posix():digest(p) for p in context.rglob('*') if p.is_file()},
        'inputs':{p.name:digest(p) for p in inputs.iterdir()},'expected_private_sha256':digest(task/'expected-private.json'),
        'limits':{'cpus':1,'memory':3*1024**3,'memory_swap':3*1024**3,'headroom':2688*1024**2,
                  'invocation_seconds':580,'discovery_seconds':120,'extraction_seconds':450,'article_seconds':125,
                  'downstream_seconds':100,'final_seconds':10},
        'workload':{'rss_admissible':8,'short_rss_rejections':2,'preexisting_short_runtime_controls':2,'neural_requests':10},
        'neural_attempts_allowed':1,'expected_predictions_mounted':False})
    return {'status':'prepared','source_files':len(bindings),'freeze_sha256':digest(task/'freeze.json')}


def check(task: Path) -> dict:
    frozen=read(task/'freeze.json')
    for name,expected in frozen['bindings'].items():assert digest(ROOT/name)==expected,name
    for name,expected in frozen['context'].items():assert digest(task/'context'/name)==expected,name
    for name,expected in frozen['inputs'].items():assert digest(task/'input'/name)==expected,name
    assert digest(task/'expected-private.json')==frozen['expected_private_sha256']
    return frozen


def create(task: Path,suffix: str,operation: str) -> str:
    state=read(task/'private-postgis-state.json');image=(task/'image.id').read_text().strip()
    name='lanes-c3b-'+state['owner'][:10]+'-'+digest(task/'freeze.json')[:6]+'-'+suffix
    output=task/('output-'+suffix);output.mkdir()
    args=['docker','create','--name',name,'--init','--label','lanes.c3b.owner='+state['owner'],'--network',state['network'],
        '--cpus','1','--memory','3g','--memory-swap','3g','--pids-limit','128','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--tmpfs','/tmp:rw,noexec,nosuid,size=67108864','--workdir','/tmp',
        '--env-file',str(task/('private-preflight.env' if operation=='preflight' else 'private-worker.env')),'--mount',f'type=bind,src={task / "input"},dst=/input,readonly',
        '--mount',f'type=bind,src={output},dst=/output',image,'python','-I','-B',
        '/app/scripts/news_ner_runtime_faults.py' if operation=='faults' else '/app/scripts/news_ner_c3b_acceptance.py']
    if operation!='faults':args.append(operation)
    assert command(task,suffix+'-create',args)==0
    return name


def build(task: Path) -> dict:
    frozen=check(task)
    assert json.loads(subprocess.run(['docker','image','inspect',frozen['base_tag']],capture_output=True,text=True,check=True).stdout)[0]['Id']==frozen['base_image']
    assert command(task,'build',['docker','build','--pull=false','--network=none','--iidfile',str(task/'image.id'),str(task/'context')],300)==0
    state=read(task/'private-postgis-state.json')
    inspected=json.loads(subprocess.run(['docker','inspect',state['container_id']],capture_output=True,text=True,check=True).stdout)[0]
    assert inspected['Config']['Labels']['lanes.c3b.owner']==state['owner']
    from sqlalchemy.engine import make_url
    for suffix,envname in (('acceptance','private-worker.env'),('preflight','private-preflight.env')):
        db='lanes_p3_verify_c3b_'+suffix+'_'+digest(task/'freeze.json')[:6]
        assert command(task,'create-'+suffix+'-db',['docker','exec',state['container_id'],'createdb','-U','postgres','-T','lanes_p3_verify_c3b_publication',db])==0
        value=make_url(state['internal_database_url']).set(database=db).render_as_string(hide_password=False)
        (task/envname).write_text('ENVIRONMENT=test\nLANES_NEWS_AUDITOR_BATCH_SIZE=8\nLANES_NEWS_AUDITOR_PROVIDER=source_rules\nDATABASE_URL='+value+'\n',encoding='utf-8')
    for suffix,operation in (('preflight','preflight'),('faults','faults')):
        name=create(task,suffix,operation)
        assert command(task,suffix+'-run',['docker','start','-a',name],120)==0
        assert command(task,suffix+'-inspect',['docker','inspect',name])==0
    write(task/'build-ready.json',{'freeze_sha256':digest(task/'freeze.json'),'preflight':read(task/'output-preflight/preflight.json')})
    return {'status':'built_software_preflight_passed','new_neural_requests':0}


def execute(task: Path) -> dict:
    check(task)
    assert read(task/'build-ready.json')['freeze_sha256']==digest(task/'freeze.json')
    tests=ET.parse(task/'all-checks.xml').getroot()
    assert not any(e.tag in ('failure','error','skipped') for e in tests.iter())
    assert read(task/'all-checks-exit.json')['exit_code']==0
    state=read(task/'private-postgis-state.json')
    assert command(task,'db-detach-bridge',['docker','network','disconnect','bridge',state['container_id']])==0
    claim={'attempts':1,'freeze_sha256':digest(task/'freeze.json'),'destination':task.name}
    write(ART/'rss-ner-c3b-integration.claim.json',claim);write(task/'attempt.json',claim)
    name=create(task,'integration','execute')
    try:code=command(task,'integration-run',['docker','start','-a',name],600)
    except (subprocess.TimeoutExpired,KeyboardInterrupt):
        command(task,'integration-guard-kill',['docker','kill',name]);code=2
        write(task/'guard-failure.json',{'code':'integration_interrupted_or_deadline','retry':False})
    command(task,'integration-inspect',['docker','inspect',name])
    return {'status':'completed_verification_pending' if code==0 else 'failed','retry':False}


def verify(task: Path) -> dict:
    check(task)
    from types import SimpleNamespace
    from app.services.news_ner_durable.assets import load_trusted_assets,with_placement_assets
    from app.services.news_ner_durable.adapter import verify_saved_result,build_native_result
    from app.services.news_ner_durable.contracts import RunEvidence
    from app.services.news_ner_durable.enrichment import enrich_native_result
    from app.services.news_ner.location_pipeline import from_neural_mentions
    request=read(task/'input/request.json')
    trusted=with_placement_assets(load_trusted_assets(ART/'ner-preview-bundle-20261019-v1',request['bundle_sha256'],expected_worker_code_sha256=request['worker_code_sha256']))
    output=task/'output-integration';history=read(output/'saved-history.json');oracles=read(task/'expected-private.json')['rows']
    summary=read(output/'summary.json');metrics=read(output/'metrics-complete.json');processing=read(output/'pipeline.json')
    assert read(task/'integration-run-exit.json')['exit_code']==0 and len(history)==10
    count=0;reviewed=0
    for saved in history:
        oracle=oracles[saved['workload_index']]['result']
        run=SimpleNamespace(**saved['run']);version=SimpleNamespace(**saved['version'])
        context=RunEvidence.from_records(run,version);result=verify_saved_result(context,run.result,trusted)
        actual=[[m.start,m.end,m.label] for m in result.native.neural_mentions]
        expected=[[m['start'],m['end'],m['label']] for m in oracle['proposal']['neural_mentions']]
        assert actual==expected;count+=len(actual)
        if saved['workload_index']==9:reviewed=len(actual)
        raw=context.source().runtime_request(context.input_fingerprint)
        pure=from_neural_mentions({**raw,'mentions':oracle['proposal']['neural_mentions']})
        expected_result=build_native_result(context,{**pure,'provenance':oracle['provenance'],'measurements':result.measurements},trusted,extracted_at=result.extracted_at)
        expected_result=enrich_native_result(context,expected_result,trusted)
        assert expected_result.model_dump(mode='json',by_alias=True)==run.result
    assert metrics['model_starts']==metrics['model_reaps']==1 and metrics['neural_requests']==10
    assert metrics['isolation']['raw_socket_denied'] and metrics['isolation']['parent_death_signal']
    assert metrics['cgroup_memory_peak_bytes']<2688*1024**2 and metrics['worker_seconds']<=580
    assert max(r['operation_seconds'] for r in processing['extraction']['runs'])<=125
    assert metrics['cold_seconds']<=60 and metrics['cleanup_seconds']<=5 and max(r['seconds'] for r in metrics['requests'])<=60
    assert reviewed==53 and count==4483
    result={**summary,'predictions_matched':count,'reviewed_predictions_matched':reviewed,
        'memory_peak_bytes':metrics['cgroup_memory_peak_bytes'],'worker_seconds':metrics['worker_seconds'],
        'maximum_operation_seconds':max(r['operation_seconds'] for r in processing['extraction']['runs']),
        'cleanup_seconds':metrics['cleanup_seconds'],'independent_verification_neural_requests':0}
    write(task/'integration-verification.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['prepare','build','execute','verify'])
    parser.add_argument('--task',type=Path,required=True);args=parser.parse_args()
    task=args.task.resolve();assert task.parent==ART.resolve()
    from sqlalchemy.engine import URL
    os.environ.update(ENVIRONMENT='test',LANES_NEWS_AUDITOR_BATCH_SIZE='8',LANES_NEWS_AUDITOR_PROVIDER='source_rules')
    os.environ['DATABASE_URL']=URL.create('postgresql+psycopg',host='127.0.0.1',port=1,database='lanes_p3_verify_import_only').render_as_string(hide_password=False)
    try:print(json.dumps(globals()[args.operation](task)))
    except Exception as exc:
        import traceback
        frames=[{'file':Path(f.filename).name,'function':f.name,'line':f.lineno} for f in traceback.extract_tb(exc.__traceback__)]
        write(task/(args.operation+'-failure.json'),{'code':'c3b_qualification_failed','exception_type':type(exc).__name__,'frames':frames})
        print(json.dumps({'code':'c3b_qualification_failed','operation':args.operation,'retry':False}));raise SystemExit(2)
