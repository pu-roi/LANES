# CRUD index
from app.crud.user import (
    get_password_hash, get_user, get_user_by_username, get_user_by_email, create_user,
    get_users_filtered, update_user_status, delete_user, hard_delete_user
)
from app.crud.report import (
    get_flood_report, get_flood_reports, get_pending_flood_reports, 
    update_flood_report_status, create_flood_report,
    get_active_avoidance_zones, create_flood_avoidance_zone,
    get_all_flood_reports_filtered, get_admin_dashboard_stats,
    deactivate_flood_avoidance_zone, deactivate_flood_avoidance_zones_bulk,
    get_all_avoidance_zones_filtered, update_flood_avoidance_zone,
    get_admin_dashboard_charts
)

from app.crud.post import create_community_post, get_post, get_posts, delete_post
from app.crud.notification import create_notification, get_notifications, get_unread_count, mark_as_read, mark_all_as_read
from app.crud.audit import create_audit_log, get_audit_logs
from app.crud.saved_place import get_saved_places_by_user, create_saved_place, delete_saved_place
