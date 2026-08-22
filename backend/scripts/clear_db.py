import sys
import os

# Add the backend folder path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.role import Role
from app.models.user import User
from app.models.profile import Profile
from app.models.setting import SystemSetting
from app.core.security import get_password_hash
from app.crud.settings import DEFAULT_SETTINGS

def clear_and_reseed_db():
    db = SessionLocal()
    try:
        print("Connecting to database and clearing existing data...", flush=True)
        
        # Delete in topological / foreign-key order
        tables_to_delete = [
            "flood_avoidance_zones",
            "flood_report_locations",
            "flood_report_surveys",
            "flood_reports",
            "post_interactions",
            "comment_interactions",
            "comments",
            "community_posts",
            "saved_places",
            "notifications",
            "addresses",
            "otp_verifications",
            "profiles",
            "users",
            "roles",
            "audit_logs",
            "visitor_counts",
            "system_settings"
        ]
        
        for tbl in tables_to_delete:
            db.execute(text(f"DELETE FROM {tbl};"))
            # Reset sequence if exists
            try:
                db.execute(text(f"ALTER SEQUENCE IF EXISTS {tbl}_id_seq RESTART WITH 1;"))
            except Exception:
                pass
            print(f"  - Cleared {tbl}", flush=True)
            
        db.commit()
        print("All tables cleared successfully!", flush=True)
        
        print("\nReseeding default database records...", flush=True)
        
        # 1. Reseed Roles
        default_roles = [
            Role(
                id=1, 
                name="Super Admin", 
                permissions={"reports": "full", "zones": "full", "users": "full", "roles": "full", "audit": "view", "data": "full", "settings": "full"}, 
                is_template=True
            ),
            Role(
                id=2, 
                name="DRRM Officer", 
                permissions={"reports": "full", "zones": "full", "users": "none", "roles": "none", "audit": "view", "data": "none", "settings": "none"}, 
                is_template=True
            ),
            Role(
                id=3, 
                name="Moderator", 
                permissions={"reports": "full", "zones": "none", "users": "none", "roles": "none", "audit": "none", "data": "none", "settings": "none"}, 
                is_template=True
            ),
            Role(
                id=4, 
                name="Commuter", 
                permissions={}, 
                is_template=True
            )
        ]
        db.add_all(default_roles)
        db.commit()
        print("  - Default roles seeded: Super Admin, DRRM Officer, Moderator, Commuter", flush=True)
        
        # 2. Reseed Default Admin User
        admin_user = User(
            id=1,
            username="admin",
            email="admin@lanes.local",
            hashed_password=get_password_hash("admin"),
            role_id=1,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print("  - Default admin user seeded: username='admin', password='admin', email='admin@lanes.local'", flush=True)
        
        # 3. Reseed Admin Profile
        admin_profile = Profile(
            user_id=admin_user.id,
            first_name="Super",
            last_name="Admin",
            trust_score=100,
            is_public=True,
            display_full_name=True,
            cover_color="#3B82F6"
        )
        db.add(admin_profile)
        db.commit()
        print("  - Default admin profile seeded.", flush=True)
        
        # 4. Reseed Default System Settings
        for key, val in DEFAULT_SETTINGS.items():
            setting = SystemSetting(key=key, value=val, last_updated_by=admin_user.id)
            db.add(setting)
        db.commit()
        print("  - Default system settings seeded.", flush=True)
        
        # 5. Summary & Verification
        roles_count = db.execute(text("SELECT COUNT(*) FROM roles;")).scalar()
        users_count = db.execute(text("SELECT COUNT(*) FROM users;")).scalar()
        profiles_count = db.execute(text("SELECT COUNT(*) FROM profiles;")).scalar()
        reports_count = db.execute(text("SELECT COUNT(*) FROM flood_reports;")).scalar()
        zones_count = db.execute(text("SELECT COUNT(*) FROM flood_avoidance_zones;")).scalar()
        posts_count = db.execute(text("SELECT COUNT(*) FROM community_posts;")).scalar()
        comments_count = db.execute(text("SELECT COUNT(*) FROM comments;")).scalar()
        settings_count = db.execute(text("SELECT COUNT(*) FROM system_settings;")).scalar()
        
        print("\nDatabase verification summary:", flush=True)
        print(f"  - Roles: {roles_count}", flush=True)
        print(f"  - Users: {users_count}", flush=True)
        print(f"  - Profiles: {profiles_count}", flush=True)
        print(f"  - System Settings: {settings_count}", flush=True)
        print(f"  - Flood Reports: {reports_count}", flush=True)
        print(f"  - Avoidance Zones: {zones_count}", flush=True)
        print(f"  - Community Posts: {posts_count}", flush=True)
        print(f"  - Comments: {comments_count}", flush=True)
        print("\nDatabase successfully cleared and reseeded with default data!", flush=True)
        
    except Exception as e:
        db.rollback()
        print(f"\nError occurred while clearing/reseeding database: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    clear_and_reseed_db()
