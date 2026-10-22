"""C3a container probe. Expectations/oracles never enter this container."""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time
from types import SimpleNamespace

sys.path.insert(0,'/app')


def write(name: str, value: object) -> None:
    path=Path('/output')/name
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,allow_nan=False,indent=2)


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=['preflight','execute'])
    args=parser.parse_args()
    from sqlalchemy import create_engine,text,select,func
    from sqlalchemy.orm import sessionmaker
    from app.services.news_ner_durable.processing import deadline,OperationDeadline,require_local_target,process_native_saved_news
    from app.services.news_ner_durable.assets import load_trusted_assets,normalizer_bindings
    from app.services.news_ner_durable.contracts import sha,NerEvidenceError
    from app.services.news_ner_runtime.supervisor import Session
    request=json.loads(Path('/input/request.json').read_text(encoding='utf-8'))
    url=os.environ['DATABASE_URL'];require_local_target(os.environ['ENVIRONMENT'],url)
    engine=create_engine(url,connect_args={'connect_timeout':5},pool_pre_ping=False);factory=sessionmaker(bind=engine)
    def assets():
        value=load_trusted_assets(Path('/assets'),request['bundle_sha256'],expected_worker_code_sha256=request['worker_code_sha256'])
        assert normalizer_bindings()==request['normalizer_bindings']
        return value
    try:
        if args.operation=='preflight':
            trusted=assets();original=signal.getsignal(signal.SIGALRM)
            try:
                with deadline(.01):time.sleep(.1)
            except OperationDeadline:pass
            else:raise AssertionError('cpu_deadline_not_enforced')
            assert signal.getsignal(signal.SIGALRM)==original and signal.getitimer(signal.ITIMER_REAL)[0]==0
            try:
                with deadline(1):
                    with deadline(1):pass
            except NerEvidenceError:pass
            else:raise AssertionError('nested_deadline_not_refused')
            with engine.connect() as db:
                assert db.scalar(text('SELECT version_num FROM alembic_version'))=='e8a6f1c2d903'
                assert db.scalar(text('SELECT postgis_version()'))
            # Exercise the Linux queue/timer/storage path with an explicit
            # fictional software stub before spending the one neural attempt.
            from app.models.news import NewsArticle,NewsArticleVersion,NewsExtractionRun
            from app.services.news_ner.location_pipeline import from_neural_mentions
            with factory() as db,db.begin():
                assert db.scalar(select(func.count()).select_from(NewsArticle))==0
                db.add(NewsArticle(canonical_url='https://example.org/c3a/software-only',publisher_source_id='c3a-fixture',
                    title='Fictional software plumbing case',article_text='A fictional drainage prevention bulletin was announced.',
                    content_fingerprint='0'*64,review_state='pending'))
            class FictionalSession:
                async def start(self):pass
                async def request(self,request,*,timeout):
                    pure=from_neural_mentions({**request,'mentions':[]})
                    return {**pure,'provenance':trusted.provenance,'measurements':{'extraction_seconds':0,'peak_worker_rss_bytes':0}}
                async def close(self):pass
            fixtures=(SimpleNamespace(id='c3a-fixture',enabled=True,verified_at=datetime.now(timezone.utc)),)
            async def software():
                return await process_native_saved_news(factory,load_assets=assets,environment='test',database_url=url,
                    limit=1,sources=fixtures,runtime_factory=lambda _:FictionalSession())
            software_summary=asyncio.run(software());write('software-plumbing.json',asdict(software_summary))
            assert software_summary.completed==1 and software_summary.error_code is None
            with factory() as db,db.begin():
                native=db.scalar(select(NewsExtractionRun));assert native.result['claims']==[]
                assert native.result['projection']['disposition']=='no_eligible_observations'
                for table in ('news_claim_sources','news_claim_decisions','flood_avoidance_zones'):
                    assert db.scalar(text('SELECT count(*) FROM '+table))==0
                db.execute(text('DELETE FROM news_extraction_runs'));db.execute(text('DELETE FROM news_article_versions'));db.execute(text('DELETE FROM news_articles'))
            write('preflight.json',{'status':'passed','native_pipeline':trusted.pipeline_version,
                'linux_timer_and_restore':True,'nested_timer_refused':True,'assets_authenticated':True,
                'fictional_native_queue_roundtrip':True,'neural_requests':0})
            return 0
        from app.models.news import NewsArticle,NewsArticleVersion,NewsExtractionRun
        from app.schemas.news_extraction import NewsArticleExtractorInput
        from app.services.news_discovery_service import extraction_input_snapshot
        from app.services.news_saved_run_service import saved_run_summary
        rows=json.loads(Path('/input/workload.json').read_text(encoding='utf-8'))['rows']
        # Synthetic development identities; no publisher fetch or live admission.
        with factory() as db,db.begin():
            assert db.scalar(select(func.count()).select_from(NewsArticle))==0
            for index,row in enumerate(rows):
                article=NewsArticle(canonical_url=f'https://example.org/c3a/{index}',publisher_source_id='c3a-fixture',
                    title='Retained C3a development fixture',excerpt='',published_at=None,article_text=row['text'],
                    content_fingerprint=sha({'fixture':index}),review_state='pending')
                db.add(article);db.flush()
                old,fingerprint=extraction_input_snapshot(NewsArticleExtractorInput(article_id=article.id,
                    canonical_url=article.canonical_url,publisher=article.publisher_source_id,title=article.title,
                    article_text=article.article_text))
                version=NewsArticleVersion(article_id=article.id,input_fingerprint=fingerprint,input_snapshot=old)
                db.add(version);db.flush()
                db.add(NewsExtractionRun(article_version_id=version.id,pipeline_version='c3a-fictional-legacy-history',mode='rules_only',status='pending',attempt_count=0))
        metrics={'model_starts':0,'neural_requests':0,'model_reaps':0,'requests':[]}
        class TrackedSession(Session):
            async def start(self):
                metrics['model_starts']+=1;started=time.monotonic();value=await super().start()
                metrics['cold_seconds']=time.monotonic()-started;metrics['isolation']=value['isolation']
                names={v.split(b'=',1)[0] for v in Path(f'/proc/{self.proc.pid}/environ').read_bytes().split(b'\0') if v}
                assert not names & {b'DATABASE_URL',b'GOOGLE_APPLICATION_CREDENTIALS',b'PYTHONPATH',b'HTTP_PROXY',b'HTTPS_PROXY'}
                return value
            async def request(self,request,*,timeout=60):
                metrics['neural_requests']+=1;started=time.monotonic();value=await super().request(request,timeout=timeout)
                metrics['requests'].append({'record_id':request['record_id'],'seconds':time.monotonic()-started});return value
            async def close(self):
                first=self.cleanup_seconds is None;await super().close()
                if first:
                    metrics['model_reaps']+=1;metrics['cleanup_seconds']=self.cleanup_seconds
                    assert self.proc is None or self.proc.returncode is not None
        sources=(SimpleNamespace(id='c3a-fixture',enabled=True,verified_at=datetime.now(timezone.utc)),)
        async def execute():
            return await process_native_saved_news(factory,load_assets=assets,environment='test',database_url=url,limit=len(rows),
                sources=sources,runtime_factory=lambda trusted:TrackedSession(trusted.manifest['model']['bundle_sha256'],trusted._code))
        started=time.monotonic()
        try:summary=asyncio.run(execute())
        finally:write('metrics.json',{**metrics,'worker_seconds':time.monotonic()-started,
            'cgroup_memory_peak_bytes':int(Path('/sys/fs/cgroup/memory.peak').read_text()),
            'parent_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024})
        write('processing.json',asdict(summary))
        if summary.completed!=len(rows) or summary.error_code or summary.failed or summary.retry_wait or summary.lease_lost:
            return 2
        # A duplicate invocation must never construct/start a model.
        async def duplicate():
            def forbidden(_):raise AssertionError('duplicate_model_start')
            return await process_native_saved_news(factory,load_assets=assets,environment='test',database_url=url,
                limit=len(rows),sources=sources,runtime_factory=forbidden)
        duplicate_summary=asyncio.run(duplicate());write('duplicate.json',asdict(duplicate_summary))
        assert duplicate_summary.captured==duplicate_summary.completed==0 and duplicate_summary.error_code is None
        # A fresh session round-trips the actual database JSONB through C1 readers.
        saved=[]
        with factory() as db:
            for run in db.scalars(select(NewsExtractionRun).where(NewsExtractionRun.mode=='ner_rules_v1').order_by(NewsExtractionRun.id)):
                version=db.get(NewsArticleVersion,run.article_version_id)
                saved.append({'run':saved_run_summary(run).model_dump(mode='json',by_alias=True),
                    'version':{'id':version.id,'article_id':version.article_id,'input_snapshot':version.input_snapshot,
                               'input_fingerprint':version.input_fingerprint}})
            assert len(saved)==len(rows)
            assert db.scalar(select(func.count()).select_from(NewsArticleVersion))==2*len(rows)
            for table in ('news_claim_sources','news_claim_cases','news_claim_decisions','flood_avoidance_zones','flood_reports'):
                assert db.scalar(text('SELECT count(*) FROM '+table))==0
        write('saved-history.json',saved)
        assert metrics['model_starts']==metrics['model_reaps']==1 and metrics['neural_requests']==len(rows)
        assert int(Path('/sys/fs/cgroup/memory.peak').read_text())<2688*1024**2
        partial=read_metrics=json.loads(Path('/output/metrics.json').read_text(encoding='utf-8'))
        write('metrics-complete.json',{**partial,'cgroup_memory_peak_bytes':int(Path('/sys/fs/cgroup/memory.peak').read_text())})
        write('summary.json',{'status':'passed_local_c3a_integration','completed':len(saved),'neural_requests':metrics['neural_requests'],
            'duplicate_neural_requests':0,'new_versions':2*len(saved),'publication_or_zones_created':False,
            'automatic_processing_enabled':False,'cloud_changes':False})
        return 0
    finally:engine.dispose()


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:
        import traceback
        write('private-failure.json',{'code':'c3a_probe_failed','trace':traceback.format_exc()})
        print(json.dumps({'code':'c3a_probe_failed'}));raise SystemExit(2)
