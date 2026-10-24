"""A matched junction can retain both equally susceptible adjoining sections."""
from types import SimpleNamespace as NS
from copy import deepcopy

import pytest
from shapely.geometry import LineString, box, mapping, shape
from app.crud.news_publication import NewsPublicationError
from app.services.news_junction_estimate_service import matched_junction, build_junction_estimate
from app.services.noah_vector_catalog_service import metric_geometry
from app.services.placement_geometry_service import line_parts


def fixture():
    x,y=121.0,14.6
    claim=NS(road_segment_raw='NS Amoranto cor Palali St.',canonical_road='NS Amoranto',
             canonical_city='Quezon City',canonical_barangay='Sienna')
    lines=[LineString([(x-.001,y),(x,y)]),LineString([(x,y),(x+.001,y)])]
    candidates=[]
    for index,line in enumerate(lines):
        names=[[],['Palali Street']] if index==0 else [['Palali Street'],[]]
        candidates.append(NS(kind='road_section',ambiguous_carriageway=False,
            candidate_id='osm:'+('1-2' if index==0 else '2-3')+':bgy:'+'a'*64,
            centerline_geojson=mapping(line),osm_way_ids=[7],cross_streets=names,
            fragment_status='available',modeled_fragments=[NS(centerline_geojson=mapping(line)) for _ in (5,25,100)],
            modeled_overlap_m={p:{1:0,2:0,3:metric_geometry(line).length} for p in (5,25,100)},
            modeled_overlap_fraction={p:1.0 for p in (5,25,100)},approximate_length_m=metric_geometry(line).length))
    parent=box(x-.01,y-.01,x+.01,y+.01)
    preview=NS(reason='multiple_equally_supported_sections',candidates_truncated=False,uncertainty_reasons=[],
        candidates=candidates,osm_catalog_sha256='a'*64,noah_catalog_sha256='b'*64,noah_source_ids={p:str(p) for p in (5,25,100)})
    noah=NS(manifest=NS(scenarios={p:NS() for p in (5,25,100)},tile_size=.01),_tile=lambda *args:{3:parent})
    service=NS(preview=lambda _:preview,roads=NS(locality_boundary=lambda _:parent,
        boundaries={'quezon city':parent},
        catalog=NS(ways=[NS(osm_id=7,bridge='no',tunnel='no',layer='0')])),noah=noah,revision='fixture')
    return claim,candidates,service


def test_one_junction_not_two_unrelated_locations_and_no_wetter_side_invented():
    claim,candidates,service=fixture();before=deepcopy(candidates)
    point,node=matched_junction(claim,candidates)
    assert node==2 and (point.x,point.y)==(121.0,14.6)
    result=build_junction_estimate(claim,service=service)
    polygon=shape(result.geometry)
    assert polygon.covers(point) and metric_geometry(polygon).area<2000
    assert len(result.evidence['candidate_ids'])==2
    assert result.evidence['measured_flood_extent'] is False
    assert result.evidence['selection_basis']=='same_reported_junction_with_equal_modeled_susceptibility'
    assert all(shape(c).covered_by(polygon) for c in result.evidence['component_centerlines'])
    assert candidates[0].centerline_geojson==before[0].centerline_geojson
    assert build_junction_estimate(claim,service=service).checksum==result.checksum


@pytest.mark.parametrize('case',['third_branch','different_way','wrong_cross_street','different_node','disconnected'])
def test_unrelated_or_incomplete_junction_candidates_remain_unresolved(case):
    claim,candidates,_=fixture()
    if case=='third_branch':candidates.append(deepcopy(candidates[0]))
    if case=='different_way':candidates[1].osm_way_ids=[8]
    if case=='wrong_cross_street':candidates[1].cross_streets[0]=['Other Street']
    if case=='different_node':candidates[1].candidate_id='osm:4-5:bgy:'+'a'*64
    if case=='disconnected':candidates[1].centerline_geojson=mapping(LineString([(121.001,14.6),(121.002,14.6)]))
    with pytest.raises(NewsPublicationError):matched_junction(claim,candidates)


@pytest.mark.parametrize('case',['bridge','scenario_missing','truncated','source_missing','unreported_section'])
def test_asset_grade_and_source_guards(case):
    claim,_,service=fixture()
    if case=='bridge':service.roads.catalog.ways[0].bridge='yes'
    if case=='scenario_missing':service.noah.manifest.scenarios.pop(5)
    if case=='truncated':service.preview(claim).candidates_truncated=True
    if case=='source_missing':service.preview(claim).noah_catalog_sha256=None
    if case=='unreported_section':claim.road_segment_raw='NS Amoranto'
    with pytest.raises(NewsPublicationError):build_junction_estimate(claim,service=service)


def test_noah_gap_remains_dry_and_components_keep_their_source_cores():
    claim,candidates,service=fixture()
    parent=service.roads.boundaries['quezon city']
    gap=box(120.99997,14.599,121.00003,14.601)
    wet=parent.difference(gap)
    service.noah._tile=lambda *args:{3:wet}
    for c in candidates:
        c.modeled_fragments=[NS(centerline_geojson=mapping(p)) for p in line_parts(shape(c.centerline_geojson).intersection(wet))]
    result=build_junction_estimate(claim,service=service)
    assert shape(result.geometry).intersection(gap).area==0
    assert len(result.evidence['component_centerlines'])==2


def test_barangay_disambiguates_junction_without_clipping_the_display_window():
    claim,_,service=fixture()
    service.roads.locality_boundary=lambda _:box(120.999,14.6,121.001,14.601)
    result=build_junction_estimate(claim,service=service)
    assert shape(result.geometry).bounds[1]<14.6
    assert result.evidence['junction_inside_reported_barangay'] is True
    assert result.evidence['administrative_boundaries_clip'] is False
