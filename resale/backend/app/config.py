from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    claude_model: str = "claude-opus-5-5"
    default_currency: str = "RUB"
    default_language: str = "ru"
    max_images: int = 6
    max_image_bytes: int = 5 * 1024 * 1024


settings = Settings()
