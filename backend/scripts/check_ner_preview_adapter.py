"""Freeze and verify the local adapter using existing development evidence only.

Creates a new private output directory. Never opens validation/holdout contents,
connects to a database, changes references or enables the running application's flag.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.news_ner.bundle import digest, verify_bundle
from app.services.news_ner.contract import IMAGE

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'backend/training/flood_ner/artifacts'


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, value: object) -> None:
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write('\n')


def verify(bundle: Path, bundle_sha: str, docker: str, output: Path) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api import deps
    from app.api.v1.endpoints import admin_news_ner as endpoint
    from app.core.database import get_db
    from app.core.limiter import limiter
    from app.schemas.news_ner_preview import ContextGraph
    from app.services.news_ner.context_association_v41 import extract
    from app.services.news_ner.projection import project

    if output.exists() or not output.resolve().is_relative_to(ART.resolve()):
        raise ValueError('new private artifact destination required')
    verify_bundle(bundle, bundle_sha)
    output.mkdir(parents=True, exist_ok=False)
    sources = {
        'articles': ART/'shadow-execution-20261019-v31/input/workload.json',
        'predictions': ART/'shadow-execution-20261019-v31/worker-output/comparisons.jsonl',
        'context_request': ART/'context-repair-prepared-20261019-v41/request.json',
        'context_outputs': ART/'context-repair-execution-20261019-v41/worker-output/context_rows.jsonl',
        'preservation': ART/'extraction-gap-assessment-20261019-v39/preservation-before.json',
        'v41_freeze': ART/'context-repair-prepared-20261019-v41/freeze.json',
    }
    rows = [r for r in read(sources['articles'])['rows'] if r['kind']=='training_article']
    assert len(rows)==6
    saved = {r['article_id']:r for r in map(json.loads,sources['predictions'].read_text(encoding='utf-8').splitlines())}
    workload=[]
    for row in rows:
        assert hashlib.sha256(row['text'].encode()).hexdigest()==row['text_sha256']==saved[row['article_id']]['text_sha256']
        workload.append({'id':row['article_id'],'text':row['text'],'text_sha256':row['text_sha256'],
                         'expected':saved[row['article_id']]['neural']['mentions']})
    for number,text in enumerate([
        'At 6 PM, Daan Piña had knee-deep flooding.',
        'Nang 6:31 PM, nagsimula ang baha sa Daan Piña.',
        'Iniulat ang flood sa Daan Piña nang 8 PM. Humupa ang baha nang 9 PM.',
    ]):
        workload.append({'id':'fictional-'+str(number),'text':text,
            'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'expected':None})
    write(output/'workload.json',workload)
    code = list((ROOT/'backend/app/services/news_ner').glob('*.py')) + [
        ROOT/'backend/app/services/news_ner/promotion.json', ROOT/'backend/app/services/news_ner_preview_service.py',
        ROOT/'backend/app/schemas/news_ner_preview.py', ROOT/'backend/app/api/v1/endpoints/admin_news_ner.py',
        ROOT/'backend/app/api/v1/api.py', ROOT/'backend/app/core/config.py',Path(__file__),
        *list((ROOT/'backend/tests').glob('test_news_ner_preview*.py'))]
    freeze={'schema':'lanes-ner-preview-adapter-check-v1','implementation':{p.relative_to(ROOT).as_posix():digest(p) for p in code},
        'source_bindings':{k:{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)} for k,p in sources.items()},
        'workload_sha256':digest(output/'workload.json'),'bundle_sha256':bundle_sha,'image':IMAGE,
        'counts':{'training_articles':6,'fictional_articles':3,'context_rows':24,'context_views':5},
        'acceptance':'all_api_responses_200_exact_original_neural_spans_context_output_parity_preservation_cleanup',
        'retries':0}
    write(output/'freeze.json',freeze)
    try:
        context_rows=read(sources['context_request'])['context_rows']
        context_saved={r['record_id']:r['views'] for r in map(json.loads,sources['context_outputs'].read_text(encoding='utf-8').splitlines())}
        assert len(context_rows)==24
        context_checks=0
        for row in context_rows:
            assert len(row['views'])==5
            for name,raw in row['views'].items():
                graph=extract(raw)
                assert graph==context_saved[row['record_id']][name]
                ContextGraph.model_validate(graph)
                groups=project(raw,graph)
                assert sorted(i for g in groups for i in g['relation_ids'])==sorted(r['id']for r in graph['relations'])
                context_checks+=1

        cfg=endpoint.settings
        cfg.ENVIRONMENT='test';cfg.NEWS_NER_PREVIEW_ENABLED=True
        cfg.NEWS_NER_PREVIEW_BUNDLE=str(bundle);cfg.NEWS_NER_PREVIEW_BUNDLE_SHA256=bundle_sha;cfg.NEWS_NER_PREVIEW_DOCKER=docker
        app=FastAPI();app.state.limiter=limiter;limiter.enabled=False
        app.include_router(endpoint.router,prefix='/api/v1/admin/news')
        row=SimpleNamespace(id=7,canonical_url='https://example.invalid/adapter-check',publisher_source_id='adapter-check',
            article_text='',article_error=None,published_at=None)
        class ReadOnlyDB:
            def get(self,model: object,identity: int) -> object:
                assert identity==7
                return row
            def __getattr__(self,name: str) -> None:
                raise AssertionError('unexpected storage operation')
        app.dependency_overrides[get_db]=lambda:ReadOnlyDB()
        app.dependency_overrides[deps.get_current_active_admin]=lambda:object()
        measurements=[]
        with TestClient(app) as client:
            for index,case in enumerate(workload):
                row.article_text=case['text']
                started=time.monotonic()
                response=client.post('/api/v1/admin/news/articles/7/ner-preview')
                value=response.json()
                write(output/f'response-{index:02}.json',{'id':case['id'],'status':response.status_code,'response':value})
                assert response.status_code==200,(index,response.status_code)
                assert response.headers['cache-control']=='no-store'
                assert value['source']['text_sha256']==case['text_sha256']
                spans=[{k:m[k]for k in ('start','end','text','label')}for m in value['neural_mentions']]
                if case['expected'] is not None:assert spans==case['expected'],index
                measurements.append({'kind':'training_article'if case['expected']is not None else'fictional',
                    'wall_seconds':time.monotonic()-started,**value['measurements']})
                write(output/f'heartbeat-{index:02}.json',{'completed':index+1})
        old_freeze=read(sources['v41_freeze'])
        for name,sha in old_freeze['implementation'].items():assert digest(ROOT/name)==sha
        preservation=read(sources['preservation'])
        for name,entry in preservation['hash_bound'].items():assert digest(ROOT/name)==entry['sha256'],name
        for key in ('historical_metadata_only','validation_holdout_metadata_only'):
            for name,entry in preservation[key].items():
                state=(ROOT/name).stat()
                assert (state.st_size,state.st_mtime_ns)==(entry['bytes'],entry['mtime_ns']),name
        for name,sha in freeze['implementation'].items():assert digest(ROOT/name)==sha,name
        for entry in freeze['source_bindings'].values():assert digest(ROOT/entry['path'])==entry['sha256']
        verify_bundle(bundle,bundle_sha)
        import subprocess
        state=subprocess.run([docker,'ps','-a','--filter','label=lanes.ner-preview.owner','--format','{{.Names}}'],capture_output=True,timeout=10,check=True)
        assert not state.stdout.strip()
        lock=ROOT/'backend/runtime_data/ner_preview/owner.lock'
        assert lock.read_bytes()==b'\0'
        write(output/'verification.json',{'status':'passed','freeze_sha256':digest(output/'freeze.json'),
            'api_cases':len(workload),'training_neural_parity_cases':6,'cached_context_view_parity_checks':context_checks,
            'measurements':measurements,'frozen_v41_files_unchanged':len(old_freeze['implementation']),
            'protected_hashes_unchanged':len(preservation['hash_bound']),
            'historical_metadata_unchanged':len(preservation['historical_metadata_only']),
            'excluded_metadata_unchanged':len(preservation['validation_holdout_metadata_only']),
            'validation_holdout_contents_opened':False,'database_writes':False,'owned_containers_remaining':0,
            'new_accuracy_measurement':False})
        print(json.dumps({'status':'passed','api_cases':len(workload),'cached_context_view_parity_checks':context_checks}))
    except BaseException as exc:
        write(output/'failure.json',{'status':'failed','error_type':type(exc).__name__})
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',type=Path,required=True);p.add_argument('--bundle-sha',required=True)
    p.add_argument('--docker',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();verify(a.bundle.resolve(),a.bundle_sha,a.docker,a.output.resolve())
