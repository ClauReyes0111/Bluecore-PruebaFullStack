from sqlalchemy import text

from app.core.database import build_engine


def test_postgres_engine_sets_search_path_to_schema():
    engine = build_engine("postgresql+psycopg://user:secret@localhost/demo", "esquema_a")

    _, connect_kwargs = engine.dialect.create_connect_args(engine.url)

    assert engine.dialect.name == "postgresql"
    assert connect_kwargs["options"] == "-csearch_path=esquema_a"


def test_non_postgres_engine_ignores_schema():
    engine = build_engine("sqlite://", "esquema_a")

    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar() == 1
