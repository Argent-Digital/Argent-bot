from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    TG_ADM_ID: int
    CORE_URL: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()