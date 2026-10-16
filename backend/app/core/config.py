from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración leída de variables de entorno o del archivo .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "mysql+pymysql://bluecore:bluecore@localhost:3306/bluecore"
    cors_origins: list[str] = ["http://localhost:4200"]


settings = Settings()
