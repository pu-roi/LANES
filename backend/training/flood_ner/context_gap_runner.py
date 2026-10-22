"""Explicit single-attempt raw rules diagnostic; no model or reference mounts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import time

if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from training.flood_ner import context_gap_audit as audit
from training.flood_ner import linux_runtime_v29 as q
from training.flood_ner.runtime_preflight import checked_path

WORKER_FILES=('training/__init__.py','training/flood_ner/__init__.py','training/flood_ner/context_gap_audit.py',
              'training/flood_ner/context_gap_worker.py','training/flood_ner/corrected_rules_worker.py')
IMPLEMENTATION=tuple('backend/'+n for n in WORKER_FILES)+tuple('backend/training/flood_ner/'+n for n in
    ('context_gap_runner.py','annotation/schema.py','annotation/validation.py','annotation/context_review.py','collection.py','sources.py'))


def rules_files(root:Path)->dict:
    from training.flood_ner.corrected_rules_worker import rules_code_files
    files={n[len('backend/'):]:sha for n,sha in rules_code_files(root).items()}
    for n in ('flooded_areas_pasig_clean.csv','pasig_barangay_reference.csv','philippines_psgc_reference.csv'):
        files['runtime_data/'+n]=audit.digest(root/'backend/runtime_data'/n)
    return files


def preflight(root:Path,path:Path,sha:str)->tuple[dict,dict]:
    audit.require(audit.digest(path)==sha,'stale audit grant')
    g=json.loads(path.read_text(encoding='utf-8'))
    audit.require(set(g)=={'schema','implementation','tests','test_receipt','request','eligibility','image_id','qualification'}and
                  g['schema']=='lanes-context-gap-grant-v32','complete audit authorization required')
    audit.require(set(g['implementation'])==set(IMPLEMENTATION),'complete audit implementation bindings required')
    for name,h in g['implementation'].items():audit.require(audit.digest(checked_path(root,name))==h,'implementation changed')
    audit.require(set(g['tests'])=={'backend/tests/test_flood_ner_context_gap_audit.py'},'audit test binding required')
    for name,h in g['tests'].items():audit.require(audit.digest(checked_path(root,name))==h,'test changed')
    tests=audit.checked_json(root,g['test_receipt'])
    audit.require(tests['implementation']==g['implementation']and tests['tests']==g['tests'],'unbound test evidence')
    raw=audit.checked_json(root,tests['raw_receipt'])
    audit.require(raw['returncode']==0 and raw['output_complete']is True and
                  'backend/tests/test_flood_ner_context_gap_audit.py'in raw['args'],'passing actual tests required')
    qual=audit.checked_json(root,g['qualification'])
    audit.require(qual['image_id']==g['image_id']and qual['status']=='offline_comparison_completed','qualified image required')
    request=audit.checked_json(root,g['request']);audit.validate_raw(request['rows'])
    audit.require(set(request)=={'schema','rows','implementation','files'}and request['schema']=='lanes-context-gap-worker-v32',
                  'raw request required')
    audit.require(set(request['implementation'])==set(WORKER_FILES),'scoped worker source required')
    for name,h in request['implementation'].items():audit.require(g['implementation'].get('backend/'+name)==h,'worker code unbound')
    audit.require(request['files']==rules_files(root),'complete exact rules/asset bindings required')
    eligibility=audit.checked_json(root,g['eligibility'])
    eligible={r['record_id']:r for r in eligibility if r['supported']is True}
    audit.require(len(eligible)==len(request['rows'])and{r['record_id']for r in request['rows']}==set(eligible),'unsupported source-use expansion')
    for row in request['rows']:
        audit.require(eligible[row['record_id']]['text_sha256']==row['text_sha256'],'source-use text binding mismatch')
    return g,request


def container_args(docker:str,image:str,name:str,mounts:dict,sha:str)->list[str]:
    audit.require(re.fullmatch('sha256:[a-f0-9]{64}',image)is not None and
                  re.fullmatch('lanes-context-gap-[a-f0-9]{16}',name)is not None,'immutable image/attempt required')
    audit.require(set(mounts)=={'/input','/output',*('/code/'+n for n in WORKER_FILES)},'exact raw-only mounts required')
    args=[docker,'create','--name',name,'--network','none','--cpus','2','--memory','4g','--memory-swap','4g',
          '--pids-limit','128','--read-only','--restart=no','--cap-drop=ALL','--security-opt=no-new-privileges',
          '--tmpfs','/tmp:rw,noexec,nosuid,size=64m','--entrypoint','python']
    for target,(source,readonly)in mounts.items():
        audit.require(source.exists()and ','not in str(source)and readonly is(target!='/output'),'unsafe mount')
        audit.require(not any(p.is_symlink()or getattr(p,'is_junction',lambda:False)()for p in(source,*source.parents)),'linked mount')
        args+=['--mount',f'type=bind,source={source.resolve()},target={target}'+(',readonly'if readonly else'')]
    for k,v in {'PYTHONDONTWRITEBYTECODE':'1','CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}.items():args+=['--env',k+'='+v]
    return args+[image,'-I','-B','/code/training/flood_ner/context_gap_worker.py','--request','/input/request.json','--sha256',sha]


def execute(root:Path,docker:str,grant_path:Path,sha:str,output:Path)->dict:
    g,request=preflight(root,grant_path,sha);art=Path(__file__).parent/'artifacts'
    audit.require(output.resolve().parent==art.resolve()and not output.exists(),'new direct private destination required')
    q.private_destination(output,art)
    with q.exclusive(art/'context-gap-active.lock',{'grant_sha256':sha,'output':output.name}):
        claims=art/'context-gap-claims';claims.mkdir(exist_ok=True);q.write_new(claims/(sha+'.json'),{'output':output.name})
        output.mkdir();inputs=output/'input';inputs.mkdir();worker=output/'worker-output';worker.mkdir()
        q.write_new(inputs/'request.json',request)
        mounts={'/input':(inputs,True),'/output':(worker,False)}
        mounts.update({'/code/'+n:(root/'backend'/n,True)for n in WORKER_FILES})
        name='lanes-context-gap-'+sha[:16]
        try:
            r=q.command([docker,'image','inspect',g['image_id']],output/'image.json');q.successful(r)
            image=json.loads(r['stdout'])[0];audit.require(image['Id']==g['image_id']and image['Os']=='linux','image unavailable')
            q.successful(q.command(container_args(docker,g['image_id'],name,mounts,audit.digest(inputs/'request.json')),output/'create.json'))
            r=q.command([docker,'inspect',name],output/'container.json');q.successful(r);q.verify_isolation(json.loads(r['stdout'])[0],mounts)
            started=time.monotonic()
            try:
                q.successful(q.command([docker,'start',name],output/'start.json'))
                q.monitor(docker,name,output,worker,started)
            except BaseException:
                q.command([docker,'kill',name],output/'failed-owned-stop.json',10)
                q.command([docker,'inspect',name],output/'failed-owned-state.json',10)
                raise
            status=json.loads((worker/'status.json').read_text(encoding='utf-8'));results=audit.jsonl(worker/'rules.jsonl')
            audit.require(status['status']=='completed'and status['neural_libraries_loaded']is False and
                          status['network_database_blocked']is True and len(results)==status['processed']==len(request['rows']),
                          'incomplete rules processing')
            for row,result in zip(request['rows'],results):
                audit.require(result['record_id']==row['record_id']and result['text_sha256']==row['text_sha256']and result['status']=='completed',
                              'missing/duplicate/mismatched result')
            preflight(root,grant_path,sha)
            safe={'status':'rules_diagnostic_completed','processed':len(results),'neural_inference':False,
                  'training_started':False,'application_connected':False,'holdout_accessed':False,'image_id':g['image_id']}
            q.write_new(output/'aggregate.json',safe);return safe
        except BaseException as exc:
            q.write_new(output/'failure.json',{'status':'failed','error_type':type(exc).__name__});raise


def main()->None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--grant',type=Path,required=True);p.add_argument('--sha256',required=True)
    p.add_argument('--execute',action='store_true');p.add_argument('--output',type=Path)
    p.add_argument('--docker',default=r'C:\Program Files\Docker\Docker\resources\bin\docker.exe');args=p.parse_args()
    root=Path(__file__).resolve().parents[3]
    if args.execute:
        audit.require(args.output is not None,'new output required');result=execute(root,args.docker,args.grant,args.sha256,args.output)
    else:
        preflight(root,args.grant,args.sha256);result={'status':'verified_read_only','neural_inference':False,'training_started':False}
    print(json.dumps(result))


if __name__=='__main__':main()
