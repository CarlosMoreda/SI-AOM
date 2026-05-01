from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SI-AOM"
    debug: bool = False
    database_url: str
    jwt_secret: str = "MUDA_ESTE_SECRET_EM_PRODUCAO"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 horas

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "t", "yes", "y", "on", "debug", "dev", "development"}:
                return True
            if normalized in {"0", "false", "f", "no", "n", "off", "release", "prod", "production", ""}:
                return False
        return False


settings = Settings()
