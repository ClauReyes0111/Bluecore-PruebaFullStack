from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración leída de variables de entorno o del archivo .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Sin valor por defecto: así la app nunca se conecta en silencio a una base no prevista
    database_url: str
    # Esquema asignado al usuario en la base de Bluecore; la app no usa ningún otro
    db_schema: str = "esquema_a"
    cors_origins: list[str] = ["http://localhost:4200"]


settings = Settings()
