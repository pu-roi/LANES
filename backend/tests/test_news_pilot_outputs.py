"""Paired persistence, repeat/deactivation safety and source-count separation."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import json

import httpx
import pytest
from shapely.geometry import box, mapping
from sqlalchemy import func, select

from app.models.news import NewsExtractionRun
from app.models.report import FloodEvent, FloodAvoidanceZone, FloodEventTimelineEntry
from app.services.news_pilot_outputs import pilot_outputs
from app.services.news_three_article_pilot import PilotAuthority
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution_worker import resolve_native_runs
from app.services.flood_event_service import deactivate_zone_and_end_event_if_final
from app.services.flood_routing_policy import get_active_flood_zones
from test_news_three_article_pilot import selected, grant
from test_news_native_resolution import answer, NOW, TEXT
from test_news_ner_integration import c3b_db, operational_trusted, base_trusted, SOURCES
from test_news_placement_preview import service
from test_news_road_placement import write_catalog, ways


@pytest.mark.asyncio
@pytest.mark.parametrize('selected', [TEXT, TEXT.removesuffix('.')+' near Guazon Street.'], indirect=True)
async def test_archive_plus_active_then_repeat_preserves_manual_deactivation(c3b_db, operational_trusted, selected, tmp_path):
    ids, resolver, authority = selected
    def handler(request):
        doc = json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        rows = [answer(m, **({'road_section': 'near Guazon Street', 'section_evidence': [0]}
            if m['label'] == 'ROAD' and 'near Guazon Street' in doc['evidence_text'] else {})) for m in doc['targets']]
        return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
            {'text': json.dumps({'results': rows})}]}}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await resolve_native_runs(c3b_db, (ids[0],), trusted=operational_trusted,
            resolver=resolver, sources=SOURCES, client=client, clock=lambda: NOW, pilot_authorization=authority)
    run_id = result['runs'][0]['run_id']
    p = deepcopy(authority.policy)
    p.update(allowed_operations=['outputs'], previewed_at=NOW.isoformat(), outputs_sha256=None)
    def auth(): return PilotAuthority(p, sha(p), operational_trusted)
    provider = service(tmp_path, city='City of Pasig')
    roads = ways(); roads[0]['name'] = 'Fictional Crescent'; roads[1]['name'] = 'Guazon Street'
    provider.roads = write_catalog(tmp_path/'roads', roads, cities=[dict(name='City of Pasig', relation_id=106569,
        boundary=mapping(box(120.99,14.60,121.03,14.67)))])
    preview = pilot_outputs(c3b_db.kw['bind'], auth(), run_id, sources=SOURCES, placement_service=provider)
    p['outputs_sha256'] = preview['outputs_sha256']
    saved = pilot_outputs(c3b_db.kw['bind'], auth(), run_id, sources=SOURCES, placement_service=provider, apply=True)
    repeated = pilot_outputs(c3b_db.kw['bind'], auth(), run_id, sources=SOURCES, placement_service=provider, apply=True)
    assert saved['status'] == repeated['status'] == 'completed'
    qualified = [o for o in saved['outputs'] if o.get('active')]
    with c3b_db() as db:
        if 'near Guazon Street' not in selected[2].policy['inputs'][0]['input_snapshot']['article_text']:
            assert not qualified
            assert db.scalar(select(func.count()).select_from(FloodEvent)) == 0
            assert db.scalar(select(func.count()).select_from(FloodAvoidanceZone)) == 0
            assert all(o.get('archive', o)['outcome'] == 'unresolved' for o in saved['outputs'])
            return
        assert len(qualified) == 1, saved
        assert db.scalar(select(func.count()).select_from(FloodEvent)) == 2
        assert db.scalar(select(func.count()).select_from(FloodAvoidanceZone)) == 2
        active = db.get(FloodAvoidanceZone, qualified[0]['active']['zone_ids'][0])
        assert active.is_active and active.expires_at is None
        assert get_active_flood_zones(db) == []
        deactivate_zone_and_end_event_if_final(db, active, occurred_at=datetime.now(timezone.utc)+timedelta(minutes=1))
        db.commit()
    pilot_outputs(c3b_db.kw['bind'], auth(), run_id, sources=SOURCES, placement_service=provider, apply=True)
    with c3b_db() as db:
        assert not db.get(FloodAvoidanceZone, qualified[0]['active']['zone_ids'][0]).is_active
        assert db.scalar(select(func.count()).select_from(FloodEvent)) == 2
