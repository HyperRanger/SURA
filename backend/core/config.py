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

    environment: str = "development"

    # One-time codes are short-lived and single-use. The resend cooldown is what
    # P4's resend timer reflects, and it is also what stops this endpoint being
    # used to bill someone's phone with SMS.
    otp_ttl_seconds: int = 300
    otp_max_attempts: int = 5
    otp_resend_cooldown_seconds: int = 60

    access_token_ttl_seconds: int = 60 * 60 * 24

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() in {"production", "prod"}

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
