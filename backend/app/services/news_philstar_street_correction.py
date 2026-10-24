"""Atomic source-bound correction of reviewed Philstar corners, no generation."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import mapping, shape
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.report import FloodAvoidanceZone as Zone, FloodEvent, FloodEventTimelineEntry as Timeline
from app.services.news_ner_durable.contracts import RunEvidence, sha
from app.services.news_philstar_pilot import SESSION, DATASET, require
from app.services.news_reviewed_corner_service import VERSION, STREETS, EXISTING, build_reviewed_corner

ENTRY = 'news_philstar_street_correction'
CORRECTION = VERSION + ':20261024'


def row_fingerprints(db: Session, *, exclude_reviewed: bool = False) -> dict[str,list[str]]:
    tables = list(db.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")))
    result = {}
    for table in tables:
        quoted = db.get_bind().dialect.identifier_preparer.quote(table)
        where = ' WHERE id NOT IN (83,84,85,88,89)' if exclude_reviewed and table == 'flood_avoidance_zones' else ''
        result[table] = sorted(db.scalars(text('SELECT md5(to_jsonb(t)::text) FROM '+quoted+' t'+where)))
    return result


def source_excerpt(body: str, claim: Any) -> str:
    rows = [line.strip() for line in body.splitlines() if claim.road_segment_raw in line
            and (claim.depth_raw or '') in line]
    require(len(rows) == 1, 'philstar_correction_excerpt_ambiguous')
    return rows[0]


def saved_corrections(db: Session, run_id: int, groups: list[str]) -> dict[str,dict]:
    rows = db.scalars(select(Timeline).where(Timeline.entry_type == ENTRY,
        Timeline.snapshot_json['correction_id'].as_string() == CORRECTION,
        Timeline.snapshot_json['run_id'].as_integer() == run_id).order_by(Timeline.id))
    return {r.snapshot_json['group_id']:r.snapshot_json for r in rows if r.snapshot_json['group_id'] in groups}


def outputs(engine: Any, authority: Any, run_id: int, sources: tuple, *, apply: bool = False,
            placement_service: Any = None) -> dict:
    from app.services.news_ner_durable.assets import with_resolution_assets
    from app.services.news_ner_durable.adapter import verify_saved_result
    from app.services.news_ner_durable.source_check import check_native_sources
    from app.services.configuration_service import read_configuration
    from app.services.news_publication_service import _operational_zone_attributes
    from app.services.historical_news_metadata import event_metadata, ENTRY as IMPORT
    from app.models.report import FloodEventLocationType as Location
    from app.services.flood_event_service import record_event_locations
    from app.models.news_publication import NewsClaimEvaluation
    from app.services.news_historical_outputs import _source
    p = authority.policy
    with Session(engine) as db, db.begin():
        if not apply:
            db.execute(text('SET TRANSACTION READ ONLY'))
        else:
            db.execute(text("SET LOCAL lock_timeout='30000'"))
            db.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':int(sha(SESSION)[:15],16)})
            db.execute(text('LOCK TABLE flood_events, flood_avoidance_zones IN SHARE ROW EXCLUSIVE MODE'))
        authority.validate_session(db,(run_id,),sources,operation='outputs')
        require(run_id == 401 and p.get('street_correction') == VERSION
            and p.get('correction_claims') == sorted(STREETS)
            and p.get('reviewed_street_roles') == {str(k):list(v) for k,v in STREETS.items()},
            'philstar_correction_scope_invalid')
        run=db.get(NewsExtractionRun,run_id);version=db.get(NewsArticleVersion,run.article_version_id)
        trusted=with_resolution_assets(authority.trusted,p['resolver'])
        result=verify_saved_result(RunEvidence.from_records(run,version),run.result,trusted)
        groups={g['claim_index']:g['group_id'] for g in result.projection['groups']
                if g['claim_index'] in STREETS}
        require(len(groups)==len(STREETS) and sorted(groups.values())==p['output_group_ids'],
            'philstar_correction_groups_changed')
        saved=saved_corrections(db,run_id,p['output_group_ids'])
        if saved:
            require(len(saved)==len(STREETS) and all(v['preview_sha256']==p.get('outputs_sha256')
                for v in saved.values()),'philstar_correction_receipt_changed')
            return dict(status='completed',stage='reused',event_ids=sorted(v['event_id'] for v in saved.values()),database_writes=0)
        # All five existing instances are source-owned; never target arbitrary IDs.
        existing={i:db.get(Zone,z) for i,z in EXISTING.items()}
        metadata=event_metadata(db,[z.event_id for z in existing.values() if z is not None])
        zone_hashes={str(z):db.scalar(text('SELECT md5(to_jsonb(t)::text) FROM flood_avoidance_zones t WHERE id=:id'),{'id':z})
                     for z in EXISTING.values()}
        require(zone_hashes==p.get('expected_zone_fingerprints'),'philstar_correction_zone_changed')
        for ordinal,zone in existing.items():
            m=metadata.get(zone.event_id) if zone else None
            require(m is not None and m.dataset_id==DATASET and m.run_id==401 and m.group_id==groups[ordinal]
                and m.result_sha256==sha(run.result),'philstar_correction_existing_lineage_changed')
        audits=check_native_sources(run,version,run.result,tuple(sorted(STREETS)),trusted,
            now=datetime.fromisoformat(p['previewed_at']))
        margin=read_configuration(db).staff_road_buffer_metres
        require(margin==p.get('buffer_metres'),'philstar_correction_buffer_changed')
        proposed=[]
        for ordinal in sorted(STREETS):
            claim=result.claims[ordinal];audit=audits[ordinal]
            require(claim.condition=='active' and not claim.is_forecast and not claim.is_negated
                and audit.outcome=='verified' and claim.event_time_resolved is not None
                and claim.event_time_resolved.astimezone(timezone.utc).isoformat()=='2026-09-09T08:30:00+00:00',
                'philstar_correction_source_unverified')
            attributes={k:getattr(v,'value',v) for k,v in _operational_zone_attributes(claim,audit).items()}
            corner=build_reviewed_corner(db,claim,ordinal,margin,placement_service)
            zone=existing.get(ordinal)
            if zone:
                require(all(getattr(getattr(zone,k),'value',getattr(zone,k))==v for k,v in attributes.items()),
                    'philstar_correction_facts_changed')
            proposed.append(dict(claim_index=ordinal,group_id=groups[ordinal],zone_id=zone.id if zone else None,
                event_id=zone.event_id if zone else None,zone_attributes=attributes,
                excerpt=source_excerpt(version.input_snapshot['article_text'],claim),**corner))
        # Core overlap is the relevant ambiguity test. Display halos may overlap.
        for index,left in enumerate(proposed):
            for right in proposed[index+1:]:
                require(not shape(left['core']).intersects(shape(right['core'])),
                    'philstar_correction_source_cores_overlap')
        others=list(db.scalars(select(Zone).where(Zone.is_active.is_(True),Zone.id.not_in(EXISTING.values()))))
        for item in proposed:
            for zone in others:
                require(not shape(item['core']).intersects(to_shape(zone.geometry)),
                    'philstar_correction_unrelated_zone_overlap')
        digest=sha(proposed)
        if not apply:
            return dict(status='completed',stage='preview',outputs=proposed,outputs_sha256=digest,database_writes=0)
        require(digest==p.get('outputs_sha256'),'philstar_correction_preview_changed')
        before=row_fingerprints(db,exclude_reviewed=True);now=datetime.now(timezone.utc);created=[]
        template=next(iter(metadata.values()))
        for item in proposed:
            ordinal=item['claim_index'];claim=result.claims[ordinal];zone=existing.get(ordinal)
            old=None
            if zone:
                old=dict(geometry=mapping(to_shape(zone.geometry)),core=mapping(to_shape(zone.source_geometry)),
                    name=zone.name,admin_notes=zone.admin_notes,is_active=zone.is_active,
                    updated_at=zone.updated_at.isoformat())
                m=metadata[zone.event_id]
            else:
                # No prior output for a supposedly missing observation may be replaced.
                require(not db.scalar(select(Timeline.id).where(Timeline.entry_type=='news_philstar_pilot_output',
                    Timeline.snapshot_json['group_id'].as_string()==item['group_id'])),
                    'philstar_correction_missing_output_exists')
                event=FloodEvent(status='active',first_reported_at=claim.event_time_resolved,verified_at=now,
                    peak_severity=item['zone_attributes']['severity_override'],peak_depth=claim.depth_canonical)
                db.add(event);db.flush()
                zone=Zone(event_id=event.id,is_active=True,expires_at=None,name=item['label'],
                    geometry=from_shape(shape(item['geometry']),srid=4326),
                    source_geometry=from_shape(shape(item['core']),srid=4326),**item['zone_attributes'])
                db.add(zone);db.flush()
                record_event_locations(db,event,((Location.ROAD,claim.road_segment_raw),
                    (Location.CITY,claim.canonical_city),(Location.BARANGAY,claim.canonical_barangay)))
                m=template.model_copy(update={'observation_key':sha({'session':SESSION,'group':item['group_id']}),
                    'group_id':item['group_id'],'observed_at':claim.event_time_resolved})
            zone.name=item['label'];zone.admin_notes=item['excerpt'];zone.updated_at=now
            zone.geometry=from_shape(shape(item['geometry']),srid=4326)
            zone.source_geometry=from_shape(shape(item['core']),srid=4326)
            revised=m.model_copy(update={'label':item['label'],'canonical_road':STREETS[ordinal][0],
                'source_excerpt':item['excerpt'],'geometry_sha256':sha(item['geometry']),'imported_at':now})
            db.add(Timeline(event_id=zone.event_id,entry_type=IMPORT,occurred_at=now,summary=revised.label,
                snapshot_json=revised.model_dump(mode='json')))
            receipt=dict(correction_id=CORRECTION,run_id=401,group_id=item['group_id'],claim_index=ordinal,
                event_id=zone.event_id,zone_id=zone.id,before=old,after=item,preview_sha256=digest,
                result_sha256=sha(run.result),source_sha256=p['inputs'][0]['body_sha256'])
            db.add(Timeline(event_id=zone.event_id,entry_type=ENTRY,occurred_at=now,
                summary=item['label'],snapshot_json=receipt))
            source=_source(db,run,ordinal,claim,now)
            db.add(NewsClaimEvaluation(claim_source_id=source.id,policy_fingerprint=sha({'correction':CORRECTION,'group':item['group_id']}),
                status='completed',attempt_count=0,result={'schema_version':'reviewed-street-correction-output-v1',
                    'group_id':item['group_id'],'outcome':'geometry_qualified',**receipt},
                created_at=now,updated_at=now,completed_at=now))
            created.append(dict(group_id=item['group_id'],zone_ids=[zone.id],event_id=zone.event_id))
        db.flush()
        after=row_fingerprints(db,exclude_reviewed=True)
        require(all(not (Counter(rows)-Counter(after[table])) for table,rows in before.items()),
            'philstar_correction_unrelated_rows_changed')
        return dict(status='completed',stage='saved',outputs=created,database_writes=True)
