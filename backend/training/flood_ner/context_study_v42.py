"""Frozen v42 comparison and independent source-bound acceptance scoring."""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from .context_cases_v42 import core_cases,result as new_result
from .context_cases_v41 import result as old_result
from .location_repair_scoring_v40 import context,temporal_result
from .context_review_v37 import fixture_result

ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'backend/training/flood_ner/artifacts'
P41=ART/'context-repair-prepared-20261019-v41'
E41=ART/'context-repair-execution-20261019-v41'
P40=ART/'location-repair-prepared-20261019-v40'
ARTICLE=ART/'ner-preview-source-link-20261019-v2'
VIEWS=('original','transport_asset','shared_locality','explicit_road','combined')
WORKER={f'news_ner/{n}':'backend/app/services/news_ner/'+n for n in
        ('__init__.py','contract.py','context_association.py','context_association_v38.py','context_association_v42.py')}
WORKER['context_worker_v42.py']='backend/training/flood_ner/context_worker_v42.py'
CODE=list(WORKER.values())+['backend/training/flood_ner/context_cases_v42.py',
    'backend/training/flood_ner/context_study_v42.py','backend/tests/test_context_association_v42.py']
IMAGE='sha256:a51ce2a6b0f19f382ce96bf63c265e060b37112098176c97c66c23e887794680'


def read(path: Path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path: Path) -> str:return hashlib.sha256(path.read_bytes()).hexdigest()
def lines(path: Path) -> list[dict]:return [json.loads(s)for s in path.read_text(encoding='utf-8').splitlines()if s]
def write(path: Path,value: object) -> None:
    with path.open('x',encoding='utf-8')as stream:json.dump(value,stream,ensure_ascii=False,indent=2,sort_keys=True);stream.write('\n')
def bound(path: Path) -> dict:return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)}


def preservation() -> dict:
    for name,digest in read(P41/'freeze.json')['implementation'].items():assert sha(ROOT/name)==digest,name
    old=read(ART/'extraction-gap-assessment-20261019-v39/preservation-before.json')
    for name,entry in old['hash_bound'].items():assert sha(ROOT/name)==entry['sha256'],name
    changes=[]
    for name,entry in old['historical_metadata_only'].items():
        state=(ROOT/name).stat()
        if (state.st_size,state.st_mtime_ns)!=(entry['bytes'],entry['mtime_ns']):changes.append(name)
    assert changes==['backend/app/core/config.py'],changes
    for name,entry in old['validation_holdout_metadata_only'].items():
        state=(ROOT/name).stat();assert (state.st_size,state.st_mtime_ns)==(entry['bytes'],entry['mtime_ns']),name
    return {'v41_source_test_hashes':55,'protected_evidence_hashes':len(old['hash_bound']),
            'historical_metadata_unchanged':len(old['historical_metadata_only'])-1,
            'preexisting_declared_config_change':changes,'excluded_metadata_unchanged':len(old['validation_holdout_metadata_only']),
            'validation_holdout_content_opened':False}


def prepare(destination: Path) -> dict:
    assert not destination.exists()
    kept=preservation()
    old=read(P41/'request.json')
    source=read(ARTICLE/'saved-article-input.json')
    prior=read(ARTICLE/'database-api-response.json')['response']
    assert len(prior['neural_mentions'])==53 and prior['neural_mentions']==prior['effective_mentions'] and not prior['proposals']
    article={'record_id':prior['graph']['record_id'],'text':source['article_text'],'text_sha256':prior['graph']['text_sha256'],
        'publication':{'value':prior['source']['published_at'],'basis':'saved_article_metadata'},'mentions':deepcopy(prior['effective_mentions'])}
    assert hashlib.sha256(article['text'].encode()).hexdigest()==article['text_sha256']
    cases=core_cases()
    groups={'context_rows':old['context_rows'],'existing_rows':old['existing_rows'],'temporal_rows':old['temporal_rows'],
        'old_regressions':old['new_rows'],'new_regressions':[c['raw']for c in cases],'article_rows':[article]}
    assert sum(map(len,groups.values()))==371
    # Explicit predeclared row targets, reviewed from source words and saved
    # types. No matcher is run here; no target is inferred from a candidate.
    supported={0:['n12','n13'],6:['n21','n22'],8:['n26','n27'],10:['n31','n32'],11:['n33'],15:['n34'],22:['n48','n49'],24:['n50']}
    ledger=read(ARTICLE/'source-review-ledger.json')
    assert len(ledger['depth_rows'])==26 and len(ledger['fact_reviews'])==59
    rows=[]
    for index,row in enumerate(ledger['depth_rows']):
        rows.append({'row_index':index,'start':row['start'],'end':row['end'],'text':row['text'],
            'targets':supported.get(index,[]),'scope':'collective'if len(supported.get(index,[]))>1 else'local',
            'access':'impassable_all'if index<5 else'light_vehicle_closed'if index<7 else'passable_unspecified',
            'caution':index>=7})
    oracle={'measured_rows':rows,'clock':ledger['missed_clock'],'dateline_ids':['n0'],
        'original_facts':prior['graph']['facts'],'original_expressions':prior['graph']['expressions'],
        'unmeasured_junction':{'start':1570,'end':1604,'targets':[]},
        'recognition_unresolved_rows':[i for i in range(26)if i not in supported]}
    inputs=[P41/'freeze.json',P41/'request.json',E41/'worker-output/context_rows.jsonl',E41/'worker-output/existing_rows.jsonl',
        P41/'new-fixtures.json',P40/'freeze.json',P40/'temporal-fixtures.json',ARTICLE/'saved-article-input.json',
        ARTICLE/'database-api-response.json',ARTICLE/'source-review-ledger.json',
        ART/'extraction-gap-assessment-20261019-v39/preservation-before.json']
    f40=read(P40/'freeze.json')
    for key in ('context_references','existing_fixtures'):
        binding=f40[key];path=ROOT/binding['path'];assert sha(path)==binding['sha256'];inputs.append(path)
    destination.mkdir(parents=True,exist_ok=False)
    request={'schema':'lanes-context-worker-v42','implementation':{name:sha(ROOT/path)for name,path in WORKER.items()},'groups':groups}
    write(destination/'request.json',request);write(destination/'new-fixtures.json',cases);write(destination/'article-oracle.json',oracle)
    write(destination/'preservation.json',kept)
    freeze={'schema':'lanes-context-freeze-v42','image':IMAGE,'attempts':1,'raw_records':371,'graphs':1419,
        'implementation':{name:sha(ROOT/name)for name in CODE},'inputs':[bound(path)for path in inputs],
        'request_sha256':sha(destination/'request.json'),'new_fixtures_sha256':sha(destination/'new-fixtures.json'),
        'article_oracle_sha256':sha(destination/'article-oracle.json'),
        'acceptance':'all_fixtures_no_new_incorrect_no_supported_loss_exact_spans_qualifiers_all_26_rows_and_59_facts_reconciled',
        'recognition_unresolved_is_not_recovery':True,'no_post_result_tuning':True}
    write(destination/'freeze.json',freeze)
    return {'status':'frozen','freeze_sha256':sha(destination/'freeze.json'),'raw_records':371}


def check(package: Path) -> dict:
    freeze=read(package/'freeze.json')
    assert freeze['schema']=='lanes-context-freeze-v42'and freeze['attempts']==1 and freeze['image']==IMAGE
    for name,digest in freeze['implementation'].items():assert sha(ROOT/name)==digest,name
    for binding in freeze['inputs']:assert sha(ROOT/binding['path'])==binding['sha256'],binding['path']
    for name,key in [('request.json','request_sha256'),('new-fixtures.json','new_fixtures_sha256'),('article-oracle.json','article_oracle_sha256')]:
        assert sha(package/name)==freeze[key]
    preservation()
    return freeze


def command(args: list[str],receipt: Path,timeout: int=30) -> dict:
    try:
        result=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',timeout=timeout)
        value={'args':args,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
    except subprocess.TimeoutExpired as exc:
        value={'args':args,'returncode':None,'error_type':type(exc).__name__}
    write(receipt,value)
    return value


def execute(package: Path,destination: Path,docker: str) -> dict:
    freeze=check(package)
    assert not destination.exists()
    claim=ART/('context-v42-'+sha(package/'freeze.json')+'.claim.json')
    write(claim,{'destination':destination.name,'attempts':1})
    destination.mkdir();raw=destination/'input';raw.mkdir();worker=destination/'worker-output';worker.mkdir()
    write(raw/'request.json',read(package/'request.json'))
    name='lanes-context-v42-'+sha(package/'freeze.json')[:16]
    mounts={'/input':(raw,True),'/output':(worker,False),**{'/code/'+n:(ROOT/p,True)for n,p in WORKER.items()}}
    args=[docker,'create','--name',name,'--network','none','--cpus','2','--memory','4g','--memory-swap','4g',
        '--pids-limit','128','--read-only','--restart=no','--cap-drop=ALL','--security-opt=no-new-privileges',
        '--tmpfs','/tmp:rw,noexec,nosuid,size=64m','--entrypoint','python','--pull=never']
    for target,(source,readonly)in mounts.items():
        assert ','not in str(source)
        args+=['--mount',f'type=bind,source={source.resolve()},target={target}'+(',readonly'if readonly else'')]
    args+=['--env','PYTHONDONTWRITEBYTECODE=1',IMAGE,'-I','-B','/code/context_worker_v42.py',sha(raw/'request.json')]
    created=False
    try:
        r=command([docker,'image','inspect',IMAGE],destination/'image.json');assert r['returncode']==0
        r=command(args,destination/'create.json');assert r['returncode']==0;created=True
        r=command([docker,'inspect',name],destination/'container.json');assert r['returncode']==0
        state=json.loads(r['stdout'])[0];host=state['HostConfig']
        assert state['Config']['Image']==IMAGE and host['NetworkMode']=='none'and host['ReadonlyRootfs']
        assert host['Memory']==host['MemorySwap']==4294967296 and host['NanoCpus']==2000000000 and host['PidsLimit']==128
        assert host['CapDrop']==['ALL']and'no-new-privileges'in host['SecurityOpt']
        actual={m['Destination']:m for m in state['Mounts']};assert set(actual)==set(mounts)
        for target,(source,readonly)in mounts.items():assert actual[target]['RW']is not readonly and Path(actual[target]['Source']).resolve()==source.resolve()
        r=command([docker,'start','--attach',name],destination/'run.json',300);assert r['returncode']==0
        r=command([docker,'inspect',name],destination/'completed-state.json');assert r['returncode']==0
        state=json.loads(r['stdout'])[0]['State'];assert not state['Running']and state['Pid']==0 and state['ExitCode']==0 and not state['OOMKilled']
        status=read(worker/'status.json');assert status['status']=='completed'and status['raw_records']==371 and status['graphs']==1419
        check(package)
        write(destination/'output-manifest.json',{'files':[bound(p)for p in sorted(worker.iterdir())if p.is_file()]})
        return {'status':'completed','raw_records':371,'graphs':1419,'neural_inference':False}
    except BaseException as exc:
        if created:command([docker,'kill',name],destination/'failed-stop.json')
        write(destination/'failure.json',{'error_type':type(exc).__name__,'retry_allowed':False})
        raise


def article_score(raw: dict,graph: dict,oracle: dict) -> dict:
    """Independent checks of the predeclared source rows; never a recognizer."""
    from app.services.news_ner.context_association_v42 import validate_output
    validate_output(raw,graph)
    expressions={e['id']:e for e in graph['expressions']}
    original_expressions={e['id']:e for e in oracle['original_expressions']}
    relations={r['fact_id']:r for r in graph['relations']}
    failures=[];rows=[]
    original_depth={(e['start'],e['end'],e['text'])for e in original_expressions.values()if e['label']=='DEPTH'}
    current_depth={(e['start'],e['end'],e['text'])for e in expressions.values()if e['label']=='DEPTH'}
    if original_depth!=current_depth or len(current_depth)!=52:failures.append('depth_span_preservation')
    def signature(fact: dict,entities: dict) -> tuple:
        return (fact['kind'],fact['value'],tuple((entities[i]['start'],entities[i]['end'],entities[i]['label'])for i in fact['entity_ids']),
                tuple((e['start'],e['end'])for e in fact['evidence']))
    candidate={signature(f,expressions):f for f in graph['facts']}
    dispositions=[]
    for fact in oracle['original_facts']:
        after=candidate.get(signature(fact,original_expressions))
        lost=[]if after is not None else['source_fact_missing']
        if after is not None:
            qualifiers=' '.join(after['qualifiers']).casefold()
            if any(q.casefold()not in qualifiers for q in fact['qualifiers']):lost.append('qualifier_loss')
        dispositions.append({'previous_fact_id':fact['id'],'preserved':not lost,'checks':lost})
    if not all(d['preserved']for d in dispositions):failures.append('original_fact_or_qualifier_loss')
    clock=oracle['clock']
    clocks=[e for e in expressions.values()if e['label']=='TIME'and(e['start'],e['end'],e['text'])==(clock['start'],clock['end'],clock['text'])]
    if len(clocks)!=1:failures.append('missing_exact_clock')
    for row in oracle['measured_rows']:
        depth=[f for f in graph['facts']if f['kind']=='depth'and f['entity_ids']and all(row['start']<=expressions[i]['start']<expressions[i]['end']<=row['end']for i in f['entity_ids'])]
        wrong=[]
        if len(depth)!=2:wrong.append('depth_fact_count')
        for fact in depth:
            relation=relations.get(fact['id'])
            targets=relation['target_entity_ids']if relation else[]
            if targets!=row['targets']:wrong.append('depth_targets')
            if targets and relation['scope']!=row['scope']:wrong.append('depth_scope')
        inherited=[f for f in graph['facts']if f['kind']in{'time','status','access'}and any(e['end']==row['end']for e in f['evidence'])]
        for kind in ('time','status','access'):
            entries=[f for f in inherited if f['kind']==kind]
            if len(entries)!=1:wrong.append(kind+'_count');continue
            fact=entries[0];relation=relations.get(fact['id'])
            if (relation['target_entity_ids']if relation else[])!=row['targets']:wrong.append(kind+'_targets')
            if kind=='time'and(fact['value']!=clock['text']or fact['temporal_role']!='observation'):wrong.append('time_role')
            if kind=='status'and fact['value']!='active':wrong.append('status')
            if kind=='access':
                if fact['value']!=row['access']:wrong.append('access_value')
                if row['caution']and not any('with caution'in q.casefold()for q in fact['qualifiers']):wrong.append('caution_qualifier')
        rows.append({'row_index':row['row_index'],'passed':not wrong,'checks':wrong,'recognition_unresolved':not row['targets']})
    if not all(r['passed']for r in rows):failures.append('measured_row_dispositions')
    if any(set(r['target_entity_ids'])&set(oracle['dateline_ids'])for r in graph['relations']):failures.append('dateline_flood_target')
    nominal=oracle['unmeasured_junction']
    for fact in graph['facts']:
        if any(e['end']==nominal['end']for e in fact['evidence']):
            r=relations.get(fact['id'])
            if r is not None:failures.append('incomplete_unmeasured_junction_resolved')
    if any(f['kind']=='time'and f['temporal_role']=='onset'and f['value']==clock['text']for f in graph['facts']):failures.append('onset_invented')
    return {'passed':not failures,'failures':failures,'rows':rows,'previous_facts':dispositions,
            'source_depth_facts_retained':52,'previous_facts_accounted':len(dispositions),
            'complete_measured_rows':sum(bool(r['targets'])for r in oracle['measured_rows']),
            'recognition_unresolved_measured_rows':len(oracle['recognition_unresolved_rows']),
            'complete_junction_rows':sum(len(r['targets'])>1 for r in oracle['measured_rows']),
            'facts':len(graph['facts']),'unassigned':len(graph['unassigned'])}


def score(package: Path,execution: Path,destination: Path) -> dict:
    assert not destination.exists();freeze=check(package)
    for binding in read(execution/'output-manifest.json')['files']:assert sha(ROOT/binding['path'])==binding['sha256']
    request=read(package/'request.json')['groups']
    groups={}
    for name,raws in request.items():
        values=lines(execution/'worker-output'/(name+'.jsonl'));byid={r['record_id']:r for r in values}
        assert len(byid)==len(values)==len(raws)and set(byid)=={r['record_id']for r in raws}
        groups[name]=byid
    existing_path=ROOT/read(P40/'freeze.json')['existing_fixtures']['path']
    refs=read(ROOT/read(P40/'freeze.json')['context_references']['path'])
    previous={r['record_id']:r for r in lines(E41/'worker-output/context_rows.jsonl')}
    fixture_cases=read(existing_path);temporal_cases=read(P40/'temporal-fixtures.json');old_cases=read(P41/'new-fixtures.json')
    tests={
        'temporal':[temporal_result(c,groups['temporal_rows'][c['raw']['record_id']]['output'])for c in temporal_cases],
        'v41_regressions':[old_result(c,groups['old_regressions'][c['raw']['record_id']]['output'])for c in old_cases],
        'v42_regressions':[new_result(c,groups['new_regressions'][c['raw']['record_id']]['output'])for c in read(package/'new-fixtures.json')]}
    views={};details={}
    for view in VIEWS:
        old_tests=[]
        for case in fixture_cases:
            rid='fictional-'+hashlib.sha256(case['case_id'].encode()).hexdigest()[:20]
            raw=next(r for r in request['existing_rows']if r['record_id']==rid)['views'][view]
            old_tests.append(fixture_result(case,raw,groups['existing_rows'][rid]['views'][view],
                exhaustive=case['case_id'].startswith(('fictional-v36_','fictional-v37_','fictional-v38_'))))
        comparisons=[]
        for item in refs:
            rid=item['record_id']
            comparisons.append({'record_id':rid,**context(item['revised_reference'],previous[rid]['views'][view],groups['context_rows'][rid]['views'][view])})
        flags={'existing_fixture_failures':sum(not t['passed']for t in old_tests),
            'new_incorrect':sum(len(c['introduced_fp'])for c in comparisons),
            'supported_lost':sum(len(c['lost_correct'])for c in comparisons),
            'qualifier_losses':sum(len(c['qualifier_errors'])for c in comparisons),
            'span_regressions':sum(len(v[k])for c in comparisons for v in c['expression_regressions'].values()for k in ('new_fp','new_fn'))}
        views[view]={'checks':flags,'counts':{k:sum(c['counts'][k]for c in comparisons)for k in ('tp','fp','fn')}}
        details[view]={'existing_fixtures':old_tests,'context':comparisons}
    raw=request['article_rows'][0]
    article=article_score(raw,groups['article_rows'][raw['record_id']]['output'],read(package/'article-oracle.json'))
    accepted=all(t['passed']for values in tests.values()for t in values)and all(not any(v['checks'].values())for v in views.values())and article['passed']
    summary={'accepted':accepted,'views':views,'fixtures':{k:{'passed':sum(t['passed']for t in values),'total':len(values)}for k,values in tests.items()},
        'article':{k:v for k,v in article.items()if k not in{'rows','previous_facts'}},'raw_records':371,'graphs':1419,
        'references_unchanged':True,'three_holds_retained':True,'neural_inference':False,'database_access':False,
        'new_accuracy_measurement':False,'no_post_result_tuning':True,'application_promoted':False,'preservation':preservation()}
    destination.mkdir();write(destination/'summary.json',summary);write(destination/'fixture-results.json',tests)
    write(destination/'context-details.json',details);write(destination/'article-dispositions.json',article)
    write(destination/'manifest.json',{'files':[bound(p)for p in sorted(destination.iterdir())if p.is_file()]})
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','check','execute','score'))
    p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path);p.add_argument('--execution',type=Path)
    p.add_argument('--docker',default='C:/Program Files/Docker/Docker/resources/bin/docker.exe');a=p.parse_args()
    if a.action=='prepare':value=prepare(a.package.resolve())
    elif a.action=='execute':value=execute(a.package.resolve(),a.output.resolve(),a.docker)
    elif a.action=='score':value=score(a.package.resolve(),a.execution.resolve(),a.output.resolve())
    else:check(a.package.resolve());value={'status':'frozen_bindings_verified'}
    print(json.dumps(value))
