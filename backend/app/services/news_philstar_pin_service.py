"""Explicit developer-reviewed Philstar pins; no inference or universal alias rule."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from typing import Any

from geoalchemy2.shape import from_shape, to_shape
from shapely import set_srid, union_all
from shapely.geometry import LineString, Point, mapping, shape
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.report import FloodAvoidanceZone as Zone, FloodEvent, FloodEventTimelineEntry as Timeline
from app.services.news_ner_durable.contracts import RunEvidence, sha
from app.services.news_philstar_pilot import BODY, DATASET, SESSION, require
from app.services.news_reviewed_corner_service import projected_buffer, name_matches
from app.services.noah_vector_catalog_service import metric_geometry
from app.services.placement_geometry_service import line_parts

VERSION = 'philstar-reviewed-pins-v1'
ENTRY = 'news_philstar_reviewed_pin'
PINS = {
    5: dict(latitude=14.643080, longitude=121.011474, osm_way_id=11435673,
            road='West Riverside Drive', label='West Riverside Interior', reported_barangay='Damayan'),
    7: dict(latitude=14.645922, longitude=121.013534, osm_way_id=11436044,
            road='Attorney Pat Senador Sr. Avenue', label='W Riverside cor Atty Pat Senador', reported_barangay='Del Monte'),
}


def pin_window(db: Any, line: dict, pin: dict) -> dict:
    """Up to 25 m each side of the reviewed pin on its already bounded road block."""
    value=db.scalar(text("""WITH source AS (SELECT ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(:line),4326),32651) g,
        ST_Transform(ST_SetSRID(ST_MakePoint(:lon,:lat),4326),32651) p), located AS
        (SELECT g,ST_LineLocatePoint(g,p)*ST_Length(g) m,ST_Length(g) len FROM source)
        SELECT ST_AsGeoJSON(ST_Transform(ST_LineSubstring(g,GREATEST(0.0,(m-25)/len),
        LEAST(1.0,(m+25)/len)),4326),12) FROM located"""),
        {'line':json.dumps(line),'lon':pin['longitude'],'lat':pin['latitude']})
    require(value is not None,'philstar_pin_window_empty')
    return json.loads(value)


def build_pin(db: Any, claim: Any, ordinal: int, margin: float, service: Any = None) -> dict:
    from app.services.news_placement_preview_service import get_news_placement_preview_service
    from app.services.news_road_placement_service import city_key
    from app.services.operational_footprint_service import validate_operational_shape
    require(ordinal in PINS and 1<=margin<=100,'philstar_pin_scope_invalid')
    service=service or get_news_placement_preview_service()
    pin=PINS[ordinal];roads=service.roads;noah=service.noah
    _=roads.revision  # Load and authenticate the lazy catalog before inspecting ways.
    require(roads.catalog is not None and roads.digest and noah.manifest is not None
        and set(noah.manifest.scenarios)=={5,25,100},'philstar_pin_assets_missing')
    require(claim.canonical_city=='Quezon City' and claim.canonical_barangay==pin['reported_barangay'],
        'philstar_pin_source_locality_changed')
    way=next((w for w in roads.catalog.ways if w.osm_id==pin['osm_way_id']),None)
    require(way is not None and name_matches(way.name,pin['road'])
        and way.bridge in ('','no') and way.tunnel in ('','no') and way.layer in ('','0'),
        'philstar_pin_road_or_grade_changed')
    point=Point(pin['longitude'],pin['latitude']);line=LineString([(n[1],n[2]) for n in way.nodes])
    require(roads.boundaries[city_key('Quezon City')].covers(point),'philstar_pin_outside_city')
    distance=metric_geometry(point).distance(metric_geometry(line))
    require(distance<=15,'philstar_pin_not_on_reviewed_road')
    # Stop at another mapped named-road junction, rather than cutting through it.
    shared={n[0] for other in roads.catalog.ways if other.osm_id!=way.osm_id
        and not name_matches(other.name,pin['road']) for n in other.nodes}
    cuts=sorted({0,len(way.nodes)-1}|{i for i,n in enumerate(way.nodes) if n[0] in shared})
    blocks=[LineString([(n[1],n[2]) for n in way.nodes[a:b+1]]) for a,b in zip(cuts,cuts[1:])]
    nearest=min(metric_geometry(b).distance(metric_geometry(point)) for b in blocks)
    selected=[b for b in blocks if metric_geometry(b).distance(metric_geometry(point))<=nearest+0.01]
    windows=[shape(pin_window(db,mapping(b),pin)) for b in selected]
    measurements=[];pieces=[]
    for window in windows:
        intersections=noah.intersections(window)
        measurements.append({str(period):{str(h):round(metric_geometry(g).length,6) for h,g in classes.items()}
            for period,classes in intersections.items()})
        pieces.extend(part for classes in intersections.values() for g in classes.values() for part in line_parts(g))
    require(bool(pieces),'philstar_pin_no_modeled_road')
    core=union_all(pieces);geometry=projected_buffer(db,mapping(core),margin)
    validation=validate_operational_shape(set_srid(shape(geometry),4326),geometry_srid=4326)
    require(validation.is_eligible,validation.reason_code)
    mapped=sorted(record.barangay for (city,_),(record,boundary) in roads.barangays.records.items()
        if city=='quezon city' and boundary.covers(point))
    evidence=dict(policy_version=VERSION,reviewed_street=pin['road'],reviewed_pin=pin,
        interpretation_basis='developer_supplied_coordinate_and_explicit_plot_instruction',
        reported_barangay=claim.canonical_barangay,mapped_barangays=mapped,
        locality_mismatch=claim.canonical_barangay not in mapped,
        source_junction_confirmed=False,source_depth_applies_to_reported_observation=True,
        pin_distance_to_road_metres=round(distance,3),max_arm_metres=25,buffer_metres=margin,
        component_centerlines=[mapping(core)],osm_way_ids=[way.osm_id],
        osm_catalog_sha256=roads.digest,noah_catalog_sha256=noah.digest,
        noah_source_ids={p:s.source_id for p,s in noah.manifest.scenarios.items()},
        scenario_measurements=measurements,outer_buffer_clipped=False,projection=32651,
        measured_flood_extent=False,proves_current_flood=False,may_affect_routing=False)
    return dict(core=mapping(core),geometry=validation.geojson,geometry_evidence=evidence,label=pin['label'])


def fingerprints(db: Session) -> dict[str,list[str]]:
    from app.services.news_philstar_street_correction import row_fingerprints
    # Normal website visits update this telemetry independently of flood work.
    # Flood/source/user records remain fully bound and must never be excluded.
    return {table:rows for table,rows in row_fingerprints(db).items() if table!='visitor_daily_visits'}


def outputs(engine: Any, authority: Any, run_id: int, sources: tuple, *, apply: bool=False,
            placement_service: Any=None) -> dict:
    from app.services.news_ner_durable.assets import with_resolution_assets
    from app.services.news_ner_durable.adapter import verify_saved_result
    from app.services.news_ner_durable.source_check import check_native_sources
    from app.services.configuration_service import read_configuration
    from app.services.news_publication_service import _operational_zone_attributes
    from app.services.historical_news_metadata import event_metadata, ENTRY as IMPORT
    from app.services.flood_event_service import record_event_locations
    from app.models.report import FloodEventLocationType as Location
    from app.models.news_publication import NewsClaimEvaluation
    from app.services.news_historical_outputs import _source
    from app.services.news_philstar_street_correction import source_excerpt
    p=authority.policy
    with Session(engine) as db,db.begin():
        if not apply:db.execute(text('SET TRANSACTION READ ONLY'))
        else:
            db.execute(text("SET LOCAL lock_timeout='30000'"))
            db.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':int(sha(SESSION)[:15],16)})
            db.execute(text('LOCK TABLE flood_events, flood_avoidance_zones IN SHARE ROW EXCLUSIVE MODE'))
        authority.validate_session(db,(run_id,),sources,operation='outputs')
        require(run_id==401 and p.get('pin_policy')==VERSION
            and p.get('reviewed_pins')=={str(k):v for k,v in PINS.items()},'philstar_pin_authority_changed')
        run=db.get(NewsExtractionRun,401);version=db.get(NewsArticleVersion,run.article_version_id)
        trusted=with_resolution_assets(authority.trusted,p['resolver'])
        result=verify_saved_result(RunEvidence.from_records(run,version),run.result,trusted)
        groups={g['claim_index']:g['group_id'] for g in result.projection['groups'] if g['claim_index'] in PINS}
        require(len(groups)==2 and sorted(groups.values())==p['output_group_ids'],'philstar_pin_groups_changed')
        saved=list(db.scalars(select(Timeline.snapshot_json).where(Timeline.entry_type==ENTRY)))
        if saved:
            require(len(saved)==2 and {v['group_id'] for v in saved}==set(groups.values())
                and all(v['preview_sha256']==p.get('outputs_sha256') and v['result_sha256']==sha(run.result) for v in saved),
                'philstar_pin_saved_receipt_changed')
            return dict(status='completed',stage='reused',outputs=[dict(group_id=v['group_id'],event_id=v['event_id'],zone_ids=[v['zone_id']]) for v in saved],database_writes=0)
        require(sha(fingerprints(db))==p.get('baseline_fingerprints_sha256'),'philstar_pin_database_changed')
        audits=check_native_sources(run,version,run.result,tuple(sorted(PINS)),trusted,now=datetime.fromisoformat(p['previewed_at']))
        margin=read_configuration(db).staff_road_buffer_metres
        require(margin==p['buffer_metres'],'philstar_pin_buffer_changed')
        proposed=[]
        for ordinal in sorted(PINS):
            claim=result.claims[ordinal];audit=audits[ordinal]
            require(audit.outcome=='verified' and claim.condition=='active' and claim.event_time_resolved is not None
                and claim.event_time_resolved.astimezone(timezone.utc).isoformat()=='2026-09-09T08:30:00+00:00',
                'philstar_pin_source_unverified')
            attrs={k:getattr(v,'value',v) for k,v in _operational_zone_attributes(claim,audit).items()}
            proposed.append(dict(claim_index=ordinal,group_id=groups[ordinal],zone_attributes=attrs,
                excerpt=source_excerpt(version.input_snapshot['article_text'],claim),**build_pin(db,claim,ordinal,margin,placement_service)))
        require(not shape(proposed[0]['core']).intersects(shape(proposed[1]['core'])),'philstar_pin_outputs_overlap')
        for item in proposed:
            require(not any(shape(item['core']).intersects(to_shape(z.geometry)) for z in db.scalars(select(Zone).where(Zone.is_active.is_(True)))),
                'philstar_pin_existing_zone_overlap')
        digest=sha(proposed)
        if not apply:return dict(status='completed',stage='preview',outputs=proposed,outputs_sha256=digest,database_writes=0)
        require(digest==p.get('outputs_sha256'),'philstar_pin_preview_changed')
        baseline=fingerprints(db);now=datetime.now(timezone.utc);created=[]
        template=event_metadata(db,[83])[83]
        require(template.dataset_id==DATASET and template.run_id==401,'philstar_pin_history_template_changed')
        for item in proposed:
            ordinal=item['claim_index'];claim=result.claims[ordinal]
            event=FloodEvent(status='active',first_reported_at=claim.event_time_resolved,verified_at=now,
                peak_severity=item['zone_attributes']['severity_override'],peak_depth=claim.depth_canonical)
            db.add(event);db.flush()
            zone=Zone(event_id=event.id,is_active=True,expires_at=None,name=item['label'],admin_notes=item['excerpt'],
                geometry=from_shape(shape(item['geometry']),srid=4326),source_geometry=from_shape(shape(item['core']),srid=4326),**item['zone_attributes'])
            db.add(zone);db.flush()
            record_event_locations(db,event,((Location.ROAD,claim.road_segment_raw),(Location.CITY,claim.canonical_city),(Location.BARANGAY,claim.canonical_barangay)))
            m=template.model_copy(update=dict(observation_key=sha({'session':SESSION,'group':item['group_id']}),
                group_id=item['group_id'],label=item['label'],canonical_road=PINS[ordinal]['road'],
                canonical_barangay=claim.canonical_barangay,source_excerpt=item['excerpt'],observed_at=claim.event_time_resolved,
                geometry_sha256=sha(item['geometry']),imported_at=now))
            db.add(Timeline(event_id=event.id,entry_type=IMPORT,occurred_at=now,summary=item['label'],snapshot_json=m.model_dump(mode='json')))
            receipt=dict(policy_version=VERSION,run_id=401,claim_index=ordinal,group_id=item['group_id'],zone_id=zone.id,event_id=event.id,
                result_sha256=sha(run.result),source_sha256=BODY,preview_sha256=digest,after=item)
            db.add(Timeline(event_id=event.id,entry_type=ENTRY,occurred_at=now,summary=item['label'],snapshot_json=receipt))
            source=_source(db,run,ordinal,claim,now)
            db.add(NewsClaimEvaluation(claim_source_id=source.id,policy_fingerprint=sha({'pin_policy':VERSION,'group':item['group_id']}),
                status='completed',attempt_count=0,result={'schema_version':'reviewed-pin-output-v1','outcome':'geometry_qualified',**receipt},
                created_at=now,updated_at=now,completed_at=now))
            created.append(dict(group_id=item['group_id'],event_id=event.id,zone_ids=[zone.id]))
        db.flush();after=fingerprints(db)
        require(all(not (Counter(rows)-Counter(after[table])) for table,rows in baseline.items()),'philstar_pin_original_rows_changed')
        return dict(status='completed',stage='saved',outputs=created,database_writes=True)
