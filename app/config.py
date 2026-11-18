from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    webhook_base_url: str = ""
    groq_api_key: str = ""
    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    primary_provider: str = "groq"
    fallback_providers: str = "gemini,openrouter"
    groq_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    gemini_model: str = "gemini-2.0-flash"
    openrouter_model: str = "meta-llama/llama-3.2-11b-vision-instruct:free"
    app_env: str = "development"
    log_level: str = "INFO"
    max_file_size_mb: int = 50
    processing_timeout_seconds: int = 180
    @property
    def fallback_list(self): return [x.strip() for x in self.fallback_providers.split(',') if x.strip()]
    @property
    def max_file_size_bytes(self): return self.max_file_size_mb * 1024 * 1024

@lru_cache
def get_settings(): return Settings()
