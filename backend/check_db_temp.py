import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.report import FloodAvoidanceZone

db = SessionLocal()
try:
    zones = db.query(FloodAvoidanceZone).order_by(FloodAvoidanceZone.id.desc()).limit(5).all()
    if not zones:
        print("No flood avoidance zones found in the database.")
    for z in zones:
        print(f"Zone ID: {z.id} | Report ID: {z.report_id} | Active: {z.is_active} | Expires: {z.expires_at}")
finally:
    db.close()
