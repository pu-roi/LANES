from copy import deepcopy
from types import SimpleNamespace
import pytest
from app.crud.news_publication import NewsPublicationError
from app.services.news_presentation_source_facts import source_facts
from app.services.news_gma_active_outputs import DATASET
from app.services.news_ner_durable.contracts import sha

def fixture():
 result={'projection':{'groups':[{'group_id':'resolved-n6','disposition':'projected','claim_index':0}]},
   'claims':[{'depth_raw':'Gutter deep','depth_canonical':'gutter','depth_inches':None,'depth_meters':None,'depth_formatted':None}]}
 run=SimpleNamespace(id=388,status='completed',article_version_id=569,result=result)
 meta=SimpleNamespace(dataset_id=DATASET,run_id=388,result_sha256=sha(result),article_version_id=569,group_id='resolved-n6',label='Rizal Ave Extn',canonical_city='City of Malabon',canonical_barangay='San Agustin')
 db=SimpleNamespace(scalars=lambda _: [run])
 return db,meta,run

def test_gauge_category_does_not_invent_measured_depth():
 db,m,r=fixture();before=deepcopy(r.result);out=source_facts(db,{77:m})[77]
 assert out['depth']=='Gutter deep' and out['depth_formatted']=='Gutter deep'
 assert out['depth_inches'] is None and out['depth_meters'] is None
 assert 'San Agustin' in out['location_label'] and r.result==before

def test_unrelated_metadata_never_queries_or_changes_legacy_values():
 db,m,_=fixture();m.dataset_id='older-history'
 db.scalars=lambda _:pytest.fail('unrelated_source_query')
 assert source_facts(db,{76:m})=={}


def test_response_revalidation_cannot_refill_unknown_source_measurements():
    from pydantic import TypeAdapter
    from app.schemas.report import FloodAvoidanceZoneResponse
    value=FloodAvoidanceZoneResponse.model_construct(id=77,depth='Gutter deep',depth_override='gutter',
        depth_inches=None,depth_meters=None,depth_formatted='Gutter deep',
        historical=SimpleNamespace(dataset_id=DATASET))
    projected=TypeAdapter(FloodAvoidanceZoneResponse).validate_python(value)
    assert projected.depth_inches is None and projected.depth_meters is None
    assert projected.depth_formatted=='Gutter deep'


def test_ordinary_zone_gauge_conversion_remains_unchanged():
    from pydantic import TypeAdapter
    from app.schemas.report import FloodAvoidanceZoneResponse
    value=FloodAvoidanceZoneResponse.model_construct(id=76,depth='gutter',depth_override='gutter',
        depth_inches=None,depth_meters=None,depth_formatted=None,historical=None)
    projected=TypeAdapter(FloodAvoidanceZoneResponse).validate_python(value)
    assert projected.depth_inches==8 and projected.depth_meters==.2

@pytest.mark.parametrize('change',['hash','version','status','group'])
def test_mismatched_evidence_fails_visibly(change):
 db,m,r=fixture()
 if change=='hash':m.result_sha256='0'*64
 if change=='version':m.article_version_id=574
 if change=='status':r.status='failed'
 if change=='group':m.group_id='other'
 with pytest.raises(NewsPublicationError):source_facts(db,{77:m})
