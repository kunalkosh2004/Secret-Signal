"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            REPO_ROOT / ".env",
            BACKEND_ROOT / ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    debug: bool = True

    # Environment
    environment: str = "development"
    log_level: str = "info"

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    google_link_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/link/callback"

    frontend_url: str = "http://localhost:5173"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_url: str = ""

    # OpenTelemetry (future)
    otel_exporter_otlp_endpoint: str = ""

    @model_validator(mode="after")
    def populate_redis_url(self) -> "Settings":
        if self.redis_url:
            return self

        auth = f":{self.redis_password}@" if self.redis_password else ""
        self.redis_url = f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return self


settings = Settings()
