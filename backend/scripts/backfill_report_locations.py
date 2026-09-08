import asyncio
import json
import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.report import FloodReport
from app.services.geocoding_service import reverse_geocode_structured
from app.services.report_service import extract_representative_coordinates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backfill")


async def backfill_reports():
    db = SessionLocal()
    try:
        # Find reports that have geometry but lack street, barangay, or city
        reports = db.query(FloodReport).filter(
            FloodReport.geometry.isnot(None),
            FloodReport.deleted_at.is_(None)
        ).all()

        logger.info(f"Found {len(reports)} total active flood reports with geometry.")
        updated_count = 0

        for r in reports:
            needs_update = not r.barangay or not r.city or not r.human_readable_location
            if not needs_update:
                continue

            geojson_str = db.scalar(func.ST_AsGeoJSON(r.geometry))
            if not geojson_str:
                continue

            try:
                geom_dict = json.loads(geojson_str)
                coords = extract_representative_coordinates(geom_dict)
                if not coords:
                    continue

                lat, lng = coords
                logger.info(f"Reverse geocoding report #{r.id} at ({lat}, {lng})...")
                parsed = await reverse_geocode_structured(lat, lng)
                if parsed:
                    if not r.human_readable_location:
                        r.human_readable_location = parsed.street or parsed.display_name
                    if not r.barangay and parsed.barangay:
                        r.barangay = parsed.barangay
                    if not r.city and parsed.city:
                        r.city = parsed.city

                    db.commit()
                    updated_count += 1
                    logger.info(
                        f"  -> Updated report #{r.id}: street='{r.human_readable_location}', "
                        f"barangay='{r.barangay}', city='{r.city}'"
                    )
            except Exception as e:
                logger.error(f"Failed to backfill report #{r.id}: {e}")

            # Politeness delay between external geocoding requests
            await asyncio.sleep(0.3)

        logger.info(f"Backfill complete! Updated {updated_count} flood reports.")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(backfill_reports())
