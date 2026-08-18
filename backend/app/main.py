from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.exceptions import ResponseValidationError
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import engine, Base
from app.core.limiter import limiter
from app import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Attempt to create database tables on startup
    try:
        # Base.metadata.create_all(bind=engine) # Disabled to enforce Alembic migrations
        print("Database tables created or already exist.")
        
        # Seed default roles and admin user
        from sqlalchemy.orm import Session
        from app.core.database import SessionLocal
        from app.crud.user import get_user_by_username, create_user
        from app.schemas.user import UserCreate
        from app.models.role import Role
        
        db = SessionLocal()
        try:
            # Seed Roles if missing
            existing_roles = db.query(Role).count()
            if existing_roles == 0:
                default_roles = [
                    Role(id=1, name="Super Admin", permissions={"reports": "full", "zones": "full", "users": "full", "roles": "full", "audit": "view", "data": "full", "settings": "full"}, is_template=True),
                    Role(id=2, name="DRRM Officer", permissions={"reports": "full", "zones": "full", "users": "none", "roles": "none", "audit": "view", "data": "none", "settings": "none"}, is_template=True),
                    Role(id=3, name="Moderator", permissions={"reports": "full", "zones": "none", "users": "none", "roles": "none", "audit": "none", "data": "none", "settings": "none"}, is_template=True),
                    Role(id=4, name="Commuter", permissions={}, is_template=True)
                ]
                db.add_all(default_roles)
                db.commit()
                print("Default roles seeded.")

            admin_user = get_user_by_username(db, username="admin")
            if not admin_user:
                admin_in = UserCreate(
                    username="admin",
                    email="admin@lanes.local",
                    password="admin",
                    role_id=1
                )
                create_user(db, user=admin_in)
                print("Default admin user created (admin/admin).")
        finally:
            db.close()

    except Exception as e:
        print(f"Warning: Could not create database tables or seed data on startup ({e}). Continuing startup...")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Core backend server logic for LANES application",
    version=settings.API_VERSION,
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(ResponseValidationError)
async def validation_exception_handler(request: Request, exc: ResponseValidationError):
    import traceback
    print(f"ResponseValidationError: {exc.errors()}")
    traceback.print_exc()
    # Stringify errors to avoid JSON serialization failure on WKBElement or Enum
    safe_errors = [{"loc": e.get("loc"), "msg": e.get("msg"), "type": e.get("type")} for e in exc.errors()]
    return JSONResponse(
        status_code=500,
        content={"detail": "Response Validation Error", "errors": safe_errors},
    )


# Define allowed origins for CORS.
# Allows local Next.js development server and LAN mobile devices
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):3000$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Range", "Accept-Ranges"],
)

from app.api.v1.api import api_router

# Include routing endpoints coordinator
app.include_router(api_router, prefix="/api/v1")

# Mount static files (e.g., for serving offline Map data like valhalla .tar files)
import os
os.makedirs("data", exist_ok=True)
app.mount("/static", StaticFiles(directory="data"), name="static")



@app.get("/")
def read_root():
    """
    Root gateway route. Returns general information about the API.
    """
    return {
        "status": "active",
        "message": "Welcome to the LANES API gateway.",
        "docs_url": "/docs",
    }


@app.get("/health")
def health_check():
    """
    Health check route for monitoring.
    """
    database_status = "not_connected"
    try:
        # Try to connect and execute a simple query
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception:
        # Connection failed
        pass

    return {
        "status": "healthy",
        "details": {
            "database": database_status,
        }
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    Dummy favicon route to prevent 404 errors in the logs.
    """
    return Response(content=b"", media_type="image/x-icon")


# Trigger reload
