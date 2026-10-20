"""Private container acceptance; saved predictions/oracles are never mounted here."""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
from datetime import datetime,timezone
from email.utils import format_datetime
from html import escape
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0,'/app')


def write(name: str,value: object) -> None:
    with (Path('/output')/name).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,allow_nan=False,indent=2)


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['preflight','execute']);args=parser.parse_args()
    from sqlalchemy import create_engine,select,func,text
    from sqlalchemy.orm import sessionmaker
    import httpx
    from app.models.news import NewsArticle,NewsArticleVersion,NewsExtractionRun
    from app.models.setting import SystemSetting
    from app.services.news_sources import NewsSource
    from app.services.news_ner_durable.assets import load_trusted_assets,with_placement_assets,normalizer_bindings
    from app.services.news_ner_durable.collection import NativeCollectionContext
    from app.services.news_ner_durable.pipeline import run_native_news_pipeline
    from app.services.news_ner_durable.processing import require_local_target,deadline,OperationDeadline
    from app.services.news_ner_durable.contracts import sha
    from app.services.news_ner_runtime.supervisor import Session
    from app.services.news_results_service import browse_news_results
    from app.services.news_saved_run_service import saved_run_summary
    from app.services.configuration_service import read_configuration,CONFIG_KEY
    request=json.loads(Path('/input/request.json').read_text(encoding='utf-8'))
    url=os.environ['DATABASE_URL'];require_local_target(os.environ['ENVIRONMENT'],url)
    engine=create_engine(url,connect_args={'connect_timeout':5},pool_timeout=5,pool_pre_ping=False)
    factory=sessionmaker(bind=engine)
    def assets():
        value=with_placement_assets(load_trusted_assets(Path('/assets'),request['bundle_sha256'],expected_worker_code_sha256=request['worker_code_sha256']))
        assert value.manifest==request['manifest'] and normalizer_bindings()==request['normalizer_bindings']
        return value
    try:
        trusted=assets();source=NewsSource('c3b-fixture','Fictional retained development source',('example.org',),
            ('https://example.org/feed',),datetime.now(timezone.utc).date(),True)
        with factory() as db:
            assert db.scalar(text('SELECT version_num FROM alembic_version'))=='e8a6f1c2d903'
            assert db.scalar(select(func.count()).select_from(NewsArticle))==0
        metrics={'model_starts':0,'neural_requests':0,'model_reaps':0,'requests':[]}
        if args.operation=='preflight':
            import signal
            previous=signal.getsignal(signal.SIGALRM)
            try:
                with deadline(.01):time.sleep(.1)
            except OperationDeadline:pass
            else:raise AssertionError('linux_deadline_not_enforced')
            assert signal.getsignal(signal.SIGALRM)==previous and signal.getitimer(signal.ITIMER_REAL)[0]==0
            now=datetime(2026,10,20,3,tzinfo=timezone.utc)
            body=('On October 20, 2026 at 10 AM PHT, Fictional Crescent in Pasig City was flooded knee-deep. '
                  'This is a fictional software plumbing fixture with no real flood assertion.')
            def handler(http_request):
                if str(http_request.url)==source.feed_urls[0]:
                    return httpx.Response(200,text='<rss><channel><item><guid>software</guid><title>Flood in Pasig</title>'
                        '<link>https://example.org/preflight</link><pubDate>'+format_datetime(now)+'</pubDate></item></channel></rss>')
                return httpx.Response(200,text='<article>'+escape(body)+'</article>',headers={'content-type':'text/html'})
            class FictionalSession:
                async def start(self):metrics['model_starts']+=1
                async def request(self,raw,*,timeout):
                    from app.services.news_ner.location_pipeline import from_neural_mentions
                    from app.services.news_ner.contract import object_sha
                    metrics['neural_requests']+=1
                    mentions=[]
                    for label,name in [('ROAD','Fictional Crescent'),('CITY','Pasig City')]:
                        start=raw['text'].index(name)
                        mentions.append({'id':'m'+str(len(mentions)),'start':start,'end':start+len(name),'text':name,'label':label,
                            'provenance_sha256':object_sha({'bundle':trusted.provenance['bundle_sha256'],
                                'tokenizer':trusted.provenance['tokenizer_sha256'],'text':raw['text_sha256']})})
                    value=from_neural_mentions({**raw,'mentions':mentions})
                    return {**value,'provenance':trusted.provenance,'measurements':{'extraction_seconds':0,'peak_worker_rss_bytes':0}}
                async def close(self):metrics['model_reaps']+=1
            runtime=FictionalSession()
            async def software():
                with httpx.Client(transport=httpx.MockTransport(handler)) as client:
                    return await run_native_news_pipeline(factory,load_assets=assets,environment='test',database_url=url,
                        sources=(source,),client=client,limit=10,clock=lambda:now,runtime_factory=lambda _:runtime)
            result=asyncio.run(software());write('pipeline.json',result)
            assert result['error_code'] is None and result['extraction']['completed']==1 and result['publication']['published']==1
            with factory() as db:
                context=NativeCollectionContext(trusted,'test',url)
                page=browse_news_results(db,page=1,page_size=12,search='',publisher=None,condition=None,placement=None,
                    order='extraction_newest',processing_context=context)
                assert page.total==1 and page.items[0].result_kind=='ner_group'
                assert db.scalar(text('SELECT count(*) FROM flood_avoidance_zones'))==0
            assert metrics['model_starts']==metrics['neural_requests']==metrics['model_reaps']==1
            write('preflight.json',{'status':'passed','assets_authenticated':True,'linux_timer_and_restore':True,
                'fictional_rss_to_native_reader_and_text_publication':True,'neural_requests':0})
            return 0
        rows=json.loads(Path('/input/workload.json').read_text(encoding='utf-8'))['rows']
        assert len(rows)==10
        # Historical retained reports never become public observations during
        # qualification. Positive publication is exercised by fictional tests.
        with factory() as db,db.begin():
            settings=read_configuration(db).model_copy(update={'news_publication_enabled':False,'news_source_ids':[source.id]})
            db.add(SystemSetting(key=CONFIG_KEY,value={'revision':1,'settings':settings.model_dump(mode='json')}))
            for index,row in enumerate(rows):
                if len(row['text'])>=120:continue
                db.add(NewsArticle(canonical_url=f'https://example.org/runtime-control/{index}',publisher_source_id=source.id,
                    title=f'Preexisting retained runtime control {index}',excerpt='',published_at=None,article_text=row['text'],
                    content_fingerprint=sha({'fixture':index}),review_state='pending'))
        def handler(http_request):
            if str(http_request.url)==source.feed_urls[0]:
                items=''.join(f'<item><guid>retained-{i}</guid><title>Fictional flood in Pasig {i}</title>'
                    f'<link>https://example.org/rss/{i}</link><pubDate>{request["publication_raw"]}</pubDate></item>' for i in range(len(rows)))
                return httpx.Response(200,text='<rss><channel>'+items+'</channel></rss>')
            index=int(http_request.url.path.rsplit('/',1)[1])
            return httpx.Response(200,text='<article>'+escape(rows[index]['text'])+'</article>',headers={'content-type':'text/html'})
        class TrackedSession(Session):
            async def start(self):
                metrics['model_starts']+=1;began=time.monotonic();value=await super().start()
                metrics['cold_seconds']=time.monotonic()-began;metrics['isolation']=value['isolation']
                names={v.split(b'=',1)[0] for v in Path(f'/proc/{self.proc.pid}/environ').read_bytes().split(b'\0') if v}
                assert not names & {b'DATABASE_URL',b'GOOGLE_APPLICATION_CREDENTIALS',b'GOOGLE_CLOUD_PROJECT'}
                metrics['child_credentials_absent']=True
                return value
            async def request(self,raw,*,timeout):
                metrics['neural_requests']+=1;began=time.monotonic();value=await super().request(raw,timeout=timeout)
                metrics['requests'].append({'seconds':time.monotonic()-began,'input_characters':len(raw['text'])})
                return value
            async def close(self):
                live=self.state!='closed';await super().close()
                if live:metrics['model_reaps']+=1
                metrics['cleanup_seconds']=self.cleanup_seconds
        def tracked(_):return TrackedSession(trusted.manifest['model']['bundle_sha256'],trusted._code)
        def stage(name,summary):
            with Path('/output/stages.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(json.dumps({'stage':name,'summary':summary})+'\n')
        async def execute():
            with httpx.Client(transport=httpx.MockTransport(handler)) as client:
                first=await run_native_news_pipeline(factory,load_assets=assets,environment='test',database_url=url,
                    sources=(source,),client=client,limit=50,runtime_factory=tracked,on_stage=stage)
                write('pipeline.json',first)
                assert first['error_code'] is None and first['extraction']['completed']==10
                assert first['collection']['captured_candidates']==8
                write('metrics.json',metrics)
                before=metrics['neural_requests']
                duplicate=await run_native_news_pipeline(factory,load_assets=assets,environment='test',database_url=url,
                    sources=(source,),client=client,limit=50,runtime_factory=tracked)
                write('duplicate.json',duplicate)
                assert duplicate['extraction']['completed']==0 and metrics['neural_requests']==before
                return first
        began=time.monotonic();result=asyncio.run(execute());metrics['worker_seconds']=time.monotonic()-began
        saved=[]
        with factory() as db:
            for run in db.scalars(select(NewsExtractionRun).where(NewsExtractionRun.mode=='ner_rules_v1').order_by(NewsExtractionRun.id)):
                version=db.get(NewsArticleVersion,run.article_version_id)
                index=int(version.input_snapshot['canonical_url'].rsplit('/',1)[1])
                assert version.input_snapshot['article_text']==rows[index]['text']
                saved.append({'workload_index':index,'run':saved_run_summary(run).model_dump(mode='json',by_alias=True),
                    'version':{'id':version.id,'article_id':version.article_id,'input_snapshot':version.input_snapshot,'input_fingerprint':version.input_fingerprint}})
            context=NativeCollectionContext(trusted,'test',url)
            page=browse_news_results(db,page=1,page_size=50,search='',publisher=None,condition=None,placement=None,
                order='extraction_newest',processing_context=context)
            for table in ('flood_avoidance_zones','flood_reports'):
                assert db.scalar(text('SELECT count(*) FROM '+table))==0
            assert db.scalar(text("SELECT count(*) FROM news_claim_decisions WHERE public_state IN ('active_alert','active_zone')"))==0
            assert len(saved)==10 and db.scalar(select(func.count()).select_from(NewsArticleVersion))==10
            counts={name:db.scalar(text('SELECT count(*) FROM '+name)) for name in ('news_claim_sources','news_claim_evaluations','news_claim_decisions')}
        write('saved-history.json',saved)
        peak=int(Path('/sys/fs/cgroup/memory.peak').read_text());assert peak<2688*1024**2
        assert metrics['model_starts']==metrics['model_reaps']==1 and metrics['neural_requests']==10
        write('metrics-complete.json',{**metrics,'cgroup_memory_peak_bytes':peak})
        write('summary.json',{'status':'passed_local_c3b_integration','rss_admitted':8,'short_rss_rejections':2,
            'preexisting_short_runtime_controls':2,'completed':len(saved),'neural_requests':metrics['neural_requests'],
            'duplicate_neural_requests':0,'native_card_count':page.total,'downstream_rows':counts,
            'retained_publication_disabled':True,'public_alerts_or_zones_created':False,'automatic_processing_enabled':False,'cloud_changes':False})
        return 0
    finally:engine.dispose()


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        import traceback
        frames=[{'file':Path(frame.filename).name,'function':frame.name,'line':frame.lineno}
                for frame in traceback.extract_tb(exc.__traceback__)]
        write('private-failure.json',{'code':'c3b_probe_failed','exception_type':type(exc).__name__,'frames':frames})
        print(json.dumps({'code':'c3b_probe_failed'}));raise SystemExit(2)
