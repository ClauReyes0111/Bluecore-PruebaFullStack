from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.database import get_db


def test_health_returns_ok_when_database_responds(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_returns_503_problem_when_database_is_down(app):
    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise OperationalError("SELECT 1", {}, Exception("down"))

    app.dependency_overrides[get_db] = lambda: BrokenSession()

    response = TestClient(app).get("/health")

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json() == {
        "type": "service_unavailable",
        "title": "Servicio no disponible",
        "status": 503,
        "detail": "La base de datos no está disponible.",
    }
