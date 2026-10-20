"""Single-attempt baseline/candidate controller. Default verifies bindings only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time

if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

from training.flood_ner import linux_runtime_v29 as q
from training.flood_ner import context_gap_runner as old
from training.flood_ner.context_gap_audit import digest, require, validate_raw
from training.flood_ner.context_acceptance import validate_raw_input
from training.flood_ner.runtime_preflight import checked_path

BASE_FILES=old.WORKER_FILES
CANDIDATE_FILES=(*BASE_FILES,'training/flood_ner/context_association.py','training/flood_ner/context_association_worker.py',
    'training/flood_ner/context_acceptance.py','training/flood_ner/annotation/__init__.py','training/flood_ner/annotation/schema.py',
    'training/flood_ner/annotation/validation.py','training/flood_ner/annotation/context_review.py',
    'training/flood_ner/collection.py','training/flood_ner/sources.py','training/flood_ner/window.py')
CODE=tuple('backend/'+n for n in CANDIDATE_FILES)+('backend/training/flood_ner/context_association_run.py',
    'backend/training/flood_ner/context_association_scoring.py','backend/training/flood_ner/context_gap_runner.py',
    'backend/training/flood_ner/linux_runtime_v29.py','backend/training/flood_ner/runtime_preflight.py')
TESTS=('backend/tests/test_flood_ner_context_association.py',)
KEYS={'schema','implementation','tests','test_receipt','image_id','qualification','baseline_request','candidate_request',
      'eligibility','reference_bindings','predecessor_manifest','comparison_protocol'}


def bound(root: Path, value: dict) -> Path:
    require(set(value)=={'path','sha256'},'exact file binding required')
    path=checked_path(root,value['path']);require(digest(path)==value['sha256'],'stale bound input');return path


def preflight(root: Path, path: Path, sha: str) -> tuple[dict,dict,dict]:
    require(digest(path)==sha,'stale comparison grant');g=json.loads(path.read_text(encoding='utf-8'))
    require(set(g)==KEYS and g['schema']=='lanes-context-association-grant-v34','complete comparison grant required')
    require(set(g['implementation'])==set(CODE)and set(g['tests'])==set(TESTS),'exact code/tests required')
    for n,h in{**g['implementation'],**g['tests']}.items():require(digest(checked_path(root,n))==h,'implementation/test changed')
    receipt=json.loads(bound(root,g['test_receipt']).read_text(encoding='utf-8'))
    require(receipt['implementation']==g['implementation']and receipt['tests']==g['tests'],'test binding differs')
    actual=json.loads(bound(root,receipt['raw_receipt']).read_text(encoding='utf-8'))
    require(actual['returncode']==0 and actual['output_complete']is True and all(n in actual['args']for n in TESTS),'authentic passing tests required')
    qual=json.loads(bound(root,g['qualification']).read_text(encoding='utf-8'))
    require(qual['status']=='offline_comparison_completed'and qual['image_id']==g['image_id'],'qualified image required')
    require(re.fullmatch(r'sha256:[a-f0-9]{64}',g['image_id'])is not None,'immutable image required')
    parent_manifest=bound(root,g['predecessor_manifest'])
    require(parent_manifest.parent.name=='context-acceptance-20261019-v33','qualified acceptance predecessor required')
    references={}
    for b in g['reference_bindings']:
        p=bound(root,b);require(p.parent==parent_manifest.parent and p.name not in references,'wrong/duplicate acceptance input')
        references[p.name]=p
    require(set(references)=={'references.json','fixtures.json','source-use.json','freeze.json'},'complete frozen reference/input bindings required')
    protocol=json.loads(bound(root,g['comparison_protocol']).read_text(encoding='utf-8'))
    require(protocol['schema']=='lanes-context-association-protocol-v34'and protocol['candidate_experiments']==1,'fixed single comparison protocol required')
    baseline=json.loads(bound(root,g['baseline_request']).read_text(encoding='utf-8'))
    candidate=json.loads(bound(root,g['candidate_request']).read_text(encoding='utf-8'))
    require(set(baseline)=={'schema','rows','implementation','files'}and baseline['schema']=='lanes-context-gap-worker-v32','frozen baseline request required')
    require(set(candidate)=={'schema','rows','implementation'}and candidate['schema']=='lanes-context-association-worker-v34','raw candidate request required')
    require(set(baseline['implementation'])==set(BASE_FILES)and set(candidate['implementation'])==set(CANDIDATE_FILES),'worker source closure differs')
    for request in(baseline,candidate):
        for n,h in request['implementation'].items():require(g['implementation'].get('backend/'+n)==h,'worker binding unqualified')
    require(baseline['files']==old.rules_files(root),'baseline production source/assets changed')
    validate_raw(baseline['rows']);require(len(baseline['rows'])==24 and len(candidate['rows'])==64,'exact workload required')
    ids=set()
    for r in candidate['rows']:
        validate_raw_input(r);require(r['record_id']not in ids,'duplicate candidate identity');ids.add(r['record_id'])
    eligible=json.loads(bound(root,g['eligibility']).read_text(encoding='utf-8'))
    require(len(eligible)==24 and len({r['record_id']for r in eligible})==24,'exact eligible training-only membership required')
    expected={r['record_id']:r for r in eligible};cr={r['record_id']:r for r in candidate['rows']}
    parent=json.loads(references['references.json'].read_text(encoding='utf-8'))
    require(len(parent)==26 and sum(x['review']['disposition']=='hold'for x in parent)==2,'all predecessor dispositions required')
    parent_eligible={'train-'+hashlib.sha256(x['current']['record_id'].encode()).hexdigest()[:20]:x for x in parent if x['review']['disposition']!='hold'}
    require(set(parent_eligible)==set(expected),'held or non-member reference reuse')
    uses={u['record_id']:u for u in json.loads(references['source-use.json'].read_text(encoding='utf-8'))}
    require({r['record_id']for r in baseline['rows']}==set(expected),'baseline membership differs')
    for r in baseline['rows']:
        e=expected[r['record_id']];c=cr[r['record_id']]
        ref=parent_eligible[r['record_id']]['current']
        use=uses[ref['record_id']]
        require(use['verified']is True and use['scope']=='private_owner_only_academic_training_evaluation'and
                use['text_sha256']==ref['text_sha256']and use['source_sha256']==ref['source']['text_sha256']and
                [use['start'],use['end']]==[ref['passage_start'],ref['passage_end']],'unsupported exact source-use scope')
        require(e['partition']=='train'and e['source_use_supported']is True and e['reference_disposition']!='hold'and
                ref['split']=='train'and r['text_sha256']==e['text_sha256']==c['text_sha256']==ref['text_sha256']and
                r['text']==c['text']==ref['text'],'held/nontraining/mismatched input')
        require(r['published_at']==(c['publication']['value']if c['publication']else None),'publication metadata differs')
    require(len(ids-set(expected))==40 and all(r.startswith('fictional-')for r in ids-set(expected)),'exact fictional-only remainder required')
    fixture_bindings=protocol['fictional_input_bindings']
    require(set(fixture_bindings)==ids-set(expected),'fictional projection membership differs')
    for rid,binding in fixture_bindings.items():
        require(cr[rid]['text_sha256']==binding['text_sha256']and
                hashlib.sha256(json.dumps(cr[rid]['mentions'],sort_keys=True,ensure_ascii=False).encode()).hexdigest()==binding['mentions_sha256'],
                'fixture source/mention projection differs')
    require(set(protocol['training_input_bindings'])==set(expected),'saved prediction projection bindings missing')
    for rid,h in protocol['training_input_bindings'].items():
        require(hashlib.sha256(json.dumps(cr[rid]['mentions'],sort_keys=True,ensure_ascii=False).encode()).hexdigest()==h,
                'saved prediction projection differs')
    return g,baseline,candidate


def container_args(docker: str, image: str, name: str, mounts: dict, entry: str, request_sha: str, code: tuple) -> list[str]:
    require(set(mounts)=={'/input','/output',*('/code/'+n for n in code)},'raw-only exact mounts required')
    require(re.fullmatch(r'lanes-context-(?:base|candidate)-[a-f0-9]{16}',name)is not None and
            re.fullmatch(r'sha256:[a-f0-9]{64}',image)is not None,'immutable attempt required')
    args=[docker,'create','--name',name,'--network','none','--cpus','2','--memory','4g','--memory-swap','4g',
          '--pids-limit','128','--read-only','--restart=no','--cap-drop=ALL','--security-opt=no-new-privileges',
          '--tmpfs','/tmp:rw,noexec,nosuid,size=64m','--entrypoint','python']
    for target,(source,readonly)in mounts.items():
        require(source.exists()and ','not in str(source)and readonly is(target!='/output'),'unsafe mount')
        require(not any(p.is_symlink()or getattr(p,'is_junction',lambda:False)()for p in(source,*source.parents)),'linked mount')
        args+=['--mount',f'type=bind,source={source.resolve()},target={target}'+(',readonly'if readonly else'')]
    for k,v in{'PYTHONDONTWRITEBYTECODE':'1','CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}.items():args+=['--env',k+'='+v]
    return args+[image,'-I','-B','/code/'+entry,'--request','/input/request.json','--sha256',request_sha]


def execute(root: Path, docker: str, grant_path: Path, sha: str, output: Path) -> dict:
    g,baseline,candidate=preflight(root,grant_path,sha);art=Path(__file__).parent/'artifacts'
    require(output.resolve().parent==art.resolve()and not output.exists(),'new direct private destination required');q.private_destination(output,art)
    with q.exclusive(art/'context-association-active.lock',{'grant_sha256':sha,'output':str(output)}):
        claims=art/'context-association-claims';claims.mkdir(exist_ok=True);q.write_new(claims/(sha+'.json'),{'output':output.name})
        output.mkdir()
        try:
            r=q.command([docker,'image','inspect',g['image_id']],output/'image.json');q.successful(r)
            require(json.loads(r['stdout'])[0]['Id']==g['image_id'],'image identity differs')
            for role,request,code,entry in(
                ('base',baseline,BASE_FILES,'training/flood_ner/context_gap_worker.py'),
                ('candidate',candidate,CANDIDATE_FILES,'training/flood_ner/context_association_worker.py')):
                attempt=output/role;attempt.mkdir();inputs=attempt/'input';inputs.mkdir();worker=attempt/'worker-output';worker.mkdir()
                q.write_new(inputs/'request.json',request);name='lanes-context-'+role+'-'+sha[:16]
                mounts={'/input':(inputs,True),'/output':(worker,False)};mounts.update({'/code/'+n:(root/'backend'/n,True)for n in code})
                q.successful(q.command(container_args(docker,g['image_id'],name,mounts,entry,digest(inputs/'request.json'),code),attempt/'create.json'))
                r=q.command([docker,'inspect',name],attempt/'container.json');q.successful(r);q.verify_isolation(json.loads(r['stdout'])[0],mounts)
                started=time.monotonic()
                try:
                    q.successful(q.command([docker,'start',name],attempt/'start.json'));_,ready=q.monitor(docker,name,attempt,worker,started)
                except BaseException:
                    q.command([docker,'kill',name],attempt/'failed-owned-stop.json',10)
                    q.command([docker,'inspect',name],attempt/'failed-owned-state.json',10);raise
                r=q.command([docker,'inspect',name],attempt/'completed-state.json');q.successful(r);state=json.loads(r['stdout'])[0]
                require(not state['State']['Running']and state['State']['Pid']==0 and state['State']['ExitCode']==0 and not state['State']['OOMKilled'],'worker failed')
                q.verify_isolation(state,mounts)
                status=json.loads((worker/'status.json').read_text(encoding='utf-8'))
                require(status['status']=='completed'and status['processed']==len(request['rows'])and
                        status['neural_libraries_loaded']is False and status['network_database_blocked']is True,'incomplete guarded worker')
                q.write_new(attempt/'measurement.json',{'startup_observed_seconds':ready,'wall_seconds':time.monotonic()-started,
                                                       'processed':status['processed']})
            preflight(root,grant_path,sha)
            result={'status':'offline_workers_completed','baseline_records':24,'candidate_records':64,
                    'neural_inference':False,'training_started':False,'application_connected':False,'image_id':g['image_id']}
            q.write_new(output/'execution-status.json',result);return result
        except BaseException as exc:
            q.write_new(output/'failure.json',{'status':'failed','error_type':type(exc).__name__});raise


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--grant',type=Path,required=True);p.add_argument('--sha256',required=True)
    p.add_argument('--execute',action='store_true');p.add_argument('--output',type=Path);p.add_argument('--docker',default=r'C:\Program Files\Docker\Docker\resources\bin\docker.exe');args=p.parse_args()
    root=Path(__file__).resolve().parents[3]
    if args.execute:
        require(args.output is not None,'absent output required');result=execute(root,args.docker,args.grant,args.sha256,args.output)
    else:
        preflight(root,args.grant,args.sha256);result={'status':'verified_read_only','training_started':False,'neural_inference':False,'application_connected':False}
    print(json.dumps(result))


if __name__=='__main__':main()
