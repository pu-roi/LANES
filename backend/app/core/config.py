from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "LANES"
    API_VERSION: str = "0.1.0"
    
    # Database Configuration
    # Defaults to PostgreSQL with psycopg (v3) driver
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/lanes"

    # OpenRouteService API Configuration
    ORS_URL: str = "https://api.openrouteservice.org/v2"
    ORS_API_KEY: str = ""

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    
    # Resend Email Configuration
    RESEND: str = ""
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "Lanes <noreply@navlanes.live>"

    @property
    def effective_resend_api_key(self) -> str:
        return self.RESEND_API_KEY or self.RESEND

    # Valhalla Engine
    VALHALLA_URL: str = "http://localhost:8002"
    VALHALLA_AUDIENCE: str = ""
    
    # Valhalla
    VALHALLA_DATA_DIR: str = "./valhalla_data"

    # Security
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


def validate_production_routing_configuration() -> None:
    """Fail closed when a production backend would call a local routing engine."""
    if settings.ENVIRONMENT.lower() not in {"production", "prod"}:
        return

    if "localhost" in settings.VALHALLA_URL or "127.0.0.1" in settings.VALHALLA_URL:
        raise RuntimeError("VALHALLA_URL must reference the private Valhalla service in production.")
    if not settings.VALHALLA_AUDIENCE:
        raise RuntimeError("VALHALLA_AUDIENCE is required for authenticated Valhalla requests in production.")
