from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    TG_ADM_ID: int

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()