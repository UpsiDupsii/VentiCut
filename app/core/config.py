from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "VentiCut"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Storage paths
    STORAGE_DIR: Path = Path("storage")
    UPLOAD_DIR: Path = Path("storage/uploads")
    TEMP_DIR: Path = Path("storage/temp")
    PROCESSED_DIR: Path = Path("storage/processed")

    # Processing limits & presets
    DEFAULT_TARGET_ASPECT_RATIO: str = "9:16"
    MAX_UPLOAD_SIZE_MB: int = 500
    MAX_SHORT_DURATION_SECONDS: int = 60
    MIN_SHORT_DURATION_SECONDS: int = 15

    # Optional AI Keys
    OPENAI_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    WHISPER_MODEL: str = "base"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
