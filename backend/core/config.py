from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/sura"
    secret_key: str = "super-secret-key"
    jwt_algorithm: str = "HS256"
    demo_otp_code: str = "123456"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
