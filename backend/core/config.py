from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
    )

    database_url: str = "postgresql+psycopg://sura:sura_pass@localhost:5432/sura_dev"
    secret_key: str = "super-secret-key"
    jwt_algorithm: str = "HS256"
    demo_otp_code: str = "123456"

    @field_validator("database_url", mode="before")
    @classmethod
    def use_psycopg_dialect(cls, value: str) -> str:
        """Accept provider URLs while consistently using the installed Psycopg 3 driver."""
        if value.startswith("postgres://"):
            return "postgresql+psycopg://" + value.removeprefix("postgres://")
        if value.startswith("postgresql://"):
            return "postgresql+psycopg://" + value.removeprefix("postgresql://")
        return value


@lru_cache()
def get_settings() -> Settings:
    return Settings()
