"""Single frozen context-only successor study using unchanged cached locations."""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from . import location_repair_study_v40 as prior
from . import context_run_v38 as original
from . import context_association_run as transport
from . import linux_runtime_v29 as runtime

ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'backend/training/flood_ner/artifacts'
P40=ART/'location-repair-prepared-20261019-v40'
E40=ART/'location-repair-execution-20261019-v40'
OLD_SHA='990c387cc4218e2490c0bb820ea8a0e42bd730223ff4be4c5393213317b7b65a'
VIEWS=('original','transport_asset','shared_locality','explicit_road','combined')
WORKER_FILES=tuple(sorted(set(original.WORKER_FILES)|{'training/flood_ner/context_association_v41.py','training/flood_ner/context_worker_v41.py'}))
CODE=tuple(sorted(set(prior.CODE)|{'backend/'+n for n in WORKER_FILES}|{
    'backend/training/flood_ner/context_cases_v41.py','backend/training/flood_ner/context_study_v41.py',
    'backend/tests/test_context_association_v41.py'}))


def require(ok: bool,reason: str) -> None:
    if not ok:raise ValueError(reason)


def read(p: Path) -> Any:return json.loads(p.read_text(encoding='utf-8'))
def lines(p: Path) -> list[dict]:return [json.loads(s)for s in p.read_text(encoding='utf-8').splitlines()if s]
def sha(p: Path) -> str:return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p: Path,value: Any) -> None:
    with p.open('x',encoding='utf-8',newline='\n')as f:json.dump(value,f,ensure_ascii=False,indent=2,sort_keys=True);f.write('\n')
def binding(p: Path) -> dict:return {'path':p.resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def checked(b: dict) -> Path:
    p=transport.checked_path(ROOT,b['path']);require(sha(p)==b['sha256'],'stale input: '+b['path']);return p


def preserved() -> dict:
    prior.preflight(P40/'freeze.json',OLD_SHA)
    for manifest in [E40/'output-manifest.json',P40/'analysis-v1/manifest.json']:
        for b in read(manifest)['files']:checked(b)
    return prior.preserve()


def prepare(package: Path,test_receipt: Path) -> dict:
    from .context_cases_v41 import core_cases
    from .context_acceptance import validate_raw_input
    prior.fresh(package);preservation=preserved()
    code={n:sha(ROOT/n)for n in CODE};test=read(test_receipt)
    require(test['source_hashes']==code and test['returncode']==0 and test['output_complete']is True
            and 'backend/tests/test_context_association_v41.py'in test['args'],'unbound/failed tests')
    oldfreeze=read(P40/'freeze.json');oldrequest=read(P40/'request.json')
    cached={group:{r['record_id']:r for r in lines(E40/'worker-output'/(group+'.jsonl'))}
            for group in ('context_rows','existing_rows')}
    request={'schema':'lanes-context-repair-worker-v41','implementation':{n:code['backend/'+n]for n in WORKER_FILES}}
    for group in ('context_rows','existing_rows'):
        values=[]
        for row in oldrequest[group]:
            result=cached[group][row['record_id']];views={'original':deepcopy(row)}
            for method in prior.METHODS:
                repair=result['methods'][method]['repair']
                require(repair['neural_mentions']==row['mentions'],'cached neural identity differs')
                view=deepcopy(row);view['mentions']=repair['effective_mentions'];validate_raw_input(view);views[method]=view
            values.append({'record_id':row['record_id'],'views':views})
        request[group]=values
    new_cases=core_cases();require(len(new_cases)==36,'36 new fixed cases required')
    request['temporal_rows']=oldrequest['temporal_rows'];request['new_rows']=[c['raw']for c in new_cases]
    for raw in request['temporal_rows']+request['new_rows']:validate_raw_input(raw)
    package.mkdir();write(package/'new-fixtures.json',new_cases);write(package/'request.json',request)
    write(package/'preservation.json',preservation)
    inputs=[P40/'freeze.json',P40/'request.json',P40/'temporal-fixtures.json',P40/'location-fixtures.json',
            P40/'analysis-v1/manifest.json',P40/'analysis-v1/summary.json',E40/'output-manifest.json',
            E40/'worker-output/training_rows.jsonl',E40/'worker-output/location_rows.jsonl',
            E40/'worker-output/context_rows.jsonl',E40/'worker-output/existing_rows.jsonl',E40/'worker-output/temporal_rows.jsonl',
            checked(oldfreeze['context_references']),checked(oldfreeze['existing_fixtures']),checked(oldfreeze['previous_context']),
            checked(oldfreeze['seven_errors']),test_receipt,package/'request.json',package/'new-fixtures.json',package/'preservation.json']
    freeze={'schema':'lanes-context-freeze-v41','implementation':code,'inputs':[binding(p)for p in inputs],
            'request':binding(package/'request.json'),'new_fixtures':binding(package/'new-fixtures.json'),
            'previous_freeze':binding(P40/'freeze.json'),'test_receipt':binding(test_receipt),
            'views':list(VIEWS),'image_id':prior.IMAGE,'attempts':1,'raw_records':334,
            'counts':{'context':24,'existing':238,'temporal':36,'new':36,'eligible':23,'held':3},
            'no_post_result_tuning':True,'location_proposals_unchanged':True,
            'acceptance':'all_310_fixtures_zero_new_wrong_zero_correct_loss_both_collective_misses_and_transport_gains_retained'}
    write(package/'freeze.json',freeze)
    return {'status':'frozen','sha256':sha(package/'freeze.json'),'raw_records':334,'preservation':preservation}


def preflight(path: Path,expected_sha: str) -> tuple[dict,dict]:
    require(sha(path)==expected_sha,'stale freeze');freeze=read(path)
    require(freeze['schema']=='lanes-context-freeze-v41'and freeze['attempts']==1 and freeze['views']==list(VIEWS)
            and freeze['no_post_result_tuning']and freeze['location_proposals_unchanged'],'protocol differs')
    require(set(freeze['implementation'])==set(CODE),'incomplete code binding')
    for n,h in freeze['implementation'].items():require(sha(ROOT/n)==h,'code/tests changed')
    for b in freeze['inputs']:checked(b)
    request=read(checked(freeze['request']))
    require(request['implementation']=={n:freeze['implementation']['backend/'+n]for n in WORKER_FILES},'worker closure differs')
    for key,count in [('context_rows',24),('existing_rows',238),('temporal_rows',36),('new_rows',36)]:
        rows=request[key];require(len(rows)==len({r['record_id']for r in rows})==count,'frozen group differs')
        for row in rows:
            raw_values=row['views'].values()if key in {'context_rows','existing_rows'}else[row]
            if key in {'context_rows','existing_rows'}:require(set(row)=={'record_id','views'}and set(row['views'])==set(VIEWS),'cached views differ')
            for value in raw_values:
                require(set(value)=={'record_id','text','text_sha256','publication','mentions'},'reference/expected data in worker input')
    preserved();return freeze,request


def execute(path: Path,expected_sha: str,output: Path,docker: str) -> dict:
    freeze,request=preflight(path,expected_sha);prior.fresh(output)
    with runtime.exclusive(ART/'context-v41-active.lock',{'freeze_sha256':expected_sha}):
        claims=ART/'context-v41-claims';claims.mkdir(exist_ok=True)
        write(claims/(expected_sha+'.json'),{'output':output.name});output.mkdir()
        name='lanes-context-candidate-'+expected_sha[:16];created=False
        try:
            r=runtime.command([docker,'image','inspect',freeze['image_id']],output/'image.json');runtime.successful(r)
            require(json.loads(r['stdout'])[0]['Id']==prior.IMAGE,'qualified image differs')
            raw=output/'input';raw.mkdir();worker=output/'worker-output';worker.mkdir();write(raw/'request.json',request)
            mounts={'/input':(raw,True),'/output':(worker,False)}
            mounts.update({'/code/'+n:(ROOT/'backend'/n,True)for n in WORKER_FILES})
            command=transport.container_args(docker,freeze['image_id'],name,mounts,'training/flood_ner/context_worker_v41.py',sha(raw/'request.json'),WORKER_FILES)
            runtime.successful(runtime.command(command,output/'create.json'));created=True
            r=runtime.command([docker,'inspect',name],output/'container.json');runtime.successful(r)
            runtime.verify_isolation(json.loads(r['stdout'])[0],mounts)
            started=time.monotonic();runtime.successful(runtime.command([docker,'start',name],output/'start.json'))
            _,cold=runtime.monitor(docker,name,output,worker,started)
            r=runtime.command([docker,'inspect',name],output/'completed-state.json');runtime.successful(r);state=json.loads(r['stdout'])[0]
            runtime.verify_isolation(state,mounts)
            require(not state['State']['Running']and state['State']['Pid']==0 and state['State']['ExitCode']==0 and not state['State']['OOMKilled'],'worker failed')
            status=read(worker/'status.json')
            require(status['status']=='completed'and status['processed']==334 and not status['neural_libraries_loaded']
                    and not status['location_recognition_rerun']and status['network_database_blocked'],'incomplete worker')
            preflight(path,expected_sha)
            result={'status':'completed','records':334,'image_id':prior.IMAGE,'cold_seconds':cold,'wall_seconds':time.monotonic()-started,
                    'neural_inference':False,'location_recognition_rerun':False,'training_started':False,'application_connected':False}
            write(output/'execution.json',result)
            write(output/'output-manifest.json',{'files':[binding(f)for f in sorted(worker.iterdir())if f.is_file()]})
            return result
        except BaseException as exc:
            if created:
                runtime.command([docker,'kill',name],output/'failed-owned-stop.json',10)
                runtime.command([docker,'inspect',name],output/'failed-owned-state.json',10)
            write(output/'failure.json',{'error_type':type(exc).__name__,'reason':str(exc),'retry_allowed':False});raise


def score(path: Path,expected_sha: str,execution: Path,destination: Path) -> dict:
    from .context_cases_v41 import result as new_result
    from .location_repair_scoring_v40 import context,temporal_result
    from .context_review_v37 import fixture_result
    from .context_association_scoring import output_keys,json_key
    freeze,request=preflight(path,expected_sha)
    require(not destination.exists()and destination.parent==path.parent,'new analysis destination required')
    require(read(execution/'execution.json')['status']=='completed','completed worker required')
    for b in read(execution/'output-manifest.json')['files']:checked(b)
    groups={}
    for group in ('context_rows','existing_rows','temporal_rows','new_rows'):
        rows=lines(execution/'worker-output'/(group+'.jsonl'));groups[group]={r['record_id']:r for r in rows}
        require(len(rows)==len(groups[group])==len(request[group])and set(groups[group])=={r['record_id']for r in request[group]},'output joins differ')
    oldfreeze=read(P40/'freeze.json')
    ref={r['record_id']:r for r in read(checked(oldfreeze['context_references']))}
    old={r['record_id']:r for r in lines(checked(oldfreeze['previous_context']))}
    cached={r['record_id']:r for r in lines(E40/'worker-output/context_rows.jsonl')}
    time_cases=read(P40/'temporal-fixtures.json');old_cases=read(checked(oldfreeze['existing_fixtures']))
    new_cases=read(checked(freeze['new_fixtures']));errors=read(checked(oldfreeze['seven_errors']))
    times=[temporal_result(c,groups['temporal_rows'][c['raw']['record_id']]['output'])for c in time_cases]
    new=[new_result(c,groups['new_rows'][c['raw']['record_id']]['output'])for c in new_cases]
    base_new=[new_result(c,groups['new_rows'][c['raw']['record_id']]['baseline'])for c in new_cases]
    summaries={};details={};dispositions={}
    for view in VIEWS:
        contextual=[];existing=[];v38_lost=[]
        for rid,item in ref.items():
            baseline=old[rid]if view=='original'else cached[rid]['methods'][view]['context']
            candidate=groups['context_rows'][rid]['views'][view]
            contextual.append({'record_id':rid,**context(item['revised_reference'],baseline,candidate)})
            v38_lost.extend(context(item['revised_reference'],old[rid],candidate)['lost_correct'])
        for case in old_cases:
            rid='fictional-'+hashlib.sha256(case['case_id'].encode()).hexdigest()[:20]
            row=next(r for r in request['existing_rows']if r['record_id']==rid)['views'][view]
            existing.append(fixture_result(case,row,groups['existing_rows'][rid]['views'][view],exhaustive=case['case_id'].startswith(('fictional-v36_','fictional-v37_','fictional-v38_'))))
        flags={'temporal_failures':sum(not r['passed']for r in times),'new_fixture_failures':sum(not r['passed']for r in new),
               'existing_fixture_failures':sum(not r['passed']for r in existing),
               'new_incorrect_associations':sum(len(r['introduced_fp'])for r in contextual),
               'lost_correct_associations':sum(len(r['lost_correct'])for r in contextual),
               'lost_v38_correct':len(v38_lost),'qualifier_failures':sum(len(r['qualifier_errors'])for r in contextual),
               'expression_regressions':sum(len(v[k])for r in contextual for v in r['expression_regressions'].values()for k in ('new_fp','new_fn'))}
        counts={k:sum(r['counts'][k]for r in contextual)for k in ('tp','fp','fn')}
        dispositions[view]=[]
        for error in errors:
            keys={json_key(k)for k in output_keys(groups['context_rows'][error['opaque_id']]['views'][view])['links']}
            dispositions[view].append({'error_id':error['error_id'],'kind':error['strict_key'][0][0],
                                       'recovered':json_key(error['strict_key'])in keys})
        summaries[view]={'counts':counts,'checks':flags,'seven_misses_recovered':sum(r['recovered']for r in dispositions[view]),
                         'gained_correct':sum(len(r['gained_correct'])for r in contextual),
                         'qualifies_context_checks':not any(flags.values())and counts['fp']==0}
        details[view]={'context':contextual,'existing_fixtures':existing}
    # Positive recovery is mandatory in the combined corrected-location view.
    combined=dispositions['combined'];transport=dispositions['transport_asset']
    targets=[e['error_id']for e in errors if e['strict_key'][2]=='collective'and
             all(target[2]=='LOCAL_AREA'for target in e['strict_key'][1])]
    required_transport={d['error_id']for d in read(P40/'analysis-v1/seven-error-dispositions.json')['transport_asset']if d['recovered']}
    collective_recovered=all(d['recovered']for d in combined if d['error_id']in targets)and len(targets)==2
    transport_retained=all(d['recovered']for d in transport+combined if d['error_id']in required_transport)
    accepted=all(s['qualifies_context_checks']for s in summaries.values())and collective_recovered and transport_retained
    destination.mkdir();write(destination/'details.json',details);write(destination/'temporal-results.json',times)
    write(destination/'new-fixture-results.json',{'candidate':new,'baseline':base_new})
    write(destination/'seven-error-dispositions.json',dispositions)
    summary={'accepted':accepted,'views':summaries,'temporal_passed':sum(r['passed']for r in times),'temporal_total':36,
             'new_fixture_passed':sum(r['passed']for r in new),'new_fixture_total':36,
             'new_fixture_baseline_passed':sum(r['passed']for r in base_new),
             'collective_misses_recovered_in_combined':collective_recovered,'four_transport_recoveries_retained':transport_retained,
             'references_unchanged':True,'three_holds_retained':True,'generalization_claim':False,
             'learned_depth_time_unfinished':True,'pure_tagalog_real_performance':'unmeasured',
             'application_connected':False,'location_recognition_rerun':False,'no_post_result_tuning':True}
    write(destination/'summary.json',summary);write(destination/'preservation.json',preserved())
    write(destination/'manifest.json',{'files':[binding(f)for f in sorted(destination.iterdir())if f.is_file()]})
    return summary


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','verify','execute','score'))
    p.add_argument('--package',type=Path);p.add_argument('--test-receipt',type=Path);p.add_argument('--freeze',type=Path)
    p.add_argument('--sha256');p.add_argument('--output',type=Path);p.add_argument('--execution',type=Path)
    p.add_argument('--docker',default=r'C:\Program Files\Docker\Docker\resources\bin\docker.exe');a=p.parse_args()
    if a.action=='prepare':result=prepare(a.package,a.test_receipt)
    elif a.action=='execute':result=execute(a.freeze,a.sha256,a.output,a.docker)
    elif a.action=='score':result=score(a.freeze,a.sha256,a.execution,a.output)
    else:preflight(a.freeze,a.sha256);result={'status':'verified_read_only','records':334}
    print(json.dumps(result))


if __name__=='__main__':main()
