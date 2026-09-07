import asyncio
import json
import httpx
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.report import FloodReport, ReportStatus

from app.core.database import SessionLocal

async def fix_reports():
    db = SessionLocal()
    reports = db.query(FloodReport).filter(FloodReport.status == ReportStatus.APPROVED).all()
    
    async with httpx.AsyncClient() as client:
        for r in reports:
            if (not r.barangay or not r.human_readable_location) and r.geometry:
                from app.schemas.report import FloodReportResponse
                response_report = FloodReportResponse.model_validate(r)
                if not response_report.geometry:
                    continue
                coords = response_report.geometry.coordinates
                if response_report.geometry.type == 'Point':
                    lon, lat = coords[0], coords[1]
                elif response_report.geometry.type == 'LineString':
                    lon, lat = coords[0][0], coords[0][1]
                else:
                    continue
                
                print(f"Fixing report {r.id} at {lat}, {lon}...")
                
                url = "https://nominatim.openstreetmap.org/reverse"
                params = {
                    "lat": lat,
                    "lon": lon,
                    "format": "json",
                    "zoom": 16  # Major streets/suburbs level
                }
                headers = {
                    "User-Agent": "LANES-Flood-Mapping-App/1.0 (lanes@example.com)"
                }
                
                try:
                    resp = await client.get(url, params=params, headers=headers, timeout=10.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        print(f"Data received: {data}")
                        if "display_name" in data:
                            address = data.get("address", {})
                            barangay = address.get("village") or address.get("suburb") or address.get("neighbourhood") or address.get("quarter")
                            if not barangay:
                                barangay = address.get("city") or "Unknown Barangay"
                            
                            hr_loc = data["display_name"]
                            r.barangay = barangay
                            r.human_readable_location = hr_loc
                            db.commit()
                            print(f"  -> Updated: {hr_loc} (Barangay: {barangay})")
                        else:
                            print("No display_name in data!")
                    else:
                        print(f"Failed with status {resp.status_code}")
                except Exception as e:
                    print(f"  -> Failed exception: {e}")

if __name__ == "__main__":
    asyncio.run(fix_reports())
