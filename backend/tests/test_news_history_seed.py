from copy import deepcopy
from datetime import datetime, timezone
import hashlib

import pytest
from sqlalchemy import func, select

from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.services.news_history_capture_registration import register_captures
from app.services.news_history_seed_inventory import training_sources, complete_training_captures
from app.services.news_historical_outputs import archive_assumed_closure
from app.services.news_historical_preparation import SourceSpec, build_preparation, save_private_package, text_sha
from app.services.news_historical_processing import load_historical_package, database_identity
from app.services.news_ner_durable.contracts import sha
from app.services.news_sources import NewsSource
from test_operational_settings_postgres import isolated_db
from test_news_ner_durable import trusted
from historical_processing_fixtures import fictional_documents
from test_news_ner_integration import c3b_db

SOURCE=NewsSource('fictional','Fictional',('example.org',),('https://example.org/feed',),datetime.now().date(),True)


@pytest.mark.parametrize('count',[1,3])
def test_general_package_round_trip_outside_september(trusted,tmp_path,count):
    frozen=fictional_documents(trusted)
    inventory=deepcopy(frozen['inventory.json']); row=inventory['sources'][0]
    inventory['history']=[];inventory['sources']=[]; specs=[]
    for index in range(count):
        source=deepcopy(row);source.update(article_id=100+index,version_id=200+index)
        source['input_snapshot']['canonical_url']=f'https://example.org/general-{index}'
        source['input_fingerprint']=sha(source['input_snapshot'])
        inventory['sources'].append(source)
        snapshot=source['input_snapshot']
        specs.append(SourceSpec(source['article_id'],source['version_id'],source['input_fingerprint'],
            text_sha(snapshot['article_text']),snapshot['canonical_url'],snapshot['publisher'],snapshot['published_at']))
    documents=build_preparation(inventory,frozen['manifest.json']['assets'],specs=tuple(specs),candidates=(),dataset_id='general-history-v1')
    save_private_package(tmp_path/'batch',documents)
    package=load_historical_package(tmp_path/'batch/manifest.json',sha(documents['manifest.json']))
    assert len(package.captures)==count and package.manifest['dataset_id']=='general-history-v1'
    assert frozen==fictional_documents(trusted)


@pytest.mark.parametrize('day,expected',[('2026-12-31','2027-01-01T00:00:00+08:00'),('2028-02-29','2028-03-01T00:00:00+08:00')])
def test_date_only_endpoint_preserves_unknown_hour(day,expected):
    observation={'precision':'date','occurrence_date':day,'observed_at':None}
    before=deepcopy(observation)
    endpoint,basis=archive_assumed_closure(observation,{})
    assert endpoint.isoformat()==expected and basis=='assumed_source_day_end' and observation==before
    assert archive_assumed_closure(observation,{'source_clearance_present':True})==(None,'unknown')
    assert archive_assumed_closure({'precision':'unknown'}, {})==(None,'unknown')


def test_training_membership_uses_complete_sources_and_excludes_dev():
    body='Complete original source body'
    digest=hashlib.sha256(body.encode()).hexdigest()
    metadata=[{'split':'train','source_sha256':digest},{'partition':'dev','source_sha256':'b'*64}]
    register=[{'source_sha256':digest,'source_id':'original','url':'https://example.org/source','publisher':'Fictional'}]
    training=training_sources(metadata,register)
    assert len(training)==1
    row={'text':'annotated passage must not be used','entities':[{'fictional':'annotation'}],
        'source':{'text':body,'text_sha256':digest,'url':'https://example.org/source','publisher':'Fictional'}}
    captures=complete_training_captures([row],training)
    assert captures[digest]['text']==body and 'entities' not in captures[digest]
    with pytest.raises(ValueError,match='capture_hash_mismatch'):
        complete_training_captures([{**row,'source':{**row['source'],'text':'tampered'}}],training)


def test_capture_preflight_repeats_and_preserves_existing_article(c3b_db):
    body='On October 1, 2026, Fictional Road in Pasig was flooded knee-deep.'
    digest=hashlib.sha256(body.encode()).hexdigest()
    captures={digest:{'url':'https://example.org/training-source','text':body,'title':'Training source',
        'publisher':'Fictional','published_at':'2026-10-01','captured_at':'2026-10-02'}}
    engine=c3b_db.kw['bind']
    options=dict(captures_sha256=sha(captures),target_sha256=database_identity(engine),
        confirmed_database=engine.url.database,environment='test',sources=(SOURCE,))
    preflight=register_captures(engine,captures,**options)
    assert not preflight['database_writes_performed']
    applied=register_captures(engine,captures,apply=True,**options)
    repeated=register_captures(engine,captures,apply=True,**options)
    assert applied['version_ids']==repeated['version_ids'] and len(applied['version_ids'])==1
    # Independent transaction owns these fixture-only rows; remove via a fresh
    # disposable database in the enclosing test invocation, never shared storage.
    from sqlalchemy.orm import Session
    with Session(engine) as check:
        version=check.get(NewsArticleVersion,applied['version_ids'][0])
        article=check.get(NewsArticle,version.article_id)
        assert article.review_state=='local_update' and article.published_at is None
        assert check.scalar(select(func.count()).select_from(NewsExtractionRun))==0
        article.title='Newer mutable article title';check.commit()
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts=list(pool.map(lambda _:register_captures(engine,captures,apply=True,**options),range(2)))
    assert all(r['version_ids']==applied['version_ids'] for r in receipts)
    with Session(engine) as check:
        assert check.scalar(select(NewsArticle.title))=='Newer mutable article title'
        assert check.scalar(select(func.count()).select_from(NewsArticleVersion))==1
    denied=register_captures(engine,captures,**{**options,'sources':()})
    assert denied['selection'][0]['outcome']=='unresolved'
    with pytest.raises(ValueError,match='capture_changed'):
        register_captures(engine,captures,**{**options,'captures_sha256':'0'*64})


def test_registration_failure_rolls_back_article_and_version(c3b_db):
    from sqlalchemy import event
    from sqlalchemy.orm import Session
    engine=c3b_db.kw['bind'];body='Original complete training source.'
    digest=hashlib.sha256(body.encode()).hexdigest()
    captures={digest:{'url':'https://example.org/rollback','text':body,'title':'Original','published_at':None}}
    def fail(_c,_cursor,statement,_params,_context,_many):
        if statement.startswith('INSERT INTO news_article_versions'):
            raise RuntimeError('fixture version failure')
    event.listen(engine,'before_cursor_execute',fail)
    try:
        with pytest.raises(RuntimeError,match='fixture version failure'):
            register_captures(engine,captures,captures_sha256=sha(captures),target_sha256=database_identity(engine),
                confirmed_database=engine.url.database,environment='test',apply=True,sources=(SOURCE,))
    finally:event.remove(engine,'before_cursor_execute',fail)
    with Session(engine) as check:
        assert check.scalar(select(func.count()).select_from(NewsArticle))==0
