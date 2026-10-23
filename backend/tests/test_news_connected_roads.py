"""Road identity precedes modeled fragments; administrative borders do not clip."""
from copy import deepcopy
import gzip
import hashlib
import json
from types import SimpleNamespace

import pytest
from shapely.geometry import LineString, Point, box, mapping, shape

from app.crud.news_publication import NewsPublicationError
from app.services.news_connected_road_service import ConnectedRoadService, components, road_name, qualified_junction_overlap
from app.services.news_ner_durable.contracts import sha


def way(identity, nodes, name='Example Avenue', **extra):
    return {'osm_id': identity, 'name': name, 'nodes': nodes, **extra}


def service(tmp_path, ways=None, **changes):
    roads = tmp_path / 'roads'; roads.mkdir()
    doc = {'format_version': 1, 'source_id': 'osm:fixture', 'snapshot_at': '2026-09-27T00:56:56Z',
        'osm_sha256': 'a'*64, 'ways': ways or [way(1, [(1,121,14.63),(2,121.002,14.63)]),
            way(2, [(2,121.002,14.63),(3,121.004,14.63)])],
        'cities': [{'name': 'Pasig', 'boundary': mapping(box(120.99,14.62,121.0025,14.64))}],
        'incomplete_ways': []}
    doc.update(changes)
    raw = gzip.compress(json.dumps(doc).encode(), mtime=0)
    (roads/'roads.json.gz').write_bytes(raw)
    (roads/'manifest.json').write_text(json.dumps({'catalog_sha256': hashlib.sha256(raw).hexdigest()}))
    result = ConnectedRoadService(roads, tmp_path/'unconfigured-noah')
    result.noah = FakeNoah(box(120.99,14.62,121.02,14.64))
    return result


class FakeNoah:
    def __init__(self, polygon):
        self.polygon = polygon
        self.revision = 'b'*64
        self.manifest = SimpleNamespace(bounds=(120.9,14.5,121.1,14.8), tile_size=.02,
            scenarios={p: SimpleNamespace(source_id='noah-fixture-'+str(p)) for p in (5,25,100)})

    def intersections(self, line):
        return {p: {1: line.intersection(self.polygon), 2: LineString(), 3: LineString()} for p in (5,25,100)}

    def _tile(self, period, key):
        return {1: self.polygon, 2: box(122,15,122.01,15.01), 3: box(122,15,122.01,15.01)}


def claim(**changes):
    return SimpleNamespace(**({'canonical_road':'Example Avenue','raw_place_name':'Example Ave.',
        'canonical_city':'City of Pasig','canonical_barangay':'Unknown boundary',
        'road_segment_raw':'Example Avenue'} | changes))


def test_connected_road_crosses_city_and_barangay_without_clip(tmp_path):
    s = service(tmp_path)
    c = claim()
    before = deepcopy(c.__dict__)
    output = s.build(c, hint=[14.63,121.001])
    assert output.evidence['osm_way_ids'] == [1,2]
    assert shape(output.geometry).bounds[2] > 121.004
    assert not output.evidence['administrative_boundaries_clip']
    assert c.__dict__ == before
    assert len(output.evidence['scenario_fragments']) == 6
    assert output.evidence['modeled_fragment_length_metres'] == pytest.approx(output.evidence['source_length_metres'])


def test_unknown_barangay_does_not_require_boundary(tmp_path):
    s = service(tmp_path)
    assert s.build(claim(canonical_barangay='Missing barangay'), hint=[14.63,121.001]).geometry


def test_no_pin_accepts_only_unique_network(tmp_path):
    s = service(tmp_path)
    assert s.build(claim()).evidence['selection']['location_hint']['origin'] == 'source_road_and_city'


def test_same_name_disconnected_network_remains_separate(tmp_path):
    roads = [way(1,[(1,121,14.63),(2,121.002,14.63)]),way(2,[(3,121,14.631),(4,121.002,14.631)])]
    s = service(tmp_path, roads)
    with pytest.raises(NewsPublicationError, match='disconnected_identity'):
        s.build(claim())
    out = s.build(claim(), hint=[14.63,121.001])
    assert out.evidence['osm_way_ids'] == [1]


def test_equally_close_pin_cannot_choose_parallel_unconnected_road(tmp_path):
    s = service(tmp_path,[way(1,[(1,121,14.63),(2,121.002,14.63)]),
                         way(2,[(3,121,14.6308),(4,121.002,14.6308)])])
    with pytest.raises(NewsPublicationError, match='hint_ambiguous'):
        s.build(claim(),hint=[14.6304,121.001])


def test_branch_is_not_silently_dropped(tmp_path):
    s=service(tmp_path,[way(1,[(1,121,14.63),(2,121.002,14.63)]),
        way(2,[(2,121.002,14.63),(3,121.004,14.63)]),way(3,[(2,121.002,14.63),(4,121.002,14.632)])])
    with pytest.raises(NewsPublicationError, match='branch_unresolved'):
        s.build(claim(),hint=[14.63,121.001])


@pytest.mark.parametrize('changes', [{'bridge':'yes'},{'layer':'1'},{'tunnel':'building_passage'}])
def test_named_road_never_globally_ignores_grade(tmp_path,changes):
    s=service(tmp_path,[way(1,[(1,121,14.63),(2,121.002,14.63)],**changes)])
    with pytest.raises(NewsPublicationError,match='grade_unresolved'):
        s.build(claim(),hint=[14.63,121.001])


def test_verified_alias_may_continue_connected_network(tmp_path):
    s=service(tmp_path,[way(1,[(1,121,14.63),(2,121.002,14.63)]),
        way(2,[(2,121.002,14.63),(3,121.004,14.63)],name='Renamed Avenue',aliases=['Example Avenue'])])
    assert s.build(claim()).evidence['osm_way_ids']==[1,2]


def test_name_change_without_alias_stops_road_identity(tmp_path):
    s=service(tmp_path,[way(1,[(1,121,14.63),(2,121.002,14.63)]),
        way(2,[(2,121.002,14.63),(3,121.004,14.63)],name='Other Avenue')])
    assert s.build(claim()).evidence['osm_way_ids']==[1]


def test_incomplete_named_way_blocks_network(tmp_path):
    s=service(tmp_path,incomplete_ways=[{'name':'Example Avenue'}])
    with pytest.raises(NewsPublicationError,match='incomplete_coverage'):
        s.build(claim())


@pytest.mark.parametrize('section', ['between First and Second Streets','from First to Second',
    'corner First Street','Example frontage road','Example service road'])
def test_explicit_physical_qualifier_is_not_expanded_to_whole_road(tmp_path,section):
    s=service(tmp_path)
    with pytest.raises(NewsPublicationError,match='explicit_section_adapter_required'):
        s.build(claim(road_segment_raw=section))


def test_empty_noah_overlap_does_not_invent_polygon(tmp_path):
    s=service(tmp_path);s.noah=FakeNoah(box(121.05,14.65,121.06,14.66))
    with pytest.raises(NewsPublicationError,match='no_modeled_overlap'):
        s.build(claim())


def test_large_dry_gap_is_preserved_as_two_components(tmp_path):
    s=service(tmp_path)
    s.noah=FakeNoah(box(120.99,14.62,121.02,14.64).difference(box(121.001,14.629,121.003,14.631)))
    out=s.build(claim());assert len(out.evidence['component_centerlines'])==2
    assert not shape(out.geometry).covers(Point(121.002,14.63))


def test_margin_preserves_narrow_modeled_dry_gap(tmp_path):
    s=service(tmp_path)
    s.noah=FakeNoah(box(120.99,14.62,121.02,14.64).difference(box(121.0018,14.629,121.0022,14.631)))
    output = s.build(claim())
    assert not shape(output.geometry).covers(Point(121.002,14.63))
    assert len(output.evidence['component_centerlines']) == 2


def test_changed_catalog_is_rejected(tmp_path):
    s=service(tmp_path)
    p=tmp_path/'roads/roads.json.gz';p.write_bytes(p.read_bytes()+b'corrupted')
    with pytest.raises(Exception):
        ConnectedRoadService(tmp_path/'roads',tmp_path/'noah')


def test_noah_coverage_limits_are_not_city_borders(tmp_path):
    s=service(tmp_path);s.noah.manifest.bounds=(120.999,14.629,121.0039,14.631)
    with pytest.raises(NewsPublicationError,match='asset_coverage'):
        s.build(claim())


def test_abbreviations_are_exact_not_fuzzy():
    assert road_name('F. Sevilla Blvd.')==road_name('F. Sevilla Boulevard')
    assert road_name('Rizal Ave Extn')==road_name('Rizal Avenue Extension')
    assert road_name('Rizal Avenue')!=road_name('Rizal Avenue Extension')


def reviewed_loop(tmp_path):
    nodes = {1:(121,14.63),2:(121.001,14.63),3:(121.002,14.6305),
             4:(121.003,14.63),5:(121.002,14.6295),6:(121.004,14.63)}
    roads = [way(i,[(n,*nodes[n]) for n in ns]) for i,ns in
             [(1,[1,2]),(2,[2,3,4]),(3,[4,5,2]),(4,[4,6])]]
    s = service(tmp_path,roads)
    s.features = {'named_network_reviews':[{'way_ids':[1,2,3,4], 'network_sha256':sha(roads),
        'way_tags':{str(i):{'oneway':'yes','name':'Example Avenue','highway':'secondary'} for i in (2,3)}}]}
    return s


def test_reviewed_oneway_loop_retains_both_arms(tmp_path):
    out=reviewed_loop(tmp_path).build(claim())
    assert out.evidence['osm_way_ids']==[1,2,3,4]
    assert out.evidence['selection']['network_topology']['cycle_way_ids']==[2,3]
    assert out.evidence['selection']['network_topology']['branches_retained']


def test_loop_without_source_direction_proof_rejected(tmp_path):
    s=reviewed_loop(tmp_path);s.features['named_network_reviews'][0]['way_tags']['3']['oneway']='no'
    with pytest.raises(NewsPublicationError,match='direction_unverified'):s.build(claim())


def test_loop_changed_source_network_rejected(tmp_path):
    s=reviewed_loop(tmp_path);s.features['named_network_reviews'][0]['network_sha256']='0'*64
    with pytest.raises(NewsPublicationError,match='review_changed'):s.build(claim())


def underloop(tmp_path):
    s=service(tmp_path,[way(9,[(90,121.001,14.629),(91,121.001,14.631)],
        name='Marcos Highway',bridge='yes',layer='1')])
    tags={'highway':'primary_link','access':'yes','destination:street':'C-5'}
    w=way(10,[(10,121,14.63),(11,121.002,14.63)],name='',tags={**tags,'tunnel':'building_passage'})
    s.features={'features':[{'reported_section':'Marcos Highway Underloop','city':'City of Pasig',
        'feature_kind':'underloop','source_pbf_sha256':'a'*64,'ways':[w],'overhead_way_ids':[9],
        'junction_bounds':[10,11], 'junction_evidence':{
            str(n):[w,way(100+n,[(n,121,14.63),(200+n,121,14.631)])] for n in (10,11)}}]}
    return s


def test_underloop_uses_ground_link_not_overhead_bridge(tmp_path):
    out=underloop(tmp_path).build(claim(canonical_road=None,road_segment_raw='Marcos Highway Underloop'),hint=[14.63,121.001])
    assert out.evidence['osm_way_ids']==[10]
    assert out.evidence['selection']['overhead_way_ids']==[9]


@pytest.mark.parametrize('field,value',[('layer','1'),('bridge','yes'),('access','no'),('tunnel','yes')])
def test_underloop_exception_is_feature_specific(tmp_path,field,value):
    s=underloop(tmp_path);s.features['features'][0]['ways'][0]['tags'][field]=value
    with pytest.raises(NewsPublicationError,match='grade_or_access'):
        s.build(claim(road_segment_raw='Marcos Highway Underloop'),hint=[14.63,121.001])


def test_underloop_wrong_junction_membership_rejected(tmp_path):
    s=underloop(tmp_path);s.features['features'][0]['junction_evidence']['10'][1]['nodes']=[(100,121,14.63),(101,121,14.631)]
    with pytest.raises(NewsPublicationError,match='junction_unverified'):
        s.build(claim(road_segment_raw='Marcos Highway Underloop'),hint=[14.63,121.001])


def junction_output(group,geometry,nodes):
    return {'group_id':group,'geometry':mapping(geometry),'geometry_evidence':{'source_node_coordinates':nodes}}


def test_selected_corridors_can_share_an_actual_junction():
    a=junction_output('a',box(121,14.63,121.0002,14.6302),[(1,121.0001,14.6301)])
    b=junction_output('b',box(121.0001,14.6301,121.0003,14.6303),[(1,121.0001,14.6301)])
    proof=qualified_junction_overlap(a,b)
    assert proof['shared_osm_node_ids']==[1] and not proof['changes_geometry']


@pytest.mark.parametrize('nodes', [[(2,121.0001,14.6301)],[(1,121.0002,14.6301)]])
def test_geometry_crossing_does_not_prove_shared_junction(nodes):
    a=junction_output('a',box(121,14.63,121.0002,14.6302),[(1,121.0001,14.6301)])
    b=junction_output('b',box(121.0001,14.6301,121.0003,14.6303),nodes)
    with pytest.raises(NewsPublicationError,match='without_shared_junction'):qualified_junction_overlap(a,b)


def test_shared_junction_does_not_authorize_remote_overlap():
    a=junction_output('a',box(121,14.63,121.01,14.64),[(1,121,14.63)])
    b=junction_output('b',box(121.001,14.631,121.009,14.639),[(1,121,14.63)])
    with pytest.raises(NewsPublicationError,match='outside_junction'):qualified_junction_overlap(a,b)


def test_component_limit_stops_instead_of_dropping_fragments(tmp_path):
    from shapely import union_all
    s=service(tmp_path)
    s.noah=FakeNoah(union_all([box(121+i*.00015,14.629,121+i*.00015+.00008,14.631) for i in range(26)]))
    with pytest.raises(NewsPublicationError,match='component_limit'):s.build(claim())


def test_modeled_hole_is_preserved_inside_corridor(tmp_path):
    s=service(tmp_path);hole=box(121.001,14.63005,121.0011,14.6301)
    s.noah=FakeNoah(box(120.99,14.62,121.02,14.64).difference(hole))
    out=s.build(claim())
    assert not shape(out.geometry).covers(hole.centroid)
    assert shape(out.geometry).covers(Point(121.00105,14.63))
