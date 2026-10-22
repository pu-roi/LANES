"""Read-only by default; single-use v35 worker with authenticated saved baselines."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

from training.flood_ner import context_association_run as previous
from training.flood_ner import linux_runtime_v29 as q
from training.flood_ner.context_acceptance import object_sha, validate_raw_input
from training.flood_ner.context_gap_audit import digest, require
from training.flood_ner.context_revision_v35 import verify_frozen_files, join_reviews

WORKER_FILES=tuple(n for n in previous.CANDIDATE_FILES if n!='training/flood_ner/context_association_worker.py')+(
    'training/flood_ner/context_association_v35.py','training/flood_ner/context_association_worker_v35.py')
CODE=tuple(sorted(set(previous.CODE)|{'backend/'+n for n in WORKER_FILES}|{
    'backend/training/flood_ner/context_revision_v35.py',
    'backend/training/flood_ner/context_association_cases_v35.py',
    'backend/training/flood_ner/context_association_run_v35.py',
    'backend/training/flood_ner/context_association_scoring_v35.py'}))
TESTS=('backend/tests/test_flood_ner_context_revision_v35.py',
       'backend/tests/test_flood_ner_context_association_v35.py',
       'backend/tests/test_flood_ner_context_association_v35_execution.py')
KEYS={'schema','predecessor_grant','predecessor_manifest','reference_freeze','reference_manifest',
      'reference_qualification','reference_qualification_bundle','reference_phase','candidate_request',
      'fixtures','protocol','implementation','tests','test_receipt'}


def read(path: Path) -> dict|list:
    return json.loads(path.read_text(encoding='utf-8'))


def verify_fixture_qualification(root: Path, protocol: dict, fixture_sha: str) -> None:
    receipt=read(previous.bound(root,protocol['fixture_qualification']))
    script=previous.bound(root,protocol['fixture_qualification_script'])
    require(receipt['returncode']==0 and receipt['output_complete']is True,'fictional qualification incomplete')
    require(str(script)in receipt['args'] and fixture_sha in receipt['args'],'fictional qualification binding differs')
    result=json.loads(receipt['stdout'])
    require(result['status']=='qualified_fictional_fixtures' and result['cases']==64
        and result['tokenizer_reconstruction_verified']is True and result['neural_inference']is False
        and result['training_started']is False,'fictional qualification missing')


def preflight(root: Path, path: Path, sha: str) -> tuple[dict,dict,dict]:
    require(digest(path)==sha,'stale successor grant')
    grant=read(path)
    require(set(grant)==KEYS and grant['schema']=='lanes-context-association-grant-v35','exact successor grant required')
    require(set(grant['implementation'])==set(CODE) and set(grant['tests'])==set(TESTS),'exact implementation/tests required')
    for name,h in {**grant['implementation'],**grant['tests']}.items():
        require(digest(previous.checked_path(root,name))==h,'changed implementation/test binding')
    old_grant=previous.bound(root,grant['predecessor_grant'])
    prior,baseline,original=previous.preflight(root,old_grant,grant['predecessor_grant']['sha256'])
    predecessor=previous.bound(root,grant['predecessor_manifest'])
    require(predecessor.parent==old_grant.parent,'wrong predecessor package')
    verify_frozen_files(predecessor.parent,read(predecessor)['files'])
    receipt=read(previous.bound(root,grant['test_receipt']))
    require(receipt['implementation']==grant['implementation'] and receipt['tests']==grant['tests'],'unqualified implementation')
    actual=read(previous.bound(root,receipt['raw_receipt']))
    require(actual['returncode']==0 and actual['output_complete']is True
        and all(name in actual['args']for name in TESTS),'authentic complete passing tests required')
    reference_manifest=previous.bound(root,grant['reference_manifest'])
    require(reference_manifest.parent.parent.name=='context-reference-review-20261019-v35','wrong source-only review package')
    verify_frozen_files(reference_manifest.parent,read(reference_manifest)['files'])
    freeze_path=previous.bound(root,grant['reference_freeze']);freeze=read(freeze_path)
    require(freeze_path.parent==reference_manifest.parent and freeze['frozen']is True,'unfrozen reference revision')
    review_root=reference_manifest.parent.parent
    verify_frozen_files(review_root,freeze['inputs']);verify_frozen_files(review_root,freeze['authoring_code'])
    phase=read(previous.bound(root,grant['reference_phase']))
    require(phase['candidate_implementation_not_yet_created']is True and
        phase['reference_freeze_sha256']==grant['reference_freeze']['sha256'],'reference-first freeze required')
    qualification=read(previous.bound(root,grant['reference_qualification']))
    require(qualification['returncode']==0 and qualification['output_complete']is True,'reference qualification failed')
    qualified=json.loads(qualification['stdout'])
    require(qualified['status']=='qualified_reference_revision' and qualified['records']==24
        and qualified['tokenizer_reconstruction_verified']is True,'reference/tokenizer qualification missing')
    bundle_path=previous.bound(root,grant['reference_qualification_bundle']);bundle=read(bundle_path)
    require(str(bundle_path)in qualification['args'] and grant['reference_qualification_bundle']['sha256']in qualification['args'],
        'reference receipt/bundle binding differs')
    for name,h in bundle['files'].items():require(digest(Path(name))==h,'changed qualified reference resource')
    pairs=join_reviews(read(review_root/'input/references.json'),read(reference_manifest.parent/'references.json'))
    revised={r['proposed']['record_id']:r for _,r in pairs}
    require(len(read(reference_manifest.parent/'all-26-dispositions.json'))==26,'counterpart accounting incomplete')
    request=read(previous.bound(root,grant['candidate_request']))
    require(set(request)=={'schema','rows','implementation'} and request['schema']=='lanes-context-association-worker-v35','raw-only worker request required')
    require(set(request['implementation'])==set(WORKER_FILES),'exact worker source closure required')
    for name,h in request['implementation'].items():require(grant['implementation'].get('backend/'+name)==h,'worker implementation unqualified')
    require(len(request['rows'])==88 and len({r['record_id']for r in request['rows']})==88,'exact unique 24+64 workload required')
    for row in request['rows']:validate_raw_input(row)
    rows={r['record_id']:r for r in request['rows']};oldrows={r['record_id']:r for r in original['rows']}
    require(all(rows.get(rid)==row for rid,row in oldrows.items()),'original raw passages/mentions/fixtures changed')
    protocol=read(previous.bound(root,grant['protocol']))
    require(protocol['schema']=='lanes-context-association-protocol-v35' and protocol['candidate_attempts']==1,'single frozen comparison required')
    require(protocol['request_rows_sha256']==object_sha(request['rows']),'raw projection not frozen')
    cases=read(previous.bound(root,grant['fixtures']))
    require(len(cases)==64 and len({c['case_id']for c in cases})==64,'complete unique fictional matrix required')
    verify_fixture_qualification(root,protocol,grant['fixtures']['sha256'])
    originals=read(old_grant.parent/'fixture-joins.json')
    require([c for c in cases if c['case_id']in {x['case']['case_id']for x in originals}]==[x['case']for x in originals],
        'original forty fictional cases changed')
    case_inputs={}
    for case in cases:
        rid='fictional-'+hashlib.sha256(case['case_id'].encode()).hexdigest()[:20]
        row=rows.get(rid)
        require(row is not None and row['text']==case['record']['text'] and row['text_sha256']==case['record']['text_sha256'],'fixture raw identity mismatch')
        places=[{k:e[k]for k in ('id','start','end','text','label')}for e in case['record']['entities']
            if e['label']in {'ROAD','LANDMARK','LOCAL_AREA','BARANGAY','CITY','PROVINCE'}]
        require([{k:m[k]for k in ('id','start','end','text','label')}for m in row['mentions']]==places,'fictional mentions changed')
        case_inputs[rid]=case
    require(set(rows)-set(case_inputs)=={r['record_id']for r in baseline['rows']},'held/nontraining/extra record admission')
    for key,suffix in [('baseline_output','base/worker-output/rules.jsonl'),('v34_output','candidate/worker-output/results.jsonl')]:
        bound=previous.bound(root,protocol[key])
        require(bound.relative_to(root).as_posix().endswith('context-association-execution-20261019-v34/'+suffix),
            'wrong saved baseline evidence')
    require(protocol['review_freeze_sha256']==grant['reference_freeze']['sha256'],'reference protocol differs')
    expected_eligible=sorted('train-'+hashlib.sha256(rid.encode()).hexdigest()[:20]for rid,r in revised.items()if r['review']['disposition']!='hold')
    require(protocol['eligible_reference_ids']==expected_eligible,'revised scoreable membership differs')
    return grant,request,{'image_id':prior['image_id'],'eligible_references':len(expected_eligible)}


def execute(root: Path, docker: str, path: Path, sha: str, output: Path) -> dict:
    grant,request,metadata=preflight(root,path,sha)
    art=Path(__file__).parent/'artifacts';require(output.resolve().parent==art.resolve() and not output.exists(),'new direct private destination required')
    q.private_destination(output,art)
    with q.exclusive(art/'context-association-v35-active.lock',{'grant_sha256':sha,'output':str(output)}):
        claims=art/'context-association-v35-claims';claims.mkdir(exist_ok=True)
        q.write_new(claims/(sha+'.json'),{'output':output.name});output.mkdir()
        name='lanes-context-candidate-'+sha[:16]
        try:
            image=q.command([docker,'image','inspect',metadata['image_id']],output/'image.json');q.successful(image)
            require(json.loads(image['stdout'])[0]['Id']==metadata['image_id'],'qualified image differs')
            inputs=output/'input';inputs.mkdir();worker=output/'worker-output';worker.mkdir()
            q.write_new(inputs/'request.json',request)
            mounts={'/input':(inputs,True),'/output':(worker,False)}
            mounts.update({'/code/'+n:(root/'backend'/n,True)for n in WORKER_FILES})
            command=previous.container_args(docker,metadata['image_id'],name,mounts,
                'training/flood_ner/context_association_worker_v35.py',digest(inputs/'request.json'),WORKER_FILES)
            q.successful(q.command(command,output/'create.json'))
            r=q.command([docker,'inspect',name],output/'container.json');q.successful(r);q.verify_isolation(json.loads(r['stdout'])[0],mounts)
            started=time.monotonic()
            try:
                q.successful(q.command([docker,'start',name],output/'start.json'))
                _,ready=q.monitor(docker,name,output,worker,started)
            except BaseException:
                q.command([docker,'kill',name],output/'failed-owned-stop.json',10)
                q.command([docker,'inspect',name],output/'failed-owned-state.json',10)
                raise
            r=q.command([docker,'inspect',name],output/'completed-state.json');q.successful(r);state=json.loads(r['stdout'])[0]
            require(not state['State']['Running'] and state['State']['Pid']==0 and state['State']['ExitCode']==0 and not state['State']['OOMKilled'],'candidate worker failed')
            q.verify_isolation(state,mounts);status=read(worker/'status.json')
            require(status['status']=='completed' and status['processed']==88 and status['neural_libraries_loaded']is False and status['network_database_blocked']is True,'guarded output incomplete')
            preflight(root,path,sha)
            result={'status':'offline_successor_worker_completed','records':88,'eligible_references':metadata['eligible_references'],
                'cold_seconds':ready,'wall_seconds':time.monotonic()-started,'image_id':metadata['image_id'],
                'neural_inference':False,'training_started':False,'application_connected':False}
            q.write_new(output/'execution-status.json',result)
            return result
        except BaseException as exc:
            q.write_new(output/'failure.json',{'status':'failed','error_type':type(exc).__name__})
            raise


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--grant',type=Path,required=True);parser.add_argument('--sha256',required=True)
    parser.add_argument('--execute',action='store_true');parser.add_argument('--output',type=Path)
    parser.add_argument('--docker',default=r'C:\Program Files\Docker\Docker\resources\bin\docker.exe')
    args=parser.parse_args();root=Path(__file__).resolve().parents[3]
    if args.execute:
        require(args.output is not None,'new output required');result=execute(root,args.docker,args.grant,args.sha256,args.output)
    else:
        _,_,metadata=preflight(root,args.grant,args.sha256)
        result={'status':'verified_read_only',**metadata,'neural_inference':False,'training_started':False,'application_connected':False}
    print(json.dumps(result))


if __name__=='__main__':main()
