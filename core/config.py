from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    secret_key: str
    anthropic_api_key: str
    database_url: str = "sqlite:///./time_manager.db"
    # Ліміт AI-запитів на користувача за хвилину (власна пропозиція)
    ai_rate_limit_per_minute: int = 5


settings = Settings()
