import uuid

BASE = "/api/v1/credit-applications"
VALID = {"applicant_document": "8-430-70", "amount": 1000, "term_months": 12}


def create(client, **overrides):
    return client.post(BASE, json={**VALID, **overrides})


def test_create_returns_201_with_location(client):
    response = create(client, applicant_document=" pe-5-687 ")

    assert response.status_code == 201
    body = response.json()
    assert response.headers["location"] == f"{BASE}/{body['id']}"
    assert body["status"] == "PENDING"
    assert body["applicant_document"] == "PE-5-687"


def test_create_invalid_returns_422_with_field_errors(client):
    response = create(client, amount=499.99, applicant_document="14-1-1")

    assert response.status_code == 422
    body = response.json()
    assert body["type"] == "validation_error"
    assert {
        "field": "amount",
        "message": "El monto debe estar entre $500.00 y $50,000.00.",
    } in body["errors"]
    assert "applicant_document" in [e["field"] for e in body["errors"]]


def test_create_malformed_json_returns_400(client):
    response = client.post(BASE, content="{monto: ", headers={"content-type": "application/json"})

    assert response.status_code == 400
    assert response.json()["type"] == "malformed_request"


def test_amount_with_cents_round_trips_exactly(client):
    created = create(client, amount=1000.10).json()

    assert created["amount"] == 1000.1
    assert client.get(f"{BASE}/{created['id']}").json()["amount"] == 1000.1


def test_list_filters_by_status(client):
    approved = create(client).json()
    create(client)
    client.patch(
        f"{BASE}/{approved['id']}/status", json={"status": "APPROVED", "comment": "Todo en orden"}
    )

    body = client.get(BASE, params={"status": "APPROVED"}).json()

    assert body["total"] == 1
    assert [item["id"] for item in body["items"]] == [approved["id"]]


def test_list_lowercase_status_returns_422_in_spanish(client):
    response = client.get(BASE, params={"status": "pending"})

    assert response.status_code == 422
    assert response.json()["errors"] == [
        {
            "field": "status",
            "message": (
                "Valor no permitido. Valores aceptados: 'PENDING', 'APPROVED' o 'REJECTED'."
            ),
        }
    ]


def test_list_limit_above_maximum_returns_422(client):
    response = client.get(BASE, params={"limit": 101})

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "limit"


def test_list_offset_beyond_total_returns_empty_items(client):
    create(client)
    create(client)

    response = client.get(BASE, params={"offset": 10})

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 2


def test_get_unknown_id_returns_404(client):
    response = client.get(f"{BASE}/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["type"] == "not_found"


def test_get_invalid_id_returns_422(client):
    response = client.get(f"{BASE}/abc")

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "id"


def test_approve_pending_application(client):
    application = create(client).json()

    response = client.patch(
        f"{BASE}/{application['id']}/status",
        json={"status": "APPROVED", "comment": "  Cumple requisitos  "},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "APPROVED"
    assert body["decision_comment"] == "Cumple requisitos"
    assert body["decided_at"] is not None


def test_second_decision_returns_409(client):
    application = create(client).json()
    url = f"{BASE}/{application['id']}/status"
    client.patch(url, json={"status": "APPROVED", "comment": "Cumple requisitos"})

    response = client.patch(url, json={"status": "REJECTED", "comment": "Cambio de opinión"})

    assert response.status_code == 409
    body = response.json()
    assert body["type"] == "application_already_decided"
    assert body["detail"] == "La solicitud ya fue aprobada y su decisión es final."


def test_patch_pending_status_returns_422(client):
    application = create(client).json()

    response = client.patch(
        f"{BASE}/{application['id']}/status", json={"status": "PENDING", "comment": "Volver atrás"}
    )

    assert response.status_code == 422


def test_patch_unknown_id_returns_404(client):
    response = client.patch(
        f"{BASE}/{uuid.uuid4()}/status", json={"status": "APPROVED", "comment": "Cumple requisitos"}
    )

    assert response.status_code == 404
