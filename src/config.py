from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    TG_ADM_ID: int
    CORE_URL: str

    SECRET_KEY_FOR_JWT: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()