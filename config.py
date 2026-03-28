from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str
    database_url: str = "sqlite+aiosqlite:///./wealthie.db"
    upload_dir: str = "./uploads"
    max_image_size_mb: int = 10
    api_key: str
    max_concurrent_jobs: int = 5

    class Config:
        env_file = ".env"


settings = Settings()