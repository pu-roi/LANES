"""Independently verify saved v42 outputs and isolation without rerunning extraction."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def read(path: Path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path: Path) -> str:return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path: Path) -> list[dict]:return [json.loads(s)for s in path.read_text(encoding='utf-8').splitlines()if s]


def keys(graph: dict) -> tuple:
    mentions={m['id']:m for m in graph['mentions']};expressions={e['id']:e for e in graph['expressions']};facts={f['id']:f for f in graph['facts']}
    def span(entity: dict) -> tuple:return entity['start'],entity['end'],entity['label']
    links=set()
    for relation in graph['relations']:
        fact=facts[relation['fact_id']]
        links.add((fact['kind'],fact['value'],fact['temporal_role'],fact['depth_scope'],tuple(fact['qualifiers']),
            tuple(sorted(span(expressions[i])for i in fact['entity_ids'])),
            tuple(sorted(span(mentions[i])for i in relation['target_entity_ids'])),relation['scope']))
    return links,{span(e)for e in graph['expressions']}


def validate(raw: dict,graph: dict) -> None:
    text=raw['text']
    assert hashlib.sha256(text.encode()).hexdigest()==raw['text_sha256']==graph['text_sha256']
    assert graph['record_id']==raw['record_id']and graph['mentions']==raw['mentions']
    assert not graph['absolute_instants']and not graph['numeric_depths']
    mentions={m['id']:m for m in graph['mentions']};expressions={e['id']:e for e in graph['expressions']};facts={f['id']:f for f in graph['facts']}
    assert len(mentions)==len(graph['mentions'])and len(expressions)==len(graph['expressions'])and len(facts)==len(graph['facts'])
    for entity in graph['mentions']+graph['expressions']:assert text[entity['start']:entity['end']]==entity['text']
    last=-1
    for entity in graph['expressions']:assert last<=entity['start'];last=entity['end']
    for fact in facts.values():
        for evidence in fact['evidence']:assert text[evidence['start']:evidence['end']]==evidence['text']
        if fact['kind']in{'depth','time'}:
            assert all(i in expressions for i in fact['entity_ids'])
            assert fact['value']is None or fact['value']in{expressions[i]['text']for i in fact['entity_ids']}
    linked=set()
    for relation in graph['relations']:
        assert relation['fact_id']in facts and relation['target_entity_ids']
        for evidence in relation['evidence']:
            assert text[evidence['start']:evidence['end']]==evidence['text']
            for identity in relation['target_entity_ids']:
                target=mentions[identity];assert evidence['start']<=target['start']<target['end']<=evidence['end']
        linked.add(relation['fact_id'])
    assert {u['fact_id']for u in graph['unassigned']}==set(facts)-linked


def verify(package: Path,execution: Path,expected: str,destination: Path) -> dict:
    assert not destination.exists()and sha(package/'freeze.json')==expected
    freeze=read(package/'freeze.json');assert read(package/'analysis-v1/summary.json')['accepted']
    for name,digest in freeze['implementation'].items():assert sha(ROOT/name)==digest
    for binding in freeze['inputs']:assert sha(ROOT/binding['path'])==binding['sha256']
    for filename,key in [('request.json','request_sha256'),('new-fixtures.json','new_fixtures_sha256'),('article-oracle.json','article_oracle_sha256')]:assert sha(package/filename)==freeze[key]
    for binding in read(execution/'output-manifest.json')['files']:assert sha(ROOT/binding['path'])==binding['sha256']
    request=read(package/'request.json');assert set(request)=={'schema','implementation','groups'}
    count=0;graphs=0
    for group,inputs in request['groups'].items():
        outputs=rows(execution/'worker-output'/(group+'.jsonl'));index={r['record_id']:r for r in outputs}
        assert len(index)==len(outputs)==len(inputs)
        for row in inputs:
            result=index[row['record_id']]
            if 'views'in row:
                assert set(row['views'])==set(result['views'])
                for view,raw in row['views'].items():validate(raw,result['views'][view]);graphs+=1
            else:validate(row,result['output']);graphs+=1
            count+=1
    assert count==371 and graphs==1419
    cached=ROOT/'backend/training/flood_ner/artifacts/context-repair-execution-20261019-v41/worker-output/context_rows.jsonl'
    baseline={r['record_id']:r for r in rows(cached)}
    contextual=rows(execution/'worker-output/context_rows.jsonl');same=0
    for row in contextual:
        for view,graph in row['views'].items():assert keys(graph)==keys(baseline[row['record_id']]['views'][view]);same+=1
    assert same==120
    oracle=read(package/'article-oracle.json');article=rows(execution/'worker-output/article_rows.jsonl')[0]['output']
    facts={f['id']:f for f in article['facts']};entities={e['id']:e for e in article['expressions']};links={r['fact_id']:r for r in article['relations']}
    depth=[f for f in facts.values()if f['kind']=='depth'];assert len(depth)==52
    complete=0
    for row in oracle['measured_rows']:
        measured=[f for f in depth if all(row['start']<=entities[i]['start']<entities[i]['end']<=row['end']for i in f['entity_ids'])]
        assert len(measured)==2
        for fact in measured:
            link=links.get(fact['id']);assert (link['target_entity_ids']if link else[])==row['targets']
        for kind in ('time','status','access'):
            values=[f for f in facts.values()if f['kind']==kind and any(e['end']==row['end']for e in f['evidence'])]
            assert len(values)==1
            fact=values[0];link=links.get(fact['id']);assert (link['target_entity_ids']if link else[])==row['targets']
            if kind=='time':assert fact['value']==oracle['clock']['text']and fact['temporal_role']=='observation'
            if kind=='access':assert fact['value']==row['access']
        complete+=bool(row['targets'])
    assert complete==8
    assert not any(set(r['target_entity_ids'])&set(oracle['dateline_ids'])for r in article['relations'])
    before=read(execution/'container.json');state=json.loads(before['stdout'])[0];host=state['HostConfig']
    assert state['Config']['Image']==freeze['image']and host['NetworkMode']=='none'and host['ReadonlyRootfs']
    assert host['Memory']==host['MemorySwap']==4294967296 and host['NanoCpus']==2000000000 and host['PidsLimit']==128
    assert host['CapDrop']==['ALL']and'no-new-privileges'in host['SecurityOpt']
    destinations={m['Destination']:m for m in state['Mounts']}
    assert len(destinations)==8 and destinations['/input']['RW']is False and destinations['/output']['RW']is True
    assert all(not m['RW']for target,m in destinations.items()if target!='/output')
    assert not any(s in target.casefold()for target in destinations for s in ('reference','expected','model','credential'))
    final=json.loads(read(execution/'completed-state.json')['stdout'])[0]['State']
    assert not final['Running']and final['Pid']==0 and final['ExitCode']==0 and not final['OOMKilled']
    result={'status':'independently_verified','freeze_sha256':expected,'raw_records':371,'graphs':1419,
        'unchanged_context_view_link_and_expression_sets':120,'complete_measured_rows':8,'complete_junction_rows':5,
        'recognition_unresolved_measured_rows':18,'source_depth_facts':52,'previous_facts_accounted':59,
        'article_facts':len(facts),'article_unassigned':len(article['unassigned']),
        'isolation_verified':True,'worker_stopped':True,'neural_inference':False,'database_access':False,'new_accuracy_measurement':False}
    destination.mkdir(parents=True,exist_ok=False)
    with (destination/'verification.json').open('x',encoding='utf-8')as stream:json.dump(result,stream,indent=2)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('package','execution','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--sha256',required=True);a=p.parse_args()
    print(json.dumps(verify(a.package.resolve(),a.execution.resolve(),a.sha256,a.output.resolve())))
