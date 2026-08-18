from fastapi import APIRouter
from app.api.v1.endpoints import users, reports, auth, admin, roles, data, settings, sse, feed, comments, weather, public, posts, notifications, analytics, sync

api_router = APIRouter()

# Group endpoints by domain with appropriate URL prefixes and tags
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(roles.router, prefix="/admin/roles", tags=["admin roles"])
api_router.include_router(data.router, prefix="/admin/data", tags=["admin data"])
api_router.include_router(settings.router, prefix="/admin/settings", tags=["admin settings"])
api_router.include_router(feed.router, prefix="/feed", tags=["feed"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(comments.router, prefix="/posts", tags=["comments"])
api_router.include_router(comments.router, prefix="/users", tags=["users search"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(public.router, prefix="/public", tags=["public"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(sse.router, prefix="/sse", tags=["sse"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
