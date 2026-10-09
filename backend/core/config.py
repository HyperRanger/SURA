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

    # A checked-out pooled connection avoids a new TLS/database handshake per
    # request. Recycling it before provider idle limits does the stale-connection
    # work off the request's critical path, so a health probe before every read
    # is unnecessary in the normal case.
    database_pool_size: int = 5
    database_max_overflow: int = 5
    database_pool_timeout_seconds: int = 10
    database_pool_recycle_seconds: int = 1500

    # One-time codes are short-lived and single-use. The resend cooldown is what
    # P4's resend timer reflects, and it is also what stops this endpoint being
    # used to bill someone's phone with SMS.
    otp_ttl_seconds: int = 300
    otp_max_attempts: int = 5
    otp_resend_cooldown_seconds: int = 60

    access_token_ttl_seconds: int = 60 * 60 * 24

    # A session that makes no request for this long is ended server-side on the
    # next request, so a forgotten tab cannot stay signed in forever.
    # `last_activity_stamp_interval_seconds` throttles the per-request write to
    # the activity timestamp: an active member stamps at most once a minute, not
    # once per request.
    session_idle_timeout_seconds: int = 5 * 60
    last_activity_stamp_interval_seconds: int = 60
    # Contact resolution helps a member build a group, but it must not become a
    # customer-directory endpoint. The limiter is durable and per authenticated
    # member, so app restarts and additional web instances do not reset it.
    contact_lookup_max_attempts: int = 10
    contact_lookup_window_seconds: int = 15 * 60

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
    # A checker cannot see that BaseSettings populates required fields from the
    # environment and .env, so it reads Settings() as missing four arguments.
    # Silenced narrowly here. Giving those fields defaults instead would be the
    # dangerous fix: a missing secret_key would then silently become "" and the
    # app would boot with no signing secret at all.
    return Settings()  # pyright: ignore[reportCallIssue]
