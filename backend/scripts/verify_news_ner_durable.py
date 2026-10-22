"""C2 retained-evidence replay. Never starts a worker, connects SQL or fetches news."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
BACKEND=ROOT/'backend'
sys.path.insert(0,str(BACKEND))

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_ner.bundle import digest
from app.services.news_ner.contract import object_sha
from app.services.news_ner.location_pipeline import from_neural_mentions
from app.services.news_ner.projection import project
from app.services.news_ner_runtime.protocol import verify_result
from app.services.news_ner_durable.adapter import build_native_result
from app.services.news_ner_durable.assets import load_trusted_assets, normalizer_bindings
from app.services.news_ner_durable.contracts import NerEvidenceError, RunEvidence, capture_native_input
from app.services.news_ner_durable.source_check import check_native_sources, source_policy_fingerprint

ART=BACKEND/'training/flood_ner/artifacts'
QUALIFIED=ART/'rss-ner-runtime-phase-b-3g-20261020-v1'
QUALIFIED_MANIFEST='8b079765472409592b99e4d2f380c95b3846ad799aa5ef437b6db46857c7d488'


def read(path: Path) -> object:
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, value: object) -> None:
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)


def verify_cached(qualified: dict, output: Path) -> dict:
    """Use the authenticated cache chain, not an old application-state controller."""
    relative='backend/training/flood_ner/artifacts/backend-location-cached-20261020-v46/freeze.json'
    assert digest(ROOT/relative)==qualified['bindings'][relative]
    frozen=read(ROOT/relative)
    for name,expected in frozen['pipeline_hashes'].items():assert digest(ROOT/name)==expected
    request_path=ART/'location-repair-prepared-20261020-v44/request.json'
    manifest_path=ART/'location-repair-execution-20261020-v44/output-manifest.json'
    assert digest(request_path)==frozen['request_sha256'] and digest(manifest_path)==frozen['v44_output_manifest_sha256']
    bindings={r['path']:r['sha256'] for r in read(manifest_path)['files']}
    count=graphs=0
    for group,rows in read(request_path)['groups'].items():
        path=ART/'location-repair-execution-20261020-v44/worker-output'/(group+'.jsonl')
        assert digest(path)==bindings[path.relative_to(ROOT).as_posix()]
        saved={r['record_id']:r for r in (json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line)}
        assert len(saved)==len(rows)
        for row in rows:
            pure=from_neural_mentions(row['raw']);proposal=pure['proposal'];expected=saved[row['record_id']]['methods']['combined']
            for key in ('record_id','text_sha256','method','neural_mentions','control_mentions','effective_mentions'):
                assert proposal[key]==expected['repair'][key]
            assert [p for p in proposal['proposals'] if p['implementation']=='lanes-location-repair-v44']==expected['repair']['proposals']
            assert [a for a in proposal['abstentions'] if a['implementation']=='lanes-location-repair-v44']==[
                dict(a,implementation='lanes-location-repair-v44') for a in expected['repair']['abstentions']]
            if 'context' in expected:
                assert pure['graph']==expected['context'];graphs+=1
            groups=project({**row['raw'],'mentions':proposal['effective_mentions']},pure['graph'])
            assigned={f['id'] for g in groups for kind in ('depth','time','status','access') for f in g[kind]}
            assert assigned|{u['fact_id'] for u in pure['graph']['unassigned']}=={f['id'] for f in pure['graph']['facts']}
            count+=1
    assert count==788 and graphs==407
    result={'cached_records':count,'saved_context_graphs_matched':graphs,'neural_inference':False}
    write(output/'cached-summary.json',result)
    return result


def main(output: Path) -> dict:
    assert output.resolve().is_relative_to(ART.resolve()) and not output.exists()
    output.mkdir(parents=False)
    completed=0
    try:
        assert digest(QUALIFIED/'final-package-manifest.json')==QUALIFIED_MANIFEST
        package=read(QUALIFIED/'final-package-manifest.json')['files']
        for name in ('freeze.json','input/request.json','input/workload.json','output/responses.jsonl','expected-predictions.json'):
            assert digest(QUALIFIED/name)==package[name]
        request=read(QUALIFIED/'input/request.json')
        trusted=load_trusted_assets(ART/'ner-preview-bundle-20261019-v1',request['bundle_sha256'],
                                    expected_worker_code_sha256=object_sha(request['code']))
        write(output/'trusted-manifest.json',trusted.manifest)
        write(output/'source-bindings.json',normalizer_bindings())
        cache=verify_cached(read(QUALIFIED/'freeze.json'),output)
        assert cache['cached_records']==788 and cache['saved_context_graphs_matched']==407
        rows=read(QUALIFIED/'input/workload.json')['rows'];expected=read(QUALIFIED/'expected-predictions.json')
        counts=Counter();omissions=Counter();audits=Counter();kinds=Counter();compared=0;reviewed_predictions=0;maximum_result_bytes=0
        with (QUALIFIED/'output/responses.jsonl').open(encoding='utf-8') as responses,(output/'native-envelopes.jsonl').open('x',encoding='utf-8') as envelopes:
            for index,row in enumerate(rows):
                line=next(responses);response=json.loads(line);original=response['result']
                raw={k:row[k] for k in ('record_id','text','text_sha256','publication')}
                assert response['record_id']==row['record_id']
                verify_result(raw,original,request['bundle_sha256'],request['code'])
                if row['record_id'] in expected:
                    assert [[m['start'],m['end'],m['label']] for m in original['proposal']['neural_mentions']]==expected[row['record_id']]
                    compared+=1
                if row['kind']=='reviewed':reviewed_predictions=len(original['proposal']['neural_mentions'])
                # Synthetic development identities, not new actual article captures.
                # Old publication metadata has no original-feed timezone proof.
                published=datetime.fromisoformat(row['publication']['value']) if row['publication'] else None
                source=NewsArticleExtractorInput(article_id=index+1,canonical_url=f'https://example.org/development-fixture/{index}',
                    publisher='retained-development-fixture',title='Retained development fixture',article_text=row['text'],published_at=published)
                snapshot,fingerprint=capture_native_input(source)
                version=SimpleNamespace(id=index+1,article_id=index+1,input_snapshot=snapshot,input_fingerprint=fingerprint)
                run=SimpleNamespace(id=index+1,article_version_id=index+1,mode='ner_rules_v1',pipeline_version=trusted.pipeline_version,
                                    status='completed',completed_at=datetime(2026,10,20,3,tzinfo=timezone.utc))
                context=RunEvidence.from_records(run,version);native_request=context.source().runtime_request(fingerprint)
                pure=from_neural_mentions({**native_request,'mentions':deepcopy(original['proposal']['neural_mentions'])})
                for key in ('proposal','graph'):
                    rebased=deepcopy(original[key]);rebased['record_id']=native_request['record_id']
                    assert rebased==pure[key]
                result=build_native_result(context,{**pure,'provenance':original['provenance'],'measurements':original['measurements']},
                    trusted,extracted_at=run.completed_at)
                saved=result.model_dump(mode='json',by_alias=True);run.result=saved
                maximum_result_bytes=max(maximum_result_bytes,len(json.dumps(saved,ensure_ascii=False).encode('utf-8')))
                checked=check_native_sources(run,version,saved,tuple(range(len(result.claims))),trusted,now=run.completed_at)
                assert len(result.projection['fact_accounting'])==len(result.native.graph.facts)
                assert result.native.graph.model_dump(mode='json',by_alias=True)==pure['graph']
                counts['claims']+=len(result.claims);counts['groups']+=len(result.projection['groups'])
                counts['facts']+=len(result.native.graph.facts);counts[result.projection['disposition']]+=1
                kinds[row['kind']]+=1
                for group in result.projection['groups']:
                    omissions.update(group['reasons']);omissions.update(group['normalizations'].get('omitted_field_reasons',[]))
                audits.update(a.outcome for a in checked.values())
                envelopes.write(json.dumps(saved,ensure_ascii=False,allow_nan=False)+'\n');envelopes.flush()
                completed+=1
                if completed%50==0:print(json.dumps({'retained_rows_checked':completed}),flush=True)
            assert not responses.read().strip()
        assert completed==355 and compared==352 and reviewed_predictions==53
        summary={'status':'passed_retained_c2_replay','retained_rows':completed,'saved_prediction_records_compared':compared,
                 'reviewed_predictions_preserved':reviewed_predictions,'cached_inputs':788,'saved_graphs':407,
                 'maximum_saved_result_bytes':maximum_result_bytes,'saved_result_limit_bytes':8*1024*1024,
                 'kinds':dict(kinds),'counts':dict(counts),'omission_reasons':dict(omissions),'source_check_outcomes':dict(audits),
                 'source_policy_fingerprint':source_policy_fingerprint(trusted),'neural_inference_runs':0,
                 'synthetic_native_envelopes_only':True,'automatic_processing_enabled':False,
                 'shared_or_cloud_changes':False,'qualified_runtime_manifest_sha256':QUALIFIED_MANIFEST}
        write(output/'summary.json',summary)
        write(output/'manifest.json',{'files':{p.relative_to(output).as_posix():digest(p) for p in output.rglob('*') if p.is_file()}})
        return summary
    except BaseException as exc:
        write(output/'failure.json',{'completed_rows':completed,'code':exc.code if isinstance(exc,NerEvidenceError) else 'retained_verification_failed',
                                    'exception_type':type(exc).__name__})
        # Private diagnostic only; the console remains bounded and text-free.
        import traceback
        (output/'private-failure-trace.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:print(json.dumps(main(args.output.resolve())))
    except BaseException:
        print(json.dumps({'status':'failed_retained_c2_replay','neural_inference_runs':0}));sys.exit(1)
