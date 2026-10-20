"""Single-use fixed-reference successor; verification is read-only by default."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time
from . import context_run_v37 as predecessor
from . import context_association_run as transport
from . import linux_runtime_v29 as q
from .context_gap_audit import digest,require
from .context_acceptance import validate_raw_input,object_sha

WORKER_FILES=tuple(n for n in predecessor.WORKER_FILES if n not in {
    'training/flood_ner/context_association_v37.py','training/flood_ner/context_association_worker_v37.py'})+(
    'training/flood_ner/context_association_v38.py','training/flood_ner/context_association_worker_v38.py')
CODE=tuple(sorted(set(predecessor.CODE)|{'backend/'+n for n in WORKER_FILES}|{
    'backend/training/flood_ner/context_run_v38.py','backend/training/flood_ner/context_review_v38.py',
    'backend/training/flood_ner/context_cases_v38.py','backend/training/flood_ner/context_scoring_v38.py'}))
TESTS=('backend/tests/test_flood_ner_context_association_v38.py','backend/tests/test_flood_ner_context_execution_v38.py',
       'backend/tests/test_flood_ner_context_scoring_v38.py')
KEYS={'schema','predecessor_grant','preservation','oracle_freeze','fixtures','request','protocol',
      'implementation','tests','test_receipt','qualification_bundle','qualification_receipt'}


def read(path: Path):return json.loads(path.read_text(encoding='utf-8'))
def bound(root: Path, value: dict)->Path:return transport.bound(root,value)


def preflight(root: Path,path: Path,sha: str)->tuple[dict,dict,dict]:
    require(digest(path)==sha,'stale grant')
    g=read(path);require(set(g)==KEYS and g['schema']=='lanes-context-fixed-links-grant-v38','exact fixed-reference grant required')
    require(set(g['implementation'])==set(CODE) and set(g['tests'])==set(TESTS),'complete code/test bindings required')
    for name,h in {**g['implementation'],**g['tests']}.items():
        require(digest(transport.checked_path(root,name))==h,'changed implementation/tests')
    oldpath=bound(root,g['predecessor_grant'])
    _,oldrequest,metadata=predecessor.preflight(root,oldpath,g['predecessor_grant']['sha256'])
    for name,item in read(bound(root,g['preservation']))['files'].items():
        f=transport.checked_path(root,name)
        require(f.stat().st_size==item['bytes'] and digest(f)==item['sha256'],'predecessor changed')
    freeze=read(bound(root,g['oracle_freeze']));fixtures=read(bound(root,g['fixtures']))
    oldg=read(oldpath);oldfixtures=read(bound(root,oldg['fixtures']))
    reference=bound(root,oldg['reference_freeze']).parent/'references.json'
    require(digest(reference)==freeze['references_sha256'] and freeze['references_unchanged'] is True,'fixed references changed')
    require(freeze['fixtures_sha256']==g['fixtures']['sha256'] and fixtures[:208]==oldfixtures,'frozen oracles changed')
    require(len(fixtures)==len({c['case_id']for c in fixtures})==238,'exact 238 fixtures required')
    bundle_path=bound(root,g['qualification_bundle']);bundle=read(bundle_path)
    require(Path(bundle['predecessor_bundle'])==bound(root,oldg['qualification_bundle'])
        and Path(bundle['fixtures'])==bound(root,g['fixtures']),'qualification scope changed')
    require(bundle['implementation_sha256']==g['implementation']['backend/training/flood_ner/context_review_v38.py'],'unqualified implementation')
    for name,h in bundle['files'].items():require(digest(Path(name))==h,'stale qualification resource')
    receipt=read(bound(root,g['qualification_receipt']))
    require(receipt['returncode']==0 and receipt['output_complete']is True and str(bundle_path)in receipt['args']
        and g['qualification_bundle']['sha256']in receipt['args'],'failed or unbound qualification')
    require(json.loads(receipt['stdout'])=={'status':'qualified_references_and_fictional_cases','references':23,'fixtures':238,
        'tokenizer_reconstruction_verified':True,'neural_inference':False,'training_started':False,'references_unchanged':True},'incomplete qualification')
    test=read(bound(root,g['test_receipt']))
    require(test['implementation']==g['implementation'] and test['tests']==g['tests'],'unbound tests')
    rawtest=read(bound(root,test['raw_receipt']))
    require(rawtest['returncode']==0 and rawtest['output_complete']is True and all(n in rawtest['args']for n in TESTS),'authentic passing tests required')
    request=read(bound(root,g['request']))
    require(set(request)=={'schema','rows','implementation'} and request['schema']=='lanes-context-association-worker-v38','raw-only request required')
    require(set(request['implementation'])==set(WORKER_FILES) and all(g['implementation'].get('backend/'+n)==h
        for n,h in request['implementation'].items()),'worker closure unqualified')
    rows={r['record_id']:r for r in request['rows']}
    require(len(rows)==len(request['rows'])==262,'exact unique 24+238 workload required')
    for row in rows.values():validate_raw_input(row)
    require(all(rows.get(r['record_id'])==r for r in oldrequest['rows']),'old real inputs or fixtures changed')
    for case in fixtures:
        rid='fictional-'+hashlib.sha256(case['case_id'].encode()).hexdigest()[:20];row=rows.get(rid);r=case['record']
        require(row is not None and row['text']==r['text'] and row['text_sha256']==r['text_sha256'],'fictional text mismatch')
        keys=('id','start','end','text','label')
        require([{k:m[k] for k in keys}for m in row['mentions']]==[{k:e[k]for k in keys}for e in r['entities']
            if e['label']in{'ROAD','LANDMARK','LOCAL_AREA','BARANGAY','CITY','PROVINCE'}],'fictional mention mismatch')
    protocol=read(bound(root,g['protocol']))
    require(protocol['schema']=='lanes-context-fixed-links-protocol-v38' and protocol['attempts']==1
        and protocol['request_rows_sha256']==object_sha(request['rows']) and protocol['references_unchanged']is True
        and protocol['no_post_result_tuning']is True,'fixed single comparison required')
    for key in ('scoring_inputs','baseline_output','v37_output','error_inventory','previous_correct_mapping','analysis_script'):
        bound(root,protocol[key])
    return g,request,metadata


def execute(root: Path,docker: str,path: Path,sha: str,output: Path)->dict:
    grant,request,metadata=preflight(root,path,sha)
    art=Path(__file__).parent/'artifacts'
    require(output.resolve().parent==art.resolve() and not output.exists(),'new direct private destination required')
    q.private_destination(output,art)
    with q.exclusive(art/'context-association-v38-active.lock',{'grant_sha256':sha,'output':str(output)}):
        claims=art/'context-association-v38-claims';claims.mkdir(exist_ok=True)
        q.write_new(claims/(sha+'.json'),{'output':output.name});output.mkdir()
        name='lanes-context-candidate-'+sha[:16]
        try:
            image=q.command([docker,'image','inspect',metadata['image_id']],output/'image.json');q.successful(image)
            require(json.loads(image['stdout'])[0]['Id']==metadata['image_id'],'qualified image differs')
            inputs=output/'input';inputs.mkdir();worker=output/'worker-output';worker.mkdir()
            q.write_new(inputs/'request.json',request)
            mounts={'/input':(inputs,True),'/output':(worker,False)}
            mounts.update({'/code/'+n:(root/'backend'/n,True)for n in WORKER_FILES})
            q.successful(q.command(transport.container_args(docker,metadata['image_id'],name,mounts,
                'training/flood_ner/context_association_worker_v38.py',digest(inputs/'request.json'),WORKER_FILES),output/'create.json'))
            r=q.command([docker,'inspect',name],output/'container.json');q.successful(r)
            q.verify_isolation(json.loads(r['stdout'])[0],mounts);started=time.monotonic()
            try:
                q.successful(q.command([docker,'start',name],output/'start.json'))
                _,ready=q.monitor(docker,name,output,worker,started)
            except BaseException:
                q.command([docker,'kill',name],output/'failed-owned-stop.json',10)
                q.command([docker,'inspect',name],output/'failed-owned-state.json',10)
                raise
            r=q.command([docker,'inspect',name],output/'completed-state.json');q.successful(r);state=json.loads(r['stdout'])[0]
            require(not state['State']['Running']and state['State']['Pid']==0 and state['State']['ExitCode']==0
                and not state['State']['OOMKilled'],'worker failure')
            q.verify_isolation(state,mounts);status=read(worker/'status.json')
            require(status['status']=='completed'and status['processed']==262 and status['neural_libraries_loaded']is False
                and status['network_database_blocked']is True,'guarded output incomplete')
            preflight(root,path,sha)
            result={'status':'offline_successor_worker_completed','records':262,'eligible_references':23,
                'cold_seconds':ready,'wall_seconds':time.monotonic()-started,'image_id':metadata['image_id'],
                'neural_inference':False,'training_started':False,'application_connected':False}
            q.write_new(output/'execution-status.json',result);return result
        except BaseException as exc:
            q.write_new(output/'failure.json',{'status':'failed','error_type':type(exc).__name__});raise


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--grant',type=Path,required=True);p.add_argument('--sha256',required=True)
    p.add_argument('--execute',action='store_true');p.add_argument('--output',type=Path)
    p.add_argument('--docker',default=r'C:\Program Files\Docker\Docker\resources\bin\docker.exe');a=p.parse_args()
    root=Path(__file__).resolve().parents[3]
    if a.execute:
        require(a.output is not None,'new output required');result=execute(root,a.docker,a.grant,a.sha256,a.output)
    else:
        _,_,m=preflight(root,a.grant,a.sha256)
        result={'status':'verified_read_only','image_id':m['image_id'],'records':262,'training_started':False,'application_connected':False}
    print(json.dumps(result))


if __name__=='__main__':main()
