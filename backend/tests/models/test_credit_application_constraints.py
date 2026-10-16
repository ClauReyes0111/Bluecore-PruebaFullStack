"""Las restricciones CHECK de la tabla rechazan datos inválidos aunque no pasen por la API."""

import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.domain.status import ApplicationStatus
from app.models.credit_application import CreditApplication

NOW = datetime(2026, 10, 15, 12, 0, 0)


def make_application(**overrides) -> CreditApplication:
    values = {
        "id": str(uuid.uuid4()),
        "applicant_document": "8-430-70",
        "amount": Decimal("1000.00"),
        "term_months": 12,
        "status": ApplicationStatus.PENDING,
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return CreditApplication(**values)


@pytest.mark.parametrize(
    "overrides",
    [
        {"amount": Decimal("499.99")},
        {"amount": Decimal("50000.01")},
        {"term_months": 5},
        {"term_months": 61},
        {"status": "CANCELLED"},
    ],
)
def test_database_rejects_out_of_range_values(db_session, overrides):
    db_session.add(make_application(**overrides))

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_database_accepts_boundary_values(db_session):
    db_session.add(make_application(amount=Decimal("500.00"), term_months=6))
    db_session.add(make_application(amount=Decimal("50000.00"), term_months=60))

    db_session.flush()
