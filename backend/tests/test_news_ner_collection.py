"""Fictional RSS capture checks. No neural inference or external HTTP."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import httpx
import pytest
from sqlalchemy import func, select

from app.models.news import NewsArticle, NewsArticleFeedEntry, NewsArticleVersion, NewsExtractionRun
from app.services.news_discovery_service import discover_news, ARTICLE_REFRESH_INTERVAL
from app.services.news_feed_service import parse_feed
from app.services.news_ner_durable.collection import NativeCollectionContext, saved_publication
from test_news_discovery import source, rss, FEED_URL, ARTICLE_URL
from test_news_ner_durable import trusted
from test_news_processing_postgres import postgres_queue


@pytest.mark.parametrize('wording,known',[
    ('Tue, 20 Oct 2026 10:00:00 +0800',True),
    ('2026-10-20T02:00:00Z',True),
    ('2026-10-20T10:00:00',False),
    ('Tue, 20 Oct 2026 10:00:00 -0000',False),
    ('not a publication clock',False),
])
def test_feed_preserves_original_publication(wording,known):
    entry=parse_feed(rss(f'<item><title>Flood update</title><link>{ARTICLE_URL}</link><pubDate>{wording}</pubDate></item>'),source(),FEED_URL)[0]
    assert entry.publication_raw==wording and entry.publication_timezone_known is known


@pytest.mark.parametrize('body',[
    'Fictional Crescent in Pasig City was flooded knee-deep. ',
    'Flood prevention works were proposed in Pasig City. ',
    'No flooding was observed in Pasig City today. ',
    'Flooding is forecast in Pasig City tomorrow. ',
])
def test_shortlisted_native_body_does_not_require_legacy_locations(postgres_queue,trusted,monkeypatch,body):
    import app.services.news_discovery_service as discovery
    def forbidden(*_args,**_kwargs):pytest.fail('native body admission called legacy location extractor')
    monkeypatch.setattr(discovery,'body_has_metro_manila_flood_claim',forbidden)
    publication=format_datetime(datetime.now(timezone.utc)-timedelta(hours=1))
    item=f'<item><guid>native</guid><title>Flood in Pasig</title><link>{ARTICLE_URL}</link><pubDate>{publication}</pubDate></item>'
    def handler(request):
        return httpx.Response(200,content=rss(item)) if str(request.url)==FEED_URL else httpx.Response(200,text='<article><p>'+body*4+'</p></article>',headers={'content-type':'text/html'})
    with postgres_queue() as db, httpx.Client(transport=httpx.MockTransport(handler)) as client:
        context=NativeCollectionContext(trusted,'test',str(db.get_bind().url.render_as_string(hide_password=False)))
        result=discover_news((source(),),client,db,processing_context=context)
        assert len(result.candidates)==1
        run=db.scalar(select(NewsExtractionRun));version=db.get(NewsArticleVersion,run.article_version_id)
        assert run.mode=='ner_rules_v1' and run.status=='pending'
        assert version.input_snapshot['publication_evidence']=={'raw':publication,'timezone_known':True,'basis':'publisher_feed'}
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun))==1
        discover_news((source(),),client,db,processing_context=context)
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun))==1
        assert db.scalar(select(func.count()).select_from(NewsArticleVersion))==1


@pytest.mark.parametrize('blocked',[False,True])
def test_native_corrections_and_failed_refresh_keep_provenance(postgres_queue,trusted,blocked):
    publication=format_datetime(datetime.now(timezone.utc)-timedelta(hours=1)); revised=False
    body='Fictional Crescent in Pasig City was flooded knee-deep. '*4
    denial='Officials denied the earlier report. Fictional Crescent in Pasig City remains dry. '*3
    def handler(request):
        if str(request.url)==FEED_URL:
            title='Officials issue a correction' if revised else 'Flood in Pasig'
            return httpx.Response(200,content=rss(f'<item><guid>native</guid><title>{title}</title><link>{ARTICLE_URL}</link><pubDate>{publication}</pubDate></item>'))
        if revised and blocked:return httpx.Response(403)
        return httpx.Response(200,text='<article><p>'+(denial if revised else body)+'</p></article>',headers={'content-type':'text/html'})
    with postgres_queue() as db, httpx.Client(transport=httpx.MockTransport(handler)) as client:
        context=NativeCollectionContext(trusted,'test',db.get_bind().url.render_as_string(hide_password=False))
        discover_news((source(),),client,db,processing_context=context)
        original=db.scalar(select(NewsArticleVersion)); snapshot=dict(original.input_snapshot)
        revised=True
        discover_news((source(),),client,db,processing_context=context)
        article=db.scalar(select(NewsArticle))
        assert db.get(NewsArticleVersion,original.id).input_snapshot==snapshot
        if blocked:
            assert article.article_text.strip()==body.strip() and article.title=='Flood in Pasig'
            assert saved_publication(db,article).raw==publication
            assert db.scalar(select(func.count()).select_from(NewsArticleVersion))==1
        else:
            assert article.article_text.strip()==denial.strip() and article.review_state=='pending'
            assert db.scalar(select(func.count()).select_from(NewsArticleVersion))==2


def test_native_collection_refuses_production_before_http(postgres_queue,trusted):
    from app.services.news_ner_durable.contracts import NerEvidenceError
    def forbidden(request):pytest.fail('guard permitted HTTP')
    with postgres_queue() as db,httpx.Client(transport=httpx.MockTransport(forbidden)) as client:
        context=NativeCollectionContext(trusted,'production',db.get_bind().url.render_as_string(hide_password=False))
        with pytest.raises(NerEvidenceError,match='ner_configuration_invalid'):
            discover_news((source(),),client,db,processing_context=context)


@pytest.mark.parametrize('status,body,error',[
    (403,'','Article HTTP 403'),
    (200,'Too short.','Article text unavailable or too short'),
    (200,'Fictional flooded street. '*5000,'Article text exceeds processing limit; full body was not extracted'),
],ids=['publisher-denial','short-body','oversized-body'])
def test_native_retrieval_protections_are_not_bypassed(postgres_queue,trusted,status,body,error):
    item=f'<item><guid>blocked</guid><title>Flood in Pasig</title><link>{ARTICLE_URL}</link></item>'
    def handler(request):
        if str(request.url)==FEED_URL:return httpx.Response(200,content=rss(item))
        return httpx.Response(status,text='<article>'+body+'</article>',headers={'content-type':'text/html'})
    with postgres_queue() as db,httpx.Client(transport=httpx.MockTransport(handler)) as client:
        ctx=NativeCollectionContext(trusted,'test',db.get_bind().url.render_as_string(hide_password=False))
        result=discover_news((source(),),client,db,processing_context=ctx)
        assert not result.candidates and any(error in notice.reason for notice in result.notices)
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun))==0


def test_native_fetch_preserves_exact_unicode_whitespace():
    from app.services.news_discovery_service import fetch_article_text
    body='  🌧️\n'+('Fictional Crescent  was flooded in Pasig City. '*4)+'\n '
    with httpx.Client(transport=httpx.MockTransport(lambda _:httpx.Response(200,text='<article>'+body+'</article>',headers={'content-type':'text/html'}))) as client:
        exact,error=fetch_article_text(source(),ARTICLE_URL,client,preserve_whitespace=True)
        legacy,_=fetch_article_text(source(),ARTICLE_URL,client)
    assert error is None and exact==body and legacy!=body


def test_duplicate_feeds_with_equivalent_clock_formats_keep_first_proof(postgres_queue,trusted):
    published=datetime.now(timezone.utc).replace(microsecond=0)-timedelta(hours=1)
    original=format_datetime(published);secondary=published.isoformat()
    feeds=(FEED_URL,FEED_URL+'?second')
    registry=replace(source(),feed_urls=feeds)
    def handler(request):
        if str(request.url) in feeds:
            raw=original if str(request.url)==FEED_URL else secondary
            return httpx.Response(200,content=rss(f'<item><guid>same</guid><title>Flood in Pasig</title><link>{ARTICLE_URL}</link><pubDate>{raw}</pubDate></item>'))
        return httpx.Response(200,text='<article>'+('Fictional Crescent in Pasig City was flooded. '*4)+'</article>',headers={'content-type':'text/html'})
    with postgres_queue() as db,httpx.Client(transport=httpx.MockTransport(handler)) as client:
        ctx=NativeCollectionContext(trusted,'test',db.get_bind().url.render_as_string(hide_password=False))
        discover_news((registry,),client,db,processing_context=ctx)
        article=db.scalar(select(NewsArticle))
        assert saved_publication(db,article).raw==original
        assert db.scalar(select(func.count()).select_from(NewsArticleFeedEntry))==2
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun))==1
