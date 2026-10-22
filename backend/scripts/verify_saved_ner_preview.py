"""Independently verify saved preview receipts without neural inference or retries."""
import argparse
import ast
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.schemas.news_ner_preview import NerPreview
from app.services.news_ner.bundle import digest, verify_bundle
from app.services.news_ner.contract import IMAGE, object_sha
from app.services.news_ner.context_association_v41 import extract, validate_output
from app.services.news_ner.location_repair_v40 import propose
from app.services.news_ner.projection import project

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'backend/training/flood_ner/artifacts'


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def verify(attempt: Path, bundle: Path, docker: str, output: Path) -> dict:
    if output.exists() or not output.resolve().is_relative_to(ART.resolve()):
        raise ValueError('new private verification destination required')
    freeze=read(attempt/'freeze.json')
    for name,sha in freeze['implementation'].items():assert digest(ROOT/name)==sha,name
    for binding in freeze['source_bindings'].values():assert digest(ROOT/binding['path'])==binding['sha256']
    assert digest(attempt/'workload.json')==freeze['workload_sha256']
    workload=read(attempt/'workload.json')
    assert len(workload)==9 and len(list(attempt.glob('response-*.json')))==9
    bundle_value=verify_bundle(bundle,freeze['bundle_sha256'])
    package=ROOT/'backend/app/services/news_ner'
    code={p.name:digest(p)for p in package.glob('*.py')}
    code['promotion.json']=digest(package/'promotion.json')
    measures=[]
    for index,case in enumerate(workload):
        saved=read(attempt/f'response-{index:02}.json')
        assert saved['id']==case['id'] and saved['status']==200
        response=saved['response'];NerPreview.model_validate(response)
        assert response['source']['text_sha256']==case['text_sha256']
        snapshot={'article_id':7,'canonical_url':'https://example.invalid/adapter-check',
            'publisher_source_id':'adapter-check','article_text':case['text'],'published_at':None}
        assert response['source']['input_sha256']==object_sha(snapshot)
        raw={'record_id':'preview-'+object_sha(snapshot),'text':case['text'],'text_sha256':case['text_sha256'],
             'publication':None,'mentions':response['effective_mentions']}
        validate_output(raw,response['graph'])
        assert response['graph']==extract(raw)
        assert response['groups']==project(raw,response['graph'])
        proposal=propose({'record_id':raw['record_id'],'text':raw['text'],'mentions':response['neural_mentions']})
        for name in ('effective_mentions','proposals','abstentions'):assert response[name]==proposal[name]
        if case['expected'] is not None:
            assert [{k:m[k]for k in ('start','end','text','label')}for m in response['neural_mentions']]==case['expected']
        provenance=response['provenance']
        assert provenance['image']==IMAGE and provenance['code_sha256']==object_sha(code)
        assert provenance['bundle_sha256']==freeze['bundle_sha256']
        assert provenance['model_manifest_sha256']==bundle_value['model_manifest_sha256']
        assert provenance['resource_manifest_sha256']==bundle_value['resource_manifest_sha256']
        assert provenance['tokenizer_sha256']==bundle_value['files']['model/tokenizer']['sha256']
        expected_neural=object_sha({'bundle':freeze['bundle_sha256'],'tokenizer':provenance['tokenizer_sha256'],'text':case['text_sha256']})
        assert all(m['provenance_sha256']==expected_neural for m in response['neural_mentions'])
        measurement=response['measurements']
        assert 0<measurement['cold_seconds']<60 and 0<=measurement['extraction_seconds']<30
        assert 0<measurement['peak_worker_rss_bytes']<=3*1024**3
        measures.append(measurement)
    request=read(ROOT/freeze['source_bindings']['context_request']['path'])['context_rows']
    cached={r['record_id']:r['views']for r in map(json.loads,(ROOT/freeze['source_bindings']['context_outputs']['path']).read_text(encoding='utf-8').splitlines())}
    count=0
    for row in request:
        assert len(row['views'])==5
        for name,raw in row['views'].items():
            assert extract(raw)==cached[row['record_id']][name]
            count+=1
    assert count==120
    old_freeze=read(ROOT/freeze['source_bindings']['v41_freeze']['path'])
    for name,sha in old_freeze['implementation'].items():assert digest(ROOT/name)==sha
    old=read(ROOT/freeze['source_bindings']['preservation']['path'])
    for name,entry in old['hash_bound'].items():assert digest(ROOT/name)==entry['sha256'],name
    changed=[]
    for name,entry in old['historical_metadata_only'].items():
        state=(ROOT/name).stat()
        if (state.st_size,state.st_mtime_ns)!=(entry['bytes'],entry['mtime_ns']):changed.append(name)
    assert changed==['backend/app/core/config.py'],changed
    # The legacy metadata set includes application code. Verify the only
    # authorized change against the clean pre-task Git version structurally;
    # preserve its original receipt instead of rewriting the old baseline.
    original=subprocess.run(['git','show','HEAD:backend/app/core/config.py'],cwd=ROOT,capture_output=True,check=True).stdout.decode('utf-8')
    current=(ROOT/'backend/app/core/config.py').read_text(encoding='utf-8')
    tree=ast.parse(current)
    fields={'NEWS_NER_PREVIEW_ENABLED','NEWS_NER_PREVIEW_BUNDLE','NEWS_NER_PREVIEW_BUNDLE_SHA256','NEWS_NER_PREVIEW_DOCKER'}
    removed=[]
    for node in tree.body:
        if isinstance(node,ast.ClassDef)and node.name=='Settings':
            kept=[]
            for child in node.body:
                if isinstance(child,ast.AnnAssign)and isinstance(child.target,ast.Name)and child.target.id in fields:removed.append(child.target.id)
                else:kept.append(child)
            node.body=kept
    assert set(removed)==fields and len(removed)==4
    assert ast.dump(tree,include_attributes=False)==ast.dump(ast.parse(original),include_attributes=False)
    assert 'NEWS_NER_PREVIEW_ENABLED: bool = False' in current
    for name,entry in old['validation_holdout_metadata_only'].items():
        state=(ROOT/name).stat()
        assert (state.st_size,state.st_mtime_ns)==(entry['bytes'],entry['mtime_ns']),name
    live=read(attempt/'live-container-inspection.json');host=live['HostConfig']
    assert live['Config']['Image']==IMAGE and host['ReadonlyRootfs']and host['NetworkMode']=='none'
    assert host['Memory']==host['MemorySwap']==4294967296 and host['NanoCpus']==2000000000 and host['PidsLimit']==128
    assert host['CapDrop']==['ALL']and 'no-new-privileges'in host['SecurityOpt']
    assert len(live['Mounts'])==2 and all(not m['RW'] for m in live['Mounts'])
    assert {m['Destination']for m in live['Mounts']}=={'/assets','/code/news_ner'}
    stopped=subprocess.run([docker,'ps','-a','--filter','label=lanes.ner-preview.owner','--format','{{.Names}}'],capture_output=True,timeout=10,check=True)
    assert not stopped.stdout.strip()
    assert (ROOT/'backend/runtime_data/ner_preview/owner.lock').read_bytes()==b'\0'
    result={'status':'saved_receipts_verified_with_declared_config_change',
        'freeze_sha256':digest(attempt/'freeze.json'),'api_cases':9,'training_neural_parity_cases':6,
        'cached_context_view_parity_checks':120,'v41_frozen_files_unchanged':len(old_freeze['implementation']),
        'protected_evidence_hashes_unchanged':len(old['hash_bound']),
        'historical_metadata_entries_unchanged':len(old['historical_metadata_only'])-1,
        'declared_application_source_changes':changed,'excluded_metadata_entries_unchanged':len(old['validation_holdout_metadata_only']),
        'live_container_isolation_verified':True,'owned_containers_remaining':0,
        'maximum_cold_seconds':max(m['cold_seconds']for m in measures),
        'maximum_extraction_seconds':max(m['extraction_seconds']for m in measures),
        'maximum_worker_rss_bytes':max(m['peak_worker_rss_bytes']for m in measures),
        'initial_audit_failure_preserved':(attempt/'failure.json').exists(),'inference_rerun_for_reconciliation':False,
        'validation_holdout_contents_opened':False,'new_accuracy_measurement':False,'database_writes':False}
    output.mkdir(parents=True,exist_ok=False)
    with (output/'verification.json').open('x',encoding='utf-8')as stream:json.dump(result,stream,indent=2)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('attempt','bundle','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--docker',required=True)
    a=p.parse_args();print(json.dumps(verify(a.attempt.resolve(),a.bundle.resolve(),a.docker,a.output.resolve())))
