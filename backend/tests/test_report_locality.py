"""Actual reviewed boundaries, stale geocoder labels and final snapped roads."""
from shapely.geometry import LineString, mapping
from shapely.ops import unary_union
from geoalchemy2.shape import from_shape
import pytest
from sqlalchemy import select

from app.models.audit import AuditLog
from app.services import report_service
from test_operational_settings_postgres import isolated_db, citizen

from app.services.flood_location_service import get_flood_location_provider
from app.services.report_locality_service import pasig_geometry_locality
from app.services.report_locality_service import reconcile_report_locality, snapshot_matches_reconciled_locality
from app.services.flood_followup_service import _location_snapshot
from app.services.geocoding_service import ParsedLocation,_canonical_point_locality
from test_zone_prediction import zone_db


def test_geometry_uses_psgc_identity_for_all_pasig_barangays():
    provider = get_flood_location_provider()
    for record, polygon in provider.records.values():
        p = polygon.representative_point()
        line = LineString([(p.x-.000001,p.y),(p.x+.000001,p.y)])
        result = pasig_geometry_locality(mapping(line))
        assert result['city']=='Pasig' and result['barangay']==record.barangay
        assert result['psgc_codes']==[record.psgc_code]


def test_multibarangay_geometry_does_not_invent_single_locality():
    provider = get_flood_location_provider()
    parts = [p for r,p in provider.records.values() if r.barangay in {'Maybunga','Rosario'}]
    result = pasig_geometry_locality(mapping(unary_union(parts)))
    assert result['city']=='Pasig' and result['barangay'] is None
    assert result['barangays']==['Maybunga','Rosario'] and len(result['psgc_codes'])==2


def test_outside_invalid_and_unknown_geometry_never_gets_pasig_label():
    assert pasig_geometry_locality({'type':'LineString','coordinates':[[120,13],[120.01,13]]}) is None
    assert pasig_geometry_locality(None) is None
    assert pasig_geometry_locality({'type':'Polygon','coordinates':[]}) is None
    assert pasig_geometry_locality(from_shape(LineString([(121.08,14.57),(121.0801,14.57)]),srid=3857)) is None


def test_reverse_geocoder_uses_canonical_psgc_barangay_instead_of_nearby_osm_suburb():
    provider = get_flood_location_provider()
    point = next(p for r,p in provider.records.values() if r.barangay=='Manggahan').representative_point()
    result = _canonical_point_locality(ParsedLocation(street='Known road',city='Pasig City',barangay='Rosario'),point.y,point.x)
    assert result.barangay=='Manggahan' and result.city=='Pasig'
    assert result.display_name=='Known road, Manggahan, Pasig'


@pytest.mark.asyncio
async def test_submission_locality_follows_final_snapped_road_and_preserves_supplied_label(isolated_db,monkeypatch):
    db,staff = isolated_db
    user = citizen(db,staff.role_id)
    provider = get_flood_location_provider()
    polygon = next(p for r,p in provider.records.values() if r.barangay=='Manggahan')
    point = polygon.representative_point()
    road = mapping(LineString([(point.x-.000001,point.y),(point.x+.000001,point.y)]))
    monkeypatch.setattr(report_service,'validate_report_road_geometry',lambda *args:(road,'NARROW_TWO_WAY'))
    report = await report_service.process_new_report(db=db,user_id=user.id,raw_text='Current gutter flood',
        source='direct_user',severity='low',depth='gutter',is_public=False,
        human_readable_location='Submitted road',city='Pasig',barangay='Rosario',geometry=road)
    assert report.city=='Pasig' and report.barangay=='Manggahan'
    audit = db.scalar(select(AuditLog).where(AuditLog.action_type=='CITIZEN_OBSERVATION',AuditLog.target_id==report.id))
    assert audit.metadata_json['submitted_location']['barangay']=='Rosario'
    assert audit.metadata_json['resolved_locality']['barangays']==['Manggahan']
    assert audit.metadata_json['prediction_features']['barangays']==['Manggahan']


def test_existing_label_reconciliation_is_audited_and_does_not_move_source_clock(zone_db):
    db,staff,zone,report,now = zone_db
    report.city,report.barangay = 'Pasig','Rosario'
    db.commit()
    original_clock = report.updated_at
    old_snapshot = _location_snapshot(report)
    metadata = reconcile_report_locality(db,report); db.commit()
    assert report.barangay=='Maybunga' and report.updated_at==original_clock
    assert metadata['before']['barangay']=='Rosario'
    assert metadata['resolved_locality']['psgc_codes']
    assert snapshot_matches_reconciled_locality(db,report,old_snapshot)
    assert not snapshot_matches_reconciled_locality(db,report,{**old_snapshot,'event_id':None})
    assert not snapshot_matches_reconciled_locality(db,report,{**old_snapshot,'geometry_sha256':'0'*64})
    assert reconcile_report_locality(db,report) is None
