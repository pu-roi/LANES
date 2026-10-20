"""Single-use raw-only successor comparison; read-only verification is the default."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time
from . import context_association_run_v35 as predecessor
from . import context_association_run as transport
from . import linux_runtime_v29 as q
from .context_acceptance import validate_raw_input,object_sha
from .context_revision_v35 import verify_frozen_files
from .context_gap_audit import digest,require

WORKER_FILES=tuple(n for n in predecessor.WORKER_FILES if n not in {
    'training/flood_ner/context_association_v35.py','training/flood_ner/context_association_worker_v35.py'})+(
    'training/flood_ner/context_association_v36.py','training/flood_ner/context_association_worker_v36.py')
CODE=tuple(sorted(set(predecessor.CODE)|{'backend/'+n for n in WORKER_FILES}|{
    'backend/training/flood_ner/context_run_v36.py','backend/training/flood_ner/context_review_v36.py',
    'backend/training/flood_ner/context_cases_v36.py','backend/training/flood_ner/context_scoring_v36.py'}))
TESTS=('backend/tests/test_flood_ner_context_association_v36.py',
    'backend/tests/test_flood_ner_context_review_v36.py','backend/tests/test_flood_ner_context_execution_v36.py')
KEYS={'schema','predecessor_grant','preservation','reference_manifest','reference_freeze','phase',
    'qualification_bundle','qualification_receipt','fixtures','request','protocol','implementation','tests','test_receipt'}


def read(path: Path):return json.loads(path.read_text(encoding='utf-8'))
def bound(root: Path,value: dict)->Path:return transport.bound(root,value)


def preflight(root: Path,path: Path,sha: str)->tuple[dict,dict,dict]:
    require(digest(path)==sha,'stale grant')
    g=read(path);require(set(g)==KEYS and g['schema']=='lanes-context-comprehensive-grant-v36','exact review-only grant required')
    require(set(g['implementation'])==set(CODE)and set(g['tests'])==set(TESTS),'complete code/test bindings required')
    for name,h in {**g['implementation'],**g['tests']}.items():
        require(digest(transport.checked_path(root,name))==h,'changed implementation/tests')
    oldpath=bound(root,g['predecessor_grant'])
    _,oldrequest,metadata=predecessor.preflight(root,oldpath,g['predecessor_grant']['sha256'])
    preservation=read(bound(root,g['preservation']))
    for name,item in preservation['files'].items():
        file=transport.checked_path(root,name)
        require(digest(file)==item['sha256']and file.stat().st_size==item['bytes'],'predecessor changed')
    manifest=bound(root,g['reference_manifest']);freeze_path=bound(root,g['reference_freeze'])
    require(manifest.parent==freeze_path.parent and manifest.parent.parent.name=='context-reference-review-20261019-v36','wrong source-only package')
    package=manifest.parent.parent;freeze=read(freeze_path)
    require(freeze['frozen']is True,'reference revision not frozen')
    for name in ('input','output','authoring'):verify_frozen_files(package,freeze[name])
    phase=read(bound(root,g['phase']))
    require(phase['candidate_implementation_not_yet_created']is True and phase['reference_freeze_sha256']==g['reference_freeze']['sha256'],
        'independent reference-first freeze required')
    require(phase['fixtures_sha256']==g['fixtures']['sha256'],'fictional oracle changed after freeze')
    prior_holds=read(package/'input/held-dispositions.json');dispositions=read(package/'review-output/all-26-dispositions.json')
    require(len(prior_holds)==3 and len(dispositions)==26,'exact 23+3 counterpart accounting required')
    require(dispositions[-3:]==prior_holds,'carried hold objects changed')
    require(read(package/'review-output/validation.json')['carried_holds_unchanged']is True,'prior holds changed')
    receipt=read(bound(root,g['qualification_receipt']));bundle_path=bound(root,g['qualification_bundle']);bundle=read(bundle_path)
    require(Path(bundle['prior'])==(package/'input/references.json').resolve()
        and Path(bundle['revised'])==(package/'review-output/references.json').resolve()
        and Path(bundle['fixtures'])==bound(root,g['fixtures']).resolve()
        and Path(bundle['source_use'])==(package/'input/source-use.json').resolve(),'qualification/reference scope mismatch')
    require(receipt['returncode']==0 and receipt['output_complete']is True and str(bundle_path)in receipt['args']
        and g['qualification_bundle']['sha256']in receipt['args'],'unbound or failed schema/tokenizer qualification')
    result=json.loads(receipt['stdout'])
    require(result=={'status':'qualified_references_and_fictional_cases','references':23,'fixtures':160,
        'tokenizer_reconstruction_verified':True,'neural_inference':False,'training_started':False},'incomplete qualification')
    for name,h in bundle['files'].items():require(digest(Path(name))==h,'qualified resource changed')
    test=read(bound(root,g['test_receipt']))
    require(test['implementation']==g['implementation']and test['tests']==g['tests'],'test grant bindings differ')
    raw=read(bound(root,test['raw_receipt']))
    require(raw['returncode']==0 and raw['output_complete']is True and all(n in raw['args']for n in TESTS),
        'complete authentic passing tests required')
    request=read(bound(root,g['request']));cases=read(bound(root,g['fixtures']))
    require(set(request)=={'schema','rows','implementation'}and request['schema']=='lanes-context-association-worker-v36','raw-only request required')
    require(set(request['implementation'])==set(WORKER_FILES),'worker source closure differs')
    require(all(g['implementation'].get('backend/'+n)==h for n,h in request['implementation'].items()),'unqualified worker')
    rows={r['record_id']:r for r in request['rows']}
    require(len(rows)==len(request['rows'])==184,'exact unique 24+160 workload required')
    for row in rows.values():validate_raw_input(row)
    require(all(rows.get(r['record_id'])==r for r in oldrequest['rows']),'original 24 inputs/64 fictional cases changed')
    require(len(cases)==160 and len({c['case_id']for c in cases})==160,'exact fictional matrix required')
    oldcases=read(bound(root,read(oldpath)['fixtures']))
    require(cases[:64]==oldcases,'original 64 oracles changed')
    for case in cases:
        rid='fictional-'+hashlib.sha256(case['case_id'].encode()).hexdigest()[:20];row=rows.get(rid)
        require(row is not None and row['text']==case['record']['text']and row['text_sha256']==case['record']['text_sha256'],'fictional source mismatch')
        places=[{k:e[k]for k in ('id','start','end','text','label')}for e in case['record']['entities']if e['label']in {'ROAD','LANDMARK','LOCAL_AREA','BARANGAY','CITY','PROVINCE'}]
        require([{k:m[k]for k in ('id','start','end','text','label')}for m in row['mentions']]==places,'fictional supplied locations changed')
    protocol=read(bound(root,g['protocol']))
    require(protocol['schema']=='lanes-context-comprehensive-protocol-v36'and protocol['attempts']==1
        and protocol['request_rows_sha256']==object_sha(request['rows'])and protocol['zero_total_incorrect_required']is True,
        'fixed single comparison and zero-error gate required')
    for name in ('baseline_output','v34_output','v35_output'):bound(root,protocol[name])
    require(protocol['reference_freeze_sha256']==g['reference_freeze']['sha256'],'scoring revision changed')
    return g,request,metadata


def execute(root: Path,docker: str,path: Path,sha: str,output: Path)->dict:
    grant,request,metadata=preflight(root,path,sha)
    art=Path(__file__).parent/'artifacts'
    require(output.resolve().parent==art.resolve()and not output.exists(),'new direct private destination required')
    q.private_destination(output,art)
    with q.exclusive(art/'context-association-v36-active.lock',{'grant_sha256':sha,'output':str(output)}):
        claims=art/'context-association-v36-claims';claims.mkdir(exist_ok=True)
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
                'training/flood_ner/context_association_worker_v36.py',digest(inputs/'request.json'),WORKER_FILES),output/'create.json'))
            receipt=q.command([docker,'inspect',name],output/'container.json');q.successful(receipt)
            q.verify_isolation(json.loads(receipt['stdout'])[0],mounts);started=time.monotonic()
            try:
                q.successful(q.command([docker,'start',name],output/'start.json'))
                _,ready=q.monitor(docker,name,output,worker,started)
            except BaseException:
                q.command([docker,'kill',name],output/'failed-owned-stop.json',10)
                q.command([docker,'inspect',name],output/'failed-owned-state.json',10)
                raise
            r=q.command([docker,'inspect',name],output/'completed-state.json');q.successful(r);state=json.loads(r['stdout'])[0]
            require(not state['State']['Running']and state['State']['Pid']==0 and state['State']['ExitCode']==0 and not state['State']['OOMKilled'],'worker failure')
            q.verify_isolation(state,mounts);status=read(worker/'status.json')
            require(status['status']=='completed'and status['processed']==184 and status['neural_libraries_loaded']is False
                and status['network_database_blocked']is True,'guarded output incomplete')
            preflight(root,path,sha)
            result={'status':'offline_successor_worker_completed','records':184,'eligible_references':23,
                'cold_seconds':ready,'wall_seconds':time.monotonic()-started,'image_id':metadata['image_id'],
                'neural_inference':False,'training_started':False,'application_connected':False}
            q.write_new(output/'execution-status.json',result);return result
        except BaseException as exc:
            q.write_new(output/'failure.json',{'status':'failed','error_type':type(exc).__name__});raise


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--grant',type=Path,required=True);p.add_argument('--sha256',required=True)
    p.add_argument('--execute',action='store_true');p.add_argument('--output',type=Path)
    p.add_argument('--docker',default=r'C:\Program Files\Docker\Docker\resources\bin\docker.exe');args=p.parse_args()
    root=Path(__file__).resolve().parents[3]
    if args.execute:
        require(args.output is not None,'new output required');result=execute(root,args.docker,args.grant,args.sha256,args.output)
    else:
        _,_,metadata=preflight(root,args.grant,args.sha256)
        result={'status':'verified_read_only','image_id':metadata['image_id'],'records':184,'training_started':False,'application_connected':False}
    print(json.dumps(result))


if __name__=='__main__':main()
