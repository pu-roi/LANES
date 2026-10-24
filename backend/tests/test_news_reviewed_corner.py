from copy import deepcopy
from types import SimpleNamespace as NS
import pytest
from shapely.geometry import LineString, box, mapping, shape
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.crud.news_publication import NewsPublicationError
from app.services.news_reviewed_corner_service import STREETS, build_reviewed_corner, name_matches, projected_buffer
from app.services.news_philstar_street_correction import source_excerpt
from app.services.news_reviewed_corner_projection import corrected_rows


@pytest.mark.parametrize('mapped,reported',[
    ('N. S. Amoranto Sr. Avenue','NS Amoranto'),('Scout Alcaraz Street','Sct Alcaraz St'),
    ('Kitanlad Street','Kitanlad')])
def test_source_reference_aliases(mapped,reported):
    assert name_matches(mapped,reported)
    assert not name_matches(mapped,'Unrelated Street')


def test_reviewed_roles_are_source_specific_and_original_excerpt_is_exact():
    assert [STREETS[i][0] for i in range(5)]==['Don Jose St','Palali St','Banawe St','Tabayoc St','Ubay St']
    claim=NS(road_segment_raw='NS Amoranto cor Palali St.',depth_raw='37 inches, waist deep')
    body='Headline\nFacebook\n'+claim.road_segment_raw+' - '+claim.depth_raw
    assert source_excerpt(body,claim)==body.splitlines()[-1]
    with pytest.raises(ValueError):source_excerpt(body+'\n'+body.splitlines()[-1],claim)


def test_projection_retains_raw_claim_and_does_not_change_other_articles():
    from app.services.news_philstar_pilot import BODY
    from app.services.news_philstar_street_correction import CORRECTION
    from app.services.news_saved_run_service import SavedRunReadError
    receipt=dict(correction_id=CORRECTION,run_id=401,group_id='group',claim_index=1,source_sha256=BODY,
        after=dict(claim_index=1,label='Palali St at NS Amoranto',excerpt='Exact article line',
            geometry_evidence={'reviewed_street':'Palali St'}))
    db=NS(scalars=lambda _: [receipt]);raw={'canonical_road':'NS Amoranto','road_segment_raw':'NS Amoranto cor Palali St.'}
    rows=[dict(run_id=401,group_id='group',claim_index=1,claim=raw),dict(run_id=397,group_id='group',claim_index=1,claim=raw)]
    before=deepcopy(rows);result=corrected_rows(db,rows)
    assert rows==before and result[0]['claim']['canonical_road']=='Palali St'
    assert result[1]==before[1]
    receipt['source_sha256']='0'*64
    with pytest.raises(SavedRunReadError):corrected_rows(db,rows)


def corner_fixture():
    x,y=121.0,14.6
    claim=NS(canonical_city='Quezon City',canonical_barangay='Sienna')
    claim.model_copy=lambda update:NS(**{**claim.__dict__,**update})
    line=LineString([(x,y),(x,y+.002)])
    candidate=NS(candidate_id='osm:1-2:bgy:'+'a'*64,kind='road_section',ambiguous_carriageway=False,
        osm_way_ids=[7],cross_streets=[['N. S. Amoranto Sr. Avenue'],['Next Street']],centerline_geojson=mapping(line))
    preview=NS(candidates=[candidate],candidates_truncated=False,uncertainty_reasons=[],
        osm_catalog_sha256='a'*64,noah_catalog_sha256='b'*64,noah_source_ids={p:str(p) for p in (5,25,100)})
    parent=box(x-.01,y-.01,x+.01,y+.01)
    service=NS(preview=lambda _:preview,roads=NS(locality_boundary=lambda _:box(x,y,x+.01,y+.01),
        boundaries={'quezon city':parent},catalog=NS(ways=[NS(osm_id=7,name='Palali Street',aliases=[],
            route_references=[],bridge='no',tunnel='no',layer='0')])),
        noah=NS(manifest=NS(scenarios={p:NS() for p in (5,25,100)},tile_size=.01),_tile=lambda *a:{3:parent}))
    return claim,candidate,service


def test_saved_map_handoff_uses_reviewed_road_not_original_avenue():
    from app.services.news_reviewed_corner_projection import saved_corner_preview
    from app.services.news_philstar_pilot import BODY
    core=mapping(LineString([(121,14.6),(121,14.6001)]));halo=mapping(box(120.9999,14.5999,121.0001,14.6002))
    item=dict(core=core,geometry=halo,label='Palali St at NS Amoranto',excerpt='Original article line',
        geometry_evidence=dict(reviewed_street='Palali St',osm_way_ids=[7],
            osm_catalog_sha256='a'*64,noah_catalog_sha256='b'*64,noah_source_ids={5:'five',25:'twentyfive',100:'hundred'}))
    db=NS(scalars=lambda _: [dict(run_id=401,source_sha256=BODY,after=item)])
    saved=saved_corner_preview(db,401,1)
    assert saved['road']=='Palali St'
    assert saved['preview'].display_zone.core_geometry==core
    assert saved['preview'].display_zone.aura_geometry==halo
    assert saved['preview'].may_affect_routing is False
    assert saved_corner_preview(None,397,1) is None


@pytest.mark.parametrize('failure',['wrong_crossing','wrong_way','bridge','wrong_locality','missing_scenario','extra_junction'])
def test_unsafe_corner_fails_before_drawing(failure):
    claim,candidate,service=corner_fixture()
    if failure=='wrong_crossing':candidate.cross_streets=[['Wrong Street'],[]]
    if failure=='wrong_way':service.roads.catalog.ways[0].name='Wrong Street'
    if failure=='bridge':service.roads.catalog.ways[0].bridge='yes'
    if failure=='wrong_locality':service.roads.locality_boundary=lambda _:box(0,0,1,1)
    if failure=='missing_scenario':service.noah.manifest.scenarios.pop(5)
    if failure=='extra_junction':
        extra=deepcopy(candidate);extra.centerline_geojson=mapping(LineString([(121.001,14.6),(121.001,14.602)]))
        service.preview(None).candidates.append(extra)
    with pytest.raises(NewsPublicationError):build_reviewed_corner(None,claim,1,25,service)


@pytest.mark.parametrize('case',['rounded','short_block','dry_gap'])
def test_postgis_round_buffer_corner_length_and_noah_gap(settings_factory,case):
    claim,candidate,service=corner_fixture()
    if case=='short_block':candidate.centerline_geojson=mapping(LineString([(121,14.6),(121,14.60005)]))
    if case=='dry_gap':
        wet=box(120.99,14.59,121.01,14.61).difference(box(120.99,14.60006,121.01,14.60012))
        service.noah._tile=lambda *a:{3:wet}
    with settings_factory() as db:
        result=build_reviewed_corner(db,claim,1,25,service)
        core=shape(result['core']);polygon=shape(result['geometry'])
        assert polygon.equals(shape(projected_buffer(db,result['core'],25)))
        length=db.scalar(text('SELECT ST_Length(ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(:g),4326),32651))'),
            {'g':__import__('json').dumps(result['core'])})
        assert 0<length<=25.00001
        assert polygon.bounds[0]<121  # Administrative edge never clips the halo.
        assert core.bounds[0]==pytest.approx(121,abs=1e-8)  # Palali, not Amoranto's east/west axis.
        assert result['geometry_evidence']['outer_buffer_clipped'] is False
        if case=='short_block':assert length<10
        if case=='dry_gap':assert len(core.geoms)==2
