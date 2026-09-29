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

    database_url: str
    secret_key: str
    jwt_algorithm: str
    demo_otp_code: str

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
