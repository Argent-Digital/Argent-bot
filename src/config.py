from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_NAME: str
    DB_PASS: str

    UX_USERNAME: str
    UX_PASS: str
    ux_URL: str

    IP: str

    SHOP_ID: int
    YKASSA_KEY: str

    OUT_URL: str
    OUT_CERT: str

    BOT_TOKEN: str
    TG_ADM_ID: int

    @property
    def DATABASE_URL_asynpg(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    

    @property
    def DATABASE_URL_synpg(self):
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()