"""Conservative citizen-origin archive matching; never updates existing incidents."""
from __future__ import annotations

from datetime import datetime
import re

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import shape
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app import models


def place_key(value: str | None) -> str:
    words = re.sub(r'[^\w]+', ' ', (value or '').casefold()).split()
    return ' '.join(w for w in words if w not in {'city', 'of'})


def citizen_archive_match(db: Session, output: dict, claim: object, *, lock: bool) -> tuple | None:
    from app.services.news_historical_processing import require
    from app.services.citizen_approval_service import observation
    from app.services.news_ner_durable.fields import PHT
    if output['disposition'] != 'historical_archive' or not output.get('geometry'):
        return None
    geometry = shape(output['geometry'])
    event, zone, report = models.FloodEvent, models.FloodAvoidanceZone, models.FloodReport
    # Spatial overlap is only a candidate search, never identity proof.
    candidates = db.execute(select(event, zone, report).join(zone, zone.event_id == event.id)
        .join(report, report.event_id == event.id).where(report.source == models.ReportSource.USER_REPORT,
            report.status == models.ReportStatus.APPROVED, report.deleted_at.is_(None),
            func.ST_Intersects(zone.geometry, from_shape(geometry, srid=4326)))).all()
    time = output['interpretation']['time']
    possible, exact = set(), {}
    for incident, footprint, submission in candidates:
        evidence = observation(db, submission.id)
        raw = evidence.get('observed_at')
        try:
            observed = datetime.fromisoformat(raw) if raw else None
        except (ValueError, TypeError):
            observed = None
        if observed is not None and observed.tzinfo is not None:
            if observed.astimezone(PHT).date().isoformat() != time['occurrence_date']:
                continue
        locations = list(db.scalars(select(models.FloodEventLocation).where(
            models.FloodEventLocation.event_id == incident.id)))
        cities = {place_key(p.display_name) for p in locations if p.location_type == models.FloodEventLocationType.CITY}
        roads = {place_key(p.display_name) for p in locations if p.location_type == models.FloodEventLocationType.ROAD}
        cities.add(place_key(submission.city))
        roads.add(place_key(submission.human_readable_location))
        # A polygon with unknown locality/time still needs review, not a duplicate insertion.
        possible.add((incident.id, footprint.id))
        named = (place_key(claim.canonical_city) in cities and
            place_key(claim.canonical_road or claim.raw_place_name) in roads)
        if (named and observed is not None and observed.tzinfo is not None
                and time['precision'] == 'instant' and time['observed_at']
                and observed == datetime.fromisoformat(time['observed_at'])
                and evidence.get('road_validated') is True
                and incident.status == models.FloodEventStatus.ENDED and not footprint.is_active
                and to_shape(footprint.geometry).equals(geometry)):
            exact[(incident.id, footprint.id)] = (incident, footprint)
    require(not possible or len(possible) == len(exact) == 1, 'historical_existing_match_unresolved')
    if not exact:
        return None
    incident, footprint = next(iter(exact.values()))
    if lock:
        incident = db.scalar(select(event).where(event.id == incident.id).with_for_update())
        footprint = db.scalar(select(zone).where(zone.id == footprint.id).with_for_update())
        require(incident.status == models.FloodEventStatus.ENDED and not footprint.is_active,
            'historical_existing_match_unresolved')
    return incident, footprint
