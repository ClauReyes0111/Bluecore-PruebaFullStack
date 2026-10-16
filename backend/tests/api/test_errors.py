import uuid

import pytest
from fastapi import HTTPException, Query
from fastapi.testclient import TestClient

from app.domain.exceptions import ApplicationAlreadyDecided, ApplicationNotFound
from app.domain.status import ApplicationStatus
from app.schemas.credit_application import CreditApplicationCreate

PROBLEM_JSON = "application/problem+json"


@pytest.fixture
def app_with_test_routes(app):
    @app.post("/test-validation")
    def validation(body: CreditApplicationCreate) -> dict:
        return {}

    @app.get("/test-items/{application_id}")
    def items(application_id: uuid.UUID, limit: int = Query(20, ge=1, le=100)) -> dict:
        return {}

    @app.get("/test-forbidden")
    def forbidden() -> dict:
        raise HTTPException(403, "Prohibido")

    @app.get("/test-boom")
    def boom() -> dict:
        raise RuntimeError("secreto")

    @app.get("/test-not-found/{application_id}")
    def not_found(application_id: str) -> dict:
        raise ApplicationNotFound(application_id)

    @app.get("/test-decided/{status}")
    def decided(status: ApplicationStatus) -> dict:
        raise ApplicationAlreadyDecided("abc", status)

    return app


@pytest.fixture
def api(app_with_test_routes) -> TestClient:
    return TestClient(app_with_test_routes, raise_server_exceptions=False)


VALID_BODY = {"applicant_document": "8-430-70", "amount": 1000, "term_months": 12}


def assert_problem(response, status, type_, title, detail):
    assert response.status_code == status
    assert response.headers["content-type"].startswith(PROBLEM_JSON)
    body = response.json()
    assert body["type"] == type_
    assert body["title"] == title
    assert body["status"] == status
    assert body["detail"] == detail
    return body


def test_unknown_route_returns_404_problem(client):
    response = client.get("/no-existe")

    assert_problem(
        response, 404, "not_found", "Recurso no encontrado", "La ruta solicitada no existe."
    )


def test_wrong_method_returns_405_problem(client):
    response = client.delete("/health")

    assert_problem(
        response,
        405,
        "method_not_allowed",
        "Método no permitido",
        "El método HTTP no está permitido en esta ruta.",
    )


def test_application_not_found_returns_404_problem(api):
    response = api.get("/test-not-found/xyz")

    assert_problem(
        response,
        404,
        "not_found",
        "Recurso no encontrado",
        "No existe una solicitud con id xyz.",
    )


@pytest.mark.parametrize(
    ("status", "word"),
    [("APPROVED", "aprobada"), ("REJECTED", "rechazada")],
)
def test_already_decided_returns_409_problem(api, status, word):
    response = api.get(f"/test-decided/{status}")

    assert_problem(
        response,
        409,
        "application_already_decided",
        "Solicitud ya decidida",
        f"La solicitud ya fue {word} y su decisión es final.",
    )


def test_unexpected_error_returns_500_without_leaking_details(api):
    response = api.get("/test-boom")

    assert_problem(
        response,
        500,
        "internal_error",
        "Error interno",
        "Ocurrió un error inesperado. Intente nuevamente más tarde.",
    )
    assert "secreto" not in response.text


def test_invalid_json_returns_400_malformed_request(api):
    response = api.post(
        "/test-validation", content="{monto: ", headers={"content-type": "application/json"}
    )

    body = assert_problem(
        response,
        400,
        "malformed_request",
        "Solicitud mal formada",
        "El cuerpo de la petición no es un JSON válido.",
    )
    assert "errors" not in body


def test_validation_error_has_422_shape(api):
    response = api.post("/test-validation", json={})

    body = assert_problem(
        response,
        422,
        "validation_error",
        "Datos inválidos",
        "La solicitud contiene datos inválidos.",
    )
    assert {"field": "term_months", "message": "Este campo es obligatorio."} in body["errors"]


def test_missing_field_message(api):
    body = api.post(
        "/test-validation", json={"applicant_document": "8-430-70", "amount": 1000}
    ).json()

    assert body["errors"] == [{"field": "term_months", "message": "Este campo es obligatorio."}]


def test_custom_error_message_is_kept_as_is(api):
    body = api.post("/test-validation", json={**VALID_BODY, "amount": 499.99}).json()

    assert body["errors"] == [
        {"field": "amount", "message": "El monto debe estar entre $500.00 y $50,000.00."}
    ]


def test_extra_field_is_not_allowed(api):
    body = api.post("/test-validation", json={**VALID_BODY, "foo": 1}).json()

    assert body["errors"] == [{"field": "foo", "message": "Campo no permitido."}]


def test_wrong_type_message(api):
    body = api.post("/test-validation", json={**VALID_BODY, "term_months": "abc"}).json()

    assert body["errors"] == [{"field": "term_months", "message": "Debe ser un número entero."}]


def test_invalid_uuid_is_exposed_as_id(api):
    body = api.get("/test-items/no-es-uuid").json()

    assert body["errors"] == [{"field": "id", "message": "El identificador no es un UUID válido."}]


def test_limit_above_maximum(api):
    body = api.get(f"/test-items/{uuid.uuid4()}", params={"limit": 101}).json()

    assert body["errors"] == [{"field": "limit", "message": "Debe ser menor o igual a 100."}]


def test_limit_below_minimum(api):
    body = api.get(f"/test-items/{uuid.uuid4()}", params={"limit": 0}).json()

    assert body["errors"] == [{"field": "limit", "message": "Debe ser mayor o igual a 1."}]


def test_json_list_body_must_be_an_object(api):
    body = api.post("/test-validation", json=[1, 2]).json()

    assert body["errors"] == [{"field": "body", "message": "El cuerpo debe ser un objeto JSON."}]


def test_generic_http_error_uses_spanish_title(api):
    response = api.get("/test-forbidden")

    assert_problem(response, 403, "http_error", "Error en la solicitud", "Prohibido")


def test_enum_error_message_is_in_spanish(api):
    body = api.get("/api/v1/credit-applications", params={"status": "pending"}).json()

    assert body["errors"] == [
        {
            "field": "status",
            "message": "Valor no permitido. Valores aceptados: 'PENDING', 'APPROVED' o 'REJECTED'.",
        }
    ]
