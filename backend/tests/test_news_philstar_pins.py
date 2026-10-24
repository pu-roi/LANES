from copy import deepcopy
from types import SimpleNamespace as NS

import pytest
from shapely.geometry import LineString, box, mapping, shape
from sqlalchemy import text

from app.services.news_philstar_pin_service import PINS, build_pin
from app.services.news_reviewed_corner_projection import corrected_rows, saved_corner_preview
from app.services.news_philstar_pilot import BODY


def fixture():
    pin=PINS[5];x,y=pin['longitude'],pin['latitude']
    nodes=[(1,x,y-.001),(2,x,y+.001)]
    way=NS(osm_id=pin['osm_way_id'],name=pin['road'],nodes=nodes,bridge='',tunnel='',layer='')
    boundary=box(x-.01,y-.01,x+.01,y+.01)
    roads=NS(revision='a'*64,catalog=NS(ways=[way]),digest='a'*64,boundaries={'quezon city':boundary},
        barangays=NS(records={('quezon city','del monte'):(NS(barangay='Del Monte'),boundary)}))
    noah=NS(manifest=NS(scenarios={p:NS(source_id=str(p)) for p in [5,25,100]}),digest='b'*64,
        intersections=lambda line:{p:{3:line} for p in [5,25,100]})
    return NS(canonical_city='Quezon City',canonical_barangay='Damayan'),NS(roads=roads,noah=noah)


@pytest.mark.parametrize('case',['remote','bridge','wrong_name','city','source_barangay','scenario'])
def test_pin_rejects_changed_identity_and_assets_before_db_access(case):
    claim,service=fixture();way=service.roads.catalog.ways[0]
    if case=='remote':way.nodes=[(1,120,14),(2,120,14.001)]
    if case=='bridge':way.bridge='yes'
    if case=='wrong_name':way.name='Different Road'
    if case=='city':service.roads.boundaries['quezon city']=box(0,0,1,1)
    if case=='source_barangay':claim.canonical_barangay='Del Monte'
    if case=='scenario':service.noah.manifest.scenarios.pop(5)
    with pytest.raises(ValueError):build_pin(None,claim,5,25,service)


def test_pin_projection_keeps_reported_barangay_and_raw_claim_immutable():
    from app.services.news_philstar_pin_service import VERSION
    claim={'canonical_road':None,'raw_place_name':'Brgy. Damayan','canonical_barangay':'Damayan'}
    item={'claim_index':5,'label':'West Riverside Interior','excerpt':'Exact source sentence',
        'geometry_evidence':{'reviewed_pin':PINS[5]}}
    receipt={'run_id':401,'group_id':'g5','claim_index':5,'source_sha256':BODY,'policy_version':VERSION,'after':item}
    class DB:
        calls=0
        def scalars(self,_):
            self.calls+=1
            return [] if self.calls==1 else [receipt]
    rows=[dict(run_id=401,group_id='g5',claim_index=5,claim=claim)];before=deepcopy(rows)
    projected=corrected_rows(DB(),rows)
    assert rows==before
    assert projected[0]['claim']['canonical_barangay']=='Damayan'
    assert projected[0]['claim']['canonical_road']=='West Riverside Drive'
    assert projected[0]['_reviewed_placement_saved']
    receipt['source_sha256']='0'*64
    with pytest.raises(ValueError):corrected_rows(DB(),rows)


def test_baseline_excludes_only_live_visit_telemetry_and_keeps_flood_source_user_records(monkeypatch):
    from app.services.news_philstar_pin_service import fingerprints
    from app.services import news_philstar_street_correction as old
    baseline={'visitor_daily_visits':['changing'],'flood_avoidance_zones':['zone'],
        'news_extraction_runs':['source'],'users':['user'],'system_settings':['flags']}
    monkeypatch.setattr(old,'row_fingerprints',lambda _:baseline)
    assert fingerprints(None)=={k:v for k,v in baseline.items() if k!='visitor_daily_visits'}
    assert 'visitor_daily_visits' in baseline


@pytest.mark.parametrize('case',['rounded','junction_stop','gap'])
def test_postgis_pin_uses_reviewed_position_full_round_buffer_and_stops_at_junction(settings_factory,case):
    claim,service=fixture();pin=PINS[5];x,y=pin['longitude'],pin['latitude']
    if case=='junction_stop':
        service.roads.catalog.ways[0].nodes=[(1,x,y-.00005),(2,x,y+.00005)]
    if case=='gap':
        service.noah.intersections=lambda line:{p:{3:line.difference(box(x-.01,y-.00003,x+.01,y+.00003))} for p in [5,25,100]}
    with settings_factory() as db:
        result=build_pin(db,claim,5,25,service)
        length=db.scalar(text('SELECT ST_Length(ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(:g),4326),32651))'),{'g':__import__('json').dumps(result['core'])})
        assert 0<length<=50.00001
        if case=='junction_stop':assert length<12
        if case=='gap':assert len(shape(result['core']).geoms)==2
        assert shape(result['geometry']).covers(shape(result['core']))
        assert result['geometry_evidence']['mapped_barangays']==['Del Monte']
        assert result['geometry_evidence']['reported_barangay']=='Damayan'
        assert result['geometry_evidence']['locality_mismatch'] is True
        assert result['geometry_evidence']['may_affect_routing'] is False
