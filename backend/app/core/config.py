from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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
    
    # Brevo SMTP Configuration
    BREVO_SMTP_SERVER: str = "smtp-relay.brevo.com"
    BREVO_SMTP_PORT: int = 587
    BREVO_SMTP_KEY: str = ""

    # Valhalla Engine
    VALHALLA_URL: str = "http://localhost:8002"
    
    # Valhalla
    VALHALLA_DATA_DIR: str = "./valhalla_data"

    # Security
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
