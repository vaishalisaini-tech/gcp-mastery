from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Task Tracker API"
    app_env: str = "local"        # Cloud Run will override with APP_ENV
    api_key: str = "dev-key"      # Day 2: comes from Secret Manager

settings = Settings()
