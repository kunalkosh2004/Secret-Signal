"""
Application settings loaded from environment variables.

Uses Pydantic Settings (pydantic-settings) for validation and type coercion.

TODO:
  - Install:  pip install pydantic-settings
  - Create a Settings class with fields matching your .env variables.
  - Instantiate once:  settings = Settings()
  - Import `settings` everywhere instead of reading os.environ directly.

Example fields:

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")

        database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/secret_signal"
        secret_key: str = "change-me-in-production"
        algorithm: str = "HS256"
        access_token_expire_minutes: int = 30

        google_client_id: str = ""
        google_client_secret: str = ""
        google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

        frontend_url: str = "http://localhost:5173"

        debug: bool = True
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/secret_signal"
    secret_key: str = "RaBbmulLabdWENGXsquvTNVQCl0tJVd-b0YInJCZ2OzJ8r5XS_B1QAYi3CSNPmp62135DWd5C05u92zXHOEjrw"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    google_client_id: str = "1083073728796-5e474n9nm2r3qshjj29ngic8tq9e3fu0.apps.googleusercontent.com"
    google_client_secret: str = "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"
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    google_link_redirect_uri: str = (
    "http://localhost:8000/api/v1/auth/google/link/callback"
)

    frontend_url: str = "http://localhost:5173"
    redis_url: str = "redis://localhost:6379/0"

    debug: bool = True


settings = Settings()
