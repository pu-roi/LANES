import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.report import FloodReport, FloodReportLocation, FloodReportSurvey
from app.models.user import User

def duplicate_reports():
    with SessionLocal() as session:
        # Find the two users
        users = session.query(User).filter(User.username.in_(['roicambe', 'roicambe02'])).all()
        user_map = {u.username: u.id for u in users}
        
        if len(users) < 2:
            print("Could not find both users 'roicambe' and 'roicambe02'.")
            return
            
        print(f"User IDs: roicambe={user_map['roicambe']}, roicambe02={user_map['roicambe02']}")

        # Fetch their reports
        reports = session.query(FloodReport).filter(FloodReport.user_id.in_([u.id for u in users])).all()
        
        print(f"Found {len(reports)} reports.")
        
        roicambe_reports = [r for r in reports if r.user_id == user_map['roicambe']]
        roicambe02_reports = [r for r in reports if r.user_id == user_map['roicambe02']]
        
        if not roicambe_reports or not roicambe02_reports:
            print("Both users need at least one report to duplicate. Please check the DB.")
            return
            
        # For simplicity, just take the first report of each user
        r1 = roicambe_reports[0]
        r2 = roicambe02_reports[0]
        
        # Function to duplicate a report and assign to a new user
        def copy_report(original_report, new_user_id):
            new_report = FloodReport(
                user_id=new_user_id,
                source=original_report.source,
                severity=original_report.severity,
                depth=original_report.depth,
                is_public=original_report.is_public,
                status=original_report.status,
                raw_text=original_report.raw_text,
                geometry=original_report.geometry  # direct copy of geometry
            )
            session.add(new_report)
            return new_report
            
        # Duplicate R2 for roicambe
        new_r2_for_roicambe = copy_report(r2, user_map['roicambe'])
        # Duplicate R1 for roicambe02
        new_r1_for_roicambe02 = copy_report(r1, user_map['roicambe02'])
        
        session.flush() # flush to get IDs
        
        # Copy locations and surveys
        for orig, new_rep in [(r2, new_r2_for_roicambe), (r1, new_r1_for_roicambe02)]:
            for loc in orig.locations:
                new_loc = FloodReportLocation(
                    report_id=new_rep.id,
                    point_type=loc.point_type,
                    address=loc.address,
                    coordinates=loc.coordinates
                )
                session.add(new_loc)
                
            if orig.survey:
                new_survey = FloodReportSurvey(
                    report_id=new_rep.id,
                    passable_vehicles=orig.survey.passable_vehicles[:] if isinstance(orig.survey.passable_vehicles, list) else orig.survey.passable_vehicles,
                    hidden_hazards=orig.survey.hidden_hazards
                )
                session.add(new_survey)
                
        session.commit()
        print("Successfully duplicated the reports!")

if __name__ == "__main__":
    duplicate_reports()
