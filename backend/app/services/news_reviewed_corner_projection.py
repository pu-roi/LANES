"""Saved placement correction projection; original extraction remains immutable."""
from __future__ import annotations

from copy import deepcopy
from typing import Any
from sqlalchemy import select
from app.models.report import FloodEventTimelineEntry as Timeline
from app.services.news_philstar_street_correction import ENTRY, CORRECTION
from app.services.news_reviewed_corner_service import STREETS
from app.services.news_philstar_pilot import BODY
from app.services.news_saved_run_service import SavedRunReadError


def corrected_rows(db: Any, rows: list[dict]) -> list[dict]:
    groups={r['group_id'] for r in rows if r.get('run_id')==401 and r.get('group_id')}
    if not groups:
        return rows
    saved=list(db.scalars(select(Timeline.snapshot_json).where(Timeline.entry_type==ENTRY,
        Timeline.snapshot_json['correction_id'].as_string()==CORRECTION,
        Timeline.snapshot_json['group_id'].as_string().in_(groups)).order_by(Timeline.id)))
    by_group={r['group_id']:r for r in saved}
    from app.services.news_philstar_pin_service import ENTRY as PIN_ENTRY, VERSION as PIN_VERSION, PINS
    pin_receipts=list(db.scalars(select(Timeline.snapshot_json).where(Timeline.entry_type==PIN_ENTRY,
        Timeline.snapshot_json['policy_version'].as_string()==PIN_VERSION,
        Timeline.snapshot_json['group_id'].as_string().in_(groups)).order_by(Timeline.id)))
    pin_groups={r['group_id']:r for r in pin_receipts if r.get('policy_version')==PIN_VERSION}
    result=[]
    for row in rows:
        value=by_group.get(row.get('group_id')) if row.get('run_id')==401 else None
        pin_value=pin_groups.get(row.get('group_id')) if row.get('run_id')==401 else None
        if pin_value:
            ordinal=row['claim_index'];item=pin_value['after']
            if (ordinal not in PINS or pin_value.get('run_id')!=401 or pin_value.get('source_sha256')!=BODY
                    or pin_value.get('claim_index')!=ordinal or item.get('claim_index')!=ordinal
                    or item.get('geometry_evidence',{}).get('reviewed_pin')!=PINS[ordinal]):
                raise SavedRunReadError('news_reviewed_pin_invalid')
            row={**row,'claim':deepcopy(row['claim']),'_reviewed_placement_saved':True}
            row['claim'].update(canonical_road=PINS[ordinal]['road'],raw_place_name=PINS[ordinal]['road'],
                road_segment_raw=item['label'],evidence_sentence=item['excerpt'])
        if value:
            ordinal=row['claim_index'];item=value.get('after',{})
            if (ordinal not in STREETS or value.get('run_id')!=401 or value.get('claim_index')!=ordinal
                    or value.get('source_sha256')!=BODY or item.get('claim_index')!=ordinal
                    or item.get('geometry_evidence',{}).get('reviewed_street')!=STREETS[ordinal][0]):
                raise SavedRunReadError('news_reviewed_placement_invalid')
            row={**row,'claim':deepcopy(row['claim']),'_reviewed_placement_saved':True}
            row['claim'].update(canonical_road=STREETS[ordinal][0],raw_place_name=STREETS[ordinal][0],
                road_segment_raw=item['label'],evidence_sentence=item['excerpt'])
        result.append(row)
    return result


def corrected_detail(db: Any, detail: Any) -> Any:
    if detail.item.run_id!=401 or not getattr(detail.item,'group_id',None):
        return detail
    original=detail.item.claim.model_dump(mode='json')
    row=corrected_rows(db,[dict(run_id=401,group_id=detail.item.group_id,
        claim_index=detail.item.claim_index,claim=original)])[0]
    if row['claim']==original:
        return detail
    projected=type(detail.item.claim).model_validate(row['claim'])
    summary=detail.item.summary.model_copy(update={'location':row['claim']['road_segment_raw'],
        'placement_is_estimate':True,'map_status':'Estimated zone plotted; exact flood extent needs verification'})
    item=detail.item.model_copy(update={'claim':projected,'summary':summary})
    return detail.model_copy(update={'item':item,'claim':projected})


def saved_corner_preview(db: Any, run_id: int, ordinal: int) -> Any:
    """Map handoffs use the saved reviewed core/aura, never the old road role."""
    from app.services.news_philstar_pin_service import PINS, ENTRY as PIN_ENTRY, VERSION as PIN_VERSION
    if run_id!=401 or ordinal not in set(STREETS)|set(PINS):
        return None
    if ordinal in PINS:
        values=list(db.scalars(select(Timeline.snapshot_json).where(Timeline.entry_type==PIN_ENTRY,
            Timeline.snapshot_json['policy_version'].as_string()==PIN_VERSION,
            Timeline.snapshot_json['claim_index'].as_integer()==ordinal).order_by(Timeline.id)))
        if not values:return None
        value=values[-1];item=value['after'];evidence=item['geometry_evidence']
        if value.get('source_sha256')!=BODY or value.get('run_id')!=401 or evidence.get('reviewed_pin')!=PINS[ordinal]:
            raise SavedRunReadError('news_reviewed_pin_invalid')
        return placement_from_saved(item,ordinal,PINS[ordinal]['road'],[],PIN_VERSION,'saved_developer_reviewed_pin_estimate')
    values=list(db.scalars(select(Timeline.snapshot_json).where(Timeline.entry_type==ENTRY,
        Timeline.snapshot_json['correction_id'].as_string()==CORRECTION,
        Timeline.snapshot_json['claim_index'].as_integer()==ordinal).order_by(Timeline.id)))
    if not values:
        return None
    value=values[-1];item=value['after'];evidence=item['geometry_evidence']
    if value.get('run_id')!=run_id or value.get('source_sha256')!=BODY or evidence['reviewed_street']!=STREETS[ordinal][0]:
        raise SavedRunReadError('news_reviewed_placement_invalid')
    return placement_from_saved(item,ordinal,STREETS[ordinal][0],[STREETS[ordinal][1]],CORRECTION,'saved_developer_reviewed_corner_estimate')


def placement_from_saved(item: dict, ordinal: int, road: str, references: list[str], revision: str, reason: str) -> Any:
    evidence=item['geometry_evidence']
    from app.schemas.news_placement import NewsPlacementPreview,PlacementSection,PlacementDisplaySection,PlacementDisplayZone
    from app.services.news_ner_durable.contracts import sha
    from shapely.geometry import shape
    from app.services.noah_vector_catalog_service import metric_geometry
    identity='reviewed-corner:'+sha(item['group_id'])[:24] if item.get('group_id') else 'reviewed-corner:'+str(ordinal)
    section=PlacementSection(candidate_id=identity,kind='road_section',centerline_geojson=item['core'],
        osm_way_ids=evidence.get('osm_way_ids',[]),cross_streets=[references,[]],ambiguous_carriageway=False,
        article_place_level=2,approximate_length_m=metric_geometry(shape(item['core'])).length,
        preview_geometry=item['core'],fragment_status='available')
    preview=NewsPlacementPreview(status='predicted_candidate',reason=reason,
        selected_candidate_id=identity,placement_kind='predicted',candidates=[section],total_candidate_count=1,
        display_sections=[PlacementDisplaySection(display_id=identity,candidate_ids=[identity],geometry=item['core'])],
        display_zone=PlacementDisplayZone(candidate_ids=[identity],core_geometry=item['core'],aura_geometry=item['geometry']),
        osm_catalog_sha256=evidence['osm_catalog_sha256'],noah_catalog_sha256=evidence['noah_catalog_sha256'],
        noah_source_ids=evidence['noah_source_ids'])
    return dict(preview=preview,revision=revision,road=road,label=item['label'],excerpt=item['excerpt'])
