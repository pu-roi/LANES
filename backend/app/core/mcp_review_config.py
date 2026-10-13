"""Dedicated, disabled-by-default MCP identity and transport configuration."""
from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPReviewSettings(BaseSettings):
    review_enabled: bool = False
    gateway_enabled: bool = False
    backend_url: str = ""
    public_url: str = ""
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    allowed_google_subject: str = ""
    allowed_email: str = ""
    assertion_private_key_file: Path | None = None
    assertion_public_key_file: Path | None = None
    oauth_signing_key: SecretStr = SecretStr("")
    oauth_storage_directory: Path | None = None
    client_redirect_uris: list[str] = []

    model_config = SettingsConfigDict(
        env_prefix="LANES_MCP_", env_file=".env", extra="ignore",
    )


@lru_cache
def mcp_settings() -> MCPReviewSettings:
    return MCPReviewSettings()


MCP_REVIEW_REVISION = "mcp-news-preview-v1"
MCP_ASSERTION_AUDIENCE = "lanes-mcp-review"
