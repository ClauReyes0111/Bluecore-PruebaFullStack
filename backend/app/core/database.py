from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def build_engine(url: str, schema: str) -> Engine:
    """Crea el engine; en PostgreSQL todas las consultas trabajan dentro de `schema`.

    Fijar search_path en la conexión evita escribir el esquema en cada modelo y garantiza
    que la aplicación solo vea esquema_a (el único asignado al usuario en la base de Bluecore).
    """
    engine_url = make_url(url)
    if engine_url.get_backend_name() == "postgresql":
        engine_url = engine_url.update_query_dict({"options": f"-csearch_path={schema}"})
    # pool_pre_ping descarta conexiones que el servidor cerró por inactividad
    return create_engine(engine_url, pool_pre_ping=True)


engine = build_engine(settings.database_url, settings.db_schema)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
