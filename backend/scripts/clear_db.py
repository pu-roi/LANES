import sys
import os

# Add the backend folder path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.core.database import SessionLocal

def clear_dummy_data():
    db = SessionLocal()
    try:
        print("Clearing database dummy data...")
        
        # Truncate tables cascade (this clears flood_reports, flood_avoidance_zones, flood_report_locations, flood_report_surveys, audit_logs, community_posts, comments, post_interactions, comment_interactions, saved_places, notifications, addresses, otp_verifications)
        db.execute(text("TRUNCATE TABLE flood_avoidance_zones, flood_report_locations, flood_report_surveys, flood_reports, audit_logs, community_posts, comments, post_interactions, comment_interactions, saved_places, notifications, addresses, otp_verifications CASCADE;"))
        
        # Optionally, we might want to reset system_settings but for now we leave them alone so the system stays configured
        # db.execute(text("TRUNCATE TABLE system_settings;"))
        
        # Delete profiles of non-admin users to avoid foreign key constraints
        db.execute(text("DELETE FROM profiles WHERE user_id IN (SELECT id FROM users WHERE username != 'admin');"))
        
        # Delete all users except the default admin
        db.execute(text("DELETE FROM users WHERE username != 'admin';"))
        
        db.commit()
        print("Database cleared successfully!")
        
        # Verify counts
        users_count = db.execute(text("SELECT COUNT(*) FROM users;")).scalar()
        reports_count = db.execute(text("SELECT COUNT(*) FROM flood_reports;")).scalar()
        zones_count = db.execute(text("SELECT COUNT(*) FROM flood_avoidance_zones;")).scalar()
        audit_count = db.execute(text("SELECT COUNT(*) FROM audit_logs;")).scalar()
        posts_count = db.execute(text("SELECT COUNT(*) FROM community_posts;")).scalar()
        comments_count = db.execute(text("SELECT COUNT(*) FROM comments;")).scalar()
        settings_count = db.execute(text("SELECT COUNT(*) FROM system_settings;")).scalar()
        
        print(f"Remaining users in database: {users_count}")
        print(f"Remaining reports in database: {reports_count}")
        print(f"Remaining avoidance zones: {zones_count}")
        print(f"Remaining audit logs: {audit_count}")
        print(f"Remaining community posts: {posts_count}")
        print(f"Remaining comments: {comments_count}")
        
    except Exception as e:
        db.rollback()
        print(f"Error occurred while clearing database: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    clear_dummy_data()
