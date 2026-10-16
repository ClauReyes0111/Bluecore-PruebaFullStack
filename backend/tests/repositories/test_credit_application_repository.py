from datetime import datetime, timedelta
from decimal import Decimal

from app.domain.status import ApplicationStatus
from app.models.credit_application import CreditApplication
from app.repositories.credit_application_repository import CreditApplicationRepository

BASE = datetime(2026, 10, 15, 12, 0, 0)
DECIDED_AT = datetime(2026, 10, 16, 9, 0, 0)


def make_application(
    id: str, created_at: datetime = BASE, status: ApplicationStatus = ApplicationStatus.PENDING
) -> CreditApplication:
    return CreditApplication(
        id=id,
        applicant_document="8-430-70",
        amount=Decimal("1000.10"),
        term_months=12,
        status=status,
        created_at=created_at,
        updated_at=created_at,
    )


def test_decide_only_once(db_session):
    repository = CreditApplicationRepository(db_session)
    repository.add(make_application("a"))

    first = repository.decide("a", ApplicationStatus.APPROVED, "Aprobada por riesgo", DECIDED_AT)
    second = repository.decide("a", ApplicationStatus.REJECTED, "Otro criterio", DECIDED_AT)

    stored = repository.get("a")
    assert first is True
    assert second is False
    assert stored.status == ApplicationStatus.APPROVED
    assert stored.decision_comment == "Aprobada por riesgo"
    assert stored.decided_at == DECIDED_AT
    assert stored.updated_at == DECIDED_AT


def test_decide_unknown_id_returns_false(db_session):
    repository = CreditApplicationRepository(db_session)

    assert (
        repository.decide("missing", ApplicationStatus.APPROVED, "Comentario", DECIDED_AT) is False
    )


def test_get_after_decide_returns_fresh_data(db_session):
    repository = CreditApplicationRepository(db_session)
    repository.add(make_application("a"))
    assert repository.get("a").status == ApplicationStatus.PENDING

    repository.decide("a", ApplicationStatus.REJECTED, "Ingresos insuficientes", DECIDED_AT)

    refreshed = repository.get("a")
    assert refreshed.status == ApplicationStatus.REJECTED
    assert refreshed.decision_comment == "Ingresos insuficientes"


def test_get_unknown_returns_none(db_session):
    assert CreditApplicationRepository(db_session).get("missing") is None


def test_list_filters_and_orders(db_session):
    repository = CreditApplicationRepository(db_session)
    repository.add(make_application("old", BASE))
    repository.add(make_application("mid", BASE + timedelta(days=1), ApplicationStatus.APPROVED))
    repository.add(make_application("new", BASE + timedelta(days=2)))

    pending, pending_total = repository.list(ApplicationStatus.PENDING, limit=10, offset=0)
    everything, total = repository.list(None, limit=10, offset=0)
    page, page_total = repository.list(None, limit=1, offset=1)
    beyond, beyond_total = repository.list(None, limit=10, offset=50)

    assert [a.id for a in pending] == ["new", "old"]
    assert pending_total == 2
    assert [a.id for a in everything] == ["new", "mid", "old"]
    assert total == 3
    assert [a.id for a in page] == ["mid"]
    assert page_total == 3
    assert beyond == []
    assert beyond_total == 3
