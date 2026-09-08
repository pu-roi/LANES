import asyncio
import json
import httpx
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.report import FloodReport, ReportStatus

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/lanes_db"  # Check .env if needed
# Actually we can just use SessionLocal
from app.core.database import SessionLocal

async def fix_reports():
    db = SessionLocal()
    reports = db.query(FloodReport).filter(FloodReport.status == ReportStatus.APPROVED).all()
    
    async with httpx.AsyncClient() as client:
        for r in reports:
            if (not r.barangay or not r.human_readable_location) and r.geometry:
                # Get coords
                # r.geometry is a WKBElement. We can get it via db.scalar(func.ST_AsGeoJSON(r.geometry))
                from sqlalchemy import func
                geojson_str = db.scalar(func.ST_AsGeoJSON(r.geometry))
                if not geojson_str:
                    continue
                geom = json.loads(geojson_str)
                if geom['type'] == 'Point':
                    lon, lat = geom['coordinates'][0], geom['coordinates'][1]
                elif geom['type'] == 'LineString':
                    lon, lat = geom['coordinates'][0][0], geom['coordinates'][0][1]
                else:
                    continue
                
                print(f"Fixing report {r.id} at {lat}, {lon}...")
                
                # Photon API
                url = f"https://photon.komoot.io/reverse?lon={lon}&lat={lat}"
                try:
                    resp = await client.get(url, timeout=10.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        features = data.get("features", [])
                        if features:
                            props = features[0].get("properties", {})
                            barangay = props.get("district") or props.get("locality") or props.get("city")
                            
                            # Construct human readable
                            parts = []
                            if props.get("name"): parts.append(props["name"])
                            elif props.get("street"): parts.append(props["street"])
                            if barangay: parts.append(barangay)
                            hr_loc = ", ".join(parts) if parts else (props.get("city") or "Unknown Location")
                            
                            r.barangay = barangay
                            r.human_readable_location = hr_loc
                            db.commit()
                            print(f"  -> Updated: {hr_loc} (Barangay: {barangay})")
                except Exception as e:
                    print(f"  -> Failed: {e}")

if __name__ == "__main__":
    asyncio.run(fix_reports())
