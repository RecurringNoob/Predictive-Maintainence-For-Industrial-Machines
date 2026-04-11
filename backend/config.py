from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/maintenance"

    # ThingSpeak
    thingspeak_channel_id: str = ""
    thingspeak_read_api_key: str = ""
    poll_interval_seconds: int = 15

    # ML
    model_path: str = "ml/predictive_maintenance.pkl"
    scaler_path: str = "ml/scaler.pkl"
    model_version: str = "v1"

    # API
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def thingspeak_url(self) -> str:
        return (
            f"https://api.thingspeak.com/channels/{self.thingspeak_channel_id}"
            f"/feeds.json?api_key={self.thingspeak_read_api_key}&results=1"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()