from copy import deepcopy
from types import SimpleNamespace

import pytest

from app.schemas.news_presentation import NewsFloodSummary
from app.schemas.news_results import NewsResultClaim
from app.schemas.news_ner_result import NerProjectedClaim
from app.services.news_verification_presentation import with_verification, detail_with_verification


def summary():
    return NewsFloodSummary(location='Reported road',area='Quezon City',location_qualifier=None,
        water_level='19 inches, knee deep',condition='Flooding reported',flood_time=None,
        flood_time_label='Flood time in article',map_status='Exact map location unknown',
        reading_status='reported_location',reading_reason=None)


def claim():
    return dict(raw_place_name='Brgy. Damayan',canonical_city='Quezon City',canonical_barangay='Damayan',
        canonical_road=None,road_segment_raw='West Riverside Interior',depth_raw='19 inches, knee deep',
        depth_formatted=None,condition='active',event_time_resolved='2026-09-09T08:30:00Z',
        event_time_kind='observation',evidence_sentence='Flooding reported at West Riverside Interior.',
        uncertainty_reasons=[],road_placement={'status':'unresolved','reason':'no_reported_road'})


def by_field(value):
    return {i.field:i for i in value.verification_issues}


def test_known_depth_is_not_flagged_when_street_is_missing_and_inputs_stay_immutable():
    raw=claim();before=deepcopy(raw);original=summary()
    value=with_verification(original,raw)
    assert set(by_field(value))=={'location','road'}
    assert by_field(value)['road'].state=='missing'
    assert raw==before and original.verification_status=='not_assessed'
    assert value.water_level==original.water_level


@pytest.mark.parametrize('raw_place,place_type,expected_road',[
    ('Talipapa Alley','street',True),('Maybunga','barangay',False),('Sample Mall','landmark',False)])
def test_road_requirement_distinguishes_streets_from_legitimate_broad_places(raw_place,place_type,expected_road):
    raw={**claim(),'raw_place_name':raw_place,'place_type':place_type,'road_segment_raw':None}
    assert ('road' in by_field(with_verification(summary(),raw))) is expected_road


def test_missing_depth_and_time_do_not_inherit_hazard_or_publication_values():
    raw={**claim(),'depth_raw':None,'depth_formatted':None,'depth_canonical':'waist',
         'event_time_resolved':None,'published_at':'2026-09-09T09:03:00Z'}
    issues=by_field(with_verification(summary(),raw))
    assert issues['water_level'].code=='depth_missing'
    assert issues['flood_time'].code=='flood_time_missing'


@pytest.mark.parametrize('change,code,state',[
    ({'audit_result':{'depth_discrepancy_note':'conflicting measurements'}},'depth_conflict','conflicting'),
    ({'audit_result':{'independent_audit':{'evidence':{'depth':{'confirmed':False}}}}},'depth_unconfirmed','uncertain'),
    ({'uncertainty_reasons':['depth_scalar_not_supported']},'depth_unconfirmed','uncertain')])
def test_depth_source_failures_have_field_specific_reasons(change,code,state):
    issue=by_field(with_verification(summary(),{**claim(),**change}))['water_level']
    assert (issue.code,issue.state)==(code,state)


def test_qualitative_depth_is_reported_without_inventing_measurements_or_duplicate_depth_badges():
    raw={**claim(),'depth_raw':'waist-deep','depth_formatted':None}
    assert 'water_level' not in by_field(with_verification(summary(),raw))
    value=with_verification(summary(),raw,depth_scope='shared')
    assert [i.field for i in value.verification_issues].count('water_level')==1
    assert by_field(value)['water_level'].code=='shared_depth'


def test_normalized_depth_alone_does_not_appear_source_verified():
    value=with_verification(summary(),{**claim(),'depth_raw':None,'depth_formatted':'Waist (0.94 m)'})
    assert by_field(value)['water_level'].code=='depth_wording_missing'


def test_saved_estimated_zone_is_not_presented_as_unplotted_or_field_verified():
    raw={**claim(),'canonical_road':'Palali Street','road_placement':{'status':'ambiguous','reason':'two_arms'}}
    value=with_verification(summary(),raw,estimated_placement=True)
    assert value.placement_is_estimate and 'plotted' in value.map_status
    assert by_field(value)['location'].code=='estimated_extent'
    assert value.verification_status=='needs_verification'
    assert 'road' not in by_field(value)
    assert with_verification(value,raw)==value


def test_source_capture_mismatch_and_condition_are_independent_of_depth():
    value=with_verification(summary(),{**claim(),'condition':'unknown'},source_state='different_capture')
    assert by_field(value)['source'].state=='conflicting'
    assert by_field(value)['condition'].code=='condition_unclear'
    assert 'water_level' not in by_field(value)


def test_native_details_recover_road_phrase_omitted_by_lightweight_claim_contract():
    raw={**claim(),'place_char_start':0,'place_char_end':13,'evidence_sentence_offset':(0,65)}
    full=NerProjectedClaim.model_validate(raw)
    lightweight=NewsResultClaim.model_validate(raw)
    class Copyable(SimpleNamespace):
        def model_copy(self,*,update):
            return Copyable(**{**self.__dict__,**update})
    item=Copyable(claim_index=0,summary=summary())
    detail=Copyable(item=item,claim=lightweight,result=Copyable(claims=[full]),source_review=None,depth_scope='individual')
    value=detail_with_verification(detail)
    assert by_field(value.item.summary)['road'].code=='road_unresolved'
    assert detail.item.summary.verification_status=='not_assessed'
    assert full.road_segment_raw=='West Riverside Interior'
