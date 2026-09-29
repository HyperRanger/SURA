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

    # Termii sends the codes. The host and sender are account-specific, so they
    # are settings rather than constants. `dnd` is the transactional channel:
    # `generic` is marketing traffic and must never carry a login code.
    termii_api_key: str | None = None
    termii_base_url: str = "https://api.termii.com"
    termii_sender_id: str = "Sura"
    termii_channel: str = "dnd"
    termii_timeout_seconds: int = 10

    otp_message_template: str = "{code} is your Sura verification code. It expires in {ttl_seconds} seconds. Never share it."

    # Bank staff get a second factor on top of the password. Turning this off is
    # a deployment decision for the demo, not a per-account setting.
    bank_mfa_required: bool = True
    bank_login_max_password_attempts: int = 5
    bank_login_lockout_seconds: int = 900

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() in {"production", "prod"}

    @property
    def is_sms_configured(self) -> bool:
        """Whether a real message can be sent.

        False means codes are generated and returned in the response instead, so
        the demo works without an account. Production refuses to start without
        one, because a signup that can never be verified is a support queue.
        """
        return bool(self.termii_api_key)

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
