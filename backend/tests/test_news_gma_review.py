"""GMA review bounds, cached adoption, semantic stop and archive-only writes."""
from copy import deepcopy
import json

import httpx
import pytest
from sqlalchemy import func, select

from app.services.news_gma_review import GmaBatchPlan, batch_manifest, REQUESTS, archive_outputs
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_three_article_pilot import PilotAuthority
from app.services.news_ner_durable.resolution_worker import resolve_native_runs
from app.models.report import FloodEvent, FloodAvoidanceZone
from app.models.news_publication import NewsClaimDecision, NewsClaimZoneLink
from test_news_ner_integration import c3b_db, operational_trusted, base_trusted, SOURCES
from test_news_three_article_pilot import selected
from test_news_native_resolution import answer, NOW, TEXT, trusted
from test_news_placement_preview import service
from test_news_road_placement import write_catalog, ways
from shapely.geometry import box, mapping


def test_exact_gma_batches_and_unchanged_dollar_cap():
    plan = GmaBatchPlan(batch_manifest())
    candidates = [{'id':'n'+str(i)} for i in range(51)]
    batches = plan.batches(candidates)
    assert [len(b) for b in batches] == [4,8,8,8,8,8,7]
    assert [t for batch in batches for t in batch] == candidates
    assert 730676000 + sum(cost for _,cost in REQUESTS[1:]) == 985885400 < 1000000000
    with pytest.raises(ResolutionError, match='inventory_changed'):
        plan.batches(candidates[:-1])
    with pytest.raises(ResolutionError, match='inventory_changed'):
        plan.batches(candidates[::-1])
    changed = batch_manifest(); changed['sizes'] = [51]
    with pytest.raises(ResolutionError, match='manifest_changed'):
        GmaBatchPlan(changed)
    with pytest.raises(ResolutionError, match='frozen_request_changed'):
        plan.adopt(0, {}, {}, None, None)


@pytest.mark.parametrize('operation', ['outputs','ner','activate','pilot-apply'])
def test_gma_authority_cannot_activate_or_process_other_articles(operation):
    policy = {'schema_version':'news-gma-review-v1', 'allowed_operations':[operation]}
    with pytest.raises(ResolutionError, match='authority_invalid'):
        PilotAuthority(policy,sha(policy),None).validate(None)


@pytest.mark.asyncio
async def test_semantic_failure_prevents_second_batch(trusted):
    from test_news_native_resolution import setup
    from dataclasses import replace
    service,_,context,baseline,_,_ = setup(trusted)
    service.config = replace(service.config, batch_size=1)
    calls = []
    def respond(request):
        doc=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        calls.append(doc)
        rows=[answer(t, clock_text='11 PM') for t in doc['targets']]
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[
            {'text':json.dumps({'results':rows})}]}}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(ResolutionError, match='clock'):
            await service.resolve(context.source(),baseline,parent_run_id=1,parent_result_sha256='0'*64,client=client)
    assert len(calls)==1


@pytest.mark.asyncio
@pytest.mark.parametrize('selected', [TEXT.removesuffix('.')+' near Guazon Street.'], indirect=True)
async def test_archive_writer_saves_only_ended_inactive_and_reuses(c3b_db, operational_trusted, selected, tmp_path, monkeypatch):
    ids,resolver,authority=selected
    def respond(request):
        doc=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        rows=[answer(t,**({'road_section':'near Guazon Street','section_evidence':[0]} if t['label']=='ROAD' else {})) for t in doc['targets']]
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[
            {'text':json.dumps({'results':rows})}]}}]})
    # Reuse the real disposable pipeline fixture's authority. GMA's narrow
    # source/parent adoption is independently checked against its frozen capture.
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        result=await resolve_native_runs(c3b_db,(ids[0],),trusted=operational_trusted,resolver=resolver,
            sources=SOURCES,client=client,clock=lambda:NOW,pilot_authorization=authority)
    run_id=result['runs'][0]['run_id']
    from app.services import news_pilot_outputs
    original=news_pilot_outputs._qualify
    def qualify(*args,**kwargs):
        kwargs['operation']='outputs'
        return original(*args,**kwargs)
    monkeypatch.setattr(news_pilot_outputs,'_qualify',qualify)
    p=deepcopy(authority.policy);p.update(allowed_operations=['outputs'],previewed_at=NOW.isoformat(),outputs_sha256=None)
    def auth():return PilotAuthority(p,sha(p),operational_trusted)
    provider=service(tmp_path,city='City of Pasig')
    roads=ways();roads[0]['name']='Fictional Crescent';roads[1]['name']='Guazon Street'
    provider.roads=write_catalog(tmp_path/'roads',roads,cities=[dict(name='City of Pasig',relation_id=106569,
        boundary=mapping(box(120.99,14.60,121.03,14.67)))])
    preview=archive_outputs(c3b_db.kw['bind'],auth(),run_id,sources=SOURCES,placement_service=provider)
    p['outputs_sha256']=preview['outputs_sha256']
    first=archive_outputs(c3b_db.kw['bind'],auth(),run_id,sources=SOURCES,placement_service=provider,apply=True)
    second=archive_outputs(c3b_db.kw['bind'],auth(),run_id,sources=SOURCES,placement_service=provider,apply=True)
    assert first['active_instances_created']==second['active_instances_created']==0
    with c3b_db() as db:
        assert db.scalar(select(func.count()).select_from(FloodEvent))==1
        assert db.scalar(select(func.count()).select_from(FloodAvoidanceZone))==1
        event=db.scalar(select(FloodEvent));zone=db.scalar(select(FloodAvoidanceZone))
        assert str(event.status.value)=='ended' and event.ended_at is not None and not zone.is_active
        assert db.scalar(select(func.count()).select_from(NewsClaimDecision))==0
        assert db.scalar(select(func.count()).select_from(NewsClaimZoneLink))==0
