from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.credit_application import (
    CreditApplicationCreate,
    CreditApplicationRead,
    StatusChange,
)

VALID_CREATE = {"applicant_document": "8-430-70", "amount": "15000", "term_months": 24}


def error_types(exc: ValidationError) -> set[str]:
    return {error["type"] for error in exc.errors()}


def create(**overrides) -> CreditApplicationCreate:
    return CreditApplicationCreate(**{**VALID_CREATE, **overrides})


# --- Monto ---


@pytest.mark.parametrize("amount", ["499.99", "50000.01"])
def test_amount_out_of_range_is_rejected(amount):
    with pytest.raises(ValidationError) as exc:
        create(amount=amount)
    assert error_types(exc.value) == {"amount_range"}


@pytest.mark.parametrize("amount", ["500", "50000", "500.000"])
def test_amount_boundaries_are_accepted(amount):
    assert create(amount=amount).amount == Decimal(amount)


def test_amount_with_three_decimals_is_rejected():
    with pytest.raises(ValidationError) as exc:
        create(amount="100.555")
    assert error_types(exc.value) == {"amount_decimals"}


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_amount_is_rejected(amount):
    with pytest.raises(ValidationError):
        create(amount=amount)


def test_amount_range_message_is_in_spanish():
    with pytest.raises(ValidationError) as exc:
        create(amount="499.99")
    assert exc.value.errors()[0]["msg"] == "El monto debe estar entre $500.00 y $50,000.00."


# --- Plazo ---


@pytest.mark.parametrize("term", [5, 61])
def test_term_out_of_range_is_rejected(term):
    with pytest.raises(ValidationError) as exc:
        create(term_months=term)
    assert error_types(exc.value) == {"term_range"}


@pytest.mark.parametrize("term", [6, 60])
def test_term_boundaries_are_accepted(term):
    assert create(term_months=term).term_months == term


def test_fractional_term_is_rejected_as_type_error():
    with pytest.raises(ValidationError) as exc:
        create(term_months=12.5)
    assert "term_range" not in error_types(exc.value)


# --- Cédula ---


def test_document_is_normalized():
    assert create(applicant_document=" pe-5-687 ").applicant_document == "PE-5-687"


def test_invalid_document_is_rejected():
    with pytest.raises(ValidationError) as exc:
        create(applicant_document="14-1-1")
    assert error_types(exc.value) == {"document_format"}


def test_unknown_field_is_rejected():
    with pytest.raises(ValidationError) as exc:
        create(foo=1)
    assert error_types(exc.value) == {"extra_forbidden"}


# --- Cambio de estado ---


@pytest.mark.parametrize("status", ["PENDING", "approved", "CANCELLED"])
def test_decision_status_must_be_approved_or_rejected(status):
    with pytest.raises(ValidationError) as exc:
        StatusChange(status=status, comment="Comentario válido")
    assert error_types(exc.value) == {"decision_status"}


@pytest.mark.parametrize("comment", ["abcd", "a" * 501, "      "])
def test_comment_length_is_enforced_after_trimming(comment):
    with pytest.raises(ValidationError) as exc:
        StatusChange(status="APPROVED", comment=comment)
    assert error_types(exc.value) == {"comment_length"}


def test_comment_is_trimmed():
    change = StatusChange(status="REJECTED", comment="  Correcto  ")
    assert change.comment == "Correcto"
    assert change.status == "REJECTED"


# --- Representación de salida ---


def test_read_schema_serializes_amount_as_number_and_dates_in_utc():
    source = SimpleNamespace(
        id="3f1c9a52-6a3e-4c55-9a4e-2d6b1f0e8c11",
        applicant_document="8-430-70",
        amount=Decimal("1000.10"),
        term_months=24,
        status="PENDING",
        decision_comment=None,
        decided_at=None,
        created_at=datetime(2026, 10, 15, 21, 30),
        updated_at=datetime(2026, 10, 15, 21, 30),
    )

    data = CreditApplicationRead.model_validate(source).model_dump(mode="json")

    assert data["amount"] == 1000.1
    assert data["created_at"] == "2026-10-15T21:30:00Z"
    assert data["decided_at"] is None
