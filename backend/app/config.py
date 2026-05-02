from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "MUDA_ESTE_SECRET_EM_PRODUCAO"


class Settings(BaseSettings):
    app_name: str = "SI-AOM"
    debug: bool = False
    database_url: str
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 horas
    allow_plaintext_password_fallback: bool = False
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return init_settings, dotenv_settings, env_settings, file_secret_settings

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

    @field_validator("cors_origins", mode="before")
    @classmethod
    def normalize_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_runtime_security(self):
        if not self.debug and self.jwt_secret == DEFAULT_JWT_SECRET:
            raise ValueError("JWT_SECRET tem de ser definido fora de debug")
        if not self.debug and self.allow_plaintext_password_fallback:
            raise ValueError(
                "ALLOW_PLAINTEXT_PASSWORD_FALLBACK so pode estar ativo em debug"
            )
        return self


settings = Settings()
