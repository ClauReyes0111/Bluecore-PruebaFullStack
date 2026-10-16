import os

# Los tests usan SQLite en memoria y no deben depender de un .env.
# Debe fijarse antes de importar cualquier módulo de app (Settings exige DATABASE_URL).
os.environ.setdefault("DATABASE_URL", "sqlite://")

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import create_app
from app.models.base import Base


@pytest.fixture
def db_session() -> Iterator[Session]:
    # SQLite en memoria: los tests corren sin Docker ni PostgreSQL.
    # StaticPool mantiene una única conexión para que la base no desaparezca entre sesiones.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def app(db_session):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db_session
    return application


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)
