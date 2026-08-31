from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    gemini_api_key: str
    api_key: str
    database_url: str = "sqlite+aiosqlite:///./wealthie.db"
    upload_dir: str = "./uploads"
    max_image_size_mb: int = 10
    max_concurrent_jobs: int = 5
    allowed_origins: str = "http://localhost:8000"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


settings = Settings()
