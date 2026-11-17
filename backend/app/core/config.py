import os
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://billing_app:billing_app@localhost:5432/billing_app"
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_password_hash: str = ""
    postgres_db: str = "billing_app"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    migration_database_url: str = ""
    jwt_secret: str = "dev-only-change-me-before-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    expose_dev_tokens: bool = True
    upload_dir: str = "uploads"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://localhost:5175,http://127.0.0.1:5175,http://localhost:3000"
    app_name: str = "PeakSuite"

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    @property
    def running_on_lambda(self) -> bool:
        return bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

    @model_validator(mode="after")
    def lambda_storage(self):
        if self.running_on_lambda and self.upload_dir == "uploads":
            self.upload_dir = "/tmp/uploads"
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def migration_url(self) -> str:
        if self.migration_database_url:
            return self.migration_database_url
        if self.postgres_password:
            from urllib.parse import quote_plus

            user = quote_plus(self.postgres_user)
            password = quote_plus(self.postgres_password)
            return (
                f"postgresql+psycopg://{user}:{password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return self.database_url


settings = Settings()
